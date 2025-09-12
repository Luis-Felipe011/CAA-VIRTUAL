# backend/services/gemini_service.py
from dotenv import load_dotenv
from pathlib import Path
import os
import google.generativeai as genai

# Carrega backend/.env
BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
DEBUG = os.getenv("DEBUG", "0") in ("1", "true", "True")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY não definida no .env")

genai.configure(api_key=API_KEY)

_SYSTEM_INSTRUCTION = (
    "Você é o assistente do CAA-Virtual. Responda APENAS com base no contexto fornecido. "
    "Se algo não estiver no contexto, diga brevemente o que falta. Responda em PT-BR."
)

_model = genai.GenerativeModel(
    MODEL_NAME,
    system_instruction=_SYSTEM_INSTRUCTION
)

def _build_prompt(pergunta: str, contexto: str) -> str:
    contexto = contexto or "Nenhum contexto disponível."
    return (
        f"Contexto (use apenas o que está aqui):\n{contexto}\n\n"
        f"Pergunta: {pergunta}\n\n"
        "Responda de forma objetiva e cite, quando útil, o arquivo/título do trecho do contexto."
    )

def gerar_resposta_gemini(pergunta: str, contexto: str, stream: bool = False):
    prompt = _build_prompt(pergunta, contexto)
    try:
        if stream:
            resp = _model.generate_content([prompt], stream=True)
            for c in resp:
                if hasattr(c, "text") and c.text:
                    yield c.text
        else:
            resp = _model.generate_content([prompt])
            text = (getattr(resp, "text", None) or "").strip()
            if not text:
                return "Não consegui gerar resposta a partir do contexto. Tente reformular a pergunta."
            return text
    except Exception as e:
        # log no servidor
        print(f"[Gemini] ERRO: {e}")
        if stream:
            yield "Desculpe, houve um erro ao gerar a resposta."
        else:
            return ("[DEV] " + str(e)) if DEBUG else "Desculpe, houve um erro ao gerar a resposta."

# Alias para compatibilidade com código antigo
gerar_resposta = gerar_resposta_gemini
