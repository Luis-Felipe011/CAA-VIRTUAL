# --- 1. IMPORTAÇÕES PRIMEIRO ---
from fastapi import FastAPI, UploadFile, File, Form, Request, Query, BackgroundTasks, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
import tempfile
import os
import uuid
import shutil # Importado para criar e mover pastas
import psycopg2 
import json
from backend.document_parsing import analyzer

# --- 2. CRIAR A INSTÂNCIA DO APP ---
app = FastAPI()

# --- 3. ADICIONAR MIDDLEWARE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ou especifique ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 4. CONFIGURAR EVENTOS DE STARTUP ---
@app.on_event("startup")
def startup_event():
    # Carrega os modelos UMA VEZ no processo principal
    # Isso permite que o analyzer use ThreadPoolExecutor sem travar
    print("Iniciando o servidor FastAPI...")
    print("Carregando modelos de IA (EasyOCR e Donut)... Isso pode demorar.")
    analyzer.init_models()
    print("Modelos de IA carregados com sucesso. Servidor pronto.")

# --- 5. DEFINIR ENDPOINTS ---

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
    background_tasks: BackgroundTasks, # Para rodar em segundo plano
    files: List[UploadFile] = File(...)
):
    form = await request.form()
    candidato_id = form.get("candidato_id") # O ID do candidato (UUID)
    
    if not candidato_id:
        return JSONResponse(status_code=400, content={"erro": "candidato_id é obrigatório."})

    config = analyzer.load_config()
    if not config:
        return JSONResponse(status_code=500, content={"erro": "Configuração do analisador não encontrada"})

    # 1. Cria um ID de lote único
    batch_id = f"{candidato_id}_{uuid.uuid4().hex[:8]}"
    
    # 2. Cria a pasta de lote temporária
    input_folder_base = config["folder_paths"]["input"]
    batch_folder_path = os.path.join(input_folder_base, batch_id)
    
    try:
        os.makedirs(batch_folder_path, exist_ok=True)
    except Exception as e:
        return JSONResponse(status_code=500, content={"erro": f"Não foi possível criar pasta do lote: {e}"})

    # 3. Salva os arquivos
    for file in files:
        file_path = os.path.join(batch_folder_path, file.filename)
        try:
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
        except Exception as e:
            shutil.rmtree(batch_folder_path) # Limpa em caso de falha
            return JSONResponse(status_code=500, content={"erro": f"Falha ao salvar o arquivo {file.filename}: {e}"})

    # 4. Agenda a tarefa pesada (analyzer.py)
    background_tasks.add_task(analyzer.run_analysis_for_batch, batch_id, candidato_id)
    
    # 5. Atualiza o step
    try:
        conn = psycopg2.connect(**config["db_credentials"])
        cur = conn.cursor()
        cur.execute("UPDATE candidate SET step = 4 WHERE id = %s", (candidato_id,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro ao atualizar step do candidato: {e}")

    # 6. Retorna a resposta IMEDIATAMENTE
    return JSONResponse(
        status_code=202,
        content={
            "status": "processamento_iniciado",
            "message": "Os documentos foram recebidos e estão sendo processados.",
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
            return JSONResponse(status_code=200, content={"status": "processando", "message": "Lote não encontrado ou ainda não salvo."})

        sumario = lote_row[0]
        
        cur.execute("""
            SELECT arquivo, qualidade, categoria, dados_extraidos
            FROM documentos d
            JOIN lotes l ON d.lote_fk = l.id
            WHERE l.lote_id = %s
        """, (batch_id,))
        
        doc_rows = cur.fetchall()
        documentos = [
            {"arquivo": r[0], "qualidade": r[1], "categoria": r[2], "dados_extraidos": r[3]} for r in doc_rows
        ]
        
        cur.close()
        conn.close()
        
        return {
            "status": "concluido",
            "batch_id": batch_id,
            "sumario": sumario,
            "documentos": documentos
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"erro": str(e)})

# --- NOVOS ENDPOINTS (QUE ESTAVAM FALTANDO PARA O RESULTADO.TSX) ---

@app.get("/candidato/{candidato_id}/todos_documentos")
async def get_todos_documentos_candidato(candidato_id: str):
    """Retorna o último processamento de CADA arquivo do candidato."""
    config = analyzer.load_config()
    try:
        conn = psycopg2.connect(**config["db_credentials"])
        cur = conn.cursor()
        # Pega o registro mais recente de cada arquivo único para este candidato
        cur.execute("""
            SELECT DISTINCT ON (d.arquivo) 
                d.arquivo, d.qualidade, d.categoria, d.dados_extraidos
            FROM documentos d
            WHERE d.id_candidate = %s
            ORDER BY d.arquivo, d.id DESC
        """, (candidato_id,))
        
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        documentos = [
            {"arquivo": r[0], "qualidade": r[1], "categoria": r[2], "dados_extraidos": r[3]} for r in rows
        ]
        return {"documentos": documentos}
    except Exception as e:
        return JSONResponse(status_code=500, content={"erro": str(e)})

@app.patch("/documento/dados")
async def atualizar_dados_documento(request: Request):
    """Atualiza o JSON de dados extraídos de um documento específico."""
    data = await request.json()
    candidato_id = data.get("candidato_id")
    arquivo = data.get("arquivo")
    novos_dados = data.get("dados")

    if not candidato_id or not arquivo or not novos_dados:
        return JSONResponse(status_code=400, content={"erro": "Dados incompletos"})

    config = analyzer.load_config()
    try:
        conn = psycopg2.connect(**config["db_credentials"])
        cur = conn.cursor()
        
        # Atualiza o registro mais recente deste arquivo para este candidato
        cur.execute("""
            UPDATE documentos
            SET dados_extraidos = %s
            WHERE id = (
                SELECT id FROM documentos
                WHERE id_candidate = %s AND arquivo = %s
                ORDER BY id DESC
                LIMIT 1
            )
        """, (json.dumps(novos_dados, ensure_ascii=False), candidato_id, arquivo))
        
        conn.commit()
        updated_rows = cur.rowcount
        cur.close()
        conn.close()
        
        if updated_rows == 0:
             return JSONResponse(status_code=404, content={"erro": "Documento não encontrado no banco."})

        return {"status": "sucesso", "mensagem": "Dados atualizados com sucesso"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"erro": str(e)})

# Para rodar: uvicorn app:app --host 0.0.0.0 --port 5003