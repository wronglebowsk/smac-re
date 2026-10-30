# The chooser / dispatch state family (mapped statically, no box time)

Derived from the static image only. Use it to avoid re-deriving these; verify with the census scripts named at the
bottom rather than by re-reading disassembly.

## The 8-way dispatch ("which chooser case")

- Site: `FUN_00546800`, 0x54eaeb-0x54eafc. `call 0x542ea0` -> `cmp eax,0x7` -> `ja 0x54ec82` ->
  `jmp DWORD PTR [eax*4+0x54ef34]`.
- Table at **0x54ef34**: `[0x54ed3f, 0x54eb03, 0x54eb03, 0x54eb29, 0x54ec34, 0x54ec40, 0x54ec4c, 0x54ec58]`.
  Cases 1 and 2 share 0x54eb03; case 3 = 0x54eb29; 4/5/6 = 0x54ec34/40/4c.
- **Case 7 = 0x54ec58** — the only case that writes a state PAIR: `ds:0x920700 = 0xc` and `ds:0x92077c = 1`.
- The key `FUN_00542ea0` (1456 B, 341 insns, 28 callees, ONE call site) selects a block-B record:
  `DAT_0099aa1c = (&DAT_00927590)[param_1 * 0x167]`, where the index arithmetic at 0x542ed9-0x542eed folds to
  `359 dwords` and the `shl eax,2` makes it **1436 BYTES** — the same per-faction record stride as
  `0x927a9c + fac*1436`. 0x927590 is block B's .SAV destination, so this array and the record block are the same
  family, 0x50c apart in base.

## State and mode globals

| global | shape | evidence |
|---|---|---|
| `ds:0x920700` | UI STATE code, domain {6, 8, 0xc, 0xd} | 31 refs / 8 writes; comparisons in FUN_00540390; 20 refs in FUN_00544530; case 7 writes 0xc |
| `ds:0x92077c` | MODE code {1, 3, 7} (+6 compared via a copy at 0x54eb1b) | 4 writes (1, 1, ebx, eax), 9 tests; co-written with 0x920700 |
| `ds:0x926bd4` | UPKEEP-SYNCH PHASE {0 idle, 1, 2} | 4 writes / 2 tests; writers bracket the prints "Skipping upkeep synch" (0x68ea94, 0x68eacc); counter 0x91c630 incremented on exit |
| `ds:0x91c630` | upkeep-synch COUNTER (factions that skipped) | 34 refs / 9 writes, 27 in FUN_00521070, `inc` at 0x5213c6 |
| `ds:0x920434` | the ID a window-reset entry publishes — **NOT a faction field** | 634 refs, **0** folded refs; 12 of 15 writes follow `mov ecx,0x91db70; call 0x4e25e0` |
| `ds:0x985afc` | read-dominant run state (meaning unnamed) | 336 refs / 5 writes (one constant 1) |
| `ds:0x94d7fc` | per-faction COUNTER, **-1 = unset** | 47 refs / 8 writes incl. 0xffffffff; `test eax,eax / jl` at 0x5aafd6-0x5aafd8 |

## The two flags that gate a production/flag pass

- `0x92044c` is a **per-record** byte (`[reg*4+0x92044c]`, register holds `tid*13` -> stride 52): 24 refs, all folded.
  `FUN_00546800` proceeds only when the faction dword at `0x94d448` has bit `0x8000000`, `ds:0x920434 != ebx`, and
  `0x92044c` bit `0x2` is set — then it **zeroes** that byte at 0x5469d3. Bit 1 there is a CONSUMED marker, not state.
- `0x94d448` carries per-faction dword flags; `0x94d448+inner*4` bit 0 is what sets bit `0x20` of the entity byte
  `[ebx+0x98adb8]` at 0x531782.

## The list machinery (why a pre-seek read is the PREVIOUS node)

- `FUN_004026b0` (`ret 4`, 201 B) is the **LIST SEEK**: rejects an index >= `[obj+0x10]` (count), walks from the
  current node `[obj+0xc]` forward via `[node+0xc]` / backward via `[node+0x10]`, then stores the resolved index at
  **`[obj+0x14]`** — that field is the post-seek cursor.
- The chooser pump calls it at 0x497717 while the node at `[obj+0xa774]` was already read at 0x497707; the object is
  re-derived (`mov ecx,[ebp-0x10]; add ecx,0xa780`) at 0x49771c/0x49771f, then `call 0x495480` + `and eax,0x20`
  (0x49772a) test the post-seek flag word. So a print at 0x497704 shows the OLD node; 0x49771c is the first
  instruction that sees the new one.
- `FUN_00495480` (21 insns) is a cached-flag **getter**: `if ([obj+8]==0) return 0; else return FUN_004027e0(obj)->[+8]`.
  A 0 from it means "no cache object", NOT "flag clear" — do not read the `and eax,0x20` as a plain bit test.

## Other settled shapes

- `0x984d38` (project table): stride **0x30 = 48 B** at all 52 indexed sites; the "x16" in a listing is `shl 4`
  applied to `3v`, i.e. the tail of the same multiply.
- `0x98adee` ("forced-pick key", live 6): **read-only** — 7 `movsx` readers, 0 writers of ANY width, no access to
  the enclosing dwords, so it is load-time save/scenario data.
- `0x927a78`: 2 refs, both inside `FUN_0059ec90` -> an input of the advance-budget routine, not a shared global.
- `0x94d650` / `0x94d654`: accumulator (261 refs / 34 writes) + per-step companion (13 / 2, zeroed at 0x59f0c1).
- `0x59f0c7`: `mov [ebx+0x94d800],-1` inside `FUN_0059ec90` — the INVALIDATION of the memoized advance threshold,
  right after the accumulator moves; one of its 3 callers zeroes the DIVISOR `[edx*4+0x94e488]` just before.

## Re-prove it with

`python3 scripts/field_census.py` | `scripts/name_global.py <addr>` | `scripts/m124_state_and_memo.py` |
`scripts/m127_m129_fields.py` | `scripts/m130_m132_chooser.py` | `scripts/m133_m142_census.py` |
`scripts/m118_flag_never_set.py` — all offline, seconds each.
