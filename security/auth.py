from flask import Blueprint, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required
from config import Config

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    from flask_jwt_extended import create_access_token
    password = request.json.get('password', '')
    if password == Config.ADMIN_PASSWORD:
        access_token = create_access_token(identity='admin')
        return jsonify(access_token=access_token), 200
    return jsonify(msg='Invalid credentials'), 401

def init_jwt(app):
    jwt = JWTManager(app)
    return jwt
