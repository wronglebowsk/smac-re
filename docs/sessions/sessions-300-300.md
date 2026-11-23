# Session notes archive — sessions 300-300

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-298-296.md` — the hot file cites only THIS archive, so
the chain onward lives here; without this line the older archives are orphans (s292).

## Session 300 (2026-11-19, PR #328 review remediation, zero box)

B26's PR came back with 10 findings, and the prior fire had left `sim/composedsave.py` **edited
but never run** - the tree carried claims (9/9, anchor `1721afbdd1439ec1`) that described a tree
that no longer existed. This fire finished the remediation and re-measured it. Every number below
comes from `python3 -u -m sim.selftest --b26`, byte-identical to `python3 -u -m sim.composedsave`
(63 lines each, sha256 of stdout `a1a5f1e0f310977b`).

- ACCEPT: **`PASS B26: 10/10 gates`** (`evidence/b26_selftest.txt:63`). Anchor moved
  `1721afbdd1439ec1` -> **`ae43e0ab9c8cfc3d`** (`:52`) because the RUN SET grew (the smuggler's
  unexposed control), not the rows: container row digest `abbd009eb9130792` unchanged (`:36`).
  Re-pinned from the printed rows: `REF_SAVE_PIN`, `SPLIT_HIST`, `OWN4_HITS`, `LEDGER_FIELDS`,
  `SMUGGLE_SEES`, `OWN4_SMUGGLE`, `SIZE_LAW`, `ENGINE_STATE`.
- **F1 went the other way, and that is the finding.** Handed the poison it used to be skipped
  for, the smuggler's exposed sha is **`44c3b8319d55eb64`** vs unexposed **`e8cef60dc765c9b2`**,
  2 units' final tiles moved, owner census **1** vs the container's **2** - it is NOT blind. What
  its equality with the clean run measures is OBJECT REUSE, now stated that way. MU14 reinstates
  the exclusion -> G6 alone.
- F2 G10 gates the size law: `[(304,304),(304,304),(356,356),(-252,-252),(356,356),(356,356)]`,
  6/6, the `-252` round = the recorded DESTROY (52 B in, 304 B out). MU15 -> G10 alone.
  F3 totals `67/67/67/68/69/72` vs B25's `67/67/67/67`: G1 compares the SAVE-only half, both
  lists printed (MU20 -> G1 alone). F4 byte histogram by record offset `69/0/0/0/0/0`, pinned.
- F5 `eng = e2` installed; pre-split == rebuilt == `(3,0,2155)` pinned, so the fix had **no
  magnitude on this fixture**: **MU19 reinstates the defect and reddens NOTHING -> declared
  NO-OP, not deleted**, while MU18 (engine year invented) reddens G5 alone. F6 ledger
  FIELD-WISE against a THIRD parse, 20 of 20 (MU17: same count, reversed order -> G3 alone).
  F7 owner census at **+14** (`UNIT_OWNER`), not the **+4** (`UNIT_FLAG`) the first probe read:
  container 2 / clean 0, printed as `(index,x,y)` records (MU16 -> G6 alone). F10 `uninterrupted`
  out of `RIVAL_KEYS` (8 rivals).
- F9 entry-point identity, MEASURED in the harness, and it BITES (relay patched in a temp copy of
  `sim/`: rc=0, 64 lines, marker once). **The first version "passed" on a temp tree that CRASHED
  on `data/alpha.json`** - a comparison that reports "differs" because it never ran is trap 24 in
  a new costume; the code now demands rc=0 AND the marker AND exactly +1 line.
- Harness `python3 -u scripts/b26_mutate.py` -> **19/19 scored + 1 declared NO-OP**
  (`evidence/b26_mutate.txt:24`) **+ MU21, the relay mutant, IDENTITY OK** (`:29`);
  `--selftest` -> **8/8 REJECTED** (`:14`). MU3/MU7 gained G10
  and MU7 gained G3 **from the measurement**, not from the prose guess.
- DELETED the four one-shot doc-rewriting scripts (F8): `scripts/b26_{np_add,np_close,np_trim,rebase_fix}.py`
  (via `git rm`) - anchor-dependent doc mutators with no verification value are operational risk;
  their history stays in git.
- SKILL MIRROR: `skill/` was BEHIND the live `~/.hermes/skills/smac-cvr-format/` (chain 2's
  "Parallel chains" section + the "review findings are CLAIMS" rule, written live at 20:38 while
  this fire was sweeping). `rsync -a --delete` live -> tracked here, so the gate's drift check
  goes green; the content is chain 2's, the sync is this PR's.
- Retracted IN PLACE: `NAMED ## B26` (three rows rewritten, two added), the `CHAIN-BUILDS` B26
  DONE row, `BUILD_SPINE.md` §B26 (now 806-897), plus a SUPERSEDED banner on
  `docs/pick-archive.md` §trim-s299 (e). NEXT_PROMPT 11,745 -> **11,985 B** (M320/M323/M324
  one-liners rotated VERBATIM to §trim-s300-chain1 (a); the `-chain1` suffix is deliberate -
  s299 saw both chains invent §trim-s299 (a) inside an hour).
- OPEN, not swept green: `found_units` 69 -> 0 in the two post-boundary rounds while
  `n_units_img` stays 70/71; and why the exposed smuggler carries the poisoned owner once, not
  twice. NEXT: **B27 rung text UNAUTHORED**; picks (vii)/(viii). #180 (M241, 2/5) stands.
- MERGE OF main under this PR (M324 #326 + M325 #329, chain 2): BOTH chains' sections kept;
  NEXT_PROMPT 12,750 -> **11,950 B** (the two CLOSED pick rows rotated VERBATIM to
  §trim-s300-chain1 (b), sha1 `b0e7c1d2614f2312`; the M325 row kept LIVE; ANSWERED range -> M227-M325).
- **NAMED.md WENT RED, AND THE FIX WAS MINE**: `scripts/gate.py` printed `[FAIL] context/evidence
  budget` because `evidence.py budget` exits 1 once a lookup doc passes its FAIL line - NAMED hit
  **250,102 B against 250,000**, and the cause was this PR's own §B26 block at **11,151 B**, >10x
  the registry's per-block cap. Its full-length rows moved VERBATIM to
  `docs/named-archive-b26-rows.md` (sha1 `45c2cad67c663308`, byte-exactness asserted at write),
  leaving one-line rows with the SAME gates, mutants and cites: NAMED is **246,259 B** and
  `python3 scripts/review_lint.py --id b26` -> **PASS (11 V rows)**. **DEBT: 3,741 B of headroom
  before the next fire reddens the gate for everyone - rotate first, then add.**
