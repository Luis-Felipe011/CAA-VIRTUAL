# backend/routes/chat_bp.py
from flask import Blueprint, request, jsonify, Response, stream_with_context
from types import GeneratorType
from services.database import get_connection
from services.gemini_service import gerar_resposta_gemini
from services.rag import buscar_docs_relevantes

# 1) CRIE O BLUEPRINT ANTES DE USAR
chat_bp = Blueprint("chat", __name__)

# 2) HELPERS
def materializa_texto(x):
    if x is None:
        return ""
    if isinstance(x, str):
        return x
    if hasattr(x, "text"):
        return str(x.text)
    if isinstance(x, dict) and "text" in x:
        return str(x["text"])
    if isinstance(x, (list, tuple, GeneratorType)):
        # Consome o gerador completamente para obter a string final
        return "".join(materializa_texto(p) for p in x)
    return str(x)

def materializa_contexto(ctx):
    if ctx is None:
        return ""
    if isinstance(ctx, str):
        return ctx
    if isinstance(ctx, GeneratorType):
        ctx = list(ctx)
    if isinstance(ctx, (list, tuple, set)):
        return "\n\n".join(map(str, ctx))
    return str(ctx)

# 3) ROTAS

@chat_bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True) or {}
    pergunta = (data.get("mensagem") or data.get("message") or "").strip()
    user_id = data.get("user_id")

    if not pergunta:
        return jsonify({"error": "mensagem vazia"}), 400

    contexto_raw = buscar_docs_relevantes(pergunta)
    contexto = materializa_contexto(contexto_raw)
    try:
        bruto_gen = gerar_resposta_gemini(pergunta, contexto, stream=False)
        resposta_completa = ""
        for chunk in bruto_gen:
            resposta_completa += materializa_texto(chunk)
        if not resposta_completa.strip():
            resposta_completa = "Desculpe, não consegui gerar uma resposta."
    except Exception as e:
        print(f"Erro ao gerar resposta do Gemini: {e}")
        resposta_completa = "Desculpe, ocorreu um erro ao processar sua mensagem."

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO sessao (user_id, mensagem, msg_bot) VALUES (%s, %s, %s)",
            (user_id, pergunta, resposta_completa),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro ao salvar mensagem do chat: {e}")

    return jsonify({"resposta": resposta_completa})


@chat_bp.route("/chat/stream", methods=["POST"])
def chat_stream():
    data = request.get_json(force=True) or {}
    pergunta = (data.get("mensagem") or data.get("message") or "").strip()
    if not pergunta:
        return jsonify({"error": "mensagem vazia"}), 400

    contexto_raw = buscar_docs_relevantes(pergunta)
    contexto = materializa_contexto(contexto_raw)

    def generate():
        for chunk in gerar_resposta_gemini(pergunta, contexto, stream=True):
            yield f"data: {materializa_texto(chunk)}\n\n"

    return Response(stream_with_context(generate()),
                    mimetype="text/event-stream")