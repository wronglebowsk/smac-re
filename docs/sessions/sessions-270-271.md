# Session notes archive — sessions 270-271

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 270 (2026-11-16, docs cap split, zero box)

- NEXT_PROMPT.md was **11,922 B — 78 B from the 12,000 B warn cap**, so the CAP SPLIT ran BEFORE any
  milestone, per protocol. Moved the §THE PICK **CLOSED enumeration** (M220 .. M308, each with the
  NAMED section to read before re-opening it, and what it settled) + the OPEN-shortlist one-liner
  **VERBATIM** to docs/pick-archive.md §trim-s270. The move is byte-exact by construction: one python
  step sliced lines[64:80] (1,614 B), appended that exact string to pick-archive and wrote the file
  with the 4-line pointer in its place. Result: wc -c NEXT_PROMPT.md = **10,694 B** (1,306 B
  headroom), evidence.py budget -> ok.
- Nothing retracted, no claim moved: zero measurements in this PR, so NAMED.md is untouched and the
  gate warns "address registry: NAMED.md untouched (fine if no addresses changed)".
- PITFALL (own): scripts/gate.py refuses a docs-only PR with "[FAIL] milestone checkpoint:
  SESSION_NOTES.md has no new '## Session' section" — a cap split needs its own session section; the
  milestone that follows closes as Session 271.
- PITFALL (own): shell-quoting a markdown body inside printf breaks on backticks/parens. Append docs
  through a quoted heredoc into python, never through printf.

## Session 271 (2026-11-16, ANALYSE M309 + a cap split, zero box)

- Cap split first, its own PR #282 MERGED: NEXT_PROMPT.md was 11,922 B (78 B from the 12,000 warn
  cap); the CLOSED enumeration moved VERBATIM to pick-archive §trim-s270 -> 10,694 B.
- **M309 closes the s268 pick.** FUN_0056d350 (299 B, 50 callers) = **the GOAL-list insert-or-max**
  of the same 8380-B block record whose SITE list M308 named. `python3 -u scripts/m309_goal_sink.py`
  -> **54/54 checks OK**, exit 0, `RESULT: PASS ...` (evidence/m309_goal_sink.txt:278,280, 17,473 B);
  re-run stdout vs committed evidence: diff **0 lines**. `python3 -u scripts/m309_mutate.py` ->
  **9/9 mutations reddened their target checks**.
- The name is the binary's own: 0x56d350's parity guard pushes **0x6914fc = "Bad GOAL"**; FUN_0056d480
  pushes **0x691508 = "Bad SITE"** - 12 B apart in one .data pool (A28). Entry = {+0 short kind, +2
  short prio, +4 d, +8 d, +0C d owner} (A5); both walks bound **0x4b = 75** (A11); stride 8380
  re-derived (A3) plus a **second independent** `imul r,r,0x20bc` at 0x470d50, outside the function.
- **The -1 6th arg** = the entry's +0C owner. Among ALL **65** .text operands naming an address inside
  the 100-entry block, +0C has **1 writer (0x56d470) and 1 reader (0x559b3e)** (A36). The reader is
  signed, `test eax,eax / jl 0x559b74`, scaled 9x -> 19x -> <<4 = **x304** onto **0x95da40**, used as
  `test BYTE [edx+0x95da40],0x20` (A38-A40), gated on the same entry's +0 == 9 (A41). **-1 selects
  nothing - it is the unbound-owner sentinel**, and a duplicate call never refreshes it (found path
  stores ONE WORD, A13).
- Callers: 40/50 push 0xffffffff; 5 push a register the def-walk closes on **ds:0x68cbb0** (340 refs,
  exactly 6 stores, all 0x4e3000-0x4f6000, A42); **5 DECLARED unattributed** (push group crosses a
  branch/call) - printed, not hidden (A32/A33). Identity of ds:0x68cbb0 stays OPEN.
- **M308 U2 partly answered**: the GOAL list's -1 sentinel HAS a writer in .text - `mov WORD PTR
  [ecx+edx+0x94ee28], 0xffff` at **0x470d5c in FUN_00470b90** (1020 B, 5 callers). M308's "0 such
  writers" row patched in place: true for the SITE window, false for the GOAL window.- **P1 (Greptile #283, on the head commit, and it was RIGHT): `open(p,'w').write(open(p).read().
  replace(c,d))` truncates the file BEFORE the argument is evaluated - it wiped all 1,156 lines of
  NAMED.md.** Repaired in the same PR: `git checkout origin/main -- NAMED.md` (170,459 B), then the
  two M308 row patches and the `## M309` block re-applied from in-memory strings; `wc -c NAMED.md` =
  173,332 and `git diff --stat` now shows additions, not a deletion wave. Law: a checkpoint tool must
  read into a variable, then open for write; and `git diff --stat` against main is a required step
  before submit - the gate passed a whole-registry deletion because it only asks whether NAMED.md
  "was updated".

- PITFALL (own, caught by my own harness): `a1..a6 = [x[1] for x in ps]` on a list push_group returns
  CHRONOLOGICAL made "arg6" silently arg1 - the census printed 17 `esi`, zero constants; only M1 of
  m309_mutate caught it. And three new gates CRASHED instead of going red (a None in a print, an
  empty `band[0]`, list-vs-tuple dict compare): **a gate that dies is not a gate either.**
