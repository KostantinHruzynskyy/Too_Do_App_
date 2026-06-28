"""
╔═══════════════════════════════════════════════════╗
║           SKYY – Health Check Tests               ║
╚═══════════════════════════════════════════════════╝
"""

import pytest
from app import create_app, db


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check_success(self, client):
        """Test successful health check."""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert 'checks' in data
        assert 'timestamp' in data['checks']
        assert 'version' in data['checks']
        assert data['checks']['database'] == 'connected'

    def test_health_check_returns_json(self, client):
        """Test that health check returns JSON."""
        response = client.get('/health')
        assert response.content_type == 'application/json'

    def test_health_check_has_required_fields(self, client):
        """Test that health check has all required fields."""
        response = client.get('/health')
        data = response.get_json()
        
        assert 'status' in data
        assert 'checks' in data
        assert 'timestamp' in data['checks']
        assert 'version' in data['checks']
        assert 'database' in data['checks']
        assert 'users' in data['checks']
        assert 'todos' in data['checks']

    def test_health_check_version_format(self, client):
        """Test that version follows semantic versioning."""
        response = client.get('/health')
        data = response.get_json()
        version = data['checks']['version']
        
        # Should be in format X.Y.Z
        parts = version.split('.')
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)

    def test_health_check_timestamp_format(self, client):
        """Test that timestamp is in ISO format."""
        from datetime import datetime
        
        response = client.get('/health')
        data = response.get_json()
        timestamp = data['checks']['timestamp']
        
        # Should be parseable as ISO format
        try:
            datetime.fromisoformat(timestamp)
        except ValueError:
            pytest.fail(f"Timestamp '{timestamp}' is not valid ISO format")

    def test_health_check_no_auth_required(self, client):
        """Test that health check doesn't require authentication."""
        response = client.get('/health')
        assert response.status_code == 200

    def test_health_check_database_connected(self, client):
        """Test that database connection is reported."""
        response = client.get('/health')
        data = response.get_json()
        assert data['checks']['database'] == 'connected'

    def test_health_check_counts_present(self, client):
        """Test that user and todo counts are present."""
        response = client.get('/health')
        data = response.get_json()
        
        # Should be integers (0 or more)
        assert isinstance(data['checks']['users'], int)
        assert isinstance(data['checks']['todos'], int)
        assert data['checks']['users'] >= 0
        assert data['checks']['todos'] >= 0


@pytest.fixture
def app():
    """Create test application."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory/'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()