"""`public.institutions` — the tenant registry (DATABASE_PLAN.md §0)."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import PublicBase, TimestampMixin, UUIDPKMixin


class Institution(UUIDPKMixin, TimestampMixin, PublicBase):
    __tablename__ = "institutions"
    __table_args__ = {"schema": "public"}

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    schema_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="trial")
    subscription_plan: Mapped[str | None] = mapped_column(String(50), nullable=True)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="UTC")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Institution {self.slug!r}>"
