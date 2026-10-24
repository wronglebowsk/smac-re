# `FUN_004e78e0` — production-vector rebuild: scan + middle-pass machine rules

Rebuilds `base+0xbc` nutrient / `+0xc0` mineral / `+0xc4` energy / `+0xc8` psi IN PLACE on the base record
(`esi` = `DAT_008f0d60`, records at `0x95da10`, stride `0x130`). Cites `A:NNN` = line NNN of the function's
extracted objdump-intel window (regenerate: `zcat evidence/m53j_text.txt.gz | awk '/^  4e78e0:/{f=1} /^  4e8d60:/{f=0} f'`);
source is `objdump -d -M intel --section=.text programs/terran.exe`, VA = file offset + 0x400000.
Models: `scripts/m53o_recon.py` (36/76 bases exact), `scripts/m53p_recon_a.py` (50/76; its `mp_best` is the
middle-pass candidate scorer). Yield dispatch `FUN_004e75f0(field, fac, bidx, x, y)` -> `4e6960` nutrient /
`4e6d40` mineral / `4e7070` energy / field 3 = 0 and clears `DAT_008f0cc8`; per-tile values = alpha
`#RESOURCEINFO` verbatim at `0x926bd8` (9 categories x 4). Seed store `0x4e79a5` reads
`0x94dc34 + (fac*0x82f + field)*4` (faction records `0x94ae14 + fac*0x20bc`) — live zero for all 8 factions,
so the seed contributes nothing.

## Stack frame (pinned from the disassembly, not from pseudocode local names)

| slot | role |
|---|---|
| `[ebp-0x8]` | processed-mask accumulator: 0 at entry (A:32), scan ORs `1<<s` (A:183), add commit ORs `1<<idx` (0x4e84f3), swap/undo rewrite it (0x4e8650 / 0x4e8870); reaches `base+0x78` only at exit 0x4e8b19 |
| `[ebp-0xc]` / `[ebp-0x28]` | best-ADD index (init 0) / best-ADD score (init 0) |
| `[ebp-0x44]` / `[ebp-0x48]` | best-SWAP score (init 0x270f) / best-SWAP index (init -1) |
| `[ebp-0x50]` | swap-mode ? 0 : accumulator — the candidate gate's exclusion set (set 0x4e8004) |
| `[ebp-0x54]` | the CURRENT candidate's own `1<<j` (stored 0x4e8021; `test` left eax intact) |
| `[ebp-0x58]` | swap-mode flag |
| `[ebp-0x4]` / `[ebp-0x2c]` | candidate `j` / loop cursor (reads `0x678510 + 4*(j-1)` = spiral XOFF[j]) |

## Entry, budget, scan

- Entry: `base+0x30 &= 0xffff7fff`; `base+0x80 = 0`; `base+0x78 &= (~DAT_008f0d30|1)` (0x4e7968-72, live
  `DAT_008f0d30 = 1`, so bit 0 always survives — NOT `~(pop|1)`).
- Skip flag `[ebp-0x30]` = 1 iff tile out-of-mask OR (bit6 AND bit31 of `base+0x38`).
- **`DAT_008f0c68` IS the loop budget** (prologue store 0x4e7904, decremented per scan A:255 and per add
  commit 0x4e85d8, published to `base+0x7c` at exit A:1414). It starts at `pop+1` and is spent on every scan
  INCLUDING out-of-bounds ones.
- Scan skip gate A:165: if budget < popcount(`base+0x78`) jump straight to the main pass (accumulator stays 0).
- Scan loop s = 0..20 over spiral XOFF@0x67850c / YOFF@0x678990 (mask bits 32..79 alias 0..15); an s already
  in `base+0x78` is skipped WITHOUT spending budget (A:176).
- `if (DAT_008f0c68 == base+0x80 + base+0x7c) goto LAB_004e8a47` (A:139) skips the scan-0 special AND the
  whole middle pass.
