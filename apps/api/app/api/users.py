from flask import jsonify, request

from app.api import api_v1
from app.service.user_service import (
    UserValidationError,
    UserAlreadyExistsError,
    create_user,
    list_users,
)

@api_v1.get("/users")
def get_users():
    """Return all users in descending creation order"""

    users = list_users()

    return jsonify(
        {
            "data": [user.to_dict() for user in users],
        }
    ), 200

@api_v1.post("/users")
def post_user():
    """Create one user from JSON request body"""

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify(
            {
                "error": {
                    "code": "INVALID_JSON",
                    "message": "Request body must be a JSON object.",
                }
            }
        ), 400

    try:
        user = create_user(payload)
    except UserValidationError as error:
        return jsonify(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(error),
                }
            }
        ), 400
    except UserAlreadyExistsError as error:
        return jsonify(
            {
                "error": {
                    "code": "CONFLICT",
                    "message": str(error),
                }
            }
        ), 409

    return jsonify(
        {
            "data": user.to_dict(),
        }
    ), 201