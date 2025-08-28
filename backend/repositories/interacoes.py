from services.database import get_connection

def criar_interacoes_table():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS interacoes (
                id SERIAL PRIMARY KEY,
                sessao_id INTEGER NOT NULL,
                pergunta TEXT NOT NULL,
                resposta TEXT NOT NULL,
                similaridade FLOAT NOT NULL,
                data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sessao_id) REFERENCES sessoes(id)
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro ao criar tabela de interações: {e}")
        return None

def salvar_interacao(sessao_id, pergunta, resposta, similaridade):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO interacoes (sessao_id, pergunta, resposta, similaridade) VALUES (%s, %s, %s, %s)",
            (sessao_id, pergunta, resposta, similaridade)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro ao salvar interação: {e}")

def buscar_interacoes_por_sessao(sessao_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT pergunta, resposta, similaridade, data_hora FROM interacoes WHERE sessao_id = %s",
            (sessao_id,)
        )
        interacoes = cur.fetchall()
        cur.close()
        conn.close()
        return interacoes
    except Exception as e:
        print(f"Erro ao buscar interações: {e}")
        return None
    
def buscar_interacao_por_id(interacao_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT sessao_id, pergunta, resposta, similaridade, data_hora FROM interacoes WHERE id = %s",
            (interacao_id,)
        )
        interacao = cur.fetchone()
        cur.close()
        conn.close()
        return interacao
    except Exception as e:
        print(f"Erro ao buscar interação: {e}")
        return None
    
def buscar_interacoes_por_usuario(usuario_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT i.pergunta, i.resposta, i.similaridade, i.data_hora
            FROM interacoes i
            JOIN sessoes s ON i.sessao_id = s.id
            WHERE s.usuario_id = %s
        """, (usuario_id,))
        interacoes = cur.fetchall()
        cur.close()
        conn.close()
        return interacoes
    except Exception as e:
        print(f"Erro ao buscar interações por usuário: {e}")
        return None