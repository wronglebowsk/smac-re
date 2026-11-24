# Session notes archive — sessions 310-311

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-308-308.md` — the hot file cites only THIS archive, so
the chain onward lives here; without this line the older archives are orphans (s292).

## Session 310-chain2 (2026-11-19, M331 CLOSED, STATIC: +2fc/+308 = upkeep INCOME siblings)

- milestone/m331 (main e0b7d0a). **+2fc = per-faction per-turn GROSS ENERGY INCOME accumulator** (noun INFERRED): zeroed 520567; feeder 4eacd9 (FUN_004eaa10) gate ds:8f0d64==1 (phase 1, sole set 4f5b2c): += clamp(base_rec+0xd4, 0, 99999); +0xd4 = +0xc4−+0xf4−4e9880(+0xc4−+0xf4); +0xc4 += 8f0c74, +0xf4 := 8f0c3c (sole stores 4e8d86/97 in 4e8d60). Tail 52080c: +1 per OWNED base in the no-interest fallback. **+308 = secondary income acc**: zeroed 520573; feeder 4f5cb0 (FUN_004f5a70(base_idx), called per owned base @5206d3): += Σ 8f0d40[k−1], k=1..7≠owner, block+0xc0==0 both; ENERGY += base_rec+0xfc @4f5c85-8c.
- Interest lead CLOSED: facprofile+0x4ec = rate%, ENERGY += trunc(E*rate/100) (magic 51eb851f sar5+signfix), gated +0x508 bit14; rate==0 → +1 E AND +1 +2fc per owned base (95da14/985af4 walk).
- Ledger +310:=+2fc, +30c:=+308−300+2fc verified NUMERICALLY 8/8 m54b_clean blocks (v2fc=[0,7,14,4,32,9,9,2], v308=[0,0,0,0,3,0,0,0], v30c=[0,6,13,4,34,9,8,1]); minus-variant dead.
- Caps: 546800 MIN(trunc(E/2), 100×(+2fc−300))≥50 else exit 54b91b (fold DERIVED=100); 535c60 Σ MIN(net, block+1058)×arg3 + trunc(E/5) (66666667). Readers: 522b70 ENERGY+net score; 531df0 920754 meter; 45a920 '{+308}' template; 40e720 via 997b20=HEAP alloc (NONFIELD).
- `python3 -u scripts/m331_ledger_census.py` → **14/14** **442270fd57be2b62** x2 (`evidence/m331_ledger_census.txt:90-91`, `_rerun.txt:90-91`); `python3 -u scripts/m331_mutate.py` → **43/43+1 NO-OP, 0 MISMATCH/CRASH** **29061c567f9132fb** (`evidence/m331_mutate.txt:48-50`); ST 5/5 (`_selftest.txt:6`). Supersedes a9983cddad88fade/75a8749314a13287 (pre-review) + 6b20830198d71116/f69da0b368c0268c (mid-round).
- Review #345 (Strata, `evidence/ai_review/pr345_20261120_022025.md`): **5 P1 + 5 P2, 9 accepted + 1 dismissed** (ACCEPT-row mutant exemption = review_lint L1 meta-rule). ALL fixes STRENGTHEN: owner spill-chain + 8f0d60-context pins (G5); ledger load→store liveness + esi entry→ledger + no-mid-branch (G8); caller loop-index law incl retry-dec (G6); scanners upgraded to ALL store mnemonics + implicit writes (mul/imul/cdq/stos/xchg...) — MU41-43 are the scanner mutants; facprofile id byte-tied to M324 save carry 596ec3/ec8/ed6 (G7); NAMED cites full paths; trim sha1 label fixed (true sha1 429295c00401). MU18/19 first-round + MU36 cascade ({G1,G5}) fixed by pins/declared-set.
- PITFALLS: 8f0d60 = base_rec pointer (M311), NOT a faction profile; 997b20 is heap (5be090) — +308 offset coincidence; 8f0c74's store lacks DWORD PTR prefix; mov-only slot/store scanners miss add/shift writes (review #345).
- OPEN: income nouns; 4e9880 formula; 8f0d40 law; block+0xc0/+304; what the ≥50 cap gates; 920754.

## Session 311 (2026-11-21, M332 CLOSED, STATIC zero box) — `ds:0x985aec` = the runtime MIRROR of the win-INI pref `"Difficulty"`

- m332 off main (B27 `1db42cf`, M331 `aeb02bf`); pick (x2); addresses in `## M332`.
- ANSWER: FUN_0058e7f0 is the private-profile READER (a 6-arg `GetPrivateProfileStringA` per preference) and the `"Difficulty"` window stores exactly ONE key-exclusive field (`ds:0x92bde8`); FUN_0058f0d0 is the WRITER (8 argc-4 pushes == the 8 `WritePrivateProfileStringA`) and pairs that key with the cell's load. All 4 stores of 0x985aec are `a3` moffs: 2 copy the master, 1 `movsx`es the byte cell 0x8f0c11. By-product: the pref table = 11 injective name->field pairs in `0x92bde8..0x92bf14`; `## M328`'s "mode global" `0x92bdf8` = `Top Menu`.
- IN PLACE: `## M308`'s "0x4ddcf1 UNATTRIBUTED" closed: no fall-in (prev = `ret`) but branch-entered by a `jge` whose eax is callee 0x5f1394's return; 0 image-wide LE-dword entries at any site. RIVAL KILLED (G8): the cell is ALSO exactly the end of the 4x0xd4 array at 0x92ba98, so "array sentinel, mirror by coincidence" fails — the cell has 2 stores/6 loads, the sentinel 0.
- ACCEPT `python3 -u scripts/m332_difficulty_census.py` -> `PASS M332: 8/8 gates` digest `c722bc1eca0b6405` (`evidence/m332_difficulty_census.txt:86-87`, 3 runs identical); HARNESS `python3 -u scripts/m332_mutate.py` -> `PASS HARNESS 18/18` (16 scored + 1 NO-OP, 0 MISMATCH/CRASH) digest `f101d888d93c5272` (`evidence/m332_mutate.txt:19-21`); `--selftest` 5/5.
- PITFALLS: (a) objdump prints a jcc target as the WHOLE operand string — `dst,src=split_ops(ops)` puts it in `dst`, so reading `src` finds ZERO branch targets and all 4 live stores looked unreachable. (b) a byte-level `find()` of a LE displacement also hits a `call rel32` whose offset is that value (enc 11 vs text 10 for 0x92bde8) — scanners must be able to DISAGREE. (c) the anchor IS the law: reader's store FOLLOWS its call, writer's load PRECEDES its push (MU15 -> G6+G7). (d) `0x92bde8..0x92bf14` is ONE struct, not 11 globals.
