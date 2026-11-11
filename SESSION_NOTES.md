

Older sessions: `docs/sessions/sessions-227-230.md` (4 sessions). Read it only when a question reaches back before session ## Session 231.

## Session 231 (2026-11-10, ANALYSE, M286 MEASURED-NEGATIVE w/ falsifier, static 5/5) - the REALLYQUIT message dialog IS family (live vptr 0x67164c at the click) but its clicks dispatch +0x4c through NONE of the 12 sites
- track_mode ANALYSE -> the M285 frontier pick: remaining Script.txt dialog
  suspects were message OK/CANCEL, menu panes, REALLYQUIT.  The box was ALREADY
  on the REALLYQUIT prompt (s229's closing Escape nudged... actually the brief
  read 'quit-prompt' but DIALOG_CUR=0; base display was open instead - the
  classifier misread).  Drive: Escape closes the base display (safe, M285),
  next Escape raises REALLYQUIT (M36), find 'oops' row by OCR, click it ONLY.
  scripts/m286_reallyquit_dispatch.py (arm = m285's 12 sites + FAM_SLOT entry
  0x5f6aa3 + pump 0x5f1394 + wndproc 0x5d0c33 LBUTTONDOWN control).
- STATIC (--static, evidence/m286_reallyquit_dispatch.txt): 5/5 gates. g1 the
  12 sites still read `call [reg+0x4c]`; g2 all 5 family vtables +0x4c ==
  0x5f6aa3; g3 image-wide scan finds EXACTLY 5 such vtables; g4 NEW: the slot
  target FUN_005f6aa3 is the dialog ROW-CLICK dispatcher - its 76-B body calls
  FUN_005e7917 (row finder over 0x18-stride rows, idx/-1) and on hit dispatches
  (**(code **)(*ecx + 0xa8))(local_c): family +0x4c IS the click->row-callback
  route of a Script.txt dialog; g5 Script.txt #REALLYQUIT pane has both rows
  (safe 'oops' + quit row).
- LIVE (--live): base display open (DIALOG_CUR=0).  Escape -> closes base
  display; Escape -> REALLYQUIT raised ('oops' row at (173,261)).  FALSIFIER
  READ at the click: dialog obj 0x014d7458 vptr 0x0067164c = FAMILY (the
  message OK/CANCEL class, 7 live instances in the pre-scan).  Clicked the
  safe 'oops' row + follow-up OK 47 px below (M37): pane closed (DIALOG_CUR
  back to 0, OCR 'pane gone').  PUMP RAN (1 hit), wndproc LBUTTONDOWN 2.
- RESULTS: site bps fired 0/12, family-slot hits NONE, FUN_005f6aa3 ENTRY 0.
  STATE 4 measured-negative WITH the falsifier satisfied: a live family dialog
  (0x67164c) at the click, its pump genuinely running, clicks delivered, pane
  closed - and +0x4c dispatched through NONE of the 12 sites.
- SETTLE: the message OK/CANCEL dialog class (0x67164c) does NOT dispatch
  family +0x4c on its click path - the click-to-row route must be inline in
  the pump, not via the +0x4c slot.  Combined with M284 (base display) and
  M285 (production chooser), THREE live dialog-ish paths now measured family
  or not-family with zero +0x4c dispatch.  The +0x4c slot (FUN_005f6aa3) has
  still never been observed dispatched from ANY live click window.
- ACCEPTANCE: python3 scripts/m286_reallyquit_dispatch.py --static -> 5/5
  PASS; live STATE 4 measured-negative with the live-vptr falsifier + pump
  control + pane-closed readback (one real invocation).
- OPEN (narrowed): M282 G5 (founder vector - box); the 64x64 odd-Rw stride
  quirk; the save-side cursor-vs-pending write order (M70); B12 rung pending.
  NEW narrowing: of the M285 frontier's three remaining dialog candidates,
  REALLYQUIT (== message OK/CANCEL class 0x67164c) is now ELIMINATED on the
  click path.  Remaining: the MENU PANES (TOPMENU/MAPMENU) - if those are
  family and their clicks dispatch +0x4c, the dispatcher is named.  Next
  fire: ANALYSE.

