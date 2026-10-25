# Session notes archive — sessions 75-75

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 75 (2026-10-24) — M53s: **THE 11 c4 RESIDUALS ARE NOT A SCAN PROBLEM AT ALL — the rebuild model matches the game's own visit-time snapshot on 76/76, and the delta is an ALLIANCE ENERGY SHARE that FUN_004eaa10 folds into base+0xc4 at 0x4eac57-0x4eac62 after 4e78e0's history shift** — `evidence/m53s_findings.md`, `scripts/m53s_c4watch.py`, `scripts/m53s_c74_watch.py`, `evidence/m53s_probe.py`
- **The leverage nobody had used (VERIFIED):** `4e78e0`'s exit shifts a history window
  (`0xac<-0xbc, 0xb0<-0xc0, 0xb4<-0xc4, 0xb8<-0xc8`, asm 0x4e8b39-0x4e8b54), so
  `base+0xac/0xb0/0xb4/0xb8` is the vector **at the visit's exit**, immune to every later
  writer. `evidence/m53s_probe.py`: model == that snapshot on **76/76 rows, all four fields**.
  The 11 residuals were therefore never a yield/neighbour/`0x8f0c4c` question — the rebuild is
  complete; the model just stops where the game's rebuild stops.
- **Energy-only, post-snapshot (VERIFIED):** `c4_now - c4_prev == -delta` on exactly the 11
  rows (gains 1,3,2,2,2,2,5,3,2,1,1) while `+0xbc/+0xc0` change on **0/76** rows visit->visit.
- **Writer, caught live (VERIFIED):** hw watchpoints on base46+0xc4 (0x961174) and base3+0xc4
  (0x95de64) across the driven round 2384->2385 (`scripts/m53s_c4watch.py`): base 46's writes
  end at **17** from 0x4e85c1 (= model = `base+0xb4`), then **0x4eac68 writes 20 then 22**; base
  3 ends at **12**, then **0x4eac68 writes 15**. Site = `mov ecx,[eax+0xc4] / add ecx,esi /
  mov [eax+0xc4],ecx` at 0x4eac57/5d/62 in **FUN_004eaa10** (eax = DAT_008f0d60), which runs
  right after 4e78e0 in every pass of the per-base turn processor FUN_004f5a70 (0x4f5ac8->
  0x4f5ad7, 0x4f5b3c->0x4f5b4b, 0x4f5c55->0x4f5c64).
- **The obvious candidate is dead (VERIFIED):** the sibling fold `base+0xc4 += DAT_008f0c74`
  (0x4eaa2e/0x4eaa30) fired **211 times over 74 bases with add = 0 on every one**
  (`scripts/m53s_c74_watch.py`). `DAT_008f0c74/78` are only ever written by `4e8d60`'s entry
  reset (0x4e8d86/0x4e8d92) and accumulate via `inc [eax*4+0x8f0c6c]` (0x4e8e82) /
  `add [ecx*4+0x8f0c6c],eax` (0x4e8f35) — the same slot family that feeds `bc` (0x4e9336/44) and
  `c0` (0x4e944b/59), which is why those two fields show no residual either.
- **Single-writer protocol:** Ghidra `grep '0xc4) ='` over all shards gives, for game records,
  only shard_012.c:17952 (`+= DAT_008f0c74`) and :18010 (`+= iVar5`); machine scan finds **no
  `add [reg+0xc4]` anywhere in .text** and only 7 displacement stores to `+0xc4` total (2 of
  them in 4eaa10; the rest are ctor/UI sites — disproofs in `evidence/m53s_writer_scan.md`).
- **Semantics (INFERRED, cited) + a dump-visible confirmation:** the fold runs once per OTHER
  faction that is allied with the owner (stance bit 2 either direction, `0x94d448+fac*0x20bc+o*4`),
  adds `n = ceil((ally-base energy + my energy)/8)` scaled by `[0x94d734+fac*0x20bc]+1` over
  `DAT_0092a274+1`, halved without stance bit 1, +1 if `DAT_00985bc0 == owner`. In the dump the
  factions with any bit-2 ally are exactly **{1,3,4,7}** — exactly the gain-bearing factions —
  and base 46 (fac 1, allies {4,7}) took **two** increments (+3, +2) while base 3 (fac 4, ally
  {1}) took one (+3). Gains reproduce across a driven round (same 11 bases, +idx 6, idx 51 3->2),
  so this is rule behaviour, not visit-time drift.
- **Driving (this position stalls the stock driver):** the HUD message pane says "nutrients", a
  BASE_WORD, so every frame classifies `base` and `--no-escape > timeout` forbids the clearing
  Escape -> two STUCK runs with zero hits. Worked instead: click the OCR'd `COMPLETE` word
  (697,416) -> "Do you really want to end the turn now?" -> `answer_confirm`; then the Council
  blocks the round (PROTOCOL DIRECTOR OK bar, PROPOSAL vote bars x=311/400/489 y~498 found by
  colour geometry because `tesseract tsv` yields nothing for those labels here, then the HIVE
  bribe pane — Escape closes it, Return advances). Post-drive dump censuses at only 31
  self-consistent rows (fresh-mask/pop have moved on — the M53r signature), so the 76/76
  self-consistency claim belongs to the pre-drive dump (`evidence/m53s_dump1/`).
- **Next:** implement the fold in `m53p_recon_a.py` (read the ally base via `FUN_004ea940`'s
  k-th-nearest rule + the stance/`0x94d4f0`/`[fac-0x244]` zero-gates) and re-run the census —
  the 11 residuals should collapse to exact. Then: why idx 6 joined and idx 51 changed by 1;
  `DAT_008f0d40[other]` consumers; the still-open M53r items.
