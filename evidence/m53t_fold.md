# M53t — `FUN_004eaa10`'s allied-energy share: machine-pinned, implemented

Follows M53s (`evidence/m53s_findings.md`), which proved the 11 c4 residuals were **downstream**
of the rebuild. This note pins the arithmetic and records the implementation in
`scripts/m53p_recon_a.py` (`alliance_fold()` / `census()`), with the acceptance run.

## The store site (VERIFIED)

`0x4eac57 mov ecx,[eax+0xc4] / 0x4eac5d add ecx,esi / 0x4eac62 mov [eax+0xc4],ecx`,
`eax = DAT_008f0d60` — the record whose visit just finished. `FUN_004f5a70` calls the pair
`0x4e78e0` then `0x4eaa10` for every base (`0x4f5ac8->0x4f5ad7`, `0x4f5b3c->0x4f5b4b`,
`0x4f5c55->0x4f5c64`).

## Per-ally term (VERIFIED, 0x4eab02-0x4eac8a)

`other = 1..7`, skipping the owner (`0x4eab04`); `esi = (other-1)*4 < 0x1c` bounds the loop.

- gate A: `stance[owner][other]` bit 2 **or** `stance[other][owner]` bit 2 — `0x4eab33` and
  `0x4eab3b`; the second address walks from `0x94f504 + owner*4` by `+0x20bc` per iteration,
  i.e. `0x94d448 + other*0x20bc + owner*4`, the transpose.
- gate B: `faction[other].+0xd54 != 0` (`0x4eab47`).
- `k` = rank (below); `ab = FUN_004ea940(other, k)`; negative means "no such base" — skip
  (`0x4eab5a`).
- `n = (base[ab].+0xb4 + base[me].+0xb4 + 7) >> 3` (`0x4eab79-0x4eab9c`), doubled when
  `[0x985bd0] > [0x985bd4]` (`0x4eab9f-0x4eaba3`).
- `D = [0x92a274] + 1`, `rnd = D >> 1` (`0x4eaba5-0x4eabbb`);
  `s = ((faction[owner].+0 + 1) * n + rnd) / D`, C truncating division (`0x4eabe0-0x4eabef`).
  `faction[owner].+0` is the machine disp `[0x94d734 + owner*0x20bc]`; Ghidra's `+0x390`
  rendering is the same field.
- `s >>= 1` unless `stance[owner][other]` bit 1 (`0x4eabf4-0x4eac00`).
- `s += 1` when `[0x985bc0] == owner` (`0x4eac11-0x4eac1d`).
- published to `DAT_008f0d40[other-1]` **before** gate C (`0x4eac27`), together with the mirror
  share (built from `faction[other].+0`) at `0x8f0c94[other-1]`.
- gate C: if `[0x94d4f0 + owner*0x20bc]` or `[0x94d4f0 + other*0x20bc]` is nonzero,
  `s = 0` (`0x4eac33-0x4eac4a`). Only this zeroed copy is added at `0x4eac5d`.

### `k` and "k-th nearest" (VERIFIED — it is k-th by ENERGY, no distance exists)

- `FUN_004ea940(fac, k)` collects that faction's bases as `key = energy(+0xb4) << 9 | idx`,
  bubble-sorts descending (`0x4ea95e-0x4eaa00`) and returns `idxarr[k]`, or `-1` when
  `k >= count` (`0x4ea993-0x4ea99e`). There is no distance computation anywhere in it.
- rank = number of the owner's bases whose `(E<<9 | idx)` exceeds
  `(E_me<<9 | [0x68cbb0])` (`0x4eaaa8-0x4eaae2`). `0x68cbb0` is written with the base's **own**
  index at `0x4f5a7c`, so the tie-break is that base's idx — not the turn's last base.

## Acceptance on the pre-drive dump (`evidence/m53s_dump1`)

- before (`--no-fold`): 76 rows, 76 self-consistent, **65 exact**, 11 c4-only residuals —
  `evidence/m53t_run_before.txt:1-12`.
- after: 76 rows, 76 self-consistent, **74 exact**, residuals `{6: +2, 51: -1}` —
  `evidence/m53t_run_after.txt:1-3`.
- **10 of the 11 residuals close exactly** (1, 3, 5, 8, 30, 34, 46, 60, 62, 69); per-row detail
  incl. which ally base each term used: `evidence/m53t_probe.txt:1-16`, `:19-24`.

## Two rows still off (INFERRED — cause identified, not modelled)

- idx 6 (`evidence/m53t_probe.txt:7-8`) takes +2 from ally 1 via base 62; observed +0. idx 30
  (`:11-12`) has the same (fac, energy, rank) tuple and **is** exact, so the difference is not
  in the dump-visible inputs.
- idx 51 (`:17-18`) takes +2, observed +3.
- Prime suspect: `FUN_004f5a70` runs the whole sequence **twice** — after the main pass it tests
  `[0x985afc] > 1` (`0x4f5b14-0x4f5b20`; 284 in this dump), calls `0x4f2ea0`, sets
  `[0x8f0d64] = 1` (`0x4f5b2c`) and re-runs `0x4e8d60 / 0x4e78e0 / 0x4e92c0 / 0x4e93f0 /
  0x4eaa10`; `4eaa10` reads that same d64 at `0x4eac95`. A single-pass model therefore cannot be
  exact on rows where the two passes disagree, and `+0xb4` is stable across the two dumps while
  `+0xc4` moves — so the second pass sees a different record than the first.
- Next probe (one driven turn, two dumps already bracket it: `m53s_dump1` = turn N,
  `m53o_mem` = turn N+1): hw watchpoint at `0x4eac57` logging `(idx, other, k, s)` and a second
  at `0x4f5b2c` to count the passes per base.

## Kit

`python3 scripts/m53p_recon_a.py --mem-dir evidence/m53s_dump1 --census [--no-fold]` — the
acceptance run; `--mem-dir` selects the snapshot (default `evidence/m53o_mem`, the post-drive
one: 31 self-consistent rows, do not use it for the exactness claim).
