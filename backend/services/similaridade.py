from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from constants.constants import EMBEDDINGS_MODEL_NAME

similarity_model = SentenceTransformer(EMBEDDINGS_MODEL_NAME)

def calcular_similaridade(resposta: str, contexto: str) -> float:
    emb_resposta = similarity_model.encode(resposta, convert_to_tensor=True)
    emb_contexto = similarity_model.encode(contexto, convert_to_tensor=True)
    similarity = cosine_similarity(emb_resposta.reshape(1, -1), emb_contexto.reshape(1, -1))[0][0]
    return similarity