import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Bibliotecas do LangChain
from langchain_chroma.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# --- CORREÇÃO CRÍTICA DE CAMINHOS ---
# Isso garante que o script encontre a pasta 'db' e o '.env' 
# mesmo se você rodar o comando da pasta raiz.
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
CAMINHO_ENV = os.path.join(DIRETORIO_ATUAL, ".env")
CAMINHO_DB = os.path.join(DIRETORIO_ATUAL, "db")

# Carrega o .env especificando o caminho exato
load_dotenv(CAMINHO_ENV)

# Configuração do Prompt
prompt_template = """
Responda à pergunta do usuário de forma objetiva e direta, usando o mínimo de informação possível, mas suficiente para atender à pergunta:
{pergunta}

Considere apenas as informações abaixo:
{base_conhecimento}
"""

def responder_chat(mensagem: str) -> str:
    try:
        # Verifica se a chave da API foi carregada
        if not os.getenv("OPENAI_API_KEY"):
            return "Erro de Configuração: API Key da OpenAI não encontrada no arquivo .env"

        # Carregar o banco de dados vetorial usando o caminho absoluto
        funcao_embedding = OpenAIEmbeddings()
        
        if not os.path.exists(CAMINHO_DB):
             return "Erro: Banco de dados vetorial não encontrado. Execute 'criar_db.py' primeiro."

        db = Chroma(persist_directory=CAMINHO_DB, embedding_function=funcao_embedding)

        # Buscar os textos mais relevantes
        resultados = db.similarity_search_with_relevance_scores(mensagem, k=4)
        
        # Se não achar nada relevante ou banco vazio
        if len(resultados) == 0 or resultados[0][1] < 0.6:
            return "Desculpe, não encontrei essa informação nos meus documentos oficiais."

        textos_resultado = []
        for resultado in resultados:
            texto = resultado[0].page_content
            textos_resultado.append(texto)

        base_conhecimento = "\n\n----\n\n".join(textos_resultado)
        prompt = ChatPromptTemplate.from_template(prompt_template)
        prompt_formatado = prompt.invoke({"pergunta": mensagem, "base_conhecimento": base_conhecimento})

        modelo = ChatOpenAI(model="gpt-4o-mini")
        texto_resposta = modelo.invoke(prompt_formatado).content
        
        return texto_resposta

    except Exception as e:
        print(f"Erro interno no chatbot: {e}")
        return "Desculpe, tive um erro interno ao processar sua pergunta."

# --- CONFIGURAÇÃO DA API ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite que o Frontend React acesse
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/chatbot")  # Rota corrigida
async def chat_endpoint(request: Request):
    data = await request.json()
    mensagem = data.get("mensagem", "")
    resposta = responder_chat(mensagem)
    return JSONResponse(content={"resposta": resposta})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5004, reload=True)