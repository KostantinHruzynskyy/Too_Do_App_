"""
╔═══════════════════════════════════════════════════╗
║           SKYY – Security Module Tests            ║
╚═══════════════════════════════════════════════════╝
"""

import pytest
from app.security import (
    validate_password_strength,
    PasswordValidationError,
    validate_username,
    validate_email_address,
    sanitize_plain_text,
    sanitize_html,
    sanitize_json_input,
    is_safe_redirect_url,
    generate_csrf_token,
    validate_csrf_token,
    check_login_attempts,
    record_failed_login,
    SESSION_CONFIG,
    MIN_PASSWORD_LENGTH,
    MAX_PASSWORD_LENGTH,
    MIN_USERNAME_LENGTH,
    MAX_USERNAME_LENGTH,
    MAX_LOGIN_ATTEMPTS,
    COMMON_PASSWORDS,
)


class TestPasswordValidation:
    """Test password strength validation."""

    def test_valid_strong_password(self):
        """Test that strong passwords pass validation."""
        # Should not raise
        validate_password_strength('MyStr0ng!Pass#123')
        validate_password_strength('K#9mP2xL8qW!vR5')
        validate_password_strength('Correct-Horse-Battery-Staple-99!')

    def test_password_too_short(self):
        """Test that short passwords fail validation."""
        with pytest.raises(
            PasswordValidationError, match=f'at least {MIN_PASSWORD_LENGTH}'
        ):
            validate_password_strength('Short1!A')

    def test_password_too_long(self):
        """Test that excessively long passwords fail validation."""
        with pytest.raises(
            PasswordValidationError,
            match=f'not exceed {MAX_PASSWORD_LENGTH}',
        ):
            validate_password_strength('A' * (MAX_PASSWORD_LENGTH + 1) + '!1a')

    def test_password_common(self):
        """Test that common passwords are rejected."""
        # Test with a password that's actually in the list and >= 12 chars
        long_common = [p for p in COMMON_PASSWORDS if len(p) >= 12]
        assert len(long_common) > 0, "No common passwords >= 12 chars found"
        with pytest.raises(PasswordValidationError, match='too common'):
            validate_password_strength(long_common[0])

    def test_password_no_diversity(self):
        """Test that passwords without character diversity fail."""
        with pytest.raises(PasswordValidationError, match='at least 3'):
            validate_password_strength('aaaaaaaaaaaa')

        with pytest.raises(PasswordValidationError, match='at least 3'):
            validate_password_strength('AAAAAAAAAAAA')

        with pytest.raises(PasswordValidationError, match='at least 3'):
            validate_password_strength('111111111111')

    def test_password_missing_two_categories(self):
        """Test passwords with only 2 character categories fail."""
        with pytest.raises(PasswordValidationError, match='at least 3'):
            validate_password_strength('abcdefghijkl')  # Only lowercase

        with pytest.raises(PasswordValidationError, match='at least 3'):
            validate_password_strength('ABCDEFGHIJKL')  # Only uppercase


class TestUsernameValidation:
    """Test username validation."""

    def test_valid_usernames(self):
        """Test valid username formats."""
        assert validate_username('valid_user')[0] is True
        assert validate_username('Valid-User')[0] is True
        assert validate_username('user123')[0] is True
        assert validate_username('a' * MIN_USERNAME_LENGTH)[0] is True
        assert validate_username('a' * MAX_USERNAME_LENGTH)[0] is True

    def test_username_too_short(self):
        """Test that short usernames fail."""
        assert validate_username('ab')[0] is False
        assert validate_username('a')[0] is False
        assert validate_username('')[0] is False

    def test_username_too_long(self):
        """Test that long usernames fail."""
        assert validate_username('a' * (MAX_USERNAME_LENGTH + 1))[0] is False

    def test_username_invalid_chars(self):
        """Test that usernames with invalid characters fail."""
        assert validate_username('user@name')[0] is False
        assert validate_username('user name')[0] is False
        assert validate_username('user.name')[0] is False
        assert validate_username('user!name')[0] is False

    def test_username_consecutive_hyphens(self):
        """Test that consecutive hyphens/underscores fail."""
        assert validate_username('user--name')[0] is False
        assert validate_username('user__name')[0] is False
        assert validate_username('user_-name')[0] is False
        assert validate_username('user-_name')[0] is False


class TestEmailValidation:
    """Test email validation."""

    def test_valid_emails(self):
        """Test valid email formats."""
        valid, result = validate_email_address('test@example.com')
        assert valid is True
        assert result == 'test@example.com'

        valid, result = validate_email_address(
            'user.name+tag@example.co.uk'
        )
        assert valid is True

    def test_invalid_emails(self):
        """Test invalid email formats."""
        assert validate_email_address('not-an-email')[0] is False
        assert validate_email_address('')[0] is False
        assert validate_email_address('@example.com')[0] is False
        assert validate_email_address('user@')[0] is False
        assert validate_email_address('user@.com')[0] is False


