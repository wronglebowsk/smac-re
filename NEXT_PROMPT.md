# NEXT_PROMPT.md — footing for the next session (written at the session-93 close, 2026-10-25)

## THE LEDGER

Closed (merged to `main`): **M54A–M54E** (#39-#44), **M54F–M54i** (#47-#50), **M54i2/M54j/M54k**
(#51-#53) + **M54k2** (#54) — the walking arc. **M55** (#55) — the solo round boundary read end to
end. **M56** — the production gate = MINERAL STORAGE, settled by controlled poke (`m56_build.py`
PASS, `test_m56_predict.py` 8/8, fixture exit 1; `NAMED.md:489` "M56 block").

**M57 IS OPEN AND NOT MERGED.** Session 93 proved the two hard halves and failed one floor:
- **PROVEN**: the GAME's own BUILD UI writes the production queue (pending 0->1->2, head `+0x50`=2,
  slot `+0x54`=2, read back after every click); the run that verified it made **0 memory writes**;
  and the queued Scout Patrol **completed at a boundary where pre-boundary storage was 8 < price
  10**, i.e. it was paid by income, not by an armed storage poke.
- **FAILED**: the exact-round prediction, 1 of 2 verified — `income_first` (storage + `+0xd0`)
  over-predicted the 2154->2155 boundary. **`base+0xd0` is NOT the per-round mineral credit**: the
  measured storage deltas across 2152->2157 were **0, +4, 0, -5, +2**. That is the open question.
  Trace: `evidence/trace_m56_build_20261025_212402.jsonl`.

Spines: **S1** production rebuild, **S2** the solo turn advance (M55/M56 opened it), S3-S5 untouched.
`ROADMAP.md:86` is the S2 row.

## THE PICK — M57-2: FIND THE TRUE MINERAL CREDIT, THEN RE-RUN THE SAME GATE

Do exactly ONE milestone, then stop.

1. **Measure the credit.** With an income base and an EMPTY queue, sample `base+0x40` at 2 ms across
   one boundary (`scripts/m55_boundary.py`'s sampler + `scratch/m56_dump.py`) and print the credit
   sequence for 3-4 boundaries. Expect it to be irregular (measured 0/+4/0/-5/+2 with a queue).
2. **Name the writer.** The credit lands somewhere in the base visit; candidates are the income add
   near `0x4ef7f6` and the recompute `FUN_004e9557`. A gdb watchpoint on `base+0x40` during one
   boundary names the store and its caller (`scripts/m53g_drive.py` is the attach harness pattern).
3. **Re-run the gate UNCHANGED**: `python3 scripts/m56_build.py --ui-queued 18 --boundaries 5
   --timeout 120`. Every floor stays: 5/5 boundaries, walk home, 1/1 positive predictions,
   provenance (0 writes), "storage below price at run start", bookkeeping exact.

**Do NOT relax a floor to fit the observed flow.** If the credit is irregular in a way the base
fields cannot predict, the milestone's honest outcome is a documented negative with the credit
sequence and the store address — not a looser prediction.

## WHAT SESSION 93 ESTABLISHED — do not re-learn these

1. **Opening the base display (needed for any queue edit).** Poke the map cursor to the base tile
   (window fields `*(0x7cdecc)+0x1dd9c/+0x1dda0` AND the handler cell `0x91b5f0/0x91b670` at
   `0x91b5e8`), set `SEL_G` (`0x91b5bc`) = -1, set orders mode (`0x91b5b8`) = 0, then `b`. Verified:
   `kind base`, pane base index (`0x6a9480+0x3ff3c`) = the base index. **With orders mode ON, `b`
   raises the Operations Director OBLITERATE prompt instead** — its "No, let them live" is the
   default, Return spares the base (verified twice, both bases still ours).
2. **The UI enqueue, exact and measured** (800x600, window "Sid Meier"):
   right arrow beside the base name **(523,433)** switches the QUEUE widget's base;
   queue row 1 **(185,437)** opens the item chooser (instant test: pixel (160,343) == (103,91,181));
   candidate array `DAT_009267e4`, count `0x9267e0`, display is a 5-col grid, cell k -> x = 128 +
   127*(k%5), y = 60 + 100*(k//5); Scout Patrol (id 2) is cell 3 -> **(509,60)**; the selection
   field is `[pane+0xa1c+0xa774]` (reads the CELL INDEX, not the item id); **INSERT (497,343)**
   writes head +0x50 / pending +0x4c / slot +0x54; **OK (285,343)** = mode 0, commits, no restore;
   CANCEL restores from the snapshot. **Re-read `pending` ~1 s after INSERT** — an immediate read can
   show the old value while the write has landed.
3. **`orders_mode` at 0 silently disables every order key** (`h`, `g`, `l` all fall through to the
   cursor-tile handler). The `h`-escalation in `m56_build.py` depends on it being ON; restore it
   before a run.
4. **Escape on the map raises the quit prompt — and after that prompt is dismissed the game stops
   accepting KEYS altogether** (mouse clicks still work; the map renders black; `cur_player`/`year`/
   `turn_flags` frozen). 150 s of Return/h did nothing. **Reload is the only recovery.** Use Escape
   ONLY while a pane that Escape closes is actually up (base screen, hint popup).
5. **Popup bars do not take clicks** (obliterate OK, hint Close / "Don't Show Again") — Return on the
   default row and Escape do. The MENU button click DOES work (75,369).
6. **`/tmp` quota**: when it fills, `P.freeze()` returns a path that does not exist and `classify`
   then says `movie`. `df /tmp` before trusting a frame; `rm -f /tmp/*.xwd /tmp/*.png` frees it.
7. **Korolev Center after reload+refound earns minerals** (measured 4 -> 6 with no input) — the old
   box's zero-income bases were the reason nothing could ever be paid for. `m54b_clean.SAV` +
   `m54g_prep.py` + a 2-turn founding recreates it at (29,42), base index **18**.

## OPERATIONAL KIT

- Production gate: `python3 scripts/m56_build.py [--arm N | --ui-queued N] [--boundaries N]
  [--timeout S] [--fixture FILE]`. `--ui-queued` makes NO memory write and floors provenance +
  "storage below price at run start".
- Rule cases: `python3 scripts/test_m56_predict.py` -> **PASS 11/11** (cases 9-11 pin `income_first`).
- Boundary sampler: `python3 scripts/m55_boundary.py [--timeout 300] [--no-poke] [--fixture F]`.
- State: `scripts/smac_state.py --json`, `scripts/m54d_census.py`, `scratch/m56_dump.py` (queue +
  income + facility bitmap per base), `scratch/m54i2_cursor.py read` (both cursor homes).
- Reload: `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` (BARE filename) ->
  HUD at 2150; then `python3 scripts/m54g_prep.py`; then
  `python3 scripts/smac_play.py --turns 2 --timeout 200 --no-escape 3000 --orders-per-turn 1
  --verbose --tag <t>` -> `FOUND rec0 (29,42) ... bases 1->2`.
- Tests to keep green: `test_m56_predict.py` 11/11, `test_walk_diff.py` 37/37, `test_classify.py`
  17/17, `check_classes.py` 17/0 (delete `evidence/**/_3x.png` after).
- `python3 scripts/evidence.py budget` BEFORE adding frames (gate FAILs at 30 MB; ~24.5 MB used).

## TRAPS

- A modal pane is invisible to memory reads and eats keys; clicks on its bars often do nothing.
- `+0xd0` is a DISPLAY/net figure, not the credit — session 93's whole failure. Do not reuse it.
- Record indices lie across a boundary; identity is (x, y, type, owner, order).
- A produced unit arrives order 0 and FREEZES the auto-end; ONE `h` on the cursor unit closes the
  turn — but only with orders mode ON and a live `SEL`.
- A disband is not a non-production: verify the arrival AT the boundary.
- One variable at a time. If a position AND a tile changed, write "confounded".

## CLOSING ORDER (exactly)

1. `## Session <N>` entry in `SESSION_NOTES.md` — what changed, the acceptance numbers WITH the
   command that produced them, what is still open, the next pick.
2. Rewrite this file, then `wc -c NEXT_PROMPT.md` (<= 15,500).
3. `rsync -a ~/.hermes/skills/smac-cvr-format/ ~/reverse/smac/skill/`
4. `git add -A && git commit -m '<ID>: checkpoint'`
5. `python3 scripts/gate.py --base main` — must be GREEN.
6. `python3 scripts/milestone.py submit --title "..."` -> `gh pr checks <n>` ->
   `python3 scripts/milestone.py merge <n>`. Merge ONLY on a PASS; otherwise say so and merge nothing.

## Never

commit to `main`; Escape on the map (quit prompt, then a key-dead game); click OK on "Do you really
want to quit?"; `pkill -f`/`pgrep|kill` by name; `--mode stop`; `file://` with `--load`; a
`clear`-prefixed command; backticks in a commit message; `skill_manage delete`; `nohup`/`&` in a
tracked terminal call (use background=true); a `MEDIA:` line unless a file is attached.

## Report style

One screen: what changed, the acceptance numbers WITH the command, what is open, the next pick.
No narration of the journey.
