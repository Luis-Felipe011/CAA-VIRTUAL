from flask import Blueprint, request, jsonify
from services.chroma import inicializar_chroma
from services.ollama import gerar_resposta_ollama
from services.similaridade import calcular_similaridade
from services.embeddings import gerar_base_vetorial
from sentence_transformers import SentenceTransformer

chatbot_bp = Blueprint("chatbot", __name__)

# Inicializa o Chroma DB
chroma_db = inicializar_chroma()

# Inicializa o modelo para classificação de perguntas
classifier_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Tipos de perguntas
QUESTION_TYPES = {
    "saudacao": "Saudação",
    "despedida": "Despedida",
    "agradecimento": "Agradecimento",
    "prouni": "Pergunta relacionada ao Prouni",
    "nao_relacionada": "Pergunta não relacionada ao Prouni"
}

# Exemplos para cada tipo (para comparação sem usar lista de palavras)
EXAMPLES = {
    "saudacao": [
        "Olá", "Oi", "Bom dia", "Boa tarde", "E aí", "Oi, tudo bem?"
    ],
    "despedida": [
        "Tchau", "Até mais", "Até logo", "Falou", "Até a próxima"
    ],
    "agradecimento": [
        "Obrigado", "Valeu", "Agradeço", "Obrigado pela ajuda"
    ],
    "prouni": [
        "Quais documentos são necessários para o Prouni?",
        "Como funciona o Prouni?",
        "Quais são os critérios do Prouni?",
        "Como me inscrever no Prouni?"
    ],
    "nao_relacionada": [
        "Qual é o seu nome?",
        "Você gosta de música?",
        "Qual é a capital da França?"
    ]
}

# Função para classificar a pergunta
def classificar_pergunta(pergunta):
    pergunta_emb = classifier_model.encode(pergunta)
    max_sim = -1
    tipo_pergunta = "nao_relacionada"
    for tipo, exemplos in EXAMPLES.items():
        for exemplo in exemplos:
            exemplo_emb = classifier_model.encode(exemplo)
            sim = (pergunta_emb @ exemplo_emb) / ( (pergunta_emb @ pergunta_emb)**0.5 * (exemplo_emb @ exemplo_emb)**0.5 )
            if sim > max_sim:
                max_sim = sim
                tipo_pergunta = tipo
    return tipo_pergunta

def extrair_palavras_chave(pergunta):
    # Simples: separa palavras maiores que 4 letras (pode ser aprimorado)
    return [w.lower() for w in pergunta.split() if len(w) > 4]

def rerank_docs(pergunta, docs, top_k=4):
    # Exemplo simples de rerank: prioriza diversidade de seções e similaridade
    from services.similaridade import calcular_similaridade
    palavras_chave = extrair_palavras_chave(pergunta)
    scored = []
    seções_usadas = set()
    for doc in docs:
        score = calcular_similaridade(pergunta, doc.page_content)
        seção = doc.metadata.get("section", "")
        # Bônus se a seção ainda não foi usada
        if seção and seção not in seções_usadas:
            score += 0.05
            seções_usadas.add(seção)
        # Bônus se palavras-chave aparecem no chunk
        if any(p in doc.page_content.lower() for p in palavras_chave):
            score += 0.05
        scored.append((score, doc))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [doc for _, doc in scored[:top_k]]

