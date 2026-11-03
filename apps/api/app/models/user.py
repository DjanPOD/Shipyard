from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db

class User(db.Model):
    """A Shipyard user account.
    
    Password handling is intentially not included yet. Authentication is the next phase,
    where passwords will be hased and never returned by the API.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def set_password(self, password: str):
        """Validate a new password and store only its hash"""

        if not isinstance(password, str):
            raise ValueError("Password must be a string.")

        if len(password) < 15:
            raise ValueError("Password must contain at least 15 characters.")

        if len(password) > 128:
            raise ValueError("Password must contain at most than 128 characters.")

        self.password_hash = generate_password_hash(
            password,
            method="scrypt",
        )

    def check_password(self, password: str) -> bool:
        """Check a supplied password against the user's stored hash."""

        if not isinstance(password, str) or not self.password_hash:
            return False

        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict[str,object]:
        """Return a JSON-safe representation suitable for API responses"""

        return {
            "id": self.id,
            "email": self.email,
            "display_name": self.display_name,
            "created_at": self.created_at.isoformat()
            if self.created_at
            else None,
            "updated": self.updated_at.isoformat()
            if self.updated_at
            else None
        }

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"