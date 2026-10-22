# SMAC (terran.exe) — full reverse-engineering roadmap

> Operational breakdown with hit-able milestones: **`MILESTONES.md`** (status board, proof
> requirement, 2-session tripwire, chapter estimates). This file is strategy; that one is the checklist.

**Goal:** understand Sid Meier's Alpha Centauri well enough to reimplement it — solo play with
working AI on modern hardware, full menus + game UI recreated (Paul's stated target), with every
subsystem documented and every shipped asset/format decoded.

**Written 2026-10-20 (session 9), after M8.** Durable project dir: `~/reverse/smac/`. Session
history: `SESSION_NOTES.md`. Turn-cycle findings: `turn_stall.md`. Netcode: `dplay_solo.md`,
`FINDINGS.md`. UI/assets: `UI_MAP.md`.

---

## 1. Retrospective — what this workflow got right, what it wasted

### Right (keep)
- **Append-only writeups + one milestone per session.** `turn_stall.md` / `SESSION_NOTES.md` let a
  fresh session start in 3 tool calls instead of re-deriving. This is the reason M6→M7→M8 chained
  across sessions at all.
- **Positive controls.** M7 (control bp on WNDPROC `FUN_005d0c33`, 403 hits) is what made M6b's
  "zero dispatcher hits" a real result instead of a gdb artifact. Cheapest high-value habit in the
  whole project.
- **Differential breakpoint counting** (this session): N auto-continue logging bps + perform the
  action + count tags. Decisive, cheap, no sampling math. It located solo's turn path in one run.
- **Local caches over engine calls.** `.text_insns.json` (capstone) + `xref_scan.py` answer call-xref
  questions in <10 s; `push ebp / mov ebp,esp` prologue scan gives function containment that matched
  Ghidra names on every known pair checked. 5,768 function starts found for free.
- **Observed vs inferred separated**, with stated caveats. No finding had to be retracted twice.

### Wasted (fix)
- **Wrong order of attack on the turn stall.** M1 built a DirectPlay hypothesis from static call
  graphs; M3 killed it with ONE runtime probe (`WINEDEBUG=+dplayx`, one launch). A falsifiable
  runtime probe should have come first. Sessions 7b–8 were spent inside a refuted frame.
- **Unverified measurement premises.** M4 blamed llvmpipe for CPU burn (wrong, M5 proved it via
  perf). M6 wasted an attach because gdb was attached during the slow intro movie. And M8 shows the
  headline symptom — "turn won't complete" — is at least largely an **automation artifact**: modal
  dialogs (ABOUT RESEARCH, CONFIRM RESEARCH PRIORITIES) swallow the TURN COMPLETE click while the
  game idles in its normal pump. 7 turns advanced with zero special effort.
- **No clean-environment check.** 10 orphaned `winedevice.exe` from dead sessions burned ~40% CPU
  each (load 12.0 on 4 cores), crawling the intro and mistiming blind clicks. Invisible for three
  sessions; boot time halved once killed.
- **No harness, no state reader.** Every turn was hand-clicked at drifting coordinates (old notes
  say end-turn row (300,231)/OK (400,257); live geometry is (300,197)/(400,222)) and read by
  screenshot+vision. Vision is the most expensive thing in the loop and it was used as a HUD
  readout.
- **Ghidra used as a lookup service instead of a batch export.** Only **109 functions** are dumped
  (85 pseudocode + 24 asm, 1.8 MB) out of **~5,768** function bodies in `.text` (0x401000–0x670000)
  ⇒ **≈1.9% of the code read**, while every new session pays ~205 s for a Ghidra import to answer
  one question. No saved Ghidra project exists in `~/reverse/smac/`.

**Verdict:** context discipline and evidence discipline are strong; **measurement infrastructure is
the bottleneck**, not RE cleverness. Recent effort went into a phenomenon that was partly tooling
error. Next work should be ~1 phase of infrastructure, then spine-first RE.

---

## 2. What "fully reverse engineered" means here (exit gates)

Checkable gates, in dependency order. "Done" = all four, but each is independently valuable.

- **G1 — Behavioral:** the game plays solo to a victory condition under an automated, dialog-aware
  harness with no human input, and each subsystem has a written model that predicts an observable
  outcome (year/energy/units/UI) that the harness verifies.
- **G2 — Data:** every shipped asset/format round-trips through a decoder+encoder we wrote:
  `.cvr` (done), `.flc` (type 7 color semantics open), `.pcx` (open), `.techs`, `.sc` scenarios,
  `.sav` saves (round-trip = strongest proof), `Script.txt` (parsed), `alpha.txt #RULES`, sound/voice
  clip catalog, CD audio/movies.
- **G3 — Code coverage:** `COVERAGE.md` ledger buckets ≥90% of non-CRT/library functions by
  subsystem with names, and the five spines (§3) are traced call-by-call with pseudocode on disk.
- **G4 — Parity:** a reimplementation reproduces recorded golden traces (seeded run: action log →
  state-delta sequence) for the automated playthroughs.

---

## 3. Strategy: corpus-first, then five spines

Do not grind function-by-function. Build a grep-able decompile corpus + a harness, then trace five
end-to-end **spines** (tracer bullets). Spines pull the interesting 20% of the code in dependency
order and each ends in a harness-verifiable assertion.

| # | Spine | Proves |
|---|-------|--------|
| S1 | boot → unpack → main menu → new game (QUICK START) | self-modifying loader, init order, scenario/faction setup |
| S2 | **turn advance (solo)** — `TURN COMPLETE` → upkeep → production → research → AI → events → next player | the game's heartbeat; already started (M8) |
| S3 | unit order → execution → combat resolution → death/occupation | action rules, combat math, unit AI |
| S4 | research spend → tech unlock → new unit/facility/ability available in UI | tech tree, `.techs`, UI unlock plumbing |
| S5 | save → quit → load → identical state | all game state is in the save file ⇒ forces a complete state inventory |

Everything else (netcode, presentation, audio, movies) attaches to whichever spine touches it.

---

## 4. Phases and milestones

### Phase 0 — Infrastructure (do first; 2–3 sessions)

**0.1 Preflight script** — `scripts/preflight.sh`
Kill orphans before measuring: `pkill -f '[t]erran.exe'; pkill -f '[w]ineserver'; pkill -f '[w]inedevice.exe'`,
assert `uptime` load < nproc, ensure Xvfb :99, launch, key-skip intro, verify HUD.
*Verify:* `load average` < 2.0 and no `winedevice.exe` older than the current wineserver.

**0.2 Game-state reader (kills most vision calls)** — `scripts/smac_state.py`
Find the Mission Year / Energy / research-pipeline / current-player globals once, then poll via
`/proc/<pid>/mem` (no gdb, no screenshot). Method: with the live game (Year 2107 = 0x83B, pid
3042382), gdb `find`/scan for the value, narrow by diffing before/after a turn, confirm the address
survives save+reload. Candidate region: the `DAT_009xxxxx` state block (M8 showed the turn
semaphore lives at `DAT_0091f698`–`0x91f6d4`, player mask `_DAT_00985b10`, current player
`DAT_00985dcc`, own index `DAT_0091b5b4`, turn counter `DAT_0091f694`).
*Verify:* printed year matches a screenshot crop for 3 consecutive turns.

**0.3 Dialog-aware automation** — `scripts/smac_play.py`
Uses `script_parsed.json` (1,357 panes with `#x/#y/#xs/#button` geometry) to click panes/buttons by
**name** instead of remembered pixels; loop turns; on each poll assert year advanced; on failure
dump which modal pane is open. Emits a **golden trace** (seed, action log, per-turn state deltas) to
`traces/`.
*Verify:* 20 consecutive turns advanced, zero vision calls, trace file written.

**0.4 Runtime DATA snapshot (data only, optional)** — `terran_runtime.bin`  
__Superseded in scope by `DATA_INVENTORY.md` (2026-10-20): the shipped data formats are PCX, FLIC,
CVR (already decoded 113/113) and plain text (`alpha.txt` = rules, 45 sections/650 records parsed to
`data/alpha.json`; `Script.txt` = dialog scripts). No exotic container needs decoding; only
`maps/planet.MP` remains unknown.__
The code needs no snapshot: `.text` raw bytes cover VA 0x401000–0x671000 (verified 2026-10-20), so
Ghidra's decompile is authoritative everywhere. What is missing from the file is **initialized data**
above VA ≈0x6a9000 (`.data` vsize 0x316284 vs rawsize 0x20000 ⇒ BSS at runtime). If a global's
*initial values* matter (GUIDs, tables, default settings), snapshot runtime memory:
`gdb -batch -p <pid> -ex 'dump binary memory /tmp/terran_data_0x6a9000.bin 0x6a9000 0x9a0000'`.
*Verify:* `DAT_0091f6c4` / `DAT_00985b10` resolve, and their initial values match what the code expects.

**0.5 One-time full Ghidra export** — `ghidra_out/shard_NNN.c` + `ghidra_out/index.csv`  
__IN PROGRESS 2026-10-20: `ghidra_scripts/ExportAll.java` (shards of 250, index.csv, MANIFEST.txt).
Consume with `scripts/fn.py` / `scripts/coverage.py` → `COVERAGE.md`.__
`analyzeHeadless` with a postScript that decompiles **every** function and emits
`address,name,size,#callers,#callees,strings_referenced`. Run in background (est. 1–3 h for ~5.8k
functions on 4 cores). After this: **grep first, REA last** — the ~205 s/session import tax disappears.
*Verify:* index row count ≈ function-manager function count; spot-check 3 known functions.

**0.6 Coverage ledger** — `COVERAGE.md` + `scripts/coverage.py`
Bucket every exported function by subsystem using strings/call-graph clusters (rendering, UI panes,
input, netcode, AI, economy, research, combat, save/load, audio, iso/cdr, scenario, movies). Print
counts + % named. This is what makes "fully RE'd" a number instead of a feeling.

### Phase 1 — Spine S2: solo turn advance (2–4 sessions; M9 starts here)
- Decompile `FUN_0051e700` (0x51e700–~0x51f730) and its callers `FUN_0050ef60`, `FUN_0050f420`,
  `FUN_00520c10`; document the per-turn sequence and the `DAT_0091f69x` semaphore semantics
  (solo drives it directly — M8: 47,004 hits, 0 when idle).
- gdb backtrace at a `FUN_0051e700` hit (trap stops *inside* game code; the EBP chain may unwind
  even though bt won't pass ntdll).
- Play 20–40 turns with the harness (§0.3). If a genuine stall appears at some year, catch it with
  armed bps + state reader.
- Deliverable: `turn_spine.md`. Exit: harness plays 40 turns unattended, and each phase of the turn
  is named in a written model.

### Phase 2 — Game systems, spine-driven (8–15 sessions)
Each = one doc file + a harness assertion. Order: S3 combat/orders → S4 tech/research → economy &
production (energy, facilities, `alpha.txt #RULES` knobs) → planet/geoscape (tiles, mining,
vibration, terraforming, probes/events) → social/psi (`FUN_004d6fb0` gate) → AI policies (start with
`FUN_00546800` **basic-block skeleton only**, 3924 lines → `ai_skeleton.md`, then per-branch) →
faction/leader abilities → victory conditions → scenario load (`.sc`) → **save/load (S5)** → map/RNG
determinism (seed capture).
Exit: G1 met.

### Phase 3 — Presentation layer (4–8 sessions)
FLIC type-7 RLE word-color semantics + per-object transparency/ref (`flc_decode4.py` in progress);
PCX v3 variant RLE (glsmac hits the same wall — expect procedural fixes); CPane/CWidget framework
(`FUN_00444140`, `FUN_0047c0e0`; widget vtable+0x124 = drag/scroll, which is why blind map clicks
fail); HUD builders; fonts; sound/voice clip token table (0x68b000–0x691600) + audio path; movie
playback (`FUN_0062ad73` → `FUN_0062bdeb`). Exit: G2 met (minus encoder-side gaps).

### Phase 4 — Netcode completion (2–3 sessions, optional/secondary)
Already mapped (`FINDINGS.md`): jackal packet, seq/ack, anti-replay, type encoding, diplomatic
types, lock/done sync. Finish: solo-vs-host divergence (M8 proved solo skips `FUN_00584010` +
`FUN_0052bce0` entirely — re-document the "dispatcher is source of truth for solo" claim as
MP/host-only), and a two-instance LAN game under Wine to golden-log the wire. Risk: Wine DirectPlay
for two instances is unproven (M3 showed solo never opens a DP session).

### Phase 5 — Reimplementation (large, optional)
Engine skeleton, data-driven from `Script.txt` + `alpha.txt` + decoded assets; `glsmac`
(`~/reverse/smac/glsmac`) as a Rosetta stone for resource naming and atlas layout. Parity = replay
golden traces from §0.3. Exit: G4.

---

## 5. Standing rules (bake into the skill; these are the lessons)

1. **Runtime before static for behavior; static before runtime for structure/formats.** One
   `WINEDEBUG`/breakpoint probe beats an hour of call-graph reading when the question is "does this
   ever run?"
2. **Preflight every measurement run** (orphans, load, boot-to-HUD confirmed) and **always arm a
   positive control** in the same log.
3. **Prefer counting to sampling**: auto-continue logging bps + perform the action + count tags.
4. **Prefer memory reads to screenshots; screenshots only for state changes, and cropped**
   (`crop=250:60:555:550` for the year/energy readout; `vstack` several crops into one vision call).
5. **One hypothesis per session, with its falsification test written down and costing ≤1 launch.**
6. **Grep the exported corpus before opening REA/Ghidra.** Keep every dump on disk; never paste a
   whole pseudocode file into chat.
7. **Never trust remembered click coordinates** — derive them from `script_parsed.json` pane geometry.
8. After each milestone: append to the topic file + one dated line to `SESSION_NOTES.md`, then stop.

---

## 6. Risks / open questions

- **Static vs runtime image — resolved.** The code is fully present in the file (`.text` raw covers
  VA 0x401000–0x671000); only initialized *data* above VA ≈0x6a9000 is BSS-only. So the full export
  (0.5) is trustworthy everywhere, and 0.4 is a data snapshot at most. No ordering constraint.
- **Scale.** ~5,768 function bodies (heuristic prologue count, `.text` 0x401000–0x670000); full
  decompile time unknown; some are MSVC CRT/ATL/MFC-ish runtime that should be *identified*, not
  read (match against known 1999 MSVC + DirectX signatures to shrink the denominator).
- **Wine nondeterminism** could poison golden traces; capture the game's RNG seed per run.
- **Automation vs real play:** a modal-dialog-driven "stall" is a UI fact, but a genuine late-game
  stall (large AI turn, many units) may still exist — Phase 1's 40-turn run is the test.
- **PCX/FLIC encoder side** may never be recoverable from the exe alone (procedural atlases);
  acceptable to ship decode-only and keep our own encoder.
- Total estimate to G3: **~20–35 short sessions** at current discipline; G4 is a project of its own.

## 7. Immediate next step (M9)

The game is live now (terran.exe pid 3042382, Year 2107). Do **0.2 state-reader address hunting**
while it is up and mid-play — that address hunt is much cheaper with a running game than a cold
boot, and everything downstream (0.3 harness, Phase 1) depends on it.
