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

## Who writes a field: pointer-form stores and the control watchpoint (s139, M88)

A grep of the objdump for the mnemonic text `mov [...+0xBASE],reg` finds only DIRECT stores. A field is
just as often written through a pointer built earlier — `lea esi,[eax*4+0xBASE]` (0x5aa9c5 in
FUN_005aa880) or `lea esi,[esi+ecx*4+0x94d7fc]` inside the 64-caller accessor FUN_0052a720 (0x52ae09) —
and then `mov [esi],ebx` (0x5aa9d3). Enumerate both forms, or stop guessing and use a hardware
watchpoint on the address: one poke plus one boundary named the writer exactly once.

- **Arm a CONTROL watchpoint on an address you know changes** (the round counter `ds:0x985afc`, written
  at 0x51f53c `a3 fc 5a 98 00` inside FUN_0051f320). If the control fires and the target stays silent,
  the target really was not written in that window; if NEITHER fires, the debug registers are not doing
  anything and the run says nothing about the target. s138's m88slot2/3 looked like "watchpoints are
  blind here" only because there was no control.
- gdb stops at the instruction AFTER the store, so walk back one instruction to name the writer — and
  skip objdump's byte-continuation lines (they carry an address label but no mnemonic column;
  0x5aaac8 is a continuation of the store at 0x5aaac1, not an instruction).
- A /proc/pid/mem poke from python does NOT trigger the inferior's debug registers (it is not an
  instruction executed by the tracee), so the poke itself never appears as a watchpoint event; verify it
  by read-back instead.
