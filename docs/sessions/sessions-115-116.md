# Session notes archive — sessions 115-116

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 115 (2026-10-28) — M74: WHO sets `type[+0x30] & 4`. ACCEPTANCE FAILED on two real invocations; the setter is NOT among the eleven absolute-address writers.

**Static first pass.** The flags word is addressed ABSOLUTELY (`[reg*4+0x98adb8]`,
`[reg+0x98adb8]`), so every access is greppable: 168 accesses to `+0x30`, and the bit-2 setters
are ELEVEN sites in four functions — `0x4eed18` (FUN_004eec30; `or BYTE [ebx*4+0x98adb8],4`,
guarded by `0x3f < param_2`, i.e. only a DESIGNED type, and it is the NEW type of a unit
transformation — the same function clears bit 0 on the OLD type at `0x4eed2b and [edi*4+..],0xfe`),
`0x573fed / 0x574107 / 0x574117` (FUN_00573a90), `0x595f82 / 0x595f91 / 0x595f9c` (FUN_00595b10,
whole-word `= 1 / 0x105 / 0x115`), `0x59d273 / 0x59d375 / 0x59d432 / 0x59db65` (FUN_0059ce10).
M73's second candidate `0x4d20f0` only READS `+0x30` (`mov ax,WORD[..]` at `0x4d258e`,
`test BYTE[..],4` at `0x4d2f35` and `0x4d3277`) — a CONFLICT with the M73 note, reported not fixed.

**Runs.** `python3 scripts/m74_flag_watch.py --ids 193,194 --boundaries 4 --poke-minerals 200
--tag m74flag` -> **FAIL** (9/10 gates); `... --tag m74flag2` -> **FAIL** (3 gates). The first
run's zero writer rows was the INSTRUMENT: every condition tested the register against the bare
tid, when `[reg*4+0x98adb8]` means the register holds `tid*13` and `[reg+0x98adb8]` means `tid*52`;
the POSAFF flag read used `*4` where it needed `*0x34`, so it printed `f30=0x00`. Corrected from
the encodings; `scripts/test_m74_flag.py` -> **37/37**.
- m74flag2 read back: `ARMED head 194 pending 0`; POSAFF id 194 `f30=0x41 edi=45` and then, in the
  SAME window, `f30=0x45 edi=27` — the markup ON -> OFF flip, measured with the flag read at the
  right address (45 = 9 x 5 with markup, 27 = 9 x 3 without). Census: `193: 0x41 -> 0x05`,
  `194: 0x41 -> 0x05`, and records `65` and `195` gained bit 2 in the same window (confounded).
  `pending 0 -> 0`, storage `200 -> 200`, head unchanged: NO completion happened (the re-enqueue
  did not land), so **`when` is still unproven**.
- With the corrected conditions, **0 of 11** writer breakpoints fired on the armed ids.

