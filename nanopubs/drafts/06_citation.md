# 06 — CiTO Citation

**Description:** *"Declare citations between papers or other works, using Citation Typing Ontology"*

> This is a question-rooted chain (no upstream paper). The CiTO cites the public
> document that articulates the claim we tested (`confirms`), plus the Icechunk
> specification that defines the protocol used as the intervention (`usesMethodIn`).

---

## Field-by-field draft

### Identifier for the citing creative work (text input, required)

URI of the Outcome published in step 05. Pull from `nanopubs/PUBLISHED.md`.

```
TBD — paste Outcome URI after publishing step 05
```

### List citations (repeatable group, required ≥1)

#### Citation 1 — Development Seed prototype (source of record for the claim)

##### Citation Type (dropdown)

```
citesAsAuthority
```

> Rationale: the prototype is the authoritative public source that states the
> synchronization claim. We cite it as the authority from which the claim originates,
> not as a work we are confirming or disputing. Question-rooted chains credit the source
> at the CiTO step with `citesAsAuthority` or `usesMethodIn` rather than `confirms`
> (which applies to paper-rooted chains where the Outcome validates a quoted claim).

##### DOI or other URL of the cited work (text input)

```
https://github.com/developmentseed/zarr-datafusion-search
```

---

#### Citation 2 — Icechunk specification (protocol reference)

##### Citation Type (dropdown)

```
usesMethodIn
```

> Rationale: the intervention (Icechunk atomic commit) is defined in the Icechunk
> specification. The harness uses the session → commit → readonly_session protocol
> described there.

##### DOI or other URL of the cited work (text input)

```
https://icechunk.io/en/latest/reference/spec/
```

---

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 06.

This completes the six-step FORRT chain:
PICO → AIDA → Claim → Study → Outcome → CiTO ✓

**Optional next layers:**
- **Research Software** (`07_research_software.md`) — the fault-injection harness
  is a reusable artefact; its RS nanopub one-way cites the FORRT Claim URI.
- **Research Synthesis** (`08_synthesis.md`) — if this chain is later combined with
  the MinIO/S3 backend runs or the F4–F6 extension into a cross-cutting synthesis.
