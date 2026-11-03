from flask import Flask, jsonify
from flask_cors import CORS

from app.core.config import Config
from app.extensions import db, jwt, migrate

def create_app(config_object=Config):
    """Create, configure, and return a Flask application instance"""

    app = Flask(__name__)
    app.config.from_object(config_object)

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": [
                    ["http://localhost:5173"],
                ]
            }
        },
    )

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    @jwt.unauthorized_loader
    def missing_token(reason):
        return jsonify(
            {
                "error":{
                    "code": "UNAUTHORIZED",
                    "message": "An access token is required."
                }
            }
        ), 401

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return jsonify(
            {
                "error":{
                    "code": "INVALID_TOKEN",
                    "message": "The access token invalid."
                }
            }
        ), 401

    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_payload):
        return jsonify(
            {
                "error":{
                    "code": "TOKEN_EXPIRED",
                    "message": "The access token has expired. Log in again."
                }
            }
        ), 401

    from app import models # noqa: F401
    from app.api import api_v1
    from app.api import health, auth # noqa: F401

    app.register_blueprint(api_v1)

    return app