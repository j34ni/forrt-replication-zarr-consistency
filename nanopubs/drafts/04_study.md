# 04 — FORRT Replication Study

**Form heading:** *"FORRT Replication Study — Describe the design of a replication study linking it to a FORRT claim."*

---

## Field-by-field draft

### Short URI suffix for study ID (text input, required)

```
icechunk-atomicity-study-2026
```

### Label/name of replication study (text input, required)

```
Icechunk atomic commit consistency study: fault-injection across storage backends
```

### Study type (dropdown, required)

- [ ] Reproduction Study — direct reproduction: same methodology, same tools.
- [x] Replication Study — replication with different methodology or conditions.
- [ ] Reproduction/Replication Study — both.

> **Rationale:** No original experimental methodology exists to reproduce — the claim
> comes from a design rationale document, not a published experiment. This study is the
> first experimental test of the claim, using fault-injection methods that go beyond
> passive reproduction.

### Search for a FORRT claim (search/select, required)

URI of the Claim published in step 03. Pull from `nanopubs/PUBLISHED.md`.

```
TBD — paste Claim URI after publishing step 03
```

### Describe what part of the claim is reproduced/replicated (textarea, required)

*Scope only — not methodology, not results.*

```
The consistency sub-claim only: that an Icechunk-backed transactional store produces
no observable metadata–data inconsistency when an update is interrupted mid-write, when
a reader accesses the store concurrently with an in-progress write, or when two writers
compete. Tested across three storage backends (local filesystem, MinIO, real S3) to
determine whether the guarantee is conditional on the object store's support for
atomic conditional writes. The study also tests two baseline configurations of a
disconnected STAC metadata index (naive and best-effort with reconciliation) to
characterise the inconsistency window and orchestration cost of current practice.

Out of scope: DataFusion query-performance, storage durability against object-store
corruption, multi-region distributed stress testing, and performance tuning of either
system.
```

### Describe how the claim is reproduced/replicated (textarea, required)

*Method in plain prose — verified against harness/ code (icechunk 2.0.6, zarr 3.2.1).*

```
A fault-injection harness (harness/, Python 3.12) generates synthetic Zarr arrays of
256 float32 values per trial (no manual data preparation). Each array is stored with a
deterministic metadata attribute — a SHA-256 checksum of the array data — that allows
mechanical detection of inconsistency: a consistency checker reads the stored attribute,
recomputes the checksum from the current data, and flags any mismatch as one observed
inconsistency.

Faults are injected by raising a SimulatedCrash exception at a specific point in the
write sequence, then abandoning the in-progress state. For Icechunk, an uncommitted
session is abandoned (equivalent to a process crash before commit). For the STAC
baseline, the zarr write or STAC JSON write is interrupted at the chosen fault point.

Three core fault scenarios are run: (F1) crash after the zarr array write but before
the STAC metadata update; (F2) crash after the STAC metadata update but before the
zarr array write (reverse write order); (F3) the consistency invariant is sampled
between the two STAC writes, simulating a concurrent reader arriving during the update
window. F2 is not applicable to Icechunk (single-session atomicity prevents it by
construction). Each scenario is applied to three configurations: Icechunk-backed Zarr
store, STAC B0 (naive: write-then-index, no transaction), and STAC B1 (best-effort:
write-ordering discipline plus an explicit reconciliation sweeper). The matrix runs 1000
independent trials per scenario per configuration on the local filesystem backend.
Results are written to Parquet (data/results/results.parquet).
```

### Describe any deviations from original methodology (textarea, optional)

```
Not applicable — this is a question-rooted chain with no prior published experimental
methodology to deviate from. The study design is original.
```

### Search keywords (Wikidata) (multi-select, optional)

Labels (not QIDs):

- Zarr
- metadata consistency
- transactional storage
- Earth observation
- data governance
- fault injection

### Search discipline (Wikidata) (search, optional)

- computer science
- data management
- Earth observation

---

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 04.
Use that URI in `05_outcome.md` field "Search for a FORRT replication study".

> **Before publishing:** replace this draft's "how" field with content verified against
> the actual harness code in `harness/` and notebooks. Method details (specific
> libraries, exact trial counts, any deviations from the SCOPE.md §10 architecture)
> must reflect what was actually implemented and run.
