# pip install python-dotenv langchain langchain-openai langchain-community langchain-chroma chromadb openai pypdf
from langchain_chroma.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

CAMINHO_DB = "db"

prompt_template = """
Responda à pergunta do usuário de forma objetiva e direta, usando o mínimo de informação possível, mas suficiente para atender à pergunta:
{pergunta}

Considere apenas as informações abaixo:
{base_conhecimento}
"""

def perguntar():
    pergunta = input("Escreva sua pergunta: ")

    # carregar o banco de dados
    funcao_embedding = OpenAIEmbeddings()
    db = Chroma(persist_directory=CAMINHO_DB, embedding_function=funcao_embedding)

    # comparar a pergunta do usuario (embedding) com o meu banco de dados
    resultados = db.similarity_search_with_relevance_scores(pergunta, k=4)
    if len(resultados) == 0 or resultados[0][1] < 0.3:
        print("Não conseguiu encontrar alguma informação relevante na base")
        return
    
    textos_resultado = []
    for resultado in resultados:
        texto = resultado[0].page_content
        textos_resultado.append(texto)
    
    base_conhecimento = "\n\n----\n\n".join(textos_resultado)
    prompt = ChatPromptTemplate.from_template(prompt_template)
    prompt = prompt.invoke({"pergunta": pergunta, "base_conhecimento": base_conhecimento})
    # print(prompt)

    modelo = ChatOpenAI(model="gpt-4o-mini")
    texto_resposta = modelo.invoke(prompt).content
    print("Resposta da IA:", texto_resposta)

def responder_chat(mensagem: str) -> str:
    # Carregar o banco de dados vetorial
    funcao_embedding = OpenAIEmbeddings()
    db = Chroma(persist_directory=CAMINHO_DB, embedding_function=funcao_embedding)

    # Buscar os textos mais relevantes
    resultados = db.similarity_search_with_relevance_scores(mensagem, k=4)
    if len(resultados) == 0 or resultados[0][1] < 0.3:
        return "Não consegui encontrar uma resposta relevante na base."

    textos_resultado = []
    for resultado in resultados:
        texto = resultado[0].page_content
        textos_resultado.append(texto)

    base_conhecimento = "\n\n----\n\n".join(textos_resultado)
    prompt = ChatPromptTemplate.from_template(prompt_template)
    prompt = prompt.invoke({"pergunta": mensagem, "base_conhecimento": base_conhecimento})

    modelo = ChatOpenAI(model="gpt-4o-mini")
    texto_resposta = modelo.invoke(prompt).content
    return texto_resposta

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ou especifique o domínio do seu frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    mensagem = data.get("mensagem", "")
    resposta = responder_chat(mensagem)
    return JSONResponse(content={"resposta": resposta})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5004, reload=True)