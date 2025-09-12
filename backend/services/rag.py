import os, glob, math
from .embeddings_service import embed_query, embed_texts

DOCS_DIR   = os.getenv("DOCS_DIR", "data/docs")
CHROMA_PATH= os.getenv("CHROMA_PATH", "data/chroma")
TOP_K      = int(os.getenv("TOP_K", "4"))

def _cos(a, b):
    dot = sum(x*y for x, y in zip(a,b))
    na = sum(x*x for x in a) ** 0.5
    nb = sum(x*x for x in b) ** 0.5
    return 0.0 if not na or not nb else dot/(na*nb)

def _buscar_chroma(query, k):
    try:
        import chromadb
    except ImportError:
        return None
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    coll = client.get_or_create_collection("docs")  # ajuste se seu nome for outro
    qv = embed_query(query)
    res = coll.query(query_embeddings=[qv], n_results=k, include=["metadatas","documents"])
    hits=[]
    for i in range(len(res["ids"][0])):
        hits.append({
            "title": (res["metadatas"][0][i] or {}).get("title") or f"doc_{i}",
            "content": res["documents"][0][i]
        })
    return hits

def _load_local_texts():
    exts = ("*.txt","*.md","*.csv","*.json")
    files=[]
    for e in exts:
        files += glob.glob(os.path.join(DOCS_DIR,"**",e), recursive=True)
    docs=[]
    for fp in files:
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                docs.append({"title": os.path.basename(fp), "content": f.read()})
        except Exception:
            pass
    return docs

def _buscar_local(query, k):
    docs = _load_local_texts()
    if not docs: return []
    qv = embed_query(query)
    ev = embed_texts([d["content"][:8000] for d in docs])
    scored = [(_cos(qv,v), d) for d,v in zip(docs,ev)]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [d for _,d in scored[:k]]

def buscar_docs_relevantes(query: str, k: int = TOP_K):
    hits = _buscar_chroma(query, k)
    if hits is None:
        hits = _buscar_local(query, k)
    partes = []
    for h in hits:
        partes.append(f"[{h['title']}]\n{h['content'][:2500]}\n")
    return "\n---\n".join(partes) if partes else "Nenhum contexto encontrado."
