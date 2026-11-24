# NAMED archive - M343 headroom rotation (s323-chain2): the M341 block VERBATIM
(moved by `scripts/m343_named_rotate.py`; the region's sha1 is pinned to `bcf9ba24a3eb4efb55182f0b655fcf5f72ab2ad3` -
run `--verify` after any edit; NAMED.md's stub keeps the ACCEPT header + one line per claim)

## M341 (s321-chain2, STATIC 10/10) — the HoF record window is `5*n - 5 + s`: THREE .text sites decode to the same law, so the 35 records at 0x983a10 are 7 blocks x 5 rows and page index 8 lands on the terminator — `evidence/m341_hof_window.txt:1`

| claim | evidence | conf |
|---|---|---|
| SITE A 0x449793/0x449796 `lea ecx,[eax+ebx*4]` + `lea ecx,[ebx+ecx*1-0x5]` decodes to 5*page + slot - 5; inputs exactly [obj+0x59f4] (0x44970f) and [obj+0xa918] (0x449715, spill 0x449728, reload 0x44978d), 0 other ebx definitions | `:2-10` | V MU1,MU2,MU8,MU9,ALG1 |
| SITE B 0x44af9b/0x44af9e = 5*[obj+0xa4c] + slot - 5; the cell's DATAFLOW is read: `mov eax,ds:0x91b5b4` @0x44aecb -> `mov [esi+0xa4c],eax` @0x44aed9 with 0 eax writes between; slot from the rank scan seeded 4 with the `jge 0x44af2b` back-edge (5 probes) | `:20-26` | V MU3,MU11,MU13,MU14,MU15 |
| SITE C 0x44b5a7..0x44b5b9 insert-shift: src index 5n+k-5, dst 5n+k-4 (delta +1); BOTH address chains (*8, sub, *5, *4+0x983a10) evaluate at (n=2,k=3) to 0x983a10+idx*0x8c and the dst = src+0x8c; k in {0..3} from four pushes each followed by `call 0x44b450` | `:11-19` | V MU10,MU16,MU17 |
| extent MEASURED at FIVE zero-init/fault sites: all base 0x983a10 / stride 0x8c / inner 5 / term 0x984d34; 0x1324 = 35*0x8c = 7*0x2bc; {1..7}x{0..4} is a bijection onto 0..34; index 35 = 0x984d34 | `:22-31` | V MU4,MU5,MU6,MU7 |
| NO CLAMP: over the 781,379 parsed insns the only direct 0x59f4 reference is the load 0x44970f; the 12 other hits are the indexed form of a DIFFERENT array (every one `[reg+reg*4+0x59f4]`, printed); 0 cmp/test on ebx between the load and the lea | `:32-33` | V MU8 |
| the 6-iteration loop is COLUMNS: the probes {1,2,4,8,0x10,0x20} sit at the exact addresses {0x449915,0x449985,0x4499f1,0x449a5c,0x449ac8,0x449b34} on byte +1 of the ONE record, and the run has exactly ONE ebx definition — the reload `mov ebx,[ebp-0x1c]` @0x449982 | `:34-35` | V MU12,MU18 |
| rivals dead: 0-based page (indices 35..39), 6 rows/page (36 cells, hi 35), flat list (three sites + k<=3), base 0x983984 (end 0x984ca8 != term) | `:36-40` | V MU1,MU3,MU4 |
| ACCEPT `python3 -u scripts/m341_hof_window.py` -> `PASS M341: 11/11` two runs diff-identical; harness 19/19 `e1c003e81552f53f` (baseline re-run = the NO-OP control), ST 4/4 | `:45-58`, `evidence/m341_mutate.txt:21` | V MU1,ALG1 |
| OPEN: +0x59f4's writer — no named store exists in .text (INFERRED: a control at obj+0x5970); the page's upper bound is therefore not established statically; reading "page 1..7" as faction-block numbering is INFERRED from the shared 5-block law | - | lead |

