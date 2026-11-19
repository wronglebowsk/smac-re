# Session notes archive — sessions 231-233

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-227-230.md` (inserted at s292: the hot file cites only the newest archive, so without this line the older archives were orphans).

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
