# Session notes archive — sessions 63-63

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 63 (2026-10-26) — M53k: **base+0xd0 HAS EXACTLY ONE WRITER — `FUN_004e93f0` (d0 = c0 − f0 − e0, called per base from inside the turn processor 0x4ef6d0) — THE ONLY PER-TURN base+0x40 WRITER IS INSIDE `FUN_004ef6d0` (income add 0x4ef7f6 / unit spend / project spend 0x4f0ca6 / drain 0x4f1e3f) — AND THE ARM IS: STOCK minerals ≥ FULL price gates completion (no accumulation); the race scan runs ONLY for OUT-of-mask bases and defers them while a funded in-mask rival races the same head; clamp B resets in-mask payers to max(0,min(10,d0))** — write-up `evidence/m53k_findings.md`
- **+0xd0 (net income):** machine stores 0x4e9557/0x4e957f in FUN_004e93f0 (`eax=ds:0x8f0d60`;
  d0 = [eax+0xc0] − [eax+0xf0], [eax+0xe0] zeroed first; mirror +0x94; f0 = DAT_008f0c38+
  DAT_008f0c4c; c0 += DAT_008f0c70; +0x48 normalized `>>3`). Called from 0x4ef6d0's base loop
  (shard_012.c:20861/22171) + 4ee410/4f5a70/founder. +0x48 = raw accumulator (+= at 4e78e0+
  0x1455; 58 live stores to Colony+0x48 in one turn). Live: Colony d0 13 = 13−0−0; U.N. 9 =
  12−3−0; d0 changed 17/75 in 1 turn.
- **+0x40 (minerals):** income add 0x4ef7f6 (`minerals += d0`, gated d0≥0 ∧ head≠−38 ∧
  +0x30&2) — LIVE WP21 `eip=0x4ef7f9 new=301` Colony 288→301; the only +0x40 hit that turn.
  Clamp B 0x4f0cc3-0x4f0ce9: post-pay minerals > min(10,d0) AND in-mask → := max(0,min(10,d0))
  — explains M48's pinned-zero ours (d0 = −1). Event writers: 4cce50 trio, 4e47d0 founder,
  585720/58fa40/507ef0/... (census `m53k_ptr_stores.txt`).
- **Arm rule (machine-verified):** gate 0x4f0a3d `cmp minerals, edi; jl return`; price =
  4e40a0 × table cost factor; **FUN_004e40a0 = 10 for in-mask factions but (era table − adjs)
  for out-mask — CAN BE 0**; race scan (0x4f0af0, gated 0x4f0ac6 to out-mask currents) keeps
  in-mask same-head bases and returns unpaid if any has d0+minerals ≥ price. Progress +0x3c
  (+= [base+0xcc] at 0x4ee8c7 in FUN_004ee410, LIVE WP22 50→56) is DISPLAY only (announce
  0x4efd49). Mask 0x985b10 = 0xff08 = {3, 8..15}: ours in; factions 0,1,2,4,5,6,7 out.
- **Case study (VERIFIED):** U.N. Disaster Relief (fac 7, out-mask) completed Aerospace
  Complex turn 2373→2374: bitmap bit29 flipped, minerals 16→25 = +income only, ZERO pay
  (price 0), clamp skipped — resolves M53j's "debits full price" tension.
- **Method:** read-only `/proc/pid/mem` TSV snapshots (`scripts/m53k_snap.py`) across turns
  2371→2375 + two gdb watchpoint runs on The Colony (idx 23 = 0x95f560 — the 0x95f568 in the
  first run was +8 wrong: 23×0x130 = 0x1b50) + cached disasm. Snapshots:
  `evidence/m53k_{pre,post1,post2,post3}_turn.tsv`; logs `m53k_watch{,2}.log`.
- **Next:** **THE PICK = M53l** (production inputs: writers of +0xc0/+0xcc and what feeds
  4e78e0's +0x48 accumulator; mask 0x985b10 + era table DAT_0068cbb8 semantics).