- Do not demand that a rotating consumer process the record YOU poked within the window — aaa20 picks
  different records per boundary (4, 6, 1 / 3 / none / 4 of them). Gate on the invariant the game
  actually asserts (aaa20's kind == the slot value it read, 8/8 events) and treat "consumer did not run
  in this window" as an uninformative window, not a failure.

## Threading, pairing, and naming a domain (census work on a value, not a store)

- **Thread a datum between breakpoints with gdb convenience variables, and clear it at the entry stop** so
  a stale value cannot impersonate a match: `set $ret = *(int *)$esp` at the callee's entry,
  `set $chr = -999` there, then print `$chr` at the store site deeper in the SAME call. A gate that
  compares a threaded value is only as strong as the thread: without the sentinel, the PREVIOUS call's
  value passes the gate.
- **Pair a look-back or look-ahead by the event's index in the WHOLE parsed list**, never by its index
  inside a filtered sub-list: `for i, e in enumerate(st): ... events[:i]` slices at the wrong offsets, so
  the look-back silently returns None and a gate FAILs on the instrument while the log already contains
  the agreement. Build `pos = {id(e): i for i, e in enumerate(events)}` once and slice with it. Check the
  informational columns of the same loop too — a wrong slice there is invisible until a later read trusts it.
- **At a post-`call` landing site, cdecl arguments sit at `[esp] .. [esp+0xc]`** when the caller pops them
  (`add esp,0x10` a few instructions later) — ONE SLOT LOWER than at the callee's entry. Printing
  `esp+4 .. esp+0x10` labels every argument one position high, and the extra slot is the callee's own
  pushed register, which often equals arg1 and reads like confirmation.
- **A big local frame is not a candidate array.** `sub esp,0xNNN` plus `mov eax,fs:0x0` /
  `mov fs:0x0,esp` plus a `[ebp-0x4]` state variable rewritten (`mov BYTE PTR [ebp-0x4],0x3`) before each
  call of a small destructor-like function is an MSVC SEH frame with C++ locals, not a scan buffer.
  **Read a wrapper's TAIL to learn what it returns:** `mov esi,eax` after the callee's call and
  `mov eax,esi` before the `ret` is a verbatim pass-through, so the semantics live in the callee and the
  wrapper is not the place to instrument.
- **Naming an unknown value's domain, three cheap steps:** (1) a caller's `cmp reg, 0xNN` against the value
  is usually the table's BOUND (`cmp ecx,0x59` ↔ 89 entries) — take the stride from the loop's own index
  arithmetic (`[reg*0xb]` = 11 dwords = 44 B); (2) dump one record RAW from `/proc` for several indices the
  census already produced and look for a fixed-offset name field (8 ASCII bytes at +16); (3) corroborate
  with a relationship the domain must satisfy (entry 10 lists prereqs 30 and 7 — a real dependency pair).
  A finding that stops at "an index into some table" is not finished: the NAME is what the next milestone
  can reason with.
- **Decode semantics without touching the box:** `grep -m1 0x<addr> ghidra_out/index.csv` gives size,
  caller count and shard; `grep -n 'FUN_<addr> @' ghidra_out/shard_*.c` gives the pseudocode start; then
  `sed -n 'A,Bp'` a 40-line window, or `awk 'NR>=A && NR<=B' shard_NNN.c | grep -n -E 'param_|return|"'`
  to locate every argument use and every return in one call. A 27 KB pseudocode body is never read whole.

## Where a breakpoint prints the wrong thing (s146, M92)

- **A breakpoint on a LOAD prints the register's PREVIOUS value** — a bp at `mov ebx,[ecx+0x94e488]`
  reports that field as whatever the last call left in `ebx`; read the memory operand outright or break
  one instruction later.
- Same class: a bp on a loop's first BODY address never fires when the loop is skipped — a zero there is
  the gate, not a missing mechanism. Break at the loop's condition, and at its EXIT when the leg's OUTPUT
  is what you intend to gate on rather than the leg plus whatever the function does next.
- **Any value the round itself mutates cannot come from a round-start snapshot** — read it per hit, and
  let the snapshot supply only the arrays.
- **A null model built from the same term is not a null**: a cat-7-only null over a cat-7 block agrees
  with the true rule by construction and re-certifies itself green run after run (s145 burned six runs
  this way).

## Freeze inputs at the CONSUMER's timing (s147, M93)

A round-boundary snapshot is only valid for values the round does not rewrite. m93post2 FAIL 8/9 ->
m93post3 PASS 9/9: the tail-block freeze (M92) holds for the 0x94e488 block, but 0x92adbc, the era
table 0x92b954, designed prereq fields and the demand dwords move between the boundary hit (0x51f320)
and the ladder inside the same round — closures/gates built on boundary-frozen copies over- and
under-fire (4 candidates). Fix: dump the input regions AT the hit where the consumer reads them
(gdb `append binary memory` per hit, like the tailx1/tailx2 dumps in scripts/m93_post_census.py).
Corollary: when a model-vs-engine mismatch splits into "model fired, engine didn't" AND "engine
fired, model didn't" on the same gate, suspect TIMING of the shared inputs, not the rule.

## Generated breakpoint conditions: the register IS the address

A harness that EMITS its own gdb conditions must compare the register bare when the site's own
encoding shows the register holds the record address — `mov esi,[ecx+0x40]` and `cmp
[ecx+0x40],edi` mean ECX *is* the base, so the condition is `if $ecx==0x95da10`. Emitting
`if *$ecx==0x95da10` tests the dword AT that address, which virtually never equals an address, so
those sites log ZERO events while a hardware watchpoint on the same field proves the leg ran.

- Read the site's bytes to pick the register, then diff the emitted `scratch/<tag>.gdb` against
  those bytes before attaching. The condition text is the cheapest thing in a run to get wrong and
  the most expensive to discover afterwards: it turns a real event into "the site never fires".
- Free self-check before arming: a printf body that prints `$ecx` as `base=0x%x` and a condition
  that DEREFERENCES `$ecx` contradict each other — one of the two is wrong, and the bytes decide.
- **Zero breakpoint events plus live watchpoint events on the same field in the same window is an
  instrument verdict, not a negative result.** Only zero from both — with the control watchpoint
  firing — says the game did not run the leg.
- Two watchpoint hits on one field in one pass name TWO writers: read the pass as a store sequence
  and disassemble backwards from EACH reported pc (the pay store and the clamp that follows it —
  `references/production-queue.md` — both hit `base+0x40` inside one visit).
- A breakpoint at a `mov eax,[ebp-0xc]` RETURN site prints the OLD eax: break at the NEXT instruction
  (in the tech chooser FUN_005aa030, 0x5aa247 is the load, 0x5aa24a is where `$eax` is the return value;
  m96human1 printed idx=0 for that reason). Likewise a register that a loop repurposes as a divisor or
  modulus is not the loop variable: at 0x5aa232 `edi` is `score+1` on the rand path (`lea edi,[eax+1]`
  at 0x5aa21a), so read the faction from `*(int *)($ebp+8)`, never `$edi`. Name every printf field the
  way the parser asks for it — a field-name bug reads as a game FAIL (m96human1 G4/G9/G11).
- A chooser/scorer leg can be predicted EXACTLY from a global RNG object: the human tech pick is
  `FUN_00625af1(0, score+1)` = thiscall `FUN_00625a0f(&ds:0x999fa0, lo, hi)` — swap if lo>hi, then
  `state = state*0x19660d + 0x3c6ef35f (mod 2^32)` and `val = ((state & 0xffff) * (hi-lo)) mod 2^32
  >> 16 + lo`. Read the state at the call site BEFORE the call, predict, compare with the register at
  the next site: 7/7 exact and the stream advanced exactly one step per candidate (s151, m96human2).
  Non-human factions use `_rand() % (score+1)` (0x64c6f0) instead — a DIFFERENT stream.
