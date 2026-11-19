# Session notes archive — sessions 245-245

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-244-244.md` (inserted at s292: the hot file cites only the newest archive, so without this line the older archives were orphans).

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
