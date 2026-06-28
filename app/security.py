"""
╔═══════════════════════════════════════════════════╗
║           SKYY SECURITY MODULE                    ║
║  Enterprise-grade protection layer                ║
╚═══════════════════════════════════════════════════╝
"""

import re
import html
import bleach
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify, current_app, abort, g, session
from email_validator import validate_email, EmailNotValidError

# ═══════════════════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════════════════

MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 128
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 32
MAX_EMAIL_LENGTH = 120
MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 2000
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_MINUTES = 15

RATE_LIMIT_LOGIN = "10 per minute"
RATE_LIMIT_REGISTER = "5 per minute"
RATE_LIMIT_API = "60 per minute"
RATE_LIMIT_GLOBAL = "200 per minute"

CSP_POLICY = {
    'default-src': ["'self'"],
    'script-src': ["'self'", "https://cdnjs.cloudflare.com", "https://kit.fontawesome.com"],
    'style-src': ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com", "https://cdnjs.cloudflare.com"],
    'font-src': ["'self'", "https://fonts.gstatic.com", "https://cdnjs.cloudflare.com"],
    'img-src': ["'self'", "data:", "https:"],
    'connect-src': ["'self'"],
    'form-action': ["'self'"],
    'frame-ancestors': ["'none'"],
    'base-uri': ["'self'"],
}

ALLOWED_DOMAINS = {'127.0.0.1', 'localhost', '192.168.1.2'}

COMMON_PASSWORDS = {
    'password', '123456', '12345678', 'qwerty', 'abc123',
    'monkey', 'letmein', 'dragon', '111111', 'baseball',
    'iloveyou', 'trustno1', 'sunshine', 'master', '123123',
    'welcome', 'shadow', 'ashley', 'football', 'jesus',
    'michael', 'ninja', 'mustang', 'password1', 'admin',
    'skyy', 'skyy2024', 'skyy123', 'password123',
    'password1234', '123456789', '1234567890', 'qwerty123',
    'password12', 'iloveyou1', 'sunshine1', 'princess',
    'charlie', 'donald', 'football1', 'whatever', 'trustno1',
}

ALLOWED_HTML_TAGS = ['b', 'i', 'u', 'em', 'strong', 'a', 'br', 'p']
ALLOWED_HTML_ATTRS = {'a': ['href', 'title', 'rel']}


# ═══════════════════════════════════════════════════════════════
#  PASSWORD VALIDATION
# ═══════════════════════════════════════════════════════════════

class PasswordValidationError(Exception):
    pass


