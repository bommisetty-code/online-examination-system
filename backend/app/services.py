from app import db
from app.models import User
from app.errors import AuthenticationError, ValidationError, ConflictError
from app.validators import validate_email, validate_username, validate_password
from datetime import datetime

class AuthService:
    """Authentication service"""
    
    @staticmethod
    def register_user(email, username, password, full_name, role='student'):
        """Register a new user"""
        
        # Validate inputs
        if not validate_email(email):
            raise ValidationError("Invalid email format")
        
        if not validate_username(username):
            raise ValidationError("Username must be 3-20 characters (alphanumeric and underscore)")
        
        is_valid, message = validate_password(password)
        if not is_valid:
            raise ValidationError(message)
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            raise ConflictError("Email already registered")
        
        if User.query.filter_by(username=username).first():
            raise ConflictError("Username already taken")
        
        # Create user
        user = User(
            email=email,
            username=username,
            full_name=full_name,
            role=role,
            is_active=True
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return user
    
    @staticmethod
    def login(username, password):
        """Authenticate user and return user object"""
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user or not user.check_password(password):
            raise AuthenticationError("Invalid username or password")
        
        if not user.is_active:
            raise AuthenticationError("Account is inactive")
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        return user
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID"""
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            raise AuthenticationError("User not found")

        user = User.query.get(user_id)
        if not user:
            raise AuthenticationError("User not found")
        return user
