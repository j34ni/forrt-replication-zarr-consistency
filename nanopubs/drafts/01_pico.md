# 01 — PICO Research Question (question-rooted chains, comparative)

> Chain shape: question-rooted (no upstream paper). PICO chosen over PCC because the
> question has a direct comparator: Icechunk vs disconnected STAC.
> See `docs/chain-decision-tree.md` and `docs/forrt-form-fields.md` § PICO.
>
> Unused step-1 alternates to remove after approval:
> ```bash
> rm nanopubs/drafts/01_quote.md nanopubs/drafts/01_pcc.md
> ```

**Form heading:** *"PICO Research Question — Define a research question using the PICO framework (Population, Intervention, Comparator, Outcome)"*

---

## Field-by-field draft

### Short ID (text input, required)

```
icechunk-atomicity-pico-2026
```

### Research Question Title (text input, required)

10–200 characters.

```
Icechunk atomic transactions vs STAC: observable metadata–data consistency under faults
```

### Complete Research Question (textarea, required)

```
Does storing array data and its metadata in a single transactional store (Icechunk)
prevent observable metadata–data inconsistency, compared to a disconnected STAC index,
when updates are interrupted or read concurrently?
```

### Question Type (radio button, required)

- [ ] Causation
- [ ] Descriptive
- [x] Effectiveness
- [ ] Experience
- [ ] Prediction

### Population (P) (textarea, required)

```
Systems managing Earth observation data collections composed of heterogeneous
scene-level arrays paired with per-granule metadata, where data and metadata must
remain mutually consistent across updates.
```

### Intervention (I) (textarea, required)

```
Storing array data and its associated metadata in a single transactional store
(Icechunk), so that data and metadata updates are committed atomically.
```

### Comparison (C) (textarea, required)

```
A disconnected metadata index (STAC) over object storage, where array data and
metadata are written and managed separately with no shared transaction.
```

### Outcome (O) (textarea, required)

```
Observable metadata–data inconsistency: states in which metadata and the corresponding
array data disagree, detectable by a reader, when updates are interrupted or occur
concurrently.
```

---

## Publication note

After publishing on platform.sciencelive4all.org, paste the resulting URI into
`nanopubs/PUBLISHED.md` step 01, then use that URI in the AIDA draft (`02_aida.md`)
field "Relates to this nanopublication".
