import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'jbd-travels-secret-super-key-2026')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jbd-jwt-secret-key-travel-secure-9988')
    JWT_ACCESS_TOKEN_EXPIRES_HOURS = 24
    
    _raw_db = os.environ.get('DATABASE_URL')
    if _raw_db and _raw_db.startswith('postgres://'):
        _raw_db = _raw_db.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_DATABASE_URI = _raw_db or f"sqlite:///{os.path.join(BASE_DIR, 'jbd_travels.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SIMULATED_APIS_ENABLED = True
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
