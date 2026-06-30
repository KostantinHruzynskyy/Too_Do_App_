"""
╔═══════════════════════════════════════════════════╗
║           SKYY – Application Factory               ║
╚═══════════════════════════════════════════════════╝
"""

from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_migrate import Migrate
from dotenv import load_dotenv
from app.security import (
    add_security_headers,
    SESSION_CONFIG,
    validate_request_size,
    rate_limit_key_func,
    RATE_LIMIT_GLOBAL,
    generate_csrf_token,
)
from app.config import get_config
from app.logger import setup_logging
import os

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
limiter = Limiter(
    key_func=rate_limit_key_func,
    default_limits=[RATE_LIMIT_GLOBAL],
    storage_uri="memory://",
)
migrate = Migrate()


def create_app():
    app = Flask(__name__)

    # ─── Load Configuration ───
    config = get_config()
    app.config.from_object(config)

    # Override with environment variables if present
    secret_key = os.getenv('SECRET_KEY', app.config.get('SECRET_KEY'))
    app.config['SECRET_KEY'] = secret_key
    db_uri = os.getenv(
        'DATABASE_URL', app.config.get('SQLALCHEMY_DATABASE_URI')
    )
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri

    # Apply session hardening
    for key, value in SESSION_CONFIG.items():
        app.config[key] = value

    # ─── Initialize Extensions ───
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    limiter.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.session_protection = 'strong'

    # ─── Setup Logging ───
    setup_logging(app)

    # ─── Request Hooks ───
    @app.before_request
    def before_request():
        """Run security checks before every request."""
        validate_request_size()
        g.csrf_token = generate_csrf_token()

    @app.after_request
    def after_request(response):
        """Add security headers to every response."""
        return add_security_headers(response)

    # ─── Error Handlers ───
    @app.errorhandler(400)
    def bad_request(e):
        return {'error': 'Bad request.'}, 400

    @app.errorhandler(403)
    def forbidden(e):
        return {'error': 'Forbidden.'}, 403

    @app.errorhandler(404)
    def not_found(e):
        return {'error': 'Not found.'}, 404

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return {'error': 'Request body too large.'}, 413

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return {'error': 'Rate limit exceeded. Please slow down.'}, 429

    @app.errorhandler(500)
    def internal_error(e):
        return {'error': 'Internal server error.'}, 500

    # ─── Register Blueprints ───
    from app.routes import main, auth
    from app.health import health
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(health)

    # ─── Create Tables ───
    with app.app_context():
        db.create_all()

    return app
