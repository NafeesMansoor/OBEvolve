"""File storage for assessment document uploads (question paper / moderation
form / compliance form) and any future evidence uploads. Uses S3 (or an
S3-compatible endpoint) when `settings.s3_endpoint_url`/`s3_access_key`/
`s3_secret_key` are configured; otherwise falls back to local disk under
`settings.local_upload_dir` (relative to the backend package root), so the
feature works out of the box with zero cloud credentials in development.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

_BACKEND_ROOT = Path(__file__).resolve().parents[2]

# Kept intentionally narrow — these are institutional exam-office documents
# (question papers, moderation/compliance forms), not general-purpose uploads.
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/png",
    "image/jpeg",
}


def _local_upload_root() -> Path:
    root = Path(settings.local_upload_dir)
    if not root.is_absolute():
        root = _BACKEND_ROOT / root
    root.mkdir(parents=True, exist_ok=True)
    return root


def _s3_configured() -> bool:
    return bool(settings.s3_endpoint_url and settings.s3_access_key and settings.s3_secret_key)


def _s3_client():
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
    )


def save_upload(file: UploadFile, *, key_prefix: str) -> tuple[str, int]:
    """Validate and persist an uploaded file; return `(storage_key, size_bytes)`."""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}. Allowed: PDF, Word, PNG, JPEG.",
        )

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    contents = file.file.read()
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {settings.max_upload_size_mb}MB limit.",
        )

    extension = Path(file.filename or "").suffix
    key = f"{key_prefix}/{uuid.uuid4()}{extension}"

    if _s3_configured():
        _s3_client().put_object(
            Bucket=settings.s3_bucket_name,
            Key=key,
            Body=contents,
            ContentType=file.content_type,
        )
    else:
        path = _local_upload_root() / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)

    return key, len(contents)


def read_upload(key: str) -> bytes:
    """Read back a previously-saved file's raw bytes."""
    if _s3_configured():
        obj = _s3_client().get_object(Bucket=settings.s3_bucket_name, Key=key)
        return obj["Body"].read()
    path = _local_upload_root() / key
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found in storage."
        )
    return path.read_bytes()


def delete_upload(key: str) -> None:
    """Best-effort delete — called when a document slot is re-uploaded."""
    if _s3_configured():
        _s3_client().delete_object(Bucket=settings.s3_bucket_name, Key=key)
        return
    path = _local_upload_root() / key
    path.unlink(missing_ok=True)
