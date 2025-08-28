from services.database import get_connection

def criar_sessoes_table():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sessoes (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER NOT NULL,
                data_hora_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro ao criar tabela de sessões: {e}")

def inserir_sessao(usuario_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO sessoes (usuario_id) VALUES (%s) RETURNING id",
            (usuario_id,)
        )
        sessao_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return sessao_id
    except Exception as e:
        print(f"Erro ao criar sessão: {e}")
        return None

def buscar_sessoes_por_usuario(usuario_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, data_hora_inicio FROM sessoes WHERE usuario_id = %s ORDER BY data_hora_inicio DESC",
            (usuario_id,)
        )
        sessoes = cur.fetchall()
        cur.close()
        conn.close()
        return sessoes
    except Exception as e:
        print(f"Erro ao buscar sessões: {e}")
        return None

def buscar_sessao_por_id(sessao_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, usuario_id, data_hora_inicio FROM sessoes WHERE id = %s",
            (sessao_id,)
        )
        sessao = cur.fetchone()
        cur.close()
        conn.close()
        return sessao
    except Exception as e:
        print(f"Erro ao buscar sessão: {e}")
        return None