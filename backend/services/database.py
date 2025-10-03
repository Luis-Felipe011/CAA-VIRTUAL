import psycopg2
from dotenv import load_dotenv, find_dotenv
import os
from pathlib import Path

# Carrega .env da raiz e o do backend (mesma lógica do app.py)
load_dotenv(find_dotenv())
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)

USER = os.getenv("PGUSER")
PASSWORD = os.getenv("PGPASSWORD") or os.getenv("DB_PASSWORD")  # <- aceita os dois
HOST = os.getenv("PGHOST")
PORT = os.getenv("PGPORT")
DBNAME = os.getenv("PGDATABASE")

def get_connection():
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
