# Session notes archive — sessions 49-49

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 49 (2026-10-22) — M50b: THE TRUNCATION WAS NEVER REAL — every pass scans all n_bases and visits each base exactly once; the year store fires BETWEEN passes, never inside one; and our base IS visited every round

`scripts/m50b_drive.py` = m50a driver with the mineral-pipeline bps replaced by the sweep instrument:
`0x520540` entry (prints the player arg from `[esp+4]` and `n_bases`), `0x5206d3` the `call 0x4f5a70`
site (prints p, idx, owner byte, n_bases, `ours`, storage `+0x40`, minerals `+0x3c`), `0x5206f9` the loop
back edge, `0x5206fd` the exit, and the existing `0x51f554` year store. Runs: `evidence/m50b_run.out` +
`evidence/m50b_watch.log` (1 round, 2351→2352, 0 OCR passes, clean detach), `evidence/m50c_run.out` +
`evidence/m50c_watch.log` (2 rounds, 2352→2354, 110 visits).

**Static (gdb file-target disasm, 0x520540-0x5206fd): the loop bound is live.**
- `0x5206c2-0x5206d0`: `edi = 0x95da14` (owner byte of base[0], stride 0x130), `eax = [ebp+8]` (player),
  and `cmp cl, al; jne 0x5206eb` — non-owned bases are skipped, not processed.
- `0x5206d3`: `push ebx; call 0x4f5a70` — one call per owned base, index passed in.
- `0x5206df`: if `0x4f5a70` returns nonzero, `dec ebx / sub edi,0x130` cancels the tail's increment,
  i.e. **the same base is re-processed** rather than skipped.
- `0x5206eb-0x5206f9`: `mov eax, ds:0x985af4` **every iteration** (n_bases reloaded), `inc ebx`,
  `cmp ebx, eax; jl 0x5206c7`. No cached count, no early-exit path other than `n_bases <= 0`.

**VERIFIED live (15 passes across 3 rounds): the sweep is complete, always.**
- Every pass ends at `last_idx = n_bases-1`: 73 with nb=74 (evidence/m50c_watch.log:32, evidence/m50c_watch.log:122, evidence/m50c_watch.log:125), 74 with nb=75
  (evidence/m50b_watch.log:31, evidence/m50b_watch.log:39). `nb_entry == nb_now` on all 15 passes — n_bases never moves mid-pass.
- Per-player visit counts sum to exactly `n_bases`: `1+7+3+7+9+0+10+37 = 74` (m50c). Every base is
  visited exactly once per round, so the "ours last ⇒ ours can skip a round" premise is dead.
- The old 21/28/28 pattern is a **per-player base count** (p=2 owns 37, p=1 owns 10, p=5 owns 3,
  p=0 owns none), not an early stop. Nothing was ever truncated.
- The year store `0x51f554` fires **between passes**: `mid_p=7, mid_idx=73, mid_visits=9` both years
  (evidence/m50c_watch.log:67, evidence/m50c_watch.log:157) — after the last player's pass completes, before p=0 of the next year. It never
  interrupts a pass, so it cannot skip a base.

**Our base is visited, and its fields are live.**
- idx 71 ("Climactic Research") is **player 2's** base: `VISIT p=2 idx=71 owner=2 ours=1 st=7 min40=1`
  (evidence/m50c_watch.log:117, evidence/m50c_watch.log:126). Player 3 owns exactly one base, idx 70 (`VISIT p=3 idx=70 owner=3 ... st=0 min40=-4`,
  m50c_watch.log:124) — so M50a's "owner 3, ours unvisited" was a misattribution of the neighbour record.
- Between the driver's poke (`+0x40 := 200`, `+0x3c := 500` at locate) and the visit, both fields read
  7 and 1. The per-base work therefore runs on our base and recomputes them; M50a's "poked min40=200
  survived ⇒ unprocessed" does not reproduce.

**Still open (now M51a):** which eip performs that rewrite. M50a's evidence was that `0x4f26e0`
early-returns at the `0x4f2705` gate for the record it believed was ours — and the visit-level data
shows the values changing anyway, so either the gate is a red herring (the writer is upstream in
`0x4f5a70`) or the M50a record identity was wrong. That is the whole of M51a.

**Harness fixes this session (both were blocking, both cost a full run):**
- gdb `-x` script must end with `continue`, or gdb runs off the end and detaches the instant the
  breakpoints are set — a 15-minute run with zero hits looks exactly like "the code never ran".
- The 3-row COMM OFFICER pane ("I have Colonel X on Channel 9…") ignores row clicks: a click only
  highlights, and the bar cycle slides onto "Display faction leader profile" → University Intelligence
  Files, which drained 39 OCR passes over 15 minutes for 0 rounds. `windowfocus`, `key Down`, return
  closes the channel deterministically (selection opens on row 1). Now in the driver and the skill.
