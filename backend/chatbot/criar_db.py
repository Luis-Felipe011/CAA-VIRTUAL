from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

import os
PASTA_BASE = os.path.join(os.path.dirname(__file__), "base")

def criar_db():
    documentos = carregar_documentos()
    chunks = dividir_chunks(documentos)
    vetorizar_chunks(chunks)

def carregar_documentos():
    carregador = PyPDFDirectoryLoader(PASTA_BASE, glob="*.pdf")
    documentos = carregador.load()
    print(f"Documentos carregados: {len(documentos)}")
    for i, doc in enumerate(documentos):
        texto = getattr(doc, 'page_content', '')
        print(f"Doc {i+1}: {len(texto)} chars | Primeiros 100: {texto[:100]}")
    return documentos

def dividir_chunks(documentos):
    separador_documentos = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=500,
        length_function=len,
        add_start_index=True
    )
    chunks = separador_documentos.split_documents(documentos)
    print(f"Chunks criados: {len(chunks)}")
    for i, chunk in enumerate(chunks[:5]):  # Mostra os 5 primeiros
        print(f"Chunk {i+1}: {chunk.page_content[:100]}")
    return chunks

def vetorizar_chunks(chunks):
    db = Chroma.from_documents(chunks, OpenAIEmbeddings(), persist_directory="db")
    print("Banco de Dados criado")

criar_db()