# backend/services/rag.py
import os, glob
from .embeddings_service import embed_query, embed_texts

DOCS_DIR    = os.getenv("DOCS_DIR", "data/docs")
CHROMA_PATH = os.getenv("CHROMA_PATH", "data/chroma")
TOP_K       = int(os.getenv("TOP_K", "4"))

def _cos(a, b):
    dot = sum(x*y for x, y in zip(a,b))
    na = sum(x*x for x in a) ** 0.5
    nb = sum(x*x for x in b) ** 0.5
    return 0.0 if not na or not nb else dot/(na*nb)

def _buscar_chroma(query, k):
    try:
        import chromadb
        from chromadb.config import Settings
    except Exception:
        return None

    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH, settings=Settings(anonymized_telemetry=False))
        coll = client.get_or_create_collection(name=os.getenv("CHROMA_COLLECTION", "docs"))
        qv = embed_query(query)
        res = coll.query(query_embeddings=[qv], n_results=k)
        hits = []
        for i in range(len(res["ids"][0])):
            hits.append({
                "title": (res["metadatas"][0][i] or {}).get("title") or f"doc_{i}",
                "content": res["documents"][0][i]
            })
        return hits
    except Exception:
        return None

def _load_local_texts():
    exts = ("*.txt","*.md","*.csv","*.json")
    files = []
    for e in exts:
        files += glob.glob(os.path.join(DOCS_DIR,"**",e), recursive=True)
    docs = []
    for fp in files:
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                docs.append({"title": os.path.basename(fp), "content": f.read()})
        except Exception:
            pass
    print("[RAG] Arquivos carregados:", [d['title'] for d in docs])
    return docs

def _buscar_local(query, k):
    docs = _load_local_texts()
    if not docs:
        return []
    qv = embed_query(query)
    # Novo: busca linha/parágrafo mais relevante em cada doc
    melhores = []
    for d in docs:
        linhas = [l.strip() for l in d["content"].splitlines() if l.strip()]
        if not linhas:
            continue
        ev = embed_texts(linhas)
        scored = [(_cos(qv, v), l) for l, v in zip(linhas, ev)]
        scored.sort(key=lambda x: x[0], reverse=True)
        melhores.append({
            "title": d["title"],
            "content": scored[0][1] if scored else ""
        })
    # Agora ranqueia os melhores trechos de todos os docs
    ev_melhores = embed_texts([m["content"] for m in melhores])
    scored_final = [(_cos(qv, v), m) for m, v in zip(melhores, ev_melhores)]
    print("[RAG] Scores de similaridade (linha):", [(score, m['title'], m['content']) for score, m in scored_final])
    scored_final.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored_final[:k]]

def buscar_docs_relevantes(query: str, k: int = TOP_K):
    # Força sempre buscar local
    hits = _buscar_local(query, k)
    partes = []
    for h in hits:
        partes.append(f"[{h['title']}]\n{h['content'][:2500]}\n")
    return "\n---\n".join(partes) if partes else "Nenhum contexto encontrado."