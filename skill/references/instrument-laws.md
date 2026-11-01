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
  printed `*0xd4 / *0x2c` was right there; my parse was the bug - check the bytes, then believe
  the pseudocode's scale.
- **A stride written in the registry is DECIMAL until proven otherwise, and an OBSERVED register is the arbiter.**
  A documented `f*8380` is 8,380 bytes (0x20BC), not hex 0x8380 (33,664): read as hex it samples every fourth
  record, and a per-faction table built that way is confidently wrong while looking well-formed ("this faction's
  word is 0xFFFFFFFF" was really a neighbouring structure). Derive the stride from the register actually used at
  the site (the `esi` steps logged at the gate) before tabulating anything per record, and make the parser SHOUT
  when a value is not a multiple of the assumed stride (`esi % STRIDE != 0`) — that one assertion is what catches
  it. A live snapshot can only contradict a registry row after its ADDRESS ARITHMETIC is verified.
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
- **gdb STARTUP/EXIT chatter is not protocol but must be whitelisted**: the debuginfod prompt block (This GDB supports / <https://...> / Enable debuginfod / Debuginfod has / To make this setting) prints BEFORE the sourced script first arms, and [Inferior 1 (process N) detached] prints after the last event — so a zero-unparsed gate FAILs on an instrument that armed and logged fine (m104w2 11/12, floors untouched). Set DEBUGINFOD_URLS= in the Popen env AND whitelist those prefixes plus [New LWP <pid> (a bare [New LWP] alternative never matches the banner with its pid in it).

## A read census that OVER-RUNS the file has no model

A read census that sums `size*count` in execution order and prints a cumulative `file_off` per site is only
valid if every executed site reads the SAME stream sequentially. Arm a superset of call sites and that
assumption dies: 190 sites executed 90, the load really ran (counts 67/18), and the sum came to **243,007
against a 242,539-byte file — over by 468 B**. The extras were three 160-B CRT reads (into 0x7cda1c,
0xbe8c10, 0xbefd3c) plus a 9-iteration per-entity loop of 6 x 4-B reads into heap (dest 0x3b7d7a8 ..
0x3c4b420, stride 0x224B8, the 0x59666d/0x5966c1 pair).

- **An over-run is a MODEL verdict, not a rounding error to shave.** It says the offset column is not a
  statement about the file at all; do not "find 468 bytes of double counting" and keep the map.
- **Filter by the FILE\*** before trusting any closure figure: capture the stream at the loader's entry
  (`set $savefile = *(unsigned int *)($esp+4)` at the loader's FIRST instruction — at a CALL SITE the same
  FILE is `[esp+0xc]`, one slot lower than the callee's entry, so a slot copied from the other shape makes
the condition permanently false and the run exits with 0 legs) and condition every reader bp on
  `*(unsigned int *)($esp+0xc) == $savefile`. Without it, a site that reads another file through the same
  wrapper counts into your map.
- Corollary: **a figure that closes to the byte is a claim about the ARMED SET**, not about the loader.
  Re-derive an inherited closure figure (even one at 99.94%) with the complete site set before quoting it
  as proof; un-armed sites are indistinguishable from unread bytes.
- **An over-run can also mean the model DOUBLE-COUNTS a real read** — file the extras as `unknown`, never as
  noise to discard. The "three 160-B CRT reads plus a 9-iteration per-entity loop" above were the very
  mechanism a later milestone was hunting: that loop IS the trailer's reader, and the same bytes are also
  consumed in bulk earlier in the load, which is exactly why the sum exceeded the file. Calling a site
  "pollution" is a claim about the file's content — do not make it from a sum that has already failed.
- **The FILE filter is necessary, not sufficient**: with it armed (savefile captured, 83 legs, 0 gdb errors,
  counts 68/19) the sum still over-ran by 144 B on a second, differently-sized save. Two files, two
  over-runs = the model, not the file.

## Identify bytes, don't count them: the poke-and-scan

"Does the loader consume THIS region of the file?" is answerable without any offset model, which is why it
survives what the census fails at:

1. Copy the file; plant a **unique** pattern (e.g. `0xCAFEBABE` in 10 dwords) in the region under test,
   changing nothing else — not the size, not the trailing dword. Assert the pattern occurs **0 times** in the
   original, so every hit in memory is yours. Keep it out of a field the format validates (a length or
   checksum): a refused load is a third valid outcome ("the region is VALIDATED") but it does not answer
   "is it consumed".
2. Load the copy, then scan every readable `/proc/<pid>/maps` region for the pattern (`os.pread` per region,
   skip >512 MB, count hits). Prove the load really ran by reading the live unit/base counts afterwards.
3. Three conclusive verdicts: hits > 0 = CONSUMED; hits == 0 with the load at the HUD and counts unchanged =
   NOT consumed; load refused = VALIDATED. Print the hit ADDRESSES — a hit names the destination, and the
   destination's owning structure names the reader via `index.csv` containment.
4. Corroborate against the census you already have: the hits should be destinations it logged, shifted by the
   field you poked (the trailer loop's hits sat at `dest - 8` because the census printed the 2nd word's
   address). Two independent instruments agreeing is the proof; either alone is a lead.

Harness template: `scripts/m112_trailer_poke.py` (no gdb, ~10 min, cheaper than a third census on a shape
that already failed).

## Extract a LAYOUT with anchors: many markers, one scan

The same poke answers "where does file offset X land?". Plant a UNIQUE 4-byte marker at each of N known
offsets, load once, and scan every readable region for all N values in ONE pass (`os.pread` per region, one
`find` per value). Each hit is an exact (offset -> destination) anchor, and anchors chain into the layout:
inside a section the mapping is 1:1 (equal offset deltas, equal destination deltas), and a section BOUNDARY is
where the destination JUMPS while the offset keeps stepping. Harness `scripts/m113_save_map.py --tag <t>
--relaunch --step 16384`: 20 markers gave 20/20 anchors on a .SAV, three slope-1 runs, the grid at 0x40a6660,
and two leg sizes corroborated TO THE BYTE from neighbouring anchors (176 B and 4,096 B) — a layout claim no
byte sum had been able to make.

- **Keep the marker count small and CONCENTRATED.** 60+ scattered pokes land in counts, pointers and length
  fields; the load then fails or parses garbage and every anchor means nothing. Make the harness refuse a
  dense sweep ("60+ markers is a mutilation, not a map") and refine with bands: `--band lo-hi[:step]`, e.g.
  four 2 KB bands around the boundaries already bracketed to 16 KB.
- **A MISSING marker is a finding, not a failed poke.** With present neighbours on both sides, an absent
  offset is a region the loader does not restore verbatim — a gated leg or a field rewritten after the copy.
  Bracket it with a finer band and report it; do not re-run the same step hoping it appears.
- **Boundaries are named by an anchor PAIR.** Report the last anchor of one run and the first of the next
  ("block A -> block B between 66,048 and 68,096, the documented 67,840 split inside it") so the next session
  narrows with one run instead of re-deriving the table.
- **A subset-sum over candidate legs is NOT a map.** Solving "which optional sections are live" by requiring
  the sizes to sum to the file admits a huge family of exact answers (181,769 decompositions of one
  242,539 B file, even after the map size constant was corrected) — an answer set that large cannot pick a
  layout. Only a content constraint or an anchor filters it; do not spend a run on the arithmetic.
- **Read the derived address LIVE before you arm on it, diff it, or publish it.** An anchor gives you a
  mapping constant; applying that constant to an offset in ANOTHER section is an assumption, not a
  measurement. The one-call check is: `os.pread(/proc/<pid>/mem, n, off + k)` and compare with the file's
  bytes at `off` — 0 differences means the constant holds locally, anything else means you are comparing two
  different sections and every "differing byte" you report is your own arithmetic. Do this BEFORE arming a
  watchpoint at a computed address (a clean zero-event run there is an instrument verdict that reads as "no
  writer"), and have the layout harness verify each anchor's neighbourhood automatically
  (`m113_save_map.local_1to1`, ±8 B) so a wrong destination cannot reach the report.

## A hot address band starves the driver — arm by relevance, not by address range

Band-based site selection is a convenience that fails silently. The MSVC CRT band 0x62b000-0x62d000 holds 31
sites calling the same four read wrappers as the loader; armed unconditioned, 0x62b8f0 and 0x62b935 fire
**8,277x each during STARTUP** — 25,957 stops in 12 minutes, ZERO loader-band hits, then the event stream
froze for 7 minutes with the load driver at 1 s CPU. That is the starvation shape, not a broken game.

- Before arming a band, count how often each site fires **outside** the mechanism you care about: a startup
  data-loader sharing the wrapper will drown a save-load census every time.
- Kill the starved run by pid and re-shape — it never recovers on its own; waiting it out only spends the
  attempt budget and leaves the box mid-run.
- Bound the damage the same way a store census does: prefer "the sites this mechanism calls" (a filtered
  band, or a FILE\*-conditioned superset) over "everything in this address window".

## Proving a read leg: destination content, not a size constant

- **Check the documented size list before claiming a constant does not exist.** A grep for the byte count
you measured (156) finds nothing while the loader pushes a NEAR MISS (152 = 156 - 4) that the format doc
already lists as an immediate leg — a negative claim built on one exact-value search is one subtraction
away from wrong. Grep the docs (`references/data-formats.md`, `SAVE_FORMAT.md`) for the value AND its
neighbours, then confirm the leg you found is the section you meant.
- **A leg is proved by WHERE it writes, not by how much it reads.** Read its destination from
`/proc/<pid>/mem` after the load and compare with the bytes you expect: the 152-B leg that looked like the
answer landed on `[9999,9999,0,0,2100,2600]`, i.e. a different section entirely. Size agreement is a
coincidence generator; content agreement is the proof.
- **Scan objdump for an immediate VALUE, not for its bytes.** Strip bracketed operands first
(`re.sub(r"\[[^\]]*\]","[]",asm)`) or every `[ebp-0x9c]` stack slot counts as the constant you are
hunting — 630 raw hits collapsed to 13 real ones for one 2-digit value, and only the survivors can
support "no code uses this size".
- **Compare across the format's corpus to separate structure from data.** N files of one format that share
bytes are saying those bytes are structure: nine saves shared their final 152 bytes exactly, with only the
trailing dword varying, so the block is a fixed trailer rather than game state — and because their SIZES
differed, its offset moves per file, so no hard-coded read leg can index it and any claim about it must be
a per-file, EOF-relative read.

## Is this bit ever SET? Scan the displacement, then check the OPERAND WIDTH

"This flag is always 0, so the branch never runs" is a claim about the whole image, and one grep either
supports it or destroys it. Scan every instruction that touches the displacement and bucket it by mnemonic:
`mov` (reads and whole-word stores), `or`/`and`/`xor` (bit surgery), `test`/`cmp` (readers), `lea` (address
arithmetic — not an access at all).

- **Width is part of the test, and a byte test is invisible to a dword-shaped search.** A gate that reads
  `test BYTE PTR [reg+disp],0x40` tests bit 6 of the LOW BYTE; a scan for `test DWORD PTR [...],0x40` or for
  `or [...],0x40` finds nothing and "proves" the flag dead. Match the displacement first, then read the
  operand size and the immediate actually used.
- **Do not confuse a high bit with the low one.** The same displacement carried 17 `or` sites setting
  0x200000 .. 0x80000000 and 0x2 — none of them touches 0x40. A flag word accumulates unrelated bits at
  different widths; bucket by the exact immediate, never by "an `or` exists here".
- **Zero setters means the bit can only arrive through a whole-word store.** Enumerate those `mov [disp],reg`
  sites and say so explicitly — "no immediate sets it; it is written only by whole-dword copies" is a much
  stronger and much more falsifiable statement than "it is never set".
- **The real setter is often a REGISTER op, invisible to a displacement grep.** `or al,0x40` / `and ah,0xbf` on a
  value later stored at the displacement never matches a scan for `or DWORD PTR [disp],imm`. Enumerate every
  register-level bit op whose result REACHES a store at that displacement, then read the store itself: the only
  such site here reloads the word into `eax` and masks it (`and eax,0xfc3fffff`) before writing, so the or'd bit
  never lands — the block TRANSLATES one bit into another (`source 0x800000 -> derived 0x40`) and parks the derived
  word in a global that no instruction moves back. "An `or` exists near this field" is neither a setter nor proof
  of one; the store's own source operand decides.
- **A bit no code sets can still arrive as DATA — check the format corpus.** The flag word lives in a block the
  loader restores 1:1, so a file carrying the bit would set it. Reading the field's offset in every save on disk
  (12 files x 8 records) is one loop, needs no box time, and is what upgrades "never observed set" into "cannot be
  set on this build and this format version". Do this before writing an inert-branch conclusion, and say which
  build/version it is scoped to.
- End-to-end harness for the whole question (tests, dword ORs, register ops, store masks, corpus):
  `scripts/m118_flag_never_set.py`.
- **An all-ones field is not a semantic value.** A live dword (and its neighbour) reading 0xFFFFFFFF next to
  zeros elsewhere has two readings: the flag is on, or the record was `-1`-filled/uninitialised. State the
  value, label the meaning INFERENCE, and decide it with a take/no-take observation — clear the bit and count
  hits at the branch TARGET — never by re-reading the value (the two-breakpoint shape that does this per subject:
  §Count BOTH sides of a branch).
- **A live snapshot can CONTRADICT the registry, so keep the claim and the observation separate.** "Bit N is 0
  for all 8 factions" is a measurement with a time and a state; a later read that shows it set for one faction
  refutes the sentence, not the world. Report both (the value, then which prior row it retracts) and leave the
  semantics open until the controlled poke runs.


## A "stride conflict" is usually ONE multiplication read in two pieces (s171, M119/M123)

`lea X,[v+v*2]; shl X,4` is v*48, not v*3 and not v*16 — the shl is the tail of the same multiply. Two rules:
(1) when you meet a claim of two conflicting strides for one array, count the SITES (52/52 here were x48) instead of
arguing from one listing line; (2) when one address appears as BOTH `[reg+disp]` and `[reg*4+disp]`, the *4 form is
usually the same field with the stride folded into the register — prove it by requiring the 2095-dword sequence
(`shl 6 / add / lea [v+X*2] / shl 4 / sub`, 24/24 sites here), because 2095 dwords = 8,380 B = the faction stride.
Third law, cheap and reusable: a global with readers and ZERO writers of any width (0x98adee, 7 `movsx`, 0 writes,
no neighbour-dword access) is LOAD-TIME data, not a gameplay counter — check the enclosing dwords before concluding.

## A harness exit code is a CLAIM: a negative result is still a result

A gate that encodes "the branch was reached and not taken" as a non-zero exit makes its own finding look like a
broken run — the next reader (or the same session, an hour later) treats a valid negative as a failed instrument and
either re-runs it or reports the milestone as blocked. Fix the exit vocabulary, not the verdict:

- `0` = **measured**. The site was reached; whether the branch was taken is the RESULT, reported in the verdict
  line (`taken`, `never taken`). A closed gate is a finding, not an error.
- `4` = the site was never reached → INCONCLUSIVE. Only this means "the run cannot decide anything".
- `5` = the driver wedged / issued no orders → **NO MEASUREMENT**. Distinguish this from `4` explicitly: a wedge
  produces zero events at every site, so reporting it as "the mechanism never ran" publishes the box's fault as a
  fact about the game.
- `8` = the box was left dirty (`TracerPid != 0`) after the run.

Corollary that applies to every harness: the verdict LINE must name which of these happened, and the parser must
read the driver's return code BEFORE interpreting a zero-event stream. One wedge that reads as "never reached"
costs an acceptance attempt and a wrong sentence in the registry.

## Count BOTH sides of a branch: the test site and the take site, per subject

A value read out of memory (a flag is set, a counter is 0) is a CORRELATION. Turning it into a causal claim costs
one window with two silent breakpoints, not two runs: one at the TEST instruction (print the tested operand AND the
subject register) and one at the TAKEN target (print the subject). Harness: `scripts/m117_gate_take.py`.

- Print the counts per SUBJECT (register / stride), never one total: the table is what shows which subjects reach
the branch and which take it, and a single total cannot distinguish "nobody reaches it" from "everybody reaches it
and nobody passes".
- Have the parser SHOUT when a printed subject value is not a multiple of the assumed stride. That assertion is what
surfaced a decimal-vs-hex stride error that a well-formed-looking table had hidden.
- Read the verdict the table earns: `tests > 0, takes == 0` = the gate is CLOSED on the measured state (a RESULT,
exit 0, printed as "never taken"); `takes` with the tested bit CLEAR = the reading is FALSIFIED, and it is reported
as falsified rather than re-interpreted; `tests == 0` = the site was never reached (exit 4, inconclusive).
- Print "reached N x per turn" next to the take count. It separates "this gate cannot fire" from "the code never
gets here", which are different findings and different next steps.
- A closed-on-this-state result is not yet an inert branch: prove the CONSTRUCTION too (does any site set it, does
any file in the format corpus carry it) before the word "inert" goes into the registry. Conversely an inert-by-
construction proof still owes the reachability number, or it cannot say how the branch would behave if it ever opened.

## An open item that names a CASE without naming its SWITCH is under-specified

A footing line like "chooser case 7" is not yet a question: the switch it indexes is unnamed, and no amount of
reading the nominally relevant function will find it. Locating the DISPATCH is the first deliverable, and it is
cheap — enumerate every `jmp DWORD PTR [reg*4+table]` in the image and keep those preceded by a bound test
(`cmp reg,0x7` / `ja`) — because the answer is usually that none of them sits in the address range the wording
implies.

- When that happens the valid close is the SEARCH NUMBERS, not an invented finding: "N jump tables scanned, M with a
  7-bound, none inside 0x…-0x…" plus the question that would disambiguate (which switch, which enum, which entry
  point). Record it in the registry so the next session starts from the scan instead of from the phrase.
- Never substitute a nearby answer for the missing one. "The closest switch I could find" published as the finding
  is worse than an open item with numbers: it retires the question with a wrong row.
- The same test applies to any open item phrased by VALUE alone ("the negative-queue producer"): if a scan for the
  literal value and for the obvious arithmetic both come back empty, the item is a shape question, and saying so
  with the two scans' results is the honest end state.

## Two doc budgets, one fix: archive the settled middle, keep the RULES live (s171)

`NEXT_PROMPT.md` (15.5k) and `NAMED.md` (250k) both hit their caps while still being the only place findings could be
recorded, and three "consolidations" in one session were just shaving bytes. The durable fix is a SPLIT, not a squeeze:
`docs/pick-archive.md` holds the milestone narrative + full trap text (the footing keeps 22 one-line RULES);
`docs/named-archive-m32-m84e.md` holds the settled blocks (the registry keeps the method + the current era). Both moves
must be verified line-by-line against the archive (0 missing here) and both files must point at each other, because a
future reader grep-ing one file must be told the other exists.

## A small state code is named by the STRINGS printed around its writers (s171, M124)

ds:0x926bd4 had 4 writes and 2 `== 1` readers and no obvious name until the format strings at the write sites were read
from the image: both 0x68ea94 and 0x68eacc are "Skipping upkeep synch", which made the value a phase code and made its
reader at 0x5aafe4 (the band-flag function) explain a previously-unexplained skip. Cheap and high-yield: for any small
enum global, resolve every string constant in the +/-10 instructions around each write before theorising about meaning.

## A literal-displacement grep misses the folded encoding - count BOTH before saying "no site reads X" (s171, M67 -> M127)

"Zero sites read plan byte +42" was wrong: 369 sites read `0x98adb2`, and **all** of them use `[reg*4+0x98adb2]`
(reg holds `tid*13`, so *4 = the 52-byte record stride) rather than `[reg+0x2a]`. The earlier search grepped the literal
displacement form, so a heavily-read field looked unread and a live-verified behaviour looked unsupported. Rule: for any
record field, grep the ABSOLUTE address of the field (base + stride + offset) AND the literal displacement, and report
both counts. Same family as the M116 stride trap: the encoding, not the syntax, decides.

## A switch is found by its TABLE, not by its `cmp .. ,0xN` (s171, M130)

"chooser case 7" looked unlocatable because I scanned for `cmp <reg>,0x7` immediately before a jump-table jump in the
chooser's own address range (0x5a6xxx-0x5aaxxx): 9 of 319 tables matched, none there. The real dispatch is in
`FUN_00546800` at 0x54eafc, keyed on the RETURN VALUE of `FUN_00542ea0` (`call` -> `cmp eax,0x7` -> `ja` -> `jmp
[eax*4+TABLE]`), i.e. the switch is in the CONSUMER of a helper, not in the "chooser" code. Rule: search all 319
`jmp DWORD PTR [reg*4+imm]` sites for the ones behind a bound check on the SAME register in the previous ~6
instructions, then read the table out of the PE to map every case; do not filter by the address range you expect.

## A decompiler's `arr[i*N]` is an ELEMENT index - multiply by the width before calling it a stride (s171, M137)

Ghidra printed `(&DAT_00927590)[param_1 * 0x167]` and it is tempting to name 0x167 (359) the record stride. The
disassembly shows the index folded arithmetically (lea [v+v*4] -> lea [v*9] -> shl 3 -> sub v -> shl 2), i.e.
`i*359*4` = **1436 bytes**, which is exactly the stride already known from M104 (0x927a9c+fac*1436). Always read the
index-building instructions and the shl/mul width before quoting a stride from decompiled C; a factor-of-4 error here
would have "discovered" a second record family that does not exist.

## Prove a STRUCT by base-register reuse, not by neighbouring offsets (s171, M164/M165)

Five displacements four bytes apart (`0x94d80c/10/14/18/1c`) looked like one struct and five fields equally. The
decidable test is (function, base-register) reuse: collect `[reg+disp]` pairs per function and require the SAME base to
reach SEVERAL of the candidates - 11 pairs reach all five here (so: one 20-byte struct), while 0x94d488 shares a base
with 0x94d55c in only one function (so: a separate field, despite adjacent ref counts). Also: a field with MANY readers
and ONE writer is an initialisation-time value (here a faction RANK, the writer an `dec ebx` loop) - degree asymmetry is
evidence, and reading the single writer tells you what the value means.

## A write-dominant field is a DERIVED CACHE, and a struct's writer sets reveal its parts (s171, M167/M168)

0x94d488 has 49 refs but 22 writes across NINE functions and a single comparison: that asymmetry says "recomputed by
many paths" (like base+0xd0 credit, M97), so it must not be gated on as authoritative state. Conversely, when every
member of a candidate struct has the same WRITE COUNT (6 each here), check the writer SETS, not the counts: the header
dword's writers (and its constants 0/1/-1 plus 7 tests) differed from the four payload dwords' five shared writers, so
the 20 bytes are a header + payload quad rather than five peers. Write counts hide structure; writer sets expose it.

## A "struct" filled from ONE byte is a bit-decoder (s171, M171)

Five dwords at 0x94d80c..0x94d81c looked like a header plus a payload quad, and the writer set confirmed the split - but
the writer is a DECODER: `[+0x10/+0x14/+0x18/+0x1c] = setne(al & 1/2/4/8)` and `[+0x0c] = 1 / -1 / 0` from `al & 0x10`
and `al & 0x20`, with `al & 0x40` also OR-ing 0x800000 into a DIFFERENT word. So the 20 bytes are one source byte's
bits, expanded. Read a struct writer's SOURCE before naming the members: `setne`/`shr`/`and` chains mean the fields are
booleans of a bitfield, and the field that receives an OR elsewhere is a side-effect, not a member.

## A bit-LEG census: four parse rules, each of which alone reports the wrong leg list

Deriving a pack/unpack bit mapping from an objdump window means pairing a TEST (the source bit) with a
write (the destination mask). Each of these shapes, missed, silently empties or shifts the leg list while
the harness still prints a clean result:

- **Accept a MEMORY-operand test as a source.** A packer samples a byte in the record, not a register:
  `test BYTE PTR [esi+0x94f4b0],0x20` is the 0x20 leg. A parser that only accepts `test reg,imm`, or only
  the DOCUMENTED width at one displacement, finds a single leg and reports success.
- **Resolve a mask REGISTER to its last `mov reg,imm`.** `test eax,ebx` / `or ecx,ebx` carry the bit in a
  register; pair each by the nearest preceding load (`mov ebx,0x40`). Skip this and every "distinct masks"
  figure collapses to one register name.
- **Normalize the two "bit 0" idioms.** `shr reg,N` + `and reg,1` and `and reg,0x80000000` + `neg/sbb/neg`
  both yield bit 0 of the same source and are ONE leg; unnormalized, bit 0 appears twice and a phantom
  bit 31 appears that no site writes.
- **Only count an `or`/`and` leg whose immediate is a SINGLE bit.** A bare `and eax,0x1` is a truncation,
  not a 31-bit clear — counting it as a destination adds a phantom leg and shifts every subsequent one.
- **A byte op's immediate sits at the BYTE's bit position, not at bit 0.** `or ah,0x8` sets 0x800 and
  `and ah,0x7f` clears 0x8000: shift the immediate left by 8 for `ah/ch/dh/bh` before unioning, or a
  whole census reports bits 0..7 for ops that live at bits 8..15 and the mask picture is silently wrong.
- **To name a store's SOURCE, walk back to the ULTIMATE definition**: skip modifiers
  (`and/or/xor/add/sub/shl/shr/inc/dec`) and keep going, stop at `mov/lea/movzx/pop/neg` or at a call that
  clobbers the register. Stopping at the first write reports `and edx,ecx` as the source and hides the
  read-modify-write: that one fix turned "27 plain assignments, zero bit-setters" into 23 register-level
  bit RMWs + 4 whole-value assignments (M190, `scripts/m188_m190_uses.py`).

Gate the result TWICE: the leg COUNT and the bit SET, both printed as tables, so a shifted leg is visible
instead of plausible. A gate that asserts only "the pack has legs" passes any parse, including one that
dropped half of them.

## A shared writer's argument TUPLE is per-site — enumerate the pushes at EVERY call

A generic tagged-record emitter takes `(name-ptr, size, payload)` and the name/size are NOT properties of
the helper: across nine call sites seven pass size `0x41`, two pass `0x1`, and one passes a register. A
finding that measures one site and says "the record is 0x41 bytes" is wrong at the sites that differ, and
the repair costs a doc-correction PR after the milestone has already merged.

- Scan `INS[i-8:i]` for the pushes before EACH `call`, print the distinct tuples as a table, and gate on the
  TABLE (counts per tuple). "9/9 pass 0x41" and "7 x 0x41, 2 x 0x1" are different facts and only one is
  true — assert the one you printed.
- The same test applies to any constant riding a shared helper: a `(dest, len)` read wrapper, a type id, a
  mode flag. The constant belongs to the CALL; the helper's body documents only the shape.

## Ghidra prints small offsets in DECIMAL and large ones in HEX — a pattern built one way matches nothing (s180)

- Ghidra prints an offset BELOW 0x10 without the prefix (`*in_ECX + 4`, `+ 8`) and 0x10 and above in HEX
  (`+ 0x30`, `+ 0x15c`). A pattern assembled with `str(off)` — decimal — therefore matched 0 C sites for
  every slot >= 0x10 and a correct claim read FAIL. Assemble the operand as an alternation,
  `(?:0x%x|%d)`, or normalize the C before matching.
- The same class of bug in the disassembly: a "within N of this site" test over `window(pc, pc+N)` is
  N **BYTES**, not N instructions. A 40-byte lookahead missed a dispatch 45 bytes away (the prologue that
  pushes a boolean is `and/neg/sbb/neg/push`) and printed "0 of 2". Count instructions, or size the window
  in bytes from the longest prologue you know is there, and print the gap you measured.
