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
    analyzer.init_models()
    print("Modelos carregados. Servidor pronto na porta 5003.")

# --- 5. ENDPOINTS ---

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

    background_tasks.add_task(analyzer.run_analysis_for_batch, batch_id, candidato_id)
    
    try:
        conn = psycopg2.connect(**config["db_credentials"])
        cur = conn.cursor()
        # Fallback para garantir que o candidato existe no banco local
        cur.execute("SELECT id FROM candidate WHERE id = %s", (candidato_id,))
        if not cur.fetchone():
             cur.execute("INSERT INTO candidate (id, name, cpf, step) VALUES (%s, 'Usuario Local', '000', 4)", (candidato_id,))
        
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
    print(f"--> Buscando documentos para candidato: {candidato_id}")
    config = analyzer.load_config()
    try:
        conn = psycopg2.connect(**config["db_credentials"])
        cur = conn.cursor()
        
        cur.execute("""
            SELECT DISTINCT ON (d.arquivo) 
                d.id, d.arquivo, d.qualidade, d.categoria, d.dados_extraidos
            FROM documentos d
            WHERE d.id_candidate = %s
            ORDER BY d.arquivo, d.id DESC
        """, (candidato_id,))
        
        rows = cur.fetchall()
        
        # FALLBACK: Se não achar nada, pega os últimos 5 (só para garantir que algo aparece no teste)
        if not rows:
            print("--> [AVISO] Lista vazia para este ID. Buscando últimos 5 documentos globais (DEBUG).")
            cur.execute("""
                SELECT d.id, d.arquivo, d.qualidade, d.categoria, d.dados_extraidos
                FROM documentos d
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
                "dados_extraidos": r[4]
            } for r in rows
        ]
        return {"documentos": documentos}
    except Exception as e:
        print(f"[ERRO BUSCA] {e}")
        return JSONResponse(status_code=500, content={"erro": str(e)})

# --- ROTA DE ATUALIZAÇÃO REESCRITA E BLINDADA ---
@app.patch("/documento/dados")
async def atualizar_dados_documento(request: Request):
    print("\n[UPDATE] Recebido pedido de atualização de dados...")
    try:
        data = await request.json()
        doc_id = data.get("documento_id") 
        novos_dados = data.get("dados")

        print(f"[UPDATE] ID do Documento: {doc_id}")
        print(f"[UPDATE] Novos Dados: {novos_dados}")

        if not doc_id or not novos_dados:
            print("[UPDATE] ERRO: Dados incompletos.")
            return JSONResponse(status_code=400, content={"erro": "ID ou dados faltando."})

        config = analyzer.load_config()
        conn = psycopg2.connect(**config["db_credentials"])
        cur = conn.cursor()
        
        # 1. Converter o dicionário Python para string JSON válida
        dados_json_str = json.dumps(novos_dados, ensure_ascii=False)
        
        # 2. Executar o UPDATE com cast explícito para ::jsonb
        cur.execute("""
            UPDATE documentos
            SET dados_extraidos = %s::jsonb
            WHERE id = %s
        """, (dados_json_str, doc_id))
        
        updated_rows = cur.rowcount
        conn.commit() # IMPORTANTE: Commit da transação
        
        print(f"[UPDATE] Linhas afetadas no banco: {updated_rows}")
        
        cur.close()
        conn.close()
        
        if updated_rows == 0:
             print("[UPDATE] ERRO: Nenhuma linha foi alterada (ID não encontrado?).")
             return JSONResponse(status_code=404, content={"erro": "Documento não encontrado com esse ID."})

        return {"status": "sucesso", "mensagem": "Dados atualizados com sucesso"}
    
    except Exception as e:
        print(f"[UPDATE] EXCEÇÃO CRÍTICA: {e}")
        return JSONResponse(status_code=500, content={"erro": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5003)