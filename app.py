import os
import asyncio
from flask import Flask
from flask_socketio import SocketIO
from config import Config
from core.dns_server import start_dns_servers
from management.admin import admin_bp
from management.api import api_bp
from monitoring.metrics import metrics_bp
from security.auth import auth_bp
from anonymity.no_log_mode import NoLogMode

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins="*")

# Register blueprints
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(metrics_bp, url_prefix='/metrics')
app.register_blueprint(auth_bp, url_prefix='/auth')

# Initialize components
no_log = NoLogMode()

@app.route('/health')
def health():
    return {'status': 'healthy', 'service': 'doh-adblock-pro'}, 200

@app.route('/dns-query', methods=['GET', 'POST'])
def doh_endpoint():
    from core.resolver import resolve_doh
    return resolve_doh()

@app.route('/dns-query-tls', methods=['POST'])
def dot_endpoint():
    from core.resolver import resolve_dot
    return resolve_dot()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    # Start DNS servers in background
    import threading
    t = threading.Thread(target=start_dns_servers, daemon=True)
    t.start()
    
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
