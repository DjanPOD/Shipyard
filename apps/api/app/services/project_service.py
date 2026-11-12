from sqlalchemy import select

from app.extensions import db
from app.models.project import Project
from app.services.organization_service import (
    OrganizationError,
    get_organization,
)


def list_projects(actor_id: int, organization_id: int):
    get_organization(actor_id, organization_id)

    statement = (
        select(Project)
        .where(Project.organization_id == organization_id)
        .order_by(Project.id.desc())
    )

    return list(db.session.scalars(statement))


def create_project(
    actor_id: int,
    organization_id: int,
    payload: dict,
) -> Project:
    _, role = get_organization(actor_id, organization_id)

    if role not in ("owner", "admin"):
        raise OrganizationError(
            "Only owners and admins can create projects.",
            "FORBIDDEN",
            403,
        )

    name = payload.get("name")
    description = payload.get("description", "")

    if not isinstance(name, str) or not name.strip():
        raise OrganizationError(
            "name is required and must be a non-empty string.",
            "VALIDATION_ERROR",
            400,
        )

    name = name.strip()

    if len(name) > 100:
        raise OrganizationError(
            "name must be 100 characters or fewer.",
            "VALIDATION_ERROR",
            400,
        )

    if not isinstance(description, str):
        raise OrganizationError(
            "description must be a string.",
            "VALIDATION_ERROR",
            400,
        )

    description = description.strip()

    if len(description) > 5000:
        raise OrganizationError(
            "description must be 5000 characters or fewer.",
            "VALIDATION_ERROR",
            400,
        )

    project = Project(
        organization_id=organization_id,
        name=name,
        description=description,
    )

    try:
        db.session.add(project)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return project


def get_project(
    actor_id: int,
    organization_id: int,
    project_id: int,
) -> Project:
    get_organization(actor_id, organization_id)

    statement = select(Project).where(
        Project.id == project_id,
        Project.organization_id == organization_id,
    )

    project = db.session.scalar(statement)

    if project is None:
        raise OrganizationError(
            "Project not found.",
            "NOT_FOUND",
            404,
        )

    return project