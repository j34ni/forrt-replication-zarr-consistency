# 03 — FORRT Claim

**Form heading:** *"FORRT Claim — Declare an original claim according to FORRT, linking it to an AIDA sentence with a specific FORRT type."*

---

## Field-by-field draft

### Short URI suffix as claim ID (text input, required)

```
icechunk-atomicity-claim-2026
```

### Label of the claim (text input, required)

```
Icechunk atomic commit prevents metadata–data inconsistency in Earth observation stores
```

### Search for an AIDA sentence (search/select, required)

URI of the AIDA published in step 02. Pull from `nanopubs/PUBLISHED.md`.

> If the AIDA was published via Nanodash (`w3id.org/np/...` namespace), paste the URI
> manually rather than relying on the platform's search.

```
TBD — paste AIDA URI after publishing step 02
```

### Type of FORRT claim (dropdown, required)

- [ ] computational performance
- [ ] scalability
- [ ] data quality
- [x] data governance
- [ ] descriptive pattern
- [ ] model performance
- [ ] statistical significance

> **Rationale:** The claim is about transactional governance of updates — whether the
> mechanism that controls how data and metadata are written together (atomic commit)
> prevents an inconsistent state. This fits "data governance" as the primary genre.
>
> **Secondary fit: data quality.** The vocabulary defines data quality as "preserving
> fidelity through transformations"; the absence of inconsistent states is a data-quality
> outcome. The form is single-select, so governance is chosen as primary (it names the
> mechanism) and quality is noted here as the secondary framing (it names the result).
> If the platform later supports multi-type claims, add data quality as secondary.

### Source URI (text input, optional)

Full URL form (not bare DOI). Primary citable source articulating the claim.

```
https://github.com/developmentseed/zarr-datafusion-search
```

---

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 03.
Use that URI in `04_study.md` field "Search for a FORRT claim".
