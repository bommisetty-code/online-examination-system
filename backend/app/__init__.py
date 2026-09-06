from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()

def create_app(config_name='development'):
    """Application factory"""
    app = Flask(__name__)
    
    # Load config
    from config import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    
    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})
    
    # Register blueprints
    from app.auth_routes import auth_bp
    from app.admin_routes import admin_bp
    from app.student_routes import student_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(student_bp)
    
    # Error handlers
    from app.errors import register_error_handlers
    register_error_handlers(app)

    @app.route('/api/health', methods=['GET'])
    def health_check():
        return {'status': 'ok', 'service': 'online_exam_system'}, 200
    
    with app.app_context():
        # Create tables
        db.create_all()
    
    return app
