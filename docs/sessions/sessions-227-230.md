# Session notes archive — sessions 227-230

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 227 (2026-11-10, ANALYSE, M283 PASS 17/17) - decode_save --sections walks 64x64 saves: the coarse-region-map length is ((W+4)/5+1)/2 * (H+4)/5 (91 B for 64x64, not 128)
- track_mode printed ANALYSE -> picked the s226 OPEN lead (decode_save's hardcoded 80x80
  map-trailer count offset fails rc=1 on every 64x64 save). Box untouched (zero box time).
  `python3 scripts/m283_sections_64x64.py` -> **SUMMARY M283: 17/17 section gates, count 17/17,
  formula True** (`evidence/m283_sections_64x64.txt`); acceptance on ONE real invocation.
- BUG: walk()'s MAP branch hardcoded the coarse region map at 128 B (the 80x80 value). For a
  64x64 save the region map is ((64+4)/5+1)/2 * (64+4)/5 = 7*13 = 91 B, so the walk read the
  count-prefixed section 37 B early: count u32 became garbage (c=67108869), the record region
  solved to 0 B -> "no 52/304 split of a 0-byte region", rc=1 on EVERY 64x64 save (m54b_clean
  included; B8's sec() equality stayed green only because both sides failed identically).
- FIX: walk() now derives the region length from the file's own dims (same formula as
  sim/save.py region_len, shard_014.c:27263-27265): 128 for 80x80, 91 for 64x64, 338 for
  128x128. Spans: 64x64 saves now walk to 21 sections that sum EXACTLY to the file byte; the
  count u32 lands at 188,299 (the sim/save.py predicted constant) on all 17 saved 64x64 saves;
  record splits agree with sim/save.py (m54b_clean 67x52 + 18x304 -> exact match of
  units_off/bases_off 222,783/226,267).
- B10's selftest gate had ENCODED the old limitation ("rc == rc; --sections fails on both") and
  FAILed after the fix -> updated to assert the new behavior: rc 0 == rc 0 and the grown founded
  image is seen with exactly ONE more 304-B record (67x52+19x304 vs 67x52+18x304). B10 re-PASS
  18/18, B8 10/10, B9 7/7 regressions GREEN (checkpoint ef5edf6); test_loop.py and
  test_save_diff.py (7/7) green.
- OPEN (unchanged): box pick (dialog +0x4c dispatcher, box UP m54b_clean); M282 G5 (which
  founder vector the recorded AI used per founding - box question); the 64x64 odd-Rw accessor
  stride quirk. Next fire: ANALYSE (analyse_since_build=1).

## Session 228 (2026-11-10, ANALYSE, M284 MEASURED-NEGATIVE) - the dialog family's +0x4c dispatch-form census is EXHAUSTIVE (12 sites, 0 load-then-call pairs, 0 direct calls, 5 vtables/466 installs) and the base-display click path does NOT dispatch it (live, wndproc-verified)
- track_mode printed ANALYSE -> picked the box lead: WHO dispatches the dialog family's +0x4c
  (FUN_005f6aa3).  Script: scripts/m284_dialog_dispatch.py.
- STATIC (--static, evidence/m284_dialog_dispatch.txt): the 12 single-insn `call [reg+0x4c]`
  sites are the COMPLETE dispatch-form set - a whole-image census found ZERO load-then-call
  pairs (`mov r,[r+0x4c]; call r` within 40 insns of the same function) and ZERO direct
  `call 0x5f6aa3`; FUN_005f6aa3 is +0x4c of exactly the same 5 vtables (466 installs) M214
  measured (method ported verbatim from m213_m216_hotspot.py).  Gates 4/4 PASS.
- LIVE (--live, scratch/m284.log): armed all 12 sites + FUN_005f6aa3 entry + a WNDPROC
  (0x5d0c33) WM_LBUTTONDOWN control, drove real xdotool clicks on the m54b_clean base display
  (b-then-clicks on the base screen).  Control fired 3x (clicks DID land in the window);
  the dialog pump FUN_005f1394 NEVER ran; zero of the 12 sites fired; FUN_005f6aa3 never
  entered.  STATE 4 measured-negative: the base display's click path does not dispatch the
  5-vtable family +0x4c through ANY of the 12 sites.
