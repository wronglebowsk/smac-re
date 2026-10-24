# M53q — build_table() implemented: the per-visit scan pool is RECOMPUTED, and the filter is a no-op

Model: `scripts/m53p_recon_a.py::build_table(idx) -> (table[25], mask21)`, wired into
`rebuild()` (entry filter `mask_in = d78 & (~fresh|1)`); the superseded stale-global path is
`--stale-mask`. Dump: `evidence/m53q_dump4.txt` (pid 2124624, year 2383-era state, cur base idx 69,
fac 3, nb 75, nunit 333, wrap 0) — refreshed with the extended `scripts/m53o_mem.py` (units blob
0x4600, new key `nunit`=0x985af0). Line refs = `evidence/m53j_text.txt.gz` unless stated.

## 1. Ground truth vs computed — the LIVE CUR BASE (VERIFIED)
`evidence/m53q_probe.py` → `evidence/m53q_probe_out.txt` dumps everything 4e63b0 reads for base 69;
live table 0x8f0ccc = `[4,0×7,8,0×12,1,1,1,1]`, live `DAT_008f0d30` = 0x101.
Computed (fresh dump): table matches 20/21 slots; **the one disagreement is step 8 (bit 8)** —
live 8, computed 0. Mask rule itself is VERIFIED: computed-from-live-table mask == live 0x101, and
`DAT_008f0d30` has exactly 2 stores in all of .text (0x4e6929/0x4e694f, asm 298597/298610, both
inside 4e63b0) ⇒ single writer, no other producer (zgrep counts: 2).
Bit-8 mismatch detail (INFERRED cause): the |=8 store 0x4e6635 needs a stack member with fac≠3,
relation≠occupied AND +25-faction-bit CLEAR (see §2); every unit on (45,9) now reads fac 2,
`w18=0xffff`, `b25=0xff`, order 0 (probe output) ⇒ all skip ⇒ 0. The live 8 means at rebuild time
that stack satisfied the test (units 106/110/137/138/144/146/147 are in transit, order 0, now —
their state changed after the last rebuild; INFERRED). Report location: **bit 8 / step 8 / tile
(45,9), foreign-stack test**, before any residual theory.

## 2. Predicate fixes vs the M53q1 decode (VERIFIED by re-reading the branch bodies)
- **Chain-walk carry-over (VERIFIED, asm 298346-298352):** the +48 walk (0x4e65ac-0x4e65cf) leaves
  `esi` at the +48 terminus (147 for tile (45,9)); the +50 walk at 0x4e663c **starts from that
  terminus, not from the head** — my first implementation re-anchored to the head and missed the
  coverage. The two chains are the same set in opposite orders (probe: +48 106→…→147, +50 147→…→106).
- **Polarity of the |=8 gate (VERIFIED, asm 298330-298352):** `cmp eax,ecx / je 0x4e663c` (0x4e65eb)
  skips when unit fac == ours (store path = FOREIGN); `cmp dx,0x440 / jne 0x4e6617` (0x4e6603) —
  when the transport-state bits ARE set the code falls through to the +25 test; `test [u+25],1<<fac
  / je 0x4e663c` (0x4e6612) **skips when the bit is SET** (x86 `test` sets ZF on nonzero AND);
  `test [stance],3 / jne 0x4e663c` (0x4e6630) skips when relation bits 0-1 occupied. So |=8 fires
  iff: foreign ∧ ¬(w18&0x440==0x440) ∧ ¬(b25 bit fac) ∧ (stance&3==0). (M53q1's "and" chain was
  right; my transcription inverted the +25 term once.)
- **Order-3 test (VERIFIED):** `FUN_005a6330(u,9,3,-1,-1)` = "u or its +50 chain carries order byte
  3" (NAMED.md:156); case 9 compares `+17`. Model: `unit(u)["order"]==3`.