- Exit: `base+0x78` = accumulator (0x4e8b19), `base+0x7c` = `DAT_008f0c68` (A:1414), `base+0x30` clears
  **bit 8 only** (A:1418 — an earlier note's `&= ~0xfe00` was imprecise), history shift `+0xac <- +0xbc`.

## Middle pass: enumeration, pair dispatch, acceptance

- Outer header 0x4e7fbc. Swap mode = `DAT_008f0c68 <= base+0x80 + base+0x7c` (`cmp`/`setle` 0x4e7fd1-6).
- Tile candidates: fixed spiral j = 1..20 (offset 0 = the base tile is the scan-0 special's job), A:540-796.
  **The only gates are** `skip if (1<<j) & ((swap?0:accumulator) | DAT_008f0d30)` (A:540-547) and map bounds
  (A:549-573, wrap only if `0x92a394` bit0). No owner / terrain / level / facility-bitmap / tech / distance
  filter exists in the loop (clean negative) and no chooser is called: `FUN_00496ad0`, `DAT_009267e4` and its
  count `0x9267e0` are never referenced here. Terrain byte 0 is used only to OR bit 15 into `base+0x30`.
- The three yield functions are called as SCORERS (A:582/594/605), not as gates.
- **Pair dispatch (0x4e82bf-0x4e82ce):** `test accumulator, [ebp-0x54]` where `[ebp-0x54]` = `1<<j` — a
  candidate whose ring bit is ALREADY in the accumulator (claimed by this visit's scan or an earlier add)
  updates the SWAP pair (strict `<`, ties keep the lowest j); every other candidate updates the ADD pair
  (strict `>`). Both pairs can fill in one iteration, so the swap path is live code.
- **Score** (A:706-773 = 0x4e81f9-0x4e82c2): one weighted 3-term integer built from the three yield results
  after the shortage test and the doubling/halving corrections — the corrections are
  `ashr(2*X - pop*(K+1), 1)`, NOT plain halves (A:681-697) — with weights from bits 24..27 of `base+0x38`
  (faction-record fallback when bit31 is clear) and divisors from `base+0xc0/+0xc4/+0xc8` clamped 1..99.
  Because the vector is rebuilt in place, those operands are the PARTIAL vector mid-execution: feed the
  model's own running sum, not the live post-rebuild values.
- **Dispatch 0x4e8458:** swap flag != 0 -> swap branch 0x4e8616; else best-add index < 0 -> nibble branch
  (writes facility entry `-idx-1` into the `base+0x84` nibble slot `base+0x80`, `base+0x80++` at 0x4e84c3,
  NO budget decrement); index == 0 -> exit; index >= 1 -> add commit (mask OR `1<<idx` 0x4e84f3, budget--
  0x4e85d8).
- **Swap commit guards (0x4e8616-0x4e8631), each exits uncommitted:** best-add index > 0; **best-add score
  strictly greater than best-swap score** (0x4e8624 `cmp` / 0x4e8626 `jle`); best-swap index > 0. Then swap
  out / swap in; the undo fires only if `base+0xbc` is still short (0x4e8856-0x4e886a).
- Continuation (0x4e85ef-0x4e8611): loop again iff budget > `base+0x80 + base+0x7c` **OR** `base+0xbc >
  (pop+1)*DAT_0092a27c` (K, live 2). The swap branch always breaks out.
- Facility tail loop (A:797-892): fixed 8 entries of 28 B at `0x926ca8` (bounded by the end ADDRESS
  `0x926d70` — `0x926ca8` is entry 0's techA field, live -1, NOT a count). Entry: +0 techA, +4 techB, +8
  yieldX, +12 value0, +16 yieldY, +20 yieldZ. Loop gates: skip-flag != 0, pop >= 5, nutrient > pop*K or
  best-food == 0, and `DAT_00985afc > 100`; per entry `FUN_005a6cd0(techA, fac) != 0` AND
  `FUN_005a6cd0(techB, fac) == 0`. Its argmax sets best-add index to `-(k+1)`. Exit refill (A:1352-1409)
  fills nibble slots `[base+0x7c, budget)` with argmax of `value0*3 + (pop >= 5 ? yieldX+yieldY : 0)`;
  `FUN_004e3c80` is the same argmax, not a RNG. Pre-scan nibble repair (A:118-157, runs iff skip-flag != 0
  and `DAT_0091c628 == 0`) counts invalid nibbles into `base+0x80` and then does `base+0x7c -= base+0x80`
  BEFORE the budget arithmetic.

## Gating globals that are scenario constants (do not model them as visit-time state)

**NOT constants (M53p correction):** `DAT_008f0d30` (the entry blocked-step mask) is rebuilt at EVERY
`FUN_004e78e0` entry — `FUN_004e63b0` is the first call (0x4e78e9), writes the 21-entry table
`0x8f0ccc..0x8f0d1c` with flag values 0/1/2/4/8 (0x4e63e8, 0x4e6442, 0x4e6518, 0x4e6533, 0x4e6563,
0x4e659f, 0x4e6635) and then sets `DAT_008f0d30 = {bit i : table[i] != 0}` (0x4e6925-0x4e694f). Live
moved 1 → 0x101 between two snapshots of the SAME idle turn, and `0x91c628` moved 0 → 1 in the same
window, so neither is safe to treat as visit-invariant; `0x8f0c4c` (score denominators 0x4e821f-0x4e8231)
has the same problem.

`0x985b48` (compared against the base INDEX inside `FUN_004e7070`) has **no store anywhere in `.text`** — its
only reference is the `cmp` at 0x4e74e9. `0x985bc0` (compared against the FACTION) has exactly one store,
0x425fc3. Both are scenario/save-loaded, so neither can differ between visits. Live: `0x985b48 = 4`,
`0x985bc0 = 2`, `0x985db8 = 0`, `0x985dc4 = 0`, `0x91c628 = 0` (so the energy x3 multiplier and the -1
modifier in `FUN_004e7070` are dead in this game), `0x92a27c = 2` (K), `0x92a2a4 = 5`, `0x92a378 =
0x92a37c = 80`, `0x92a394 = 0` (no wrap), `0x692184 = 40`, `0x985afc = 281`, `0x68cbb0` = current base index.

## Energy `+1` inventory (`FUN_004e7070`, args `(fac, bidx, x, y, flag5)`)

Every per-tile `+1`, all of them already implemented in the model's `y2` (re-confirmed M53p: an
independent reimplementation of `FUN_004e7070` disagrees on 0 of the mask tiles of all 76 bases) — so a
c4-only residual is NOT a
missing yield branch: the neighbour loop (`rec+8 & 0x800000` and `rec+7 == owner byte of the current base`);
base facility bit 1 (raises the `DAT_00926bf0` base value); facility bit 3 OR bit 0x1a (`+ DAT_00926c20`);
`DAT_00985bc0 == fac`; terrain `+0xc` bit 0x80 on land; `FUN_005831a0(x,y) == 3` (`+ DAT_00926c00`); the `uc`
bit-pattern test (`(uc & 0x80000002) == 2 && (uc >> 0x18) < 9`, or bit 3, or bit 10, or bit 11);
`DAT_00985b48 == bidx`; `1 < facrec[0x94d67c] + (base+0x30 bit 2)` — with `facrec[0x94d67c]` =
{0,-2,0,0,1,0,0,0} this can only fire for faction 4 on a bit-2 base; the cap-2 spill to `DAT_008f0cc8`; and
the `LAB_004e7586` modifiers (`+1` if `base+0x34 & 0x2000`, `-1` if `& 0x4000` and value != 0, `-1` if
`DAT_00985db8`, x3 if `DAT_00985dc4 & (0x91c628 ? 2 : 1)`).
