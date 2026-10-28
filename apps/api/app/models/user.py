from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

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
        index=True
    )

    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

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