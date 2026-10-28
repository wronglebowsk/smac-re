

Older sessions: `docs/sessions/sessions-115-116.md` (2 sessions). Read it only when a question reaches back before session ## Session 117.

## Session 117 (2026-10-28) — M75: the production sweep's MATCH SEMANTICS. ACCEPTANCE PASS (tag `m75sweep1`): the sweep marks EVERY valid UNMARKED designed record — the three bytes do NOT gate designed marking.

**Instrument.** `scripts/m75_sweep_replay.py`: implements FUN_00572800's loop from the
instruction bytes, predicts tid 194's marked set from live memory, reloads `m54b_clean.SAV`
(`m54a_load.py --relaunch`), enqueues 194 (`m57_ui_enqueue`), arms 4 hw watchpoints
(193/194/192/128), pokes storage 200, drives boundaries (early-stop when 193&194 carry
bit 2), compares prediction vs the stores. One real invocation:

    reload rc=0; PREDICTED sweep(194) marked set: [192, 193]
    boundary 0: rc=0 38s flags 193=0x41 194=0x41 192=0x01
    boundary 1: rc=0 71s flags 193=0x145 194=0x45 192=0x105
    events: 0x4efe67 tid194 0x45 | 0x5729de tid192 0x105 | 0x5729de tid193 0x145
    census diff: 192:0x01->0x105, 193:0x41->0x145, 194:0x41->0x45
    gates g1..g5 all True; newly_bit2=[192,193,194]; marked-untouched=[64,128,129,130,131]
    ACCEPTANCE m75sweep1: PASS (predicted=[192, 193] observed_sweep=[192, 193] tracer=0)

