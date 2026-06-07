# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.0
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # 01 — Atomic synchronization: fault-injection consistency test
#
# **Claim under test:** Icechunk-backed transactional stores produce zero observable
# metadata–data inconsistencies under writer failure and concurrent access, whereas
# disconnected STAC metadata indexes over object storage produce such inconsistencies
# without external orchestration.
#
# **Method:** A fault-injection harness generates synthetic Zarr arrays carrying a
# SHA-256 checksum attribute. A consistency checker recomputes the checksum from data
# and compares. Faults are injected at specific points in the write sequence across
# three scenarios (F1, F2, F3) for three systems (Icechunk, STAC B0, STAC B1).
#
# **Status:** written, untested — results cells will be populated on first run.

# %% [markdown]
# ## 0. Environment check

# %%
import sys
print(f"Python {sys.version}")

import zarr
print(f"zarr {zarr.__version__}")

import icechunk
print(f"icechunk {icechunk.__version__}")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# %% [markdown]
# ## 1. Run the fault-injection matrix
#
# Runs F1, F2, F3 across Icechunk / STAC-B0 / STAC-B1 on the local filesystem backend.
# Each scenario runs `N_TRIALS` independent trials with fresh stores.
#
# Runtime estimate: ~5 min for N_TRIALS=1000 on a modern laptop (~30 s per 100 trials).
# N_TRIALS=1000 matches the trial count cited throughout the Outcome nanopub
# (`nanopubs/drafts/05_outcome.md`) and the figure below — keep them in sync.

# %%
import sys
sys.path.insert(0, str(Path("..").resolve()))

from harness.run_matrix import run_all

RESULTS_PATH = "../data/results/results.parquet"
N_TRIALS = 1000

df = run_all(n_trials=N_TRIALS, out_path=RESULTS_PATH, seed=42)
df.head(12)

# %% [markdown]
# ## 2. Headline counts: inconsistencies per scenario × system
#
# `results.parquet` may also contain object-store (MinIO/NIRD) trials from a
# `--minio-trials` run (see `harness/run_matrix.py`). This figure is scoped to the
# *local filesystem* backend specifically — filter to it explicitly so a mixed-backend
# results file doesn't silently inflate the Icechunk trial count (e.g. 1000 local +
# 100 MinIO → 1100, corrupting the "N=1000" framing below).

# %%
df_local = df[df["backend"] == "local"]

summary = (
    df_local.groupby(["scenario", "system"])["inconsistent"]
    .agg(["sum", "count"])
    .rename(columns={"sum": "inconsistent_count", "count": "trials"})
    .reset_index()
)
summary["inconsistency_rate"] = summary["inconsistent_count"] / summary["trials"]
print(summary.to_string(index=False))

# %% [markdown]
# ## 3. Figure: inconsistency count per scenario × system
#
# Design:
# - **F1 B1**: labelled with pre-sweep (1000) + annotation showing post-sweep (→0).
#   Bar height = window that exists; annotation shows it is recoverable.
# - **F2 B1**: cross-hatched — this is a measured F2-state check (is STAC ever ahead
#   of data?), not a fault injection. Zero is real but means "write-ordering holds".
# - **Y-axis**: worst-case trial count (deterministic injection), not a probability.

# %%
SYSTEM_ORDER = ["icechunk", "stac_b0", "stac_b1"]
SCENARIO_ORDER = ["F1", "F2", "F3"]
COLORS = {"icechunk": "#2196F3", "stac_b0": "#F44336", "stac_b1": "#FF9800"}
LABELS = {"icechunk": "Icechunk", "stac_b0": "STAC B0\n(naive)", "stac_b1": "STAC B1\n(best-effort)"}

N = N_TRIALS
f1_b1_post = int(df_local[(df_local["scenario"] == "F1") & (df_local["system"] == "stac_b1")]["post_sweep_inconsistent"].sum())

fig, axes = plt.subplots(1, 3, figsize=(12, 4.5), sharey=True)

