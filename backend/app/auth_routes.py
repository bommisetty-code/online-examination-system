from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity
from app.services import AuthService
from app.decorators import token_required
from app.errors import APIError, ValidationError, AuthenticationError, ConflictError
from app.validators import validate_email, validate_username, validate_password

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user (admin only for MVP)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        
        email = data.get('email', '').strip()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        full_name = data.get('full_name', '').strip()
        role = data.get('role', 'student')  # 'admin' or 'student'
        
        # Validate role
        if role not in ['admin', 'student']:
            return jsonify({'message': 'Invalid role'}), 400
        
        # Register user
        user = AuthService.register_user(email, username, password, full_name, role)
        
        return jsonify({
            'message': 'User registered successfully',
            'user_id': user.id,
            'username': user.username,
            'role': user.role
        }), 201
    
    except (ValidationError, ConflictError) as e:
        return jsonify({'message': e.message}), e.status_code
    except Exception as e:
        return jsonify({'message': 'Registration failed', 'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'message': 'Username and password required'}), 400
        
        # Authenticate user
        user = AuthService.login(username, password)
        
        # Create JWT token
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
        )
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'full_name': user.full_name
            }
        }), 200
    
    except AuthenticationError as e:
        return jsonify({'message': e.message}), 401
    except Exception as e:
        return jsonify({'message': 'Login failed', 'error': str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile():
    """Get current user profile"""
    try:
        user_id = int(get_jwt_identity())
        user = AuthService.get_user_by_id(user_id)
        
        return jsonify({
            'user': user.to_dict()
        }), 200
    
    except AuthenticationError as e:
        return jsonify({'message': e.message}), 401
    except Exception as e:
        return jsonify({'message': 'Failed to get profile', 'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    """User logout"""
    return jsonify({'message': 'Logged out successfully'}), 200
