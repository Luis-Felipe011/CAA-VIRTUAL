from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).resolve().parent / ".env")

from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

from routes.chatbot import chatbot_bp
from routes.candidato import candidato_bp
from routes.documento import documento_bp
from routes.chat_bp import chat_bp

app.register_blueprint(chat_bp, url_prefix="/api")
app.register_blueprint(chatbot_bp, url_prefix="/api")
app.register_blueprint(candidato_bp, url_prefix="/api")
app.register_blueprint(documento_bp, url_prefix="/api")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
