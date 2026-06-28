"""
╔═══════════════════════════════════════════════════╗
║           SKYY – Health Check Endpoint            ║
║  Used by Docker/K8s for liveness & readiness      ║
╚═══════════════════════════════════════════════════╝
"""

from flask import Blueprint, jsonify
from flask_login import current_user
from app import db
from app.models import User, Todo
from datetime import datetime, timezone

health = Blueprint('health', __name__)


@health.route('/health')
def health_check():
    """Comprehensive health check endpoint."""
    status = 'healthy'
    checks = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': '2.0.0',
    }

    # Database check
    try:
        db.session.execute(db.text('SELECT 1'))
        checks['database'] = 'connected'
    except Exception as e:
        checks['database'] = f'error: {str(e)}'
        status = 'degraded'

    # User count (quick sanity check)
    try:
        user_count = User.query.count()
        checks['users'] = user_count
    except Exception as e:
        checks['users'] = f'error: {str(e)}'
        status = 'degraded'

    # Todo count
    try:
        todo_count = Todo.query.count()
        checks['todos'] = todo_count
    except Exception as e:
        checks['todos'] = f'error: {str(e)}'
        status = 'degraded'

    response_code = 200 if status == 'healthy' else 503
    return jsonify({'status': status, 'checks': checks}), response_code