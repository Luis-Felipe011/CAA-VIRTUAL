

from fastapi import FastAPI, UploadFile, File, Form, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
import tempfile
import os
import uuid
import psycopg2
from backend.document_parsing import analyzer


# Cria a instância principal da API
app = FastAPI(
    title="API de Análise de Documentos",
    description="Processa e lista documentos reprovados dos candidatos",
    version="1.0.0"
)

# Middleware de CORS (permite conexões externas, ex: do front-end)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Pode restringir a origem se quiser, ex: ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------
# EVENTO DE INICIALIZAÇÃO
# ---------------------------
@app.on_event("startup")
def startup_event():
    analyzer.init_models()


# ---------------------------
# ROTA: Buscar documentos reprovados
# ---------------------------
@app.get("/documentos_reprovados")
async def documentos_reprovados(candidato_id: str = Query(...)):
    config = analyzer.load_config()
    try:
        conn = psycopg2.connect(**config["db_credentials"])
        cur = conn.cursor()

        cur.execute("""
            SELECT d.arquivo, d.qualidade, d.categoria, d.dados_extraidos
            FROM documentos d
            JOIN lotes l ON d.lote_fk = l.id
            WHERE d.id_candidate = %s AND d.qualidade NOT LIKE 'Aprovado%%'
            ORDER BY l.id DESC
        """, (candidato_id,))

        rows = cur.fetchall()
        cur.close()
        conn.close()

        documentos = [
            {"arquivo": r[0], "status": r[1], "categoria": r[2], "dados_extraidos": r[3]}
            for r in rows
        ]
        return {"reprovados": documentos}

    except Exception as e:
        return {"erro": str(e)}


# ---------------------------
# ROTA: Processar documentos enviados
# ---------------------------
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
            # Se a qualidade não for aprovada, marca explicitamente como reprovado por qualidade ruim
            if qualidade.strip().lower().startswith("reprovado"):
                qualidade = "Reprovado (Qualidade ruim)"
                categoria = "N/A"
                dados_extraidos = None
            else:
                categoria = analyzer.classify_document_with_ocr(tmp_path, config)
                if categoria in ["Outros", "Erro OCR", "Erro Leitura Imagem"]:
                    if categoria == "Erro OCR" or categoria == "Erro Leitura Imagem":
                        qualidade = "Reprovado (Erro OCR)"
                    else:
                        qualidade = "Reprovado (Não identificado)"
                    dados_extraidos = None
                else:
                    dados_extraidos = analyzer.extract_data(tmp_path, categoria, config)
            resultados.append({
                "arquivo": filename,
                "qualidade": qualidade,
                "categoria": categoria,
                "dados_extraidos": dados_extraidos,
                "caminho": tmp_path,
                "candidato_id": candidato_id
            })
        finally:
            os.remove(tmp_path)

    # Gera sumário e salva no banco
    batch_summary = analyzer.generate_batch_summary(batch_id, resultados, config)
    analyzer.manage_db_connection(config, batch_id, batch_summary, resultados)

    # Atualiza o candidato para etapa 4 (Análise)
    if candidato_id:
        try:
            conn = psycopg2.connect(**config["db_credentials"])
            cur = conn.cursor()
            cur.execute("UPDATE candidate SET step = 4 WHERE id = %s", (candidato_id,))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Erro ao atualizar step do candidato: {e}")

    return JSONResponse(content={"resultados": resultados})


# ---------------------------
# TESTE / HOME
# ---------------------------
@app.get("/")
def home():
    return {"mensagem": "API de análise de documentos está rodando corretamente!"}


# ---------------------------
# PARA EXECUTAR:
# ---------------------------
# uvicorn app:app --host 0.0.0.0 --port 5003
