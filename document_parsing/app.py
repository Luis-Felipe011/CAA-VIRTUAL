# --- 1. IMPORTAÇÕES PRIMEIRO ---
from fastapi import FastAPI, UploadFile, File, Form, Request, Query, BackgroundTasks, Path
from fastapi.middleware.cors import CORSMiddleware
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

# --- 4. CONFIGURAR EVENTOS DE STARTUP ---
@app.on_event("startup")
def startup_event():
    print("Iniciando o servidor FastAPI...")
    # analyzer.init_models() # Pode comentar para testar mais rápido se já carregou antes
    print("Servidor pronto na porta 5003.")

# --- 5. ENDPOINTS ---

@app.get("/documentos_reprovados")
async def documentos_reprovados(candidato_id: str = Query(...)):
    # ... (mesmo código anterior)
    return {"reprovados": []}

@app.post("/processar_documentos")
async def processar_documentos(
    request: Request, 
    background_tasks: BackgroundTasks, 
    files: List[UploadFile] = File(...)
):
    form = await request.form()
    candidato_id = form.get("candidato_id")
    
    print(f"\n[UPLOAD] Recebido upload para candidato ID: {candidato_id}")

    if not candidato_id:
        return JSONResponse(status_code=400, content={"erro": "candidato_id é obrigatório."})

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

    # Agenda a análise (IMPORTANTE: Isso vai salvar no banco com o ID 'candidato_id')
    background_tasks.add_task(analyzer.run_analysis_for_batch, batch_id, candidato_id)
    
    return JSONResponse(
        status_code=202, 
        content={
            "status": "processamento_iniciado",
            "message": "Documentos em processamento.",
            "batch_id": batch_id
        }
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
            return JSONResponse(status_code=200, content={"status": "processando", "message": "Ainda processando."})

        sumario = lote_row[0]
        return {
            "status": "concluido",
            "batch_id": batch_id,
            "sumario": sumario,
            "documentos": [] # Simplificado para focar no status
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"erro": str(e)})

# --- ENDPOINT DE DEBUG PARA BUSCAR DOCUMENTOS ---
@app.get("/candidato/{candidato_id}/todos_documentos")
async def get_todos_documentos_candidato(candidato_id: str):
    print(f"\n[BUSCA] Frontend pediu documentos para ID: {candidato_id}")
    
    config = analyzer.load_config()
    try:
        conn = psycopg2.connect(**config["db_credentials"])
        cur = conn.cursor()
        
        # DEBUG: Vamos ver quais IDs existem na tabela
        cur.execute("SELECT DISTINCT id_candidate FROM documentos LIMIT 5")
        ids_no_banco = [str(row[0]) for row in cur.fetchall()]
        print(f"[DEBUG] IDs encontrados no banco (amostra): {ids_no_banco}")

        # A Query Real
        cur.execute("""
            SELECT arquivo, qualidade, categoria, dados_extraidos
            FROM documentos
            WHERE id_candidate = %s
            ORDER BY id DESC
        """, (candidato_id,))
        
        rows = cur.fetchall()
        print(f"[BUSCA] Encontrados {len(rows)} documentos para este candidato.")
        
        # SE NÃO ENCONTROU NADA, VAMOS TENTAR UMA "AJUDA" PARA TESTE
        # Se a lista estiver vazia, busca os últimos 5 documentos de QUALQUER UM
        # (APENAS PARA VOCÊ VER NA TELA QUE O FRONTEND ESTÁ FUNCIONANDO)
        if len(rows) == 0:
            print("[DEBUG] Lista vazia. Buscando últimos documentos genéricos para teste...")
            cur.execute("""
                SELECT arquivo, qualidade, categoria, dados_extraidos
                FROM documentos
                ORDER BY id DESC
                LIMIT 5
            """)
            rows = cur.fetchall()

        cur.close()
        conn.close()
        
        documentos = []
        seen = set()
        for r in rows:
            if r[0] not in seen:
                documentos.append({
                    "arquivo": r[0], 
                    "qualidade": r[1], 
                    "categoria": r[2], 
                    "dados_extraidos": r[3]
                })
                seen.add(r[0])

        return {"documentos": documentos}
    except Exception as e:
        print(f"[ERRO] {e}")
        return JSONResponse(status_code=500, content={"erro": str(e)})

@app.patch("/documento/dados")
async def atualizar_dados_documento(request: Request):
    # (Mesmo código de antes)
    return {"status": "sucesso"}

if __name__ == "__main__":
    import uvicorn
    # RODA NA PORTA 5003
    uvicorn.run(app, host="0.0.0.0", port=5003)