from sqlalchemy import select

from app.extensions import db
from app.models.organizations import Organization, OrganizationMembership

class OrganizationError(Exception):
    def __init__(self, message: str, code: str, status: int):
        super().__init__(message)
        self.code = code
        self.status = status


def create_organization(
    user_id: int,
    payload: dict,
) -> tuple[Organization, str]:
    name = payload.get("name")

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

    organization = Organization(name=name)

    try:
        db.session.add(organization)

        # Insert within the transaction so the generated ID is available.
        db.session.flush()

        membership = OrganizationMembership(
            organization_id=organization.id,
            user_id=user_id,
            role="owner"
        )

        db.session.add(membership)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return organization, membership.role

def list_organizations(user_id: int):
    statement = (
        select(Organization, OrganizationMembership.role)
        .join(
            OrganizationMembership,
            OrganizationMembership.organization_id == Organization.id,
        )
        .where(OrganizationMembership.user_id == user_id)
        .order_by(Organization.id.desc())
    )

    return db.session.execute(statement).all()

def get_organization(
    user_id: int,
    organization_id: int,
) -> tuple[Organization, str]:
    statement = (
        select(Organization, OrganizationMembership.role)
        .join(
            OrganizationMembership,
            OrganizationMembership.organization_id == Organization.id,
        )
        .where(
            Organization.id == organization_id,
            OrganizationMembership.user_id == user_id,
        )
    )

    result = db.session.execute(statement).first()

    if result is None:
        raise OrganizationError(
            "Organization not found.",
            "NOT_FOUND",
            404,
        )

    return result[0], result[1]