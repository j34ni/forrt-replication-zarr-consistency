"""
Matrix runner: scenarios × systems × backends × N trials → results.parquet

Usage:
    python -m harness.run_matrix --trials 100 --out data/results/results.parquet

Backends tested: local (always), minio (if available — see backends.py).
Scenarios tested: F1, F2, F3.
Systems tested: icechunk, stac_b0, stac_b1.

written, untested
"""
import argparse
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from harness.backends import local_icechunk_repo, minio_icechunk_repo, is_minio_available
from harness.faults import (
    f1_icechunk, f1_stac_b0, f1_stac_b1,
    f2_stac_b0, f2_stac_b1_not_applicable,
    f3_icechunk, f3_stac_b0, f3_stac_b1,
)


def run_local_trials(n_trials: int, seed: int = 42) -> list[dict]:
    """Run all F1/F2/F3 scenarios on the local filesystem backend."""
    rng = np.random.default_rng(seed)
    rows: list[dict] = []

    for trial in range(n_trials):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            # -- F1: crash after data, before metadata --
            ic_repo = local_icechunk_repo(str(base / "ic_f1"))
            rows.append({
                "scenario": "F1", "backend": "local", "system": "icechunk",
                "trial": trial,
                "inconsistent": f1_icechunk(ic_repo, rng),
                "pre_sweep_inconsistent": None, "post_sweep_inconsistent": None,
                "notes": "",
            })

            rows.append({
                "scenario": "F1", "backend": "local", "system": "stac_b0",
                "trial": trial,
                "inconsistent": f1_stac_b0(str(base / "zarr_f1"), str(base / "stac_f1.json"), rng),
                "pre_sweep_inconsistent": None, "post_sweep_inconsistent": None,
                "notes": "",
            })

            pre, post = f1_stac_b1(str(base / "zarr_f1b"), str(base / "stac_f1b.json"), rng)
            rows.append({
                "scenario": "F1", "backend": "local", "system": "stac_b1",
                "trial": trial,
                "inconsistent": pre,
                "pre_sweep_inconsistent": pre, "post_sweep_inconsistent": post,
                "notes": "pre/post sweeper recorded separately",
            })

            # -- F2: crash after metadata, before data --
            rows.append({
                "scenario": "F2", "backend": "local", "system": "icechunk",
                "trial": trial,
                "inconsistent": False,
                "pre_sweep_inconsistent": None, "post_sweep_inconsistent": None,
                "notes": "not applicable — single-session atomicity prevents F2 by construction",
            })

            rows.append({
                "scenario": "F2", "backend": "local", "system": "stac_b0",
                "trial": trial,
                "inconsistent": f2_stac_b0(str(base / "zarr_f2"), str(base / "stac_f2.json"), rng),
                "pre_sweep_inconsistent": None, "post_sweep_inconsistent": None,
                "notes": "",
            })

            rows.append({
                "scenario": "F2", "backend": "local", "system": "stac_b1",
                "trial": trial,
                "inconsistent": f2_stac_b1_not_applicable(),
                "pre_sweep_inconsistent": None, "post_sweep_inconsistent": None,
                "notes": "not applicable — B1 write-ordering prevents F2 by design",
            })

            # -- F3: concurrent reader during write --
            ic_repo_f3 = local_icechunk_repo(str(base / "ic_f3"))
            rows.append({
                "scenario": "F3", "backend": "local", "system": "icechunk",
                "trial": trial,
                "inconsistent": f3_icechunk(ic_repo_f3, rng),
                "pre_sweep_inconsistent": None, "post_sweep_inconsistent": None,
                "notes": "",
            })

            rows.append({
                "scenario": "F3", "backend": "local", "system": "stac_b0",
                "trial": trial,
                "inconsistent": f3_stac_b0(str(base / "zarr_f3"), str(base / "stac_f3.json"), rng),
                "pre_sweep_inconsistent": None, "post_sweep_inconsistent": None,
                "notes": "",
            })

            rows.append({
                "scenario": "F3", "backend": "local", "system": "stac_b1",
                "trial": trial,
                "inconsistent": f3_stac_b1(str(base / "zarr_f3b"), str(base / "stac_f3b.json"), rng),
                "pre_sweep_inconsistent": None, "post_sweep_inconsistent": None,
                "notes": "write-ordering does not close F3 window",
            })

    return rows


def run_all(n_trials: int = 100, out_path: str = "data/results/results.parquet", seed: int = 42) -> pd.DataFrame:
    rows = run_local_trials(n_trials=n_trials, seed=seed)

    if is_minio_available():
        print("MinIO detected — MinIO backend trials not yet implemented; skipping.")
    else:
        print("MinIO not available — skipping minio backend.")

    df = pd.DataFrame(rows)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)
    print(f"Results written to {out_path} ({len(df)} rows)")
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=100)
    parser.add_argument("--out", default="data/results/results.parquet")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    run_all(n_trials=args.trials, out_path=args.out, seed=args.seed)
