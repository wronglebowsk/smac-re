# M53s — the 11 c4-only residuals are a POST-REBUILD ALLIANCE ENERGY FOLD (rule, not drift)

Dump provenance: every number below comes from `evidence/m53o_mem/` refreshed by
`python3 scripts/m53o_mem.py` on 2026-10-24, pid 2124624 (Wine, terran.exe), plus the census
`evidence/m53s_run0.txt` (`scripts/m53p_recon_a.py $(seq 0 75)`, baseline reproduced exactly:
76 rows, 76 self-consistent, 65 exact, 11 c4 residuals = idx 1,3,5,8,30,34,46,51,60,62,69,
cells bc 0 c0 0 c4 11 c8 0) and the driven-round dump in `evidence/m53s_run1.txt`.
Pre-drive snapshot kept at `evidence/m53s_dump1/`.

## F1 VERIFIED — the model already reproduces the rebuild's own visit-time output, 76/76
`FUN_004e78e0`'s exit block shifts a history window before it returns (asm
`evidence/m53o_fn4e78e0_asm.txt` A:1414-1420 = 0x4e8b39-0x4e8b54: `mov eax,0xac / add eax,4 /
cmp eax,0xbc / mov edx,[eax+ecx+0xc] / mov [eax+ecx-4],edx / jl`), which copies
`0xac<-0xbc, 0xb0<-0xc0, 0xb4<-0xc4, 0xb8<-0xc8`. So `base+0xac/0xb0/0xb4/0xb8` is the vector
as of the visit's exit, before any later writer can touch it.
`evidence/m53s_probe.py` on the run0 dump: **"model==history(ac,b0,b4,b8) on 76 rows"** — all
four fields, zero mismatches. => the 11 residuals are NOT a scan/yield rule gap, NOT pop
drift, NOT a mask/budget problem. The rebuild model is complete.

## F2 VERIFIED — the residual is an ENERGY-ONLY gain applied after that snapshot
Same dump: `c4_now - c4_prev == -delta` on exactly the 11 residual rows (gains
{1:1, 3:3, 5:2, 8:2, 30:2, 34:2, 46:5, 51:3, 60:2, 62:1, 69:1}) and `+0xbc/+0xc0` changed on
**0 of 76** rows visit->visit (`evidence/m53s_probe.py`, `raw_ac` vs `vec` in rows.json).

## F3 VERIFIED (live) — the writer is FUN_004eaa10's per-allied-faction fold
Hardware watchpoints on base46+0xc4 (0x961174) and base3+0xc4 (0x95de64) for the whole driven
round 2384->2385 (`scripts/m53s_c4watch.py`, log `evidence/m53s_c4w_watch.log`):
- base 46 (fac 1): write PCs seen 0x4e79a8 (seed store), 0x4e7c19 (scan add), 0x4e7ea7 (scan-0
  special add), 0x4e85c1 (middle-pass add) — the last of which leaves **17**, exactly the
  model's value and `base+0xb4` — then **0x4eac68** writes **20** and then **22** (= stored c4).
- base 3 (fac 4): ... 0x4e85c1 leaves **12** (= model/history), then **0x4eac68** writes **15**
  (= stored c4).
gdb reports the instruction AFTER a store, so the writing site is **0x4eac57 `mov ecx,[eax+0xc4]`
/ 0x4eac5d `add ecx,esi` / 0x4eac62 `mov [eax+0xc4],ecx`** in **FUN_004eaa10** (eax = DAT_008f0d60,
the current base pointer, loaded at 0x4eac4c). => stored `+0xc4` = rebuild value + Sigma(esi).

## F4 VERIFIED (live) — the OTHER fold in the same function is a no-op here
`0x4eaa1b mov ecx,ds:0x8f0c74` / `0x4eaa2e add esi,ecx` / `0x4eaa30 mov [eax+0xc4],esi`
(`base+0xc4 += DAT_008f0c74`) was hooked with an int3 (`scripts/m53s_c74_watch.py`, log
`evidence/m53s_c74_watch.log`): **211 hits over 74 distinct bases in one round, add = 0 on all
211**. `DAT_008f0c74/0x8f0c78` are written ONLY by `FUN_004e8d60`'s entry reset (0x4e8d86 /
0x4e8d92, eax = 0) and accumulate only via the indexed sites 0x4e8e82 `inc [eax*4+0x8f0c6c]` /
0x4e8f35 `add [ecx*4+0x8f0c6c],eax`; the bc/c0 consumers are 0x4e9336+0x4e9344 and
0x4e944b+0x4e9459 — and bc/c0 gains are 0 on 76/76, consistent with the whole slot family
being 0 at fold time.

## F5 VERIFIED — single-writer evidence (both renderings + machine count)
- Ghidra: `grep -rn '0xc4) =' ghidra_out/shard_*.c` yields, for game records, exactly
  `shard_012.c:17952` `*(int *)(DAT_008f0d60 + 0xc4) = *(int *)(DAT_008f0d60 + 0xc4) + DAT_008f0c74;`
  and `shard_012.c:18010` `*(int *)(DAT_008f0d60 + 0xc4) = *(int *)(DAT_008f0d60 + 0xc4) + iVar5;`
  (the rest are `in_ECX + 0xc4` UI thiscall sites in shards 017-020).
