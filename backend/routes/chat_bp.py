from flask import Blueprint, request, jsonify, Response, stream_with_context
from services.gemini_service import gerar_resposta_gemini
from services.rag import buscar_docs_relevantes

chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True) or {}
    pergunta = (data.get("mensagem") or data.get("message") or "").strip()
    if not pergunta:
        return jsonify({"error": "mensagem vazia"}), 400
    contexto = buscar_docs_relevantes(pergunta)
    resposta = gerar_resposta(pergunta, contexto, stream=False)
    return jsonify({"resposta": resposta})

@chat_bp.route("/chat/stream", methods=["POST"])
def chat_stream():
    data = request.get_json(force=True) or {}
    pergunta = (data.get("mensagem") or data.get("message") or "").strip()
    if not pergunta:
        return jsonify({"error": "mensagem vazia"}), 400
    contexto = buscar_docs_relevantes(pergunta)

    def generate():
        for chunk in gerar_resposta(pergunta, contexto, stream=True):
            yield f"data: {chunk}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")
