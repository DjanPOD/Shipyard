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

class InvalidCredentialsError(Exception):
    """The supplied credentials cannot authenticate a user."""

def register_user(payload: Mapping[str, Any]) -> User:
    email = _validate_email(payload.get("email"))
    display_name = _validate_display_name(payload.get("display_name"))

    user = User(
        email=email,
        display_name=display_name,
    )

    try:
        user.set_password(payload.get("password"))
    except ValueError as error:
        raise UserValidationError(str(error)) from error

    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()

         # Only classify the error as an email conflict if that email exists.
        existing_user = db.session.scalar(
            select(User).where(User.email == email)
        )

        if existing_user is not None:
            raise UserAlreadyExistsError(
                "An account with that email already exists"
            ) from error

        # Unexpected database failures must not be disguised as duplicates.
        raise 

    return user

def authenticate_user(payload: Mapping[str: Any]) -> User:
    email = payload.get("email")
    password = payload.get("password")

    if not isinstance(email, str) or not isinstance(password, str):
        raise InvalidCredentialsError("Invalid email or password.")

    email = email.strip().lower()

    user = db.session.scalar(
        select(User).where(User.email == email)
    )

    if user is None or not user.check_password(password):
        raise InvalidCredentialsError("Invalid email or password.")

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

    # Basic MVP validation; this does not verify ownership or deliverability.
    if email.count("@") != 1 or any (char.isspace() for char in email):
        raise UserValidationError("email must be valid email address.")

    local_part, domain = email.split("@")

    if not local_part or not domain:
        raise UserValidationError("email must be a valid email address.")
    
    return email

def _validate_display_name(value: object):
    """Validate and normalize a display name."""

    if not isinstance(value, str):
        raise UserValidationError(
            "displayName is required to be a string."
        )

    display_name = value.strip()

    if not display_name:
        raise UserValidationError("display_name cannot be empty")

    if len(display_name) > 100:
        raise UserValidationError("display_name must be 100 characters or fewer")

    return display_name