"""
Consistency invariant: attrs['data_sha256'] must equal sha256(array['data']).

The invariant is a deterministic function of the data, so any metadata–data
disagreement is mechanically detectable without prior knowledge of the correct value.

written, untested
"""
import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import zarr

if TYPE_CHECKING:
    import icechunk


def compute_sha256(arr: np.ndarray) -> str:
    """SHA-256 of array bytes in C-contiguous order."""
    return hashlib.sha256(np.ascontiguousarray(arr).tobytes()).hexdigest()


def check_icechunk(repo: "icechunk.Repository", branch: str = "main") -> tuple[bool, str | None, str]:
    """
    Open a fresh readonly session and compare stored sha256 with recomputed value.
    Returns (consistent, stored_sha256, actual_sha256).
    A separate readonly_session is used so we always read the latest *committed* snapshot,
    never in-progress writer state.
    """
    session = repo.readonly_session(branch)
    store = session.store
    root = zarr.open_group(store=store, mode="r")
    stored: str | None = root.attrs.get("data_sha256", None)
    actual: str = compute_sha256(root["data"][:])
    return stored == actual, stored, actual


def check_stac(zarr_path: str, stac_path: str) -> tuple[bool, str | None, str]:
    """
    Read zarr array from plain local store, read STAC JSON, compare sha256 values.
    Returns (consistent, stored_sha256, actual_sha256).
    """
    root = zarr.open_group(zarr_path, mode="r")
    actual: str = compute_sha256(root["data"][:])
    with open(stac_path) as fh:
        stac = json.load(fh)
    stored: str | None = stac.get("properties", {}).get("data_sha256", None)
    return stored == actual, stored, actual
