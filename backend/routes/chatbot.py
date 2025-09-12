# backend/routes/chatbot.py
from flask import Blueprint, request, jsonify
from services.chroma import buscar_contexto
from services.gemini_service import gerar_resposta_gemini

chatbot_bp = Blueprint("chatbot", __name__)

@chatbot_bp.route("/chatbot", methods=["POST"])
def chat():
    try:
        data = request.get_json(force=True) or {}
        pergunta = (data.get("mensagem") or data.get("message") or "").strip()
        if not pergunta:
            return jsonify({"response": "Mensagem vazia.", "error": "empty_message"}), 200

        contexto, similaridade = buscar_contexto(pergunta, k=4, collection_name="docs")
        resposta = gerar_resposta_gemini(pergunta, contexto, stream=False)

        return jsonify({
            "response": resposta,
            "similaridade": round(similaridade, 4),
        }), 200
    except Exception as e:
        print("[Chatbot] EXCEPTION:", e)
        return jsonify({
            "response": "Desculpe, ocorreu um erro ao processar sua mensagem.",
            "error": "internal_error",
        }), 200
