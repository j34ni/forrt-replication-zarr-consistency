"""
STAC baseline: disconnected metadata index over plain Zarr object storage.

B0 (naive): write zarr array to disk, then write STAC JSON. No transaction.
            Any interruption between the two writes leaves an inconsistent state.
B1 (best-effort): write-ordering discipline (data always before STAC) + a
            reconciliation sweeper that detects and fixes stale STAC entries.
            Eliminates F2-type inconsistencies; reduces but does not eliminate F1/F3.

The STAC "index" here is a minimal JSON file (properties.data_sha256 field).
A real deployment would use pgstac or a STAC API, but the consistency behaviour
is identical — the write is still separate from the zarr write.

written, untested
"""
import json
from pathlib import Path
from typing import Literal

import numpy as np
import zarr

from harness.invariant import compute_sha256


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_zarr(zarr_path: str, data: np.ndarray) -> None:
    root = zarr.open_group(zarr_path, mode="a")
    root["data"][:] = data


def _write_stac(stac_path: str, sha256: str) -> None:
    stac = {"type": "Feature", "id": "test-item", "properties": {"data_sha256": sha256}}
    Path(stac_path).write_text(json.dumps(stac))


def _init_zarr(zarr_path: str, data: np.ndarray) -> None:
    root = zarr.open_group(zarr_path, mode="w")
    arr = root.create_array("data", shape=data.shape, dtype=data.dtype)
    arr[:] = data


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def stac_initial_write(zarr_path: str, stac_path: str, data: np.ndarray) -> None:
    """Write initial consistent state: zarr array + matching STAC JSON."""
    _init_zarr(zarr_path, data)
    _write_stac(stac_path, compute_sha256(data))


# ---------------------------------------------------------------------------
# B0 — naive (no transaction, no reconciliation)
# ---------------------------------------------------------------------------

class SimulatedCrash(Exception):
    pass


FaultPoint = Literal["after_data", "after_stac", None]


def stac_b0_update(
    zarr_path: str,
    stac_path: str,
    new_data: np.ndarray,
    fault_point: FaultPoint = None,
) -> None:
    """
    B0 naive update: write zarr → write STAC. fault_point controls where a crash is injected.
    'after_data'  → data written, STAC not updated → stale STAC (F1-type inconsistency).
    'after_stac'  → STAC updated but data not yet written → forward-pointing STAC (F2 reverse order).
    None          → clean write, both updated.
    """
    _write_zarr(zarr_path, new_data)
    if fault_point == "after_data":
        raise SimulatedCrash("F1: crash after zarr write, before STAC update")
    _write_stac(stac_path, compute_sha256(new_data))
    if fault_point == "after_stac":
        raise SimulatedCrash("unexpected: fault after both writes (no-op for consistency)")


def stac_b0_update_reverse_order(
    zarr_path: str,
    stac_path: str,
    new_data: np.ndarray,
    fault_point: FaultPoint = None,
) -> None:
    """
    B0 reverse-order: write STAC → write zarr. Used for F2 scenario.
    'after_data'  → STAC updated, zarr not yet written → STAC ahead of data.
    """
    _write_stac(stac_path, compute_sha256(new_data))
    if fault_point == "after_data":
        raise SimulatedCrash("F2: crash after STAC write, before zarr write")
    _write_zarr(zarr_path, new_data)


def stac_b0_mid_write_check(
    zarr_path: str,
    stac_path: str,
    new_data: np.ndarray,
) -> bool:
    """
    F3 simulation: write zarr, CHECK invariant (simulating a concurrent reader between
    the two writes), then write STAC. Returns True if inconsistency was observed mid-write.
    """
    _write_zarr(zarr_path, new_data)
    # Simulate concurrent reader arriving between the two writes:
    from harness.invariant import check_stac
    consistent_mid, _, _ = check_stac(zarr_path, stac_path)
    _write_stac(stac_path, compute_sha256(new_data))
    return not consistent_mid  # True = inconsistency was observed


# ---------------------------------------------------------------------------
# B1 — best-effort (write-ordering + reconciliation sweeper)
# ---------------------------------------------------------------------------

def stac_b1_update(
    zarr_path: str,
    stac_path: str,
    new_data: np.ndarray,
    fault_point: FaultPoint = None,
) -> None:
    """
    B1 update: always data-before-STAC (eliminates F2). fault_point='after_data' → F1 scenario.
    B1 does NOT prevent the F1 inconsistency window; the sweeper closes it eventually.
    """
    _write_zarr(zarr_path, new_data)
    if fault_point == "after_data":
        raise SimulatedCrash("F1 (B1): crash after zarr write, before STAC update")
    _write_stac(stac_path, compute_sha256(new_data))


def stac_b1_sweeper(zarr_path: str, stac_path: str) -> bool:
    """
    Reconciliation sweeper: recompute sha256 from zarr, update STAC if mismatch.
    Returns True if a mismatch was found and corrected (i.e. inconsistency was present).
    """
    from harness.invariant import check_stac, compute_sha256
    consistent, stored, actual = check_stac(zarr_path, stac_path)
    if not consistent:
        _write_stac(stac_path, actual)
        return True
    return False


def stac_b1_mid_write_check(
    zarr_path: str,
    stac_path: str,
    new_data: np.ndarray,
) -> bool:
    """F3 simulation for B1: same window exists — data written before STAC, reader sees gap."""
    return stac_b0_mid_write_check(zarr_path, stac_path, new_data)