## Session 232 (2026-11-10, ANALYSE, M287 MEASURED-NEGATIVE w/ falsifier, static 5/5) - the in-game game MENU pane is NOT family (live vptr 0x67919c at the click); FOUR click paths now measured, zero +0x4c dispatch anywhere
- track_mode ANALYSE -> the M286 frontier pick: the last click-path candidate,
  the MENU PANE.  Static: the console bar (MENU button (61,369) -> GAME/HQ/
  NETWORK/MAP/ACTION/TERRAFORM/SCENARIO/EDIT MAP/HELP) is CHROME - its
  vocabulary appears in NO Script.txt pane (g4); the real menu is the popup
  the GAME row raises (12 rows, vision-verified on the live frame).  Drive
  (scripts/m287_menu_dispatch.py, arm = m286's 12 sites + FAM_SLOT 0x5f6aa3
  entry + pump + wndproc LBUTTONDOWN): normalize to HUD -> click MENU ->
  click GAME at (26,190) (GAME row does not OCR; NETWORK anchors y226, 18-px
  stride - geometry from TWO independent frames) -> FALSIFIER READ -> click
  ONE safe row (Preferences... at (172,350), vision coords; NEVER the y>=548
  Resign/Start/Quit rows) -> falsifier read 2 -> Escape-loop recovery
  (quit-prompt-safe: Escape on the bare HUD raised REALLYQUIT and the OLD
  normalize mistook the HUD status bar through it for clean - fixed).
- LIVE: bar raised (8 rows after MENU click), GAME clicked, popup OPEN
  (vision-verified).  FALSIFIER: LIVE menu obj=0x03cbc0c8 vptr=0x0067919c
  NOT FAMILY at the click (run 2 read DIALOG_CUR=0 - the pane is not even a
  DIALOG_CUR-tracked dialog that run, consistent with chrome/drawn).  Row
  click at Preferences -> same pane (no new dialog), vptr scan delta 0.
  RESULTS: site bps 0/12 (both runs), family-slot hits NONE, entry 0.
  STATE 4 measured-negative w/ falsifier.
- SETTLE: the in-game game menu pane is ALSO not one of the 5 family classes
  (the M285 chooser reading).  FOUR click paths now measured live with zero
  +0x4c dispatch: M284 base display, M285 chooser, M286 REALLYQUIT (family,
  inline row cb in pump), M287 menu pane.  The family +0x4c slot target
  FUN_005f6aa3 has STILL never been observed entered from ANY live click.
  +0x4c is NOT dispatched on any click path - next shape: Return-key path or
  dialog CREATE-time (FUN_00405ef0).
- ACCEPTANCE: python3 scripts/m287_menu_dispatch.py --static -> 5/5 PASS;
  --live -> STATE 4 measured-negative w/ live-vptr falsifier, twice
  (evidence/m287_menu_dispatch.txt).
- OPEN: M282 G5 (founder vector); 64x64 odd-Rw stride quirk (M247);
  negative-id table stride (M70); save-side cursor-vs-pending order (M70);
  B12 rung for the next BUILD fire.  Next fire: ANALYSE (frontier: the
  +0x4c dispatch question narrows to CREATE-time FUN_00405ef0 or the
  Return-key path; M282 G5 box question also open).

## Session 233 (2026-11-10, ANALYSE, M288 STATIC 5/5, no box time) - +0x4c CLOSED: CREATE-time and Return-key paths both avoid the slot; FUN_005f6aa3 is reachable only through a live family +0x4c dispatch which no reachable path takes
- track_mode ANALYSE -> the M287 frontier pick: +0x4c's two residual shapes,
  dialog CREATE-time (FUN_00405ef0 installs 0x67164c) vs the Return-key path.
  Static-only milestone (scripts/m288_create_key_dispatch.py, evidence/
  m288_create_key_dispatch.txt): instruction-cache + file-image censuses.
