# Session notes archive — sessions 118-119

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

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
