# backend/services/chroma.py
import os
from typing import Tuple

from .embeddings_service import embeddings  # wrapper compatível

CHROMA_PATH = os.getenv("CHROMA_PATH", "data/chroma")

def inicializar_chroma(collection_name: str = "docs"):
    import chromadb  # import local
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    coll = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embeddings
    )
    return coll

def buscar_contexto(query: str, k: int = 4, collection_name: str = "docs") -> Tuple[str, float]:
    """Consulta o Chroma e monta contexto concatenado + melhor similaridade (0..1)."""
    try:
        coll = inicializar_chroma(collection_name)
        res = coll.query(
            query_texts=[query],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
        documentos = (res.get("documents") or [[]])[0]
        metadatas  = (res.get("metadatas") or [[]])[0]
        distances  = (res.get("distances") or [[]])[0]

        partes = []
        melhor = 0.0
        for doc, meta, dist in zip(documentos, metadatas, distances):
            title = (meta or {}).get("title") or (meta or {}).get("source") or "doc"
            snippet = (doc or "")[:2500]
            partes.append(f"[{title}]\n{snippet}\n")
            if dist is not None:
                sim = max(0.0, 1.0 - float(dist))
                melhor = max(melhor, sim)

        contexto = "\n---\n".join(partes)
        return contexto, melhor
    except Exception as e:
        print(f"[Chroma] ERRO buscar_contexto: {e}")
        return "", 0.0
