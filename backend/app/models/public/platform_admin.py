"""`public.platform_admins` — Super Administrator accounts, the only role
that spans institutions (DATABASE_PLAN.md §0)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import PublicBase, UUIDPKMixin


class PlatformAdmin(UUIDPKMixin, PublicBase):
    __tablename__ = "platform_admins"
    __table_args__ = {"schema": "public"}

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mfa_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PlatformAdmin {self.email!r}>"
