# Session notes archive — sessions 127-127

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

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
