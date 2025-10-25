
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List
import tempfile
import os
from backend.document_parsing import analyzer
import uuid

app = FastAPI()

@app.on_event("startup")
def startup_event():
    analyzer.init_models()

@app.post("/processar_documentos")
async def processar_documentos(files: List[UploadFile] = File(...)):
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
    return JSONResponse(content={"resultados": resultados})

# Para rodar: uvicorn app:app --host 0.0.0.0 --port 5002
