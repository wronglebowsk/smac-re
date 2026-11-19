# Session notes archive — sessions 240-240

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-239-239.md` (inserted at s292: the hot file cites only the newest archive, so without this line the older archives were orphans).

## Session 240 (2026-11-10, CORRECTION, M293) - the three verified Greptile P1s: "distant target -> msg 0x2408" (M290/B13) RETRACTED - msg leg = OWN-TILE + second gate [ebp-0xa4]; M284-M287 live SITE censuses INSTRUMENT-INVALID; sim/selftest run_save IndexError fixed. These were claimed facts, so they are retracted plainly, per AGENTS.md.
- D1 (bytes; gate scripts/m290_hub_decision.py:160): 0x563d48 jne 0x563dfa
  - the distant leg reaches NEITHER founder NOR msg; only esi==0 falls to
  [ebp-0xa4] (single writer 0x55f6d6 = ds:0x920434!=0 AND owner==ds:0x91b5b4):
  flag 0 -> founder 0x563d82-86 (FUN_004cca50, pod args); flag!=0 -> msg
  0x2408 block 0x563d59-0x563d7d + jmp 0x56c925. Own-tile gating +
  founder-args = pod record STAND. The old G4 sliced its OWN table at
  0x563d4e..0x563d81 (founder je-target 0x563d82 abuts the end) - could
  not fail; G4 now parses real branch targets. ACCEPTANCE: python3
  scripts/m290_hub_decision.py programs/saves/m54b_clean.SAV
  evidence/m289_gdb_raw.log evidence/trace_m289_20261110_071759.jsonl ->
  PASS M290: 9/9 (evidence/m290_hub_decision.txt:33; 3 runs, 1-2 were my
  instrument, floors never cut).
- D1b read-only /proc probe (pid 4087359, TracerPid 0): ds:0x920434=0 ->
  msg leg UNREACHABLE in solo: s239 "MSG never observed" was structural,
  not inertia. OPEN: name ds:0x920434 (scenario/MP gate?).
- D2 sim/hubfound.py:94: distant -> ("distant",) (was ("msg",0x2408));
  own+flag -> msg; own -> found. ACCEPTANCE: python3 -m sim.selftest --b13
  programs/saves/m54b_clean.SAV -> PASS B13: 12/12 (evidence/
  b13_hubfound.txt:4).
- D3 guard `if $reg >= 0x1000000` (m284/m285/m286/m287 dispatch arms)
  excluded the five family vtables 0x67164c/0x6717cc/0x6728c0/0x675cc4/
  0x6776c8 (image base 0x400000) - a real family dispatch printed NOTHING:
  every "0 of 12 fired" in M284-M287 = instrument-silence, RETRACTED (CTRL
  rows prove the windows ran). Guards now >= 0x400000; static halves stand;
  re-armed census = open lead. No live re-run this fire (box kept clean).
- D4 sim/selftest.py:177: walk returns (rows, notes), prints nothing -
  buf...[-1] IndexError every run. ACCEPTANCE: python3 -m sim.selftest
  --sav programs/saves/m54b_clean.SAV -> PASS B2: 7/7
  (evidence/s240_b2_run.txt:2).
- Docs: NAMED M290/B13/M292 fixed in place + INVALID banners M284-M288 +
  ## M293; path:line cites per AGENTS.md:50. Next: gate tables
  0x94e5a8/0x94eca8 + name ds:0x920434. BUILD = B14.
