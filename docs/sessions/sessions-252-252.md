# Session notes archive — sessions 252-252

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-250-251.md` (inserted at s292: the hot file cites only the newest archive, so without this line the older archives were orphans).

## Session 252 (2026-11-11, STATIC, zero box) - B18 BUILD: the site-gate value source executable

`python3 scripts/track_mode.py` -> MODE=BUILD next_rung=B18 (UNAUTHORED) - the rung was
written by this fire from BUILD_SPINE.md in the B14/B16/B17 pattern. `sim/sitegate.py`
puts M298's three closed semantics on top of B17's decision core: the lazy-nibble CACHE
(`edi = BYTE[rec+2]>>4`; the pinned `jne 0x51dfac` at 0x51df8d runs the 0x5aff90 call AND
the 0x582cc0 write-back ONLY on a zero nibble), the `BYTE[rec+3]` SITE index, and the two
MAX stores (the unconditional 28-B slot at 0x989ce8 and the owner-block cell at
0x94eca8 + 8380*block + site, SKIPPED when the -1 owner sentinel clamps to 0).

`python3 -m sim.selftest --b18 programs/saves/m54b_clean.SAV` -> **PASS B18: 10/10 gates**
(evidence/b18_sitegate.txt):
- G1 62/62 pins resolve and the LAWS are DECODED from the pinned bytes: nibble-split
  write-back; no edi/esi/ebx in the 19-insn callee; BOTH store chains MAX by the
  cmp/jle-over-the-take polarity (a MIN would need `jge`); no cmp/test/branch inside
  0x582cc0; stride 28 from (site*8-site)<<2 with the +4 counter inside the slot (the
  retracted 4x-value stride would alias it onto the next slot's dword).
- G2 the write-back target rec2+2 == the score getter's byte on 4096/4096 tiles;
  8192/8192 (old byte x edi) nibble-law combos; the cache is 4 bits (edi>15 truncates -
  no recorded val reaches it).
- G3 the cache STATE machine over the 2321 recorded rows / 101 tiles: 2288 cached-path
  hits, 1 lazy write-back, 32 adopted live mutations; 9 tiles re-valued in-window
  carrying 230 rows (== M296 S3b); the replayed end-state nibble == the s249 dump on
  86/101 tiles (the 15 are the A5 post-grading drift).
- G4 the save-seeded read path 1931 match / 1 lazy / 389 mutation == B17 G7's recorded
  1931 and 1.
- G5 the s249 snapshot classes 2102 match / 134 bit4 / 85 nibble and **lazy 0** ==
  M297 S3 verbatim (a recorded nonzero val never meets a zeroed nibble - the write-back
  is never undone on a graded tile); 177 records moved the high nibble y2150->y2212, 103
  of them keeping the low nibble.
- G6 the nibble moves BOTH ways (182 below / 31 above the recorded val) = an overwrite,
  not an accumulator; the "getter reads the LOW nibble" rival matches only 76 rows.
- G7 site = BYTE[rec+3] {1: 2253, 9: 68}, max site 9 under the 128-entry region bound,
  1026/1026 single-site visits; the -1 owner sentinel on 277 rows == the cell-store skip
  class, and 0 records of 4096 carry a legitimate 0 owner; the 22-B column-byte0 site
  rival diverges on 2321/2321; the pinned inner walk covers exactly one 32-record row.
- G8 the MAX funnel: 2 slot entries, 5 cell entries over 5 owner blocks, 277 cell-store
  skips == the 277 owner(-1) rows and NO block-0 entry; all tables monotone, every slot AND
  every (block,site) cell equal to the recorded per-pair MAX with 0 disagreements (the
  Greptile #264 P2 fix - the cells are GRADED now, not just counted); last-write rival
  diverges 1 slot, min 1 slot + 5 cells, owner-block-blind key 4 cells (digest
  888f5366f04c74b1). The tables' LIVE contents stay DECLARED unrecorded.
- G9 the 10 rivals refuted by recorded numbers; G10 two module runs identical sha256
  461714e03cc72a32.
DECLARED UNMODELED: the 0x5aff90 value body, the slot's [+4] visit counter (its ++ is
gated on call 0x5832b0), ebx's walked-table provenance beyond the owner-byte reading, the
live 0x989ce8/0x94eca8 contents (a read-only /proc window: LEAD), and every M297 A5
caveat. Box untouched (s244 state; zero /proc, zero gdb). NAMED.md gains the B18 block;
BUILD_SPINE.md now carries the B18 rung.
