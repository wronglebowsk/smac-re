# Session notes archive — sessions 76-77

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 76 (2026-10-24) — M53t: **THE FOLD IS IMPLEMENTED AND 10 OF THE 11 RESIDUALS CLOSE EXACTLY (74/76)** — `evidence/m53t_fold.md`, `scripts/m53p_recon_a.py` (`alliance_fold`, `census`, `--mem-dir`)
- **What the share actually is (VERIFIED, full decode 0x4eab02-0x4eac8a):** per allied OTHER
  faction, `n = (E[ally k-th] + E[me] + 7) >> 3` on `base+0xb4`, `s = ((faction[owner].+0 + 1)*n
  + D/2) / D` with `D = [0x92a274]+1`, halved unless `stance[owner][other]` bit 1, `+1` when
  `[0x985bc0] == owner`, then zeroed if `[0x94d4f0 + fac*0x20bc]` is set for owner or other.
  Gate A is the stance bit 2 **in both directions** (the second read is the transpose at
  `0x94f504 + owner*4`, advanced `+0x20bc`). Published to `DAT_008f0d40[other-1]` *before* the
  zero-gate, so the published copy keeps the ungated value.
- **`FUN_004ea940` is not "k-th nearest" — it is k-th by ENERGY** (key `E<<9 | idx`, bubble sort
  desc, `-1` when `k >= count`); no distance is computed in it. Rank `k` = number of the owner's
  bases above `(E_me<<9 | [0x68cbb0])`, and `0x68cbb0` is set to the base's OWN index at
  `0x4f5a7c` — using the dump's global (the last base visited, 69) mis-ranks ties and was the one
  real bug in the first implementation (idx 1 came out +1 too high).
- **Acceptance (pre-drive dump `evidence/m53s_dump1`, pid 2124624):** before 76 sc / 65 exact /
  11 c4-only; after **76 sc / 74 exact**, residuals `{6: +2, 51: -1}` —
  `evidence/m53t_run_before.txt:1-12`, `evidence/m53t_run_after.txt:1-3`, per-row ally detail
  `evidence/m53t_probe.txt:1-24`. Closed: idx 1, 3, 5, 8, 30, 34, 46, 60, 62, 69.
- **The two stragglers are NOT formula errors (INFERRED):** idx 6 and idx 30 have identical
  (fac, energy, rank) yet +0 vs +2 observed (`probe:7-8` vs `:11-12`), and idx 51 wants one more
  than the formula gives. Prime suspect: `FUN_004f5a70` runs the whole
  `4e8d60/4e78e0/4e92c0/4e93f0/4eaa10` sequence **twice** — second pass gated on `[0x985afc] > 1`
  (284 here) with `[0x8f0d64] = 1` (`0x4f5b14-0x4f5b2c`), and `4eaa10` reads d64 at `0x4eac95`.
  `+0xb4` is byte-identical across the two dumps while `+0xc4` moves, so pass 2 sees a different
  record. Do NOT close this by fitting constants.
- **Kit:** `--census` (all 76 rows, exactness before/after the fold), `--no-fold`, `--mem-dir`
  (the post-drive `evidence/m53o_mem` has only 31 self-consistent rows — never use it for the
  exactness claim), and `show()` now prints the fold line.
- **Next:** the M53 thread is CLOSED as a model; the two rows above are a background probe
  (watchpoint at 0x4eac57 + a pass counter at 0x4f5b2c over one driven turn), not a queue. Next
  session is the harness/G1 switch — see `NEXT_PROMPT.md`.

## Session 77 (2026-10-24) — M54a: **THE HUD NO LONGER TRICKS THE CLASSIFIER, THE DRIVER ANSWERS THE PANES — THE 40-TURN RUN IS STILL OPEN (→ M54b)**
- **The bug, fixed and pinned.** `classify()` returned `base` for ANY frame whose OCR text held a
  BASE_WORD, and the HUD's own message pane prints news lines that do: `nutrients` at (355,438)
  with TURN COMPLETE at (628,419) on `evidence/m54a/live_hud.png` (the session-75 stall position,
  captured first this session). The test is positional now — `base_word_positions` +
  `in_msgpane`, `MSGPANE = (0,425,800,600)`: base words count only outside that strip, or while
  the HUD button row is absent (a real base screen has no TURN COMPLETE row: `m45a_post.png`,
  words at y 16-45 + (279,273), `btn=None`). Acceptance numbers, no game needed:
  `python3 scripts/test_classify.py` → **PASS 10/10 screen classifications**; the same frames
  through the older suite `python3 scripts/check_classes.py` → **frames: 10 failures: 0**.
  `scripts/m54a_ocrscan.py` re-OCRs every evidence PNG into `evidence/m54a/ocrscan.json:1`
  (base-word coords, button centre, flatness, the OLD classify label) — that is where the
  "was `base` / was `title`" claims come from.
