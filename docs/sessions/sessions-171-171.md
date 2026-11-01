# Session notes archive — sessions 171-171

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 171 (cont. 24) — M166-M168 (all PASS): what the rank is, how the struct splits, and a derived cache

`python3 scripts/m166_m168_roles.py` — SUMMARY M166=PASS M167=PASS M168=PASS.

- **M166 — the rank is consumed as an ORDERING TEST.** 0x94d434: 196 refs of which **92 are `cmp`**, against small
  constants **2/4/5/6/7**; the ranking INPUT is the 7-entry dword table at **0x926a7c**, read by only two functions (the
  init loop in FUN_0059aa00 and FUN_00531df0 at 0x532150), and the top entry is EXCLUDED by the single `-1` store at
  0x59ac72 into `0x926a78+n*4`. So the shape is: an order among 7 candidates, one discarded, the result compared
  against small thresholds. **What is being ranked stays unnamed** — recorded as bounded.
- **M167 — the 20-byte struct SPLITS into a header + a payload quad.** All five members have exactly 6 writes, but the
  WRITER SETS differ: `+0x00` is written by FUN_004dc100 (x3) and FUN_0059ec90 (x3) with constants 0/1/0xffffffff and
  carries 7 tests, while `+0x04/+0x08/+0x0c/+0x10` share the SAME five writers (FUN_004dc100, FUN_00510230,
  FUN_00512b40, FUN_00516b80, FUN_0059ec90 x2). Uniformity would have shown one writer set for all five; it does not.
- **M168 — 0x94d488 is a DERIVED/CACHED value, not state.** 22 writes spread over **9 functions** against 49 refs and a
  single comparison. That is the write-dominant profile (cf. base+0xd0 credit, M97): many paths recompute it, so a test
  that treats it as authoritative state is reading whichever path ran last.

## Session 171 (cont. 25) — M169-M171 (all PASS): the totalled table, the aggregator, and a bit-decoder dressed as a struct

`python3 scripts/m169_m171_aggregate.py` — SUMMARY M169=PASS M170=PASS M171=PASS.

- **M169 — 0x926a7c is TOTALLED, not flagged.** Its second reader (FUN_00531df0, 0x532150) runs inside a per-faction
  loop that walks the blocks at stride **0x20bc (8,380)** while stepping the table index by 4, doing
  `ds:0x9204ac++` and `ds:0x9204c4 += [eax+0x926a7c]` — a COUNT and a SUM. So the array M163 ranks is a per-faction
  quantity being totalled across factions.
- **M170 — FUN_00531df0 is the per-faction AGGREGATOR** (6459 B, 1905 insns, 17 call sites): it builds a `1<<faction`
  mask (`shl edi,cl`), gates on **`cmp [ebx+0x94d434],0x5`** — the M163 rank used as a `< 5` threshold, exactly what its
  92 comparisons predicted — and accumulates the count/sum above (plus 0x920720 / 0x9204c8 counters).
- **M171 — FUN_004dc100 is a BIT-DECODER, not a copier.** One byte arrives in AL and the "20-byte struct" is filled as
  **four BOOLEAN dwords**: `[esi+0x94d810/14/18/1c] = setne(al & 1/2/4/8)` (four `setne dl`), the header
  `[esi+0x94d80c]` gets the TRISTATE 1 / -1 / 0 from the `al & 0x10` / `al & 0x20` tests, and `al & 0x40` triggers
  `or [esi+0x94d430],0x800000`. M164's "header + payload quad" is the decoded shape of ONE SOURCE BYTE's bits.
