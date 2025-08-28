from pathlib import Path

# Diretório base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Diretório para persistência do Chroma DB
CHROMA_DIR = BASE_DIR / "chroma_base_pdf"
CHROMA_DIR.mkdir(exist_ok=True)

# Pasta com seus PDFs
PDF_DIR = BASE_DIR / "pdfs"

# Nome do modelo de embeddings
EMBEDDINGS_MODEL_NAME = "multi-qa-mpnet-base-dot-v1"

# Comando e modelo do Ollama
OLLAMA_COMMAND = "ollama"
OLLAMA_MODEL = "mistral"
