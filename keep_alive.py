from flask import Flask, render_template, jsonify
from threading import Thread
import os
import sys
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

# Configuração do banco de dados
# Certifique-se de que DATABASE_URL existe, ou use um valor padrão para desenvolvimento
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    logger.warning("DATABASE_URL não configurado, usando SQLite para desenvolvimento")
    database_url = "sqlite:///database.db"

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Importa e inicializa o banco de dados
from models import db

# Inicializa o app com a extensão de banco de dados
db.init_app(app)

# Cria todas as tabelas se não existirem
with app.app_context():
    db.create_all()
    logger.info("Banco de dados inicializado")

@app.route('/')
def home():
    """Render the home page"""
    # O token agora está fixo no código, então sempre mostramos como ativo
    has_token = True
    # Bot sempre ativo, não precisa mais verificar variável de ambiente
    return render_template('index.html', has_token=has_token)

@app.route('/health')
def health():
    """Health check endpoint"""
    return {"status": "online"}

@app.route('/api/status')
def status():
    """API endpoint to check bot status"""
    has_token = bool(os.environ.get("DISCORD_TOKEN"))
    
    # Check if bot_runner was imported, which means bot is running
    bot_running = 'bot_runner' in sys.modules
    
    return jsonify({
        "bot_status": "active" if has_token and bot_running else "setup_required",
        "web_server": "online",
        "token_configured": has_token,
        "bot_thread_active": bot_running
    })

def run():
    """Run the Flask app on the specified host and port"""
    try:
        app.run(host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Error starting Flask server: {str(e)}")

def keep_alive():
    """Start the Flask server in a new thread"""
    logger.info("Starting keep-alive web server")
    server_thread = Thread(target=run)
    server_thread.daemon = True  # Thread will close when main program exits
    server_thread.start()
    logger.info("Keep-alive web server started")
