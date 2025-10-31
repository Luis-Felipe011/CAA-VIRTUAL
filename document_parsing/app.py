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
    # O init_models() agora é chamado dentro de cada processo-filho 
    # pelo analyzer.py, então não precisamos chamar aqui, 
    # mas carregar a config é uma boa ideia.
    config = analyzer.load_config()
    if config:
        print("Configuração carregada com sucesso.")
    else:
        print("ERRO: Não foi possível carregar a configuração no startup.")

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

# --- ENDPOINT /processar_documentos (REFEITO PARA USAR BACKGROUND TASKS) ---
@app.post("/processar_documentos")
async def processar_documentos(
    request: Request, 
    background_tasks: BackgroundTasks, # Para rodar em segundo plano
    files: List[UploadFile] = File(...)
):
    form = await request.form()
    candidato_id = form.get("candidato_id") # Opcional
    
    config = analyzer.load_config()
    if not config:
        return JSONResponse(status_code=500, content={"erro": "Configuração do analisador não encontrada"})

    # 1. Cria um ID de lote único
    # Usamos o candidato_id se ele existir, para rastreamento
    if candidato_id:
        batch_id = f"{candidato_id}_{uuid.uuid4().hex[:8]}"
    else:
        batch_id = f"api_batch_{uuid.uuid4().hex[:8]}"
    
    # 2. Cria a pasta de lote temporária (onde o analyzer espera)
    input_folder_base = config["folder_paths"]["input"]
    batch_folder_path = os.path.join(input_folder_base, batch_id)
    
    try:
        os.makedirs(batch_folder_path, exist_ok=True)
    except Exception as e:
        return JSONResponse(status_code=500, content={"erro": f"Não foi possível criar pasta do lote: {e}"})

    # 3. Salva os arquivos (upload) DENTRO da pasta do lote
    for file in files:
        file_path = os.path.join(batch_folder_path, file.filename)
        try:
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
        except Exception as e:
            # Em caso de falha, limpa a pasta e retorna erro
            shutil.rmtree(batch_folder_path)
            return JSONResponse(status_code=500, content={"erro": f"Falha ao salvar o arquivo {file.filename}: {e}"})

    # 4. Agenda a tarefa pesada (analyzer.py) para rodar em segundo plano
    # O analyzer.py fará todo o trabalho: paralelismo, salvar no DB, e mover a pasta
    background_tasks.add_task(analyzer.run_analysis_for_batch, batch_id)
    
    # 5. (Opcional) Atualiza o step do candidato IMEDIATAMENTE
    if candidato_id:
        try:
            conn = psycopg2.connect(**config["db_credentials"])
            cur = conn.cursor()
            cur.execute("UPDATE candidate SET step = 4 WHERE id = %s", (candidato_id,))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Erro ao atualizar step do candidato: {e}") # Não retorna erro, só loga

    # 6. Retorna a resposta IMEDIATAMENTE para o frontend
    return JSONResponse(
        status_code=202, # 202 "Accepted" (Aceito)
        content={
            "status": "processamento_iniciado",
            "message": "Os documentos foram recebidos e estão sendo processados.",
            "batch_id": batch_id
        }
    )

# --- NOVO ENDPOINT: Para o frontend buscar o resultado ---
@app.get("/resultado_lote/{batch_id}")
async def get_resultado_lote(batch_id: str = Path(...)):
    """
    Consulta o banco de dados para ver o resultado de um lote 
    que foi processado em segundo plano.
    """
    config = analyzer.load_config()
    try:
        conn = psycopg2.connect(**config["db_credentials"])
        cur = conn.cursor()
        
        # 1. Busca o sumário do lote
        cur.execute("SELECT sumario FROM lotes WHERE lote_id = %s", (batch_id,))
        lote_row = cur.fetchone()
        
        if not lote_row:
            return JSONResponse(status_code=404, content={"status": "nao_encontrado", "message": "Lote não encontrado ou ainda não salvo."})

        sumario = lote_row[0]
        
        # 2. Busca os documentos processados
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

# Para rodar: uvicorn app:app --host 0.0.0.0 --port 5002