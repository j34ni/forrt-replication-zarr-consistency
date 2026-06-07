# 05 — FORRT Replication Outcome

**Form heading:** *"FORRT Replication Outcome — Record the outcome of a replication study."*

> All numbers in this draft are read directly from `data/results/results.parquet`,
> produced by running `python -m harness.run_matrix --trials 1000` (icechunk 2.0.6,
> zarr 3.2.1, local filesystem backend, seed=42). Do not edit these numbers without
> re-running the matrix.

---

## Field-by-field draft

### Short URI suffix for outcome ID (text input, required)

```
icechunk-atomicity-outcome-2026
```

### Plain-text label for the outcome (text input, required)

```
Icechunk atomic commit: zero inconsistencies across F1/F2/F3, local filesystem backend
```

### Search for a FORRT replication study (search/select, required)

URI of the Replication Study published in step 04. Pull from `nanopubs/PUBLISHED.md`.

```
TBD — paste Study URI after publishing step 04
```

### Repository URL (text input, required)

```
https://github.com/j34ni/forrt-replication-zarr
```

### Completion date (date picker, required)

```
2026-06-07
```

### Validation status (dropdown, required)

- [x] Validated
- [ ] PartiallySupported
- [ ] Contradicted
- [ ] Inconclusive
- [ ] NotTested

> **Rationale:** Both sides of the claim are confirmed on the tested backend. Icechunk
> produces zero inconsistencies across all three core fault scenarios (1000 trials each).
> STAC without external orchestration produces inconsistencies in 100 percent of trials
> across all scenarios. STAC B1 (best-effort orchestration) eliminates some scenarios
> but cannot close the F3 concurrent-read window.
>
> The backend scope is limited to local filesystem (MinIO and real S3 pending) — this
> limitation is noted below but does not change the validation status, because the claim
> is about the mechanism (atomic commit vs disconnected write), not the backend.
>
> CiTO intention for step 06: `confirms`.

### Confidence level (dropdown, required)

- [ ] VeryHighConfidence
- [x] HighConfidence
- [ ] Moderate
- [ ] LowConfidence
- [ ] VeryLowConfidence

> **Rationale:** Strong, deterministic evidence — 1000 trials per scenario with zero
> variance in Icechunk results. Confidence is high rather than very high because the
> MinIO and real S3 backends (where the guarantee depends on conditional writes) have
> not yet been tested.

### Describe the overall conclusion about the original claim (textarea, required)

```
The claim is validated on the local filesystem backend across all three core fault
scenarios. Icechunk's atomic commit produces zero observable metadata–data
inconsistencies in 1000 independent trials under writer failure mid-update (F1),
reverse-order crash (F2), and concurrent reads during an in-progress write (F3). A
disconnected STAC metadata index over object storage (B0, naive) produces
inconsistencies in 100 percent of trials across all three scenarios.

STAC B1 (best-effort orchestration: write-ordering + reconciliation sweeper) eliminates
F2 entirely and closes the F1 window after the sweeper runs. However, B1 cannot prevent
the F3 concurrent-read window: 100 percent of simulated concurrent reads observe an
inconsistency during an in-progress write, identical to B0. This confirms the source
document's characterisation that external orchestration is complex and fragile — and
adds a stronger finding: best-effort orchestration cannot close the concurrent-read
window at all without a locking mechanism that STAC does not provide.
```

### Describe the evidence that supports your conclusion (textarea, required)

```
Fault-injection harness, 1000 trials per scenario per system, local filesystem backend.
icechunk 2.0.6, zarr 3.2.1, Python 3.12. Results in data/results/results.parquet.

F1 — crash after data write, before metadata update:
  Icechunk:       0/1000 inconsistencies (0 percentage points)
  STAC B0:     1000/1000 (100 percentage points)
  STAC B1 pre-sweep:  1000/1000 — post-sweep: 0/1000

F2 — crash after metadata update, before data write:
  Icechunk:       0/1000 (not applicable — single-session atomicity prevents this
                  by construction; recorded as 0)
  STAC B0:     1000/1000 (100 percentage points)
  STAC B1:        0/1000 (write-ordering discipline eliminates F2 entirely)

F3 — concurrent reader during in-progress write:
  Icechunk:       0/1000 (readonly_session reads last committed snapshot only)
  STAC B0:     1000/1000 (100 percentage points)
  STAC B1:     1000/1000 (100 percentage points — write-ordering does not close
                  the concurrent-read window)
```

### Describe what limits the conclusions of the study (textarea, optional)

```
Backend scope: local filesystem only. MinIO and real S3 backends are not yet tested.
Icechunk's atomicity guarantee on object stores depends on conditional writes
(compare-and-swap); this primitive must be verified per backend. Icechunk 2.0.6 itself
warns that the local filesystem store is "not safe for concurrent commits." Our F1/F2/F3
scenarios involve only a single writer at a time, so this warning does not affect the
results reported here — but concurrent-writer scenarios (F4: overlapping chunks,
F5: disjoint chunks) are not yet tested.

Synthetic data only: 256 float32 values per array. Real L2 EO granule sizes (hundreds
of megabytes per scene) may produce different timing characteristics for the F3 window,
though the binary presence/absence of inconsistency is expected to be backend-invariant.

F3 window duration (staleness window) was not measured in this study — only the
presence or absence of inconsistency was recorded. Quantifying the window in wall-clock
time requires a threaded reader design and is deferred to a follow-on run.

F4–F6 (concurrent competing writers, partial batch failure) are out of scope for this
initial vertical slice.
```

---

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 05.
Use that URI in `06_citation.md` field "Identifier for the citing creative work".
