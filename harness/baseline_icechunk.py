"""
Icechunk baseline operations.

All data + metadata writes happen inside a single session. The session is either
committed (atomic, fully visible) or abandoned (nothing visible). There is no partial
state reachable by a reader using a separate readonly_session.

written, untested
"""
import numpy as np
import zarr
import icechunk

from harness.invariant import compute_sha256


def icechunk_initial_write(repo: icechunk.Repository, data: np.ndarray) -> str:
    """Write initial data + sha256 attr to a fresh repo. Returns snapshot id."""
    session = repo.writable_session("main")
    store = session.store
    root = zarr.open_group(store=store, mode="w")
    arr = root.create_array("data", shape=data.shape, dtype=data.dtype)
    arr[:] = data
    root.attrs.update({"data_sha256": compute_sha256(data)})
    return session.commit("initial write")


def icechunk_update_committed(repo: icechunk.Repository, new_data: np.ndarray) -> str:
    """Normal update: write new data + updated sha256 attr, commit. Returns snapshot id."""
    session = repo.writable_session("main")
    store = session.store
    root = zarr.open_group(store=store, mode="a")
    root["data"][:] = new_data
    root.attrs.update({"data_sha256": compute_sha256(new_data)})
    return session.commit("update data")


def icechunk_update_abandoned(repo: icechunk.Repository, new_data: np.ndarray) -> None:
    """
    Simulate a crash: open session, write data + attr, then abandon without committing.
    The session object goes out of scope; no commit is issued.
    This is the Icechunk equivalent of a process crash mid-write.
    """
    session = repo.writable_session("main")
    store = session.store
    root = zarr.open_group(store=store, mode="a")
    root["data"][:] = new_data
    root.attrs.update({"data_sha256": compute_sha256(new_data)})
    # deliberately NOT calling session.commit() — session is abandoned here


def icechunk_read_during_write(
    repo: icechunk.Repository,
    new_data: np.ndarray,
) -> tuple[bool, bool]:
    """
    Simulate F3: open a writable session, write (without committing), then check
    what a concurrent readonly_session sees. Returns (mid_write_consistent, post_commit_consistent).
    """
    session = repo.writable_session("main")
    store = session.store
    root = zarr.open_group(store=store, mode="a")
    root["data"][:] = new_data
    root.attrs.update({"data_sha256": compute_sha256(new_data)})

    # A concurrent reader opens a fresh readonly session — reads last committed snapshot.
    from harness.invariant import check_icechunk
    mid_write_consistent, _, _ = check_icechunk(repo)

    session.commit("update data")

    post_commit_consistent, _, _ = check_icechunk(repo)
    return mid_write_consistent, post_commit_consistent