- g1: the 12 `call [reg+0x4c]` sites unchanged (M284 set).  g2: FUN_005f6aa3
  has 0 direct callers image-wide and its ONLY 5 data refs are the 5 family
  vtables' +0x4c entries (0x671698/0x671818/0x67290c/0x675d10/0x677714 =
  FAMILY[i]+0x4c): reachable ONLY via a live family +0x4c dispatch.
- g3 CREATE-time: 466 family-vptr install sites live in 72 owner functions,
  and install-owner set INTERSECTS site-owner set = EMPTY; the 0x67164c
  installer FUN_00405ef0 + its two callees (FUN_005ee350, FUN_005f6b8c)
  contain no +0x4c call and no 0x5f6aa3 ref.  A vptr install never
  dispatches the slot.
- g4 Return-key: WM_KEYDOWN (0x100) -> FUN_005d1576 -> vtable +0x12c (all 5
  family vtables = 0x5d629d, a hotkey dispatcher) -> FUN_005cf43a -> vtable
  +0x60 dispatch; WM_CHAR 0x102 -> FUN_005d15d5; WM_SYSKEYDOWN 0x104 ->
  FUN_005d1601; the pump FUN_005f1394 (INLINE row callback, M286).  NONE of
  the six chain bodies contains a +0x4c CALL dispatch (M284 forms: call
  [reg+0x4c] or load-then-call pair).  One data load found and REFUTED:
  0x5d632d `mov eax,[edx+0x4c]` feeds FUN_00631070(hotkey-table+0x4c) - a
  DATA read of the hotkey binding, not a +0x4c dispatch.
- g5: the 11 site-owner functions' DIRECT callers are all outside both paths
  (FUN_004c6530, FUN_00404fb0, FUN_004c6e40, FUN_005b3e70, FUN_005d65bb,
  FUN_005fc20f, FUN_005faae5, FUN_005faca2, FUN_006302ac, FUN_0063cbb0,
  FUN_0063cc31; four owners have no direct callers at all = vtable/table
  entries themselves).  None is a family-vptr installer or a key-chain fn.
- RESULT: STATIC PASS 5/5 (one invocation; also re-run x4 identical).  The
  +0x4c family slot (FUN_005f6aa3, the dialog row-click dispatcher) is
  reachable ONLY through a live family +0x4c dispatch, and FOUR live click
  paths (M284/M285/M286/M287) plus this static closure of CREATE-time and the
  key path show no reachable path takes it.  The M284-M287 series is now
  complete: +0x4c is dispatched on NO click, NO key, NO create path.  The
  row callback lives inline in the pump (0x5f1394, M286).
- ACCEPTANCE: python3 scripts/m288_create_key_dispatch.py -> STATIC PASS
  (5/5) with the printed table in evidence/m288_create_key_dispatch.txt.
- OPEN (unchanged): M282 G5 (which founder vector the recorded AI used -
  live box question); 64x64 odd-Rw accessor stride quirk (M247); negative-id
  table stride (M70); save-side cursor-vs-pending order (M70); B12 rung for
  the next BUILD fire.  Next fire: ANALYSE.

## Session 234 (2026-11-10, BUILD, B12 CREATE leg 12/12, no box time) - the completion's produced unit RECORD: gate(8+1>=9) -> pay to 0 -> one new 52-B record (29,42,type2,owner3,order 0) appended at the array END -> pop, replayed against the game's OWN recorded m56 boundaries byte-for-byte; MERGED #240
- track_mode BUILD -> rung B12 written into BUILD_SPINE.md FIRST (per chapter R),
  then built.  sim/production.py: the M56/M59/M61 completion law - GATE (storage
  + income >= price, the income add inside the same visit), PAY (storage -= 
  price), CREATE (a NEW 52-B unit record appended at units_off + n_units*52:
  x@0 u16, y@2 u16, flag@4 u32=0, type@10 u16 = the queue head, owner@14 u8 =
  the base faction, order@17 u8 = 0, nlegs@18 u8 = 0; the rest declared
  unmodeled, composed as zero), POP (B11 law: one item, stale tail).  The
  rung was written first: the CREATE leg is the piece B11 deliberately left
  out (B11 stops at pay+pop; the unit record itself was never composed).
