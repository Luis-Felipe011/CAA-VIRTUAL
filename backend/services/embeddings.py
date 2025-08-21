from langchain_huggingface import HuggingFaceEmbeddings
from constants.constants import EMBEDDINGS_MODEL_NAME, CHROMA_DIR, PDF_DIR
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

def clean_text(text):
    import re, unicodedata
    text = re.sub(r'Página \d+ de \d+', '', text)
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = text.strip()
    print(f"[Limpeza] Texto limpo: {text[:80]}...")
    return text

embeddings = HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL_NAME)

def gerar_base_vetorial():
    print(f"[Embeddings] Usando modelo: {EMBEDDINGS_MODEL_NAME}")
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=160)
    all_chunks = []
    unique_texts = set()
    total_docs = 0

    for pdf_path in PDF_DIR.glob("*.pdf"):
        print(f"[Ingestão] Processando {pdf_path.name}...")
        docs = PyPDFLoader(str(pdf_path)).load()
        total_docs += len(docs)
        chunks = splitter.split_documents(docs)
        print(f"[Chunking] {len(chunks)} chunks gerados para {pdf_path.name}")
        for idx, chunk in enumerate(chunks):
            cleaned = clean_text(chunk.page_content)
            if cleaned not in unique_texts and len(cleaned) >= 200:
                unique_texts.add(cleaned)
                chunk.page_content = cleaned
                chunk.metadata["source"] = pdf_path.name
                chunk.metadata["chunk_id"] = f"{pdf_path.stem}_{idx}"
                all_chunks.append(chunk)
            else:
                print(f"[Deduplicação] Chunk duplicado ou curto removido: {cleaned[:60]}...")

    print(f"[Ingestão] Total de documentos: {total_docs}")
    print(f"[Chroma] Indexando {len(all_chunks)} chunks em {CHROMA_DIR}")
    try:
        print(f"[Chroma] Persist directory: {CHROMA_DIR}")
        if all_chunks:
            print(f"[Chroma] Exemplo de chunk: {all_chunks[0].page_content[:100]}...")
        else:
            print("[Chroma] Nenhum chunk para indexar.")
        Chroma.from_documents(
            documents=all_chunks,
            embedding=embeddings,
            persist_directory=str(CHROMA_DIR)
        )
        print("✅ Base vetorial criada/atualizada com sucesso!")
    except Exception as e:
        print(f"[ERRO] Falha ao criar base vetorial: {e}")
        import traceback; traceback.print_exc()
        raise