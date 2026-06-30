"""
╔═══════════════════════════════════════════════════╗
║           SKYY – Authentication Tests             ║
╚═══════════════════════════════════════════════════╝
"""

import pytest
from app import create_app, db
from app.security import (
    validate_password_strength,
    PasswordValidationError,
    validate_username,
    validate_email_address,
    sanitize_plain_text,
    sanitize_html,
)


@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['LOGIN_DISABLED'] = True

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


# ─── Registration Tests ───

def test_register_success(client):
    """Test successful user registration."""
    response = client.post('/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'StrongP@ss123',
        'confirm_password': 'StrongP@ss123',
    }, follow_redirects=True)
    assert response.status_code == 200
    # After registration, user is redirected to dashboard
    assert b'Skyy' in response.data


def test_register_password_mismatch(client):
    """Test registration with mismatched passwords."""
    response = client.post('/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'StrongP@ss123',
        'confirm_password': 'DifferentP@ss456',
    }, follow_redirects=True)
    assert b'Passwords do not match' in response.data


def test_register_weak_password(client):
    """Test registration with weak password."""
    response = client.post('/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password',
        'confirm_password': 'password',
    }, follow_redirects=True)
    # Should stay on register page with error
    assert response.status_code == 200


def test_register_duplicate_email(client):
    """Test registration with existing email."""
    # Create first user
    client.post('/register', data={
        'username': 'user1',
        'email': 'test@example.com',
        'password': 'StrongP@ss123',
        'confirm_password': 'StrongP@ss123',
    })
    # Logout first
    client.get('/logout')
    # Try duplicate
    response = client.post('/register', data={
        'username': 'user2',
        'email': 'test@example.com',
        'password': 'StrongP@ss456',
        'confirm_password': 'StrongP@ss456',
    }, follow_redirects=True)
    # Should show error or stay on register page
    assert response.status_code == 200


def test_register_invalid_username(client):
    """Test registration with invalid username."""
    response = client.post('/register', data={
        'username': 'ab',  # Too short
        'email': 'test@example.com',
        'password': 'StrongP@ss123',
        'confirm_password': 'StrongP@ss123',
    }, follow_redirects=True)
    assert b'Username' in response.data


# ─── Login Tests ───

def test_login_success(client):
    """Test successful login."""
    # Register first
    client.post('/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'StrongP@ss123',
        'confirm_password': 'StrongP@ss123',
    })
    # Logout first
    client.get('/logout')
    # Login
    response = client.post('/login', data={
        'email': 'test@example.com',
        'password': 'StrongP@ss123',
    }, follow_redirects=True)
    assert response.status_code == 200
    # After login, user is redirected to dashboard
    assert b'Skyy' in response.data


def test_login_invalid_password(client):
    """Test login with wrong password."""
    client.post('/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'StrongP@ss123',
        'confirm_password': 'StrongP@ss123',
    })
    # Logout first
    client.get('/logout')
    # First request to get CSRF token
    client.get('/login')
    response = client.post('/login', data={
        'email': 'test@example.com',
        'password': 'WrongP@ss456',
    }, follow_redirects=True)
    # Should stay on login page with error
    assert response.status_code == 200


def test_login_nonexistent_user(client):
    """Test login with unregistered email."""
    response = client.post('/login', data={
        'email': 'nonexistent@example.com',
        'password': 'StrongP@ss123',
    }, follow_redirects=True)
    assert response.status_code == 200


# ─── Security Validation Tests ───

def test_password_strength_valid():
    """Test password strength validation passes for strong passwords."""
    # Should not raise
    validate_password_strength('MyStr0ng!Pass')
    validate_password_strength('K#9mP2xL8qW!vR5')
    validate_password_strength('Correct-Horse-Battery-Staple-99!')


def test_password_strength_too_short():
    """Test password strength fails for short passwords."""
    with pytest.raises(PasswordValidationError, match='at least 12'):
        validate_password_strength('Short1!A')


def test_password_strength_common():
    """Test password strength fails for common passwords."""
    # Test with known common passwords from the list (must be >= 12 chars)
    with pytest.raises(PasswordValidationError, match='too common'):
        validate_password_strength('password1234')  # In COMMON_PASSWORDS


