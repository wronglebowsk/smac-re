# Session notes archive — sessions 59-59

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 59 (2026-10-24) — M53g: **`[chooser_sub+0xa774]` IS THE SELECTION CELL INDEX — AND REPLACE FIRES LIVE AT (365,343) VIA BAR PARAM 7 (UNGATED)**; the drawn REPLACE bar body (x 381-421) is phantom grid cell 17, whose clicks take the setter path and never reach the bar handler
- **Guard semantics (VERIFIED live, `m53g_watch.log:68-74,101-107`):** chooser open → paint clears
  guard to −1 (pc 0x495541) then sets it to the enumeration index of the item in the selected queue
  slot (0x495b00; slot 1 held Scout Patrol → guard 5); icon click → setter 0x4962ec := cell index
  (Colony Pod → 6); bar-row click → phantom cell (x 397 → 17); CANCEL → −1 (0x496a43). Cell index =
  position in a 5-col grid (rows y~60/160/260 = cells 0-14; bar row overlaps cells 15-19; col3 = 17).
- **Complete writer set (VERIFIED, whole-`.text` census, 43 refs / 13 stores, `evidence/m53g_a774_all_refs.txt`):**
  paint clear 0x495541 + match stores 0x495b00/0x495e6f (`FUN_004954e0`); setter 0x4962ec
  (`FUN_004962a0` = **vtable+0x48** of the chooser class, vptr 0x672298 live); mutator `FUN_004963b0`
  (vtable+0x60, 8 stores, sort/swap with +0xa818, never fired live); CANCEL clear 0x496a43
  (`FUN_00496950`). No other writer exists.
- **Bar handler `FUN_00496950` = vtable+0xa8** (only pointer: 0x672340 = vptr+0xa8). Jump table
  0x496a9a indexes `param+2`; cases 0=HELP(gate)1 2=gate,mode7 5=INSERT(gate) 7=mode7 **ungated**
  −1=OK 0, −2=CANCEL 0+guard−1; gate = `cmp [this+0xa774],-1; je 0x496a91`. **0x496a91 is the shared
  epilogue return** — mode-storing paths reach it too (corrects M53e's BAR_IGNORED-as-refusal reading);
  **one handler run per click** (corrects "runs twice").
- **REPLACE live:** click (365,343) → BARH param=7 guard=12 → MODEWP pc=0x496a5c mode=7 → POST_PICK
  edi=−26 → dispatcher mode-7 handler → **D20_STORE +0x54 2→−26** (W54 pc=0x417e08, `log:104-112`);
  repeat at (345,343) hit +0x58. CANCEL → RESTORE ×10 → queue exactly restored (f4c=2 f54=2 f58=2).
  Session 56's lone mode-7 hit = same rect (INFERRED).
- **Rect map (param ← click, VERIFIED):** HELP 0←160 · OK −1←285 · **REPLACE 7←345/365 (NOT 397)** ·
  INSERT 5←425/440/497 · DELETE 4←602 · CANCEL −2←692. Dead zone x~381-421 = phantom cell 17 →
  setter(17), handler never called — M53e's five REPLACE clicks at 397 all died there. Params 1/2/3/6
  mouse-unreachable from this widget (case-2 gate never exercised by mouse; guard is irrelevant to
  REPLACE). M53e's guard-reads-5/17 mystery = cell indices, not a selection mismatch.
- **Harness:** `scripts/m53g_drive.py` (BARH/GATE0/2/5 probes + SELWP on pane+0xb190; 4 hw watchpoints
  total; stop via `--mode stop --tag m53g`). CANCEL-restore makes armed REPLACE probes non-destructive.
- **Open:** exact param-7/5 button rects + why REPLACE's rect sits left of its drawn bar; enumeration
  contents (guard 12 → item −26 vs M53a `|q|=39+idx`); vtable+0x60 mutator path; vtable+8 `FUN_00494c40`
  (runs after OK/CANCEL when slot≠0); producers of modes 2/3/6.
- **Next:** `NEXT_PROMPT.md` rewritten for session 60; **THE PICK = M53h** (chooser enumeration +
  button-table: what fills cells 0-19, the −26/secret-project encoding, and the Script.txt/button-table
  record that places REPLACE's rect left of its bar).
