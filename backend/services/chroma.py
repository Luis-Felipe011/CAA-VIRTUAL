from langchain_chroma import Chroma
from constants.constants import CHROMA_DIR
from services.embeddings import embeddings

def inicializar_chroma():
    return Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=embeddings
    )