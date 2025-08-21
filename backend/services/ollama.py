import subprocess
from flask import current_app
from constants.constants import OLLAMA_COMMAND, OLLAMA_MODEL

def gerar_resposta_ollama(pergunta: str, contexto: str) -> str:
    prompt = (
        "Você é Silvia, assistente do Prouni. Responda APENAS com base no contexto abaixo. "
        "Se a resposta envolver documentos, cite a seção e o edital. "
        "Se não houver informação, diga que não encontrou no edital.\n\n"
        f"Contexto:\n{contexto}\n\n"
        f"Pergunta: {pergunta}\n\n"
        "Resposta da Silvia:"
    )
    comando = [OLLAMA_COMMAND, "run", OLLAMA_MODEL, prompt]
    try:
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
        )
        return resultado.stdout.strip()
    except subprocess.CalledProcessError as e:
        current_app.logger.error("Erro no Ollama: %s", e.stderr)
        return "Erro interno ao gerar resposta."