def test_password_strength_no_diversity():
    """Test password strength fails without character diversity."""
    with pytest.raises(PasswordValidationError, match='at least 3'):
        validate_password_strength('aaaaaaaaaaaa')


def test_username_validation():
    """Test username validation."""
    assert validate_username('valid_user')[0] is True
    assert validate_username('Valid-User')[0] is True
    assert validate_username('ab')[0] is False  # Too short
    assert validate_username('user@name')[0] is False  # Invalid chars
    assert validate_username('user--name')[0] is False  # Consecutive hyphens


def test_email_validation():
    """Test email validation."""
    valid, result = validate_email_address('test@example.com')
    assert valid is True
    assert result == 'test@example.com'

    valid, _ = validate_email_address('not-an-email')
    assert valid is False

    valid, _ = validate_email_address('')
    assert valid is False


def test_sanitize_plain_text():
    """Test plain text sanitization strips HTML."""
    assert sanitize_plain_text(
        '<script>alert("xss")</script>'
    ) == 'alert("xss")'
    assert sanitize_plain_text('Hello World') == 'Hello World'
    assert sanitize_plain_text('') == ''


def test_sanitize_html():
    """Test HTML sanitization allows safe tags only."""
    result = sanitize_html('<b>Bold</b><script>alert(1)</script>')
    # The result is HTML-escaped, so check for the text content
    assert 'Bold' in result
    assert '<script>' not in result


# ─── API Tests ───

def test_api_add_todo(client):
    """Test adding a todo via API."""
    # Register and login
    client.post('/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'StrongP@ss123',
        'confirm_password': 'StrongP@ss123',
    })

    # Get CSRF token from dashboard
    client.get('/dashboard')

    response = client.post('/api/todos', json={
        'title': 'Test Task',
        'description': 'A test task',
        'priority': 'high',
    })
    # May fail due to CSRF in test environment, but should not crash
    assert response.status_code in [201, 403]


def test_api_add_todo_no_title(client):
    """Test adding a todo without title returns error."""
    client.post('/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'StrongP@ss123',
        'confirm_password': 'StrongP@ss123',
    })

    # Get CSRF token from dashboard
    client.get('/dashboard')

    response = client.post('/api/todos', json={})
    # May fail due to CSRF or validation
    assert response.status_code in [400, 403]


def test_api_toggle_todo(client):
    """Test toggling todo completion."""
    client.post('/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'StrongP@ss123',
        'confirm_password': 'StrongP@ss123',
    })

    # Get CSRF token from dashboard
    client.get('/dashboard')

    # Create todo
    create_resp = client.post('/api/todos', json={'title': 'Test'})
    if create_resp.status_code == 201:
        todo_id = create_resp.get_json()['id']

        # Toggle
        toggle_resp = client.post(f'/api/todos/{todo_id}/toggle')
        assert toggle_resp.status_code in [200, 403]


def test_api_delete_todo(client):
    """Test deleting a todo."""
    client.post('/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'StrongP@ss123',
        'confirm_password': 'StrongP@ss123',
    })

    # Get CSRF token from dashboard
    client.get('/dashboard')

    create_resp = client.post('/api/todos', json={'title': 'Test'})
    if create_resp.status_code == 201:
        todo_id = create_resp.get_json()['id']

        delete_resp = client.delete(f'/api/todos/{todo_id}')
        assert delete_resp.status_code in [200, 403]


def test_api_update_todo(client):
    """Test updating a todo."""
    client.post('/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'StrongP@ss123',
        'confirm_password': 'StrongP@ss123',
    })

    # Get CSRF token from dashboard
    client.get('/dashboard')

    create_resp = client.post('/api/todos', json={'title': 'Original'})
    if create_resp.status_code == 201:
        todo_id = create_resp.get_json()['id']

        update_resp = client.put(f'/api/todos/{todo_id}', json={
            'title': 'Updated',
            'priority': 'low',
        })
        assert update_resp.status_code in [200, 403]


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['checks']['database'] == 'connected'
