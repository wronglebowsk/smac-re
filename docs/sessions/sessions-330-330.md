# Session notes archive — sessions 330-330

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-329-330.md` — the hot file cites only THIS archive, so
the chain onward lives here; without this line the older archives are orphans (s292).

## Session 330 (2026-11-24) — B33: the OR at `0x4f0ec0` is UNIT-ONLY — the facility leg spends and never stamps

- **ACCEPT** `python3 -u -m sim.facilityleg` -> **`PASS B33: 12/12 gates`** `b89b9e6bd940e8d3`
  (`evidence/b33_facilityleg.txt:65`), rerun byte-identical; relay `--b33` identical;
  `scripts/b33_mutate.py` 11/11 (`evidence/b33_mutate.txt:13`).
- **CENSUS** FUN_004ef6d0 = 3,164 insns, 12,298 B CONTIGUOUS (lengths summed), `0x4ef6d0..0x4f26da`
  == Ghidra `size=12298` read from `ghidra_out/index.csv`; CFG 3,482 edges, 0 external, 0 indirect.
  Fixture: `scripts/b33_extract.py --check` (objdump wrap lines folded into lengths).
- **REACH** entry + unit branch `0x4ef8a4` reach the stamp block `0x4f0e90` (3,045 insns);
  facility branch `0x4efa2c` reaches 886 and does NOT.
- **DOOR** `preds(0x4f0e90)={0x4f0d94}`, `preds(0x4f0ca1)={0x4f0b80}`, `0x4f0b80` = `jg` on
  `[ebp-0x30]`; that local is written at ONE site, `0x4ef8a4` (unit branch), never facility-reached.
- **SPEND** facility `0x4efed8/db/dd` (`[ecx+0x40]`), unit `0x4f0ca1/a4/a6` (`[edx+0x40]`).
- **SCORE** recorded: 4/4 unit heads gain the mapper bit, 0/2 facility-range; Virgin Soil head 2,
  bitmap `00000008..` -> `10000000..` (bit 2 absent, 4 gained, 27 lost), `st` 2 -> 0.
- **RIVALS** shared-OR 4/6 windows (predicts `0400000800000000`), off-map refusal 1/6, after-pop 0/6.
- **RETRACTION (declared gap)** B32's "why a facility head does not stamp" is ANSWERED: the `jg`.
- **PROTOCOL** `scripts/b33_named_rotate.py` rotated `## M333` VERBATIM (sha1 `be87f76187588fde
  4268db6355ba93f44eacc0cd`, 26 tokens) to `docs/named-archive-b33-rows.md`.
- **REVIEW (#381, 7 findings)**: all fixed - MU11 reddens G6; G1 sums byte lengths and reads
  Ghidra's size; G2 pins 3,482 edges; G3 pins the three sets as nested; G4 reads the local from the
  census; G11 asserts the `cmp ebx,0x40`/`jl` split; the parser folds wrapped bytes and marks
  indirect calls `ind`; cites repointed (`:65`).
- **MERGED** #381 as `8cb969b` (squash) after the #381 triage; CI gate pass.
- **OPEN** facility stamp elsewhere (`0x4e4528`/`0x4f3ebc`/`0x4f3f4c`); the `0x98adb8` row; loss 27.

## Session 331 (docs, 2026-11-24) — record the B33 merge; no new milestone taken

- B33 merged as `8cb969b` (#381 squash) on a GREEN verdict after the local review triage; the
  cursor said "PR pending" when it was committed pre-merge, which would send the next fire looking
  for an open PR - it now records the squash hash.
- Archived the #381 review artifacts under `evidence/ai_review/` (they were untracked).

## Session 330-chain2 (2026-11-24) — M356: +0x30 bit 2 = state bit (11 setters, 1 toggler); +0x24/+0x25/+0x26 feed three rule tables

- **ACCEPT** `scripts/m356_prototype_stamp.py` -> **`PASS M356: 17/17 gates`**,
  digest `c1a2beb794cec9f8`, x2 same (`evidence/m356_x2.txt:103`); `m356_mutate.py` ->
  **27/27, NO-OP ['MU29'], coverage ALL 17 gates** (`evidence/m356_mutate.txt:32`).
- **CENSUS** (instruction shapes; last write to the stored register + flags-word load
  provenance): 46 writes to +0x30 (= 0x98adb8); **11 bit-2 setters**, **0 AND-clears**,
  **1 XOR-toggler 0x4396f6** (`xor dx,0x4` @0x4396e6), 0 unresolved register masks, 16 ANDs
  all carrying immediates. First draft said "one-way latch" — the toggler REFUTES it.
- **TWO 0->1 GUARDS**: 0x4d2ff9 load->test->jne-skips-store->OR->store->`call 0x584520`;
  0x4efe60 stores `al|4` then tests the OLD bit, `call 0x572800` only on 0->1; both behind
  `cmp idx,0x40 / jl` (owner band).
- **FEEDS** (`trace_base`): **+0x24 -> 0x92ae80** chassis, stride 0x90, 188 chains; **+0x25 ->
  0x92b950** 21 recs, 181 chains; **+0x26 -> 0x92fd18** 10 recs, 47 chains — exclusive; extents
  DERIVED from each loop (init/stride/bound). Reference census 238/227/11, 94/88/6: every
  non-load reference is a `cmp`, none names a table base.
- **FINALIZER 0x595e80** compares weapon `[0x92b950][+0x25]` with armor `[0x92fd18][+0x26]`
  (`cmp al,bl`) and assigns the +0x2b mode (3/1/4/5/10); flags init 1/0x105/0x115.
- **RIVAL REFUTED**: "+0x27/+0x28 are 0x10-stride ordinals" — 0 table chains either; +0x28 has
  ONE writer (0x595d1c).
- **RETRACTIONS**: (M354) +0x24 is the CHASSIS ORDINAL, not "domain"; (this draft) bit 2 is
  not monotone. A fixed backwards window had attributed a guard `and` to a later store —
  classify by the LAST write to the register (0x4399c5 vs the 0x4399d8 reload).
- **DOC CAP**: `scripts/m356_named_rotate.py` rotated `## M298` VERBATIM ->
  `docs/named-archive-m356-rows.md` (sha1 `a7e25e64`).
- OPEN: +0x27/+0x28 nouns; bit2 UI reading INFERRED.
