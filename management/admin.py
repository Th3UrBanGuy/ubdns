from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from config import Config
from blocking.blocklist import BlocklistManager
from monitoring.analytics import Analytics
import json

admin_bp = Blueprint('admin', __name__)
blocklist = BlocklistManager()
analytics = Analytics()

@admin_bp.before_request
def check_auth():
    if request.endpoint != 'admin.login' and not session.get('admin'):
        return redirect(url_for('admin.login'))

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == Config.ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin.dashboard'))
        return render_template('admin/login.html', error='Invalid password')
    return render_template('admin/login.html', error=None)

@admin_bp.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
def dashboard():
    stats = analytics.get_stats()
    blocklist_stats = blocklist.stats()
    custom_domains = list(blocklist.custom)
    return render_template('admin/dashboard.html', 
                          stats=stats, 
                          blocklist_stats=blocklist_stats,
                          custom_domains=custom_domains)

@admin_bp.route('/add_domain', methods=['POST'])
def add_domain():
    domain = request.form.get('domain', '').strip()
    if domain and '.' in domain:
        blocklist.add_custom(domain)
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/remove_domain', methods=['POST'])
def remove_domain():
    domain = request.form.get('domain', '').strip()
    if domain:
        blocklist.remove_custom(domain)
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/refresh')
def refresh():
    import threading
    threading.Thread(target=blocklist.load, daemon=True).start()
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/settings')
def settings():
    return render_template('admin/settings.html')
