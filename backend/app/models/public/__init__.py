"""Models living in the `public` schema (cross-tenant control plane)."""

from app.models.public.institution import Institution
from app.models.public.platform_admin import PlatformAdmin

__all__ = ["Institution", "PlatformAdmin"]
