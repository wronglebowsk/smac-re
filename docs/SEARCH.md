# Semantic search over the project

`scripts/index.py` builds a small local index over two corpora and answers fuzzy questions
that grep cannot: *"have we already ruled this out?"* and *"which function might do this?"*.

It is a **discovery aid, not evidence**. A hit gives you a `file:line` or an address; you still
prove the claim before it enters the notes.

## Commands

```bash
python3 scripts/index.py build                 # incremental, ~1 s when nothing changed
python3 scripts/index.py build --cold          # re-embed everything (~35 s)
python3 scripts/index.py build --all           # include boilerplate functions (10,284 chunks)
python3 scripts/index.py search "why does our base never convert minerals"
python3 scripts/index.py search "draw a rectangle with saved state" --kind function
python3 scripts/index.py search "mineral spend" --json | jq
python3 scripts/index.py status                # counts + staleness + source fingerprint
```

`milestone.py merge` rebuilds the index automatically after a successful merge
(`--no-index` to skip). The rebuild is **fail-soft**: if the embedding endpoint is down, the
merge still stands and the previous index is kept. Search then prints a clear error rather than
silently returning stale results.

## What is indexed

| corpus | chunks | text |
|---|---|---|
| session notes | one per `## Session` section, hot file + `docs/sessions/` | headline + body, capped at 1500 chars |
| functions | one per function, from `ghidra_out/shard_*.c` | signature, NAMED.md description if any, string refs, data refs, callees |

Chunks are capped at **1500 characters** because the model truncates at 512 tokens. Anything
longer is silently cut, so the index never pretends to see the end of a long section.

**Boilerplate functions are excluded by default.** A function with no name, no strings, no data
references and fewer than six callees produces text like `FUN_004b8e30 calls FUN_004b8e30` —
it embeds to noise and dilutes real queries. That leaves 2,786 of 10,284 functions, plus notes.

## LLM summaries (`scripts/summarize.py`)

The mechanical text for an unnamed function carries no meaning, so it is labelled once by the
local 125B (`$SUMMARY_URL`) and the sentence is folded into the chunk:

```bash
python3 scripts/summarize.py --dry-run     # work remaining
python3 scripts/summarize.py               # resumable; ~1.7 h for 2,786 functions
```

`index/summaries.jsonl` is committed (it is expensive to regenerate) and keyed by a hash of the
decompiled body, so a rerun only labels functions that changed. `enable_thinking: false` is
mandatory — this model otherwise spends the whole 120-token budget reasoning and returns an
empty string.

**Ordering matters.** A NAMED row is identifier-rich and beats prose: appending a summary in
front of it cost 3 of 8 rank-1 hits (mean pooling dilutes exact names). So NAMED leads, the
summary is only used when a function is unnamed, and callees are always included.

## Measured quality (2026-10-22)

- Notes: *"why does our base never convert minerals into energy"* → the M50a section at rank 1 (0.737).
- Named functions: *"draw a rectangle with saved graphics state"* → `0x5dd09c` at rank 1 (0.809);
  *"open a file and sniff the magic bytes"* → `0x598340` at rank 1 (0.789).
- Anonymous functions: **fixed by the summary pass** — *"load a map or scenario file"* → `0x598250`
  at rank 1 (0.782), a map loader we had not identified; *"advance the game year counter"* →
  `0x4e0350` at rank 1; *"load a PCX image for an icon"* → `0x610308` at rank 1 (was rank 7).
- 10-query benchmark with hand-picked targets: **hit@1 5/10, hit@10 8/10**. Both top-10 misses
  turned out to be *bad labels*: the rank-1 answer was a better fit than the function I had
  nominated. Score these against a judged top-3, not exact address match.

The model's "unrelated" baseline is high (~0.65–0.70 cosine), so treat the absolute score as a
ranking signal only; compare hits against each other, not against 1.0.

## Where the data lives

```
index/chunks.jsonl   ~800 KB   text + pointer back (path:line or address)
index/vectors.f32    ~8.6 MB   one L2-normalised 768-float vector per chunk
index/meta.json                model, dimension, counts, source fingerprint
```

All of it is **derived and disposable**, and gitignored: delete `index/` and rebuild. The sources
are authoritative. Nothing runs as a service — search loads the file and does a dot-product scan
(~0.3 s at 2,809 chunks in pure Python).

## Failure modes

- **Stale index.** `status` compares the stored source fingerprint against the files and prints
  `STALE`. A merge rebuilds it; a hand-edited note does not.
- **Embedding endpoint down.** `index.py build` exits non-zero with the fix command; `merge`
  downgrades that to a warning.
- **Model changed.** `meta.json` pins the model name and dimension; a mismatch discards the cache
  and rebuilds rather than mixing vectors from two models.
- **Concurrency.** The 258v server 500s on parallel requests (`Infer Request is busy`), so the
  builder is deliberately single-threaded. Do not parallelise it until that bug is fixed.

## What is in the index (M53Q3)

`scripts/index.py build` now chunks **two corpora**:
- `kind=function` — decompiled Ghidra functions, text = address + size + NAMED row (if any) + summary.
- `kind=note` — every `## ` section of `SESSION_NOTES.md`, `docs/sessions/*.md`, **every
  `evidence/*.md`**, **every `skill/references/*.md`**, plus **one chunk per `NAMED.md` row**.
Long sections are packed into <=1400-char windows, never truncated. Notes carry a +0.02 cosine prior
(`NOTE_PRIOR`), because curated prose is what a milestone question actually wants.
`status` hashes all of those files (not just SESSION_NOTES + Ghidra shards), so an edited finding makes
the index STALE immediately.

Acceptance test (the two queries that used to fail): `search "unit chain link +48 +50 livelock"` returns
`NAMED.md:484/485` (the two chain walkers) in the top two; `search "energy-only residual in the middle
pass c4"` returns `evidence/m53p_j_findings.md` first.
