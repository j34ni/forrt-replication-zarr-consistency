# SCOPE.md — replication scope: atomic synchronization claim

Replication target: the **synchronization** rationale stated in Development Seed's
`zarr-datafusion-search` prototype. The prototype attributes the idea to an Earthmover
whitepaper (*Level 2 Data Collections in Zarr / Icechunk*), but **that whitepaper is not
publicly available — we searched and could not find it.** The synchronization claim is,
however, stated verbatim in the prototype's own "Why" section, so the **source of record
for this replication is the Development Seed prototype**, not the (unreachable) whitepaper.

> "Our current metadata management solutions (STAC, CMR, ODC) all use disconnected
> metadata stores which reference raw data assets in object storage … systems require
> complex, fragile orchestration to maintain consistency between metadata indexes and
> source data. Using Icechunk as store can alleviate this as array data and metadata
> updates can be completed in a single atomic transaction."
> — Development Seed, `zarr-datafusion-search` prototype, "Why" section (verbatim).

**This is a question-rooted chain.** Because the originating claim lives in a whitepaper
we cannot reach (only a second-hand relay exists in the prototype), the chain is anchored
on our own PICO question rather than a Quote-with-comment. The chain shape is:

```
PICO question → AIDA → FORRT Claim → Replication Study → Replication Outcome → CiTO Citation
```

The prototype, the Icechunk repo, and STAC are cited as **supporting references** at the
AIDA step's "Supported by other publications" group. The closing CiTO points at the
prototype with `citesAsAuthority` / `usesMethodIn`. Question-rooted changes the *anchor*,
not the *credit* — the idea originates with Earthmover/Development Seed.

This document scopes **only** the consistency/atomicity sub-claim. The DataFusion
query-performance benchmark is a separate replication.

---

## 1. The claim, stated falsifiably

> **C:** When an update touches both array data and its associated metadata, an
> Icechunk-backed store is **never observable** in a state where data and metadata
> disagree — under (a) a writer that fails mid-update, (b) a reader running
> concurrently with a writer, and (c) two writers racing. A disconnected
> STAC-index-over-object-storage baseline **can** reach such a state, or requires
> external orchestration to avoid it.

Two things must both be shown for the claim to hold; either failing falsifies it:
1. **Icechunk side → 0 observable inconsistencies** across all fault scenarios.
2. **Baseline side → >0**, or zero only at the cost of measurable extra orchestration.

---

## 2. What Icechunk actually guarantees (so we test the right thing)

- **Serializable isolation.** Readers always read a committed snapshot; a writer's
  changes are invisible until commit, then visible all at once. Readers take no locks.
- **Atomic commit** via a conditional update to a single reference (branch tip).
- **Optimistic concurrency** for concurrent writers: commit rejected (`ConflictError`)
  if the tip moved since the session started; non-overlapping chunk edits can rebase.
- **⚠️ Conditioned on the object store.** Atomicity needs conditional writes
  (compare-and-swap) + strong read-after-write consistency. This is a **variable, not a
  constant** — pin and document it. Run the *same* matrix on at least:
  - real S3 (conditional PUT supported),
  - MinIO (verify its conditional-write support),
  - local filesystem backend.
  If a backend lacks the primitive, Icechunk's guarantee legitimately weakens — that is
  itself a finding, not a bug to hide.

---

## 3. The invariant (how we *detect* inconsistency)

Pick a metadata value that is a **deterministic function of the data**, so any
disagreement is mechanically detectable:

- Store an array `A` plus an attribute `attrs["data_sha256"]` (or `attrs["sum"]`,
  `attrs["count"]`, `attrs["band_list"]`).
- A **consistency checker** reads metadata, reads data, recomputes the function, and
  asserts equality. Mismatch = one observed inconsistency.

Sample the invariant (i) after every operation and (ii) at random points *during*
operations (the concurrent-read case). Count violations.

---

## 4. Baseline design — avoid the strawman

The whitepaper's real claim is not "STAC can't be made consistent" — it's "STAC needs
fragile external orchestration; Icechunk gets it for free." So run **two** baselines:

- **B0 — naive:** write asset to object storage, then update the STAC item
  (pgstac or static STAC JSON), no transaction, no reconciliation. Shows the natural
  failure mode.
- **B1 — best-effort:** the orchestration practitioners actually use — write-then-index
  ordering, idempotency keys, a reconciliation/sweeper job. Show the **residual**
  inconsistency window and **quantify the orchestration burden** (LOC, moving parts,
  reconciliation latency).

