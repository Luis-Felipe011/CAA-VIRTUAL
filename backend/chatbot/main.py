# pip install python-dotenv langchain langchain-openai langchain-community langchain-chroma chromadb openai pypdf
from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_chroma.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os


load_dotenv()

app = Flask(__name__)
CORS(app)
CAMINHO_DB = "db"

prompt_template = """
Responda à pergunta do usuário de forma objetiva e direta, usando o mínimo de informação possível, mas suficiente para atender à pergunta:
{pergunta}

Considere apenas as informações abaixo:
{base_conhecimento}
"""

@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    data = request.get_json(force=True)
    pergunta = data.get('message') or data.get('mensagem')
    if not pergunta:
        return jsonify({"ok": False, "error": "mensagem vazia"}), 400

    funcao_embedding = OpenAIEmbeddings()
    db = Chroma(persist_directory=CAMINHO_DB, embedding_function=funcao_embedding)
    resultados = db.similarity_search_with_relevance_scores(pergunta, k=4)
    if len(resultados) == 0 or resultados[0][1] < 0.3:
        return jsonify({"ok": True, "resposta": "Não conseguiu encontrar alguma informação relevante na base"})

    textos_resultado = [resultado[0].page_content for resultado in resultados]
    base_conhecimento = "\n\n----\n\n".join(textos_resultado)
    prompt = ChatPromptTemplate.from_template(prompt_template)
    prompt = prompt.invoke({"pergunta": pergunta, "base_conhecimento": base_conhecimento})

    modelo = ChatOpenAI(model="gpt-4o-mini")
    texto_resposta = modelo.invoke(prompt).content
    return jsonify({"ok": True, "resposta": texto_resposta})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)