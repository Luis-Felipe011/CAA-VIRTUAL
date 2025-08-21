from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Pasta raiz do backend (onde este arquivo está)
BASE_DIR = Path(__file__).parent

# Pasta com seus PDFs
PDF_DIR = BASE_DIR / "pdfs"

# Diretório onde o Chroma irá persistir
PERSIST_DIR = BASE_DIR / "chroma_base_pdf"


# Configurações de split/chunking
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

# Carrega e processa todos os PDFs da pasta
all_chunks = []
for pdf_path in PDF_DIR.glob("*.pdf"):
    print(f"📄 Processando {pdf_path.name}...")
    docs = PyPDFLoader(str(pdf_path)).load()
    chunks = splitter.split_documents(docs)
    all_chunks.extend(chunks)

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
# Cria ou atualiza a base vetorial com Chroma
Chroma.from_documents(
    documents=all_chunks,
    embedding=embeddings,
    persist_directory=str(PERSIST_DIR)
)

print("✅ Base vetorial criada/atualizada com sucesso!")