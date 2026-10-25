# Session notes archive — sessions 72-72

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 72 (2026-10-24) — M53Q3: **THE SEMANTIC INDEX NOW CONTAINS OUR FINDINGS — `note_chunks()` used to hold only SESSION_NOTES + rotated archives (42 chunks vs 2,790 decompiled functions) and truncated every section at 1500 chars, so `index.py search` could not find a single evidence note; it now chunks every `evidence/*.md`, `skill/references/*.md` and `NAMED.md` row (2,832 -> 3,465 chunks) with a +0.02 note prior, and the two queries that used to fail now return the right hits at rank 1-2** — `scripts/index.py`, `docs/SEARCH.md`
- **Diagnosis (VERIFIED).** `index/meta.json` had 2,790 functions / 42 notes; `note_chunks()` read only
  `SESSION_NOTES.md` + `docs/sessions/*.md` and did `text[:MAX_CHARS]`, so long session sections lost
  their tail citations and no `evidence/*.md` was indexed at all. `source_fingerprint()` hashed only
  SESSION_NOTES + Ghidra shards, so editing a finding never marked the index stale. Measured failure:
  `search "unit chain link field +48 +50 livelock"` returned 8 unrelated functions (FUN_005ab130 and
  FUN_005a6330 absent); `search "energy-only residual in the middle pass c4"` ranked our own note 7th at
  0.722 vs 0.734 for noise (0.012 spread over 2,832 candidates). Only consumer: `scripts/index.py`
  (grep over `~`), so the 258v GPU was idle ~all day.
- **Fix (VERIFIED by rebuild + acceptance test).** `_note_sources()` = SESSION_NOTES + NAMED + every
  `evidence/*.md` + every `skill/references/*.md` + `docs/sessions/*.md`; `_pack()` splits sections into
  <=1400-char windows (no truncation); one chunk per NAMED row (`named:<line>`); `source_fingerprint()`
  covers all of them; `NOTE_PRIOR = 0.02` added to note cosine scores. Rebuild: **3,465 chunks
  (2,790 functions, 675 notes), 409-693 chunks embedded in 16-24 s**; full rebuild stays cheap because
  the digest cache only re-embeds changed chunks.
- **Acceptance test (the point of the milestone).** `search "unit chain link +48 +50 livelock"` ->
  `NAMED.md:485` (`0x5a6330`, walks `+48`) rank 1, `NAMED.md:484` (`0x5ab130`, walks `+50`) rank 2.
  `search "energy-only residual in the middle pass c4"` -> `evidence/m53p_j_findings.md:75` rank 1,
  `evidence/m53p_partial_findings.md:32` rank 2, `evidence/m53p_swap_findings.md:58` rank 6. Before the
  fix: zero on-point hits in either.
- Caveat: `skill/references/wine-operations.md` (moved verbatim from the old SKILL.md) also contains the
  7-vector-add-site digest, so it competes with `production-rebuild.md` for production questions — worth
  splitting when that file is next touched.
- **Next:** `NEXT_PROMPT.md` — M53q unchanged (implement `build_table`); `index.py search` is now the
  first look-up step before grepping.
