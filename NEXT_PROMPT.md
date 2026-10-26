# NEXT_PROMPT.md — footing for the next session (written at the session-94 close, 2026-10-25)

## THE LEDGER

Closed (merged to `main`): **M54A–M54E** (#39-#44), **M54F–M54i** (#47-#50), **M54i2/M54j/M54k**
(#51-#53) + **M54k2** (#54) — the walking arc. **M55** (#55) — the solo round boundary read end to
end. **M56** (#56) — the production gate = MINERAL STORAGE (`m56_build.py` PASS,
`test_m56_predict.py` 8/8 then 11/11; `NAMED.md` "M56 block").

**M57 IS OPEN AND UNMERGED (branch `milestone/m57`, no PR).** Session 93 proved the GAME's own BUILD
UI writes the queue (0 memory writes) and that a queued unit completes paid by income. Session 94
(M57-2) found the credit and re-ran the gate UNCHANGED: `m56_build.py --ui-queued 17 --boundaries 8
--timeout 240` -> **exit 1** (`evidence/trace_m56_build_20261025_215056.jsonl`): 8/8 boundaries
flipped, provenance + storage-below-price floors ok, but **0/0 positive predictions verified** (the
model read income 1/round; the visit completed at minerals 7 + a fresh recompute), + `r4 bookkeeping
base 17 BAD` (pending 1->0 unpredicted), + `r6/r7 walk-home BAD` (after-snapshot at settle 0.3 s
caught cur_player mid-walk — sampling artifact). Per the rule, nothing merged.

**THE CREDIT (session 94's answer, all read from memory).** Storage is NOT `+= d0` once per round.
Inside ONE base visit at the flip there are SEVERAL stores — measured boundary sequence
`store 7->9, store 9->0 (pay, edi=9), pending 1->0 (pop)` — and `+0xd0` is RECOMPUTED every visit
(measured walk 1->3->0->1->2->3->4 as produced units arrived and were DISBANDED: upkeep tracks the
garrison). The income add IS gated `d0>0 && head!=-38 && !(flag30&2)` (0x4ef7db-0x4ef7f9) and fires
**with pending 0 while the head slot is stale** (the pop leaves stale ids in the tail). Clamp B
(0x4eff20) stores only when storage > min(`*0x92a370`=10, d0). The pay deducts `$edi` = the PRICE
(m52a live: `SPENDA old=200 new=190 edi=10` at price 10 — supersedes NAMED's "edi = sweep-entry
index" row). The MIDDLE movement (9 after the add, before the pay) is UNNAMED — that is Open (1).

Spines: **S1** production rebuild, **S2** the solo turn advance, S3-S5 untouched. `ROADMAP.md:86`
is the S2 row.

## THE PICK — M57-3: AN INCOME-STABLE BASE, THEN THE SAME GATE

Do exactly ONE milestone, then stop.

1. **Reload + re-found** (the box is dying: 2176, Korolev income 0, minerals 0):
   `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` (BARE filename) -> HUD at
   2150; `python3 scripts/m54g_prep.py`; `python3 scripts/smac_play.py --turns 2 --timeout 200
   --no-escape 3000 --orders-per-turn 1 --verbose --tag <t>` -> `FOUND rec0 (29,42) ... bases 1->2`.
   That box had Korolev income 2 (session 93). **Locate Korolev by NAME every step — the base array
   compacts (its index walked 17->18->17 inside one session).**
2. **UI-enqueue ONE Scout Patrol** at minerals < 10: `python3 scripts/m57_ui_enqueue.py
   --base-index <idx> --cell-item 2 --inserts 1` (read-back after every click; it cycles the queue
   widget and locates the chooser cell BY CONTENT).
3. **Run the gate**: `python3 scripts/m56_build.py --ui-queued <idx> --boundaries <6-10> --timeout
   240 --settle 2.5`. `--settle 2.5` only moves WHEN the after-snapshot is taken (so the walk-home
   floor sees the walk finished) — it changes no floor semantics. Every floor stays: boundaries
   flipped +1, walk home, >= 1 POSITIVE prediction verified, provenance (0 writes), "storage below
   price at run start", bookkeeping exact, no unexplained order-0 arrival on our bases.

**Do NOT relax a floor to fit the observed flow.** If a stable income still cannot predict the exact
round because of the unnamed middle store, the honest outcome is the documented negative (it is
already written in SESSION_NOTES session 94) and the next step is Open (1): enumerate EVERY write to
`base+0x40` inside one visit with breakpoints at all disasm write sites (`m57_credit.py` is the
harness; do NOT use a hw watchpoint — see traps).

## WHAT SESSION 94 ESTABLISHED — do not re-learn these

1. **The credit is event-dependent, not a constant** (above). A per-round prediction is exact only
   while `+0xd0` is stable; produced-unit arrivals + support disbands move it mid-round.
2. **The gdb harness works, its register prints mostly DO NOT.** Conditional breakpoints
   (`if $eax == <base addr>`) filter the visit correctly and the baked-base field reads match the
   sampler exactly; but `$ecx`-as-d0, `$edi`-as-price at the sites and the clamp pair printed values
   inconsistent with the fields, and the GATE at `0x4f0a3d` NEVER fired for Korolev (it sits on the
   `*0x8f0d60`-current-base branch via the 0x4ef985 AND-test, not the per-base path). Evidence = the
   sampler + field read-backs, never the register side-values.
3. **The hw watchpoint on `+0x40` is unusable for cadence** — the field is read constantly, the
   inferior crawls (~1 round/45 s, year never moved). Breakpoints at write sites instead.
4. **The BUILD UI queue widget's base is INDEPENDENT of the display's base** (both orders observed).
   Right arrow (523,433) moves the field `0x6a9480+0x3ff3c`; INSERT (497,343) lands on whichever
   base the widget holds. Recipe: `b` (cursor poked to the base tile at BOTH homes, SEL=-1, orders
   mode=0), cycle the arrow until `+0x3ff3c` == target, row 1 (185,437), cell click
   (x=128+127*(k%5), y=60+100*(k//5)), INSERT, OK (285,343); read pending ~1 s after each click.
   The chooser guard `[0x6a9e9c+0xa774]` reads the CELL INDEX. **Scout Patrol (id 2) is cell 4 NOW**
   (candidate array `DAT_009267e4` = [192,195,194,193,2,...], count 67) — era-dependent, locate by
   content. `m57_ui_enqueue.py` does all of this with read-backs.
5. **The enqueue dispatch `0x417ee0` fires with `*0x8f0d60` = the target base** (proved live,
   curbase=0x95ef70 = Korolev), but m53g_drive's static store addresses (`0x418b57/0x418ad3/
   0x418ac7/0x418b24`) did NOT hit on the INSERT write — re-derive before trusting them.
6. **A produced unit arrives order 0 and FREEZES the auto-end** (m56_build escalates Return -> `h`
   every 4 s past 8 s parked on our turn -> OK click at (630,247) past 15 s; `m57_credit.py` copied
   it). `h` needs orders mode ON. The support popup ("minerals output ... not sufficient to support
   Scout Patrol") means produced units DIE to upkeep when the base's net income can't carry them.
7. **Rounds at this stage run ~20 s** (gdb attached or not); a 5-boundary acceptance run is ~2 min.
   Set terminal timeouts generously; the script's own `--timeout` is per-run.
8. **From session 93 (still true):** opening the base display needs BOTH cursor homes poked to the
   base tile (`*(0x7cdecc)+0x1dd9c/+0x1dda0` and `0x91b5f0/0x91b670` at index `0x91b5e8`), `SEL_G
   0x91b5bc` = -1, orders mode `0x91b5b8` = 0, then `b`; Escape on the map = quit prompt then a
   key-dead game (reload only); popup bars ignore clicks (Return/Escape work; MENU click (75,369)
   works); `/tmp` quota makes `freeze()` lie; `m54b_clean.SAV` + `m54g_prep.py` + a 2-turn founding
   recreates Korolev Center at (29,42) with income.

## OPERATIONAL KIT

- **PREFLIGHT — run this FIRST, every session:** `python3 scripts/smac_preflight.py` (read-only;
  exit 1 on any FAIL). It checks the one authoritative address table, proves terran.exe is alive
  with TracerPid=0 and no leftover gdb, lists OUR bases BY NAME with index/coords/pending/head/
  minerals/income, decodes our unit records, and checks /tmp room + the evidence budget. `SMAC_PID`
  overrides the pgrep. If it FAILs, do not build on the state.
- Production gate: `python3 scripts/m56_build.py [--arm N | --ui-queued N] [--boundaries N]
  [--timeout S] [--settle S] [--fixture FILE]`. `--ui-queued` makes NO memory write and floors
  provenance + "storage below price at run start".
- Rule cases: `python3 scripts/test_m56_predict.py` -> **PASS 11/11** (cases 9-11 pin `income_first`).
  Fixture: `m56_build.py --fixture scratch/m56_fixture_bad.json` -> exit 1.
- Credit harness: `python3 scripts/m57_credit.py [--mode queue|empty] [--boundaries N] [--timeout S]
  [--tag T] [--wp]` (gdb write-site breakpoints conditioned on the base + sampler + Return/h/OK
  escalation; `--stop` detaches a leftover gdb). UI enqueue: `scripts/m57_ui_enqueue.py`. Enqueue
  dispatch watcher: `scripts/m57_uiwatch.py --hold S` then `--stop`.
- State: `scripts/smac_state.py --json`, `scripts/m54d_census.py`, `scratch/m56_dump.py` (queue +
  income + facility bitmap per base), `scratch/m54i2_cursor.py read` (both cursor homes).
- Reload: `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` (BARE filename) ->
  HUD at 2150; then `python3 scripts/m54g_prep.py`; then
  `python3 scripts/smac_play.py --turns 2 --timeout 200 --no-escape 3000 --orders-per-turn 1
  --verbose --tag <t>` -> `FOUND rec0 (29,42) ... bases 1->2`.
- Tests to keep green: `test_m56_predict.py` 11/11, `test_walk_diff.py` 37/37, `test_classify.py`
  17/17, `check_classes.py` 17/0 (delete UNTRACKED `evidence/**/_3x.png` after; the 14 tracked ones
  stay).
- `python3 scripts/evidence.py budget` BEFORE adding frames (gate FAILs at 30 MB; ~25 MB used).

## TRAPS

- **gdb register side-values lie** (see 2 above); the sampler + read-backs are the evidence.
- **A hw watchpoint on a constantly-read field crawls the game** — year never moves. Breakpoints.
- **Pokes lie while a tracer is attached** — poke BEFORE attaching, verify after `kill -CONT`
  (smac_play M33 note). `m57_credit.py` makes NO writes while gdb is up.
- **The queue widget base != the display base**; INSERT lands on the widget's base. Verify pending
  after every click.
- **Base indices drift** (array compaction): locate by NAME/(x,y). Record indices lie across a
  boundary too; identity is (x, y, type, owner, order).
- Escape on the map raises the quit prompt, and after it is dismissed the game takes NO KEYS (only
  clicks) — reload is the only recovery. Never Escape on the map; never click OK on the quit prompt.
- `orders_mode` (`0x91b5b8`) at 0 silently disables every order key (`h`/`g`/`l` fall through to the
  cursor-tile handler); it opens the BASE screen via `b` instead. Restore it before a run that uses
  `h`.
- A modal pane is invisible to memory reads and eats keys; popup BARS do not take clicks (Return on
  the default row and Escape do; the MENU click at (75,369) works).
- `/tmp` quota: `P.freeze()` returns a path that does not exist when full — `df /tmp` before
  trusting a frame; `rm -f /tmp/*.xwd /tmp/*.png` frees it.
- The after-snapshot must be taken AFTER the walk completes (`--settle 2.5`), else the walk-home
  floor fails on a sampling artifact.
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
