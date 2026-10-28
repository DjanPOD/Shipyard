import pytest

from app import create_app
from app.extensions import db

class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False


@pytest.fixture()
def app():
    """Create a new application and empty database for every test."""

    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()

        yield app

        db.session.remove()
        db.drop_all()

@pytest.fixture()
def client(app):
    """Provide Flask's test client for making HTTP requests."""

    return app.test_client()