def validate_password_strength(password: str) -> None:
    """Validate password against enterprise security policy."""
    if len(password) < MIN_PASSWORD_LENGTH:
        raise PasswordValidationError(
            f'Password must be at least {MIN_PASSWORD_LENGTH} characters long.'
        )
    if len(password) > MAX_PASSWORD_LENGTH:
        raise PasswordValidationError(
            f'Password must not exceed {MAX_PASSWORD_LENGTH} characters.'
        )
    if password.lower() in COMMON_PASSWORDS:
        raise PasswordValidationError('This password is too common.')
    checks = {
        'uppercase': bool(re.search(r'[A-Z]', password)),
        'lowercase': bool(re.search(r'[a-z]', password)),
        'digit': bool(re.search(r'\d', password)),
        'special': bool(re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;`~]', password)),
    }
    passed = sum(checks.values())
    if passed < 3:
        missing = [k for k, v in checks.items() if not v]
        raise PasswordValidationError(
            f'Password must contain at least 3 of: uppercase, lowercase, digit, special. '
            f'Missing: {", ".join(missing)}.'
        )


# ═══════════════════════════════════════════════════════════════
#  INPUT SANITIZATION
# ═══════════════════════════════════════════════════════════════

def sanitize_html(text: str) -> str:
    if not text:
        return text
    cleaned = bleach.clean(text, tags=ALLOWED_HTML_TAGS, attributes=ALLOWED_HTML_ATTRS, strip=True)
    return html.escape(cleaned, quote=True)


def sanitize_plain_text(text: str) -> str:
    if not text:
        return text
    cleaned = bleach.clean(text, tags=[], strip=True)
    cleaned = ' '.join(cleaned.split())
    return cleaned


def sanitize_json_input(data: dict, allowed_fields: set) -> dict:
    if not data or not isinstance(data, dict):
        return {}
    sanitized = {}
    for field in allowed_fields:
        if field not in data:
            continue
        value = data[field]
        if isinstance(value, str):
            value = value.strip()
            if not value:
                continue
        sanitized[field] = value
    return sanitized


# ═══════════════════════════════════════════════════════════════
#  USERNAME / EMAIL VALIDATION
# ═══════════════════════════════════════════════════════════════

def validate_username(username: str) -> tuple[bool, str]:
    if not username:
        return False, 'Username is required.'
    username = username.strip()
    if len(username) < MIN_USERNAME_LENGTH:
        return False, f'Username must be at least {MIN_USERNAME_LENGTH} characters.'
    if len(username) > MAX_USERNAME_LENGTH:
        return False, f'Username must not exceed {MAX_USERNAME_LENGTH} characters.'
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, 'Username can only contain letters, numbers, hyphens, and underscores.'
    if re.search(r'[-_]{2,}', username):
        return False, 'Username cannot contain consecutive hyphens or underscores.'
    return True, ''


def validate_email_address(email: str) -> tuple[bool, str]:
    if not email:
        return False, 'Email is required.'
    try:
        validation = validate_email(email, check_deliverability=False)
        return True, validation.normalized
    except EmailNotValidError as e:
        return False, str(e)


# ═══════════════════════════════════════════════════════════════
#  OPEN REDIRECT PROTECTION
# ═══════════════════════════════════════════════════════════════

def is_safe_redirect_url(target: str) -> bool:
    if not target:
        return False
    if target.startswith(('//', 'http://', 'https://')):
        from urllib.parse import urlparse
        parsed = urlparse(target)
        hostname = parsed.hostname or ''
        if hostname not in ALLOWED_DOMAINS and not hostname.endswith('.allowed-domain.com'):
            return False
    if '..' in target.split('/') and target != '/':
        return False
    if not target.startswith('/'):
        return False
    return True


# ═══════════════════════════════════════════════════════════════
#  CSRF TOKEN (session-based for API)
# ═══════════════════════════════════════════════════════════════

def generate_csrf_token() -> str:
    """Generate a cryptographically secure CSRF token stored in session."""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']


def validate_csrf_token(token: str) -> bool:
    """Validate CSRF token (constant-time comparison)."""
    stored_token = session.get('_csrf_token')
    if not token or not stored_token:
        return False
    return secrets.compare_digest(stored_token, token)


# ═══════════════════════════════════════════════════════════════
#  RATE LIMITING KEY FUNCTION
# ═══════════════════════════════════════════════════════════════

def rate_limit_key_func() -> str:
    ip = request.remote_addr or 'unknown'
    ua = request.headers.get('User-Agent', 'unknown')[:50]
    return f"{ip}:{ua}"


# ═══════════════════════════════════════════════════════════════
#  REQUEST SIZE LIMITER
# ═══════════════════════════════════════════════════════════════

MAX_REQUEST_SIZE = 1024 * 100


def validate_request_size():
    content_length = request.content_length
    if content_length and content_length > MAX_REQUEST_SIZE:
        abort(413, description='Request body too large.')


# ═══════════════════════════════════════════════════════════════
#  DECORATORS
# ═══════════════════════════════════════════════════════════════

def require_csrf(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ('POST', 'PUT', 'DELETE'):
            token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
            if not validate_csrf_token(token):
                return jsonify({'error': 'CSRF validation failed.'}), 403
        return f(*args, **kwargs)
    return decorated_function


def validate_content_type(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ('POST', 'PUT'):
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json.'}), 415
        return f(*args, **kwargs)
    return decorated_function


# ═══════════════════════════════════════════════════════════════
#  SECURITY HEADERS HELPER
# ═══════════════════════════════════════════════════════════════

def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = (
        'camera=(), microphone=(), geolocation=(), '
        'payment=(), usb=(), fullscreen=(self)'
    )
    csp_directives = []
    for directive, sources in CSP_POLICY.items():
        csp_directives.append(f"{directive} {' '.join(sources)}")
    response.headers['Content-Security-Policy'] = '; '.join(csp_directives)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


# ═══════════════════════════════════════════════════════════════
#  SESSION CONFIGURATION
# ═══════════════════════════════════════════════════════════════

SESSION_CONFIG = {
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SECURE': False,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'SESSION_COOKIE_NAME': '__Secure-Skyy-Session',
    'PERMANENT_SESSION_LIFETIME': timedelta(hours=4),
    'REMEMBER_COOKIE_HTTPONLY': True,
    'REMEMBER_COOKIE_SECURE': False,
    'REMEMBER_COOKIE_SAMESITE': 'Lax',
    'REMEMBER_COOKIE_DURATION': timedelta(days=30),
    'REMEMBER_COOKIE_NAME': '__Secure-Skyy-Remember',
}


# ═══════════════════════════════════════════════════════════════
#  LOGIN ATTEMPT TRACKING
# ═══════════════════════════════════════════════════════════════

_login_attempts = {}


def check_login_attempts() -> tuple[bool, int]:
    ip = request.remote_addr or 'unknown'
    now = datetime.now(timezone.utc)
    if ip in _login_attempts:
        _login_attempts[ip] = [
            t for t in _login_attempts[ip]
            if t > now - timedelta(minutes=LOGIN_LOCKOUT_MINUTES)
        ]
        if len(_login_attempts[ip]) >= MAX_LOGIN_ATTEMPTS:
            retry_after = int(
                (_login_attempts[ip][0] + timedelta(minutes=LOGIN_LOCKOUT_MINUTES) - now).total_seconds()
            )
            return False, max(retry_after, 0)
    return True, 0


def record_failed_login():
    ip = request.remote_addr or 'unknown'
    if ip not in _login_attempts:
        _login_attempts[ip] = []
    _login_attempts[ip].append(datetime.now(timezone.utc))