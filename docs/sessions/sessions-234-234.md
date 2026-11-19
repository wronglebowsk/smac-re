# Session notes archive — sessions 234-234

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-231-233.md` (inserted at s292: the hot file cites only the newest archive, so without this line the older archives were orphans).

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
