# services/rerank.py
from services.similaridade import calcular_similaridade

def rerank_docs(pergunta, docs, top_k=4):
    scored = []
    for doc in docs:
        score = calcular_similaridade(pergunta, doc.page_content)
        scored.append((score, doc))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [doc for score, doc in scored[:top_k]]