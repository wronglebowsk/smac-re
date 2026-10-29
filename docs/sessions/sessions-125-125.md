# Session notes archive — sessions 125-125

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 125 (2026-10-28) — M82: BITS 6/7 OF THE TYPE-RECORD FLAG WORD HAVE NO TESTER; THE LIVE POKE TEST DID NOT RUN (acceptance FAIL, nothing merged)

CONCURRENT SESSION: session 126 ran the same prompt in the SAME worktree while I was running
(`evidence/m82census_s126.txt` 11:49, commit 989db9b "acceptance m82bit7b in flight" 11:53).
The box is ONE Wine process, so the third window (m82bit7c, armed 11:56) ran with another agent
able to attach/poke it.

STATIC (bytes; `grep -n 98adb8 scratch/m574/text.txt` = 168 sites, `python3 scratch/m71/dis.py
577c60 577cc0`): every `test BYTE PTR [...0x98adb8],imm` uses 0x1/0x4/0x8/0x10 — NO test of bit 6
(0x40) or bit 7 (0x80) in the absolute form, and no pointer-form `test BYTE PTR [reg+0x30/0x31],
0x40/0x80` either (both shapes grepped). The only bit-7-specific instruction is the CLEARER
`and BYTE PTR [eax*4+0x98adb8],0x7f` at 0x577ca8 (followed by `call 0x43f470` with ecx 0x71df20).
The markup test is bit 2 ONLY (`test BYTE PTR [ecx+0x98adb8],0x4`, 0x5ac99c) and B comes only from
0x5ac950, so the gate's `edi` cannot depend on bits 6/7. M74's live row (f30=0x41 — bit 6 SET —
with edi 45 = markup ON, evidence/m74flag2.gdblog) already falsifies "bit 6 = markup off".

CENSUS (`python3 scripts/m82_bit7_poke.py` PART 1, 512 slots read at once, 11:47): nonempty 34;
band0 0-13 = 0x1; 64 = 5; 128-131 = 5; 192 = 1, 193/194 = 0x41; 256 = 5; 320-323 = 5, 324/325 =
0xc1; 384/385 = 1, 386 = 0xc1; 448 = 5, 449 = 0x1c5. bit6 carriers [193,194,324,325,386,449],
bit7 [324,325,386,449], bit2 [64,128-131,256,320-323,448,449]. THE CENSUS MOVES: the 12:06 re-read
reads 385 = 0x81, 386 = 0x1, a NEW 387 = 0xc1, bit6 [193,194,324,325,387,449], bit7
[324,325,385,387,449], 194 = 0x45 — the sweep re-inits and re-marks faction records between
rounds, so a carrier list is a snapshot, not a property of the record.

ACCEPTANCE m82bit7a/b/c FAIL (`python3 scripts/m82_bit7_poke.py --tag m82bit7X`, 3 boundaries, 4
base-conditioned silent bps 0x4efa4b/0x4efa52/0x4efa5e/0x4efa63). a: died at 200 s inside the
m70_clear_dialog step — a concurrent veilbrowser Chrome window (pid 4179644 "PeopleSearchNow Opt
Out", 1280x800) was stacked OVER the Wine window at 0,0, so `xwd -root` cropped to 800x600:0:0
OCR'd the BROWSER and every screen read hung (session_brief and m65_screen also printed nothing in
60 s); fixed with `DISPLAY=:99 xdotool windowraise 0x400004`. b: armed and printed `ARMED
base=0x95da10 head=2 pending=1 storage=20` then `GATE id=2 storage=20 edi=9 f30=0x1` — the UI
chooser (`m57_ui_enqueue --cell-item 194`) landed cell 2 again, so the gate never visited 194; cut
at the 420 s foreground cap. c: head set by a controlled poke (+0x50 = 194, +0x4c = 1, read back
head 194 pending 1), flag 194 0x45 -> 0x41, storage 20, `ARMED ... head=194 pending=1 storage=20`,
then ZERO GATE/BAIL rows in 10 min (trace_m82bit7c_r0 is 0 bytes — the first smac_play never wrote
a look; a NETFLASH dialog stack was up at arm time).

OPEN / NEXT (M83): the same three-window test on a QUIET box — no concurrent session, Wine window
raised, dialogs cleared, queue head poked — W1 (bit2 off, bit7 off) -> edi, poke ONLY bit 7 -> W2,
W3 bit2 ON as the control that the instrument can see a markup switch; the bytes predict edi
unchanged. Still open: why `[ebp-0xc]` != 0 for 324/325 and == 0 for 385; who calls FUN_00573a90;
what re-inits 385/386/387 between rounds.
Evidence: evidence/m82bit7b.gdblog, evidence/m82bit7c.gdblog, evidence/m82census_s126.txt (s126's
copy of the same census), traces trace_m82bit7b_r0..r2, trace_m82bit7c_r0.
