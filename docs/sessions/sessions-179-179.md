# Session notes archive — sessions 179-179

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 179 (2026-11-01) — CAP TRIAGE ONLY: NEXT_PROMPT.md 15,496 -> 14,052 BYTES (split, never shave)

**No milestone this fire.** `python3 scripts/evidence.py budget` opened the fire with NEXT_PROMPT.md at 15,496
BYTES, over the kickoff's 15,300 cap-triage trigger: s178 had closed at the gate-side 15,500 target, which is
the WRONG target (it consumed a whole fire). The skill's two cap bullets now say close at <=15,300 BYTES.

- The split: `python3 scratch/s179_split.py` moved footing lines 60-82 — the s178 (M197-M200) block and the
  s175-s177 (M188-M196) block, 23 lines / 2,406 chars — VERBATIM into `docs/pick-archive.md` (16,797 -> 19,671
  chars) under a header naming the registry rows and the four census outputs, and left a 7-line archived pointer
  in their place. The script asserts the moved blob is byte-identically present in the archive and prints
  `moved_lines=23 moved_chars=2406 verbatim_in_archive=True lost=0` on rc 0 — no line was shaved.
- Result after the header/wording edits: `python3 scripts/evidence.py budget` prints NEXT_PROMPT.md **14,052**
  (= `wc -c`; the file is 13,988 CHARS, 64 less) — 1,248 B under the 15,300 trigger, 1,948 B under the gate's
  16,000 FAIL. `python3 scripts/evidence.py prune`: "uncited images older than 7d: 0 (0 KB)" — nothing to apply;
  evidence/ 28.2 MB (warn, FAIL 30).
- **Instrument-vs-prose fix found on the way:** `cmd_budget` compares `os.path.getsize` (BYTES) while its column
  header said `chars` and its `DOC_BUDGETS` comment said "characters" — the skill even asserted "budget counts
  chars, `wc -c` disagrees", which is false (budget == wc -c, verified 14,018 = 14,018). Header now prints
  `bytes`, the comment says BYTES, `docs/EVIDENCE.md` and both skill bullets say BYTES. Thresholds unchanged, so
  the byte reading is the stricter (safer) one.
- Nothing was measured: no census, no box time, the Wine process untouched, so the s174e BOX STATE IS STILL
  UNVERIFIED and M181 is still a LEAD with no positive control. All four picks are untouched and re-queued
  verbatim (the "Pick from:" bullet was not moved).
- Docs: header + CLOSING ORDER re-aimed at 15,300; live skill patched (2 bullets) and `skill/` rsynced. NAMED.md
  untouched — no address changed meaning this fire.
