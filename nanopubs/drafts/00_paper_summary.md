# Source summary (question-rooted chain — no upstream paper)

> This is the working scratchpad for Phase 1 of this replication. Because the chain is
> question-rooted (no publicly published paper makes the claim), this file replaces the
> paper-analysis role of `00_paper_summary.md` with a source-analysis role.
> It is not itself a nanopub; it feeds the PICO / AIDA / Claim drafts.

---

## Primary citable source

**Document:** zarr-datafusion-search README
**URL:** https://github.com/developmentseed/zarr-datafusion-search
**Authors:** Development Seed
**Year:** accessed 2026

**Internal Earthmover concept:** "Level 2 Data Collections in Zarr / Icechunk"
(referenced in the README but not publicly released as a document)

---

## The claim surfaced by this source

From the README's **Synchronization** bullet (verbatim, three sentences):

> Our current metadata management solutions (STAC, CMR, ODC) all use disconnected
> metadata stores which reference raw data assets in object storage.
> This can present problems as systems require complex, fragile orchestration to maintain
> consistency between metadata indexes and source data.  Using Icechunk as store can
> alleviate this as array data and metadata updates can be completed in a single atomic
> transaction.

This is the claim the replication tests. The chain starts with a **PICO question**
(not a Quote-with-comment) because the Earthmover whitepaper that originated the claim
was never publicly released; the README is the closest citable public source but was
authored by Development Seed, not Earthmover.

---

## Technical backing

The formal atomicity guarantee is specified at:
https://icechunk.io/en/latest/reference/spec/

Key sentences from the spec (for reference — cite in the Study nanopub's methodology field, not here):

> "Writes to repositories will be committed atomically and will not be partially visible."

> "when updating the object in storage, the client MUST detect whether a different
> session has updated the repo info in the interim."

The spec also documents the conditional-write dependency: the guarantee holds only on
object stores that support compare-and-swap. This is the variable we treat as a factor
in the backend matrix (local FS / MinIO / real S3).

---

## Context: the Level 2 EO use case

Earthmover's concept targets Level 2 Earth observation collections such as Sentinel-2 L2A:
individual heterogeneous scenes that cannot be concatenated into a single datacube because
each granule has variable dtypes, codecs, and CRS values. The proposed architecture stores
both the array data and the granule metadata (acquisition date, bbox, CRS, band list) inside
the same Zarr/Icechunk store, replacing the conventional pattern of a separate STAC/CMR/ODC
metadata index referencing raw object storage.

The replication tests specifically the **consistency sub-claim**: that unifying data and
metadata in one transactional store eliminates the inconsistency window that the
disconnected-index pattern creates.

---

## Replication design choice

- [x] **Replication Study** — the study uses fault-injection methods that go beyond
  passive reproduction; no original experimental data exists to reproduce. The design
  is: same claim, new controlled experiment testing it.

---

## Notes for downstream drafts

- CiTO Citation (step 06) cites the zarr-datafusion-search README URL with intention
  `citesAsAuthority` (the closest public source articulating the claim). Additionally
  cite the Icechunk spec with `usesMethodIn`.
- AIDA (step 02) will be the declarative answer to the PICO question.
- PICO content rule: fault scenarios, trial counts, backend matrix go in Study "how" —
  not in Population or Outcome fields.
