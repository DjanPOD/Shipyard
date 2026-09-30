from flask import Flask
from flask_cors import CORS

from app.core.config import Config
from app.extensions import db, migrate

def create_app(config_object=Config):
    """Create, configure, and return a Flask application instance"""

    app = Flask(__name__)
    app.config.from_object(config_object)

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": [
                    "http://localhost:5173"
                ]
            }
        },
    )

    db.init_app(app)
    migrate.init_app(app, db)

    from app.api import api_v1
    from app.api import health # noqa: F401

    app.register_blueprint(api_v1)

    return app