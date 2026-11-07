from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.organizations import OrganizationMembership
from app.models.user import User
from app.services.organization_service import (
    OrganizationError,
    get_organization,
)


def list_members(actor_id: int, organization_id: int):
    # Confirm membership before exposing the team's account information.
    get_organization(actor_id, organization_id)

    statement = (
        select(User, OrganizationMembership.role)
        .join(
            OrganizationMembership,
            OrganizationMembership.user_id == User.id,
        )
        .where(
            OrganizationMembership.organization_id == organization_id,
        )
        .order_by(User.id)
    )

    return db.session.execute(statement).all()


def add_member(
    actor_id: int,
    organization_id: int,
    payload: dict,
) -> tuple[User, str]:
    _, actor_role = get_organization(actor_id, organization_id)

    if actor_role != "owner":
        raise OrganizationError(
            "Only the organization owner can add members.",
            "FORBIDDEN",
            403,
        )

    email = payload.get("email")
    role = payload.get("role", "member")

    if not isinstance(email, str) or not email.strip():
        raise OrganizationError(
            "email is required and must be a non-empty string.",
            "VALIDATION_ERROR",
            400,
        )

    if role not in ("member", "admin"):
        raise OrganizationError(
            "role must be member or admin.",
            "VALIDATION_ERROR",
            400,
        )

    email = email.strip().lower()

    user = db.session.scalar(
        select(User).where(User.email == email)
    )

    if user is None:
        raise OrganizationError(
            "No Shipyard account was found for that email.",
            "USER_NOT_FOUND",
            404,
        )

    membership = OrganizationMembership(
        organization_id=organization_id,
        user_id=user.id,
        role=role,
    )

    try:
        db.session.add(membership)
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()

        existing_membership = db.session.get(
            OrganizationMembership,
            (organization_id, user.id),
        )

        if existing_membership is not None:
            raise OrganizationError(
                "This user already belongs to the organization.",
                "CONFLICT",
                409,
            ) from error

        raise

    return user, membership.role