# Snakefile — orchestrates the replication pipeline end-to-end.
#
# This replication is a fault-injection harness, not a data-analysis pipeline:
# there is no external dataset to download/clean — the harness (harness/) generates
# synthetic Zarr arrays and injects faults into Icechunk- and STAC-backed stores.
# The whole pipeline therefore lives in one notebook, 01_atomic_sync.py, which
# runs the fault matrix (via harness.run_matrix.run_all), writes the results
# table, and renders the comparison figure.
#
# Usage:
#   snakemake --cores 1                  # run everything
#   snakemake --cores 1 -n               # dry run

import sys

sys.path.insert(0, ".")
from harness.backends import minio_env_set

NOTEBOOKS = "notebooks"
DATA = "data"
FIGURES = "figures"

# The notebook only renders the full four-panel figure (main_result.png) when
# MINIO_* credentials are present — without them it deliberately writes
# main_result_local_only.png instead, so a credential-less run can never
# silently overwrite the committed NIRD/Sigma2 evidence (see
# notebooks/01_atomic_sync.py and nanopubs/drafts/05_outcome.md). The declared
# Snakemake target must match whichever file this run will actually produce.
MAIN_FIGURE = f"{FIGURES}/main_result.png" if minio_env_set() else f"{FIGURES}/main_result_local_only.png"


rule all:
    input:
        MAIN_FIGURE,
        f"{DATA}/results/results.parquet",


# ---------- 01: Atomic synchronization fault-injection matrix + figure ----------
# Runs F1-F3 (and, with MINIO_* env vars set, F1-F4) across Icechunk / STAC B0 / B1,
# writes data/results/results.parquet, and renders the comparison figure (see
# MAIN_FIGURE above for which file this run produces).
# See harness/run_matrix.py and notebooks/01_atomic_sync.py for the full design.
rule atomic_sync:
    output:
        MAIN_FIGURE,
        f"{DATA}/results/results.parquet",
    log:
        "results/logs/01_atomic_sync.log",
    shell:
        f"cd {{NOTEBOOKS}} && jupytext --to notebook --execute 01_atomic_sync.py 2>&1 | tee ../{{log}}"
