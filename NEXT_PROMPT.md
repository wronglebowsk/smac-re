# NEXT_PROMPT — SMAC RE, session 75

Read IN FULL: this file, then `FOOTING.md` (facts — do not re-derive), kit, options. Do ONE milestone, checkpoint to
`SESSION_NOTES.md` (+ rewrite this), STOP.

Ledger: M48d, M50a-b, M51a, M52a-b, M53a-M53r, **M53s (done, session 75)**; open: **M53t (THE
PICK)** + "Later" list.

## First actions
1. Skill `smac-cvr-format`: `SKILL.md` ~19 KB (fine whole); depth in `references/` — open ONLY what
   the milestone needs: `production-rebuild.md` (scan/budget/middle-pass rules), `code-atlas.md`
   (fields), `wine-operations.md`.
2. `tail -95 ~/reverse/smac/SESSION_NOTES.md` — Session 75 (M53s) is the latest milestone.
3. `git status`; `git branch` (never commit to main); then `python3 scripts/milestone.py start <ID>`.
4. Live state (re-verify `scripts/smac_state.py --json` first): pid 2124624 (`pgrep -x terran.exe`),
   year 2385, turn_flags 0x10000, **idle**, cur_player == player == 3, TracerPid 0; dump globals:
   cur base idx 69, nb 75, nunit 331, mask 0xff08, `0x91c628 = 1` (it MOVES), `0x8f0c44 = 3`,
   `0x8f0c4c = 6`, `0x8f0d30 = 1`, `0x985b48 = -2`, `0x985bc0 = 2`. The Colony = idx 23, owner 2
   (relocate by owner byte / faction byte@14, NOT by name; unit slots SHUFFLE).
5. **THE MODEL READS A DUMP**: `scripts/m53p_recon_a.py` consumes `evidence/m53o_mem/*.bin`; run
   `python3 scripts/m53o_mem.py` FIRST and name the refresh in every report. `--stale-mask` =
   superseded entry path; `--no-pop-recover` = plain replay view (default runs the drift probe).
6. **Baseline before any change** (fresh dump; `evidence/m53s_run0.txt` is the reference run): 76
   rows, 76 self-consistent, 65 exact, 11 c4-only residuals (1,3,5,8,30,34,46,51,60,62,69), cells
   bc 0 c0 0 c4 11 c8 0. `python3 evidence/m53s_probe.py` must then print
   `model==history(ac,b0,b4,b8) on 76 rows` and
   `gains: {1:1,3:3,5:2,8:2,30:2,34:2,46:5,51:3,60:2,62:1,69:1}`.

## Footing — open `FOOTING.md` (~12 KB) before touching the game

The verified rebuild model (M48d -> M53s) now lives in **`FOOTING.md`** — moved out of this file to keep
the always-loaded prompt under budget. Sections: `### M53s (75)` the 11 c4 residuals = `FUN_004eaa10`'s
allied-energy fold, NOT a scan bug · `### M53r (74)` pop-drift budget · `### M53q (73)` pool recomputed
per base · `### M53o (67)` vector == yield sum · `### Standing` base/unit record offsets + globals.
Grep `^### ` and read only the section the milestone needs. Do not re-derive: `4e78e0`'s exit shifts
history, so `base+0xac/b0/b4/b8` is the visit-exit vector (model matches 76/76); the residual is folded
at 0x4eac57-62 *after* the rebuild, not inside it.

