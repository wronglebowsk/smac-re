# Session notes archive — sessions 171-171

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 171 (cont. 9) — M114 CORRECTION: the "two rewritten tails" are a K STRADDLING ARTIFACT. The save is 1:1.

M114's claim is RETRACTED, caught 20 minutes later by checking the addresses before arming a watchpoint on them.
The two "rewrite zones" came from windows that STRADDLE a region boundary but were compared with ONE region's
`k`, so they diffed by construction:
- "block A tail 67,080..67,143" is below block B's base (67,852) and was diffed with block B's k=0x916C84 -> the
  238 "diffs" are block-A-vs-block-B content, and the 16-byte "stride" is just two different arrays lining up.
- "map header tail 81,408..82,100" straddles the grid start (82,088) and was diffed with the GRID's k=0x40925B0.

With per-region k the whole file is CLEAN:
```
block A      66,048..67,840   k=0x94D104   0 byte diffs
block B      67,852..79,328   k=0x916C84   0 byte diffs
map header   79,364..82,088   k=0x916D6C   2 byte diffs, both at the FIRST offset (79,364)
grid         82,088..172,200  k=0x40925B0  10 byte diffs, starting at the FIRST offset (82,088)
```
So the restore is **1:1 for every byte of the four big regions**, and the only divergences are a handful of bytes
at the START of the map header and the START of the grid, plus the 2 dwords already known in the 52-record array
(222,831 cleared, the poked field at 223,152 normalised). Confirmed live before arming anything: file 67,080 ->
0x95D70C holds 65,535 in BOTH the file and memory, i.e. no rewrite there.
LAW: a diff window must lie WHOLLY inside one region — a window across a boundary compared with one region's `k`
manufactures diffs that look exactly like real rewriting.

## Session 171 (cont. 10) — the two systemic fixes, as CODE (not advice)

1. **`scripts/save_diff.py` + `scripts/test_save_diff.py` (PASS 7/7)** — the region guard M114 needed. It derives
   regions from the poke anchors (`k = dest - off`), refuses any range that crosses a KNOWN section boundary
   (67,852 block B / 82,088 grid / 172,200 trailer / 172,291 next section / 222,783 52-records — each derived from
   an anchor plus its documented destination base, not a midpoint), and names the boundary it refused on.
   The two windows M114 merged are now REFUSED BY THE TOOL (`67072-69120` -> boundary 67,072; `81408-82100` ->
   the grid start), so the next session cannot repeat that comparison by accident.
2. **`scripts/m109_leg_census.py` teardown** — after the verdict it SIGTERM/SIGKILLs gdb by pid in a loop, then
   READS `TracerPid` from /proc and records it in the log header; if it is not 0 the harness exits **8** with the
   pid to kill. Two runs today (m111b3, m112a1) printed a verdict while gdb was still attached to the game.
3. **`scripts/m113_save_map.py` now verifies every anchor LOCALLY** (`local_1to1`, ±8 B by default): a hit proves
   the marker landed, the local comparison proves the mapping AROUND it is 1:1, which is the assumption every
   later diff leans on. Checked against the live box: 64,000->0x95CB04, 68,096->0x927684, 81,408->0x92AB6C (±64),
   82,432->0x40A67B0 (±64) and 174,000->0x986501 all return 0 local diffs — which independently confirms that
   M114's "map header tail" was the straddle artifact and nothing else.

## Session 171 (cont. 11) — M116 ACCEPTED (m116flag, PASS): the band-flag gate is a BYTE test, no OR sets 0x40, and "0 for all 8" is FALSE

`python3 scripts/m116_band_flag.py` (static over the image + live read of the 8 faction words) — **PASS**.

- **The gate is a byte test** at **0x5aaf7f**: `test BYTE PTR [esi+0x94d430],0x40`, inside **FUN_005aadf0+0x18f**
  (528 B), three instructions after `mov [esi+0x94d800],eax` (the FUN_005aab70 advance threshold is reloaded and
  stored, then the byte is tested). Exactly ONE such test exists in the image.
