from flask import jsonify, request
from flask_jwt_extended import(
    create_access_token,
    get_jwt_identity,
    jwt_required,
)

from app.api import api_v1
from app.extensions import db
from app.models.user import User
from app.service.user_service import(
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserValidationError,
    authenticate_user,
    register_user,
)

def error_response(code: str, message: str, status: int):
    return jsonify(
        {
            "error": {
                "code": code,
                "message": message,
            }
        }
    ), status

@api_v1.post("/auth/register")
def register():
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return error_response(
            "INVALID_JSON",
            "Request body must be a JSON object.",
            400,
        )

    try:
        user = register_user(payload)
    except UserValidationError as error:
        return error_response("VALIDATION_ERROR", str(error), 400)
    except UserAlreadyExistsError as error:
        return error_response("CONFLICT", str(error), 409)

    return jsonify({"data": user.to_dict()}),201

@api_v1.post("/auth/login")
def login():
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return error_response("INVALID_JSON", "Request body must be a JSON object.", 400,)

    try:
        user = authenticate_user(payload)
    except InvalidCredentialsError as error:
        return error_response("INVALID_CREDENTIALS", str(error), 401)

    access_token = create_access_token(identity=str(user.id))

    return jsonify(
        {
            "data": {
                "access_token": access_token,
                "token_type": "Bearer",
                "user": user.to_dict(),
            }
        }
    ), 200

@api_v1.get("/auth/me")
@jwt_required()
def get_current_user():
    identity = get_jwt_identity()

    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return error_response(
            "UNAUTHORIZED",
            "Invalid account identity.",
            401,
        )

    user = db.session.get(User, user_id)

    if user is None:
        return error_response(
            "UNAUTHORIZED",
            "Account no longer exists.",
            401,
        )

    return jsonify({
        "data": user.to_dict()
    }), 200
