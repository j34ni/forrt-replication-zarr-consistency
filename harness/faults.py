"""
Fault scenario runners: F1, F2, F3 for each system.

Each function runs one trial and returns whether an inconsistency was observed.
The caller (run_matrix.py) calls these N times per scenario × system × backend.

Scenarios:
  F1 — crash after data write, before metadata update.
  F2 — crash after metadata update, before data write (STAC only; Icechunk not applicable).
  F3 — concurrent reader observes store mid-write.

written, untested
"""
import tempfile
from pathlib import Path

import numpy as np

from harness.invariant import check_icechunk, check_stac
from harness.baseline_stac import (
    stac_initial_write,
    stac_b0_update,
    stac_b0_update_reverse_order,
    stac_b0_mid_write_check,
    stac_b1_update,
    stac_b1_sweeper,
    stac_b1_mid_write_check,
    SimulatedCrash,
)
from harness.baseline_icechunk import (
    icechunk_initial_write,
    icechunk_update_abandoned,
    icechunk_read_during_write,
)


def _random_data(rng: np.random.Generator) -> np.ndarray:
    return rng.standard_normal(256).astype("float32")


# ---------------------------------------------------------------------------
# F1 — crash after data, before metadata
# ---------------------------------------------------------------------------

def f1_icechunk(repo, rng: np.random.Generator) -> bool:
    """Icechunk F1: abandon session before commit. Expect: no inconsistency."""
    data_v1 = _random_data(rng)
    icechunk_initial_write(repo, data_v1)

    data_v2 = _random_data(rng)
    icechunk_update_abandoned(repo, data_v2)

    consistent, _, _ = check_icechunk(repo)
    return not consistent  # True = inconsistency observed (expected: False)


def f1_stac_b0(zarr_path: str, stac_path: str, rng: np.random.Generator) -> bool:
    """STAC B0 F1: write zarr, crash before STAC update. Expect: inconsistency."""
    data_v1 = _random_data(rng)
    stac_initial_write(zarr_path, stac_path, data_v1)

    data_v2 = _random_data(rng)
    try:
        stac_b0_update(zarr_path, stac_path, data_v2, fault_point="after_data")
    except SimulatedCrash:
        pass

    consistent, _, _ = check_stac(zarr_path, stac_path)
    return not consistent  # True = inconsistency observed (expected: True)


def f1_stac_b1(zarr_path: str, stac_path: str, rng: np.random.Generator) -> tuple[bool, bool]:
    """
    STAC B1 F1: write zarr, crash before STAC update, then run sweeper.
    Returns (pre_sweep_inconsistent, post_sweep_inconsistent).
    Expected: (True, False) — inconsistency exists until sweeper runs.
    """
    data_v1 = _random_data(rng)
    stac_initial_write(zarr_path, stac_path, data_v1)

    data_v2 = _random_data(rng)
    try:
        stac_b1_update(zarr_path, stac_path, data_v2, fault_point="after_data")
    except SimulatedCrash:
        pass

    consistent_pre, _, _ = check_stac(zarr_path, stac_path)
    stac_b1_sweeper(zarr_path, stac_path)
    consistent_post, _, _ = check_stac(zarr_path, stac_path)
    return not consistent_pre, not consistent_post


# ---------------------------------------------------------------------------
# F2 — crash after metadata update, before data write
# (Icechunk: not applicable — single-session atomicity prevents F2 by construction)
# ---------------------------------------------------------------------------

def f2_stac_b0(zarr_path: str, stac_path: str, rng: np.random.Generator) -> bool:
    """STAC B0 F2: write STAC, crash before zarr write. Expect: inconsistency."""
    data_v1 = _random_data(rng)
    stac_initial_write(zarr_path, stac_path, data_v1)

    data_v2 = _random_data(rng)
    try:
        stac_b0_update_reverse_order(zarr_path, stac_path, data_v2, fault_point="after_data")
    except SimulatedCrash:
        pass

    consistent, _, _ = check_stac(zarr_path, stac_path)
    return not consistent  # True = inconsistency observed (expected: True)


def f2_stac_b1_not_applicable() -> bool:
    """
    B1 enforces data-before-STAC write ordering, so F2 cannot occur in B1.
    The B1 sweeper also runs data-before-STAC. Returns False (no inconsistency by design).
    """
    return False


# ---------------------------------------------------------------------------
# F3 — concurrent reader during write
# ---------------------------------------------------------------------------

def f3_icechunk(repo, rng: np.random.Generator) -> bool:
    """
    Icechunk F3: reader uses a fresh readonly_session during an in-progress write.
    The readonly_session reads the last committed snapshot — never mid-write state.
    Expect: no inconsistency observed mid-write.
    """
    data_v1 = _random_data(rng)
    icechunk_initial_write(repo, data_v1)

    data_v2 = _random_data(rng)
    mid_consistent, post_consistent = icechunk_read_during_write(repo, data_v2)

    # inconsistency = mid-write reader saw a mixed state
    return not mid_consistent  # expected: False


def f3_stac_b0(zarr_path: str, stac_path: str, rng: np.random.Generator) -> bool:
    """STAC B0 F3: reader sees zarr with new data but STAC with old sha256. Expect: inconsistency."""
    data_v1 = _random_data(rng)
    stac_initial_write(zarr_path, stac_path, data_v1)

    data_v2 = _random_data(rng)
    inconsistency_observed = stac_b0_mid_write_check(zarr_path, stac_path, data_v2)
    return inconsistency_observed  # expected: True


def f3_stac_b1(zarr_path: str, stac_path: str, rng: np.random.Generator) -> bool:
    """
    STAC B1 F3: same inconsistency window as B0 — write-ordering doesn't close F3.
    The sweeper helps for F1 but runs asynchronously; it does not protect the F3 window.
    """
    data_v1 = _random_data(rng)
    stac_initial_write(zarr_path, stac_path, data_v1)

    data_v2 = _random_data(rng)
    inconsistency_observed = stac_b1_mid_write_check(zarr_path, stac_path, data_v2)
    return inconsistency_observed  # expected: True
