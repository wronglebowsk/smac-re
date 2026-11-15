

Older sessions: `docs/sessions/sessions-239-239.md` (1 sessions). Read it only when a question reaches back before session ## Session 240.

## Session 240 (2026-11-10, CORRECTION, M293) - the three verified Greptile P1s: "distant target -> msg 0x2408" (M290/B13) RETRACTED - msg leg = OWN-TILE + second gate [ebp-0xa4]; M284-M287 live SITE censuses INSTRUMENT-INVALID; sim/selftest run_save IndexError fixed. These were claimed facts, so they are retracted plainly, per AGENTS.md.
- D1 (bytes; gate scripts/m290_hub_decision.py:160): 0x563d48 jne 0x563dfa
  - the distant leg reaches NEITHER founder NOR msg; only esi==0 falls to
  [ebp-0xa4] (single writer 0x55f6d6 = ds:0x920434!=0 AND owner==ds:0x91b5b4):
  flag 0 -> founder 0x563d82-86 (FUN_004cca50, pod args); flag!=0 -> msg
  0x2408 block 0x563d59-0x563d7d + jmp 0x56c925. Own-tile gating +
  founder-args = pod record STAND. The old G4 sliced its OWN table at
  0x563d4e..0x563d81 (founder je-target 0x563d82 abuts the end) - could
  not fail; G4 now parses real branch targets. ACCEPTANCE: python3
  scripts/m290_hub_decision.py programs/saves/m54b_clean.SAV
  evidence/m289_gdb_raw.log evidence/trace_m289_20261110_071759.jsonl ->
  PASS M290: 9/9 (evidence/m290_hub_decision.txt:33; 3 runs, 1-2 were my
  instrument, floors never cut).
- D1b read-only /proc probe (pid 4087359, TracerPid 0): ds:0x920434=0 ->
  msg leg UNREACHABLE in solo: s239 "MSG never observed" was structural,
  not inertia. OPEN: name ds:0x920434 (scenario/MP gate?).
- D2 sim/hubfound.py:94: distant -> ("distant",) (was ("msg",0x2408));
  own+flag -> msg; own -> found. ACCEPTANCE: python3 -m sim.selftest --b13
  programs/saves/m54b_clean.SAV -> PASS B13: 12/12 (evidence/
  b13_hubfound.txt:4).
- D3 guard `if $reg >= 0x1000000` (m284/m285/m286/m287 dispatch arms)
  excluded the five family vtables 0x67164c/0x6717cc/0x6728c0/0x675cc4/
  0x6776c8 (image base 0x400000) - a real family dispatch printed NOTHING:
  every "0 of 12 fired" in M284-M287 = instrument-silence, RETRACTED (CTRL
  rows prove the windows ran). Guards now >= 0x400000; static halves stand;
  re-armed census = open lead. No live re-run this fire (box kept clean).
- D4 sim/selftest.py:177: walk returns (rows, notes), prints nothing -
  buf...[-1] IndexError every run. ACCEPTANCE: python3 -m sim.selftest
  --sav programs/saves/m54b_clean.SAV -> PASS B2: 7/7
  (evidence/s240_b2_run.txt:2).
- Docs: NAMED M290/B13/M292 fixed in place + INVALID banners M284-M288 +
  ## M293; path:line cites per AGENTS.md:50. Next: gate tables
  0x94e5a8/0x94eca8 + name ds:0x920434. BUILD = B14.

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

## Session 243 (2026-11-10, BUILD B15, PASS 7/7, zero box contact) - gate tables 0x94e5a8/0x94eca8 NAMED; pod-scan price gate EXECUTABLE (sim/gatetables.py)

- ACCEPTANCE: `python3 -m sim.selftest --b15 programs/saves/m54b_clean.SAV` -> **PASS B15: 7/7**
  (`evidence/b15_gate_tables.txt:1`). Authority = RECORDED objdump windows `evidence/b15_gate_window.txt`
  (210 lines, 6 windows, terran.exe sha256 header; `scripts/b15_gate_window.py`).
- LAY CENSUS (`name_global.py --disp`, saved to evidence): `0x94e5a8 = site_score` byte x128 per
  faction block (blk+0x120): 99 refs / 24 funcs / 5 stores (M94 pair 0x556721/0x556b5a); FUN_0055f650
  22 refs 0 writes. `0x94eca8 = site_gate` byte x128 (blk+0x1860): 7 refs / 4 funcs, **0 direct
  stores** - the only writer is FUN_0051dcb0 (zero sweep 0x51dcd1/0x51dce7 + ADDRESS-COPIED store
  lea 0x51dfe2 -> `mov BYTE PTR [ecx],al` 0x51dff3; value source via 0x582cc0 OPEN). The bare-ds grep
  found 0/1 refs - the [reg+disp] scaling trap; `--disp` answers it.
- `ds:0x920434 = published_window_id`: name_global reconfirms M125 - 634 refs, exactly 15 stores
  (pcs == the M125 set, asserted in G2); solo live = 0 (M293 D1b); it is the msg gate at 0x55f6b0.
- GATE LAW executable, every branch byte-verified: argmax-skip; bypass `value >= 2*(8-dist)`;
  site_score==0 accept; `[blk+0x94e488]<2` accept; thr=(pod-region verdict==8)?1:4, max(site_gate);
  value>=thr accept; then skip legs `case!=8`, `byte[unit+0x11]==0x18`,
  `dword[0x989ce4+28*region] >= 6*(site_score+1)` (edx at 0x563c8e carries the dl from 0x563c3d -
  NOT a ring index).
- GATES: G1 73 pins == recorded window, table-swap rival 0; G2 census re-check vs shipped evidence;
  G3 closed form == recorded-byte INTERPRETER on 14,520 decision-grid cases; G4 the 4 rivals each
  disagree with the recorded bytes (81/146/236/2851); G5 27 recorded winner events modelled -
  24 bypass-accepted / 3 row-dependent (the exact print list for the box follow-up); G6 gated-scan ==
  podscan.scan_esi under permissive rows 7/7; G7 determinism, window sha256 685892fd4c2837df.
- THE INTERPRETER caught 2 real bugs pre-merge (the tiles ceiling is 6*(site_score+1) via the dl
  copy into edx; the unit byte is RAW ==0x18, not a bool) that a closed-form-only rung would have
  shipped - LAW: when the recorded bytes are window-able, grade the closed form against a byte
  interpreter, not only against events.
- Box: ZERO contact (build fire). Evidence +~10 KB. `evidence.py budget` at close under 60 k;
  NAMED.md 234.5 k (warn 250 k) - archive split stays a hygiene lead.
- OPEN/leads (recorded, not pursued): the al source for 0x51dff3 in FUN_0051dcb0; callers of
  FUN_0051dcb0 uncensused; the 0x94e5a8 readers in FUN_004f6030 (15 refs) / FUN_0050d140 0x50e4fb
  and the 0x564xxx-0x56c8xx band inside FUN_0055f650 uncensused; live table rows for the 3
  row-dependent winners -> the re-armed pod-walk census prints them (guard re-derivation law M293).
- GREPTILE ROUND 1 (#256, 2 P1 + 4 P2, ALL FIXED pre-merge): scan_esi_gated put UNIT_BASE in the
  [ebp-0x10] slot while the interpreter adds the absolute 0x933289 (double base - G6's permissive
  rows never reached that leg; a deep-leg row regime now walks FULL chain incl. unit+tiles before
  accept); scan_esi_gated silently needed acceptance() to pre-load the window (now lazy-loads
  evidence/b15_gate_window.txt); FAM_STRIDE published 0x8380 where the fold is DECIMAL 8380 =
  0x20BC; site_score blk-offset wording (0x94d448+0x1160, M92 view +0x120 from 0x94e488); the
  window recorder hashed terran.exe but trusted the text cache (now every window line's bytes are
  verified against the exe at the single anchor-derived VA->file delta -0x400000, ambiguous or
  missing -> refuse); G7's len==64 hash tautology replaced by a pinned digest (window sha256 now
  c1b3712b6be6f5d3). Re-run after fixes: PASS B15 7/7, 14,520-case grid green.
  Next: ANALYSE/box (pod-walk census re-arm); next BUILD = B16.

