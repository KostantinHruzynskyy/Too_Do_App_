"""
╔═══════════════════════════════════════════════════╗
║           SKYY – Configuration Module             ║
║  Environment-based config for dev/staging/prod    ║
╚═══════════════════════════════════════════════════╝
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration with sensible defaults."""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(64).hex())
    DEBUG = False
    TESTING = False

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 'sqlite:///skyy_todo.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # Session
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = (
        os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    )
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_NAME = '__Secure-Skyy-Session'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=4)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = (
        os.getenv('REMEMBER_COOKIE_SECURE', 'False').lower() == 'true'
    )
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_DURATION = timedelta(days=30)

    # Rate Limiting
    RATELIMIT_STORAGE_URI = os.getenv('RATE_LIMIT_STORAGE', 'memory://')
    RATELIMIT_STRATEGY = 'fixed-window'
    RATELIMIT_HEADERS_ENABLED = True

    # File Uploads
    MAX_CONTENT_LENGTH = 100 * 1024  # 100KB

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/skyy.log')

    # Security
    BCRYPT_LOG_ROUNDS = 12
    LOGIN_DISABLED = False

    # CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour


class DevelopmentConfig(Config):
    """Development environment."""
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 'sqlite:///skyy_todo.db'
    )


class TestingConfig(Config):
    """Testing environment."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    LOGIN_DISABLED = True
    RATELIMIT_ENABLED = False


class StagingConfig(Config):
    """Staging environment."""
    DEBUG = True
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


class ProductionConfig(Config):
    """Production environment."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    BCRYPT_LOG_ROUNDS = 14
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20,
    }


# Config mapping
CONFIG_MAP = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
}


def get_config():
    """Get the current configuration based on environment."""
    env = os.getenv('FLASK_ENV', 'development')
    return CONFIG_MAP.get(env, DevelopmentConfig)