- ACCEPTANCE: python3 -m sim.selftest --b12 programs/saves/m54b_clean.SAV
  evidence/trace_m56_build_20261026_145157.jsonl -> PASS B12 12/12
  (evidence/b12_production.txt).  The trace is the ORIGINAL terran.exe's own
  10-boundary run on Korolev Center (29,42) head 2: the model reproduces
  exactly +1 (29,42,2,3,order 0) at r0 (the recorded net unit-array delta,
  and the record's idx == n_units-1, the append law) and zero later
  (r1..r9, gate fails: pending 0 / storage+income < price).  Pay+pop: the
  model's post-visit storage 0 + queue [2,2,2,2,0,..] pending 0 == the
  recorded r1 round_before.  Three rivals fail the same fit: wrong tile
  (28,42), order 2 (the idle order - the r0 arrival is order 0, M56's "a
  produced unit arrives order 0 on its base tile"), and a gate without the
  income term (8 < 9 bails r0 against a recorded arrival).  Written image:
  savewriter append_units= (the B10 founded-image shape, for units) - only
  the units-count dword ([68]) plus the one 52-B record differ, originals
  byte-identical, bases+tail byte-identical after the 52-B shift, re-parse
  reads n_units 68 with the new record at the end, decode_save --sections
  green; two runs -> identical written_sha256 259bd5ab8fcc6e88; the CLI
  python3 -m sim.production --sav <sav> --trace <tr> --out <f> exits 0.
- SETTLE: B1-B12 done.  R2's "build lands a unit" slice is now executable
  end-to-end: queue (B11) -> completion create (B12) -> save write (B8).
- OPEN (unchanged): M282 G5 (which founder vector the recorded AI used -
  live box question); 64x64 odd-Rw accessor stride quirk (M247); negative-id
  table stride (M70); save-side cursor-vs-pending order (M70).  Next fire:
  ANALYSE - the pick NEXT_PROMPT names (M282 G5 or the frontier).

## Session 235 (2026-11-10, ANALYSE, M289 LIVE 7/7, box time) - which founder vector the recorded AI used: the AI HUB FUN_0055f650 -> FUN_004cca50 -> founder FUN_004e47d0; 7/7 live foundings on a 30-turn m54b_clean window, the 0x4408 action-dispatch leg 0, the 5a0aa0 chain entered 3x but completed 0; count 18->23 exact with 2 destroys; MERGED #241
- track_mode ANALYSE -> the M282 G5 frontier (NEXT_PROMPT pick): which founder
  vector the recorded AI used - 0x4408 vs 0x5f650 vs the 5a0aa0 chain.  Live-box
  milestone (the one open live question).  scripts/m289_founder_vector.py arms
  ONE silent breakpoint PER VECTOR at the call site unique to it (image-wide
  proof: exactly 3 call sites load FUN_004cca50, 3 load FUN_0059ec90) + the
  founder entry (ret/fac/x/y/live count) + the destroyer -1 store (0x4e515d) +
  the sweep-entry control (0x4e8d60); drives the clean save with the AI for 30
  turns (smac_play --no-orders so OUR side stays inert), then detaches and
  classifies every founder hit by the vector site that fired just before it.
- MEASURED: 7/7 founder hits ALL vec=hub (ret 0x4ccbe2 via FUN_004cca50, caller
  site 0x563d86 inside FUN_0055f650); fac 6,6,6,5,7,1,6 at (20,48)(63,51)(12,48)
  (27,19)(23,33)(27,29)(1,43); 3 "VEC chain" entries (FUN_005a0aa0->59ec90) with
  ZERO completed foundings (the faction-create path bailed each time - open
  why); 0 v4408, 0 hotkey.  Count accounting strict: 18,19,20 (+3) DESTROY
  (21), 20,21,22,23 (+4) DESTROY (24) -> box end 23, late=0.  Control: 1627
  sweep rows; driver rc 0; yama toggled and verified restored.
- REFUTES M282's static thesis ("reached live via the 0x4408 action-dispatch
  leg"): the 0x4408 path EXISTS (G5 static) but the live AI never took it in
  this window - it calls the founder through the hub's DIRECT call.
- ACCEPTANCE 1: python3 scripts/m289_founder_vector.py 30 -> rc 0, VERDICT
  MEASURED (evidence/m289_founder_vector.txt + scratch/m289_gdb_raw.log copied
  to evidence/m289_gdb_raw.log).  ACCEPTANCE 2 (independent re-walk of the raw
  log): python3 scripts/m289_accept.py -> PASS M289: 6/6 - founder vector(s):
  {'hub': 7} (evidence/m289_accept.txt).
- BONUS: the census produced a NEW golden trace evidence/trace_m289_20261110_
  071759.jsonl (30 turns, year 2150->2180, n_bases 18->23) - the first trace
  carrying 7 REAL founding (faction,x,y) events for the sim to fit.
- BOX HYGIENE (two NEW traps, both fixed in-session): (a) yama ptrace_scope=1
  blocks n100's own /proc/pid/mem reads (smac_state/accept_ready EACCES) - the
  box's working default is 0 and the census must restore the PRE-toggle value,
  not hardcode 1; (b) root-owned /tmp/acceptready* frames (left by an earlier
  sudo run) make accept_ready's freeze fail silently and it classifies a STALE
  frame (byte-identical quit-prompt ghost) - chown them back to n100.  Also:
  the reallyquit dialog dismisses via click Oops row (400,268) then OK (~319),
  Escape/Return alone looped.
- OPEN: why the 5a0aa0 chain bailed 3x; the hub's founding DECISION rule (which
  pod/tile/faction) vs B10's assumed first-unoccupied; M247; M70 x2.  Next:
  ANALYSE - fit the hub founder decision to the m289 trace.

## Session 236 (2026-11-10, ANALYSE, M290 9/9, no box time) - the hub's FOUNDING DECISION fitted to the m289 record: the dispatch is OWN-TILE-GATED (a distant target takes the 0x2408 auto-build message and can NEVER found); founder args are the POD RECORD's owner@+14/y@+10/x@+8, so the tile choice is entirely the pod's walk; B10's first-unoccupied rule REFUTED (recorded ranks 542-1691 of 2146)
- track_mode ANALYSE -> the s235 frontier pick: fit the hub founder decision
  to the m289 record, static+model, no box.  scripts/m290_hub_decision.py,
  9 byte-level/fit gates.  ACCEPTANCE: python3 scripts/m290_hub_decision.py
  programs/saves/m54b_clean.SAV evidence/m289_gdb_raw.log
  evidence/trace_m289_20261110_071759.jsonl -> PASS M290: 9/9 (3rd
  invocation; runs 1-2 were instrument bugs, floors never weakened).
- MEASURED (bytes are the arbiter): hub dispatch 0x563d3c-0x563d8b - cmp
  [ebp-0x44],8 (settle case), test esi,esi / jne 0x563dfa: esi = the scan's
  CHOSEN target offset, ZERO = the unit's own tile -> 0x563d86 call
  FUN_004cca50; nonzero -> 0x563d4e leg push 0x2408 + call FUN_00583fa0
  ("Auto-sending BUILD BASE message") and NO founder call.  Vector
  prologue 0x4cca57-0x4cca74 folds 52*u then loads cl=owner[+14],
  eax=y[+10], edi=x[+8]; 0x4ccbda-dc push edx/edi/esi, 0x4ccbdd call
  founder - the FOUND ret=0x4ccbe2 of all 7 recorded foundings.  Founder
  FUN_004e47d0: capacity guard ONLY (count<0x200), no tile-legality bail.
- FIT to the 7 sites: ALL land (cat 3-6 via the 44-B RECORD view:
  rec=(W/2)*y+(x>>1), byte 0 of the record's first half) AND none already
  a base tile; ledger FOUND cnt=18,19,20,20,21,22,23 + 2 DESTROY rows
  (between F3/F4 and after F7) replay to endpoint 23 with peak 24,
  matching the jsonl per-turn curve (same-turn found+destroy nets are
  invisible per-turn - the M289 +3->20 accounting).
- RIVAL REFUTED: sim/basefound.py:118 "ASSUMED: first in-bounds tile no
  base occupies (row-major)" - the recorded sites rank 542-1691 of 2146
  unoccupied-land tiles in that order (mean 1202): B10's TILE rule explains
  NO real founding's coords (its record/curve machinery stays valid; only
  the (x,y) choice was a placeholder).
- NEW TRAP (fired on run 1): the save's 22-B COLUMN view (sim/save.py
  tile()[0]) does NOT reproduce the live byte-0 category - 5/7 legal sites
  misread cat 0.  Read the 44-B record view instead (record =
  grid_off + 44*((W/2)*y + (x>>1)), byte 0 = the live category).
