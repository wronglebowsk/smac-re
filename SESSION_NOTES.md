

## Session 71 (2026-10-24) — M53Q2: **THE SCAN-POOL TABLE IS DECODED — `FUN_004e63b0` writes the 21 entries from 9 store sites with a 6-value vocabulary (2 = off-map/not-visible, 0 = scannable, 4 = terrain test, |=8 unit order, |=0x10 another base's step, |=0x20 foreign presence) and builds `DAT_008f0d30` ITSELF (ret 0x4e6959), which corrects the M53p attribution; the `=1` store is dead (guarded to index >= 21)** — `evidence/m53q_8f0ccc_writers.md` (child decode, 7,966 B) audited in `evidence/m53q_verify.md`
- **Verified by me on the instruction stream (asm line numbers = `zgrep -n` in `evidence/m53j_text.txt.gz`).**
  All 9 sites exist with the claimed immediates: 0x4e63e8 `mov [ecx+0x8f0ccc],1` (:298155), 0x4e6442 `=2`
  (:298184), 0x4e6518 `=2` (:298261), 0x4e6533 `=0` (:298269), 0x4e6563 `=4` (:298284), 0x4e659f
  `or ...,8` (:298305), 0x4e6635 `or ...,8` (:298352), 0x4e6699 `or ...,0x20` (:298388), 0x4e68de
  RMW `mov eax,[ecx+0x8f0ccc] / or al,0x10 / mov [ecx+0x8f0ccc],eax` (:298574-575).
- **Two corrections to standing text.** (1) **The mask build is inside `FUN_004e63b0`, not `4e78e0`**:
  0x4e6925 (`xor edx,edx`, :298595) through 0x4e6946 (`cmp eax,0x8f0d20`, :298606) precedes **`ret` at
  0x4e6959** (:298614) — so the table is built AFTER both passes and `|0x10` bits DO enter
  `DAT_008f0d30`; `NEXT_PROMPT` and `references/production-rebuild.md` are corrected. (2) **Value 1 is a
  decoy**: 0x4e63e3/66 `cmp ecx,0x54 / jl` guards the store, and `ecx` is a BYTE offset (`add ecx,4 /
  cmp ecx,0x54` at 0x4e68e4-67), so it only fires at index >= 21, writing 0x8f0d20+ which nothing reads.
- **Control shape (child, verified at the call site).** `FUN_004e63b0` takes NO arguments
  (0x4e78e9 `e8 c2 ea ff ff` = `call 0x4e63b0`, nothing pushed) and reads its base from `*(0x8f0d60)`
  (x/+0, y/+2, fac/+4) with width `*(0x692184)` = 40; loop A walks 25 spiral byte-offsets (21 real),
  loop B walks all bases 0x95da10/0x130 skipping `[0x68cbb0]`, loop C walks the 21 steps. Spiral tables
  re-verified at DX 0x67850c / DY 0x678990 (25 entries, consumer bound `cmp ecx,0x15`).
- **`0x8f0c68` / `0x8f0c4c`.** 0x8f0c68 is set in the CALLER right after the call: 0x4e7904
  `mov ds:0x8f0c68,ecx` (:300041) = `(int8)*(0x8f0d60+6)+1`, decremented at 0x4e7c36 and 0x4e7ecd.
  0x8f0c4c is NOT written by either function (writers 0x4e8dbc / 0x4e90e0 / 0x4f3063 / 0x4f3110 per the
  child; not re-verified here).
- **What stays INFERRED:** the SEMANTICS of each branch (which visibility bit, order 3 = convoy,
  hostile stance `&3==0`, the dist<=5/<=2 loops) — the child read the branch bodies, I only audited the
  stores and address arithmetic. A computed mask that matches a live `DAT_008f0d30` is the proof.
- **Next:** `NEXT_PROMPT.md` (15,226 B) — **M53q is now implementation, not discovery**: write
  `build_table(base, fac)` into `scripts/m53p_recon_a.py` behind `--stale-mask`, then measure all 76.