@chatbot_bp.route("/api/chatbot", methods=["POST"])
def chatbot():
    global chroma_db

    print("\n[Chatbot] Nova requisição recebida")
    data = request.json or {}
    pergunta = data.get("message", "")
    print(f"[Chatbot] Pergunta recebida: {pergunta}")

    # Classifica a pergunta
    try:
        tipo = classificar_pergunta(pergunta)
        print(f"[Chatbot] Tipo de pergunta classificado: {tipo}")
    except Exception as e:
        print(f"[ERRO] Falha ao classificar pergunta: {e}")
        import traceback; traceback.print_exc()
        return jsonify({"response": "Erro ao classificar pergunta.", "similaridade": 0.0})

    # Respostas rápidas para tipos não relacionados ao Prouni
    respostas_rapidas = {
        "saudacao": "Olá! Como posso ajudar você com informações sobre o Prouni?",
        "despedida": "Até mais! Se precisar de algo sobre o Prouni, estarei aqui.",
        "agradecimento": "De nada! Estou aqui para ajudar com o Prouni.",
        "nao_relacionada": "Desculpe, só posso responder perguntas relacionadas ao Prouni."
    }

    if tipo != "prouni":
        print(f"[Chatbot] Resposta rápida para tipo: {tipo}")
        return jsonify({"response": respostas_rapidas.get(tipo, "Desculpe, não entendi."), "similaridade": 1.0})

    # Busca contexto no Chroma DB (busca híbrida e rerank)
    try:
        print("[Chatbot] Buscando contexto no Chroma DB (híbrido)...")
        # Se sua versão do ChromaDB suportar hybrid_search, use-a. Caso contrário, use similarity_search.
        try:
            contexto_docs = chroma_db.hybrid_search(pergunta, k=10)
        except Exception:
            contexto_docs = chroma_db.similarity_search(pergunta, k=10)
        print(f"[Chatbot] {len(contexto_docs) if contexto_docs else 0} documentos de contexto encontrados")
        contexto_docs = rerank_docs(pergunta, contexto_docs, top_k=4)
        for i, doc in enumerate(contexto_docs):
            print(f"[Chatbot] Contexto {i+1}: {doc.page_content[:120]}... [Fonte: {doc.metadata.get('source', '')}] [Seção: {doc.metadata.get('section', '')}]")
    except Exception as e:
        print(f"[ERRO] Falha ao buscar contexto no Chroma DB: {e}")
        import traceback; traceback.print_exc()
        return jsonify({"response": "Erro ao buscar contexto.", "similaridade": 0.0})

    if not contexto_docs:
        try:
            print("[Chatbot] Nenhum contexto encontrado, gerando base vetorial...")
            gerar_base_vetorial()
        except Exception as e:
            print(f"[ERRO] Falha ao gerar base vetorial: {e}")
            import traceback; traceback.print_exc()
            return jsonify({"response": "Erro interno ao gerar base vetorial.", "similaridade": 0.0})

        # Recarrega o Chroma DB após gerar a base vetorial
        try:
            print("[Chatbot] Recarregando Chroma DB...")
            chroma_db = inicializar_chroma()
            print("[Chatbot] Chroma DB recarregado.")
        except Exception as e:
            print(f"[ERRO] Falha ao recarregar Chroma DB: {e}")
            import traceback; traceback.print_exc()
            return jsonify({"response": "Erro ao recarregar base vetorial.", "similaridade": 0.0})

        # Tenta buscar o contexto novamente
        try:
            print("[Chatbot] Buscando contexto novamente após ingestão...")
            contexto_docs = chroma_db.hybrid_search(pergunta, k=10)
            print(f"[Chatbot] {len(contexto_docs) if contexto_docs else 0} documentos de contexto encontrados (segunda tentativa)")
            contexto_docs = rerank_docs(pergunta, contexto_docs, top_k=4)
            for i, doc in enumerate(contexto_docs):
                print(f"[Chatbot] Contexto {i+1}: {doc.page_content[:120]}... [Fonte: {doc.metadata.get('source', '')}] [Seção: {doc.metadata.get('section', '')}]")
        except Exception as e:
            print(f"[ERRO] Falha ao buscar contexto após ingestão: {e}")
            import traceback; traceback.print_exc()
            return jsonify({"response": "Erro ao buscar contexto após ingestão.", "similaridade": 0.0})

        if not contexto_docs:
            print("[Chatbot] Nenhum contexto encontrado após ingestão.")
            return jsonify({"response": "Desculpe, não encontrei informações relevantes.", "similaridade": 0.0})

    # Extrai o texto do contexto
    try:
        contexto = ""
        for doc in contexto_docs:
            secao = doc.metadata.get("section", "")
            fonte = doc.metadata.get("source", "")
            chunk_id = doc.metadata.get("chunk_id", "")
            contexto += f"[Seção: {secao}] [Fonte: {fonte}] [Chunk: {chunk_id}]\n{doc.page_content}\n\n"
        print(f"[Chatbot] Contexto extraído com sucesso.")
    except Exception as e:
        print(f"[ERRO] Falha ao extrair contexto: {e}")
        import traceback; traceback.print_exc()
        return jsonify({"response": "Erro ao extrair contexto.", "similaridade": 0.0})

    # Gera a resposta usando o Ollama
    try:
        print("[Chatbot] Gerando resposta com Ollama...")
        pergunta = pergunta.replace('\0', '')
        contexto = contexto.replace('\0', '')
        resposta = gerar_resposta_ollama(pergunta, contexto)
        print(f"[Chatbot] Resposta gerada: {resposta[:200]}...")
    except Exception as e:
        print(f"[ERRO] Falha ao gerar resposta com Ollama: {e}")
        import traceback; traceback.print_exc()
        return jsonify({"response": "Erro ao gerar resposta.", "similaridade": 0.0})

    # Calcula a similaridade entre a resposta e o contexto
    try:
        similaridade = float(calcular_similaridade(resposta, contexto))
        print(f"[Chatbot] Similaridade calculada: {similaridade}")
    except Exception as e:
        print(f"[ERRO] Falha ao calcular similaridade: {e}")
        import traceback; traceback.print_exc()
        similaridade = 0.0

    print(f"[Chatbot] Pergunta: {pergunta}")
    print(f"[Chatbot] Tipo: {tipo}")
    print(f"[Chatbot] Similaridade: {similaridade}")

    # Log detalhado das embeddings (opcional, pode ser pesado)
    try:
        pergunta_emb = classifier_model.encode(pergunta)
        print(f"[Embeddings] Vetor da pergunta (primeiros 10 valores): {pergunta_emb[:10]}")
        if contexto_docs:
            contexto_emb = classifier_model.encode(contexto_docs[0].page_content)
            print(f"[Embeddings] Vetor do 1º contexto (primeiros 10 valores): {contexto_emb[:10]}")
    except Exception as e:
        print(f"[ERRO] Falha ao logar embeddings: {e}")

    return jsonify({"response": resposta, "similaridade": similaridade})