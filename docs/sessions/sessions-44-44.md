# Session notes archive — sessions 44-44

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 44 (2026-10-22) — M47: WRITE PROVENANCE — the exact stores that move faction energy; `base+0x7e` retracted as a Ghidra short*-artifact (the addend is `base+0xfc`); ledger writers are action-time; six input-blocking panes that `classify()` calls `hud`

- **Positive control first (H):** `hw watch` on the mission year fired once, `eip=0x51f554
  val=2335` in `FUN_0051f320` when the round rolled 2334→2335 (`evidence/m47_year_watch.log`).
  Hardware watchpoints DO work under this Wine build; earlier sessions only ever armed them.
- **Income (H):** watching our energy `0x953884` through a round caught
  `eip=0x4f5c92 val=21 ecx=0x962f90(=our base) esi=0x6234 edi=3`; disassembly at the site is
  `4f5c7f mov 0xfc(%ecx),%edx · 4f5c85 add %edx,%eax · 4f5c8c mov %eax,0x94d650(%esi)`
  ⇒ **faction energy += `base+0xfc`**, inside `FUN_004f5a70`. Our 19→21→20→19 reproduced
  exactly (two upkeep debits of 1 for runtime items 6 and 7).
- **Retraction (H):** `base+0x7e` is never written — zero hits on `base+0x7c..0x7f` over two
  armed rounds, and it reads 0 always. Ghidra prints `*(int *)(DAT_008f0d60 + 0x7e)` but
  `DAT_008f0d60` is a **short\***, so `+0x7e` = `0xfc` **bytes**. M46's "transient income field
  with no visible writer" was decompiler pointer maths, not a missing writer.
- **Upkeep (H):** `eip=0x4f4958` in `FUN_004f47f0`: `mov 0x94d650(%edi),%ecx · sub %eax,%ecx ·
  mov %ecx,0x94d650(%edi)` then `faction+0xe0 += cost` at `0x4f4962`; `esi` = runtime item id
  (6 = Recreation Commons, 7 = Energy Bank); item 8 (Network Node) never fires — disabled list.
- **Ledger (M, open):** `faction+4` got **zero** writes for us *and* for Morgan across a full
  idle round ⇒ the ledger is written by player ACTIONS (research/gifts/terraform), not upkeep.
- **AI round (H, `evidence/m47f_watch.log`, 28 hits):** Morgan p4 2335→2336 — income at
  `0x4f5c92` per base; upkeep at `0x4f4958` per item (2,6,7,8,0x18,0x1b; cost 1-2); a **direct
  per-base debit of −7 twice at `eip=0x4f2dc4`** in `FUN_004f26e0` (the production/rush step that
  reads `energy/10` and `energy/50`); and a final whole-faction write at `0x506d2b` (=905).
  ⇒ M46's "AI gaps = ledger debits" is NOT supported for idle rounds.
- **Operational (H, cost the session):** six panes block input while `classify()` says `hud`
  because the HUD is visible behind them — advisor advisory ("PLANETARY ECOLOGIST / Mindworm
  boil spotted") → `Return`; advisor story page ("Book of Planet", long body) → click (400,470);
  council convenes page → `Return`; council ballot → click the **ABSTAIN** word centre; result
  page ("MEASURE FAILS") → `Return`; faction-info table (Tech:/Mil:/Pop:/Wealth:/Territory:/
  Overall:) → click (400,580). Rule of thumb: `hud` + TURN COMPLETE visible but the year will not
  move after a click ⇒ `Return` once, then click the pane's bottom-centre.
- **Harness:** `scripts/m47_watch{,2,3,4,year}.gdb` + `scripts/m47_drive.py` (end-turn driver with
  the pane rules). All read-only: TracerPid 0 before pokes, watches armed after, `kill -INT gdb`
  then `kill -CONT` every time.
- **Open:** ledger writers (needs a round in which we research/gift/terraform); what `faction+
  0x1b8` is; the 2320 +4 credit; mineral economy isolation; name of the `0x506d2b` host function
  (Ghidra lumps it into `FUN_00502cd0`, 18 KB — address is solid, name is not).
