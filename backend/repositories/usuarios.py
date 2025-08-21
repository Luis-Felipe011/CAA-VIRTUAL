from services.database import get_connection

def criar_usuarios_table():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro ao criar tabela de usuários: {e}")
        return None

def inserir_usuario(nome, email):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO usuarios (nome, email) VALUES (%s, %s) RETURNING id",
            (nome, email)
        )
        usuario_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return usuario_id
    except Exception as e:
        print(f"Erro ao criar usuário: {e}")
        return None

def buscar_usuario_por_email(email):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, nome, email FROM usuarios WHERE email = %s",
            (email,)
        )
        usuario = cur.fetchone()
        cur.close()
        conn.close()
        return usuario
    except Exception as e:
        print(f"Erro ao buscar usuário: {e}")
        return None
    
def buscar_usuario_por_id(usuario_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, nome, email FROM usuarios WHERE id = %s",
            (usuario_id,)
        )
        usuario = cur.fetchone()
        cur.close()
        conn.close()
        return usuario
    except Exception as e:
        print(f"Erro ao buscar usuário: {e}")
        return None

def inserir_candidato(uid, nome, cpf, step):
    try:
        conn = get_connection()
        cur = conn.cursor()
        # Verifica se já existe
        cur.execute("SELECT id FROM candidate WHERE id = %s", (uid,))
        existe = cur.fetchone()
        if existe:
            # Atualiza nome e cpf
            cur.execute(
                "UPDATE candidate SET nome = %s, cpf = %s, step = %s WHERE id = %s RETURNING id",
                (nome, cpf, step, uid)
            )
        else:
            # Insere novo
            cur.execute(
                "INSERT INTO candidate (id, nome, cpf, step) VALUES (%s, %s, %s, %s) RETURNING id",
                (uid, nome, cpf, step)
            )
        candidato_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return candidato_id
    except Exception as e:
        print(f"Erro ao criar/atualizar candidato: {e}")
        return None