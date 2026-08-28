"""Application settings, loaded from environment variables / .env.

Uses pydantic-settings so every configuration value is validated at process
startup rather than failing deep inside a request handler.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    environment: str = Field(default="development")
    debug: bool = Field(default=True)
    project_name: str = "OBEvolve"
    # Product version — bump alongside frontend/package.json's "version" and
    # frontend/src/lib/version.ts's APP_VERSION (no shared build step wires
    # the three together automatically). Exposed via GET /health and the
    # OpenAPI spec (see app/main.py).
    app_version: str = "1.0.1"
    api_v1_prefix: str = "/api/v1"

    # --- Database ---
    database_url: str = Field(
        default="postgresql+psycopg://obevolve:change-me@localhost:5432/obevolve"
    )

    # --- Redis / Celery ---
    redis_url: str = Field(default="redis://localhost:6379/0")

    # --- Auth / JWT ---
    jwt_secret_key: str = Field(default="change-me-to-a-long-random-string")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)

    # --- Google Sign-In ---
    # OAuth 2.0 Client ID from https://console.cloud.google.com/apis/credentials
    # (type "Web application"). Required both here (to verify the ID token's
    # `aud` claim, app/api/v1/endpoints/auth.py's /auth/google) and on the
    # frontend (frontend/.env's VITE_GOOGLE_CLIENT_ID, to request the token in
    # the first place) — same value in both places. Google Sign-In is an
    # additional login path, not a replacement: any existing user account
    # whose email Google reports as verified can use it, but password login
    # keeps working for everyone regardless.
    google_client_id: str | None = Field(default=None)

    # --- CORS ---
    backend_cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    # --- Frontend ---
    # Origin the SPA is served from — used only to build absolute links back
    # to the frontend (e.g. the password-reset link mailed to a user). Not
    # to be confused with backend_cors_origins above.
    frontend_origin: str = Field(default="http://localhost:5173")

    # --- Tenancy ---
    dev_tenant_header: str = Field(default="X-Institution-Slug")
    tenant_schema_prefix: str = Field(default="tenant_")

    # --- Object storage ---
    # If s3_endpoint_url/s3_access_key/s3_secret_key are unset (the default —
    # nothing requires S3 credentials to run this app locally), uploads fall
    # back to local disk under `local_upload_dir`. See app/services/storage.py.
    s3_endpoint_url: str | None = None
    s3_access_key: str | None = None
    s3_secret_key: str | None = None
    s3_bucket_name: str = Field(default="obevolve-evidence")
    local_upload_dir: str = Field(default="uploads")
    max_upload_size_mb: int = Field(default=20)


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — avoids re-parsing the environment per call."""
    return Settings()


settings = get_settings()
