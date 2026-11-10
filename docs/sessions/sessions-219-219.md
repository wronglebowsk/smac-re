# Session notes archive — sessions 219-219

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 219 (2026-11-10, ANALYSE static, M278 PASS 7/7) - block 0 = the player-index-0 real row + the unowned fallback; neither neutral nor player slot
- s218 pick (a) (static, ZERO box time): the two 0x94eaa8 writers' block-index source.
  `python3 scripts/m278_block0_semantics.py` -> **SUMMARY M278: 7/7 gates PASS** (`evidence/m278_block0.txt`).
- ANSWERS: both block atoms are OWNER-PLAYER bytes, not loop counters. writer1 (FUN_0051dcb0,
  inc 0x51df61): ebx = BYTE[0x95da14+304*i] = base+4 (i = the index FUN_004e37f0 returns from its
  base-table walk: mov ebx,0x95da14/add ebx,0x130/count ds:0x985af4) - M43's identity, 167/167.
  No qualifying base -> -1 sentinel -> **clamped to 0** (0x51df1d-0x51df24, the only ebx test, its
  jge targets the FOLD) - block 0 also receives UNOWNED tiles' aggregates. writer2 (FUN_0055f650
  AI hub, add -10 0x564ab1): esi = [ebp-0xc] (ONE store, 0x55f71d) = BYTE[52*arg+0x933286] =
  unit+14 OWNER of the acting unit; the entry cross-checks it against ds:0x91b5b4 (current player).
- DOMAIN + DISCRIMINATOR: the family spans exactly 8 blocks (sweep 0x94eca8->0x95f288 steps
  0x20bc=8380 8x; min/max loop esi 0..7). Guard-attributed branch census: exactly 3 conditional
  branches in FUN_0051dcb0 are keyed on ebx and NONE skips the store at ebx==0 - the rival
  "block 0 is neutral" model needs that guard or a +1 bias; NEITHER exists. The human was not
  block 0 either (M43 recorded cur=3, player 0 = destroyed-but-visited faction owning 199 tiles).
- INSTRUMENT LESSONS (now in the skill): (1) slicing a script by "def main(" to reuse it cuts
  m277's own exec STRING (it contains the token) - anchor "\ndef main("; exec-reuse NESTS the
  namespaces (dst_regs = _ns["_ns"]["dst_regs"]); (2) a bare "## M277" header token occurs TWICE
  in NAMED.md (cross-reference) - registry checks must anchor the FULL header line; (3) an `and`
  chain ending in a re.Match poisons sum(res) - bool() every regex clause before gate().
- OPEN: static picks (b) row-family layout (0x94e8a8/0x94e5a8/0x94e7a8) and (c) who reads regions
  >=128; box pick (dialog +0x4c dispatcher) unchanged. `python3 scripts/track_mode.py` next fire.
