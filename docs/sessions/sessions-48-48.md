# Session notes archive — sessions 48-48

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 48 (2026-10-22) — M50a: 0x4f26e0 IS NOT A COST STEP — it is the per-base mineral↔energy conversion/income step and a THIRD storage writer (0x4f2d7d); deltas live-observed 0…+12 (storage GAINS); our base early-returns via the base+0x38 flag gate; sweep truncated again at 28 visits (ours unvisited)

`scripts/m50a_drive.py` (copy of m49a_drive.py + 3 bps: F26E0 entry 0x4f26e0, **CONVST 0x4f2d7d**
(the store), RET26E0 0x4f5ae1; own counters $nb26/$ncv/$nre). Run `evidence/m50a_*` (1 round,
2349→2350, 0 OCR, clean detach; sweep PIPE n=1..28, all own≠3 — the YEAR store 0x51f554 fired
mid-sweep, our base never processed; poked min40=200 survived, OURBASE log line 246).
Static: clean 32-bit disasm of 0x4f26e0 (gdb file-target recipe) + Ghidra pseudocode.

**VERIFIED (disasm + live ×1 round, 28 F26E0 hits / 10 CONVST hits): `0x4f26e0` is a mineral
INCOME/CONVERSION step, not a production cost.**
- Early-return gates (0x4f2705-0x4f2729): (a) event-owner ∧ `~(base+0x38)` bits 0x1a/0x1c set
  ⇒ return — **our base takes this path** (f30=0x805000 has bit 0x1c ⇒ 0x4f26e0 never executed
  for us: 0 ours=1 hits, log lines 59-246); (b) `base+0x40 == 0` ⇒ return.
- Reads `base+0x50` (queue) → `|q|×240 + 0x984d44 + 0x44` = the ITEM table (stride 0xF0 — the
  same 0x984d48 rows M46 named; int1 = required-tech id, e.g. 44/43) used as a DIVISOR-ish
  multiplier; amount ebx = f(event mask, energy pool `0x94d650+p·0x82f·4`, queue value, item
  int1, government/trait term `0x927a84+p·0x3c`+0x50 (value 100 doubles), global 0x985bb8=−1,
  `0x985aec`); clamped `0 ≤ ebx ≤ min(energy-derived, energy_pool − storage)`.
- **Third storage writer: 0x4f2d7d `base+0x40 := storage + ((E/esi)·45)/trait`** (the
  (E/esi)·45 = ×5·×9·<<2 formula at 0x4f2d68-71; esi = 0x4e40a0 event result, live edi=4/esi
  values on entry prints). Then event-owner branch (0x4f2d85): event owners SKIP the energy-side
  adjustment (0x4f2dc4-0x4f2e97); non-event owners also add `−(0x985aec·ebx)/((8−gov[+0x50])·2)`
  to the energy pool.
- **Live CONVST deltas (log lines 131-192): storage CHANGES by 0…+12 — GAINS, not debits**:
  own=6 deltas 0,0,0,0,+1,+4 (lines 131-178); own=7 deltas +12,+3,+2,+1 (lines 185-192).
  own=4: CONVST never fired (branch not taken; own=4 bases show min40 unchanged entry→exit,
  lines 59-90). ⇒ M44's "unspent base minerals → energy ≈1:1" anti-correlation is NOT this
  function's storage path (player 4 takes a different branch; its +10.9 energy/round comes from
  elsewhere). The conversion amount scales with the FACTION ENERGY POOL (AI pools 192-1080 vs
  ours 19) — energy-rich factions pump more minerals into base storage per round.
- **Production mineral cost STILL OPEN**: the per-base chain 0x4f26e0 → 0x4ee410 touches
  storage only at 0x4f2d7d (credit); 0x4ee410 has no base+0x40 access (grep-verified); the only
  debits remain the M49a index-quirk at 0x4efee0. ⇒ production appears effectively free of
  mineral costs in solo; the queued-item "cost" read at 0x4f2750 is the item table's tech-id
  slot, not a price.

**Sweep early-stop (M50b data point)**: this round PIPE n=1..28 (all own≠3) then the YEAR store
interrupted — third independent observation of truncation (21/28/28). Consistent with
0x520540's per-base loop aborting mid-array when the round/year advance lands inside the sweep;
exact mechanism still OPEN.

**Pitfall**: none new operational (clean round, 0 OCR). Note the CONVST bp prints pre-store
values ($eax = the NEW value about to be stored; delta = new − current).

Next (options): M50b sweep early-stop (bp 0x520540 loop body + 0x51f320 caller ordering);
M50c cc source; M50d the 2320 +4 credit; M50e faction NAME mapping; NEW: the energy-side of
0x4f26e0 on a non-event AI base (pin the energy pool store in 0x4f2dc4-0x4f2e97, correlate
CONVST delta vs pool delta in one round); NEW: what makes our base take the 0x4f2705 flag gate
(base+0x38 bit 0x1c = ? — likely the "no AI spending/disrupted" flag) and whether clearing it
routes us through the conversion (minerals income!).