**RETRACTION (M74's sweep semantics).** s116 said the sweep marks records "whose
+0x24/+0x25/+0x26 match the produced unit's". FALSE for designed candidates: 192
(triple 00/02/00, tier-FAILING vs 194's 00/02/01 — tier25 rank[02]=03 > 194's byte 02)
WAS stored at 0x5729d5; 193 (matching triple) was stored; the marked designed
64/128/129/130/131 got NO store; alpha 0-13 got NO store. The sweep's live effect is
"mark every valid unmarked designed record" (the gate that discriminates is bit-2/validity,
not the bytes). The byte triple + tier tables + category gate are only reachable on the
alpha-candidate path (validator `0x5a6cd0(tid, produced_flag_byte)` then the three tier
tests); zero alpha candidates were marked this scenario, so that path stays UNTESTED.

**Fields (measured live, fresh save).** +0x24 selects the 144-byte row at `0x92ae80+(v*0x90)`
(same row M73's markup `C` byte `0x92ae81[+0x24*0x90]` and the build-base `==1` land test
read); the sweep's category gate compares those rows. `0x92b950[+0x24]` and `0x92fd18[+0x25/+0x26]`
are 16-byte-row tier tables, rank = row[0] (0x92b950: 00->01 01->02 02->04 03->05 04->06 05->08;
0x92fd18: 00->01 01->02 02->03 03->04 04->05 05->06); a tier test passes when candidate rank
(row[0], signed, >0 required) <= produced byte. Validator `0x5a6cd0(tid, shift)` = tech-table
record `[tid*0x14 + 0x92fdd4]` dw0 >= 0 and bit `shift` of ownership byte `0x985c1c[tech]`
(shift = produced record's +0x30 low byte; shift 0x41 here).

**Consequence for M73/M74.** At the FIRST designed production the sweep marks all remaining
unmarked designed records, so markup (`(C*P+50)/100`) is charged at most once per designed
record (only those already marked at load skip it from their first visit). Live: after the
run 192/193/194 carry bit 2; 192 ALSO still carries the 0x100 sweep marker.

**Open.** (a) why the marker clear `0x4ef398` (FUN_004ef380) cleared 193's 0x100 but not
192's (census 192=0x105 after; the clear writes +0x31, OUTSIDE the watched low WORD, so the
gdblog cannot show it — watch the HIGH byte or census-diff for 0x100 residue); (b) the
alpha-candidate path (validator+tiers) never fired — to exercise it: produce a designed unit
while an alpha designed... i.e. find a scenario where `0x5a6cd0(tid, flagbyte)` is true for
some tid<0x40 (needs `0x985c1c[tech]` bit `flagbyte&0x1f`... bit index >7 semantics unclear);
(c) the outer-loop block the sweep covers (edi start/tick: stores landed on 192/193 although
the entry computes edi=194*52 — the 64-record window arithmetic is NOT yet reconciled with
the instruction bytes); (d) other FUN_00572800 callers (shard_002 param_3=1, shard_012:20852,
shard_014:17826). NEXT pick: M76 — the 0x100 sweep marker: who clears it and for which
records (watch the +0x31 byte, census before/after a designed production).
Evidence: `evidence/m75sweep1.gdblog`, `evidence/m75sweep1_seq.jsonl`, traces `m75sweep1_r0..r1`.

## Session 118 (2026-10-28) — M76: WHO CLEARS THE 0x100 SWEEP MARKER, AND FOR WHICH RECORDS. ACCEPTANCE PASS (tag `m76marker1`).

**Instrument.** `scripts/m76_marker_clear.py --tag m76marker1`: 12 silent breakpoints (gate
`0x4efa5e`, production setter `0x4efe50`, sweep store `0x5729d5`, the clear `0x4ef398` printing
tid/owner/flags/RETURN-ADDRESS, the two selectors `0x4ef597` and `0x4f060f`, the upkeep inline
clear `0x52145e` + its test `0x521448`, the three marker setters `0x4f05bd`/`0x5a7d00`/`0x5a7f67`,
the whole-word codec stores `0x595f82/91/9c`), reloads `m54b_clean.SAV`, enqueues 194, drives
boundaries, then REPLAYS the observed stores onto the before-census and reads the 0x100 bit back.
One real invocation:

    reload rc=0; baseline 0x100-carriers: []; predicted sweep(194) marks: [192, 193]
    boundary 0: rc=0 36s  192=0x001 193=0x041 194=0x041  0x100-carriers=[]
    boundary 1: rc=0 69s  192=0x105 193=0x145 194=0x045  0x100-carriers=[192, 193]
    boundary 2: rc=0 121s 192=0x005 193=0x045 194=0x045  0x100-carriers=[]
    events: PRODSET 194 f=0x41 | SWEEP 192 f=0x1 | SWEEP 193 f=0x41 |
            CLEAR 192 owner=3 f=0x105 ret=0x4f062b | CLEAR 193 owner=3 f=0x145 ret=0x4f062b |
            PRODSET 194 f=0x45
    census diff: 192:0x001->0x005, 193:0x041->0x045, 194:0x041->0x045
    gates g1..g5 all True; cleared=[192,193] residue=[] marker_mismatch=[] word_mismatch=[]
    ACCEPTANCE m76marker1: PASS (clears=2 residue=[] tracer=0)

**WHO.** `0x4ef398 and BYTE PTR [ebx+0x98adb9],0xfe` is the FIRST statement of FUN_004ef380(owner,
tid) — ebx = tid*52 comes from `[ebp+0xc]*13<<2` (`0x4ef386-0x4ef392`), so the clear always lands
on the record PASSED IN. In this window the caller is the PRODUCTION function's own inline
selector: test `0x4f060f` (`test cl,1` / `test cl,4` / `and ecx,0x100` / `test cx,cx`), call
`0x4f0626`, return `0x4f062b`, owner = edi = 3. The OTHER selector FUN_004ef540 (test `0x4ef597`,
called only from `0x5a7d14`/`0x5a7f7b` inside FUN_005a7970) printed ZERO pass entries; the upkeep
inline clear (FUN_00521070 `and bh,0xfe` `0x521452` + `mov WORD PTR [edi],bx` `0x52145e`, which
also reaches FUN_004ef380 at `0x521479`) and the tech-path setters `0x5a7d00`/`0x5a7f67`
(`or BYTE [eax*4+0x98adb9],1`) printed nothing.

**FOR WHICH RECORDS.** Both selectors walk the same 128-slot window `{0..63} U {owner*64..+63}`
and call on `flags & 1 && flags & 4 && flags & 0x100`. Printed rows: 192 (0x105), 193 (0x145),
194 (0x45) — the two carriers called, 194 (no marker) did not: predicted == observed.

**WHEN.** LATER than the sweep, not in the same breath: the sweep marks at the FIRST production
(marked at boundary 1) and every carrier is clear by the next boundary. M75's "192 keeps the 0x100
marker" is RETRACTED as a snapshot artifact — the marker is transient. The clearing visit printed
no PRODSET before its CLEARs, so it reached the pass without executing `0x4efe50`.

**Open.** (a) which control path reaches `0x4f05e2` (gate bail `0x4efa63`? pay epilogue
`0x4efed8`?) and what the pass gate `(DAT_00920434 == 0) || ((bVar8 & DAT_00985b10) == 0)` is —
its else branch SETS the marker at `0x4f05bd` (0 events seen); (b) the upkeep inline clear and the
FUN_005a7970 sweep+clear pair never fired here — when do those passes run; (c) the alpha
validator/tier path (M75 open (a)) is still untested; (d) `0x595f82/91/9c` printed tid 324/325 with
`$esi/52` — esi there is NOT a type-record pointer, so those sites are outside the 256-record
array and were left out of the replay. NEXT pick: M77 — the control flow into the production
inline pass + `DAT_00920434`.
Evidence: `evidence/m76marker1.gdblog`, `evidence/m76marker1_seq.jsonl`, traces `m76marker1_r0..r2`.

## Session 119 (2026-10-28) — M77: WHAT REACHES the production marker-clear pass, and its GATE. ACCEPTANCE PASS (tag `m77gate1`).

Static (instruction bytes, `scratch/m574/text.txt`, window `4ef6d0-4f0c60`, reverse CFG
`scratch/m77_cfg.py`): `0x4f05e2` has ONE in-edge — the fall-through from `0x4f05e0`
(`xor esi,esi`), whose only in-edges are `je 0x4f05e0` at `0x4f05d2` and the fall-through from
`0x4f05de` (`test DWORD PTR ds:0x985abc,0x100000` → `je 0x4f0637`). Both come from the gate
block `0x4f0591-0x4f05de` (in-edges: `0x4f056c`/`0x4f0578`/`0x4f057f` branches + fall-through
`0x4f058e`), which first BAILS at `0x4f0599 je 0x4f0637` when `[ebp-0x20] == 0`. Operands:
`eax = DAT_00920434` (`0x4f05a5`), `al = low byte DAT_00985b10` (`0x4f05af`), `bl = low byte
[ebp-0x2c]` = `1 << owner` — `[ebp-0x2c]` is built at `0x4ef804-0x4ef815` (`mov esi,1; shl esi,cl`,
cl = ebx = `BYTE [base+4]`, base = `*DAT_008f0d60`). Admission: `(0x920434 == 0 || !(mask &
(1<<owner)))` → `0x4f05c6`; there, sweep iff `!(mask & bit)` (`0x4f05d2`) else iff
`0x985abc & 0x100000` (`0x4f05d4`); the ELSE (`0x920434 != 0 && bit set`) SETS the marker at
`0x4f05bd` and skips the sweep. The `[ebp-0x20]` writers are `0x4ef8c0` (1, queue-head special
codes 34-37), `0x4ef8c9`/`0x4efed1` (0) and `0x4efe6c` (`edx = 1` iff the record's flag bit 2 was
CLEAR before the `or al,4` store at `0x4efe60` — i.e. FIRST production of that record).

LIVE (`scripts/m77_gate_trace.py --tag m77gate1`: reload `m54b_clean.SAV`, enqueue 194 idx 0,
storage 200, 4 boundaries, 11 silent breakpoints): pre-attach `DAT_00920434=0`,
`DAT_00985b10=0x08`, `DAT_00985abc=0x003a7168` (bit20=1). 11 GATE visits (owners 1,2,3,5,6):
10 print `l20=0` and are followed by NOTHING (predicted NOENTRY, matched); the one with `l20=1`
(owner 3, record `10088 = 194*52`) took ROUTEB (`0x4f05d4`) → SWEEPIN (`0x4f05e0`) and handed
192 (flags 0x105) and 193 (0x145) to `0x4ef398`; both end the run WITHOUT 0x100. MARKSET 0
events while every visit printed `0x920434 == 0` — the else branch is DEAD in this state (this
is why M76 saw 0 events at `0x4f05bd`). Last `[ebp-0x20]` writer before the sweep printed
`L20FLAG edx=1 tid=194` = `0x4efe6c`, first-production route; `0x4ef8c0` printed ZERO events.
Census: b0 192=0x001 193=0x041 194=0x041; b1 192=0x105 193=0x145 194=0x045 (carriers);
b2/b3 192=0x005 193=0x045 (clear). g1-g8 True → PASS.

**RETRACTION (M76):** "the clear pass fired on a visit that printed NO production setter
(`0x4efe50`)" is a conditioned-breakpoint artifact — M76's PRODSET cond is
`*(int *)0x8f0d60 == $b`, so it cannot print for another base; the unconditional `0x4efe6c`
breakpoint prints the setter on the sweeping visit.

**Open.** (a) the census timing: the sweep visit's eligibility says FIRST production of 194, yet
carriers survive to the boundary-1 census and are gone by boundary 2 — either the marks are
re-applied later in the same turn by another FUN_00572800 caller (M76: FUN_004ef540 is called
only at `0x5a7d14`/`0x5a7f7b`, right after a sweep call) or the census races the pass; (b)
DAT_00920434 and DAT_00985b10 are unnamed (writers `0x50fe70/0x50fff5/0x510196/0x515ad8/
0x516f30/0x51f267/0x52280c/0x57ed04/0x598db9/0x5a09ad` and `0x4df82e/0x4df9a3/0x4df9ab/0x4e08ca/
0x512bf6 (imm 0x10)/0x512c0e/0x525eed/0x57f051/0x57f071/0x57f2da/0x57f2f8`); (c) the upkeep and
tech passes still never fired. NEXT pick: M78 — same-visit marks vs clears + the other
FUN_00572800 callers.
Evidence: `evidence/m77gate1.gdblog`, `evidence/m77gate1_seq.jsonl`, traces `m77gate1_r0..r3`.

## Session 120 (2026-10-28) — M78: SAME-VISIT marks vs clears, and who else calls FUN_00572800/FUN_004ef380. ACCEPTANCE PASS (tag `m78order3`).

`python3 scripts/m78_mark_clear.py --tag m78order3 --boundaries 4 --no-reload` (state from
`SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch`, round 50): enqueue 194 at
University Base idx 0, storage poked 200 read back 200, 12 silent breakpoints (FUNCIN 0x4ef6d0,
PRODFLAG 0x4efe60, L20FLAG 0x4efe6c, SWEEPCALL 0x572800, MARK 0x5729d5, GATE 0x4f0591, MARKSET
0x4f05bd, SWEEPIN 0x4f05e0, CLEAR 0x4ef398, UPKCLR 0x52145e, TECHSET 0x5a7d00/0x5a7f67) and the
per-boundary census APPENDED into the gdb log, so events and censuses share ONE ordered stream.
Baseline 192=0x001 193=0x041 194=0x041, carriers [].

**ORDERING (unit = VISIT, i.e. one entry of the production function).** visit 36: PRODFLAG tid=194
pre=0x41 -> L20FLAG edx=1 -> SWEEPCALL owner=3 tid=194 mode=0 ret=0x4efe83 -> MARK 192 (pre 0x001)
+ MARK 193 (pre 0x041) -> GATE l20=1 owner=3 rec=10088 (=194*52) -> SWEEPIN -> CLEAR 192 (pre 0x105)
+ CLEAR 193 (pre 0x145), all in the SAME visit. Cross-visit mark->clear pairs = [] and no later
caller re-marks, so H_ACROSS is RULED OUT and M77's paradox is a MEASUREMENT ARTIFACT: the census
that read 192=0x105 193=0x145 at boundary 1 sits BETWEEN the mark and the clear of visit 36 — the
driver reads /proc/pid/mem while the engine is stopped inside the production pass. g9 asserts that
every census which sees 0x100 is inside its tid's mark->clear pair; census 1 is the only one and it
is. Census replay exact at all 4 boundaries (carriers [] / [192,193] / [] / []), so the
instrumented writer set explains every 0x100 change; MARKSET 0, and 0x4ef5b3 / 0x52145e /
0x5a7d00 / 0x5a7f67 printed ZERO events (the upkeep and tech passes still never ran).

**CALLERS.** Static (instruction bytes): `call 0x572800` at 0x4394be (FUN_00438ad0), 0x4efe7e
(FUN_004ef6d0), 0x5741fe (FUN_00573a90), 0x5a7d0e + 0x5a7f75 (FUN_005a7970); `call 0x4ef380` at
0x4ef5ae (FUN_004ef540), 0x4f0626 (production inline), 0x521479 (FUN_00521070), 0x5a8568
(FUN_005a7970). Live here: SWEEPCALL rets {0x4efe83 x1 (tid 194), 0x574203 x4 = FUN_00573a90 on
array indices 324/325/385/387, other owners — those sweeps marked NOTHING}; CLEAR rets {0x4f062b
x2}. Every observed ret is a static call target (g2). Side fact: the production loop also fires
PRODFLAG/L20FLAG at indices 322/323, so it walks PAST the 256-record array the census covers.

**OPEN.** (a) what the >=256 indices are and what FUN_00573a90's sweep does for them; (b)
DAT_00920434 and DAT_00985b10 still unnamed (live 0 / 0x08 = owner 3; every GATE admitted, so the
0x4f05bd else-branch stayed dead); (c) when the upkeep/tech passes run at all. NEXT pick: M79 —
name those two globals and find what turns the MARKSET else-branch on.
Evidence: `evidence/m78order3.gdblog`, `evidence/m78order3_seq.jsonl`, traces `m78order3_r0..r3`;
failed instruments kept: `evidence/m78order1.gdblog` (census lines overwritten — a non-O_APPEND
log fd) and tag m78order2 (a quit prompt raised by an Escape on the bare map swallowed the enqueue).

## Session 121 (2026-10-28) — M79: NAME the two production-gate globals; what turns the 0x4f05bd MARKSET else-branch on. ACCEPTANCE PASS (tag `m79net5`).

`python3 scripts/m79_netgame_poke.py --tag m79net5 --boundaries 3` (reload `m54b_clean.SAV`, enqueue at University Base idx 0, storage poked 200 read back 200, 11 silent breakpoints incl. POKE 0x4f05a5 (`set var *(int *)0x920434 = 1`) and RESTORE 0x4f0637, census APPENDED into the gdb log): baseline 192=0x001 193=0x041 194=0x041 carriers []; **end census 192=0x105 193=0x145 194=0x145 carriers [192,193,194] — exactly the NETGAME-ON prediction**; census replay exact 3/3; SWEEPIN/CLEAR/UPKCLR **0 events**; MARKSET tid=194 pre=0x45 once; POKE pre=0 post=1 once (owner 3, rec=10088=194*52); end globals 0x920434=0 0x985b10=0x08 0x985b11=0xff. g1-g9 True -> PASS.

**THE GATE** (instruction bytes 0x4f0591-0x4f0637): bail at 0x4f0599 when `[ebp-0x20]==0`; `0x4f05a5 mov eax,ds:0x920434` / `0x4f05af mov al,ds:0x985b10`; admit iff netgame==0 OR the owner bit is absent from the mask; ELSE `0x4f05ba mov eax,[ebp-0x1c]` + `0x4f05bd or BYTE [eax+0x98adb9],0x1` (bit 0 of the flag WORD's high byte = 0x100) + `jmp 0x4f0637`, which SKIPS the clear pass. So MARKSET is netplay-only: solo netgame==0 kept it dead (m78order3 printed MARKSET 0). Poking the flag at the instruction that READS it (restored at the block's only convergence point) fires the else branch: MARKSET 0x100 on the produced record 194 and the sweep's 0x104 marks on 192/193 SURVIVE to the end census — read back from memory, not just from events.

**NAMES.** `0x920434` = **netgame/multiplayer flag** (0 = single player): FUN_0057ecf0 (game launch) sets 1 at entry and clears it at its tail; 7 of its 9 writers store straight after `call 0x4e25e0`; FUN_00528930 (netplay move) returns 0 when it is 0. `0x985b10` = **human/local-player mask**, byte keyed `1 << faction` (live 0x08 = player 3), sibling `0x985b11` = 0xff = all 8 player slots; FUN_004df630 writes `= 1 << p` and `= 0x985b11 & 0xfe`, FUN_00525e10 clears `1 << *(rec+0x788)`, FUN_0057ecf0 rebuilds it from the 412-byte player array at 0x91e494 (count 0x91e2d0, live 0). **Ruled out: `1 << cur_player`** — the gate visits printed cur_player (0x985dcc) = 1, 2, 5, 6 while the mask stayed 0x08.

**OPEN / PITFALLS.** (a) three instrument bugs fixed mid-milestone: the census parser must re-read `m2.group(1)` (m79net2 died on `int('BOUNDARY')`); the log tag alternation must be LONGEST-first or `MARK` swallows `MARKSET` and `POKE` swallows `POKEPOST` (m79net4 KeyError); PRODFLAG fires for EVERY record the pass walks (128/322/323/194 in m79net1), so attribute the sweep by its own predecessor. (b) the gate visit arrives in the boundary AFTER the marks: m79net2 (2 boundaries) caught the 0x104 marks but never reached 0x4f0591; a 4-boundary run dies on the 420 s foreground cap (m79net1, cut mid-window). (c) the chooser landed item 2 (`head 2 pending 1`) while 194 sat in the stale tail — and record 194's first-production visit happened anyway: the production pass WALKS the record array, the queue head is not what drives this gate. (d) 0x985b10's exact predicate (human mask vs players-with-a-controller) is inferred; the current-player reading is what the run ruled out. NEXT pick: M80 — what the record indices >= 256 are (128/322-325/385/387) and what FUN_00573a90's sweep does for them; the upkeep/tech passes still never fired.
Evidence: `evidence/m79net5.gdblog`, `evidence/m79net5_seq.jsonl`, traces `m79net5_r0..r2`; failed instruments kept `m79net1/2/4`.

## Session 122 (2026-10-28) — M80: THE RECORD ARRAY IS 8 FACTION BANDS OF 64; FUN_00573a90'S ARG 1 IS A FACTION; indices >= 256 ARE LIVE DESIGN SLOTS

The prompt opened with "M74", but M74 is already merged (#75, NAMED M74-RESOLVED, tag `m74flag3`,
s116): this session ran the cursor's pick M80 instead.

STATIC (bytes, `python3 scratch/m71/dis.py 573a90 573b60` / `5740e0 5741a0` / `5741a0 574210`):
FUN_00573a90 `0x573aa3 mov esi,[ebp+8]` = param_1 for the whole function; scan counter lives in
`[ebp-0x18]` and stops at 0x80 (`cmp ebx,0x80` 0x573fbd); record index = counter<0x40 ? counter :
`(counter&0x3f) + param_1<<6` (0x573bc7-0x573bec); `0x574167-0x574176` computes `(i+i%64)>>6` and
`cmp eax,esi` REJECTS unless band 0 or band == esi; `0x574178-0x57417e lea ecx,[edi+edi*2];
lea edx,[edi+ecx*4]; lea eax,[edx*4+0x98ad88]` = record 0x98ad88 + idx*52; 0x574142 writes the plan
byte; `0x5741d9-0x5741e1 push 0x20; lea edx,[ebx+0x98ad88]; call 0x64c5e0` copies 32 B INTO the
record; 0x5741e9 clears record+0x1f; 0x5741f0 `and BYTE [ebx+0x98adb8],0xfd`; `0x5741fe push 0;
push eax([ebp-0x4]); push esi; call 0x572800`, and FUN_00572800's own band base is
`param_1*0xd00` = faction*64*52 (shard_014.c:17568, FUN_00572800 head).

BASELINE census (`python3 scripts/m80_band_census.py --json`, fresh m54b_clean r50, pid 4073650):
b0 0..13 (Colony Pod..Unity Foil), b1 64, b2 128..131, b3 192..194 (ours), b4 256, b5 320..325,
b6 384..386 (387 EMPTY), b7 448..449 — every band contiguous from band_start; owner byte +0x2c is
0 for 320/321/322/323/324/325 and 0x40 only on 385.

ACCEPTANCE `m80band1` PASS on ONE invocation (`python3 scripts/m80_band_sweep.py`, 2 boundaries,
5 silent breakpoints): SW573 visits 2 facs [5] idx [(5,324),(5,325)] (ebx=16848=324*52); SWENTER 2
owner=5 tid=324/325 mode=0 ret=0x574203; CLR4 2 fac=5 ebxidx=324/325 **pre=0xc1** (bit 2 already
clear — the `and ~4` was a no-op here); MARKHIGH 0; census flag-diffs {324:(0,193), 325:(0,193)};
BOUNDARY 0 hi=256,320-323,384-386,448,449 → BOUNDARY 1 hi adds **324,325**, which now read
"Impact Squad" / "Impact Rover" flags 0xc1 — they were EMPTY at window start and are the next two
free slots after 323. F573IN printed ret=0x5749a7 x6, 0x574da9, 0x575424.

CONSEQUENCES. M78's "FUN_00573a90 on indices 324/325/385/387" was never a record index in esi —
esi is the FACTION (live 5) and 324/325 are the sweep's tid argument; a census limited to 0..255
never looked at factions 4-7, which is why 128/322/323 looked like anomalies (they are factions
2/5's slots). OPEN: who writes the record's `+0x30 = 0xc1` (bits 0/6/7) before 0x5741f0
(unattributed — no breakpoint there); what bits 6/7 mean; who calls FUN_00573a90 (ret
0x5749a7/0x574da9/0x575424); why the sweep's band-walk/mark path (guard `tid<0x40 || flags&4`)
never engages for a fresh record. NEXT pick: M81 — the +0x30 bits 6/7 and the record-creation
writer. Evidence: `evidence/m80band1.gdblog`, `_seq.jsonl`, `_census.json`.

## Session 123 (2026-10-28) — M81: THE SWEEP'S CREATE PATH RAN WITH +0x30 ALREADY WRITTEN; ACCEPTANCE FAILED, NOTHING MERGED

The prompt opened with "M74" again; M74 is merged (#75, NAMED M74-RESOLVED, m74flag3, s116) — the cursor's pick M81 ran.

BOX FIRST: the brief said BLOCKED (credit 0, minerals 0 < price 9). Ran the printed FIX (m54a_load --relaunch m54b_clean.SAV -> smac_play --turns 1 -> m57_ui_enqueue --base-index 0 --cell-item 2 --inserts 1) and it did NOT produce credit > 0. Static reason: base+0xd0 (the income accept_ready calls `credit`) has only TWO writers in the whole .text — 0x6310c6 and 0x631154 (`mov [obj+0xd0],param_1` inside the state blocks reached via `call [obj+0x90]` from 0x4bb6f7/0x4bc567/0x5cec2e, i.e. player-record init) — income is never recomputed per round. Live census: University Base income 0 rate(+0xcc) 0 while all 17 other bases read income 1-6. The accrual add 0x4ef7f6 `+0x40 += [eax+0xd0]` therefore adds 0; the sanctioned route stays the per-boundary storage poke 200 (m74flag3 pattern). Our queued Scout DID complete during the first window (pending 1 -> 0).

ACCEPTANCE m81write1/m81write1b FAIL (`python3 scripts/m81_flag_writer.py --tag m81write1 --boundaries 2`, then `--tag m81write1b --boundaries 3`; 4 hw watchpoints on the flag WORDS of slots 324-327 + silent bps 0x5741e1/0x5741f0/0x5741fe): run A armed only 2 hw (WATCH was [326,327]) and saw 0 events with all four slots EMPTY at baseline; run B armed 4 hw, baseline 324/325 = "Impact Squad"/"Impact Rover" flag 0xc1 (created between the runs — the M80 records are live state, a clean reload does NOT carry them), G1+G4 True, G2/G3/G5/G6 False, FLAGW []. Gates G1-G6 as designed, no floor weakened -> FAIL.

THE ONE REAL EVENT (evidence/m81write1b.gdblog): `TAG0 idx=($ebx/52) esi=6 ebx=20020 f30=0x81` — the create-path visit at 0x5741e1 fired for record 385 (20020/52 = faction 6's band) with the flag WORD ALREADY 0x81 BEFORE the 32 B copy. So the +0x30 bits are written before the sweep reaches 0x5741e1, consistent with M80's CLR4 pre=0xc1. Note the flag disagreement: census flags 324/325 0xc1 but the live sweep visit read 0x81 on 385 — do not assert one value for created records.

BLOCKER (instrument bug, why the logs are empty): the bp command printf's `%.20s` argument `*(char *)(rec+0)` makes gdb's own printf ERROR ("Cannot access memory at address 0x4c" — it treats the inferior pointer value as a host address), the error aborts the batch script at that line and DETACHES the inferior mid-window; the remaining boundaries ran uninstrumented (smac_play rc=0, gdb already gone). Fix for the next attempt: drop the name field from bp printfs (print idx/esi/ebx/f30 only) or use x/s outside commands. NEXT: re-run the same shape with the fixed printf; the writer of the created record's +0x30 is still unnamed, and the sweep visits factions' bands as their designs complete (385/fac6 seen this window, 324/325/fac5 in the gap).
Evidence: evidence/m81write1.gdblog, evidence/m81write1b.gdblog, traces m81write1_r0..1, m81write1b_r0..2.

## Session 124 (2026-10-28) — M81: THE CREATED RECORD'S +0x30 IS WRITTEN BY THE SWEEP ITSELF, BEFORE ITS OWN 32 B COPY; ACCEPTANCE PASS

The prompt opened with "M74" again; M74 is merged (#75). The cursor's pick — M81 re-run — ran.

BOX: brief BLOCKED (screen 'base' pane; minerals 0, credit 0). Escape cleared the pane (`scripts/m70_clear_dialog.py` -> READS hud). base+0xd0 income is still 0 for University Base (s123 finding), so the run uses its own per-boundary storage poke 200 (poked, read back 200).

INSTRUMENT (scripts/m81_flag_writer.py — 4 bugs fixed, NO gate touched): (1) the site bp printf carried `(char *)(rec+0)` as a `%.20s` arg -> gdb "Cannot access memory" aborts the batch script and DETACHES mid-window (that is why s123's logs looked empty); dropped. (2) `idx=@@I@@` was substituted INSIDE the format string, so gdb printed the literal text `($ebx/52)`; the LINE regex then never matched a TAG line, SWCOPY parsed as [] and G5 said False on a run that HAD the events — @@I@@ is now a printf ARGUMENT (`idx=%d`). (3) parse() branched on `m.group(1)`, which for a two-branch alternation is the WHOLE match, so a TAG line took the FLAGW branch -> `int(None)` TypeError after a good window; branch is now `m.group(2)`. (4) the arm check read the log once at 3 s and failed a run that armed fine; it now polls up to 30 s for "ARMED" plus 4 "Hardware watchpoint" lines.

ACCEPTANCE `m81write4` PASS on ONE invocation (`python3 scripts/m81_flag_writer.py --tag m81write4 --boundaries 3`, run right after a fresh `m54b_clean.SAV` reload so all four watched slots are EMPTY at baseline): G1 4 hw armed; G2 slots 324-327 empty; FLAGW [(324,0x595f8b,0x1),(324,0x57412c,0x41),(324,0x574133,0xc1),(325,0x595f8b,0x1),(325,0x57412c,0x41),(325,0x574133,0xc1)]; SWCOPY (324, esi 5, f30 0xc1),(325, esi 5, f30 0xc1); store pcs 0x595f8b/0x57412c/0x574133 all OUTSIDE {0x5741e1,0x5741f0,0x5741fe,0x572800}; gates G1-G6 all True -> PASS. Read-back from /proc/pid/mem after the window: 324 "Impact Squad" flag 0xc1, 325 "Impact Rover" 0xc1, 326/327 still empty. (m81write2 and m81write3 ran the same window and logged the same 6 FLAGW + 6 TAG events; they failed only on the parser bugs.)

THE ANSWER (a watchpoint reports the pc AFTER the store, so the store is the preceding instruction): 0x595f8b <- `0x595f82 mov WORD PTR [esi+0x98adb8],0x1` inside FUN_00595b10, which the sweep calls at `0x5740f7` with its own six params -> the record's flags WORD is RESET to bit 0 first. Then in the same visit FUN_00573a90 ORs: `0x574125 or BYTE PTR [ebx+0x98adb8],0x40` (bit 6) iff the local `[ebp-0xc]` (written 0x573e9f from max(edi, movsx(al)) at 0x573e92-0x573e9a) is != 0; `0x57412c or BYTE PTR [ebx+0x98adb8],0x80` (bit 7) UNCONDITIONALLY on that path (the `je 0x57412c` at 0x574123 lands on it). Bit 2's ORs did NOT run this window — the value went 0x1 -> 0x41, never 0x45 (`0x574107` needs eax == -2; `0x574117` needs `DWORD [0x985aec] > 1`). All three stores precede the 32 B copy at 0x5741e1, which is exactly why M80 read CLR4 pre=0xc1 and s123 read 0x81 pre-copy (0x81 = bit 7 set, bit 6 clear -> [ebp-0xc] was 0 for that record). ALSO NAMED: `0x595f91 mov WORD PTR [esi+0x98adb8],0x105` and `0x595f9c ...0x115` in the same FUN_00595b10 — the 0x100 marker bit is an INIT-time possibility, not only the 0x5729d5 mark path. Callers of 0x595b10: 0x4392fe, 0x5740f7, 0x57a021.

OPEN: what bits 6/7 MEAN (bit 7 is set unconditionally by the sweep on every record it (re)init, yet ours 192/193/194 read 0x105/0x145 with bit 7 CLEAR, so bit 7 is not the M78 marker); why [ebp-0xc] != 0 for 324/325 and == 0 for s123's record 385; who calls FUN_00573a90 (ret 0x5749a7 x6 / 0x574da9 / 0x575424); what global 0x985aec is; the upkeep/tech passes 0x52145e/0x5a7d00/0x5a7f67 (ZERO events ever); the alpha path 0x5a6cd0. NEXT pick M82: census +0x30 across all 8 bands, then ONE controlled poke of bit 7 on record 194 and re-read the price gate at 0x4efa5e. Evidence: evidence/m81write4.gdblog (+ m81write2/3), traces m81write4_r0..2.

## Session 125 (2026-10-28) — M82: BITS 6/7 OF THE TYPE-RECORD FLAG WORD HAVE NO TESTER; THE LIVE POKE TEST DID NOT RUN (acceptance FAIL, nothing merged)

CONCURRENT SESSION: session 126 ran the same prompt in the SAME worktree while I was running
(`evidence/m82census_s126.txt` 11:49, commit 989db9b "acceptance m82bit7b in flight" 11:53).
The box is ONE Wine process, so the third window (m82bit7c, armed 11:56) ran with another agent
able to attach/poke it.

STATIC (bytes; `grep -n 98adb8 scratch/m574/text.txt` = 168 sites, `python3 scratch/m71/dis.py
577c60 577cc0`): every `test BYTE PTR [...0x98adb8],imm` uses 0x1/0x4/0x8/0x10 — NO test of bit 6
(0x40) or bit 7 (0x80) in the absolute form, and no pointer-form `test BYTE PTR [reg+0x30/0x31],
0x40/0x80` either (both shapes grepped). The only bit-7-specific instruction is the CLEARER
`and BYTE PTR [eax*4+0x98adb8],0x7f` at 0x577ca8 (followed by `call 0x43f470` with ecx 0x71df20).
The markup test is bit 2 ONLY (`test BYTE PTR [ecx+0x98adb8],0x4`, 0x5ac99c) and B comes only from
0x5ac950, so the gate's `edi` cannot depend on bits 6/7. M74's live row (f30=0x41 — bit 6 SET —
with edi 45 = markup ON, evidence/m74flag2.gdblog) already falsifies "bit 6 = markup off".

CENSUS (`python3 scripts/m82_bit7_poke.py` PART 1, 512 slots read at once, 11:47): nonempty 34;
band0 0-13 = 0x1; 64 = 5; 128-131 = 5; 192 = 1, 193/194 = 0x41; 256 = 5; 320-323 = 5, 324/325 =
0xc1; 384/385 = 1, 386 = 0xc1; 448 = 5, 449 = 0x1c5. bit6 carriers [193,194,324,325,386,449],
bit7 [324,325,386,449], bit2 [64,128-131,256,320-323,448,449]. THE CENSUS MOVES: the 12:06 re-read
reads 385 = 0x81, 386 = 0x1, a NEW 387 = 0xc1, bit6 [193,194,324,325,387,449], bit7
[324,325,385,387,449], 194 = 0x45 — the sweep re-inits and re-marks faction records between
rounds, so a carrier list is a snapshot, not a property of the record.

ACCEPTANCE m82bit7a/b/c FAIL (`python3 scripts/m82_bit7_poke.py --tag m82bit7X`, 3 boundaries, 4
base-conditioned silent bps 0x4efa4b/0x4efa52/0x4efa5e/0x4efa63). a: died at 200 s inside the
m70_clear_dialog step — a concurrent veilbrowser Chrome window (pid 4179644 "PeopleSearchNow Opt
Out", 1280x800) was stacked OVER the Wine window at 0,0, so `xwd -root` cropped to 800x600:0:0
OCR'd the BROWSER and every screen read hung (session_brief and m65_screen also printed nothing in
60 s); fixed with `DISPLAY=:99 xdotool windowraise 0x400004`. b: armed and printed `ARMED
base=0x95da10 head=2 pending=1 storage=20` then `GATE id=2 storage=20 edi=9 f30=0x1` — the UI
chooser (`m57_ui_enqueue --cell-item 194`) landed cell 2 again, so the gate never visited 194; cut
at the 420 s foreground cap. c: head set by a controlled poke (+0x50 = 194, +0x4c = 1, read back
head 194 pending 1), flag 194 0x45 -> 0x41, storage 20, `ARMED ... head=194 pending=1 storage=20`,
then ZERO GATE/BAIL rows in 10 min (trace_m82bit7c_r0 is 0 bytes — the first smac_play never wrote
a look; a NETFLASH dialog stack was up at arm time).

OPEN / NEXT (M83): the same three-window test on a QUIET box — no concurrent session, Wine window
raised, dialogs cleared, queue head poked — W1 (bit2 off, bit7 off) -> edi, poke ONLY bit 7 -> W2,
W3 bit2 ON as the control that the instrument can see a markup switch; the bytes predict edi
unchanged. Still open: why `[ebp-0xc]` != 0 for 324/325 and == 0 for 385; who calls FUN_00573a90;
what re-inits 385/386/387 between rounds.
Evidence: evidence/m82bit7b.gdblog, evidence/m82bit7c.gdblog, evidence/m82census_s126.txt (s126's
copy of the same census), traces trace_m82bit7b_r0..r2, trace_m82bit7c_r0.

## Session 127 (2026-10-28) — M82: BIT 7 OF THE TYPE FLAG WORD DOES NOT TOUCH THE PRICE GATE; ACCEPTANCE PASS (tag `m82bit7d`)

The prompt opened with \"M74\" again; M74 is merged (#75). The cursor's pick M82 ran. s125/s126's
live test never completed: their m82bit7c armed (head 194 pending 1 storage 20) but terran.exe died
into a Wine \"serious problem\" dialog (stuck `winedbg --auto 124 20`, zero gate rows). Box fix:
killed winedbg by PID, `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` (twice
\"no window after relaunch\", third attempt after the winedbg kill reached HUD ~36 s).

ACCEPTANCE `m82bit7d` PASS on ONE invocation (`python3 scripts/m82_bit7_poke.py --tag m82bit7d`,
3 boundaries, 4 silent base-conditioned bps 0x4efa4b/52/5e/63, storage poked 20 read back 20 every
boundary): baseline census `CENSUS 512 slots: nonempty 32 ... bit6 [193, 194, 386, 449] bit7 [386,
449] bit2 [64, 128, 129, 130, 131, 194, 256, 320, 321, 322, 323, 448, 449]`; queue poke head 194
pending 1 slots [194, 0, 0]; setup flag 194 0x41 -> 0x41. W1 flag 0x41: GATE+BAIL id=194 storage=20
**edi=45** f30=0x41 (t=53s rows=5); POKE bit7 only: 0x41 -> 0xc1 changed=[128], read back from
/proc/pid/mem; W2 flag 0xc1: GATE+BAIL **edi=45** (t=91s rows=4); CONTROL bit7 off + bit2 on ->
0x45; W3: GATE+BAIL **edi=27** (t=127s rows=4) — the instrument demonstrably sees the markup switch.
`edi W1=45 W2=45 W3 control=27 -> VERDICT bit7 does NOT gate the price`; gates G1..G7 all True ->
PASS. After census: bit6 [193, 194, 324, 325, 386, 449] bit7 [324, 325, 386, 449] flag(194)=0x45
(bit7 back off; 324/325 re-created mid-window, the s124 reload behavior).

WHY THE SHAPE DISCRIMINATES: W2 differs from W1 by exactly one bit (G4 proves it) and W3 differs
from W1 in a bit the gate DOES test (edi 45 vs 27 = markup on vs off, M73/M74). Bit 7 set moved
nothing. Census + static agree: bit 7 lives only on sweep-created band-6/7 records (386/449; 324/325
band 5 when created live) — records that went through 0x57412c — and never on ours (192/193/194).
Static enumeration of all 168 flag-WORD sites: ORs 0x4 (0x4eed18, 0x573fed, 0x574107/117), 0x8
(0x573499, 0x573a81), 0x10/0x20 (0x531747/0x531782), 0x40 (0x574125), 0x80 (0x57412c), 0x104
(0x5729d5); ANDs 0xfe (0x4eed2b, 0x5727ed), 0xfd (0x5741f0), **0x7f (0x577ca8 — the ONLY bit-7
clearer**, inside FUN_00577280, shard_014.c:19576: validate test bit 0, `&4` markup test, a value
`(+0x30<<8|high)+0x19 * 0x34`-style compared > 0x3f, sets 0x200 when bit 3 set, then clears bit 3
and bit 7); NO `test` of bit 6/0x40 anywhere.
OPEN: what bit 5 (0x20 @ 0x531782) means; who clears bit 6; who calls FUN_00573a90/FUN_00577280;
`[ebp-0xc]` != 0 for 324/325 vs 0 for 385; global 0x985aec; upkeep/tech passes 0x52145e/0x5a7d00/
0x5a7f67 (ZERO events ever); alpha 0x5a6cd0. NEXT pick: the 0x4194b3 handler / widget message 0x4d00,
or bit 5 + FUN_00577280's identity.
Evidence: evidence/m82bit7d.gdblog (6 gate rows), traces trace_m82bit7d_r0..r2,
scratch/m82bit7d.out; failed instruments kept m82bit7a/b/c.

## Session 129 (2026-10-28) - M84: WHAT MAKES 0x496ad0 RETURN +9999 (static, bytes); ACCEPTANCE m84canc1 FAIL - the cancel statement runs but the sentinel never fires

The prompt opened with "M74" again; M74 is merged (#75). M83 is unmerged (m83cw2 FAIL, branch
milestone/m83), so the ledger's pick M84 ran on milestone/m84 from main 7a69b20.

STATIC (instruction bytes): 0x496ad0 (size 3310) picks its return value at 0x497680-0x4976ff -
0x497683 `cmp DWORD [ecx+0xa774],-1` (ecx = `[ebp-0x10]` = the 24 KB buffer the caller passes at
0x418601 `lea edx,[ebp-0x5e2c]`); if -1 and 0x49768f `cmp [edx+0xa778],0` is zero -> eax =
0xffffd8f1 = +9999 (0x4976ce); if -1 and result != 0 -> eax = 0 (0x497698); if the field != -1 ->
eax = the pump return (0x497704 ff15 0x401940, negated when 0x495480's bit 0x20 is clear). The
field is written -1 in exactly TWO places in .text: **0x496a43** (inside FUN_00496950, the dialog's
message handler: `mov [eax+0xa774],-1` right after `mov [ecx+0xa778],0` - handler case 7 = CANCEL:
result 0 + armed) and 0x495541 (inside FUN_004954e0, the dialog's own setup, called once from
0x496ad0). Handler FUN_00496950 (shard_009.c:14701) cases 0/2/5 `return` when the field is already
-1; 1/3/4/6/8 set result 2/3/4/6/7. So +9999 = THE DIALOG-CANCEL SENTINEL: cancel arms the field,
the next pump return becomes +9999, and the caller's 0x41861b/0x4186d2 `cmp edi,0xffffd8f1` is what
gates the 0x270f block (M83). The SAME +0xa774 offset is the chooser's guard: m57_ui_enqueue.py
reads `0x6A9E9C + 0xa774` as the chooser cell index, so the field is one UI-object convention, not
production-specific.

ACCEPTANCE FAIL (`python3 scripts/m84_cancel_sentinel.py --tag m84canc1 --escape --no-ok`, ONE
invocation, 3 silent bps 0x41860f/0x496a43/0x497683 + M83's 0x418d7d/0x577280): ARMED ptr=0x95ef70
fac=3 pend=0 head=2; enqueue rc=0 stopped with the chooser open (guard cell index 3, pending 1);
Escape rc=0 closed it. events SENT 1 (edi=2), ARM 2 (one is the ARMED line; the real ARM printed
**buf=0** + gdb "Cannot access memory at address 0xa774" - ecx was 0 at 0x496a43), GATE 1
(buf=0x6a9e9c cancel=3 result=5), BRANCH 0, ENTRY 0 -> G1 True, G2-G7 False -> FAIL. So the
cancel-arming STATEMENT does execute during a chooser session, but the buffer instance seen at the
return gate held cancel=3 (a cell index, not -1) and the pump returned 2, not -9999.

OPEN / NEXT (M84b): the ARM breakpoint's ecx is not the buffer there (register semantics, the trap
says so) - take the buffer address from the caller's own push at 0x418601-0x41860a (bp at 0x41860a
reads [esp+0xc]) and re-run the same 5-bp shape with events ORDERED by time; the claim to falsify
is "Escape on the chooser routes through handler case 7 (0x496a43) and the next pump return is
+9999". Also open: which widget message code reaches FUN_00496950 case 7 (no direct `call` to
0x496950 exists in .text - it is reached through a widget handler table); FUN_004954e0's -1 write
at 0x495541 (setup-time arm?); who owns 0x6a9e9c.
Evidence: evidence/m84canc1.gdblog, scratch/m84canc1.gdb, scratch/m84_tmpl.py (m83's script, the
shape this reused). No new evidence dir files beyond the log (budget 27.5 MB, gate FAILs at 30).

## Session 130 (2026-10-28) — M84b: THE CANCEL SENTINEL IS LIVE (Escape -> arm -> -9999); ACCEPTANCE m84canc2 FAIL ON THE 0x270f LEG

s129's M84 sat unpushed (no PR): this session first ran `milestone.py submit` for it (PR #84; acceptance FAIL -> merge nothing), then ran the pick M84b on milestone/m84b from main 7a69b20, carrying the m84 footing forward (`git checkout milestone/m84 -- NEXT_PROMPT.md SESSION_NOTES.md NAMED.md scripts/m84_cancel_sentinel.py scripts/m57_ui_enqueue.py evidence/m84canc1.gdblog`) — an unmerged branch is the only place that footing lives.

INSTRUMENT BUGS FOUND FROM BYTES BEFORE MEASURING (all three were s129's, not the game's): B1 0x496a40 `mov eax,[ebp-0x4]`, 0x496a43 `mov [eax+0xa774],-1` — the object is in EAX; m84canc1 printed $ecx (0), gdb faulted on 0xa774, its commands block aborted and gdb DETACHED, so that run died at the ARM. B2 0x496af1 `mov [ebp-0x10],ecx` + 0x497680 `mov ecx,[ebp-0x10]` — the guard field lives on the thiscall chooser_sub the caller loads at 0x418604 `lea ecx,[ebx+0xa1c]` = 0x6a9e9c, NOT the 24 KB `[ebp-0x5e2c]` buffer pushed at 0x418601 (live CALL: buf=0xbe3984, a stack address). B3 the sentinel is NEGATIVE: printf %d prints -9999, so m84canc1's `edi == 9999` gate could never pass; every sentinel read is now the unsigned 0xffffd8f1.

ACCEPTANCE m84canc2 FAIL (`python3 scripts/m84_cancel_sentinel.py --tag m84canc2 --escape --no-ok`, ONE invocation, 6 silent bps 0x41860a/0x41860f/0x496a43/0x497683/0x418d7d/0x577280, events printed in log order; `python3 scratch/m84b_selftest.py` shows the shape discriminates — positive ALL, 6 negatives each fail >= 1 gate). Box was BLOCKED (screen 'base' -> one Escape -> hud; then its printed FIX `m57_ui_enqueue.py --base-index 18 --cell-item 2 --inserts 1` made it READY, pending 1). ORDERED: CALL obj=0x6a9e9c cancel=3 mode=0 slot=1 -> GATE cancel=3 mode=5 -> SENT edi=2 -> CALL obj=0x6a9e9c cancel=3 mode=5 slot=3 -> ARM obj=0x6a9e9c pre=3 mode=0 (the Escape; a real transition) -> GATE cancel=0xffffffff mode=0 -> SENT edi=-9999 edi_hex=0xffffd8f1. G1/G2/G3/G8 True; BRANCH 0, ENTRY 0 -> G4-G7 False -> FAIL, merge nothing.

THE FAILED LEG IS THE FINDING (bytes, not instrument): 0x41861b `cmp edi,0xffffd8f1`/`jne 0x41864c` — on -9999 the loop 0x418623-0x41863f restores the ten queue slots into base+0x50..+0x78 and 0x418649 restores pending at base+0x4c from [ebp-0x20]; 0x4186d2 `cmp edi,0xffffd8f1`/`jle 0x419967` then leaves via 0x419967 (`push 1; mov [ebx+0x3ff5c],0; call 0x416080`). RETRACT s129's "0x41861b/0x4186d2 gate the 0x270f block": the ONLY branch to 0x418d7d is 0x4187be `cmp edi,0x270f`/`je`, i.e. POSITIVE +9999, reached on the mode 5/7 paths (0x4187a2/0x4187ad) only when [ebp+0x8] != 0. So 0x577280 (sole bit-7 clearer 0x577ca8) runs on a +9999 chooser result, not on cancel. OPEN: what puts 9999 in the chooser item list / makes 0x496ad0 return +9999.
Evidence: evidence/m84canc2.gdblog, scratch/m84canc2.gdb, scratch/m84b_selftest.py (evidence 27.5 MB).

## Session 131 (2026-10-28) — M84c: THE MODAL IS A 3-VALUE CHOOSER; +9999 IS A ROW KEY NO CODE INSERTS (acceptance m84cprobe1 FAIL)

Prompt said M74 (merged #75 long ago); the repo pick was **M84c** — what makes 0x496ad0 return POSITIVE +9999 = 0x270f, the only value that enters 0x418d7d and thunks 0x577280. Branch milestone/m84c from main 7a69b20, carrying s128-s130 footing (`git checkout milestone/m84b -- NEXT_PROMPT.md SESSION_NOTES.md NAMED.md scripts/m84_cancel_sentinel.py evidence/m84canc[12].gdblog`). PITFALL: `milestone.py start` resets the tree to main, so the carried docs AND SESSION_CURSOR.md must be re-written AFTER it (mine reverted to s127's M82 line).

STATIC (instruction bytes, scratch/m71/dis.py windows): the pump 0x497704 `mov ecx,[obj+0xa774]; push ecx; add ecx,0xa780; call 0x4026b0` = SEEK the list at obj+0xa780 (0x4026b0: index > [c+0x10]-1 -> return 0; cursor=[c+8]; walk `node=[cursor+0xc]`; [c+0x14]=index), then 0x497725 `call 0x495480; and eax,0x20` — bit SET -> 0x49773a `call 0x401940` (0x401940: `[c+8]==0 -> 0` else **return [[c+0xc]+4]**) -> 0x4977ab returns eax; bit CLEAR -> 0x497777 same call then `neg eax`. So the modal's THREE value sources are: -9999 (armed, mode 0), 0 (armed, mode != 0), and +/- the +4 word (the KEY) of the seeked node. Caller: 0x41860f `mov edi,eax`, 0x418616 snapshots it to [ebp-0x10], 0x418794/0x4187a2 reload it, 0x4187be `cmp edi,0x270f`. n_callers: 0x496ad0 = 1 (0x41860a only), FUN_004954e0 = 1, and the ONLY writers of that list are 4 functions calling FUN_0042ee20 — 0x4954e0 (2 sites, key = the setup loop var), 0x42e4d0/0x42ef40 (`(&DAT_00997120,0,4,0)`), 0x4b0a80; NO caller passes 9999.

ACCEPTANCE FAIL (`python3 scripts/m84c_item_pump.py --tag m84cprobe1`, ONE invocation, 8 silent bps 0x41860a/0x42ee20/0x497704/0x4977ab/0x41860f/0x4187be/0x418d7d/0x577280): PUMP obj=0x6a9e9c idx=3 count=13 cur plus4=42 -> VAL eax=2 -> SENT 2 -> CHK edi=2 -> CALL mode=5 slot=3 -> PUMP cur plus4=2 -> VAL 2 -> SENT 2 -> CHK 2. gates G1 True G2 True **G3 False** G4 True **G5 False** G6 True G7 True; counts PUMP 2 NODE 2 VAL 2 SENT 2 INS-on-chooser-list 13 CHK 2 BRANCH 0 ENTRY 0; node+4 [2, 42]; inserted words [0,1,2,3,6,16,17,18,32,34,38,39,41,42,161,192,193,194]. G3 is MY INSTRUMENT: the NODE print sits at 0x497704, BEFORE the seek at 0x497717, so it prints the PREVIOUS cursor (fix: print at 0x49771c). G5 is the finding: the list keys are dialog category ids 0..0x2a — no 9999 item exists, so 0x418d7d/0x577280 is unreachable from the build chooser. merge nothing. OPEN: 0x4a99e0 `cmp [ebp+0x8],0x270f; jle` then `sub ecx,0x270f` + stride-0xb4c table at 0x888514 is where keys > 9999 mean something else — the next lead. Evidence: evidence/m84cprobe1.gdblog (27.5 MB).

## Session 132 (2026-10-28) — M84d: WHO CALLS 0x4a99e0 WITH A KEY > 9999 — NOT THE PRODUCTION PATH (acceptance m84dky1 FAIL, merge nothing)

Prompt said M74 (merged #75); the repo pick was M84d. Branch milestone/m84d from main, carrying
the s128-s131 footing (`git checkout milestone/m84c -- NEXT_PROMPT.md SESSION_NOTES.md NAMED.md
scripts/m84c_item_pump.py scripts/m84_cancel_sentinel.py evidence/...`).

STATIC (bytes + a live /proc/pid/mem census, before measuring). (1) THE >9999 LEG IS A PER-FACTION
CONTEXT SWITCH: 0x4a99e0 `cmp [ebp+0x8],0x270f`/`jle 0x4a9ad3`; 0x4a99fc `[this+0x1d6f0]=1`,
0x4a9a09 `sub ecx,0x270f` (stored back at 0x4a9a0f), edx=(ds:0x888514-1)*0xb4c -> 0x4a9a24
`[this+edx+0xb38]=-1`, 0x4a9a60 `call [[this+(fac-1)*0xb4c+0x80]+0xf0]`, 0x4a9a75
`[this+(key-9999-1)*0xb4c+0xb38]=2`, 0x4a9aac the same notify on the new slot, 0x4a9ac9
`call 0x4a72c0(this, ds:0x86ae40, key-9999, [this+0x1d6e0])`; records are 2892 B at this+0x80.
The <=9999 leg needs `[this+8]==4` and `[this+0x1d6dc]==ds:0x91b5b4` (=3 live) and switches on
0xcef..0xcf4, so the same argument is a message code below 10000 and an index above it.
(2) WHO OWNS IT: the dword 0x4a99e0 appears ONCE in the image, 0x67671c, inside a 197-slot pointer
run 0x676584-0x676894; 0x498ea6/0x498eac store vptr 0x67658c at [obj] and 0x676584 at [obj+0x444]
(0x498f00 `sub ecx,0x444` is the secondary thunk), i.e. primary vtable slot 100 / secondary slot
102, reached by a computed index (no `call [reg+0x190]` anywhere in .text); only 2 .text
references to that table exist, both constructors (0x498ea8, 0x49988c). A scan of every rw region
of terran.exe found ZERO objects with vptr 0x67658c/0x676584/0x67673c. (3) ds:0x888514 IS A
FACTION INDEX (live 0): 0x4a0c17 loops i < ds:0x985af4 (=19) over stride-0x130 records at 0x95da14
comparing BYTE[i] to it, and those 19 records read "University Base"(3), "Gaia's Landing"(2),
"The Hive"(2), "Morgan Industries"(4), "Sparta Command"(5), "New Jerusalem"(6), "U.N.
Headquarters"(2) ... "Korolev Center"(3) — base records with the OWNER FACTION at +0, ours = 3 =
cur_player; 0x499f13 indexes a second per-faction array the same way (`imul eax,0x20bc` over
0x94d7fc, 8380-byte records, slots 0..8 populated, slot 0 reads -1).

ACCEPTANCE FAIL — `python3 scripts/m84d_faction_key.py --tag m84dky1 --boundaries 8 --timeout 380`
(ONE invocation): gdb armed 8 silent bps (0x4a99ec entry, 0x4a9a24 OUT store, 0x4a9a60 notify-out,
0x4a9a75 IN store, 0x4a9aac notify-in, 0x4a9ab2 AFTER, plus the sibling writers 0x4a7d84 and
0x4a759f of [x+0x1d6f0]); the log shows "Breakpoint 1 at 0x4a99ec" ... "Breakpoint 8 at 0x4a759f"
and a clean "[Inferior 1 (process 29779) detached]". Driver m56_build rc=0 in 83 s: "positive
predictions 1/1 verified; boundaries 8/8" (a real production arrival). Events: keys 0, low 0,
OUT 0, IN 0, AFTER 0, notify 0/0, SETFLAG2 0, CLEARFLAG 0 -> G1..G8 all False -> FAIL, merge
nothing. So 0x4a99e0 was entered ZERO times (neither leg) in 8 boundaries and neither sibling flag
writer ran: the class is not instantiated in a normal game loop, so the >9999 vocabulary is not on
the build/production path — this closes the M84c lead (0x4a99e0 is not where 9999 means something
ELSE for the chooser).
OPEN: who calls the constructor FUN_00498e20 (n_callers=1) — that names the screen/mode that owns
this object; the dispatcher that computes slot 100; who WRITES ds:0x888514 (all 37 .text
references to it are reads — the writer is not a `mov ds:0x888514` in .text). NEXT pick: the
0x4194b3 handler / widget message 0x4d00, or ds:0x888514's writer.
Evidence: evidence/m84dky1.gdblog (36 lines), scratch/m84d/{peek,probe2,probe3}.py; evidence 28.0 MB.

## Session 133 (2026-10-28) — M84e: 0x4d00 IS A QUEUE POST, NOT A CALL; ITS HANDLER IS 0x52ed7d (acceptance m84edisp1/2/3 FAIL, merge nothing)

Prompt said M74 (merged #75); the repo pick was M84e. Branch milestone/m84e from main 7a69b20, carrying the s128-s132 footing (`git checkout milestone/m84d -- NAMED.md NEXT_PROMPT.md SESSION_NOTES.md scripts/m84_cancel_sentinel.py scripts/m84c_item_pump.py scripts/m84d_faction_key.py skill/`).

STATIC (instruction bytes only, scratch/m71/dis.py windows): (1) 0x584010 is a POST, not a dispatcher — it builds a 32-byte record on its OWN stack ([ebp-0x20]: +0 WORD code, +4 ds:0x91b5b4, +8 the 0x671368 result, +0xc ds:0x91f694, +0x10..+0x1c the sender's args 2..5) and enqueues it `push [ebp+0xc]; push 0x20; push &rec; mov ecx,0x91db70; call 0x52a260` under the re-entrancy guard inc/dec ds:0x920438. (2) the pumps pop it back: `mov ecx,0x91db70; call 0x6361ff`, `test eax,eax; je` else `push edx; push ecx; push eax; mov ecx,esi; call 0x52bce0` (16 such loops, 0x5262ff-0x526707). (3) 0x52bce0 IS the dispatcher: 0x52bd33 `mov ebx,[ebp+0x8]` = the record, 0x52bd3b `mov ax,[ebx]` = the code, 53 `cmp eax,...` arms; the ONLY 0x4d00 arm in .text is 0x52eb61 `cmp eax,0x4d00` / 0x52eb66 `jg 0x52ef74` / 0x52eb6c `je 0x52ed7d`, and 0x4194a4 (`push 0x4d00; call 0x584010`, inside the chooser function 0x417ee0) is the ONLY sender of 0x4d00 in .text. (4) the handler 0x52ed7d: eax = [rec+0x10] (the sender's arg2 = 0xffffffd9 - edi), then 0x52ed89 `lea edx,[eax+eax*2+0x75]` + shl 4 + 0x52ed97 `lea eax,[edx+0x984d38]` = 0x984d38 + a2*48 + 1872, and 1872 = 39*48 cancels the -39 sentinel -> 0x984d38 - tid*48: a THIRD stride-48 site for the M67 stride conflict. rec+0x14 (0/1/2, pushed at 0x419486/0x419473/neither) selects three sub-behaviours over 1436-byte records at 0x927590 / 0x927894 + player*1436. (5) RETRACT M70's mechanism: 0x52ed7d-0x52f756 writes NOTHING at +0x3ff5c / 0x6e93dc — 0x4194b3 `mov [ebx+0x3ff5c],0` is the instruction right after `call 0x584010` RETURNS, in the SENDER.

LIVE (`python3 scripts/m84e_msg_dispatch.py --tag m84edisp3 --base-index 0`, ONE invocation, 7 silent bps 0x4194a9 POST / 0x4194b3 ZERO / 0x4194bd ZEROAFTER / 0x52bd3e-if-$ax==0x4d00 DISP / 0x52eb6c-if-$eax==0x4d00 ARM / 0x52ed7d HND / 0x52eda4 IDX; `--tag selftest` = positive ALL, negative 6 gates False, so the shape discriminates): 7 bps armed, enqueue rc=0 "pane closed after 1 Escape(s): class hud", events ZERO obj=0x6a9480 pre=15 -> ZEROAFTER post=0: the cursor store IS live and lands (15 -> 0 read back), but POST 0, DISP 0, ARM 0, HND 0, IDX 0 -> G1-G8 FAIL. Two findings from that: (a) ebx at 0x4194b3 was 0x6a9480 = the STATIC PANE (m57's PANE_BASE_IDX base), so the cursor is a PANE-RELATIVE field +0x3ff5c = 0x6aa9dc here, not the fixed 0x6e93dc M70/M71 named; (b) the post IS CONDITIONAL — 0x419464/0x419479/0x41948e/0x419492 all jump to 0x4194b1 past 0x4194a9, so "cursor zeroed, no 0x4d00 posted" is a real path, not a miss. m84edisp1/m84edisp2 (--base-index 18) also 0 events: the INSERT clicks landed on the PANE's base (University pending 0->8->14) while m57 read base 18 and printed "INSERT 1 never landed" — a pane/target mismatch, plus a quit-prompt mid-window (the very failure normalize_screen's docstring names).
OPEN: the -39 branch that POSTS needs a chooser selection to complete (enqueue --no-ok, then close the chooser on a row) — re-run the same 7-bp instrument unchanged; the handler's mode 0/1/2 semantics (0x626634/0x6265a2 list ops over 1436-byte records at 0x927590/0x927894, builders at 0x997b28/0x99aa48, ids 0x68f4e8/0x68fc10 read as zeros in RAM); who else owns a +0x3ff5c cursor. NEXT pick: FUN_00498e20's single caller (names the mode that owns the 0x270f keys) or ds:0x888514's writer.
Evidence: evidence/m84edisp1.gdblog, m84edisp2.gdblog, m84edisp3.gdblog; scratch/m84edisp{1,2,3}.gdb (evidence 27.5 MB).

## Session 134 (2026-10-28) — M84e follow-up (bytes only): the 0x4d00 POST is GATED on ds:0x920434, the OPENING-MENU flag — s133's POST 0 is THE GAME, not the instrument

Prompt said M74 (merged #75); the repo pick was M84e, and a sibling cron session had already run it while I was briefing (milestone/m84e 592e177 + dae5049, acceptance m84edisp1/2/3 FAIL, PR #88 gate pass, merge nothing). One box: I did NOT arm a second gdb (s125/s126 collision rule) and instead verified its zero from instruction bytes.

STATIC (scratch/m71/dis.py windows, no box): the POST 0x4194a9 sits behind THREE gates inside FUN_00417ee0: 0x4193b2 `mov eax,ds:0x920434` / 0x4193b7 test / 0x4193b9 `je 0x4194b1`; 0x4193bf `mov eax,[ebp+0x8]` / `jne 0x4194b1` (arg1 must be 0); 0x4193ca `mov edi,[esi+0x50]` (= base+0x50, the queue HEAD) / 0x4193d0 `cmp edi,[ebp-0x1c]` / `je 0x4194b1` (no post when the head equals the snapshot). 0x4194b1 is the block's COMMON exit — four jumps land on it (0x4193b9, 0x4193c4, 0x4193d2, plus the ladder's 0x419462/0x419479/0x41948e/0x419492) — and it is `push 1; mov [ebx+0x3ff5c],0; call 0x4eb6b0`: the cursor zero happens WITHOUT any POST, which is exactly s133's read-back cursor 15 -> 0. Before the gates, 0x41937c-0x4193b0 walks base+0x50 for i < [base+0x4c] and `inc`s the byte at 0x94de84 + item + tid*8380 (M63's queued-count; 8380 = 0x20bc = M84d's per-faction stride), so the mutation the block performs is a queued-count bump.
WHO SETS THE GATE: `grep -n "ds:0x920434," scratch/m574/text.txt` (comma = store) lists the stores (0x50fe70, 0x50fff5, 0x510196, 0x515ad8, 0x515fb1, 0x516f30, 0x516fd4, 0x51f267, 0x52280c, 0x52289d, ...); `grep -rn -B80 "DAT_00920434 = " ghidra_out/*.c` shows every writer stores 0 (FUN_0050fea0, FUN_00522850 twice, shard_015 twice, ...) and exactly ONE stores 1 — FUN_0057ecf0 (0x57ecf0, 2639 B) at its entry, whose strings are INTRO / SCENARIO / TOPMENU / MULTIMENU / ALPHA / openinga_pcx / openingb_pcx / fx_opening_menu_wav, i.e. the opening movie + scenario/top-menu loop; it stores 0 again on exit. Live ds:0x920434 = 0 on the hud (the footing's gate globals).
CONSEQUENCE: in a loaded game the build-queue block can only leave via 0x4194b1, so POST 0 / DISP 0 / ARM 0 / HND 0 in m84edisp1/2/3 is the branch outcome, not an arming failure. The mode that owns message 0x4d00 is the OPENING MENU — the same dead-leg shape as M84d's vtable with no instance. OPEN (one variable): is FUN_00417ee0 (n_callers=10) ever entered with ds:0x920434 == 1 — poke 0x920434 = 1, mutate the queue, re-run `scripts/m84e_msg_dispatch.py` unchanged; shard_001.c:9463 `for (; DAT_00920434 = iVar2, ...)` is a variable store I did not chase.
Evidence: no new evidence file (bytes only; scratch/m71/dis.py windows 419340-41940f, 52bce0-52be60, 52ed7d-52ee10).

## Session 135 (2026-10-28) — M84f: the NETGAME gate is LIVE-measured; the poke leg is blocked by BOX STATE (m84fpath1 census, m84fleg4/5 invalid)

Prompt said M74; the repo pick was M84f (make the 0x4d00 POST leg fire). Branch milestone/m84f from main, carrying m84e's footing (instrument + docs + skill).

MEASURED (`python3 scripts/m84f_path_census.py --tag m84fpath1 --base 17 --inserts 1`, ONE invocation, 7 print-only bps + a /proc read-back): the netgame-gated block DOES run on a real UI insert — CHOOSER 2 (the 0x41860a modal call), CASE 1 (0x419355), BUMP 7 (`inc [0x94de84 + item + tid*8380]`, one per queue slot), EXIT 1 (0x4194b1), NETCALL 1 (0x528760 from 0x419368), netgame 0, pend 5 -> 6 read back. So s134's static reading is confirmed live: the block walks the queue, reaches `mov eax,ds:0x920434` at 0x4193b2 and, with the flag 0, takes `je 0x4194b1` = `push 1; mov [ebx+0x3ff5c],0; call 0x4eb6b0` — cursor zero plus a call, NO 0x4d00 post. Gates G1/G2/G3/G5 True, G4 False — G4 was MY wrong prediction ("the case never runs"); the case runs and stops AT the gate.

INSTRUMENT PITFALL (cost two runs): a MEMORY WRITE inside a gdb breakpoint command list — `set {int}0x920434 = 1` or `set var *(int *)0x920434 = 1` — aborts the batch with "Left operand of assignment is not an lvalue" at the FIRST hit and gdb DETACHES (m84fleg1/2/3: 36-line log = ARMED + 9 "Breakpoint at" lines + the error, 0 events; the driver's insert still lands because detaching resumes the inferior). The working poke is python-side: os.pwrite to /proc/pid/mem succeeds WHILE gdb is attached (m84fleg4: 632 writes, 0 errors, print-only bps logged cleanly).

BLOCKED (box state, not bytes): after `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` the game is 2150 r50 — University Base only, pend 0, credit 0, and the chooser's candidate array is EMPTY (`m57_ui_enqueue: FAIL: item 2 not in candidate array []`), so no insert can be driven; ds:0x8f0d60 is 0 until a pane opens, which killed the ARMED printf (`*(int *)($b + 0x4c)` on 0x4c -> EIO). The 2163 r63 state (chooser [192,195,194,193,2,0,1,196], Korolev pend 1) was LOST by that reload. NEXT: get a buildable state (fresh save + turns, or a later save), then `python3 scripts/m84f_post_leg.py --tag m84fleg6 --base <buildable idx> --inserts 2` — poke on odd visits, control on even, 9 print-only bps; the flag-1 arm is the only unmeasured leg.
Evidence: evidence/m84fpath1.gdblog (valid), evidence/m84fleg4.gdblog, evidence/m84fleg5.gdblog; scratch/m84f*.gdb; evidence 27.6 MB.

## Session 136 (2026-10-28) — M85: the tech/upkeep trio splits into "MP-only by design" and "reachable helper"; the live arm is blocked by the TURN TRIGGER (m85cens1 FAIL)

Static (deterministic: `ghidra_out/index.csv` addr/size_bytes + call lines in `scratch/m574/text.txt`): 0x52145e is inside FUN_00521070 (+1006), whose ONLY call site is 0x522376 — and m55_boundary.py's docstring identifies FUN_00521070 as the MULTIPLAYER 7-stage driver (mode_flags & 0x10). So the M67 "zero events" at 0x52145e is BY DESIGN in solo, not a bad breakpoint. 0x5a7d00 (+912) and 0x5a7f67 (+1527) are both inside FUN_005a7970: 47 call sites, one at 0x507e57 inside the human-turn loop FUN_0050f420 — so those zeros are an untaken branch, not unreachable code.

Live (`python3 scripts/m85_tech_census.py --tag m85cens1 --timeout 120`): FAIL — round 50 -> 50, year 2150 -> 2150, driver rc=1 ("no round boundary (year never moved) within 120.0s"), events = {ARMED: 1}. ONE VARIABLE ISOLATED: the same driver without gdb (`python3 scripts/m55_boundary.py --timeout 90`) fails identically, so the instrument is innocent — the box cannot end a turn.

Input probe (measured): game window = X id 10485761 "Sid Meier's Alpha Centauri" inside Wine desktop "smac - Wine Desktop"; state cur_player 3 (us), turn_flags 0, stage 0, round 50 — it IS our turn. Return is inert BOTH ways: XSendEvent (`xdotool key --window 10485761 Return`) and XTEST after focus (`xdotool windowfocus 10485761; xdotool key Return`) leave round/year unchanged. s132/s133 logged "one Enter fires the boundary within 0.2 s" on this box, so the trigger, not the code, changed with state. Next: CLICK the on-screen END TURN control (clicks still land — m57_ui_enqueue's do), or restore a state where Enter is the end-turn key (no unit selected).

CONFLICT recorded, unresolved: ds:0x920434 is "save_later" in m55_boundary.py's G table and "NETGAME" in the M84e/s134-135 docs. Compatible story (a chooser save-for-later mode would explain why FUN_0057ecf0 is the only 1-writer) but unproved.
Evidence: evidence/m85cens1.gdblog; scratch/m85cens1.gdb; scratch/m85diag.png (root grab, unread).

### s136 addendum — the live blocker is BOX-LEVEL INPUT FOCUS, not a driver choice

- `m85cens2` (driver switched to m44_idle, the pane-clicking turn advancer): driver rc=1 in 0 s, round 50 -> 50.
- `m85cens3` printed the child's stderr: a bare traceback, so the census is not the place to debug it.
- Run standalone, `m44_idle.py --tag m85probe --rounds 1 --budget 60` exits rc=0 and reports `reason: "1 rounds"`, but its own snapshot line still reads `[round 1] {"year": 2150 ...}` and `m85cens3_drv` (budget 420) does the same: the driver walks its loop and the YEAR NEVER MOVES.
- `xdotool getactivewindow` returns EMPTY and `windowfocus 10485761` does not change that: this X session has NO input focus at all. The game window is 800x600 at (0,0) (id 10485761, "Sid Meier's Alpha Centauri" inside "smac - Wine Desktop") and it IS rendering — mean luma 19.3, 19% of pixels > 32 in a fresh 800x600 grab — so this is not a blank window.
- Consequence: no keyboard OR pane-click path can end a turn on this box right now (keys: 6x Return inert via XSendEvent and via XTEST; clicks: m44's find_ok_bar route leaves year at 2150). s133's successful boundary runs happened while the window still had focus.
- NEXT (one command, before any boundary work): restore X focus — `xdotool windowactivate --sync 10485761` (needs a WM) or start/attach a WM, then re-check `xdotool getactivewindow` is non-empty; only then `python3 scripts/m85_tech_census.py --tag m85cens4 --rounds 1`.

## Session 137 (2026-10-28) — M85 CLOSED: the solo boundary IS live and DOES enter the helper; the M67 zeros split into "MP-only by design" + "branch not taken" (m85cens5 PASS)

Prompt said M74; the repo pick was M85 (PR #90 open, m85cens1-3 FAIL, blocker named as "no X focus").

BOX REPAIR (measured): s136's focus diagnosis was a red herring — `getactivewindow` ALWAYS errors on :99 (no WM supports _NET_ACTIVE_WINDOW); `xdotool windowfocus 10485761` sticks (`getwindowfocus getwindowname` returns the game window) and keys DO reach the game (one Escape flipped classify base->hud). But the s135-state box (2150 r50) swallowed every turn-end input: XTEST Return for 90 s did nothing, and a click on the MEASURED TURN COMPLETE center (OCR bbox (675,416); the vision tool's coords are scale-shifted — real bar y 405-427, the white box at y 484 is the recenter button) produced no confirm dialog and no round change. Cause NOT isolated (confounded: s135's 0x920434 /proc pokes, repeated gdb attach/detach, or a load artifact are all candidates). `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` restored the boundary immediately (m55_boundary fired, round 50->52).

INSTRUMENT DEFECT (why m85cens1/2/3 died): census's driver m44_idle asserts `TracerPid == 0` at entry — it cannot run under census's own gdb (m85cens4: driver rc=1 in 0 s, "AssertionError: tracer attached"); and its `--rounds 1` snapshot condition `y > last_year - 1 and not rounds` counts the CURRENT turn as a completed round, so it exits rc=0 in 0 s never having clicked. Census now drives with m55_boundary.py (no tracer assert, windowfocuses itself).

ACCEPTANCE PASS — `python3 scripts/m85_tech_census.py --tag m85cens5 --timeout 240` (ONE invocation): all six gates True; round 52->53, year 2152->2153 read back from /proc/201960/mem; EVENT COUNTS {ARMED:1, HELPER:1, ROUNDINC:1, STAGE:0, MP45E:0, H1:0, H2:0}; driver rc=0 "PASS boundary 2152->2153: player walk observed (cur_player [0,1,2,3,5,6,7])".

OUTCOME: (1) FUN_00521070 (MP 7-stage driver) never entered in a solo boundary — 0x52145e silence is BY DESIGN (G2/G3). (2) FUN_005a7970 IS entered once per boundary, eax=0, return site 0x569948 = inside FUN_0055f650 (0x55f650, 54483 B, call sites 0x50dd84/0x56cf12) — NOT the human-loop site 0x507e57 — so the M67 zeros at 0x5a7d00 (+912) / 0x5a7f67 (+1527) are UNTAKEN BRANCHES inside a live helper, not dead code (G4). (3) The round increment 0x51f320 fired once per boundary.

OPEN: which leg eax=0 takes inside FUN_005a7970 and what gates the two tails; who calls FUN_0055f650 at 0x50dd84 (round driver?); ds:0x920434 save_later-vs-NETGAME conflict still recorded (G6). NEXT pick: M86 — the helper's boundary visit: disassemble 0x5a7970 entry + the branches to 0x5a7d00/0x5a7f67, add a bp printing eax and the branch inputs, re-run census unchanged on a fresh-loaded box.
Evidence: evidence/m85cens5.gdblog (975 B), evidence/m85cens4.gdblog, scratch/m85cens5_bnd.jsonl; evidence 27.9 MB.
