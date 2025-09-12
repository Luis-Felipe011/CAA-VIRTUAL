# backend/services/embeddings_service.py
"""
Embeddings e indexação (RAG) usando Gemini + Chroma.

- Carrega variáveis do backend/.env
- Fornece um wrapper de embeddings compatível com Chroma (assinatura __call__(self, input))
- Função gerar_base_vetorial() para popular a coleção com chunks de arquivos do DOCS_DIR
"""

from dotenv import load_dotenv
from pathlib import Path

# Carrega primeiro backend/.env; depois services/.env se existir (sem sobrescrever)
BASE_DIR = Path(__file__).resolve().parents[1]  # .../backend
load_dotenv(BASE_DIR / ".env")                  # backend/.env
load_dotenv(Path(__file__).resolve().parent / ".env", override=False)  # opcional

import os
import glob
from typing import List, Iterable, Union, Dict, Any

import google.generativeai as genai

# -----------------------
# Config
# -----------------------
API_KEY = os.getenv("GEMINI_API_KEY")
EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "text-embedding-004")
DOCS_DIR = os.getenv("DOCS_DIR", "data/docs")
CHROMA_PATH = os.getenv("CHROMA_PATH", "data/chroma")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "docs")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY não definida no .env")

genai.configure(api_key=API_KEY)

# -----------------------
# Embeddings helpers
# -----------------------
def _embed_batch(texts: List[str]) -> List[List[float]]:
    """Gera embeddings com Gemini (um vetor por texto)."""
    vecs: List[List[float]] = []
    for t in texts:
        r = genai.embed_content(model=EMBED_MODEL, content=(t or ""))
        vecs.append(r["embedding"])
    return vecs

def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embeddings para uma lista de textos."""
    return _embed_batch(texts)

def embed_query(text: str) -> List[float]:
    """Embedding para uma única consulta."""
    return _embed_batch([text])[0]

# Tipagem opcional para casar com Chroma (não é obrigatória em runtime)
try:
    from chromadb.api.types import Documents, Embeddings  # type: ignore
except Exception:
    Documents = list   # type: ignore
    Embeddings = list  # type: ignore

class GeminiEmbeddingFunction:
    """
    Wrapper compatível com Chroma.
    IMPORTANTE: o parâmetro do __call__ deve se chamar exatamente 'input'.
    """
    def __call__(self, input: Documents) -> Embeddings:  # noqa: A003
        if isinstance(input, str):
            texts = [input]
        else:
            texts = list(input or [])
        return _embed_batch(texts)

# >>> Objeto a ser passado como embedding_function no Chroma
embeddings = GeminiEmbeddingFunction()

# -----------------------
# Indexação (base vetorial)
# -----------------------
def _read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def _read_pdf_file(path: str) -> str:
    """Leitura simples de PDF (se pypdf estiver instalado)."""
    try:
        import pypdf  # pip install pypdf
    except Exception:
        return ""  # ignora PDFs se não houver pypdf
    try:
        reader = pypdf.PdfReader(path)
        texts = []
        for page in reader.pages:
            t = page.extract_text() or ""
            if t.strip():
                texts.append(t)
        return "\n".join(texts)
    except Exception:
        return ""

def _chunk(text: str, max_chars: int = 1500, overlap: int = 200) -> List[str]:
    """Divide o texto em pedaços com overlap para melhor contexto."""
    text = text.replace("\r", "")
    chunks: List[str] = []
    i = 0
    n = len(text)
    while i < n:
        end = min(i + max_chars, n)
        chunks.append(text[i:end])
        if end == n:
            break
        i = max(0, end - overlap)
    return chunks

def gerar_base_vetorial(
    docs_dir: str | None = None,
    chroma_path: str | None = None,
    collection_name: str | None = None,
) -> Dict[str, Any]:
    """
    Varre DOCS_DIR, quebra arquivos em chunks e adiciona na coleção Chroma.
    Usa embeddings do Gemini via 'embeddings' (wrapper compatível).
    """
    try:
        import chromadb  # pip install chromadb
    except ImportError as e:
        raise RuntimeError(
            "chromadb não instalado. Instale com: pip install chromadb"
        ) from e

    docs_dir = docs_dir or DOCS_DIR
    chroma_path = chroma_path or CHROMA_PATH
    collection_name = collection_name or COLLECTION_NAME

    # Inicializa Chroma
    client = chromadb.PersistentClient(path=chroma_path)
    coll = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embeddings,  # nosso wrapper
    )

    # Coleta arquivos
    patterns = ("*.txt", "*.md", "*.csv", "*.json", "*.pdf")
    files: List[str] = []
    for p in patterns:
        files.extend(glob.glob(os.path.join(docs_dir, "**", p), recursive=True))

    total_files = 0
    total_chunks = 0

    ids: List[str] = []
    docs: List[str] = []
    metas: List[Dict[str, Any]] = []

    for fp in files:
        ext = os.path.splitext(fp)[1].lower()
        if ext == ".pdf":
            text = _read_pdf_file(fp)
        else:
            try:
                text = _read_text_file(fp)
            except Exception:
                text = ""

        if not text.strip():
            continue

        total_files += 1
        title = os.path.basename(fp)
        chunks = _chunk(text)
        for idx, ch in enumerate(chunks):
            ids.append(f"{title}-{idx}")
            docs.append(ch)
            metas.append({"title": title, "path": fp, "chunk": idx})

        # Flush em lotes para não acumular demais
        if len(ids) >= 256:
            coll.add(documents=docs, metadatas=metas, ids=ids)
            total_chunks += len(ids)
            ids, docs, metas = [], [], []

    # Adiciona o resto
    if ids:
        coll.add(documents=docs, metadatas=metas, ids=ids)
        total_chunks += len(ids)

    return {
        "docs_dir": docs_dir,
        "chroma_path": chroma_path,
        "collection": collection_name,
        "arquivos_processados": total_files,
        "chunks_adicionados": total_chunks,
    }
