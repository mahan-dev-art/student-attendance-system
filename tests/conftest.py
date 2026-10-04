import pytest
from app import create_app
from config import Config
from models import db

class TestConfig(Config):
    TESTING=True
    WTF_CSRF_ENABLED=False
    SQLALCHEMY_DATABASE_URI="sqlite:///:memory:"
    SECRET_KEY="test-secret"
    ESP32_API_KEY="test-api-key"

@pytest.fixture()
def app():
    app=create_app(TestConfig)
    with app.app_context(): db.drop_all(); db.create_all()
    yield app
    with app.app_context(): db.session.remove(); db.drop_all()

@pytest.fixture()
def client(app): return app.test_client()
