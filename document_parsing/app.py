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

# --- 4. CONFIGURAR EVENTOS DE STARTUP (CORRIGIDO) ---
@app.on_event("startup")
def startup_event():
    # --- CORREÇÃO AQUI ---
    # Com o ThreadPoolExecutor, os modelos DEVEM ser carregados
    # uma vez no processo principal (a API) ao iniciar.
    print("Iniciando o servidor FastAPI...")
    print("Carregando modelos de IA (EasyOCR e Donut)... Isso pode demorar.")
    analyzer.init_models()
    print("Modelos de IA carregados com sucesso. Servidor pronto.")
    # --- FIM DA CORREÇÃO ---

# --- 5. DEFINIR ENDPOINTS ---

@app.get("/documentos_reprovados")
async def documentos_reprovados(candidato_id: str = Query(...)):
    config = analyzer.load_config()
    try:
        conn = psycopg2.connect(**config["db_credentials"])
        cur = conn.cursor()
        # A sua query SQL para a nova tabela
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

# --- ENDPOINT /processar_documentos (REFEITO PARA USAR BACKGROUND TASKS) ---
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
            shutil.rmtree(batch_folder_path) # Limpa em caso de falha
            return JSONResponse(status_code=500, content={"erro": f"Falha ao salvar o arquivo {file.filename}: {e}"})

    # 4. Agenda a tarefa pesada (analyzer.py) para rodar em segundo plano
    #    *** AQUI PASSAMOS O candidato_id PARA O ANALYZER ***
    background_tasks.add_task(analyzer.run_analysis_for_batch, batch_id, candidato_id)
    
    # 5. Atualiza o step do candidato IMEDIATAMENTE
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
            # Isso não é um erro, apenas significa que o processamento (que está em background)
            # ainda não terminou e não salvou no banco.
            return JSONResponse(status_code=200, content={"status": "processando", "message": "O lote ainda está sendo processado."})

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

# Para rodar: uvicorn app:app --host 0.0.0.0 --port 5003