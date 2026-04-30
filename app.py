import os
from flask import Flask, request, session, redirect, url_for, render_template, jsonify
from flask_socketio import SocketIO
from config import Config
import threading

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

cloudflare_tunnel = None
node_manager = None

def init_components():
    global cloudflare_tunnel, node_manager
    
    from cloudflare_tunnel import CloudflareTunnel
    from node_manager import NodeManager
    
    cloudflare_tunnel = CloudflareTunnel()
    node_manager = NodeManager()
    
    if os.getenv('ENABLE_CLOUDFLARE_TUNNEL', 'false').lower() == 'true':
        def start_tunnel():
            url = cloudflare_tunnel.start()
            if url:
                node_manager.register_node('primary', url, 'Cloudflare Tunnel')
                print("Public URL: {}".format(url))
        
        threading.Thread(target=start_tunnel, daemon=True).start()

@app.route('/health')
def health():
    return {'status': 'healthy', 'service': 'doh-adblock-pro'}, 200

@app.route('/dns-query', methods=['GET', 'POST'])
def doh_endpoint():
    from core.resolver import resolve_doh
    return resolve_doh()

@app.route('/tunnel-info')
def tunnel_info():
    """API endpoint to get tunnel info - read directly from file"""
    try:
        # Read directly from file (most reliable)
        with open('data/tunnel_url.txt', 'r') as f:
            url = f.read().strip()
        if url:
            return jsonify({
                'url': url,
                'running': True,
                'doh_url': '{}/dns-query'.format(url),
                'admin_url': '{}/admin/login'.format(url)
            })
    except:
        pass
    
    # Fallback to CloudflareTunnel instance
    if cloudflare_tunnel:
        return jsonify(cloudflare_tunnel.get_tunnel_info())
    return jsonify({'url': None})

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('password') == Config.ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        return render_template('admin/login.html', error='Invalid password')
    return render_template('admin/login.html', error=None)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/')
@app.route('/admin')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    from monitoring.analytics import Analytics
    from blocking.blocklist import BlocklistManager
    
    analytics = Analytics()
    bl = BlocklistManager()
    
    stats = analytics.get_stats()
    blocklist_stats = bl.stats()
    custom_domains = list(bl.custom)
    
    tunnel_info = cloudflare_tunnel.get_tunnel_info() if cloudflare_tunnel else None
    nodes = node_manager.get_nodes() if node_manager else {}
    
    return render_template('admin/dashboard.html', 
                          stats=stats, 
                          blocklist_stats=blocklist_stats,
                          custom_domains=custom_domains,
                          tunnel_info=tunnel_info,
                          nodes=nodes)

@app.route('/admin/add_domain', methods=['POST'])
def add_domain():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    from blocking.blocklist import BlocklistManager
    bl = BlocklistManager()
    domain = request.form.get('domain', '').strip()
    if domain and '.' in domain:
        bl.add_custom(domain)
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/remove_domain', methods=['POST'])
def remove_domain():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    from blocking.blocklist import BlocklistManager
    bl = BlocklistManager()
    domain = request.form.get('domain', '').strip()
    if domain:
        bl.remove_custom(domain)
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/refresh')
def refresh():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    from blocking.blocklist import BlocklistManager
    import threading
    bl = BlocklistManager()
    threading.Thread(target=bl.load, daemon=True).start()
    return redirect(url_for('admin_dashboard'))

@app.route('/api/nodes/register', methods=['POST'])
def register_node():
    data = request.json
    node_id = data.get('node_id')
    url = data.get('url')
    location = data.get('location', 'Unknown')
    
    if node_id and url:
        node_manager.register_node(node_id, url, location)
        return jsonify({'status': 'registered', 'node_id': node_id}), 200
    
    return jsonify({'error': 'Missing node_id or url'}), 400

@app.route('/api/nodes', methods=['GET'])
def list_nodes():
    return jsonify(node_manager.get_nodes())

@app.route('/api/nodes/<node_id>', methods=['DELETE'])
def delete_node(node_id):
    node_manager.remove_node(node_id)
    return jsonify({'status': 'removed'}), 200

# Initialize components on import (for gunicorn)
init_components()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