- Machine: whole-.text scan finds **no `add DWORD PTR [reg+0xc4]` anywhere**; the only
  non-stack displacement stores to `+0xc4` are 0x4eaa30, 0x4eac62 (FUN_004eaa10), 0x5ba9d6,
  0x5caebd, 0x5cb48d, 0x5cbf8b, 0x5cccbc (UI/ctor sites — see `evidence/m53s_writer_scan.md`).
  Inside FUN_004eaa10 the `[eax+0xc4]` lines are 7: 5 loads + the 2 stores above.

## F6 INFERRED (cited, read by the writer-scan pass) — what esi is
Per OTHER faction `other` (loop bound `cmp esi,0x1c` at 0x4eac7e, faction-record stride
0x20bc), gated on alliance stance bit 2 in either direction
(`test BYTE [0x94d448+owner*0x20bc+other*4],2` 0x4eab33 / reverse 0x4eab3b),
`faction[other]+0xd54 != 0` (0x4eab47) and `FUN_004ea940(other,k) >= 0` (0x4eab5a, k-th nearest
base of `other` exists); zeroed afterwards by `[0x94d4f0+owner*0x20bc] != 0` (0x4eac33) or
`[faction[other]-0x244] != 0` (0x4eac40) -> `xor esi,esi` (0x4eac4a).
`n = ((base_ally[k]+0xb4 + base+0xb4 + 7 + (sum&7)) >> 3)` (0x4eab79-0x4eab9c, i.e.
ceil((ally energy + my energy)/8), doubled when DAT_00985bd4 < DAT_00985bd0),
`esi = ((([0x94d734+owner*0x20bc]+1)*n + ((count-1)>>1)) / (DAT_0092a274+1))` (0x4eabe0-0x4eabef),
halved when stance bit 1 absent (0x4eabf4/0x4eabfe), `+1` if DAT_00985bc0 == owner (0x4eac19).
Also stored to  `DAT_008f0d40[other]` (0x4eac27). The numerator line is machine-pinned VERIFIED:
  0x4eabe0 `mov eax,[ecx+0x94d734] / inc eax / imul eax,ebx / add eax,edi / cdq / idiv esi /
  mov esi,eax` (ecx = faction-scaled record index, as at 0x4eab33/0x4eac33); one Ghidra rendering
  calls the same field `faction[owner].+0x390` — trust the machine disp 0x94d734.
  4eaa10 runs right after 4e78e0 in every pass
of the per-base turn processor FUN_004f5a70 (call pairs 0x4f5ac8->0x4f5ad7, 0x4f5b3c->0x4f5b4b,
0x4f5c55->0x4f5c64).

## F7 VERIFIED — the alliance gate shows straight through the dump
Stance bytes read from the dump (`facrec.bin`, `0x94d448 + fac*0x20bc + other*4`, bit 2 either
direction): allies(1) = {4,7}, allies(3) = {7}, allies(4) = {1}, allies(7) = {1,3}; factions
0,2,5,6 have **no** allies. The gain-bearing bases' factions are exactly **{1,3,4,7}**. Base 46
(fac 1, two allies) took **two** increments at 0x4eac62 (+3 then +2); base 3 (fac 4, one ally)
took **one** (+3). Gains are reproducible: after the driven round the gain set is
{1:1,3:3,5:2,6:2,8:2,30:2,34:2,46:5,51:2,60:2,62:1,69:1} — the same 11 bases plus idx 6, with
idx 51 3->2. So this is systematic rule behaviour, not visit-time drift.

## Verdict
RULE, not drift. The rebuild model stops where `FUN_004e78e0` stops and is exact there
(76/76 against the visit-time history snapshot); the game then folds an **allied-faction
energy share** into `base+0xc4` in `FUN_004eaa10` at 0x4eac57-0x4eac62, which the model does
not model. Reproducible collapse: bases 46 (17 -> 22) and 3 (12 -> 15) close exactly, with the
per-allied-faction increments visible in the watchpoint log.
Retire: "0xc4/0xc8 have NO downstream writers" (M53o) — `+0xc4` has two, both in FUN_004eaa10.

## Kit added this session
- `scripts/m53s_c4watch.py` — hw watchpoints on two bases' `+0xc4`, logs pc + new value (the
  decisive tool; arm/stop via pidfile, never signal by name).
- `scripts/m53s_c74_watch.py` — int3 on 0x4eaa2e logging idx/c4pre/add/c74/curidx.
- `evidence/m53s_probe.py` — history-snapshot comparison + "which base-record field equals the
  gain" sweep (answer: none).
- `evidence/m53s_endturn.py`, `evidence/m53s_barclick.py` — driving notes: the stock driver
  stalls here because the HUD message pane contains "nutrients", a BASE_WORD, so every frame
  classifies as `base` and `--no-escape N>timeout` forbids the Escape that would clear it (two
  STUCK runs, 0 hits). What works: click the OCR'd `COMPLETE` word (697,416) -> "Do you really
  want to end the turn now?" -> `answer_confirm` (Yes row then OK bar; Return alone keeps "No").
  The Council phase then blocks the round: PROTOCOL DIRECTOR OK bar, PROPOSAL vote bars measured
  at x = 311/400/489, y ~= 498 (found by COLOUR GEOMETRY — `tesseract tsv` returns nothing for
  these labels on this build), then the HIVE bribe pane (response bar y ~= 220; Escape closed
  it, Return advanced).
- Census caveat: the post-drive dump censuses at 31 self-consistent rows (fresh-mask/pop inputs
  have moved on from the visit-time values — the M53r drift signature); use the pre-drive dump
  for the 76/76 claim. model==history still holds where the scan reproduces (5,30,60,69).
