import psycopg2
from dotenv import load_dotenv
import os

# Carrega variáveis do .env
load_dotenv()

# Lê variáveis de ambiente
USER = os.getenv("PGUSER")
PASSWORD = os.getenv("PGPASSWORD")
HOST = os.getenv("PGHOST")
PORT = os.getenv("PGPORT")
DBNAME = os.getenv("PGDATABASE")

# Função para conectar ao banco de dados
def get_db_connection():
    try:
        conn = psycopg2.connect(
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
            dbname=DBNAME
        )
        print("✅ Conectado ao banco de dados com sucesso!")
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco de dados: {e}")
        raise

# Função para consultar documentos
def fetch_documentos():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, numero, nome, secao FROM documentos;")
        resultados = cur.fetchall()
        cur.close()
        conn.close()
        return resultados
    except Exception as e:
        print(f"❌ Erro ao consultar documentos: {e}")
        raise