## Session 244 (M294, box fire) - pod-walk gate-row census RE-ARMED; B15 law predicts every dispatch from printed rows
- Instrument scripts/m294_gate_row_census.py: m292 static gates re-run (never reused blind) + 27 NEW byte-pins
  (S1/S2 PASS) for GDEEP@0x563c3d/GACC@0x563ca7/GROW@0x563cb3 + prologue/fold pins; blk fold identity 8380*o re-derived.
- Box: s241 state was BLOCKED (pending 0, then credit 0 - structural in this save, d0-gated); ran accept_ready FIX
  (relaunch+m54g_prep+drive 1+enqueue), then advanced 37 turns to y2188 (m54b_clean's recorded year), 24-turn census.
  Rows: HUB=2870 (rets exactly {0x50dd89,0x56cf17}), DISP=192, ISS=184, FOUND=4, CTRL=1857. TracerPid 0 post, yama restored to pre (0).
- Run 1 model FAILed 2129/2129 visits with ZERO direction-of-law failures -> static diagnosis (dis 0x5638a9-0x563bf7):
  the loop head has 7 eligibility pre-checks jumping straight to the 0x563cb3 tail (walk 0x469060, mask vs [ebp-0x58]
  0x563917, elev 0x563928/3e, region: BYTE[tileview+3]==[ebp-0x34] AT 0x56394E ([ebp-0x34] stays the POD region through
  the whole loop - the gate's region IS the pod region), 0x563954 dh&0x20, no-go call 0x4e3c00>=0 @0x563963) - on those
  paths tail $esi = slot/x garbage, not value. Fixed replay (decision rows carry exact incoming best; winner = last
  accepted slot; tail win cross-check); selftest scratch/m294_model_test.py 3/3.
- REMODEL over the RECORDED rows (same B15 grading law): G5 parity 2129 visits / 2321 decision slots / 260 accepts /
  0 disagreements / 0 DISP-without-rows; G4/G7/G8 PASS; VERDICT PASS. evidence/m294_gate_rows.txt; raw
  m294_gate_rows_raw.txt; run-1 trail evidence/m294_gate_rows_run1_note.txt (the 2 MB run-1 report was overwritten by
  the rerun rename pre-commit - trail gap recorded, numbers in the note).
- G6: targets (22,14)/(18,2) did NOT recur this window (foundings (6,46),(12,48),(40,14),(62,46)) - recorded, not hidden;
  in-window row-dependent accepts printed (e.g. u=45 slot24 val6 mult7 gate10 verd0 case8 tiles345 -> case8open).
- STEP 2 (static, after green): FUN_0051dcb0 has EXACTLY 11 e8-callers (incl. the founder vector FUN_004e47d0@0x4e4dc8);
  site_gate store 0x51dff3 = max(cell@0x51dfeb, edi); edi = BYTE[rec+2]>>4 (0x51df85) OR call 0x582cc0 result (0x51df9f,
  after 0x5aff90@0x51df97); cell addr = 0x94eca8+[ebp-0xc]+4*min(edi,[esi+0x989ce8]) - VALUE-INDEXED (flagged).
  evidence/m294_sitegate_callers.txt. OPEN: semantics of 0x582cc0 + [ebp-0xc] index.
- Evidence +~2.7 MB -> evidence.py budget printed at close; NAMED ## M294 <=1 KB added.

## Session 245 (2026-11-10, BUILD B16, PASS 7/7, zero box contact) - pod-scan loop HEAD PRE-CHECK CHAIN named + executable (sim/precheck.py); the m294 x/y transposition law
- `python3 scripts/track_mode.py` said `MODE=BUILD next_rung=B16`, so this fire BUILT B16
  (the rung was not yet in BUILD_SPINE.md, so it is authored on the branch) instead of
  taking the ANALYSE pick - and the build landed on the same chain the pick named, graded
  against RECORDED rows (no box, no /proc, no gdb).
- ACCEPTANCE: `python3 -m sim.selftest --b16 programs/saves/m54b_clean.SAV` ->
  **PASS B16: 7/7 gates** (console + report: evidence/b16_precheck_chain.txt; byte-window
  transcriber `python3 scripts/b16_pin_window.py` -> evidence/b16_precheck_window.txt,
  250 instructions, objdump -M intel from the function entry 0x55f650).
- G1: 31 pins - the 7 chain legs AND the prologue stores feeding them - match the recorded
  window. Chain: bounds 0x5638d2 (`call 0x469060` range-tests BOTH legs; X is pre-wrapped by
  0x469010 at 0x5638b9 so only Y bites), class (byte0&0xe0)<0x60 == [ebp-0x58], byte8&0x20
  needs cat<2, elevation band byte5&0xc0 > 0x40 needs cat<3, region byte3 == [ebp-0x34],
  occ byte9&0x20, no-go `call 0x4e3c00(owner,X,Y)` >= 0 (M294's (x,y,owner) order corrected
  in NAMED: the pushes at 0x56395d-0x563962 put owner first).
- The pick's three questions: (2) [ebp-0x58] is written at 0x563814 as ([ebp-0x40]==1),
  [ebp-0x40] = the unit TYPE's required-class byte BYTE[0x92ae81+144*BYTE[0x98adac+52*type]] (144 = lea*9 then shl4; stride corrected s246 per Greptile #258);
  the `cmp ecx,eax / jne 0x563f18` at 0x563812-0x563817 gates the WHOLE scan on its equality
  with the POD tile's own water flag [ebp-0x74] (0x55f783-0x55f79c) - THEOREM the sim uses:
  required class == classflag(pod tile). (3) the elevation band is the top two bits of
  tile-record byte 5 (bands > 0x40 bite only land-category tiles): it excludes 3304 recorded
  slots and is never contradicted by a recorded decision slot. (1) the no-go stays OPEN:
  **8482** (pod,slot) tests pass all 6 modelled checks yet printed no decision row.

- G2 (a new instrument law, recorded in the skill `instrument-laws.md`): the m294 census
  printed its two coordinate legs TRANSPOSED - `x=` is *(int*)($ebp-0x8), the multiplied side
  of the tile-record formula, `y=` is *(int*)($ebp-0x4), the >>1 side. With the law applied,
  pod recovery from a visit's decision rows is consistent 1026/1026 and matches the DISP
  rows' unit-record x/y 201/201; without it 638 and 0. M294's own verdict is unaffected (its
  replay read slot/val/best/win only), so the merged claim stands and only the raw rows'
  labels needed the correction.
- G3/G4 (25650 (pod,slot) tests): 0 recorded decision slots violate bounds, elev or occ.
  fail&skip per check = bounds 110 / class 5036 / b8_bit20 9311 / elev 3304 / region 5880 /
  occ 389; solo (sole-excluder) = 0/0/5775/2181/185/212 - bounds and class never exclude a
  slot ALONE in this window, stated in the gate rather than hidden.
- G5: every visit's decision rows share ONE class flag and ONE region byte (0 mixed of
  1026). G6: the confusion grid (2128 decision&pass / 193 decision&fail / 8482 skip&pass /
  14847 skip&fail), the per-check table, the solo set and the pod/DISP/rival counts are
  pinned in `sim/precheck.py BASE`; G7 two runs byte-identical (sha256 3d5f6e8e...).
- Drift attributed, not smoothed: the 106 class and 192 region fail&rec slots are
  all-or-nothing per visit (106 all, 0 some) - the pod tile read from the y2150 save differs
  from the live tile in the y2188+24 window, so the stale side is the pod-state read, not
  the laws.
- Box untouched (still s244: y2212 cnt30, TracerPid 0). Next pick: the 0x4e3c00 no-go (the
  8482-slot population is its measurement), or the OPEN 0x51dfe2 cell addr / 0x582cc0
  side-effects; the CHAIN-PICKS trio stays open.

### 245c. Close-out audit trail (post-submit, same fire)

- Audit finding on my own module, NOT yet fixed (context cap hit at close-out):
  `sim.precheck.load_visits` keys the (pod,slot) set by `d["y"]`, i.e. the
  TRANSPOSED leg - the same register-vs-label trap the B16 law it documents warns
  about, so the law-fit compares recovery against a transposed target. The map
  stays 1:1, so the sizes the confusion grid grades (25650 tests, the 8482/2128
  cells) are unaffected either way; what the fit's 1026/1026 agreement PROVES is
  looser than intended. Suggested fix for the next fire: key by `d["x"]` (the Y
  leg stays in the tuple's first slot per the docstring's own convention) - and
  only after showing the law still fits (recover_pod's ring-sum is symmetric, so
  both orderings can recover the pod; the point is to test the pair the law names).
- Chain step B ran FIRST per the operator amendment (s246 scheduled before the
  review wait), so this fire submits the audit as a record instead of shipping an
  unverified re-fit.

## Session 246 (2026-11-10, s246)

### 246a. #258 (B16) closed per the MERGE RULE and merged (main 9567ec1)

Greptile posted 1 P1 + 2 P2 at 22:20; dispositions (full text in the PR body):
- P1 ACCEPTED: the 8482 pass-6-no-row cells are also the value-vs-best skip
  (0x563c09-0x563c11 after the chain, before GDEEP 0x563c3d). Relabeled
  sim/precheck.py (NOTE + UNMODELED), NAMED.md, NEXT_PROMPT.md; bytes pinned by
  extending evidence/b16_precheck_window.txt to 0x563bf0-0x563c60 (284 insns).
- P2 stride: BYTE[0x92ae81 + 144*BYTE[0x98adac + 52*type]] (lea*9 then shl4,
  0x55f757/0x55f75c) - fixed in precheck.py:37, NAMED.md, SESSION_NOTES.md:671.
- P2 report: report_text counts matched pins now; chain evidence regenerated
  (`python3 -m sim.precheck --out evidence/b16_precheck_chain.txt`).
- s245c self-audit REFUTED, no code change: DISP prints unit-record fields
  0x933278/0x93327a (true X,Y); law orientation 201/201 vs them, the audit's
  untransposed orientation 0/201 (BASE rival_disp_ok) - G2 tests the pair the
  law names; the proposed re-key would install the rival the gate rejects.
`python3 -m sim.selftest --b16 programs/saves/m54b_clean.SAV` PASS 7/7; merged
via `python3 scripts/milestone.py merge 258` (Greptile registered no check run on
the new head inside the 10-min cap - operator amendment 2).

### 246b. M295 - the 0x4e3c00(owner,X,Y) no-go NAMED, pinned, MEASURED INERT

fn.py + dis: FUN_004e3c00 = territory_nogo, calling FUN_004e3b50 =
owner_of_tile_visible: tile7 = signed BYTE[44-B tileview+7] (B16's view/form,
0x4e3b53-0x4e3b76; movsx at evidence/m295_nogo_window.txt:19), visible if
BYTE[0x985ae8] bit 0x80 or pair-flagword bits 3+27 (immediate 0x08000008,
window :45,:46). pair array base = per-faction block 0x94d430 (disasm constant,
170 uses, e.g. [edx+0x94d430] at 0x429ab9) + 0x18 = 0x94d448 (M143 folded
[owner*2095+tile7]*4). c00 blocks
(returns non-negative) iff tile7 >= 1, tile7 differs from the pod owner, the
human-mask BYTE[0x985b10] (NAMED M96; masked 0xff at 0x4e3c34) has the pod or
tile bit, and the flagword bit 4 is CLEAR (alliance, window :120). The return value is
FUN_004e37f0's (nearest-base sweep writing DAT_008f0d34 = M294's dist;
sentinel 9999). MEASURED `python3 scripts/m295_nogo_fit.py` (evidence
m295_nogo_fit.txt): over the m294 window the full rule rejects 0 recorded
slots and 0 pass-6-no-row cells (697 owner-known visits; 329 visits with
unresolvable u above the 67-record units array); t7 dist of the 8482:
255:2490, 4:2058, 6:1822, 5:1190, 2:872, 1:45, 3:4, 7:1; human_mask 0x8,
feature_bits 0x0. Rivals collide with recorded slots: foreign-only 1045,
+mask 124, +not-ally 119. Within the graded subset R4 rejects nothing, so the
8482 are BEST EXPLAINED as the VALUE<=BEST ARGMAX SKIP (0x563c09-0x563c11) -
the next leg. NOT CLOSED (Greptile P1c): grading covers the 697 owner-known
visits vs the y2150 save (window is y2188+); live-flag-matched inputs are the
only closer. Cites: window :19,:45,:46,:104,:120,:122;
fit evidence/m295_nogo_fit.txt:4-8. Window scripts/m295_nogo_window.py -> evidence/
m295_nogo_window.txt (129 insns). Callers 0x5597ea, 0x563963/0x5643e9/0x5647a1
(the last three inside FUN_0055f650) - lead.

### 246c. Greptile round 2 on #259 (3 P1 + 1 P2), dispositions

- P1 "wrong flags" ACCEPTED: block A record base is 0x94d430 (170 disasm uses;
  0x94d104 appears 0 times - the atlas headline phrasing is a fix-lead), so the
  pair-flagwords sit at saved block+0x18. Script fixed, evidence regenerated:
  R3 collisions 91 -> 119; R4 still 0 rejects.
- P1 "wrong bit" ACCEPTED: the recorded immediate is 0x08000008 = bits 3+27
  (not 31); the 0xff-masked human-mask read is at 0x4e3c34 (window :104).
  Model + all descriptions corrected.
- P1 "partial results" ACCEPTED: INERT claim softened everywhere to "0 rejects
  in the graded owner-known subset vs the older save"; live no-go stays OPEN
  and s247's pick carries that.
- P2 (path:line cites) ACCEPTED: window/fit line cites added to 246b and the
  NAMED ## M295 rows.

## Session 247 (s247, M296, 2026-11-11)

- M296 THE ARGMAX LEG FITTED, all-static (no box touched): `python3 scripts/
  m296_argmax_fit.py` -> evidence/m296_argmax_fit.txt: **PASS M296: 9/9** over (Greptile #260 round 1: 4 P2s - evidence now saves the REPORT lines, S0 coverage pins 1026/2321/25650/8482, byte9 labels, tie-claim softened below)
  1026 visits / 2321 GDEEP-GACC rows / the 8482 pool. Byte windows: evidence/
  m296_init_window.txt (scripts/m296_init_window.py, 11 pins OK).
- BYTE FACTS: (1) `and eax,0x1000` at 0x46e792 tests dword[rec+8] bit 0x1000 =
  BYTE9 bit4 (NOT byte8 - the M295-era shorthand is corrected here); 1083
  in-window tests, all pool-side (never a row). (2) [ebp-0x24] is zeroed
  unconditionally at 0x563839 EVERY scan; the ONLY override is case==8
  (`cmp esi,8` 0x563836) + order-0x18 (`cmp BYTE[unit+17],0x18` 0x563845 - the
  move-to-base order, NAMED 0x4d3770/0x4d6fb0, +20/+28 = base tile) +
  wrapped-diff gate>2 (0x46e540/0x46e5a0): best_init = value(base tile)-1
  (0x563896-9f). A move-to-base pod accepts candidates >= its base tile's value;
  every other visit starts best=0.
- FIT: S1 val>best 2321/2321; S2 best == max(best_init, prior GACC vals)
  2321/2321; S7 GROW best column replays 25650/25650 slots; S7b case-8 leg 1/1
  nonzero-init, value leg 0 save-gradeable hits (the lone move-to-base init
  u=45 best=5 carries a save-STALE dest: (19,6) byte2=0x05+0x1000 bit, not a
  save base - live closer); S5 rivals miss the val column (low 105, cat 98,
  full/b8hi 0 vs nib 1931/2321); S5b: 0 of 2321 rows has val==best (>= never observed; 5721 static tie candidates corroborate, nogo-unverified); S6
  bypass 61/61 + 0 GDEEP rows at/over the 2*(8-dist) cap. S3 static val
  coverage 1739/2129 AGREED + 192/192 DRIFT; 390 mismatches = LIVE byte2
  mutation (9 tiles carry 2+ machine-attested vals). Pool: 6048/8482
  static-explained as val<=best skips (5721 ties, 904 of the explained via the
  0x1000 zero); 2434 unexplained = mutation/no-go/live class - THE LIVE
  FLAG-MATCHED CENSUS (M295 P1c + this) is the shared closer - LEAD.
- s245/s246 facts held; kickoff M295 re-run first: R4-empty table verbatim
  (evidence/m295_nogo_fit.txt). NEXT_PROMPT regenerated (s247 close).

## Session 248 (s248, B17, 2026-11-11)

- BUILD FIRE (track_mode printed MODE=BUILD next_rung=B17). The rung was not in
  BUILD_SPINE.md, so this fire AUTHORS it (B14/B16 precedent): **B17 - the
  pod-scan loop DECISION CORE made executable**. `sim/scanleg.py` COMPOSES the
  M296 best/argmax chain (best_init law + accept store 0x563caa + winner),
  B15's price_gate (sim.gatetables) and B16's grid law (sim.precheck, read
  TRANSPOSED) into ONE slot-strict replay of the m294 gate-row window.
- ACCEPTANCE `python3 -m sim.selftest --b17` -> evidence/b17_scanleg_chain.txt:1
  **PASS B17: 10/10**: G1 pins 1026 visits / 2321 decision slots / 25650 GROW /
  260 accepts / 61 bypass (m296 S0 + NAMED ## M294); G2 best_init law-vs-machine
  990/1026 (the zero-leg needs NO unit record; 362 scans name post-save units -
  bucketed not_in_save, never graded as saved state); m2b class 36 = 3 save-
  recorded (u=45 machine-5 vs save-dest -1 = the S7b stale-dest class, value leg
  OPEN; 2 save-invisible dests) + 33 unit-not-in-save; case-8 leg 1/1; G3+G4 the
  GROW BEST *and WIN* columns both replay 25650/25650 (the win replay is NEW -
  M296 pinned best only) AND the M296-S2 incoming-best law re-checks all 2321
  decision rows against the REPLAYED best; G5 accepts 260/260 predicted from the REPLAYED best
  (bypass 61 + legs value 4 / bases 192 / mult0 2 / case8open 1), 0 GDEEP rows
  at/over the 2*(8-dist) cap; G6 predicted winner == DISP esi 201/201 (0 drift
  skips); G7 save-view val-law 1931/2321 (lazy 1; 0 tie rows; 0x1000-zero tests
  pool-side only, 1083); G8 pool 6048/8482 explained (5721 ties), 2434 DECLARED
  residue; G9 rivals fail the SAME grid (>=-argmax 5721 tie cells; frozen-best
  diverges 1713/25650; no-bypass +61 GDEEP; no-init-law 24 slots in u=45); G10
  two module runs byte-identical (sha256 pinned in the evidence).
- Kickoff per the fire's shape: M296 re-run FIRST -> **PASS M296: 9/9** verbatim
  (re-run, not re-derived); #180 (M241) re-checked: zero inline comments/reviews,
  still 2/5 gates = no real PASS to merge on, stays open unchanged.
- NO box time (build track: no /proc, no gdb). The live-map flag-matched census
  is UNTOUCHED - it stays s249's pick (THE PICK in NEXT_PROMPT, regenerated).

## Session 249 (s249-m297): M297 - the LIVE-MAP flag-matched census
Open-PR sweep first: B17 re-ran green on main - `python3 -m sim.selftest --b17` ->
evidence/b17_scanleg_chain.txt:1 "PASS B17: 10/10 gates ...". #180 (M241)
re-confirmed the documented-FAIL milestone (2/5 gates, zero review activity since
2026-11-01) - left open, gates NOT weakened. #105 = docs badge, not a milestone.
CENSUS (scripts/s249_livecensus.py --predict then --live; accept_ready.py BLOCKED
on the structural credit-0 (documented, walk/scan kinds run anyway), preflight PASS;
ONE read-only /proc pass, zero gdb, TracerPid 0->0, yama 0 recorded/restored
unchanged, year 2212 cnt 30 pinned before AND after, starttime identical):
tileview base = dword[0x92ae14]=0x40a5cd0, 44 B x 2048 recs dumped
(evidence/s249_live_map.bin), rowmul 32 = W/2, bounds 64/64, byte0/byte3
identity 2100/2321 (90.5%). RESULT: the 8482-cell pool under LIVE bytes closes to
UNEXPLAINED 0 (tie 7518 / lt 287 / live-static-fail 677 / no-go 0); the 2434
residue = tie_live 2146 + lt 35 + static-fail 253. M295 P1c: no-go R4 on LIVE
flags rejects 0/8482 AND 0/2321 - INERT, explains none of the residue. Rivals
fail the live grid: R1 1538 / R2 42 / R3 42 recorded collisions, ge-argmax 7518
ties printed no row. u=45 CLOSED on the dest-moved branch: live unit-45 order
+17=0x00, dest(9,47), owner 6 vs save 0x18/(19,6). S3 strict live row law =
documented FAIL finding: 2102/2321 exact, lazy 0, drift-after-grading 219
(bit4-flips 134 + nibble 85; 201 machine-attested, 18 unattested) - an
end-of-window snapshot grades only the LAST turn's rows. scripts/s249_attestation.py
re-derives the scorecard + taxonomy from shipped evidence (idempotent block).

## Session 250 (2026-11-11, zero box time) - #262 finished: attestation v2 + all PR reviews disposed, MERGED

s249 died mid-close-out before running scripts/s249_attestation.py, leaving
PR #262 (M297 LIVE-MAP census) open with two unread reviews (Greptile 1xP1
snapshot-vs-history + 4xP2; hermes-review 4xP1 + 2xP2). Dispositions, all in
the PR body: (1) hermes P1 starttime bug CONFIRMED - /proc/PID/stat split on
") " leaves idx 0 = state letter, starttime = idx 19; fixed in
scripts/s249_livecensus.py (S0/S8 + attestation A6 amendment: the hygiene
claim stands WITHOUT the token - pins 2212/3 + TracerPid 0->0 + map identity
2100/2321). (2) hermes P1 S7 gate(True) CONFIRMED - now asserts independent
recounts of both no-go counters + owner coverage + t7-dist == 8482. (3) hermes
P1 S3 attestation CONFIRMED - drift_taxonomy(): a miss is attested ONLY by a
machine grading event LATER on the same tile (the 97-row/9-tile multival set
was a lower bound; bit4 flips are val-invisible). (4) hermes P1 owner-silent
CONFIRMED in code (row_no_owner/pool_no_owner counted + gated) but machine-
CLEAN on the shipped run: all 115 visit units in [0,2500), owners loaded for
exactly that set. (5) Greptile P1 caveat made explicit in addendum A5 + NAMED
rows + PR body: every live verdict is END-WINDOW - a tie NOW != a tie at the
skip. (6) Greptile/hermes P2s: attestation v2 DERIVES the A1 scorecard from
the shipped gate lines - now prints P6 PARTIAL-MISS (R2 42/R3 42 vs predicted
>=50 floors, save-side 124/119, live mask 0x8 shrinks mask-gated collisions);
the hermes P2#1 "P4 printed 0" claim was WRONG (shipped line shows 2434; its
dead `if False` line removed anyway). `python3 scripts/s249_attestation.py`
once: **A0 shipped-verify PASS 25/25** - every bin-derivable number on the
shipped gate lines reproduces exactly under the fixed instruments (2102/0/
134/85, 201 attested/18 unattested, 7518/287/677/0/0, t7-dist, identity
2100/2321, (19,6) 0x5/0x10/value 0, tie ROWS 0, owner coverage). Census gate
state unchanged: FAIL M297 1/7, S3 = the documented finding (floor NOT
weakened). Merged #262 after the MERGE-RULE wait. Next: s251 small statics.

## Session 251 (2026-11-11, STATIC, zero box) - M298 SMALL STATICS pair CLOSED

No /proc, no gdb, no box contact (s244 state untouched since s249's read-only pass).
Milestone: the two holes M294 left OPEN in FUN_0051dcb0 (sole site_gate writer).

- (a) 0x582cc0 body pinned (19 insns): push/pop ebp + eax/ecx/edx only, ZERO
  edi/esi/ebx writes => edi (0x5aff90 return, copied 0x51df9f) SURVIVES the call into
  the slot-max 0x51dfc3 and the cell-max 0x51dfee-51dff3 (no reload; both maxes); 0x51dfac reloads eax over only the
  DISCARDED return (rec base, lea 0x582ce6). Effect = CACHE WRITE-BACK: BYTE[rec2+2] =
  (old&0x0F)|(param_3<<4), rec2 = [0x92ae14]+0x2c*([0x692184]*param_2+sar(param_1,1)) -
  the same +2 high nibble the cached-path test 0x51df85 reads: next walk skips
  0x5aff90 (525 insns).
- (b) [ebp-0xc] caller hypothesis REFUTED: own frame (0x51dcb1 mov ebp,esp; 0x51dcb3
  sub esp,0x1c), void/0-args; EXACTLY ONE store in 386 insns: 0x51dd57
  mov [ebp-0xc],ecx = zero-extended BYTE[rec+3] (xor ecx 0x51dd48; mov cl,[edi+3]
  0x51dd4f); record cursor base [0x92ae14] 0x51dd1e, +0x2c at 0x51e128/0x51e133; the
  other 5 refs (0x51dd9f/df28/dfac/e021/e0cc) loads; store precedes first load.
  Site/region index is record byte +3, not caller-supplied.
- FINDING (phrasing fix): M294's `cell addr = 0x94eca8+[ebp-0xc]+4*min(...)` wrong -
  max(edi,slot) STORED 0x51dfcb to the 28B/site slot (jle 0x51dfc5 keeps old when edi<=old) [28*[ebp-0xc]+0x989ce8] (esi via
  (x*8-x)<<2 0x51dfb1-ba); addr 0x51dfe2 = 0x94eca8+4*(2095*ebx)+[ebp-0xc] (0x51dfd3-e0
  65x/131x/<<4/-x; 4*2095 = 8380 = M297 faction block stride); cell = max(edi,old)
  0x51dfeb-f3; ebx = scan idx (xor 0x51ddf5; -1 clamp 0x51df22-24); ebx==0 skips the
  cell store (test/je 0x51dfd1), slot-max store survives. ebx's walked table
  (0x51de2c-0x51df1d) = recorded LEAD, not chased.
Evidence: evidence/s251_statics_fn51dcb0.txt (162 lines verbatim); dump
scratch/s251_fn51dcb0.txt. NAMED M298 block + line-1711 status closed. Gate GREEN.

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

## Session 253 (2026-11-11, STATIC, zero box) - B18 #264 CLOSED: the review round (10 P1 + 2 P2) fixed IN-BRANCH, MERGED #264
- s252 died mid-close-out; its kickoff claimed no outstanding P1s - WRONG: 10 P1 +
  2 P2 inline comments sat on head 522cdc8. Every finding run to ground against the
  pinned windows; all fixed IN-BRANCH (or dismissed WITH a shipped proof, below).
- The unfinished script = scratch/sitegate.py = shipped sim/sitegate.py + four FOLD
  DECODERS, DEFINED BUT NEVER WIRED. Wired: G1 DECODES the record fold -> (44-B
  stride, byte +2), slot stride 28 from the chain 0x51dfaf-ba, base 0x989ce8 +
  counter +4 off the [esi+disp] operands (0x51dfcb/0x51e00d), cell fold -> 8380*block
  + 0x94eca8 with the site byte UNSCALED (the pinned lea scales the BLOCK term by 4;
  ecx==site via newly pinned mov ecx,eax 0x51dfaf) - arithmetic identities REPLACED
  by byte-read laws. PINS 62 -> 64.
- decode_max_polarity GRADES old loads: slot = full-DWORD 0x51dfbd; cell = newly
  pinned `xor eax,eax` 0x51dfe9 + `mov al,[ecx]` 0x51dfeb IMMEDIATELY before the cmp.
  G2 nibble law = SYMBOLIC run of the four pinned ops (mask/shift parsed from their
  texts) == write_back 8192/8192; rec2_off byte-graded vs the INDEPENDENTLY shipped
  podscan Grid.rb view 4096/4096 (+ Grid.val getter 4096/4096).
- G3 classifier: a ZERO nibble takes the lazy path WHATEVER the val (new lazy_zero
  class) - EMPTY here: 2288/0/1/32, counts unchanged, control flow honest. G5/G6 run
  only AFTER the live-dump length is validated (FAIL, not IndexError). G5 PROVES
  "dword[rec+8] bit 0x1000 == byte9 bit4" on 8192/8192 dwords - that P1 was WRONG
  (same physical bit). G7 GRADES the eight-block owner family ({-1} u 1..8, <=8
  distinct); G8 enforces cell blocks 1..8. acceptance() all() over ITS OWN gates.
- ACCEPTANCE: `python3 -m sim.selftest --b18 programs/saves/m54b_clean.SAV` -> **PASS
  B18: 10/10** (evidence/b18_sitegate.txt regenerated); `python3 scripts/gate.py
  --base main` -> GATE GREEN (0 warnings). Box: ZERO.

- LANDING: #264 squashed to main as 487f0b4 at 23:52:47Z (owner account; the own
  `gh pr merge` found it already merged and verified main). GREPTILE SILENT on head
  6ce43b5 (no check run, no new comment within the capped wait). Chain: s254
  scheduled at 23:47:57Z (one-shot, deliver local, the 7-tool allowlist).

- SHARED-WORKTREE INCIDENT (s253): `git add -A` at the main landing swept a
  concurrent out-of-chain actor's UNCOMMITTED M299 WIP into 51b9c4b; they then
  self-committed on top (0ff59c7, local, unpushed). My index-withdrawal was
  therefore UN-DONE (it would have reverted THEIR commit and, pushed, published
  their unreviewed work). Left: their WIP in main's 51b9c4b snapshot + their
  local commit for the operator; my docs warning sits UNCOMMITTED here on
  purpose. RULE: stage NAMED paths only on n100; check `git status --short`.

## Session 254 (2026-11-11/12, STATIC, zero box) - #264 LANDED by this fire + M299 CLOSED
- OPEN-PR JOB: on-head `python3 -m sim.selftest --b18 programs/saves/m54b_clean.SAV` ->
  **PASS 10/10**; `python3 scripts/gate.py --base main` -> GREEN; #264 squashed to main as
  **487f0b4** (23:52:47Z) with a GREPTILE-SILENT body note (no comment AND no check run on
  head 6ce43b5 within the 10-min cap - amendment 3). B1-B18 DONE.
- COLLISION (rule C): the s253 fire stayed LIVE while this s254 fire ran (amendment 7 booked
  s254 "in 1m", overlapping s253's own merge+landing). Sequence: s254 merged #264 first;
  s253's landing `git add -A` (51b9c4b) swept this fire's uncommitted M299 WIP into main,
  then index-withdrew it (12d6ad2), then reset main back to 0ff59c7 (this fire's pinned
  skeleton, adopted). This fire restored the swept files, pinned its work (branch
  `s254-collision-m299`) and finished ALL of it inside an isolated `git worktree`
  (`~/reverse/wt-s254`, scratch/ symlinked). s253's two warnings (NEXT_PROMPT bullet +
  notes line) are ADOPTED into this PR. LESSONS carried to s255: schedule "in 12m";
  collision-check + worktree FIRST; stage NAMED paths, NEVER `add -A`.
- M299 (THE PICK from the B18 leads): the slot [+4] visit counter's FUN_005832b0 gate.
  `python3 scripts/m299_visitgate.py` -> **PASS M299: 7/7** (evidence/m299_visitgate.txt,
  46 pins + windows W1/W2): G2 the call passes the pinned (x,y) push-slot pair shared with
  0x5aff90/0x582cc0; G3 the callee fold DECODES to the shared 44-B tile_record law (4096/
  4096, sar included); G4 `je 0x51e11d` gates the lone `inc`+`mov [esi+0x989cec]` = slot
  base + 4 on the pinned 28*site esi (0 writes to esi in between; callee pops ebx/esi/edi
  on all 6 rets); G5 PURE 4-rung ladder (0x102000 = B16 occ bit5|byte10 bit4 / 0x985ac4
  bit 0x2000 / 0xc000000 / 0x10000000 / 0x92a380==0, 0x92a380 = **rand+1** per
  MAP_FORMAT.md:116); G6 parity lattice (h&3)+4*(d&3), branch A exactly 1/16 classes
  36/36, 13/13 constants cross-tool; G7 the s249 2048-record dump MEETS the inputs:
  rung1-close 481, occ 16, bits26/27 12, rung3-open 5, class>=0x60 1087. DECLARED:
  counter VALUES + 0x92a380/0x692210/0x69220c VALUES never recorded.
- ACCEPTANCE: `python3 scripts/gate.py --base main` -> GREEN on this branch; merge #265
  per the MERGE RULE (Greptile cap 10 min). Box: ZERO.

## Session 255 (2026-11-15, STATIC, zero box) - M300: the 24 callers of FUN_005832b0 censused; only 0x51dffd gates the [+4] write
- THE PICK from the M299 lead list. `python3 scripts/m300_callers.py` -> **PASS M300:
  12/12** (every quoted number computed+asserted there; `evidence/m300_callers.txt`).
- S1: 24 call sites in scratch/m574/text.txt == Ghidra index.csv n_callers (two
  instruments); 0x5832b0 NEVER appears outside a call rel32 -> no indirect/vtable use.
  24 sites span 13 caller functions (biggest FUN_0055f650: 7 sites, and the OPEN
  0x56c6de continue-leg lead lives INSIDE it).
- Gates supplied: 21/24 truth-branch (test eax,eax + je/jne; 0x50e216 also pushes the
  raw value as an arg - leg-ambiguous); 2 store the raw value to a frame slot (0x4cf907
  ->[ebp-0x1c], 0x5858fa ->[ebp-0x7c]); 1 converts sign to a 0x200 mask bit (0x568567
  mov ebx,eax; neg; sbb; and 0x200).
- Counter-writer uniqueness: whole-dump mentions of 0x989cec live ONLY in FUN_0051dcb0
  (5 lines; lone STORE = M299's 0x51e01b); the only other slot-base materialization is
  0x51dd05 `mov eax,0x989ce8` - same function. No caller function outside FUN_0051dcb0
  writes [+4] unless a pointer were passed in. DECLARED: pointer-passthrough +
  non-literal addressing out of static scope (the live "any other writer" watchpoint
  check remains OPEN).
- Reach to FUN_0051dcb0 (reverse BFS over DIRECT call edges; 11 direct sites in the
  writer): exactly 1 site (0x51dffd) feeds the counter gate; 1 (0x59ddf4, FUN_0059ce10
  M94 walker) reaches it DIRECTLY;  15 sites / 7 fns reach transitively (depth 2-8:
  FUN_0055f650x7@d3, FUN_00585720x3@d2, FUN_0050d140x2@d4, FUN_004c40e0, FUN_004cf4c0,
  FUN_0051c750, FUN_0059e2c0); 6 sites CANNOT-REACH: FUN_0046a610, FUN_004e63b0 (M53q
  scan-pool rebuild), FUN_0058b1b0x3, FUN_005aff90 (B18 value body - sibling consumer
  of the same (x,y) fold, NOT nested in the counter path).
- NEW STATIC LAW: a straight-line post-call classifier must DIE at the next `call`
  (caller-saved eax) and treat conditional branches as both-legs; the raw S3w windows
  are the witness, class strings only labels. (rk-vs-t regex-anchor bug caught 3
  phantom value-arith classes before submit - windows audit clean after.)
- Box: ZERO (s244 state untouched). NEXT_PROMPT rewritten for s256.

## Session 256 (2026-11-15, STATIC, zero box) - M301: the lead "ebx's table 0x51de2c-0x51df1d" is REFUTED - it is a base_array walk, not a table
- THE PICK from the M294 lead list. `python3 scripts/m301_ebxtable.py` -> **PASS M301: 8/8**
  (every quoted number computed+asserted there; `evidence/m301_ebxtable.txt`, 199 ln).
- (a) ENTRIES: ZERO. The range is 0xf3 = 243 B (ends on the last byte of `test ebx,ebx`
  0x51df1d): 60 4-B dword slots + 3 B leftover, and 0 dwords - aligned or at any byte offset -
  resolve to a VA inside .text; the span tiles GAP-FREE as 81 instructions = 68 of ONE loop
  (0x51de27-0x51deef, sole back edge `jl 0x51de27`) + 13 of its straight-line exit block, and
  contains 4 `call 0x64b870`. (`m301_ebxtable.txt:95-104`)
- (b) NATURE: executable CODE - not code addresses, pointers, masks or offsets. 243 B read
  straight out of the PE file image (programs/terran.exe, .text, file off 0x11de2c) are
  BYTE-IDENTICAL to the dump; Ghidra n_insns 386 == the dump's instruction count over the
  function window; 0 indirect jmp/call in all of FUN_0051dcb0; 0 lea/mov/push of any range
  address image-wide; the 4 external edges into the range all target its EXIT BLOCK
  (0x51de05, 0x51de19, 0x51ddc0, 0x51dded -> 0x51defd), none enters the walk. (A3 :115, A7 :191)
- (c) INDEXING: it walks the NAMED base_array 0x95da10 (NAMED.md:74). Base register eax =
  cursor, `mov eax,0x95da12` 0x51de1f = base+2 (row y field), spill/reload [ebp-0x14]; stride
  `add eax,0x130` 0x51dee2 = 304 B = that record size; index = trip counter [ebp-0x18] (0 at
  0x51de10, inc 0x51dee1) bounded by the BSS row count ds:0x985af4 (`test`/`jle` 0x51de17-19
  skip the walk whole, `cmp` 0x51dee7 drives the back edge). The value compared against the
  row's flag byte, ebx = BYTE[304*i + 0x95da14] (0x51ddff) with i = FUN_004e37f0's return
  (call 0x51ddb1): the scale chain 0x51ddf2/0x51ddf7/0x51ddfa evaluates to exactly 304*i. (A4/A5)
- (d) VERDICT: the range is UPSTREAM of 0x51dffd and gates NOTHING the [+4] write depends on.
  Of the 11 branches between the range exit and the call, ZERO land past the call - the
  ebx==0 leg `je 0x51dff5` 0x51dfd1 targets the PRE-CALL block, so the call and `test eax,eax`
  run on every leg, bypassed-walk included. ebx's only post-range consumers are the cell
  stores (0x51dfc9 `test ebx,ebx` / 0x51dfd3-0x51dff3) and the POST-STORE byte read 0x51e02c;
  the counter address is esi, the 28-B fold of [ebp-0xc] (M299), never ebx. FUN_005832b0's eax
  has exactly ONE consumer (`test eax,eax` 0x51e005), is overwritten at 0x51e024, and there are
  0 backward edges from after the call into the range - the predicate's return CANNOT reach it.
- RETRACTION: the "ebx's walked table (0x51de2c-0x51df1d) recorded as a LEAD" phrasing at
  NAMED.md:1009 (M294) is wrong - patched in place, and the resolution registered as ## M301.
- NEW STATIC LAW: before censusing "address X-Y is a table", run 4 falsifiers: (1) does the
  span tile gap-free as instructions from its OWN encoding bytes; (2) does any dword in it
  (aligned and byte-offset) resolve into .text; (3) is any address in it the operand of a
  NON-BRANCH instruction image-wide; (4) does the containing function contain an indirect
  jmp/call at all. 243 B of hand-read disassembly reads like a table until (1) runs.
- OPEN: whose record the exit block's BYTE[edi+0x7] belongs to (edi = [ebp-0x4], sole
  pre-range writer 0x51dd28); the walk's semantic predicate (a tile-class test on the 44-B
  tile view 0x51de5b-0x51de61 + a distance compare vs ds:0x8f0d34 0x51dece-0x51ded0, then 3
  `or ebx,-1` sentinels) - shape VERIFIED, meaning INFERRED.
