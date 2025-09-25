# backend/services/embeddings_service.py
"""
Embeddings e indexação (RAG) usando Gemini + Chroma.
"""
from dotenv import load_dotenv
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parents[1]  # .../backend
load_dotenv(BASE_DIR / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env", override=False)

import os, glob
from typing import List, Iterable, Union, Dict, Any
import google.generativeai as genai

API_KEY = os.getenv("GEMINI_API_KEY")
EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "text-embedding-004")
DOCS_DIR = os.getenv("DOCS_DIR", "data/docs")
CHROMA_PATH = os.getenv("CHROMA_PATH", "data/chroma")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "docs")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY não definida no .env")

genai.configure(api_key=API_KEY)

def _embed_batch(texts: List[str]) -> List[List[float]]:
    vecs: List[List[float]] = []
    for t in texts:
        r = genai.embed_content(model=EMBED_MODEL, content=(t or ""))
        vecs.append(r["embedding"])
    return vecs

def embed_texts(texts: List[str]) -> List[List[float]]:
    return _embed_batch(texts)

def embed_query(text: str) -> List[float]:
    return _embed_batch([text])[0]

try:
    from chromadb.api.types import Documents, Embeddings  # type: ignore
except Exception:
    Documents = list   # type: ignore
    Embeddings = list  # type: ignore

class GeminiEmbeddingFunction:
    def __call__(self, input: "Documents") -> "Embeddings":  # noqa: A003
        if isinstance(input, str):
            texts = [input]
        else:
            texts = list(input or [])
        return _embed_batch(texts)

embeddings = GeminiEmbeddingFunction()

# ---------- Indexação ----------
def _read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def _read_pdf_file(path: str) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
        reader = PdfReader(path)
        texts = []
        for page in reader.pages:
            t = page.extract_text() or ""
            if t.strip():
                texts.append(t)
        return "\n".join(texts)
    except Exception:
        return ""

def _chunk(text: str, max_chars: int = 1500, overlap: int = 200) -> List[str]:
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
    try:
        import chromadb
        from chromadb.config import Settings
    except Exception:
        return {"error": "chromadb não instalado"}

    docs_dir = docs_dir or DOCS_DIR
    chroma_path = chroma_path or CHROMA_PATH
    collection_name = collection_name or COLLECTION_NAME

    client = chromadb.PersistentClient(path=chroma_path, settings=Settings(anonymized_telemetry=False))
    coll = client.get_or_create_collection(name=collection_name, embedding_function=embeddings)

    exts = ("*.txt","*.md","*.csv","*.json","*.pdf")
    files: List[str] = []
    for e in exts:
        files += glob.glob(os.path.join(docs_dir,"**",e), recursive=True)

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

        if len(ids) >= 256:
            coll.add(documents=docs, metadatas=metas, ids=ids)
            total_chunks += len(ids)
            ids, docs, metas = [], [], []

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
