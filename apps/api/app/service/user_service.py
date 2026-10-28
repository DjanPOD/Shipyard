from collections.abc import Mapping
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.user import User

class UserAlreadyExistsError(Exception):
    """Raised when a user email already exists."""

class UserValidationError(Exception):
    """Raised when input does not meet the API's requirements"""

def list_users() -> list[User]:
    """Return users ordered from newest to oldest"""

    statement = select(User).order_by(User.created_at.desc())
    return list(db.session.scalars(statement))

def create_user(payload: Mapping[str, Any]) -> User:
    """Validate input, create a user, persist it, and return it"""

    email = _validate_email(payload.get("email"))
    display_name = _validate_display_name(payload.get("displayName"))

    user = User(
        email=email,
        display_name=display_name
    )

    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        raise UserAlreadyExistsError(
            "A user with the email already exists."
        ) from error

    return user

def _validate_email(value: object):
    """Validate and normalize an email for the current MVP."""
    if not isinstance(value, str):
        raise UserValidationError("email is required and must be a string.")

    email = value.strip().lower()

    if not email:
        raise UserValidationError("email cannot be empty.")

    if len(email) > 255:
        raise UserValidationError("email must be 255 characters or fewer.")

    if "@" not in email or email.startswith("@") or email.endswith("@"):
        raise UserValidationError("email must be valid email address.")

    return email

def _validate_display_name(value: object):
    """Validate and normalize a display name."""

    if not isinstance(value, str):
        raise UserValidationError(
            "displayName is required to be a string."
        )

    display_name = value.strip()

    if not display_name:
        raise UserValidationError("display cannot be empty")

    if len(display_name) > 100:
        raise UserValidationError("displayName must be 100 characters or fewer")

    return display_name