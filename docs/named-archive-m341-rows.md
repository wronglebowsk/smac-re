# NAMED archive - M341 headroom rotation (s321-chain2): the M338 block VERBATIM
(moved by `scripts/m341_named_rotate.py`; the region's sha1 is pinned to `b82cddad74c849a0616ea0365ae620a8f44753c4` -
run `--verify` after any edit; NAMED.md's stub keeps one line per claim)

## M338 (s319-chain2, STATIC 8/8, review #357 hardened) — the LAST two `#DIFF` readers: `0x57c606` is the literal loop counter 0..5; `0x44a1c8` indexes with a hall-of-fame record byte (+0x20) that is the faction's EFFECTIVE DIFFICULTY — `evidence/m338_diff_readers.txt:1`

| claim | line | kind |
|---|---|---|
| table census: `.text` refs to 0x94d2ac = 2 base loads + 7 scaled readers {0x44a1c8,0x484cc9,0x485426,0x48678f,0x486f40,0x57c606,0x599405}, 0 stores; declared==measured both ways | `:1-10` | V MU2,MU11,MU12,ALG1 |
| `0x57c606`: `xor esi,esi` (0x57c604) immediately precedes; the body's only esi write (broad write-classifier) is `inc` 0x57c6ca; `cmp esi,6`/`jl 0x57c606` => 0..5, and the LOADER is read (0x57ac74 mov esi / 0x57ac85 add 4 / 0x57ac88 cmp 0x94d2c4) = the same 6 | `:11-16` | V MU1 |
| `0x44a1c8`: exact 6-instruction window `eax=[ebp-0x1c]`, `xor edx,edx`, scratch clear, `ecx=0x997b28`, `dl=BYTE[eax+0x20]`, `[edx*4+0x94d2ac]`; 0 insns between the byte load and the index; 0 eax clobbers (write-classifier) | `:17-24` | V MU3,MU15 |
| `[ebp-0x1c]` = record of the 35x0x8c buffer 0x983a10: 3 stores only, the 0x4497b7 store's SOURCE is eax, no eax clobber in (0x4497ad,0x4497b7), no bracket-crossing jump; `(8-1)*(1+4)*4 = 0x8c` | `:25-33` | V MU4,MU5,MU13 |
| buffer = `hallfame.jhh`: the fopen WINDOW is `push 0x689f3c; push 0x689f40; call 0x64c980` with PE strings `rb`/`hallfame.jhh`, the read window pushes size 0x1324/buffer/call 0x64cc00, zero-init is the exact 8-insn sequence 35x0x8c to 0x984d34, sibling 0x44adc0 nests 5 per 0x2bc | `:34-41` | V MU6,MU7 |
| field +0x20: the module is MEASURED as the 7 functions that address 0x983a10 (ghidra extents); their union has exactly 2 stores — 0x44b15b from `BYTE[0x94d438+8380*faction]` (fold decoded = 0x20bc, cell = 0x94d430+8) and 0x44b612 a struct copy (scope: a computed-pointer store outside them is not excluded) | `:42-47` | V MU8,MU9 |
| 0x94d438 = the faction's EFFECTIVE DIFFICULTY: the exact 6-insn branch `mov al,ds:0x985b10; test dl,al; mov eax,ds:0x985aec; jne 0x59eed6; mov eax,3; mov [esi+0x94d438],eax`, plus save-load 0x57ef57 (same 8380 fold) | `:48-50` | V MU10,MU14 |
| rivals dead: index is NOT `ds:0x985aec` (0 refs in the chain); 0x983a10 is NOT the faction array (decoded 0x8c vs 0x20bc); 0x57c606's index is NOT stored | `:51-58` | V MU7 |
| ACCEPT `m338_diff_readers.py` -> `PASS M338: 8/8` `1ae1563d47d0039e` x2 (sha256 288a0edc); harness 16/16 `56455db0eadbedd7` (`evidence/m338_mutate.txt:18`), ST 3/3; review #357's 10 findings all fixed IN the gates | `:59-67` | V |
| OPEN: the +0x20 index is UNCLAMPED (a HoF byte >=6 reads past `0x94d2c4`); FUN_0058e7f0 admitting a pref >=6 is now ANSWERED by M340 (ADMITTED, 7/7); 0x44a1c8's window is the HoF screen INFERRED | - | lead |