- WHY (settled context): the base display is a CPane screen, NOT one of the 5 family vtables
  (0x67164c/0x6717cc/0x6728c0/0x675cc4/0x6776c8 - those are Script.txt dialog classes); the
  modal pump 0x5f1394 stays silent on it, and its clicks route through the CPane/world
  handlers, not the dialog-family hotspot dispatcher.  The family +0x4c dispatcher is a
  SCRIPT.TXT-dialog-path question (chooser/menus), which this save's empty-queue state never
  opened.
- ACCEPTANCE: python3 scripts/m284_dialog_dispatch.py --static -> 4/4 PASS; live STATE 4
  measured-negative with the wndproc control fired 3x (evidence = scratch/m284.log rows).
- OPEN (unchanged): M282 G5 (which founder vector the recorded AI used per founding - box);
  the 64x64 odd-Rw accessor stride quirk.  NEW narrowing: the family +0x4c dispatcher must
  live on the Script.txt dialog (chooser/menu) path - open a real chooser (non-empty queue,
  m54g_prep + one turn per standing facts) and re-run the same instrument.  Next fire: ANALYSE.

## Session 229 (2026-11-10, ANALYSE, M285 MEASURED-NEGATIVE w/ falsifier, static 5/5) - a REAL Script.txt production chooser does NOT dispatch the family +0x4c either (live dialog at the click reads vptr 0x672298, non-family)
- track_mode ANALYSE -> the M284 re-scope pick: open a real chooser (m54g_prep + one turn
  per standing facts) and re-run the +0x4c instrument live, falsifier = a live vtable read
  at the click. scripts/m285_chooser_dispatch.py.
- STATIC (--static, evidence/m285_chooser_dispatch.txt): 5/5 gates. g1 the 12 sites still
  read `call [reg+0x4c]`; g2 all 5 family vtables' +0x4c == 0x5f6aa3; g3 whole-image scan
  finds EXACTLY 5 vtables holding +0x4c==0x5f6aa3 (the family is closed); g4 NEW: the
  production chooser class 0x672298 (M53g live vptr) +0x4c = 0x404ed0 stub, NOT family;
  g5 FUN_00405ef0 (dialog ctor) body contains the 0x67164c store (dialogs ARE family).
- LIVE (--live): m54g_prep --unit 0 (rec0 -> type 0 colonist at (29,42)) then one boundary
  (2153->2154, m55_boundary PASS) -> candidate array 67 items [192,194,193,2,0,1,...] per
  standing facts. Armed all 12 sites + FUN_005f6aa3 entry + pump 0x5f1394 + wndproc
  0x5d0c33 WM_LBUTTONDOWN control. Opened the base display (b), ROW1 click opened the
  production item chooser, clicked cell k=2 (382,60), INSERT bar (497,343), OK bar
  (285,343). READ-BACK: base0 pending 0->1, slots [0,193,0,0,0,0] - the INSERT LANDED,
  the clicks really drove the chooser's own handlers at minerals 0 / credit 0.
- LIVE vptr reads at the click (the falsifier): DIALOG_CUR (0x9939c4) = 0x6a9e9c = the
  chooser sub-object, its vptr = 0x672298 - the chooser class, NOT any of the 5 family
  vtables (+0x4c is the return-0 stub 0x404ed0, so its clicks CANNOT dispatch 0x5f6aa3).
  Family vptr occurrences in writable memory were LIVE the whole window (0x67164c x7,
  0x675cc4 x2, 0x6776c8 x1) - so the zero is not a dead-class artifact; those instances
  live on OTHER paths (message OK/CANCEL dialogs, menu panes).
- RESULTS: site bps fired 0/12, family-slot hits NONE, ENTRY hits 0, pump control 0,
  wndproc LBUTTONDOWN controls 6. STATE 4 measured-negative: clicks delivered + chooser
  functioned, but the family +0x4c is dispatched through NONE of the 12 sites on this
  path - the production chooser is a DIFFERENT (0x672298) class, exactly as M284's
  base-display negative predicted the re-scope would find.