- **`FUN_005a5c00` is NOT identity here (VERIFIED, asm 541515-541525):** identity returns require
  `arg<0` or `*(0x920434)==0`; live `0x920434 = 0` (probe) ⇒ full body: if `+48<0 ∨ +50<0` return arg,
  else rescan same-tile units and return the +50 head (asm 541560-541596). Equivalent to the head of
  the tile stack; model uses the linear-scan head (same result on the probe's data).
- **`FUN_005ab130` (VERIFIED, asm 548632-548694):** tile record `+8` bit 1 (occupancy) → return the
  record's list head; else linear scan for `+0==x ∧ +2==y` then the +50 walk to the head; -1 if none.
  Model implements the scan path (INFERRED-equivalent while the occupancy bit is consistent).
- **Hex distance (VERIFIED, asm 0x4e6733-59 / 0x4e6874-8f):** `mx − (((manhattan>>1) − mn + 1)>>1)`
  over wrapped deltas (wrap correction via abs() + `cmp eax,0x692184` fold; NAMED.md:218).
- **Dead `=1` site re-confirmed:** only 0x4e63e8 stores 1 and only at byte offset ≥ 0x54 (index ≥ 21);
  the only reference to 0x8f0d20+ is the mask-loop bound `cmp eax,0x8f0d20` (asm 298606).

## 3. THE HEADLINE: the fresh filter clears NOTHING — and the stale global was never the filter
Direct check (fresh dump, `evidence/m53q_maskcmp.py` + recheck): for **all 76 rows**
`pool(=d78) & fresh_mask == {bit 0 only}` — the fresh mask never intersects the stored pool, so
`d78 & (~fresh|1) == d78` everywhere. The fresh mask differs from the stale global 0x101 on 76/76
rows (e.g. idx 27 fresh 0x1cda4b), and the 20 pools that carry bit 8 have bit 8 **allowed** by
their own fresh mask (idx 1 pool 0x20b2d ∋ 0x100, fresh 0x144001 ∌ 0x100).
Empirical tie-break (VERIFIED): the game's stored processed for idx 1/69 KEEPS bit 8
(mask_in == processed == 0x20b2d / 0x818ad) ⇒ the game's entry filter did not clear bit 8 ⇒ the
filter mask was the per-base fresh mask (which allows step 8), NOT the stale global 0x101 (which
blocks it). The model's `--stale-mask` path coincidentally matches because it skips filtering
entirely; the census outputs of both paths are byte-identical on this dump
(`evidence/m53q_census_new.txt` vs `--stale-mask`: empty diff over the 76 idx rows).
**Consequence (VERIFIED by census):** `base+0x78` IS the per-base scan pool, the entry filter is a
no-op in practice, and the model's pool selection was already right for 65 rows. The M53p
"stale-global contamination" framing is superseded: there was no contamination because the filter
never bit.

## 4. Re-measured census on THIS dump (was 46 sc / 7 residual when session 68 wrote NEXT_PROMPT)
`evidence/m53q_census_new.txt` parsed with `evidence/m53p_swap_parse.py`:
**76 rows, 65 self-consistent, 54 exact, 11 residual; cell mismatches bc 11 c0 9 c4 21 c8 0.**
- Residuals (sc, pool right, vector wrong) — **all c4-only**: idx 1(f1,−1) 3(f4,−3) 5(f7,−2) 8(f1,−2)
  30(f4,−2) 34(f4,−2) 46(f1,−5) 51(f1,−3) 60(f4,−2) 62(f1,−1) 69(f3,−1). Faction set now {1,3,4,7}
  (was {1,3,4}); membership moved round to round as NEXT_PROMPT predicted.
- **idx 31 (the session-68 "fac2 bc −1" residual) collapsed to EXACT** on this dump (mask_in ==
  processed == 0x149f5, all four deltas 0 — census line 156).
- The 11 NON-self-consistent rows are **all fac 2** (37,40,42,44,52,55,58,61,64,70,72,
  `evidence/m53q_nonsc.py`): same-cardinality step-SET mismatches — e.g. idx 44 pool 0x1d, model
  processed 0x1b (drops step 4, the highest index when budget runs out), stored 0x1d (the game kept
  step 4 and dropped step 2). The scan budget is right; the **iteration/selection order** differs —
  a scan-order question, not a mask question (the fresh filter clears nothing, §3).

## 5. Done-criteria scorecard
"76/76 self-consistent" NOT reached: 65/76. The 11 failures are the fac-2 scan-ORDER rows (§4) —
no mask semantics can fix them (the filter clears nothing). "residuals re-measured": DONE (§4: 11
c4-only residuals, idx 31 collapsed to exact). "computed mask vs live mismatch reported before the
residual theory": DONE (§1: bit 8 / step 8 / tile (45,9), foreign-stack test — the one slot where
the computed table disagrees with the live table on the live cur base). The decode→implementation
step is complete; the remaining stories are (a) the fac-2 scan order, (b) the c4-only residuals —
queued as M53r.