The defensible result is: Icechunk = 0 windows + 0 extra orchestration; B1 = small
residual window + N units of orchestration; B0 = large window. Reporting only B0 would
be a strawman — Anne will flag it.

---

## 5. Fault scenarios

| # | Scenario | Inject | Expected baseline | Expected Icechunk |
|---|----------|--------|-------------------|-------------------|
| F1 | Crash after data, before metadata | kill process between the two writes | dangling/stale metadata | nothing committed; last snapshot intact |
| F2 | Crash after metadata, before data | reverse order, kill between | metadata points at absent/partial data | nothing committed |
| F3 | Concurrent read during write | reader polls invariant mid-write | can observe mixed state | reads pre-commit snapshot, then post-commit; never mixed |
| F4 | Two writers race (overlapping chunk) | two sessions commit same chunk | lost update / silent overwrite | one `ConflictError`, clean retry |
| F5 | Two writers, disjoint chunks | concurrent commits | possible index race | both succeed via rebase |
| F6 | Partial batch (N items, item k fails) | fail mid-batch | items 1..k-1 updated, rest not | all-or-nothing |

F1–F3 are the core (do first); F4–F6 are stretch.

---

## 6. Metrics

- **Headline:** count of observed inconsistent states per 1000 trials, per scenario,
  per backend. Target: 0 (Icechunk) vs >0 (B0; characterise B1).
- **Staleness window:** wall-clock duration the inconsistency is visible to a reader
  (baseline F3).
- **Orchestration cost (B1):** lines of orchestration code, number of services,
  reconciliation lag before consistency is restored.
- **Concurrency outcome (F4/F5):** conflict-detected vs silent-corruption counts.

---

## 7. Out of scope (state explicitly in the writeup)

- Query latency / DataFusion search performance (separate replication).
- Durability vs object-store-level data corruption.
- Multi-region / multi-node distributed stress testing.
- Performance tuning of either system.

---

## 8. FORRT framing

- **PICO question (no method):** *Does storing array data and its metadata in a single
  transactional store (Icechunk) prevent observable metadata–data inconsistency,
  compared to a disconnected STAC index, when updates are interrupted or read
  concurrently?*
- **Claim type:** **data governance** (transactional governance of updates) — secondary
  fit: **data quality** (no inconsistent states). Note both in the Claim nanopub.
- **Study — scope:** the two systems, the fault matrix, the storage backends, the
  invariant. **Study — method:** fault-injection harness + consistency checker + trial
  counts + backend matrix. (No results here.)
- **Outcome:** the inconsistency counts, windows, and orchestration costs. Results live
  *only* in the Outcome nanopub.
- **Research Software nanopub:** the fault-injection harness is reusable upstream
  software → its own RS nanopub, one-way citing the FORRT chain. Icechunk/STAC
  themselves are *not* our software — don't claim them.

---

## 9. Repo / reproducibility requirements (project standard)

- Self-contained: the harness **generates** its synthetic Zarr arrays (no manual data
  prep). Optionally pull one real Sentinel-2 tile via a STAC API for a realism check,
  but the controlled fault tests use synthetic data.
- Standard set: README, environment.yml (single source of truth, drives CI),
  Dockerfile, LICENSE (MIT), CITATION.cff (Zenodo DOI), codemeta.json, Snakefile,
  .gitignore, myst.yml + index.md, GitHub Actions (CI + MyST deploy).
- environment.yml must include everything the notebook imports (icechunk, zarr,
  pystac/pystac-client or pgstac client, nbclient, ipykernel, …).
- Notebook executed in CI (`jupyter execute --inplace`) so MyST shows the result tables.

---

## 10. Suggested minimal architecture

```
harness/
  invariant.py        # data_sha256 / recompute-and-compare checker
  backends.py         # s3 | minio | local store factory (pin consistency mode)
  baseline_stac.py    # B0 naive + B1 best-effort (write+index, sweeper)
  baseline_icechunk.py# session → write data+attrs → commit
  faults.py           # F1..F6 injectors (process kill, concurrent reader/writer)
  run_matrix.py       # scenarios × backends × N trials → results.parquet
notebooks/
  01_atomic_sync.ipynb# generate data, run matrix, plot counts/windows
```

Start with **F1–F3 on the local + MinIO backends** as a one-week vertical slice; if the
asymmetry reproduces, expand to F4–F6 and real S3.