- ACCEPTANCE: static 5/5 PASS; live STATE 4 measured-negative with the live-vptr
  falsifier + INSERT read-back (pending 0->1 item 193) - one real invocation.
- OPEN (unchanged): M282 G5 (which founder vector the recorded AI used - box); the 64x64
  odd-Rw accessor stride quirk.  NARROWED: the family +0x4c dispatcher is NOT on the base
  display (M284) NOR the production-chooser path (M285); candidate dialogs remaining =
  the message OK/CANCEL dialog (FUN_005f1394's own class: 0x67164c x7 live), the menu
  panes (TOPMENU/MAPMENU/SCENARIOMENU), the REALLYQUIT prompt.  Next fire: ANALYSE.

## Session 230 (2026-11-10, BUILD, B11 queue-mechanics leg) 13/13 - the production-queue law replays the game's OWN m69/m70/m71/m72 queue states byte-for-byte; R2's "build" slice now executable
- track_mode printed BUILD -> wrote rung B11 into BUILD_SPINE.md FIRST, then built it.
  sim/queue.py: the M68-M72 queue law. INSERT obeys the widget CURSOR (queue[pos]=item,
  pos = the widget's cursor row; shift runs min(9,max(pending+1,cursor)) DOWN to cursor+1,
  store uses the ORIGINAL cursor, pending++ only when pending<9, enqueue tail parks the
  cursor at rows+1, the 0x4d00 handler zeroes it). Duplicate id REFUSED (M68). Negative
  slot value is the TYPE's (195->-3, 196->-6, stored VERBATIM; mapping rule OPEN). Head
  sentinel = 0xffffffd9 (-39). POP pops ONE item, for k in range(pending): slots[k]=
  slots[k+1], pending-=1 -> queue[pending] KEEPS its stale id (measured [2,193,192,0] ->
  [193,192,192,0] = a duplicate no instruction wrote). Affordability = the visitor's OWN
  cost product at 0x4efa5e, NOT price_of (head 193 wants 27).
- ACCEPTANCE: python3 -m sim.selftest --b11 programs/saves/m54b_clean.SAV -> PASS 13/13
  (evidence/b11_queue_mechanics.txt; sha256 29753b325093c6e1). Replays evidence/m69_cursor.jsonl
  (poked cursor 4, INSERT 0 -> landing [4,0], pending 4->5, stale 193 moved to 5, cursor 6),
  m70_cursor_events.jsonl (rowclick 3 -> cursor 1; insert 193@1 p1 cur2; insert 192@2 p2 cur3;
  0x4d00 -> 0), m71pop_seq/m71pop3_seq ([193,192,192,0] p1), m72gate4 (storage 18 vs edi 27
  BAILS x2, queue untouched) + m72gate5 (storage 27 PAYS, storage 0) - the game's OWN bytes.
- RIVALS fail the same fit: shift-left-by-K gives [193,192,0..] (model [193,192,192]); price_of
  18 pays at storage 18 (game bails). Written queue state (pending 1, head 988) composes into
  record 0 via queue_bytes + savewriter: ONLY dwords 0x4c/0x50..0x77 change, re-parse reads
  pending 1 head 988, tail byte-exact, decode_save --sections still rc 0. `python3 -m sim.queue
  --sav <sav> --out <f>` exit 0. B8 10/10, B9 7/7, B10 18/18 regressions GREEN.
- NEW: the queue's SAVE-RECORD offsets are now written+re-read (pending@0x4c, slots@0x50..0x77)
  but only as compose/read-back; the cursor-vs-pending store-order interaction on the WRITE side
  and the negative-id table stride (-v)*48 vs *16 stay OPEN (M70). The M282 G5 found-event
  SCHEDULING frontier is DECLARED, not modeled: B11 replays recorded queue states, it does not
  predict which turns found/write. Next fire: BUILD (B12 - write the rung into BUILD_SPINE.md
  first: candidates are the cursor-vs-save write law, unit-growth from a completion, or R2's
  end-turn/save slice closure).