- **Nothing ORs 0x40 into it.** 170 instructions touch disp 0x94d430; the 17 `or` sites set 0x800000, 0x400000,
  0x1000000, 0x2000000, 0x4000000, 0x8000000, 0x10000000, 0x80000000, 0x40000000, 0x20000000, 0x200000 and 0x2 —
  **zero set 0x40**, so the bit can only arrive through a whole-dword store (18 sites).
- **"bit 0x40 = 0 for all 8 factions" is FALSE at the current state**: the eight words read
  0, **0xFFFFFFFF**, 0, 0, 0, 0, 0, 0 — bit 0x40 is SET for faction 1 and zero for the other seven.
- **But the interpretation is NOT established.** Faction 1's whole dword (and 0x94d434) is 0xFFFFFFFF, which is also
  the shape of a -1-filled/uninitialised record. So "the second ask runs for faction 1" is an INFERENCE. The
  controlled test is a poke: clear bit 0x40 for faction 1 and count hits at 0x5aaf88 (the taken branch).
NAMED's row is amended to say exactly that instead of "never ran".

## Session 171 (cont. 12) — M117 (m117g2): the byte test IS reached 17x a round and never taken; and M116's live half is RETRACTED (stride is DECIMAL)

`python3 scripts/m117_gate_take.py --tag m117g2 --turns 1 --relaunch --save m54b_clean.SAV` — two silent bps:
0x5aaf7f (the byte test, logs `esi` + the byte) and 0x5aaf88 (the taken branch), over one real turn on a clean load.

**17 test hits, 0 take hits, 0 gdb errors.** Per faction: 0 -> reached 0; 1 -> 2; 2 -> 4; 3 -> 1; 4 -> 3; 5 -> 3;
6 -> 3; 7 -> 1. So the gate is **live and reachable every round** (factions 1..7; faction 0 never) and **never
taken**: bit 0x40 is clear for all eight in this state, which MATCHES the original NAMED row — the M89 second ask is
inert here, and the open question is what SETS bit 0x40 (no `or` does; the 18 whole-dword stores are the candidates).

**M116's live half is RETRACTED — my own stride bug.** NAMED writes the faction stride as `f*8380`; that is
**DECIMAL 8,380 = 0x20BC**, and I read it as hex 0x8380 (33,664). The M116 table therefore sampled factions
0, 4, 8, 12... and its "0xFFFFFFFF for faction 1" was really 0x94d430 + 0x8380, a different structure. The corrected
read of the true stride gives **0, 0, 0x04000000, 0, 0, 0, 0x10000000, 0** — bit 0x40 clear everywhere. M116's
**static** half stands unchanged (the `test BYTE PTR [esi+0x94d430],0x40` at 0x5aaf7f in FUN_005aadf0+0x18f, and
the 17 `or` sites, none of which sets 0x40). `scripts/m116_band_flag.py` now carries the decimal stride and prints
"matches NAMED" when no faction has the bit.
Also: m117g1 was a WEDGE (`smac_play` rc=5, HUD byte-static 61 s) — the harness now reports a wedge as
**NO MEASUREMENT** instead of "the test was never reached", because those are different facts.

## Session 171 (cont. 13) — the M117 harness called a NEGATIVE RESULT a failure (exit 4)

`m117g2` exited **4** because its code was `rc = 0 if (not tests or takes) else 4` — i.e. "the gate was reached and
never taken" was encoded as a failure. That is the milestone's actual FINDING (17 test hits, 0 takes, bit 0x40 clear
for all eight), so the harness was mislabelling its own result. Fixed:
`rc = 0` whenever the site was reached (take or no take), `4` only when the site was never reached (inconclusive),
`5` for a wedge (no measurement), `8` for a dirty box. Same class as m111b3/m112a1's stale-gdb "success": an exit
code that does not mean what its reader will assume.