- OPEN (unchanged): why the 5a0aa0 chain bailed 3x; M247; M70 x2.  NEW
  OPEN: which pod the hub picks and the walk TARGET (the scan's score
  law at 0x563c00-0x563d40, (dist*10000)/(value+1) shape) vs the recorded
  founding TURNS - the decision is now reduced to POD MOVEMENT.
  Next: ANALYSE - the pod-walk target rule.

## Session 237 (2026-11-10, BUILD, B13 12/12) - M290's founder dispatch is EXECUTABLE: sim/hubfound.py - own-tile-gated (distant target = msg 0x2408, never founds), founder args = the POD's record fields, capacity-only guard; 7/7 recorded founding tuples replay exact, strict ledger 18+7-2=23 peak 24 vs the m289 curve, both rivals fail the same fit
- track_mode BUILD (3 ANALYSE fires since B12) -> the rung went into
  BUILD_SPINE.md FIRST (pod-driven founding-dispatch leg, replacing B10's
  REFUTED (x,y) placeholder), then sim/hubfound.py + run_b13 in sim.selftest.
- ACCEPTANCE: python3 -m sim.selftest --b13 programs/saves/m54b_clean.SAV
  -> PASS B13: 12/12 (evidence/b13_hubfound.txt; 3rd invocation; runs 1-2
  were instrument bugs - python3.14 argparse refuses a 3-tuple metavar with
  nargs='+', and a 6-tuple event unpack - floors never weakened).
