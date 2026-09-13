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

    # ---------------------------------------------------------
    # CORS Configuration
    # ---------------------------------------------------------
    configured_origins = os.getenv('CORS_ORIGINS', '')

    allowed_origins = [
        origin.strip()
        for origin in configured_origins.split(',')
        if origin.strip()
    ]

    # Always allow local development frontend
    local_origins = [
        'http://localhost:5173',
        'http://127.0.0.1:5173',
    ]

    for origin in local_origins:
        if origin not in allowed_origins:
            allowed_origins.append(origin)

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": allowed_origins
            }
        },
        supports_credentials=True
    )

    # ---------------------------------------------------------
    # Register blueprints
    # ---------------------------------------------------------
    from app.auth_routes import auth_bp
    from app.admin_routes import admin_bp
    from app.student_routes import student_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(student_bp)

    # ---------------------------------------------------------
    # Error handlers
    # ---------------------------------------------------------
    from app.errors import register_error_handlers
    register_error_handlers(app)

    # ---------------------------------------------------------
    # Health check
    # ---------------------------------------------------------
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return {
            'status': 'ok',
            'service': 'online_exam_system'
        }, 200

    # ---------------------------------------------------------
    # Create database tables
    # ---------------------------------------------------------
    with app.app_context():
        db.create_all()

    return app