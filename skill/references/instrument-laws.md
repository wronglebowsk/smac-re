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
- When a GATE compares watchpoint-reported pcs with a static store list, the expected set is
  `store + instruction length`, NOT the store addresses: 10 bytes for
  `mov DWORD PTR [reg+disp32],imm32`, 6 for `mov [reg+disp32],reg`. Gating on the store address FAILs
  the run on the instrument while the log already names exactly those stores.
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
  Verify the emitted file with a python `repr()` of its printf lines — backslash counts survive repr
  and do NOT survive a bash-quoted grep pattern, so a shell-side check can flash "False" on correct
  bytes while repr shows them exact.
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

## The window, the memo, and what a poke may gate

- **`rc == 0` from the turn driver does not mean the round's segments are done.** The driver returns as
  soon as the round counter moves while the other factions' upkeep is still executing, so a gdb detach at
  that moment loses the LAST stores — they run after the detach and log nothing, and the read-back gate
  FAILs on the instrument with every other gate green. Telltale: the mismatched subject's `/proc` value is
  the model's answer computed from the CURRENT inputs. Before detaching, poll `/proc/<pid>/mem` for
  `cur_player` until it is back with the HUMAN faction (derive it from the mask global's low byte:
  `(mask & -mask).bit_length() - 1`) — every segment in between has logged by then.
- **A memoized field's gate reads its inputs AT the hit, not from the pre-run snapshot.** Where the site
  stores a value a callee computes from globals, print every input that callee reads in the same printf
  (expression arguments are free) and recompute from THOSE: a snapshot of a memo asserts when it was last
  recomputed, which the engine does not owe you.
- **Validate a model before spending an acceptance invocation on it.** Give the harness a `--predict` mode
  that reads live memory, prints the prediction table and exits without attaching gdb or pressing a key —
  seconds, not a run. When it disagrees with live cached values, sweep the plausible stale-input space
  (era, per-faction counters, percent globals) for an input state that EXPLAINS each mismatch: a mismatch
  an earlier state explains confirms BOTH the model and the cache law, and only a mismatch NO state
  explains is a model bug. Off-by-one answers usually mean a mistranslated line — re-read the
  pseudocode's variable lifetime (Ghidra reassigns pseudo-locals mid-function; see code-atlas.md) before
  blaming the engine.
- **A poke that ARMS the branch you also gate on discriminates nothing.** If forcing a value makes the
  branch fire, "the branch fired because condition C held" is self-fulfilled: gate the ARITHMETIC instead
  (the value the store wrote, recomputed from hit-time inputs), keep the poke minimal (`value + 1`, not
  `1 << 30`), print the pre-poke live value next to the poked one, and say in the report which gates the
  poke armed.

## A breakpoint at the pc a hardware watchpoint REPORTS is eaten by the watchpoint
A watchpoint reports `store + INSTRUCTION LENGTH`; a silent bp placed AT that same pc logs nothing
for the watched records (m99p1: 27 of 37 store read-backs vanished at 0x5aaef1 = 0x5aaeeb+6). Put
the read-back bp ONE instruction later and read the memory (`*(int *)($esi+0x94d7f8)`), not the
register that held the value. Also: a poke is evidence only if the CONSUMER reads it — prove the
value at the consumer site (m99p1: [0x94d6a4] poked -5, read back -5, live 0 at 0x4f3558).

## A /proc/pid/mem PEEK IS INVISIBLE to a hardware watchpoint (s155, m100mult1)
gdb decides whether to REPORT a trap by comparing the watched value against its OWN last snapshot, and
that snapshot only moves at a stop gdb reports. A poke written by another process through
`/proc/pid/mem` is invisible until something else changes the word: when the game later stores the
ORIGINAL value back, gdb sees "unchanged" and logs NOTHING. m100mult1: fac2, whose multiplier is 0,
logged 0 of its 4 rebuild stores while three other factions logged 4/4 — an instrument artifact, not a
game fact. Therefore: (1) put watchpoints on fields whose value actually changes in the window; (2) to
prove a writer ran on a stable-valued field, POKEd it and read the restore back from /proc — the
poke-undo IS the evidence, not the log; (3) never gate "no writer" on "zero events" for a field that
can be rewritten with the same value.


