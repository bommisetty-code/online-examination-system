from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from flask import jsonify

def token_required(fn):
    """Decorator to verify JWT token is present"""
    @wraps(fn)
    def decorated(*args, **kwargs):
        verify_jwt_in_request()
        return fn(*args, **kwargs)
    return decorated

def admin_required(fn):
    """Decorator to require admin role"""
    @wraps(fn)
    def decorated(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'message': 'Admin access required'}), 403
        return fn(*args, **kwargs)
    return decorated

def student_required(fn):
    """Decorator to require student role"""
    @wraps(fn)
    def decorated(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get('role') != 'student':
            return jsonify({'message': 'Student access required'}), 403
        return fn(*args, **kwargs)
    return decorated
