from flask import Flask
from flask_cors import CORS
from routes.chatbot import chatbot_bp
from services.database import get_connection
from routes.candidato import candidato_bp
from routes.documento import documento_bp
# Inicialização do Flask
app = Flask(__name__)

app.register_blueprint(documento_bp)  # Adicione esta linha

# Configuração do CORS
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

try:
    conn = get_connection()
    conn.close()
except Exception as e:
    print(f"Erro ao conectar ao banco de dados durante a inicialização: {e}")

app.register_blueprint(chatbot_bp)
app.register_blueprint(candidato_bp)

if __name__ == "__main__":
    app.run()