for ax, scenario in zip(axes, SCENARIO_ORDER):
    sub = summary[summary["scenario"] == scenario].set_index("system").reindex(SYSTEM_ORDER)
    counts = sub["inconsistent_count"].fillna(0)

    for i, (sys, count) in enumerate(zip(SYSTEM_ORDER, counts)):
        hatch = "///" if (scenario == "F2" and sys == "stac_b1") else None
        ax.bar(LABELS[sys], count, color=COLORS[sys], edgecolor="white",
               linewidth=0.5, hatch=hatch)

        label_y = count + N * 0.02
        if scenario == "F1" and sys == "stac_b1":
            ax.text(i, label_y, f"{int(count)}", ha="center", va="bottom",
                    fontsize=10, fontweight="bold", color="#CC6600")
            ax.annotate(
                f"→ {f1_b1_post} post-sweep",
                xy=(i, count * 0.5), xytext=(i, count + N * 0.22),
                ha="center", fontsize=7.5, color="#555",
                arrowprops=dict(arrowstyle="-|>", color="#888", lw=0.8),
            )
        elif scenario == "F2" and sys == "stac_b1":
            ax.text(i, label_y, f"{int(count)}", ha="center", va="bottom",
                    fontsize=10, fontweight="bold")
            ax.text(i, label_y + N * 0.08, "write-order\nholds", ha="center",
                    fontsize=7, color="#777", style="italic")
        else:
            ax.text(i, label_y, f"{int(count)}", ha="center", va="bottom",
                    fontsize=10, fontweight="bold")

    ax.set_title(f"Scenario {scenario}", fontsize=11, fontweight="bold")
    ax.set_ylabel(f"Worst-case trial count\n(deterministic, N={N})" if ax is axes[0] else "")
    ax.set_ylim(0, N * 1.5)
    ax.set_xticks(range(len(SYSTEM_ORDER)))
    ax.set_xticklabels([LABELS[s] for s in SYSTEM_ORDER], fontsize=9)
    ax.axhline(0, color="black", linewidth=0.8)

fig.suptitle(
    "Metadata–data inconsistency under fault injection — Icechunk vs STAC\n"
    f"Local filesystem backend · F1/F2/F3 · {N} trials each (worst-case, deterministic)",
    fontsize=11, fontweight="bold",
)
fig.tight_layout()
fig.savefig("../figures/main_result.png", dpi=150, bbox_inches="tight")
plt.show()

# %% [markdown]
# ## 4. B1 sweeper detail: pre- vs post-sweep inconsistencies (F1 only)

# %%
f1_b1 = df[(df["scenario"] == "F1") & (df["system"] == "stac_b1")]
pre = int(f1_b1["pre_sweep_inconsistent"].sum())
post = int(f1_b1["post_sweep_inconsistent"].sum())
print(f"STAC B1 / F1 — inconsistencies before sweeper: {pre}/{N_TRIALS}")
print(f"STAC B1 / F1 — inconsistencies after sweeper:  {post}/{N_TRIALS}")
print()
print("Interpretation: B1 reduces the window (sweeper reconciles) but does not prevent")
print("the initial inconsistency — the window exists until the sweeper runs.")

# %% [markdown]
# ## 5. Interpretation
#
# Results are reported in `nanopubs/drafts/05_outcome.md` after this notebook has been
# executed and the numbers verified. Do not update the Outcome draft until this cell
# block has run successfully end-to-end.
#
# Key quantities to carry into the Outcome:
# - F1 Icechunk inconsistency count (expected: 0)
# - F1 STAC B0 inconsistency count (expected: N_TRIALS)
# - F1 STAC B1 pre-sweep count (expected: N_TRIALS), post-sweep count (expected: 0)
# - F2 STAC B0 inconsistency count (expected: N_TRIALS)
# - F2 STAC B1 count (expected: 0 — prevented by write-ordering)
# - F3 Icechunk inconsistency count (expected: 0)
# - F3 STAC B0 inconsistency count (expected: N_TRIALS)
# - F3 STAC B1 inconsistency count (expected: N_TRIALS — write-ordering does not close F3)