- MEASURED: every one of the 9 recorded rows' PRE-op cnt agrees with the
  ledger replay through B10's leg (destroy slot ASSUMED last, declared);
  survivors (6,20,48)(6,63,51)(5,27,19)(7,23,33)(1,27,29), destroyed
  (6,12,48) and (6,1,43) ABSENT from the final 23; written image: only the
  bases-count dword (offset 72) differs in the prefix, originals + tail
  byte-identical, re-parses n_bases 23; cat44 (44-B record view) puts all 7
  sites on land (cat 3) and none on a base tile; G12 CLI two runs sha256
  6dfbd810a1b6013f. RIVALS: ungated distant dispatch invents 7 tuples of
  which 0 occur in the record; the B10 placeholder reproduces 0/7.
- REGRESSION: B10 18/18 and B12 12/12 still green (basefound._tile marked
  REFUTED, comment-only edit).
- OPEN (unchanged): why the 5a0aa0 chain bailed 3x; M247; M70 x2. The pod
  WALK stays the only unmodeled link between a pod and a founding.
  Next: ANALYSE - the pod-walk target rule (the scan's score law at
  0x563c00-0x563d40 vs the recorded founding TURNS).

## Session 238 (2026-11-10, ANALYSE, M291 10/10, no box time) - the hub's founding SCAN is a STRICT site-value argmax over a 25-entry even-manhattan ring, NOT a (dist*10000)/(value+1) score (that immediate is absent from the 54,483-B body); the record falsifies dropping the owner byte3 gate
- track_mode ANALYSE -> the s237 pick: the pod-walk target rule, static+model.
  scripts/m291_pod_scan.py, 10 gates. ACCEPTANCE: python3 scripts/m291_pod_scan.py
  -> PASS M291: 10/10 (evidence/m291_pod_scan.txt; 6th invocation - runs 1-5 were
  all instrument bugs of mine, floors never weakened: three x86 encoding mis-
  transcriptions (imm8-vs-imm32 for cmp eax,0x19; ModRM for cmp esi,[ebp-0x24])
  plus the heredoc transport that unescapes backslashes INSIDE heredoc content
  (byte literals landed on disk as raw bytes; the shipped script uses bytes([...])
  lists and no backslash classes, and an & even in a comment is refused by the wrapper).
- MEASURED (bytes from the terran.exe file image): ring tables 0x67850c/0x678990
  (.rdata, 25 dwords): entry 0 = own tile, 1-8 = the manhattan-2 diamond, 9-24 =
  manhattan-4, ascending; wrap 0x469010/0x469060. Value = FUN_0046e770: and-eax-
  0x1000 -> 0, else mov dl,[rec+2] + sar 4 (lazy FUN_005aff90 when the cache is 0).
  Strict max: cmp esi,eax then jle 0x563cb3 (ties keep the closer ring entry);
  best-store 0x563caa. Nearest-location distance FUN_004e3620 (9999 sentinel
  0x4e3631, store DAT_008f0d34 0x4e36f5, 152-B-stride location list, map-wrapped
  max-min octant formula); value >= 2*(8-DAT_008f0d34) bypasses the per-site
  0x94e5a8/0x94eca8 gates.
- FIT vs the 7 recorded tuples: 7/7 self-argmax over their own ring (grown
  occupancy, 44-B record view); the no-owngate variant loses EXACTLY fac1 (27,29)
  (byte3 14 vs a rival - owner-equality is required by the record); B10 first-
  unoccupied 0/7; seeded null self-argmax rate 27/88 = 0.307, binom p(7/7|null) 2.6e-4.
- Box: only the recon pass did a READ-ONLY /proc ring-table probe; the acceptance
  reads the .rdata file image. pid 4087359 untouched, TracerPid 0.
- OPEN (unchanged): the 5a0aa0 chain bailing 3x; M247; M70 x2. UNMODELED: the
  0x94e5a8/0x94eca8 gate tables and the 0x4e3c00 no-go (the 7/7 fit passed without
  modeling them). NEW frontier: POD MOVEMENT - which pod (callers of FUN_0055f650,
  unit id) and the per-turn walk vs the recorded founding turns (rise turns
  6,9,18,19,22,23); needs a unit-position census (box). Next: ANALYSE - the
  pod-movement leg.

## Session 239 (2026-11-10, ANALYSE, M292 5/5, BOX census) - pod MOVEMENT settled: the hub vector runs per-unit (arg1 = unit index) and dispatches on the m291 RING ENTRY INDEX esi - 0 = found (MSG 0x2408 if human-owned), 1-8 = continue w/o order, >=9 = issue order b (0x62) at the wrapped ring tile (the WALK); 9 FOUNDs / 26 turns, 2 walked pods
- track_mode ANALYSE -> the s238 pick. scripts/m292_pod_movement.py (static
  G1-G3 byte gates + live gdb census + parse + verdict). ACCEPTANCE:
  python3 scripts/m292_pod_movement.py --turns 26 -> PASS M292: 5/5
  (evidence/m292_pod_movement.txt + m292_gdb_raw.log; 2nd invocation - run 1
  at 12 turns scored 4/5 with only 1 FOUND, a window-length artifact not a
  refutation; floors never weakened).
- STATIC (bytes arbiter): hub 0x55f65c mov edi,[ebp+8] = unit index; 13u*4
  fold 0x55f6b8-0x55f6bf -> record 0x933278+52u (x@+0 y@+2 owner@+14); own
  flag = owner vs ds:0x91b5b4 (live value 3 = HUMAN fac). Exactly 2 call
  sites image-wide: 0x50dd84 (FUN_0050d140), 0x56cf12 (FUN_0056cdf0).
  Dispatch 0x563d46 test esi,esi (esi = ring entry): 0, not-own ->
  0x563d82-86 push u, call FUN_004cca50 (FOUND); 0, own -> push 0x2408,
  0x563d75 call FUN_00583fa0 (MSG); 1-8 -> 0x563e06 dec esi, no order;
  >=9 -> tables 0x678990/0x67850c[esi] + own tile, wrap FUN_00469010,
  0x563e3b call FUN_005560f0(u, 0x62, tile) = the walk order.
- LIVE (m54b_clean t0 continued, 26 turns 2150->2188): HUB=2308 (ret
  0x56cf17 x2282 per-unit + 0x50dd89 x26 once-round); DISP=29, st==8 on
  every row, ownflag==(ownrec==3) 29/29 (52u+14 owner arithmetic live);
  legs partition exactly: 9x esi=0 -> HUBFOUND, 9x esi 1-8, 11x esi>=9 ->
  ISS; FOUND=9 ALL ret=0x4ccbe2, cnt 18->27, every one paired
  same-segment with its HUBFOUND (x,y); WALK u=66 (53,47)->(53,49), u=60
  (27,51)->(1,43). FOUND facs {1,2,5,6,7}; golden tiles (20,48)(63,51)
  (1,43) reproduced; (27,29) taken by fac7 here (golden: fac1) - timelines
  diverged once run 1 founded (12,48) at t6.
- Box: pid 4087359 unchanged, TracerPid 0 pre/post, yama restored, no stale
  gdb. Evidence +92 KB (raw log 91,561 B), budget re-measured at close.
- OPEN (unchanged): 5a0aa0 bailing 3x; M247; M70 x2; 188-row cursor caller.
  NEW OPEN: who gates hub VISITS (FUN_0056cdf0/FUN_0050d140 entry tests)
  and the 0x56c6de continue-leg target. Next: ANALYSE - UNMODELED
  0x94e5a8/0x94eca8 per-site gate tables + FUN_004e3c00 no-go (static
  census + fit vs recorded sites); MSG-leg (human pod at best tile) never
  observed live. Next BUILD fire = B14.

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
  min 0x51dfc3 and max 0x51dfee-51dff3 (no reload); 0x51dfac reloads eax over only the
  DISCARDED return (rec base, lea 0x582ce6). Effect = CACHE WRITE-BACK: BYTE[rec2+2] =
  (old&0x0F)|(param_3<<4), rec2 = 0x92ae14+0x2c*(0x692184*param_2+sar(param_1,1)) -
  the same +2 high nibble the cached-path test 0x51df85 reads: next walk skips
  0x5aff90 (525 insns).
- (b) [ebp-0xc] caller hypothesis REFUTED: own frame (0x51dcb1 mov ebp,esp; 0x51dcb3
  sub esp,0x1c), void/0-args; EXACTLY ONE store in 386 insns: 0x51dd57
  mov [ebp-0xc],ecx = zero-extended BYTE[rec+3] (xor ecx 0x51dd48; mov cl,[edi+3]
  0x51dd4f); record cursor base [0x92ae14] 0x51dd1e, +0x2c at 0x51e128/0x51e133; the
  other 5 refs (0x51dd9f/df28/dfac/e021/e0cc) loads; store precedes first load.
  Site/region index is record byte +3, not caller-supplied.
- FINDING (phrasing fix): M294's `cell addr = 0x94eca8+[ebp-0xc]+4*min(...)` wrong -
  min(edi,slot) STORED 0x51dfcb to the 28B/site slot [28*[ebp-0xc]+0x989ce8] (esi via
  (x*8-x)<<2 0x51dfb1-ba); addr 0x51dfe2 = 0x94eca8+4*(2095*ebx)+[ebp-0xc] (0x51dfd3-e0
  65x/131x/<<4/-x; 4*2095 = 8380 = M297 faction block stride); cell = max(edi,old)
  0x51dfeb-f3; ebx = scan idx (xor 0x51ddf5; -1 clamp 0x51df22-24); ebx==0 skips the
  cell store (test/je 0x51dfd1), min store survives. ebx's walked table
  (0x51de2c-0x51df1d) = recorded LEAD, not chased.
Evidence: evidence/s251_statics_fn51dcb0.txt (162 lines verbatim); dump
scratch/s251_fn51dcb0.txt. NAMED M298 block + line-1711 status closed. Gate GREEN.
