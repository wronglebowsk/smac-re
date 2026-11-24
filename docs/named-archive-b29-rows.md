# NAMED archive - B29 headroom rotation (s319): the M334 block VERBATIM
(moved by `scripts/b29_named_rotate.py`; the region's sha1 is pinned to `579f90da7d8cbeefaf218d9249a049bd10b7eef5` -
run `--verify` after any edit; NAMED.md's stub keeps one line per claim)

## M334 (s316-chain2, STATIC, zero box) — FUN_004f47f0's upkeep-FAILURE branch = a DIFFICULTY-GATED AUTO-SELL of one facility from the current base; ENERGY is ASSIGNED the price, not refunded (closes pick (x7); CORRECTS `docs/named-archive-m32-m84e.md:268`)

| claim | evidence | conf / mutant |
|---|---|---|
| after `ENERGY -= cost`/`+300 += cost` (folds DERIVED 48*item, 8380*owner) the fn re-reads ENERGY, tests vs 0 (`xor eax,eax`@0x4f4960 = the zero source), 3-way dispatch: A `cmp [block+0x8],1`→clamp, B `cmp [base_rec+0x50],neg(item)`→clamp, C = sell; both clamp stores take eax and no instruction between the zeroing and either store writes eax | `evidence/m334_powershort_census.txt:4-10` | V MU1-6,MU35,ME2 |
| `block+0x8` = the faction's EFFECTIVE DIFFICULTY: 2 destination-named writers + 0 folded-pointer stores (60-step def walk); create `0x59eed6` = `ds:0x985aec` (human) / imm 3 (AI) behind `mov al,ds:0x985b10`+`test dl,al`+`jne 0x59eed6`, save-load `0x57ef57` = the movsx of edx through `[ecx*4+0x94d438]` with ecx = 2095*eax (×4 = 8380) ⇒ difficulty<2 never sells | `:11-18` | V MU7-9,MU26,MU33,MU38,ME1,ME5 |
| the sell clears the SAME bit the charge tests: both mapper calls take the loop item (charge `push esi`; removal `push ecx` ← `[ebp-0x4]`, the slot the loop bottom writes from esi), both address folds derived 304*base + byte_index + 0x95da9c; clear = `not`/`and`/`mov byte [eax]` | `:19-24` | V MU10-13,MU22-24,MU27,MU28,MU39,ME3 + RIVAL2 |
| `ENERGY := FUN_004e40a0(owner,1,-1) × row[item]+12` — the 48*item fold feeds the imul's base reg, the imul dest = the call result = the store's source (0 eax writes between), args (owner byte from `[rec+4]`,1,-1); MOV store with **0** reads of block+0x220 on the path ⇒ the archived "refund (+=)" is REFUTED | `:25-29` | V MU14-17,MU29,MU30,MU36,MU37 + RIVAL1 |
| announced: `FUN_0048f100(0x68d24c='POWERSHORT',0x10000,0xe,0x68d238='genwarning_sm.pcx',0)` + `FUN_006265a2(1,row[item]+0,-1,-1)` — full cdecl arg lists pinned, the row+0 load's edx unmodified before its push; strings read out of the PE | `:30-34` | V MU18-20,MU25,MU31,MU32,ME6 + RIVAL3 |
| no loop exit after a sale (back-edge 0x4f4a3b→0x4f480b) ⇒ several facilities can go in one round; 2 map-address materializations in the fn, 0 writes to the address reg between the fold and the store; 0 folded refs to block+0x220 (control: 10 folded refs to block+0 image-wide, so the scan is not vacuous) | `:35-39` | V MU21,MU22,MU24,MU34,MU39,ME3,ME4 |
| INFERRED/OPEN: `base_rec+0x50` = queue head (archived live H `named-archive-m32-m84e.md:312`; 51 sites read [R+0x50] with R:=ds:0x8f0d60 incl. 0x4f4994); `row+12` runtime value (39×48 table is .bss, no .text store names it) ⇒ numeric ENERGY outcome; FUN_004e40a0 = ECONOMIC FACTOR (archived H) | `:39` | lead |

ACCEPT `python3 -u scripts/m334_powershort_census.py` → `PASS M334: 7/7 gates` digest `5b5ece39af02baba` x2 (`:56-57`, `_rerun.txt:56-57`); harness `python3 -u scripts/m334_mutate.py` → `PASS HARNESS 45/45` digest `a5a5091e533f7883`, coverage 10/10 (`evidence/m334_mutate.txt:47-49`, `_rerun.txt` identical), `--selftest` 6/6 (`_selftest.txt:8`)

