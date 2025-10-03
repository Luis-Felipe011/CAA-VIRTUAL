# backend/routes/chat_bp.py
from flask import Blueprint, request, jsonify, Response, stream_with_context
from types import GeneratorType
from services.database import get_connection
from services.gemini_service import gerar_resposta_gemini
from services.rag import buscar_docs_relevantes

chat_bp = Blueprint("chat", __name__)

# ========= Helpers =========
def materializa_texto(x):
    if x is None:
        return ""
    if isinstance(x, str):
        return x
    if hasattr(x, "text"):
        try:
            return str(x.text)
        except Exception:
            pass
    if isinstance(x, dict):
        if "text" in x:
            return str(x["text"])
        if "candidates" in x:
            try:
                return str(x["candidates"][0]["content"]["parts"][0]["text"])
            except Exception:
                pass
    if isinstance(x, (list, tuple, GeneratorType)):
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

# ========= Rotas =========
@chat_bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True) or {}
    print("[/api/chat] payload:", data)

    pergunta = (data.get("mensagem") or data.get("message") or "").strip()
    user_id = data.get("user_id")
    if not pergunta:
        return jsonify({"ok": False, "error": "mensagem vazia"}), 400

    # 1) RAG
    contexto_raw = buscar_docs_relevantes(pergunta)
    contexto = materializa_contexto(contexto_raw)
    print("[DEBUG] Contexto enviado ao Gemini:", contexto)

    # 2) LLM (não-stream) — deve retornar string
    # Gere o prompt e mostre para depuração
    from services.gemini_service import _build_prompt
    # Novo prompt mais claro e exigindo citação
    if not contexto or contexto.strip().lower() in ["nenhum contexto encontrado.", "", "none"]:
        prompt = (
            f"Pergunta: {pergunta}\n"
            "Responda de forma objetiva. Se não souber, diga 'Não encontrado no contexto.'"
        )
        print("[DEBUG] Prompt enviado ao Gemini (livre):", prompt)
        bruto = gerar_resposta_gemini(pergunta, "", stream=False)
    else:
        prompt = (
            "Contexto (use apenas o que está aqui):\n"
            f"{contexto}\n\n"
            f"Pergunta: {pergunta}\n"
            "Responda de forma objetiva, cite o documento/título do contexto e, se não souber, diga 'Não encontrado no contexto.'"
        )
        print("[DEBUG] Prompt enviado ao Gemini:", prompt)
        bruto = gerar_resposta_gemini(pergunta, contexto, stream=False)
    resposta = materializa_texto(bruto).strip()
    if not resposta:
        resposta = "Desculpe, não consegui gerar uma resposta."

    print(f"[/api/chat] pergunta='{pergunta[:80]}'")
    print(f"[/api/chat] resposta_len={len(resposta)} preview='{resposta[:120]}'")

    # 3) Persistência (não derruba fluxo se falhar)
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO sessao (user_id, mensagem, msg_bot) VALUES (%s, %s, %s)",
            (user_id, pergunta, resposta),
        )
        conn.commit()
        cur.close(); conn.close()
    except Exception as e:
        print(f"[/api/chat] WARN persistência: {e}")

    return jsonify({"ok": True, "resposta": resposta})

@chat_bp.route("/chat/stream", methods=["POST"])
def chat_stream():
    data = request.get_json(force=True) or {}
    pergunta = (data.get("mensagem") or data.get("message") or "").strip()
    if not pergunta:
        return jsonify({"ok": False, "error": "mensagem vazia"}), 400

    contexto_raw = buscar_docs_relevantes(pergunta)
    contexto = materializa_contexto(contexto_raw)

    def generate():
        for chunk in gerar_resposta_gemini(pergunta, contexto, stream=True):
            txt = materializa_texto(chunk).strip()
            if not txt:
                continue
            yield f"data: {txt}\n\n"

    return Response(stream_with_context(generate()),
                    mimetype="text/event-stream")
