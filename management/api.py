from flask import Blueprint, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from config import Config
from blocking.blocklist import BlocklistManager
from monitoring.analytics import Analytics
from management.per_client import ClientRules

api_bp = Blueprint('api', __name__)
jwt = JWTManager()
blocklist = BlocklistManager()
analytics = Analytics()
client_rules = ClientRules()

@api_bp.route('/token', methods=['POST'])
def get_token():
    password = request.json.get('password', '')
    if password == Config.ADMIN_PASSWORD:
        access_token = create_access_token(identity='admin')
        return jsonify(access_token=access_token), 200
    return jsonify(msg='Bad password'), 401

@api_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    return jsonify(analytics.get_stats())

@api_bp.route('/blocklist', methods=['GET'])
@jwt_required()
def get_blocklist():
    return jsonify({
        'custom': list(blocklist.custom),
        'stats': blocklist.stats()
    })

@api_bp.route('/blocklist/add', methods=['POST'])
@jwt_required()
def api_add_domain():
    domain = request.json.get('domain', '')
    if domain:
        blocklist.add_custom(domain)
        return jsonify(msg='Added'), 200
    return jsonify(msg='Invalid domain'), 400

@api_bp.route('/blocklist/remove', methods=['POST'])
@jwt_required()
def api_remove_domain():
    domain = request.json.get('domain', '')
    if domain:
        blocklist.remove_custom(domain)
        return jsonify(msg='Removed'), 200
    return jsonify(msg='Invalid domain'), 400

@api_bp.route('/client-rules', methods=['GET', 'POST', 'DELETE'])
@jwt_required()
def manage_client_rules():
    if request.method == 'GET':
        return jsonify(client_rules.get_all())
    elif request.method == 'POST':
        ip = request.json.get('ip')
        rule = request.json.get('rule')
        client_rules.add_rule(ip, rule)
        return jsonify(msg='Rule added'), 200
    elif request.method == 'DELETE':
        ip = request.json.get('ip')
        client_rules.remove_rules(ip)
        return jsonify(msg='Rules removed'), 200
