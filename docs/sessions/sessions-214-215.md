# Session notes archive — sessions 214-215

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 214 (2026-11-05, ANALYSE static, M274 PASS 6/6) - the 128-bound loop is NEVER clamped; big-map spills read the sibling verdict array silently
- Picked the M273 follow-ups (static, no box): `scripts/m274_rowcap_census.py` ->
  **SUMMARY M274: 6/6 gates PASS** (`evidence/m274_census.txt`), body 0x556690-0x559e9d, 4,235 insns
  read from the aligned scratch/m574/text.txt cache (containment from ghidra_out/index.csv).
- ANSWERS: (G1) the region loop has ONE bound, the constant `cmp ecx,0x80` at 0x558b1c - no clamp to
  the 94-slot row anywhere; (G2) regions 94..127 SCALED (max 2*127=254 B) land INSIDE the sibling
  verdict array 0x94eba8 (gap 256) -> on 80x80/128x128 maps the overflow is SILENT WRONG DATA;
  (G4) a nonzero verdict byte stores 0x8 (0x557fdf) then jmps the loop tail (0x557fe7) - that skip,
  not a shallow loop, is why M273 saw only sparse events; (G5) the verdict array has exactly 5 store
  sites (0x8/dl=7-or-8/0x0/0x2/0x7).
- CORRECTION (mine, from M273): "8380 mod 188 = 88" was an arithmetic slip - it is **108**; the
  non-integrality conclusion is unaffected. Fixed in NAMED.md, NEXT_PROMPT.md, notes.
- The fold re-derived from bytes: esi = 2*region + 188*(E+edi) - the multiplier is (E+edi), NOT a
  bare faction index. The row slot [ebp-0x18] has 15 writers in the body -> the live cursor's origin
  is a DEF-USE pick, not settled. New open picks: which writer feeds the UNSCALED read site; the
  def-use of the 15 row-slot writers.
- Method law: an objdump --start-address INSIDE an instruction silently misaligns the window
  (invented .byte lines, poisoned a reachability walk) - use the aligned cache or the fn entry.

## Session 215 (2026-11-05, ANALYSE static, M275 PASS 8/8) - the read site has ONE reaching def (the fold) - and the live cursor contradicts the fold's arithmetic
- Picked M274's def-use follow-up (static, no box): `scripts/m275_rowslot_defuse.py` ->
  **SUMMARY M275: 8/8 gates PASS** (`evidence/m275_defuse.txt`). Sound CFG (0 indirect jumps,
  4,235 insns); reaching defs of [ebp-0x18] at the read-site load 0x55844b = **{0x558038}** only.
- CORRECTS M256's fold prose: re-decoded `mov eax,edi; shl eax,6; add eax,edi; lea esi,[ecx+eax*2];
  shl esi,1` = **esi = 2*region + 130*edi**, edi = the function ARGUMENT (last writer 0x557fbb
  `mov edi,[ebp+0x8]`). (188 = 2*94 is the table's row CAPACITY - a different quantity; M274's
  "188*(E+edi)" was my own mis-multiply: 16*3-1 = 47, x2 = 94 per unit... the script's G6 shape
  check now pins the exact insn sequence.)
- THE FINDING: M273's live rows differ by whole 8380 strides, but **8380 mod 130 = 60 != 0** -
  no integer arg yields them through this fold. Static and live are irreconcilable as modeled;
  the missing writer is outside the visible displacement forms (G8: 14 block-band stores, zero
  at the slot's absolute faces). Queued pick: hw-watchpoint the frame slot during the
  auto-manager (watch reports pc = store + insn length).
- Self-check win: my mental "8380 mod 130 = 100" was WRONG; the computed assert caught it (60).
  Numbers come from the script, never from my arithmetic - the gate asserted before shipping.