- **Three screen classes the driver had wrong.** (1) `quit-prompt`: the "Do you really want to
  quit?" dialog wears the game title as its banner, so `title` fired on it and a 40-turn run
  STOPPED at turn 13 refusing to answer it (`evidence/m54a/quit_prompt.png`; m37_screen0.png and
  m15_title_now.png are the same dialog, not title screens). Escape = "Oops, no, wait!" is the
  safe answer; OK exits. (2) `help`: the HELP browser (FACTION PROFILES/CONCEPTS) contains base
  words, ignores Escape entirely, and closes only on its EXIT bar (BACK (275,344), EXIT (525,344)
  on `evidence/m54a/live_now2.png`). (3) the battle **Replay** screen ("Replay: 2415" + a Close bar
  at (400,587), `evidence/m54a/movie_stuck.png`) OCRs to 5 words → `movie` → the driver waited;
  now a `movie`/`unknown` frame with a bar at y ≥ 560 gets clicked.
- **Bar geometry: a horizontal RUN does not work on this build.** The push-bars are DITHERED —
  fill (103,91,181) on every OTHER scanline, (28,80,99) between (measured band y 489-507 on the
  PROPOSAL vote, `evidence/m54a/stuck2.png`) — and their labels are drawn INSIDE them, so
  session 75's `run > 55 px` test finds ZERO bars exactly where the vote is. `pane_bars` is now
  band + column density: rows bar-filled over 100 px, grouped across 1-row dither gaps, then
  per-column fill inside the band; 30% duty splits YEA/NAY/ABSTAIN at centres 311/400/489 = the
  YEA(310,495) NAY(398,495) ABSTAIN(485,495) row hand-measured in session 75. 40% duty cuts a
  labelled bar in half; 15% merges the row and you click NAY.
- **The driver now answers the round's modals itself** (`handle_pane`, ahead of the generic
  dialog/Escape paths in `service_turn`, both phases): Council PROPOSAL vote → click YEA
  (`vote-yea@311,498/council`, 6 hits live); Council "Have you any further business?" → top option
  row then the MERGED OK bar (the label splits it into (266,347)+(534,347); click the centre
  (400,347)) — 4 hits, the turn advanced right after; HIVE bribe → Escape then Return (11 hits);
  quit dialog → Escape (2); help browser → EXIT (1); replay → Close (89). Live totals across the
  9 runs: **45 turn-records, 29 turns advanced with the year +1 on each, 16 stalls**, position
  2385 → 2416, n_bases 75 → 79. `Return` is still the right answer for advisory panes — the
  PSYCH CHAPLAIN "Our citizens are starving" alert has a highlighted `Zoom to Base Control` row
  that `pane_bars` reports at (310,221) and clicking it does NOT clear it
  (`evidence/m54a/stuck_pane.png`; turn 0 STUCK 277.8 s on two identical clicks).
- **THE 40-TURN ACCEPTANCE IS NOT MET — that is M54b.** Best single invocation: 12 turn-records /
  12 advanced / 1 stall, max dt 164 s (`evidence/trace_m54a40c_20261024_174316.jsonl:14`); the
  longest run after the pane fixes: 12 records / 10 advanced (`evidence/m54a/run40h.log:1`).
  Runs die on 2 consecutive stalls, and the stalls were: OCR starvation when another job shared
  the box (one turn burned 355 s on ~1 OCR pass per iteration), the help browser, the replay, and
  finally the game falling back to the TITLE screen mid-round (the driver clicked into the LOAD
  file browser and clicked its OK bar 20×). No STUCK ever exceeded 2× the per-turn timeout.
- **State of the box:** pid 2124624 is alive but at the title menu (I clicked CANCEL on the LOAD
  browser — `evidence/m54a/after_cancel.png` reads `start game / scenario / load game / …`). The
  position is NOT lost: the game autosaves into `programs/saves/auto/` (newest 19:05) and
  `programs/Alpha Centauri Autosave 1.SAV` (19:08). Next session: load the autosave (the
  `scripts/m48d_boot.py` load path) before driving anything.
- **Next:** **M54b** — the 40-turn unattended assertion: a boot/load wizard step for the driver,
  a per-turn budget that survives a long Council/replay round (the 2-stall abort is too eager),
  and never clicking a bar outside the pane we own.
