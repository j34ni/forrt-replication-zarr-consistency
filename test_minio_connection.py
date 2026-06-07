"""Standalone MinIO connection test — run with: pixi run python test_minio_connection.py

Requires MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY (and optionally
MINIO_BUCKET, defaulting to jeani-ns1000k-grid4earth) in the environment.
"""
import os

import icechunk
import numpy as np
import zarr

storage = icechunk.s3_storage(
    bucket=os.environ.get("MINIO_BUCKET", "jeani-ns1000k-grid4earth"),
    prefix="icechunk-atomicity-test/_connection-test",
    endpoint_url=os.environ["MINIO_ENDPOINT"],
    allow_http=False,
    access_key_id=os.environ["MINIO_ACCESS_KEY"],
    secret_access_key=os.environ["MINIO_SECRET_KEY"],
    force_path_style=True,
)

repo = icechunk.Repository.create(storage)
session = repo.writable_session("main")
root = zarr.open_group(store=session.store, mode="w")
root.create_array("data", shape=(4,), dtype="float32")[:] = np.array([1, 2, 3, 4], dtype="float32")
session.commit("connection test")
print("SUCCESS")

s2 = repo.readonly_session("main")
print("Read back:", zarr.open_group(store=s2.store, mode="r")["data"][:])
