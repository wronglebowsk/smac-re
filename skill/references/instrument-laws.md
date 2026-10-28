# Instrument laws: containment, legs, cadence

## Containment before blame (`ghidra_out/index.csv`)

Header: `addr,name,size_bytes,n_insns,n_callers,n_callees,n_strings,ok,chars,shard`. Containment =
`addr <= site < addr + size_bytes`. Print the resolved row so a wrong lookup cannot impersonate a finding.

- A site inside a function with ONE call site, where the docs/strings name a mode you are not in (e.g.
  the multiplayer stage driver FUN_00521070), is unreachable BY DESIGN — no re-run will ever log it.
- Two sites inside the SAME many-caller helper, one of whose callers sits in the human-turn loop, are an
  UNTAKEN BRANCH: the game is live and the breakpoint asked the wrong question.
- A `csv.DictReader` with guessed column names and a bare `except: continue` reports "no containing
  function" for EVERY address — read the header line first.

## Leg census: predictions first, counters second

Compute each site's expected hit count from live memory before arming (the gate globals, the caller's
args off `$esp`, the table values the branch itself loads), print those predictions, then gate on
agreement with the counters. Working templates: `scripts/m86_helper_legs.py` (FUN_005a7970's leg ladder
plus both gate blocks) and `scripts/m87_aaa20_trigger.py` (attribute every hit by its return site, then
resolve the caller by containment).

- Demanding a hit at a site the TAKEN leg cannot reach FAILs the milestone, not the game — fix the leg
  map, never lower a floor (s138: m86cens1 died exactly here, on gates that asked for loop-tail hits the
  table-miss leg cannot produce).
- A breakpoint at an address that is BOTH a branch target and a loop-completion fallthrough is not a leg
  proof — read the predecessors in the disassembly before naming a leg from a counter (0x5a7f9f is
  `jne 0x5a7f9f`'s target AND the 64-record band loop's fallthrough; ALT=3 with ENTRY=1 was the
  3-entry table walk, not three calls).
- A hit count inside a window is not a CADENCE: tie each hit to a boundary (round/year read at the hit)
  or write "cadence unproven". s138: FUN_005aaa20 fired only on the FIRST boundary after a fresh save
  load, and only in windows where the driver's own accounting failed and the round jumped 2 — two
  variables moved together, so that is reported as confounded.
- Attribute a call by its RETURN SITE: `*(int *)$esp` at the callee's entry, then containment. That is
  how FUN_005aadf0 (site 0x5aaf46) -> FUN_005aaa20 (site 0x5aaacb) -> FUN_005a7970 was named, with the
  call bytes printed (`e8 d5 fa ff ff call 0x5aaa20`).
- A typo in your own constant FAILs the instrument, not the game: m87trig1 died on 0x5aaccb where the
  real call site is 0x5aaacb. Print the bytes you claim to have named, and gate on them.
