from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.api import api_v1
from app.extensions import db
from app.models.user import User
from app.services.organization_service import (
    OrganizationError,
    create_organization,
    get_organization,
    list_organizations,
)
from app.services.membership_service import add_member, list_members
from app.services.project_service import (
    create_project,
    get_project,
    list_projects,
)

def current_user_id() -> int:
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        raise OrganizationError(
            "Invalid account identity.",
            "UNAUTHORIZED",
            401,
        )

    if db.session.get(User, user_id) is None:
        raise OrganizationError(
            "Account no longer exists.",
            "UNAUTHORIZED",
            401,
        )

    return user_id


@api_v1.errorhandler(OrganizationError)
def handle_organization_error(error):
    return jsonify(
        {
            "error": {
                "code": error.code,
                "message": str(error),
            }
        }
    ), error.status


@api_v1.post("/organizations")
@jwt_required()
def post_organization():
    user_id = current_user_id()
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        raise OrganizationError(
            "Request body must be a JSON object.",
            "INVALID_JSON",
            400,
        )

    organization, role = create_organization(user_id, payload)

    return jsonify(
        {
            "data": {
                **organization.to_dict(),
                "role": role,
            }
        }
    ), 201


@api_v1.get("/organizations")
@jwt_required()
def get_organizations():
    user_id = current_user_id()
    rows = list_organizations(user_id)

    return jsonify(
        {
            "data": [
                {
                    **organization.to_dict(),
                    "role": role,
                }
                for organization, role in rows
            ]
        }
    ), 200


@api_v1.get("/organizations/<int:organization_id>")
@jwt_required()
def get_organization_detail(organization_id: int):
    user_id = current_user_id()
    organization, role = get_organization(user_id, organization_id)

    return jsonify(
        {
            "data": {
                **organization.to_dict(),
                "role": role,
            }
        }
    ), 200

@api_v1.get("/organizations/<int:organization_id>/members")
@jwt_required()
def get_organization_members(organization_id: int):
    actor_id = current_user_id()
    rows = list_members(actor_id, organization_id)

    return jsonify(
        {
            "data": [
                {
                    "user_id": user.id,
                    "email": user.email,
                    "display_name": user.display_name,
                    "role": role,
                }
                for user, role in rows
            ]
        }
    ), 200


@api_v1.post("/organizations/<int:organization_id>/members")
@jwt_required()
def post_organization_member(organization_id: int):
    actor_id = current_user_id()
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        raise OrganizationError(
            "Request body must be a JSON object.",
            "INVALID_JSON",
            400,
        )

    user, role = add_member(actor_id, organization_id, payload)

    return jsonify(
        {
            "data": {
                "user_id": user.id,
                "email": user.email,
                "display_name": user.display_name,
                "role": role,
            }
        }
    ), 201

@api_v1.get("/organizations/<int:organization_id>/projects")
@jwt_required()
def get_organization_projects(organization_id: int):
    projects = list_projects(current_user_id(), organization_id)

    return jsonify(
        {
            "data": [project.to_dict() for project in projects],
        }
    ), 200


@api_v1.post("/organizations/<int:organization_id>/projects")
@jwt_required()
def post_organization_project(organization_id: int):
    actor_id = current_user_id()
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        raise OrganizationError(
            "Request body must be a JSON object.",
            "INVALID_JSON",
            400,
        )

    project = create_project(actor_id, organization_id, payload)

    return jsonify({"data": project.to_dict()}), 201


@api_v1.get(
    "/organizations/<int:organization_id>/projects/<int:project_id>"
)
@jwt_required()
def get_organization_project(
    organization_id: int,
    project_id: int,
):
    project = get_project(
        current_user_id(),
        organization_id,
        project_id,
    )

    return jsonify({"data": project.to_dict()}), 200