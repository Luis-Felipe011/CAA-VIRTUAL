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

def get_connection():
    """
    Retorna uma conexão com o banco de dados PostgreSQL.
    """
    try:
        conn = psycopg2.connect(
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
            dbname=DBNAME
        )
        print("✅ Conexão com o banco de dados estabelecida com sucesso!")
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco de dados: {e}")
        raise