**New candidate.** `0x597487 mov WORD PTR [eax+0x30],dx` inside `FUN_00596850`: a stride-52 sweep
(`add eax,0x34` ... `jne 0x5973bc`) that copies a SOURCE-TABLE row into every type record's
fields `+0x23..+0x30`, called only from `FUN_00597ce0` and `FUN_00597ee0`. A whole-word table copy
explains `0x41 -> 0x05` on several records at once with none of the eleven bit-2 setters firing.
(My first grep for `[reg+0x30]` stores reported zero because I matched lowercase `ptr [` against
objdump's `PTR [`; corrected, it finds 101 stores, three of them byte/word.)

**Tooling.** `scripts/m74_flag_watch.py` (11 conditional writer breakpoints + the `0x4efa5e` visit
gate, a 256-record `+0x30` census before/after, per-boundary storage poke + read-back, 10 gates)
and `scripts/test_m74_flag.py`. Branch `milestone/m74` holds them; **no PR, acceptance FAILED**.

**Open / next pick.** M74 stays open: (1) is `FUN_00596850` called mid-game (a unit-table reload)
or only at load — read `FUN_00597ce0` / `FUN_00597ee0` and breakpoint `0x597487`; (2) arm with
`pending >= 1` and a REAL completion (enqueue, then read `pending` back BEFORE attaching); (3) the
census must say why `65` and `195` move together with `193`/`194`.

## Session 116 (2026-10-28) — M74: WHO sets `type[+0x30] & 4`, and WHEN. ACCEPTANCE PASS (tag `m74flag3`), the writer is the PRODUCTION path itself.

**Box first.** The s115 box was DEAD: no `terrans.exe` in `ps`, the Xvfb frame stale —
`accept_ready` read the frozen frame as screen `help` (a FACTION PROFILES page with a modal
Treaty-OK popup at ~(378,455) on top; EXIT clicks at (500,360) were no-ops on a dead process).
Relaunch `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` -> HUD round 50.
`m57_ui_enqueue --base-index 0 --cell-item 194 --inserts 1` -> pending 1, queue [2, 194].

**New instrument, right shape.** `scripts/m74_flag_hw.py`: four 2-byte HARDWARE watchpoints on
the flag WORDS themselves (`*(short *)(0x98adb8 + tid*52)` for tids 193/194/65/195), refuses to
drive unless gdb echoes "Hardware watchpoint" 4 times, then 3 boundaries with storage re-poked
200 before each. One real invocation:

    pid 3716776 ... watched flags before: 65=0x0, 193=0x41, 194=0x41, 195=0x0
    armed: 4 hardware watchpoints on [193, 194, 65, 195]
    boundary 0: rc=0 32s | boundary 1: rc=0 69s | boundary 2: rc=0 117s
    watched flags after: 193=0x45, 194=0x45 | head 194 pending 0 round 53 tracer 0
    --- 3 FLAGW events ---
      tid 194 pc 0x4efe67 val 0x45 | tid 193 pc 0x5729de val 0x145 | tid 193 pc 0x4ef39f val 0x45
    ACCEPTANCE m74flag3: PASS

**The three writers, mapped back one instruction (watchpoint pc is AFTER the store):**
1. `0x4efe60 mov WORD PTR [esi+0x98adb8],ax` in FUN_004ef6d0 (the production function, between
   the gate `0x4efa5e` and pay `0x4efed8`): `cmp ebx,0x40` skips non-designed; else `mov ax,[rec];
   or al,0x4; mov [rec],ax` — sets bit 2 on the PRODUCED unit's record at the moment it is made;
   `[ebp-0x20] = (~old)&4` (newly-set flag) and `je 0x4efed8` sends an ALREADY-marked record
   straight to pay. The newly-set path `0x4efe71..0x4efed0` calls `FUN_00572800(eax, tid, 0)` at
   `0x4efe7e`, sets current-base `0x8f0d60 = 0x95da10 + esi*304`, and runs refresh calls
   `0x4e8d60/0x4e78e0/0x4e92c0/0x4e93f0/0x4eaa10`. (194: 0x41 -> 0x45.)
2. `0x5729d5 or WORD PTR [edi+0x98adb8],0x104` in FUN_00572800 — a stride-0x34 loop over the 256
   records, guarded at entry by `tid >= 0x40 && !(flag & 4)` (first production only). It marks
   every record that is valid (`&1`), unmarked (`!( &4)`), passes validator `0x5a6cd0`, and whose
   classification bytes `+0x24/+0x25/+0x26` match the produced unit's (with rank tables
   `DAT_0092b950`/`0x92fd18`). Marks bit 2 AND a temporary marker bit 8 (0x100). (193: 0x41 -> 0x145.)
3. `0x4ef398 and BYTE PTR [ebx+0x98adb9],0xfe` in FUN_004ef380 — clears the 0x100 marker.
   (193: 0x145 -> 0x45.)

**WHEN, proven:** at PRODUCTION (past the gate, before pay), not at completion detection or a
round boundary: head 2 completed at r51, 194 popped to head, 194's store fired at its production
(r52/53); census read back after: 193/194 = 0x45. This also explains M73's live 45 -> 27: the
first production charges markup (bit clear at gate time) then SETS the bit, so every later visit
skips it — and the sweep marks sibling designed records (same chassis family) so they skip markup
from their first production too (why 65/195-type records move with 193/194).

**Retractions.** (a) `0x597487` (FUN_00596850 sweep) is NOT a live setter: FUN_00596850 is a
save/LOAD codec — called only from FUN_00597ce0 (fopen + magic 0x56 read, `FUN_00596850(f,1)`)
and FUN_00597ee0 (save, `FUN_00596850(f,0)`); its sweep copies a stride-48 file buffer into the
`0x93327a` table (stride 52, count `0x985af0`), while `0x98ad88` itself is read/written whole
(0x6800 B) — different table, load-time only. (b) The eleven absolute-address writers stand but
are NOT the production setter: none fired in s115 or here. The real setter evaded both grep
shapes because it is a read-modify-write through a COPIED register (`mov ax,[x]; or al,4;
mov [x],ax`) — a plain MOV with the `0x98adb8` addend, not an immediate bit-op.

**Open / next pick.** M75 candidate: the sweep's match semantics — what `+0x24/+0x25/+0x26` are
(chassis/level/domain?) and why 193 matches 194 but 195/65 do not; also who else calls
FUN_00572800 (shard_002 `param_3=1` path, shard_012:20852, shard_014:17826) and FUN_004ef380
(shard_013:12093 with `DAT_0091b5b4`); and s115's `0x41 -> 0x05` (bit 6 LOST) is still unexplained
— it needs a whole-word writer, likely one of the `0x595f82/91/9c` conversion stores.
Evidence: `evidence/m74flag3.gdblog`, `evidence/m74flag3_seq.jsonl`, traces `m74flag3_r0..r2`.