## Displacement census and offline /proc models (s156, M101)

- A store census that classifies "the watched displacement sits in the FIRST operand" counts
  `cmp DWORD PTR [ecx*4+0x94d700],0x0` as a store and silently inflates the site list (m101feed2
  G8 expected 2, got 4). Filter on the MNEMONIC too: only mov/add/sub/and/or/xor/adc/sbb/inc/dec/
  neg/shl/shr/rep write their first operand; cmp/test never do.
- Derive a table stride by walking the lea chain in PROGRAM ORDER and tracking which register each
  lea WRITES - a chain like `lea ebx,[edx+edx*4]` then `lea ebx,[edx+ebx*2]` is idx*5 then idx*11,
  not two independent multipliers. Getting it wrong (200/60 instead of 212/44) makes every record
  lookup land on the wrong row and turns a correct model into a mismatch (m101feed1 G2). Ghidra's
  printed `*0xd4 / *0x2c` was right there; my parse was the bug - check the bytes, then believe the
  pseudocode's scale.
- An OFFLINE model (read the inputs + the target from /proc, no gdb) is only coherent while nothing
  runs between the target's last recompute and the read. SMAC auto-advances rounds while the human
  turn is pending, and a value rebuilt in faction f's own segment LAGS an accumulator bumped later in
  that segment by one accrual - so a green offline gate can go red on the next read of the same box
  (m101feed3 6/8, then m101feed4 8/8 on the frozen box). Probe the round twice ~10 s apart BEFORE
  believing either verdict, and check the state can still satisfy your own gates (a sign-mixing gate
  stops discriminating once every value drifts positive).

- **gdb printf format strings pass VERBATIM to C printf**: `"...\n"` (ONE backslash) prints a
  newline, but `"...\\n"` (TWO backslashes — the shape a raw-string template gets if you write
  `\\n`) prints a LITERAL `\n`, so the whole event stream collapses into ONE unparsed line and a
  full census reads as zero events (m102hit1: 15 bps armed, 47 events emitted, parse found 0; the
  events themselves were all correct). One backslash in the format, and keep the comma between the
  format string and the printf arguments.
- **Group per-invocation events by the direction of the CALL bp**: a bp at the instruction AFTER
  `call X` (e.g. 0x520909) fires AFTER the callee's own events, so a rebuild's events PRECEDE its
  CALL line — group BACKWARD from the CALL. Forward grouping produced empty groups that failed
  every chain gate on perfect data (m102hit2 12/14, G3/G6 red, G4/G5/G7 green). Unwatched factions
  yield legitimately empty groups: skip them in chain gates, do not fail on them.
- **Count printf SPECS against ARGS before the run.** A format/args mismatch — including a stray
  `%%` in a gdb-script line that python never `%`-formats (TMPL blocks are `.replace`d, not formatted,
  so `%%d` there is a literal percent) — ABORTS the whole sourced script and DETACHES at the first
  hit, so the window collapses to the events before that breakpoint (m103d1/d2 both died this way
  after 2 useful events). Assert it in the harness when you build the script.
- **Calling a game function from gdb.** An inferior `call` is ABANDONED ("The program being debugged
  stopped while in a function called from GDB") as soon as ANY breakpoint hits inside the callee — the
  body still runs, so arm the store bps first and read the effect back from /proc (m103d3 got the
  rebuild, but the call line said done=0). A MANUAL frame (`set $esp = $esp - 8`, write the two words,
  `set $eip = func`) must put the RETURN ADDRESS at esp+0 and the ARG at esp+4 — cdecl order — and
  save/restore eax/ecx/edx around it (the callee clobbers them; edi/esi/ebp are pushed by the prologue);
  reversed words made param_1 = 0x520909 and SIGSEGVed terran.exe at 0x59ec34, which killed the box and
  left a winedbg that had to be cleared before the next relaunch (m103d4/d5).