- Box: ZERO (s244 state untouched). NEXT_PROMPT rewritten for s257.

## Session 257 (2026-11-15, BUILD B19 10/10, zero box) - the slot [+4] visit counter made EXECUTABLE (sim/visitcounter.py); the rung was UNAUTHORED, this fire wrote it (as B14/B16/B17/B18)
- track_mode BUILD next_rung=B19 -> the rung B18 DECLARED ("the slot [+4] visit
  counter, its ++ gated on call 0x5832b0"), now that M299 (the gate body),
  M300 (the 24 callers) and M301 (the ebx deflection) have landed. ACCEPTANCE:
  `python3 -m sim.selftest --b19 programs/saves/m54b_clean.SAV` -> PASS B19
  10/10, output evidence/b19_visitcounter.txt (table first, then gates; two
  runs byte-identical, report sha256 e161b2f9...).
- HOW IT'S ANCHORED (skill law: constants read out of the bytes, instruments
  that fail differently): the model PARSSES the pinned W1 (44 lines
  0x51dfac-0x51e02c) / W2 (114 lines 0x5832b0-0x5833b7) windows out of
  evidence/m299_visitgate.txt ITSELF and decodes every constant from the
  instruction texts (rung masks, the ds:0x985ac4/0x92a380/0x69220c/0x692210
  globals, the lattice coefs -5/-3 as neg/shl/sub and lea[+*2]/sub chains, the
  counter operand [esi+0x989cec] == the MAX operand +4, the 28-B slot stride as
  (8-1)<<2); adjacency is by ORDERED INSTRUCTIONS, not addr+1 arithmetic
  (instruction lengths differ - the addr+k scan initially missed the sub
  ebx,edx leg). Branch A runs as TWO implementations (the decoded chain vs
  M299's closed rungA) that must agree (0/76960 disagreements) AND reproduce
  the RECORDED 36/36 lattice theorem; the recorded census 481/16/12/5/1087 +
  dump digest 093d10a868da55b2 re-grade through the model's OWN rung readers.
- MEASURED (this fire's anchors, RECORDED population cited): over the 2321
  recorded decision rows (B17 loader + B16 transposition + B18 site_of law,
  sites {1:2253, 9:68} == B18's RECORDED anchor - the counter table and the
  MAX table are the SAME 28-B slots, +4 vs +0): 1222 rows CERTAINLY REFUSE
  (rung1 mask hit - no live state can increment), 0 CERTAINLY ACCEPT (the
  class is pass1 & bits26/27 & bit28: EMPTY in the dump AND in the rows), the
  remaining 1099 are UNDECIDED-but-possible and ALL are branch-A domain
  (census {'branchA':1099,'rung1':1222}); under the DECLARED baseline
  Live(flag2000=False, rand=1): 20 accepts (all eax=2 branch-A parity hits),
  1079 undecided (parity misses falling to the never-recorded branch-B stride
  lattice). The eax=1 return is STRUCTURAL ONLY in this window: 0 graded rows
  and (with sel clear, flag-clear leg) 5 dump records reach the rung3 leg -
  no 'only-2-accepts' rival is gradeable on the rows (DECLARED, G9).
  Save-vs-live record views diverge on 4008 counter-table field deltas over
  the same rows (the B16/B18 drift law, counted not smoothed).
- RETRACTED/CORRECTED: none of prior claims - B18's DECLARED list entry for
  the counter is now CLOSED (module executable); its live-VALUES entry stays
  OPEN and SHARPENS: the next read-only /proc pass that dumps ds:0x92a380,
  ds:0x69220c, ds:0x692210, ds:0x985ac4 + the 0x989ce8/0x94eca8 tables grades
  every B19 number ABSOLUTELY (the LEAD already in NEXT_PROMPT).
- PITFALLS: (1) a rung whose rivals need a POPULATION that the recorded window
  leaves EMPTY must say so (G9's eax=1 note) - do not grade a rival on zero
  witnesses; (2) evidence-file-embedded disassembly is a first-class PIN
  SOURCE: parse it, and keep the window edge honest (M301's 6th eax mention
  0x51e033 lies PAST W1's end 0x51e02c - compare inside-the-window lists,
  say so); (3) sim/selftest acceptance paths must not double-print a verdict -
  the module CLI owns its PASS line, the rung's PASS line belongs to
  sim.selftest (it adds G10).
- Box: ZERO. NEXT_PROMPT rewritten for s258.

## Session 258 (2026-11-15, BOX-READ read-only /proc) - M302: B19's declared-unmodeled live values pinned; the 1099 undecided branchA rows collapse to 38 accept / 1061 refuse
- ACCEPTANCE `python3 scripts/m302_livepins.py` -> PASS M302 10/10,
  evidence/m302_livepins.txt (table first, then A1..A10; verdict :170). READ-
  ONLY on the box throughout: os.pread on /proc/501182/mem (pid from pgrep -x
  terran.exe), no pwrite/gdb/poke/relaunch; TracerPid printed 0 at start AND
  end; year 2150 + round 50 unchanged across the pass (A10); an unmapped read
  reports UNKNOWN (self-tested via the 0x1000 sentinel, A2), never 0.
- PINNED (y2150, m54b_clean): ds:0x92a380 (rand+1) = 9661 (0x25bd; & 0xf = 13),
  ds:0x69220c = 61, ds:0x692210 = 11, ds:0x985ac4 = 0x1a0e so bit 0x2000 is
  CLEAR - flag2000=False, B19's declared baseline bit-state CONFIRMED live.
  Slot region 0x989ce8+28*site: 128/128 slots readable (3584 B, no UNKNOWNs);
  the recorded sites: site 1 MAX 15 / counter 40, site 9 MAX 3 / counter 2;
  nonzero MAX sites [1,3,4,5,6,7,9,10,13,14,15,16,65,66,69,70], nonzero CNT
  [1,6,9,13,16,63,65,70]. The table is NONZERO at a freshly-loaded idle box ->
  carried by the save or rebuilt at load (OPEN); CNT>MAX occurs at [1,63,65] -
  no landed law relates the two fields (MAX is fed by the 4-bit nibble cache
  or the UNMODELED FUN_005aff90 body), so counter<=MAX is PRINTED, never
  asserted; the two-pass read never decreased any field (MAX store + ++ are
  the only writers, B18 G8 + B19 - A5).
- REPLAY (shipped sim.visitcounter rows/P/grid + the pinned Live): 2321 rows ->
  CERTAIN-accept 38 / CERTAIN-refuse 2283 / still-undecided 0. The 1099
  previously-undecided branchA rows: 38 CERTAIN-accept / 1061 CERTAIN-refuse /
  0 undecided (A8), per-B18-site {1:(38,993), 9:(0,68)} == B18's anchor rows.
  Legs: 37 branchA-hit (eax=2, live residue 13) + 1 branchB (eax=1 - the FIRST
  non-structural eax=1 decision row; B19 had 0 witnesses) + 1062 branchB-refuse;
  all 1222 rung1 rows still refuse (A6); eax in {0,1,2} (A7). B19's 20
  baseline accepts (rand==1) ALL flip - the 38 live accepts are a different row set.
- PITFALL: the `s` field of the m294 graded_rows tuple is the LOG SLOT key, NOT
  B18's site id - per-site splits must go through sgt.site_of(rec); the first
  run printed 25 "sites" (a mislabel caught only by pairing against B18's
  {1,9} anchor).

## Session 259 (2026-11-15, ANALYSE, zero box) - M303: the 0x51e02c "post-counter read" is the LOAD HALF of a byte CNT++ on the per-block twin of the slot table
- ACCEPTANCE `python3 scripts/m303_downstream.py` -> PASS M303 10/10,
  evidence/m303_downstream.txt (S0-S9 tables, then A1..A10; two runs byte-identical).
- MODE: track_mode printed ANALYSE (analyse_since_build=1, next_rung B20) although
  the s258 NEXT_PROMPT pick claimed a merge flips the next fire to BUILD -
  track_mode is authoritative (the kickoff itself said so); B20 stays queued.
- THE ANSWER: 0x51e02c is not a read-for-a-test - it is load++store
  (0x51e02c mov dl / 0x51e033 lea eax,[SAME SIB+disp] / 0x51e03a inc dl /
  0x51e03e mov [eax],dl), entered on the SAME `je 0x51e007` fall-through as the
  dword CNT++ (M299), inside FUN_0051dcb0 (the per-map-tile pass: outer loop
  advances tile records by 0x2c at 0x51e128). Byte addr = site + 8380*block +
  0x94ed28 - shadow-fold 65=64+1 -> 131=1+2*65 -> 2095=131*16-1 -> *4; the two
  6-insn folds (0x51dfd3/0x51e013) are BYTE-IDENTICAL (rematerialized across the
  0x51dffd call). The table: 0x94ed28 = 0x94eca8+0x80, the per-block visit-CNT
  byte array, twin of the MAX byte array at 0x94eca8: 8 blocks x 8380-B records
  (init 0x51dcb8-0x51dd03: byte fields [edx+site] and [edx+site+0x80] zeroed,
  edx steps 0x20bc to 0x95f288 - the SAME 8380 the fold computes, derived twice),
  128 entries x 1 B - the BYTE twin keyed by (block,site) of the DWORD slot
  table 0x989ce8 keyed by site. B18-28-B REFUTED for THIS expression:
  (site*8-site)<<2=28*site is the esi fold 0x51dfb1-ba three insns earlier
  (SIB 8d 34 c5 vs 8d 04 53), feeding the DWORD twin; multipliers 28 and 8380
  coexist in one window.
- CONSUMER CENSUS: 11 literal mentions = the whole corpus (A1); MAX field: 6
  external readers (FUN_0050d140/FUN_00556690/FUN_0055f650x4) + the in-window
  max-store 0x51dff3 (gated ebx!=0 by je 0x51dff5); CNT field: ONE external
  reader FUN_004f6030 0x4f946d -> test al,al/jne (a visited? gate). ALL
  external consumers terminate in cmp/test (A7); NO family byte feeds the DWORD
  0x989ce8 (both MAX stores take the walk candidate edi; loaded bytes appear
  only in the cmp); NO store to family/twin outside FUN_0051dcb0 (A8: 6 init
  zeros + 5 update sites incl. the sibling `inc WORD[0x94e8a8]` @0x51df3d -
  same 8380 block phase, width 2, scale *2: proof the *4 at 0x51e02c is
  multiplier placement, not entry width). The post-store branch 0x51e040 `je`
  tests `test ebx,ebx` flags, never the byte; dl dead after 0x51e03e.
  name_global.py 0x94ed28 --disp says "0 writes" - correct about LITERAL writes
  only; the 0x51e03e store is register-after-lea pointer form (A10) - the
  two-instrument disagreement is the finding's teeth.
- PITFALL: byte-reg->dword-reg naming must be a lookup table, NOT `reg[0]+"ax"`
  (that yields "aax"): three S6 rows printed "no consumer" until fixed - the
  A7 assert (every reader finds a consumer) is what caught it, i.e. the
  table-then-assert shape earns its keep.

## Session 260 (2026-11-15, ANALYSE, zero box) - M304: the seven FUN_0055f650 predicate sites are chosen by the [ebp-0x44] CASE LADDER + per-arm loops; 0x56c6de is the hub's COMMON EXIT (7 jmps); M300's predicate frame slots are FOREIGN frames

- `python3 scripts/track_mode.py` -> MODE=ANALYSE (analyse_since_build=2, next_rung=B20); M303 merged as #271.
- `python3 scripts/m304_chooser.py` -> **PASS M304: 12/12** (A1-A12; two runs byte-identical; zero box/proc/gdb) -> `evidence/m304_chooser.txt`. CFG of the entry-window [0x55f650,0x56cb23) (index.csv size 0xd4d3; Ghidra n_insns 16822 vs 16845 parsed): 3017 blocks, 5249 edges, 104 dominance-verified loops, 139 backward branches; the 7 sites recomputed == M300's table.
- Guards (closest pred jcc <- flag-setter <- decider <- producer, S2): 0x56429c `jne 0x5642b1`<-`cmp eax,3`<-`mov eax,[ebp-0x44]` (the CASE selector == 3); 0x56444b `jne 0x5644a8`<-`test dl,al`<-`mov dl,[ebp-0x64]` (+ arrival jne 0x56442c); 0x5645d9 ENTERED via `je 0x5645d0`<-`test eax,eax`<-`mov eax,[ebp-0xc]`; 0x5651e3 `je 0x56526c`<-`test eax,eax`<-`mov eax,[ebp-0x18]`; 0x568567 its ONLY pred is a **VACUOUS jne 0x56855f (target==next insn - jump-to-next artifact)** - unguarded on arrival, the chooser is the 18-leg upstream chain; 0x56b77c OR-arrivals: 3 jccs (`je`[ebp-0x74]==0, `jne`[ebp-0x40]!=0, `je`[ebp-0x6c]==0) + fall-through; 0x56c5f4 OR-arrivals: 4 jccs (`jne`[ebp-0xc]!=0, `jne`[ebp-0x40]!=1, `jl` class&~0x1f vs 0x60, `jne` BYTE[..+0x94e5a8] score-byte set) + fall-through.
- Loop-vs-paths: max sites in ONE loop span = 2 -> rival "ONE loop walks all 7" FAILS; all 7/7 inside loop spans -> rival "7 straight paths, ZERO loops" FAILS. Truth: a case ladder (31 `cmp [ebp-0x44],imm` in-window; slot writers 3, prologue producer 0x55f74a = type-record plan byte M127/B15) AND per-arm loops: X/Y grid walks ([ebp-0x4] +2, [ebp-0x8] +1, tails 0x5649c1/0x5649d3), 21-entry table walk (ebx +4 vs 0x54, tail 0x5645f2), [ebp-0x2c] walk (tail 0x56527b), [ebp-0x30] vs 9 (tail 0x5688a3), and the settle nest [ebp-0x70] vs 9 (0x56b061..0x56c6a0, tails 0x56c6a0; sites 6+7) x direction [ebp-0x4c] vs 8 (0x56c46c..0x56c670) x [ebp-0x54] vs 0x20 32-entry (0x56c4f9..0x56c660, site 7). B18's BRANCH-POLARITY law (evidence/b18_sitegate.txt G1) is the instrument law instantiated: leg semantics decode from branch landing, never address adjacency.
- The 0x56c6de leg: a block HEAD with **8 preds = 7 unconditional `jmp 0x56c6de`** (0x55fc5b, 0x561d8d, 0x563e0d, 0x566419, 0x56678b, 0x56832b, 0x569952 - each skipping 3669..16060 insns of the arms below it) + fall-through 0x56c6d7 (after BYTE[unit+0x2b]=0x78). The leg reads esi=[ebp-0x10], edi=[ebp-0x84] (best-direction; ZERO writers dominate it), `jge 0x56c966` = act, else clear unit flag bit 0x10000 (0x93327c and 0xfffeffff) + order byte 0x933289=0 -> `jmp 0x56cafa`; back edges 0x56c75b/0x56c76c/0x56c7a6 re-enter via 0x56c6d4 - it is the hub arms' COMMON EXIT + unit cleanup, not a per-predicate continue.
- CORRECTION to the M300 lead framing: NO hub site stores predicate eax to a frame slot (0/7 STORED-class; 6 truth-branch + 1 into-ebx sign->0x200 mask). In the hub frame [ebp-0x1c] is hot shared scratch (126 accesses / 79 writers / 43 nest-local, 0 dominating the leg) and [ebp-0x7c] is NEVER written inside the settle nest (25 accesses / 8 writers / 0 nest-local / 0 dominating) - at the leg it holds a STALE other-arm value. The M300 predicate-STORE slots are FOREIGN frames: FUN_004cf4c0 stores its [ebp-0x1c] at 0x4cf920 (21 B past the call) and FUN_00585720 stores its [ebp-0x7c] at 0x5858ff - each with EXACTLY ONE true reader (0x4cfef2, 0x589fe5, both `mov r32,[slot]`) - the M300 "readers of the stored predicate slots" lead is CLOSED.
- Instrument laws (NEW, skill code-atlas): (1) the scratch/m574/text.txt cache TRUNCATES long encoding-byte columns at 20 chars - never compute insn lengths from the byte column; (2) a CFG split must END blocks at every jcc/jmp/ret, not only before branch targets - the first M304 census printed 0 back edges because of target-only splitting; (3) some jcc are jump-to-next VACUOUS artifacts (target == next insn => no skip-leg; e.g. 0x568559) - mark them before calling them guards.
