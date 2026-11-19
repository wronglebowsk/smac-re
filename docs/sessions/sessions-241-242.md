# Session notes archive — sessions 241-242

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-240-240.md` (inserted at s292: the hot file cites only the newest archive, so without this line the older archives were orphans).

## Session 241 (2026-11-10, BUILD, B14 10/10, no box) - the M291 hub SCAN + M292 esi-dispatch/WALK are ONE executable leg (sim/podscan.py); the rung was missing from the spine, so this build fire authored B14 first
- track_mode printed BUILD/next_rung=B14 but the BUILD_SPINE.md ladder ended at
  B13: the fire AUTHORED the B14 rung (from B13's DECLARED walk frontier +
  M291/M292's settled laws), appended it to the spine, then executed it.
- sim/podscan.py: RING_DX/DY 25-entry literals vs the recorded file-image dump
  evidence/b14_ring_table.txt (scripts/b14_ring_dump.py reads .rdata
  0x67850c dx / 0x678990 dy from the PE; the sim never loads the binary);
  scan_esi = M291 strict site-value argmax (score rec byte2 high nibble;
  eligibility cat-flag equality + byte3 owner-equality + rec+9 bit 0x20 clear
  + unoccupied; ties keep the closer entry; self-argmax iff esi==0);
  dispatch_leg: esi 0 -> found, or msg 0x2408 under msg_gate(global!=0 AND
  owner==human) (s240); 1..8 continue; 9..24 walk (order 0x62 at the WRAPPED
  ring tile). New recorded fact: table order, esi 21=(+4,0) 22=(-4,0)
  23=(0,+4) 24=(0,-4); the ISS log tile= field is the target X ONLY (the bp
  at 0x563e3b printfs eax) - target-Y is static-gated law, DECLARED.
- ACCEPTANCE: python3 -m sim.selftest --b14 programs/saves/m54b_clean.SAV ->
  PASS B14: 11/11 (evidence/b14_podscan.txt:23). The recorded file is from
  the post-review invocation (invocation 3; 1-2 died on MY instrument -
  a stray code block; KeyError u on FOUND/DESTROY rows - floors never
  touched).
- GREPTILE round 1 on #252: 2 P1s + 3 P2s, all resolved pre-merge. P1#1
  CONFIRMED (scan_esi returned FIRST-better, the loop is a full argmax:
  best [ebp-0x24]/[ebp-0x84], strict update 0x563c0f-0x563caa) - fixed
  + new G2b (brute-forced argmax on a fixed sample; 200 sample tiles
  discriminate first-better from argmax, so the gate would have caught
  the bug). P1#2 CONFIRMED (the fit never exercised Y-out-of-range; the
  loop head wraps X via 0x469010 and bounds-checks Y via 0x469060 - Y
  NEVER wraps; scratch/m574/text.txt 0x5638af-0x5638dc) - fixed.
  P2s: G5 pairing now CONSUMES its DISP row and pairs FOUND with the
  IMMEDIATE HUBFOUND; G10 reports move to a unique tempdir; the split
  NAMED cite joined. Gates 10 -> 11, PASS 11/11.
- Parity numbers: m289 golden 7/7 self-argmax via the sim scan; rivals fail
  the SAME fit (no-owner-gate 6/7 loses exactly fac1(27,29); B10 row-major
  placeholder 0/7); m292 29 DISP rows partition 9 found / 9 continue / 11
  walk / 0 msg with ISS/HUBFOUND/FOUND adjacency all paired; walk target-X
  11/11 (table-swap rival 0/11); census ledger count-strict 19->27 (POST 27
  per evidence/m292_pod_movement.txt:2); msg law case table + solo inertness
  (ds:0x920434=0 AND every row own=0 -> structural).
- Box: ZERO contact (build fire). Evidence +~11 KB (ring dump 700 B,
  acceptance 2.4 KB); budget re-measured at close.
- OPEN (unchanged): UNMODELED 0x94e5a8/0x94eca8 per-site gate tables +
  FUN_004e3c00 no-go (now named in the rung text as DECLARED); name
  ds:0x920434; re-arm the M284-M287 live census (guards fixed); 188-row
  cursor caller. Next: ANALYSE (gate tables / 0x920434); next BUILD = B15.

## Session 242 (2026-11-10, CONTEXT-HYGIENE fire, PASS - no research findings) - always-loaded 84,743 -> 56,169 B; evidence 28.8 -> 17.1 MB via HOT-WINDOW cite retention

- ACCEPTANCE (`python3 scripts/evidence.py budget` at close): always-loaded 56,169 B vs the 60 k ritual ✓;
  skill/SKILL.md 65,962 -> 40,625 B (warn 55 k); NEXT_PROMPT.md 15,190 -> 11,953 B (warn 12 k);
  evidence/ 28.8 -> 17.1 MB (warn 20): the old prune rule found 1 victim against a 9 MB overshoot.
- THE RULE (docs/EVIDENCE.md "Pruning rules", implemented in scripts/evidence.py): an IMAGE stays hot only
  while the HOT WINDOW cites it - newest 8 `## Session` sections + NEXT_PROMPT/AGENTS/cursor - or it is
  younger than --keep-days, or scripts/test_*.py/sim/ names it (TEST FIXTURE). pick-archive/NAMED/references
  no longer hold images hot (one mention in the full notes history used to keep a screenshot hot forever).
- THE NUMBERS: 58 images/11.8 MB -> 1 hot (164 kB) + 31 pruned to git-only 6.8 MB via `prune --apply`
  (.prune_log.jsonl 190 -> 221 rows) + 26 fixtures `git mv`'d to `evidence/fixtures/` (4.9 MB, uncounted).
- NOTHING DELETED WITHOUT A TRAIL: SKILL depth VERBATIM -> skill/references (new wine-pitfalls/netcode/
  ui-assets/cvr-format.md; 8 existing refs appended); NEXT_PROMPT build+pick ledgers -> NAMED
  §CHAIN-BUILDS/§CHAIN-PICKS; the s241 FULL trap text -> docs/pick-archive.md §s242-traps. Fixture path
  rewrites landed in the 2 test scripts + 12 md files (`git mv` keeps `git log --follow`).
- VERIFIED: `scripts/test_classify.py` PASS 17/17 and `scripts/test_hud_bar.py` PASS 26/26 on the moved
  fixtures; 8 sim rungs re-run green (--b6 6/6 --b7 6/6 --b8 10/10 --b9 7/7 --b10 18/18 --b11 13/13
  --b13 12/12 --b14 11/11; sim/ untouched, --b12 needs a trace arg); NAMED.md now 233,100 B (fail 250 k) -
  a named-archive split is a future fire, not this one.
- GREPTILE ROUND 1 (2 P1 + 1 P2, ALL FIXED pre-merge): scripts/check_classes.py still opened old
  paths and SKIPPED missing frames silently -> resolves evidence/fixtures/ now and a missing frame
  FAILS; long-dead m15_hud/m15_mainmenu/m15_autolist rows dropped; m15_stuck_screen.png restored from
  git (4fd8ebe^) into fixtures; evidence.py treats check_classes.py as fixture code.
  accept_ready.py + session_brief.py counted ALL of evidence/ against the 29 MB floor -> both share
  `evidence.evidence_mb()` (fixtures uncounted). SKILL retired-structural-laws pointer -> code-atlas.md.
