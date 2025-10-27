# Endpoint para buscar documentos reprovados de um candidato
from fastapi import Query

@app.get("/documentos_reprovados")
async def documentos_reprovados(candidato_id: str = Query(...)):
    config = analyzer.load_config()
    try:
        import psycopg2
        conn = psycopg2.connect(**config["db_credentials"])
        cur = conn.cursor()
        # Busca o último lote do candidato (pode ser melhorado para múltiplos lotes)
        cur.execute("""
            SELECT d.arquivo, d.qualidade, d.categoria, d.dados_extraidos
            FROM documentos d
            JOIN lotes l ON d.lote_fk = l.id
            WHERE l.lote_id LIKE %s AND d.qualidade NOT LIKE 'Aprovado%%'
            ORDER BY l.id DESC
        """, (f'%{candidato_id}%',))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        documentos = [
            {"arquivo": r[0], "qualidade": r[1], "categoria": r[2], "dados_extraidos": r[3]} for r in rows
        ]
        return {"reprovados": documentos}
    except Exception as e:
        return {"erro": str(e)}

from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
import tempfile
import os
from backend.document_parsing import analyzer
import uuid


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ou especifique ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    analyzer.init_models()

@app.post("/processar_documentos")
async def processar_documentos(request: Request, files: List[UploadFile] = File(...)):
    form = await request.form()
    candidato_id = form.get("candidato_id")
    resultados = []
    config = analyzer.load_config()
    batch_id = f"api_{uuid.uuid4().hex[:8]}"
    for file in files:
        filename = file.filename
        suffix = os.path.splitext(filename)[1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        try:
            qualidade = analyzer.assess_quality(tmp_path, config)
            categoria = analyzer.classify_document_with_ocr(tmp_path, config) if "Aprovado" in qualidade else "N/A"
            dados_extraidos = analyzer.extract_data(tmp_path, categoria, config) if "Aprovado" in qualidade and "Erro" not in categoria else None
            resultados.append({
                "arquivo": filename,
                "qualidade": qualidade,
                "categoria": categoria,
                "dados_extraidos": dados_extraidos
            })
        finally:
            os.remove(tmp_path)

    # Gera sumário do lote para o banco
    batch_summary = analyzer.generate_batch_summary(batch_id, resultados, config)
    analyzer.manage_db_connection(config, batch_id, batch_summary, resultados)

    # Atualiza o step do candidato para 4 (Análise) se candidato_id for fornecido
    if candidato_id:
        try:
            import psycopg2
            conn = psycopg2.connect(**config["db_credentials"])
            cur = conn.cursor()
            cur.execute("UPDATE candidate SET step = 4 WHERE id = %s", (candidato_id,))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Erro ao atualizar step do candidato: {e}")

    return JSONResponse(content={"resultados": resultados})

# Para rodar: uvicorn app:app --host 0.0.0.0 --port 5002
