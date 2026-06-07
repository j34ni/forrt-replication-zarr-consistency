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


def stac_is_ahead_of_data(zarr_path: str, stac_path: str, candidate_sha256: str) -> bool:
    """
    F2-state detector: returns True if STAC references a sha256 that the zarr array
    does not currently contain — i.e. STAC is ahead of the data.

    This is distinct from the generic sha256 mismatch (check_stac): it specifically
    tests whether STAC points at data that was *intended* to be written but wasn't
    committed yet (the F2 failure mode for a metadata-before-data write ordering).

    candidate_sha256 is the sha256 of the update that was attempted. If STAC stores
    that value but zarr still holds the old data, STAC is ahead (F2 state).

    For a correctly-ordered B1 implementation (data-before-STAC), this must always
    return False — but making it a measured check means a future write-order regression
    in B1 would flip it to True.
    """
    root = zarr.open_group(zarr_path, mode="r")
    actual: str = compute_sha256(root["data"][:])
    with open(stac_path) as fh:
        stored: str | None = json.load(fh).get("properties", {}).get("data_sha256")
    return stored == candidate_sha256 and actual != candidate_sha256
