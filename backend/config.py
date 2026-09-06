import os
from datetime import timedelta

class Config:
    """Base configuration"""
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'mysql+mysqlconnector://root:password@localhost/online_exam_system'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT
    JWT_SECRET_KEY = os.getenv(
        'JWT_SECRET_KEY',
        'online_exam_system_dev_secret_key_change_me_2026'
    )
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    # Security
    BCRYPT_LOG_ROUNDS = 12
    
    # Session
    SESSION_TIMEOUT = 30 * 60  # 30 minutes

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_SECRET_KEY = 'test_secret_key_for_online_exam_system_2026'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