## Static-reading kit
- **Look-up before grep:** `python3 scripts/index.py search "<question>"` — indexes evidence/*.md +
  skill/references/*.md + NAMED.md (3,465 chunks); returns file:line leads; cite the file, not the
  hit.
- **Cached whole-`.text` disassembly `evidence/m53j_text.txt.gz`** (objdump intel). Locate a VA:
  `zgrep -n '  4eac62:' evidence/m53j_text.txt.gz`; windows `gunzip -c … | sed -n 'A,Bp'` (plain
  `sed` on .gz returns nothing). **VA = file offset + 0x400000.** VA→function: `awk -v A=0x005ab223
  -F, 'NR>1 && $1<=A {n=$2;p=$1} END{print p,n}' ghidra_out/index.csv` (COMMA separated).
  FUN_004e78e0 window with A:NNN numbering: `evidence/m53o_fn4e78e0_asm.txt`. Destination-only
  store sweeps (filter `ebp` out of the destination; include `[reg+reg*1-0x4]` walk forms) are the
  way to find a field's writers — the ones that cracked M53s are written up in
  `evidence/m53s_findings.md` F5 + `evidence/m53s_writer_scan.md`.
- POINTER-TYPE SCALES — the trap: Ghidra types some DATs `short *` (offsets HALF) or `int *` (x4).
  Never trust a pseudocode field offset; pin against machine disp or live pread (`frec()` in
  m53p_recon_a.py takes ABSOLUTE addrs). x86 `test/je` fires when the tested bits ARE set; read the
  machine branch before believing pseudocode cmp/jle polarity (M53r tripped on guard-1). **gdb
  watchpoints report the instruction AFTER the store.**
- Pseudocode: `scripts/fn.py 0xADDR > evidence/<id>_fn.txt`; corpus `grep -rn <pat> ghidra_out/
  shard_*.c`; alpha headers name the columns (`alpha.txt` :132 #RESOURCEINFO, :560 #UNITS, :590
  #FACILITIES, :710 #RESOURCES); `scripts/parse_alpha.py` -> `data/alpha.json`.
## Operational kit
- pid via `pgrep -x terran.exe`; window via `scripts/smac_play.py find_window()` (10485761, 800x600,
  root position 0,0 — root-capture pixels ARE window coords). Preflight: no gdb, TracerPid 0,
  `ptrace_scope` 0. `xwd` needs **`-display :99`** (DISPLAY=:0 fails). No ImageMagick: convert with
  `ffmpeg -loglevel error -i f.xwd -vf crop=800:600:0:0 -y f.png`. **`tesseract <png> tsv` and
  `--psm 6` return NOTHING on this build** — use `smac_play.ocr_fast()` (returns (text,cx,cy,w,h))
  or plain `tesseract f.png -`. Dark-labelled bars are invisible to OCR: find them by **COLOUR
  GEOMETRY** (light periwinkle: b>120, r,g>90, |r-g|<40, b-r>25, run > 55 px over >= 12 scanlines)
  — `evidence/m53s_barclick.py`.
- **Turn driver:** `python3 scripts/smac_play.py --turns N --timeout S --no-escape S'` where
  **`--no-escape N` = "never press Escape during the first N seconds"** (the driver classifies the
  "Do you really want to quit?" dialog as a title screen; clear it with `xdotool windowfocus <win>`
  + Escape, NEVER click). **This checkout has NO `--mode stop`** — bound a backgrounded driver with
  shell `timeout`; never `pkill -f`/`pgrep|kill` by name. **NEW (session 75): if the base/tile panel
  is open and the message pane says "nutrients" (a BASE_WORD), every frame classifies as `base`, so
  the driver never clicks TURN COMPLETE and — with `--no-escape` > timeout — never Escapes either
  (two 250 s STUCK runs, zero hook hits).** Working recipe: `python3 evidence/m53s_endturn.py
  [limit]` (clicks the OCR'd `COMPLETE` word at 697,416, answers "Do you really want to end the
  turn now?" with `answer_confirm` — Yes row then OK bar; **Return alone keeps "No"**), then ride
  the Council phase: PROTOCOL DIRECTOR OK bar, PROPOSAL vote bars measured at x = 311/400/489,
  y ~= 498, then the HIVE bribe pane (response bar y ~= 220; Escape closes it, Return advances).
  A round costs ~15 s of AI plus the Council clicks; `m53s_barclick.py` clicks the bottom bar.
- **Stalled round? Run `python3 scripts/m53q_livelock.py`** (turn_flags + `+48`/`+50` chain census;
  `--fix` pokes the offending link to 0xFFFF). Signature: turn_flags bit 1 + hot main + static
  screen. It read CLEAN throughout session 75 (the stalls were UI modals, not livelock).
- **PROPOSAL pane** (stalls AI phase): TRUE window coords YEA (310,495) / NAY (398,495) / ABSTAIN
  (485,495), one OK (393,495); `YEA: 2 NAY: 3` = tally (re-measured 311/400/489 @ ~498 in 2385).
  Capture `xwd -display :99 -root -silent` + upscale + tesseract; click after `xdotool windowfocus`.
- **Snapshots:** `python3 scripts/m53l_snap.py > evidence/x.tsv` (read-only walk of all bases) and
  `python3 scripts/m53o_mem.py` (refreshes the dump the model reads). **Model:**
  `python3 scripts/m53p_recon_a.py $(seq 0 75)` — parse with `evidence/m53p_swap_parse.py` (`--sc`)
  or `evidence/m53p_fresh_parse.py`. Per-row probes: **`evidence/m53s_probe.py` (model-vs-history
  snapshot equality + "which base field equals the gain" sweep)**, `m53q_maskcmp.py`, `m53q_nonsc.py`,
  `m53r_sig.py` (saved-carry vs replay-budget signature), live probe `m53q_probe.py`.
  `--no-pop-recover` = plain replay view; the default prints `pop-drift=+1(pop a->b)` on recovered.
- **Watchpoints: x86 DR budget = 4 hw slots** (8-byte windows need 8-alignment = 2 DRs each); pair
  with the 10 Hz `/proc/mem` poller `scripts/m53m_poll.py`. Bake addresses as LITERALS **but compute
  them in code** (a hand-computed literal cost a wasted run: base46+0xc4 = **0x961174**, not
  0x991174), `stdbuf -o0`, `gdb -batch -nx -q -p PID -x scripts/x.gdb` backgrounded + drive +
  snapshot in ONE job (`scripts/m53n_drive.py` = template). **Watchpoints fire on VALUE CHANGE, not
  on stores, and name the NEXT instruction.** Ready-made arm/stop pairs: **`scripts/m53s_c4watch.py`**
  (hw watch two bases' `+0xc4`, logs pc + new value) and **`scripts/m53s_c74_watch.py`** (int3 at
  0x4eaa2e, logs idx/c4pre/add/c74/curidx): `--mode arm` preflights and returns, `--mode stop`
  SIGINTs the pidfile pid, waits for "detached", `kill -CONT terran.exe` — never signal by name.
## Milestone options (pick ONE)
- **M53t — IMPLEMENT THE FOLD, close the 11 residuals (THE PICK).** In `scripts/m53p_recon_a.py`,
  after the rebuild, add `base+0xc4 += Sigma over allied other-factions of esi` per findings F6:
  stance bit 2 either direction (`0x94d448+fac*0x20bc+o*4`), `faction[other]+0xd54 != 0`, the k-th
  nearest allied base via `FUN_004ea940` (walks 0x95dac4 stride 0x130 — read its k-selection and
  where 4eaa10's `local_10` comes from first), the `0x94d4f0` / `[fac-record-0x244]` zero-gates,
  `n = ceil((ally_base+0xb4 + my+0xb4)/8)` (double if `0x985bd4 < 0x985bd0`), `esi = (([0x94d734+
  fac*0x20bc]+1)*n + ((count-1)>>1))/(0x92a274+1)`, halve without stance bit 1, `+1` if
  `0x985bc0 == fac`. Acceptance: on the pre-drive dump state the 11 residuals collapse to exact
  (gains {1:1,3:3,5:2,8:2,30:2,34:2,46:5,51:3,60:2,62:1,69:1} reproduced from data, not asserted)
  and the 65 exact rows stay exact. Do NOT re-open the scan/yield rules — F1 says they are done.
- **Then (Later):** why idx 6 joined the gain set and idx 51's gain moved 3 -> 2; consumers of
  `DAT_008f0d40`; `unit+24/25` + `unit+38` semantics; who writes the seed dwords (faction+0x2e20);
  `base+0x84` nibble semantics; `DAT_008f0cc8` consumer; who sets +0xe0; byte@5 meaning;
  `turn_flags` bit 16; the bit-8 live-table disagreement at tile (45,9); `c80_end != stored d80` on
  idx 24/35; why pop-drift is fac-2-only; the 417ee0 UI row-loop behind the 13x; M50c-e, M51b.
- **Retired premises, do not resurrect:** "bc/c0/cc are persistent accumulators written only by
  4e92c0/4e93f0"; "4ef6d0 never runs"/"re-runs the block twice"; "the round walks all bases in index
  order" (grouped by owner, ours LAST); "bc/c0 gain per sweep fire"; "the Colony is fac 3" (owner 2,
  idx 23); "4e40a0 tests the whole mask dword" (LOW byte only); "pseudocode offsets are byte
  offsets" (short* x2, int* x4 — `DAT_008f0d60[3]` = pop byte@6); "claim table 0x985aa0[72]" (33 @
  0x985b3c); "PROPOSAL pane `YEA: 2 NAY: 3` is a key hint"; "4e3470's 19 hits = calls"; "0x4f1e3f
  drains base+0x40"; "base+0x78 entry mask = ~(pop|1)"; "DAT_008f0d30 = 1 is a scenario constant";
  "the freshness marker 0x68cbb4 is -1 while idle"; "the entry filter clears pool bits via the
  stale global d30" (pool∩fresh = {bit 0} on 76/76); "the +50 walk re-anchors to the stack head";
  "the |=8 gate fires when the +25 faction bit is SET"; "FUN_005a5c00 is identity" (only when
  0x920434 != 0); "the middle-pass corrections subtract pop+k2 then halve"; "the model reads live
  memory"; "0x91c628 = 0 is constant"; the session-68 "Class S / Class J" framing; **"the 11 fac-2
  non-sc rows are a scan-ORDER problem"** (M53r: pop-drift budget rows); **"skip flag = tile
  out-of-mask"** (faction-mask test, M53r); **"swap guard: best-add index > 0 exits uncommitted"**
  (it COMMITS only then); **"4e78e0 exit clears bit 8 of +0x30"** (bit 17); **"pop byte@6 is the pop
  the visit used"** (dump value is post-visit — 22 rows drift +1); the session-73 census 65 sc / 54
  exact (session-74 dump: 76 sc / 65 exact); **"the 11 c4-only residuals mean a missing yield
  branch, a drifted 4e7070 input, or `0x8f0c4c` divisors"** (M53s: the model matches the game's own
  visit-time snapshot 76/76 — the delta is downstream of the rebuild); **"0xc4/0xc8 have NO
  downstream writers"** (c4 has two, both in FUN_004eaa10: 0x4eaa30 and 0x4eac62); **"stored
  base+0xc4 == the rebuild's output"** (it is snapshot + alliance share); **"the driver can always
  end a turn with `--turns 1`"** (see Operational kit).