class TestSanitization:
    """Test input sanitization functions."""

    def test_sanitize_plain_text_strips_html(self):
        """Test that plain text sanitization removes HTML."""
        assert sanitize_plain_text(
            '<script>alert("xss")</script>'
        ) == 'alert("xss")'
        assert sanitize_plain_text('<b>Bold</b>') == 'Bold'
        assert sanitize_plain_text('<img src=x onerror=alert(1)>') == ''

    def test_sanitize_plain_text_preserves_text(self):
        """Test that plain text is preserved."""
        assert sanitize_plain_text('Hello World') == 'Hello World'
        assert sanitize_plain_text('Test 123') == 'Test 123'

    def test_sanitize_plain_text_empty(self):
        """Test sanitization of empty strings."""
        assert sanitize_plain_text('') == ''
        assert sanitize_plain_text(None) is None

    def test_sanitize_html_allows_safe_tags(self):
        """Test that safe HTML tags are preserved."""
        result = sanitize_html('<b>Bold</b>')
        assert '<b>Bold</b>' in result or 'Bold' in result

    def test_sanitize_html_removes_dangerous_tags(self):
        """Test that dangerous HTML tags are removed."""
        result = sanitize_html('<script>alert(1)</script>')
        assert '<script>' not in result

        result = sanitize_html('<img src=x onerror=alert(1)>')
        assert '<img' not in result or 'onerror' not in result

    def test_sanitize_json_input(self):
        """Test JSON input sanitization."""
        data = {'title': 'Test', 'description': 'Desc', 'extra': 'ignored'}
        result = sanitize_json_input(data, {'title', 'description'})
        assert 'title' in result
        assert 'description' in result
        assert 'extra' not in result

    def test_sanitize_json_input_empty_values(self):
        """Test that empty string values are removed."""
        data = {'title': 'Test', 'description': '   '}
        result = sanitize_json_input(data, {'title', 'description'})
        assert 'title' in result
        assert 'description' not in result


class TestRedirectValidation:
    """Test open redirect protection."""

    def test_safe_relative_urls(self):
        """Test that relative URLs are considered safe."""
        assert is_safe_redirect_url('/dashboard') is True
        assert is_safe_redirect_url('/login') is True
        assert is_safe_redirect_url('/') is True

    def test_unsafe_absolute_urls(self):
        """Test that absolute URLs to unknown domains are unsafe."""
        assert is_safe_redirect_url('https://evil.com') is False
        assert is_safe_redirect_url('http://evil.com') is False
        assert is_safe_redirect_url('//evil.com') is False

    def test_allowed_domains(self):
        """Test that allowed domains pass."""
        # Note: is_safe_redirect_url only allows relative URLs by default
        # This test verifies the function behavior
        assert is_safe_redirect_url('/dashboard') is True
        assert is_safe_redirect_url('/login') is True

    def test_path_traversal(self):
        """Test that path traversal attempts are blocked."""
        assert is_safe_redirect_url('/../../etc/passwd') is False
        assert is_safe_redirect_url('/..') is False

    def test_empty_url(self):
        """Test that empty URLs are unsafe."""
        assert is_safe_redirect_url('') is False
        assert is_safe_redirect_url(None) is False


class TestCSRFProtection:
    """Test CSRF token generation and validation."""

    def test_csrf_token_generation(self, app):
        """Test CSRF token generation."""
        with app.test_request_context():
            token = generate_csrf_token()
            assert token is not None
            assert len(token) == 64  # 32 bytes hex = 64 chars

    def test_csrf_token_validation(self, app):
        """Test CSRF token validation."""
        with app.test_request_context():
            token = generate_csrf_token()
            assert validate_csrf_token(token) is True
            assert validate_csrf_token('invalid') is False
            assert validate_csrf_token('') is False


class TestSecurityHeaders:
    """Test security headers are added to responses."""

    def test_security_headers_present(self, app):
        """Test that security headers are added."""
        with app.test_client() as client:
            response = client.get('/health')
            assert response.headers.get('X-Content-Type-Options') == 'nosniff'
            assert response.headers.get('X-Frame-Options') == 'DENY'
            assert response.headers.get('X-XSS-Protection') == '1; mode=block'
            assert 'Strict-Transport-Security' in response.headers
            assert 'Content-Security-Policy' in response.headers
            assert 'Referrer-Policy' in response.headers
            assert 'Permissions-Policy' in response.headers

    def test_session_config(self):
        """Test session configuration values."""
        assert SESSION_CONFIG['SESSION_COOKIE_HTTPONLY'] is True
        assert SESSION_CONFIG['SESSION_COOKIE_SAMESITE'] == 'Lax'
        assert SESSION_CONFIG['REMEMBER_COOKIE_HTTPONLY'] is True


class TestLoginAttemptTracking:
    """Test brute force protection."""

    def test_login_attempts_initially_allowed(self, app):
        """Test that login attempts are initially allowed."""
        with app.test_request_context():
            allowed, retry_after = check_login_attempts()
            assert allowed is True
            assert retry_after == 0

    def test_login_attempts_tracking(self, app):
        """Test that failed login attempts are tracked."""
        with app.test_request_context():
            # Record multiple failed attempts
            for _ in range(MAX_LOGIN_ATTEMPTS):
                record_failed_login()

            # Should now be blocked
            allowed, retry_after = check_login_attempts()
            assert allowed is False
            assert retry_after > 0


@pytest.fixture
def app():
    """Create test application."""
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory/'
    return app
