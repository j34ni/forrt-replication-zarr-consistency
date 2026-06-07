"""
Store factory: returns (icechunk.Repository, zarr_path, stac_path) tuples for each backend.

Supported backends: local, minio.
MinIO requires a running MinIO server; configure via environment variables:
  MINIO_ENDPOINT   default: http://localhost:9000
  MINIO_BUCKET     default: icechunk-test
  MINIO_ACCESS_KEY default: minioadmin
  MINIO_SECRET_KEY default: minioadmin

written, untested
"""
import os
from pathlib import Path

import icechunk


def local_icechunk_repo(store_dir: str) -> "icechunk.Repository":
    """Create or open a local-filesystem-backed Icechunk repository."""
    path = str(store_dir)
    storage = icechunk.local_filesystem_storage(path)
    try:
        return icechunk.Repository.open(storage)
    except Exception:
        return icechunk.Repository.create(storage)


def minio_icechunk_repo(bucket: str, prefix: str) -> "icechunk.Repository":
    """Create or open a MinIO-backed Icechunk repository.

    MinIO supports conditional writes (ETag-based), so Icechunk's atomicity guarantee
    holds — but this must be verified per MinIO version. Document the MinIO version
    used in the Outcome nanopub.
    """
    endpoint = os.environ.get("MINIO_ENDPOINT", "http://localhost:9000")
    access_key = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
    secret_key = os.environ.get("MINIO_SECRET_KEY", "minioadmin")

    storage = icechunk.s3_storage(
        bucket=bucket,
        prefix=prefix,
        endpoint_url=endpoint,
        allow_http=True,
        access_key_id=access_key,
        secret_access_key=secret_key,
        force_path_style=True,  # required for MinIO path-style addressing
    )
    try:
        return icechunk.Repository.open(storage)
    except Exception:
        return icechunk.Repository.create(storage)


def is_minio_available() -> bool:
    """Probe MinIO endpoint; return False (skip backend) if unreachable."""
    import urllib.request
    endpoint = os.environ.get("MINIO_ENDPOINT", "http://localhost:9000")
    try:
        urllib.request.urlopen(f"{endpoint}/minio/health/live", timeout=2)
        return True
    except Exception:
        return False
