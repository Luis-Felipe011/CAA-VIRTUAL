# --- 1. IMPORTAÇÕES PRIMEIRO ---
from fastapi import FastAPI, UploadFile, File, Form, Request, Query, BackgroundTasks, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # <--- NOVO IMPORT
from fastapi.responses import JSONResponse
from typing import List
import tempfile
import os
import uuid
import shutil 
import psycopg2 
import json
from backend.document_parsing import analyzer

# --- 2. CRIAR A INSTÂNCIA DO APP ---
app = FastAPI()

# --- 3. ADICIONAR MIDDLEWARE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURAÇÃO DE IMAGENS (NOVA) ---
# Isso torna a pasta "documentos_processados" acessível via navegador
# Exemplo: http://localhost:5003/imagens/lote_xyz/1.jpg
os.makedirs("documentos_processados", exist_ok=True) # Garante que a pasta existe
app.mount("/imagens", StaticFiles(directory="documentos_processados"), name="imagens")

# --- 4. CONFIGURAR EVENTOS DE STARTUP ---
@app.on_event("startup")
def startup_event():
    print("Iniciando o servidor FastAPI...")
    print("Carregando modelos de IA... Isso pode demorar.")
    analyzer.init_models()
    print("Modelos carregados. Servidor pronto na porta 5003.")

# ... (MANTENHA O RESTO DOS ENDPOINTS IGUAIS: documentos_reprovados, processar_documentos, etc.) ...

# --- A ÚNICA OUTRA MUDANÇA É NO get_resultado_lote e get_todos_documentos ---
# (Mas na verdade, o frontend vai construir a URL sozinho, então não precisa mudar a lógica aqui)

# ... (MANTENHA O RESTO DO CÓDIGO ATÉ O FINAL) ...
@app.get("/documentos_reprovados")
async def documentos_reprovados(candidato_id: str = Query(...)):
    config = analyzer.load_config()
    try:
        conn = psycopg2.connect(**config["db_credentials"])
        cur = conn.cursor()
        cur.execute("""
            SELECT d.arquivo, d.qualidade, d.categoria, d.dados_extraidos
            FROM documentos d
            WHERE d.id_candidate = %s AND d.qualidade NOT LIKE 'Aprovado%%'
        """, (candidato_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        documentos = [
            {"arquivo": r[0], "qualidade": r[1], "categoria": r[2], "dados_extraidos": r[3]} for r in rows
        ]
        return {"reprovados": documentos}
    except Exception as e:
        return {"erro": str(e)}

@app.post("/processar_documentos")
async def processar_documentos(
    request: Request, 
    background_tasks: BackgroundTasks, 
    files: List[UploadFile] = File(...)
):
    form = await request.form()
    candidato_id = form.get("candidato_id")
    
    if not candidato_id:
        return JSONResponse(status_code=400, content={"erro": "candidato_id é obrigatório."})

    print(f"--> Upload recebido para: {candidato_id}")
    config = analyzer.load_config()
    batch_id = f"{candidato_id}_{uuid.uuid4().hex[:8]}"
    input_folder_base = config["folder_paths"]["input"]
    batch_folder_path = os.path.join(input_folder_base, batch_id)
    
    os.makedirs(batch_folder_path, exist_ok=True)

    for file in files:
        file_path = os.path.join(batch_folder_path, file.filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

    background_tasks.add_task(analyzer.run_analysis_for_batch, batch_id, candidato_id)
    
    try:
        conn = psycopg2.connect(**config["db_credentials"])
        cur = conn.cursor()
        cur.execute("SELECT id FROM candidate WHERE id = %s", (candidato_id,))
        if cur.fetchone():
            cur.execute("UPDATE candidate SET step = 4 WHERE id = %s", (candidato_id,))
            conn.commit()
        cur.close()
        conn.close()
    except Exception:
        pass

    return JSONResponse(
        status_code=202, 
        content={"status": "processamento_iniciado", "batch_id": batch_id}
    )

@app.get("/resultado_lote/{batch_id}")
async def get_resultado_lote(batch_id: str = Path(...)):
    config = analyzer.load_config()
    try:
        conn = psycopg2.connect(**config["db_credentials"])
        cur = conn.cursor()
        
        cur.execute("SELECT sumario FROM lotes WHERE lote_id = %s", (batch_id,))
        lote_row = cur.fetchone()
        
        if not lote_row:
            return JSONResponse(status_code=200, content={"status": "processando"})

        sumario = lote_row[0]
        return {"status": "concluido", "batch_id": batch_id, "sumario": sumario}
    except Exception as e:
        return JSONResponse(status_code=500, content={"erro": str(e)})

@app.get("/candidato/{candidato_id}/todos_documentos")
async def get_todos_documentos_candidato(candidato_id: str):
    print(f"--> Buscando docs para: {candidato_id}")
    config = analyzer.load_config()
    try:
        conn = psycopg2.connect(**config["db_credentials"])
        cur = conn.cursor()
        
        # Busca também o lote_id para construirmos a URL da imagem
        cur.execute("""
            SELECT DISTINCT ON (d.arquivo) 
                d.id, d.arquivo, d.qualidade, d.categoria, d.dados_extraidos, l.lote_id
            FROM documentos d
            JOIN lotes l ON d.lote_fk = l.id
            WHERE d.id_candidate = %s
            ORDER BY d.arquivo, d.id DESC
        """, (candidato_id,))
        
        rows = cur.fetchall()
        
        if not rows:
            print("--> [AVISO] Lista vazia. Buscando fallback (últimos 5).")
            cur.execute("""
                SELECT d.id, d.arquivo, d.qualidade, d.categoria, d.dados_extraidos, l.lote_id
                FROM documentos d
                JOIN lotes l ON d.lote_fk = l.id
                ORDER BY d.id DESC
                LIMIT 5
            """)
            rows = cur.fetchall()

        cur.close()
        conn.close()
        
        documentos = [
            {
                "id": r[0], 
                "arquivo": r[1], 
                "qualidade": r[2], 
                "categoria": r[3], 
                "dados_extraidos": r[4],
                "lote_id": r[5] # Novo campo necessário para a URL
            } for r in rows
        ]
        return {"documentos": documentos}
    except Exception as e:
        print(f"[ERRO BUSCA] {e}")
        return JSONResponse(status_code=500, content={"erro": str(e)})

@app.patch("/documento/dados")
async def atualizar_dados_documento(request: Request):
    data = await request.json()
    doc_id = data.get("documento_id") 
    novos_dados = data.get("dados")

    if not doc_id or not novos_dados:
        return JSONResponse(status_code=400, content={"erro": "ID ou dados faltando."})

    config = analyzer.load_config()
    try:
        conn = psycopg2.connect(**config["db_credentials"])
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE documentos
            SET dados_extraidos = %s::jsonb
            WHERE id = %s
        """, (json.dumps(novos_dados, ensure_ascii=False), doc_id))
        
        conn.commit()
        updated = cur.rowcount
        cur.close()
        conn.close()
        
        if updated == 0:
             return JSONResponse(status_code=404, content={"erro": "Documento não encontrado."})

        return {"status": "sucesso", "mensagem": "Dados atualizados com sucesso"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"erro": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5003)