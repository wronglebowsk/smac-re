---
name: smac-cvr-format
description: "Use for SMAC .cvr Caviar voxel decode/render or SMAC RE."
---

# SMAC .cvr = Caviar voxel models

Sid Meier's Alpha Centauri (1999) `terran.exe` + `programs/*.cvr` live in
`~/reverse/smac/` (durable). Full writeup: `~/reverse/smac/FINDINGS.md`.
**The repo AND the Wine box are LOCAL as of 2026-11-15.** Both moved off `n100` onto the gateway
host: repo `/home/paul/reverse/smac`, Ghidra `~/tools/ghidra_12.1.4_PUBLIC` (JDK 21), Wine
`~/tools/wine-10.20-staging-tkg-x86` + prefix `~/.wine-smac32`. Wine 32-bit needs the i386
multiarch libs (`libc6/libgl1/libasound2/libgnutls30t64/libgcrypt20/libpulse0/libfreetype6` all
`:i386`); the wine-11 amd64-wow64 build CANNOT open the win32 prefix. Everything runs in-process —
no SSH, no `smacsh`. Two things the move taught: a stale `git worktree` entry pointing at the old
host makes `milestone.py merge` fail to delete its branch **after GitHub has already merged**
(`cannot delete branch 'milestone/…' used by worktree at '/home/n100/…'`) — `git worktree prune`
first; and every script path that hardcoded `/home/user/…` (no machine ever had it) had to be
repointed, so grep `home/user` before assuming a helper still runs. The n100 tree is kept only as
a cold rollback; **legacy `smacsh` discipline, if you drive it: a python file AUTHORED through the
smacsh heredoc must be backslash-free** (the transport unescapes backslash sequences, so a byte
literal lands as RAW bytes — the file still compiles, then compares wrong; ship `bytes([0x.., ...])`
lists, no backslash regex classes, and no `&` anywhere in the heredoc), **and scp must target
`<n100-user>@<lan-ip>`** (the `n100` ssh alias resolves to a tailscale IP that times out).
The live skill copy sits on the session host while the tracked copy is `skill/` in the repo, so a
skill edit must land on both in the same session.
**Versioned at `github.com/wronglebowsk/smac-re` (private)**; a copy of this skill is tracked
in-repo under `skill/` — after editing the skill, refresh it there and push. Game binaries,
`programs/`, `smac.iso`, `glsmac/` and regenerable Ghidra/FLIC output are gitignored: never
`git add -f` them.
Decoder + iso renderer: `~/reverse/smac/cvr_decode.py` (validates 113/113).

**This file warns at 55,000 BYTES and FAILS the repo gate at 70,000 (`wc -c` of `skill/SKILL.md`).** The
always-loaded set (AGENTS.md + NEXT_PROMPT.md + this file) carries a 60 kB ritual target
(`docs/EVIDENCE.md`), so keep this file near 44 KB or less — run `python3 scripts/evidence.py budget`
before and after an append. Depth lives in `references/`; open the ONE file you need:
`code-atlas.md` (record/field layouts, VA→function recipe, the PE section table, the census-script family),
`wine-operations.md` (driving, dialogs, watchpoints), `wine-pitfalls.md` (the FULL s242-retired Wine/gdb
pitfall set, verbatim), `instrument-laws.md` (the laws), `solo-round-boundary.md` (solo heartbeat model,
auto-end timing, boundary diff accounting), `production-rebuild.md` (production-vector machine rules),
`production-queue.md` (the build queue: gate `0x4efa5e` and its own affordability test, the completion
chain, **the INSERT is not a sort**, POP pops ONE item and left-shifts only `0..pending-1`, the visit's
cost product vs `price_of`, the cursor-field writers, slots 1..`pending`, the negative recordless types,
the produced-unit freeze, mock-mem predictor tests), `static-store-census.md` (store census shapes, the
live write-enumeration acceptance §9, why-a-site-never-fires §10, the vtable model §13, census-parser
traps §14), `ptrace-level-probes.md` (strace raw args, soft-dirty/pagemap, one tracer per task, the
.SAV chain), `wine-headless-harness.md` (turn automation), `open-leads.md` (unanswered questions with
cites), `screen-read.md` (why ONE OCR pass is not a screen read), `verify-outcome.md`,
`gdb-command-list.md`, `ui-chooser-state.md`, `git-workflow.md`, `wine-runnability.md`,
`data-formats.md` (map/save containers + the CVR sibling), `cvr-format.md` (the .cvr TLV/voxel format
core, retired to depth s242), `netcode.md` (the "jackal" netcode map), `ui-assets.md` (Script.txt,
alpha.txt, PCX/FLIC, glsmac), `ghidra-batch-export.md`, `terraforming-order-path.md`,
`session-discipline.md` (budget, closing order, handoff, shadow-running the cron loop, parallel
two-endpoint chains, and the full s242-retired discipline/evidence text), `review-pipeline.md` (local review pipeline: lint design
classes, reviewer validation). `grep -n '^## \|^### ' SKILL.md` and the references, then
`sed -n 'A,Bp'` the section you need. When adding depth, append to the right reference; only new
cross-cutting pitfalls belong here.
**Before statically deriving a field or mechanism a kickoff prompt names, grep the skill's `references/` and the repo docs for that offset/mechanism** — much of the UI plumbing (chooser bars, its cancel sentinel, the handler case map) is already settled in `references/wine-operations.md`; a from-scratch objdump derivation spends ~15 tool calls re-deriving a settled answer, and instruction bytes are the arbiter only for a CONFLICT, not the first move. The same grep extends to the LIVE half: before re-instrumenting a site address, `grep -rn <hex-addr> scripts/ evidence/` — a prior census script often already encodes the derivation (and its evidence file already states the reading the new gate would otherwise guess wrong).
The same rule kills NEGATIVE claims: before writing "no code uses constant X", grep the docs' size/offset lists for X AND its near neighbours — a documented 152-B leg is 156 minus a 4-byte field, so an exact-value grep for 156 supports a conclusion that is one subtraction wrong. Then confirm the candidate leg by reading its DESTINATION in `/proc` and comparing content, not by its size (`references/instrument-laws.md` §Proving a read leg).
**For a static fire, import the shared engine instead of writing a second one**: `scripts/m308_site_list.py` exports
`parse_text` (the whole `.text` cache → instruction map, already validated against `index.csv` `n_insns`),
`load_spans`, `load_index`, `pe_sections`, `va2off`, `window`. Hand-rolling either a cache line-split or a PE
offset map produces phantom findings (a "missing instruction" the engine has; one-character tokens read as asset
names), and a mid-line `split` misparses `movsx`/`movzx` (its bytes column is one field narrower, so the
remainder starts with a space and the mnemonic parses as empty) —
`references/instrument-laws.md` §Static text-cache parse traps.
Master plan / exit gates (G1–G4) / phase list: **`~/reverse/smac/ROADMAP.md`** — read it before picking
a milestone. Phase 0 = harness + state reader + full Ghidra export + coverage ledger; do it before more
RE. Five spines (boot, solo turn, unit orders/combat, research/tech, save/load) drive Phases 1–2.

```bash
cd ~/reverse/smac
python3 cvr_decode.py "programs/*.cvr" "programs/*.CVR"   # validate corpus
python3 cvr_decode.py --list Apsid.cvr                    # voxel/frame listing
python3 cvr_decode.py --render programs/Drop.cvr          # -> Drop.render.png in cwd
```

## Git workflow — full text: `references/git-workflow.md`
Never commit to `main`. `milestone.py start <ID>` branches from **`main`** and resets the tree: a milestone
you must build on that was never merged has NONE of its scripts in the tree — branch from it instead
(`git checkout -B milestone/<ID> milestone/<prev>`) and say so in the session entry. `start` refuses a dirty
worktree: stash the `SESSION_CURSOR.md` write, start, pop it onto the new branch — never commit a cursor write
to `main` just to clean the tree. That commit also breaks a landing: a squash merge plus any local `main`
commit makes `merge <n>` abort its ff-only pull AFTER GitHub merged (recovery in the reference); `main` cannot
be pushed (pre-push hook), so post-merge tweaks ride their own branch + PR. When re-running a milestone whose
branch exists, `start` refuses and leaves you on `main`: check the branch + `ls scripts/<id>*` before
concluding the instrument is missing. **Verify the named milestone is not already merged before starting** —
a kickoff prompt can lag the repo: `git log --oneline | grep -i <ID>` plus `grep -n '^## <ID>' NAMED.md`
answers in one call; if both hit, run what `SESSION_CURSOR.md` names and state the swap.
Cycle: `milestone.py start <ID>` → work → `gate.py --base main` GREEN → `submit --title …` → `gh pr checks` →
`merge`. **Create the PR body with a JSON FILE, not inline `curl -d`** — an apostrophe closes the shell quote
and the whole command (including the push) fails as 422 `head invalid`. **Merging several PRs in one session is
queue-bound:** `gh pr checks` sits `pending` 2-4 min merely queued — poll with ~200 s sleeps;
`milestone.py merge` refuses while pending; a force-merge is never the answer.
**Triage every review finding (local `ai_review.py` since Greptile's credits ran out); a re-push does NOT buy another review** (one review per PR, on OPEN). Read the
inline findings with `gh api repos/<owner>/<repo>/pulls/<n>/comments --jq '.[] | "\(.path):\(.line) \(.body)"'`,
fix or dismiss each, and answer all of them in ONE `gh pr comment --body-file` (apostrophes: use the file, never
inline `-b`). The recurring P1 on this repo is a gate that passes on an UNMEASURED state — check every
assertion for "can this FAIL on a real input?" before submitting, and prefer retracting the claim to
re-wording it when the reviewer is right. A docs-only follow-up PR coming back with zero findings is the
cheapest proof the fix actually landed.
**`gh pr edit` is unusable on this repo** (it dies on a GraphQL `projectCards`/Projects-classic deprecation):
patch the title through REST instead — `gh api -X PATCH repos/<owner>/<repo>/pulls/<n> -f title="..."`.
**A GREEN gate is not permission to merge.** The gate audits docs/evidence/harness, not the acceptance. If the
acceptance printed FAIL, keep the checkpoint commits on the branch, submit nothing (or leave the PR unmerged),
and report the FAIL with numbers — weakening a threshold to go green is the one thing never allowed.
**A squash-merge TITLE outlives the finding:** if the milestone opened "BLOCKED" and resolved later on the same
branch, land a small docs PR stating the correction; when a later session narrows a finding, patch the
finding's own `NAMED.md` block in place — a retraction only in `SESSION_NOTES.md` leaves the registry
asserting the older, stronger claim. **A delegated fire will "flag it in the PR" instead of editing the older
block**, so the parent does the in-place patch BEFORE merging (and re-reads the child's claimed retraction of a
prior finding against the shard/exe itself — the registry, not the PR comment, is what the next fire greps).
Each milestone ends with a `## Session N` section in `SESSION_NOTES.md` and a rewritten `NEXT_PROMPT.md`
(<= 12,000 BYTES at close — the budget warn; what `evidence.py budget` prints is `wc -c`). `scratch/` is
gitignored: probes are not repo products; the tracked products are `scripts/`, `evidence/`, docs.
**Skill sync is by CONTENT, not mtime:** a `git checkout` resets mtimes and a merged PR can leave one side
holding a rule the other never got; the gate compares only `SKILL.md`, so an edited `references/` file drifts
silently. Per file: `diff -rq skill/ ~/.hermes/skills/smac-cvr-format/`, reconcile by content, then
`rsync -a skill/ ~/.hermes/skills/smac-cvr-format/` — in the same session, before the closing commit.

## Session discipline (this project is context-heavy) — full text: `references/session-discipline.md`

- `milestone.py start <id>` resets to main: footing carried from an unmerged branch AND `SESSION_CURSOR.md`
  must be re-written AFTER it, or the cursor reverts and a later write is refused as stale. `start` also swaps
  `NEXT_PROMPT.md` for MAIN's copy — when the previous session's update sits unmerged, re-read the sections
  AFTER start and anchor edits on that copy.
- A list cursor read BEFORE the seek is the PREVIOUS cursor: the chooser pump seeks at `0x497717` and only then
  reads `[[c+0xc]+4]`; print at `0x49771c`, not at the pump entry `0x497704`.
- **The save's 22-B COLUMN view is NOT the live tile record** (s236, M290): `sim/save.py tile()[0]` mixes in
  byte 22 and misreads the category. The live byte-0 category (`& 0xe0`: 0-2 water, 3-6 land) lives at
  `grid_off + 44*((W/2)*y + (x>>1))` — the FIRST half of the 44-B record. Any tile-legality fit must use the
  record view or it "proves" the game founded on sea.

Paul wants SMAC RE broken into **small pieces**: complete ONE milestone, write it to a file, append one dated
line to `SESSION_NOTES.md`, then STOP — ending after a single milestone is a success, not a shortfall.
Exception: a **"keep going until you finish <chapter>"** overrides the stop rule — work the chapter's
milestones, doc + evidence each, report once, never relabel partial as done. A bare **"keep going"** after a
report is approval for the recommendation (including `milestone.py merge <n>` on a green PR) — DO it, do not
re-summarise.
**On a chat platform (Telegram), chain tools SILENTLY**: every between-tool sentence arrives as its own message.

### Budget and closing order
- Budget by TOOL CALLS: brief+accept <= 6, milestone 6-30, **checkpoint commit by ~15**, stop measuring at
  30-40, close at 40-50. A fire costs ~5-7 k tokens/call, so "commit at 25" lands at ~167 k with nothing
  committed — branch + commit the SKELETON before probing (measured: 108 k vs 167 k). Cap ACCEPTANCE
  INVOCATIONS at three; the third failure IS the finding. **A static instrument iterates the same way**: debug a
  RED gate by `exec`-ing its source up to the driver and recomputing THAT ONE condition (recipe:
  `references/code-atlas.md`), never by re-running the whole script — a run of six full re-runs plus three
  anchor-fix rounds on the mutation sweep is exactly how a fire hits the iteration ceiling with `NAMED.md`,
  `SESSION_NOTES.md` and the cursor still uncommitted, which costs the next fire its footing. In the
  persistent `execute_code` kernel that costs double: one aliased name (`subprocess = [...]`) poisons every
  later cell, and a module imported before an edit keeps validating the OLD mutation list — re-import +
  `importlib.reload`, or run the step through `terminal` instead of fighting the kernel.
- Close order, every time: cursor -> gate GREEN -> notes entry (`patch`) -> **checkpoint commit** ->
  `NEXT_PROMPT.md` -> submit/PR. Never leave the commit until after the handoff docs. **Every VERIFIED NAMED
  row names the mutation that reddens it** (s290 law; no mutant = INFERRED/OPEN; tracers also get an ALGORITHM
  mutant - depth: `references/instrument-laws.md` §Algorithm mutants + the coverage law). Review pipeline:
  `review_lint.py` at close + `ai_review.py` at submit (`docs/AI-REVIEW.md`; design laws:
  `references/review-pipeline.md`).
- `NEXT_PROMPT.md` <= 12,000 BYTES AT CLOSE (the budget warn; the gate FAILs at 16,000, and closing past the
  warn hands the NEXT fire a docs-only split). `test_loop.py` appends bytes in CI: keep >100 B of headroom
  under whatever number you quote. `SESSION_CURSOR.md` <= 600 B before any step that can exceed ~2 min.
- Docs > 10 KB: `patch` anchored sections, never `read_file`-then-`write_file` — one whole-doc call must fit
  the model's OUTPUT cap, or it truncates mid-JSON and the sanitizer drops it (`missing required field
  'path'`); every retry spends a turn. Two identical re-emissions failing = STOP and compose the file in an
  `execute_code` cell (`open(p,"w").write(src)`; stage big files as scratch chunks and `cat` them together;
  when appending, write the NEW chunk to a scratch path and concatenate — feeding `read_file` output back
  into `write_file` is refused, the guard reads its line-number prefixes as not real content). Anchor in
  hard-wrapped docs by regex `\s+` joins or by INDEX.
- Every always-loaded doc has its own cap and `budget` prints them. **When a cap binds a SECOND session,
  SPLIT**: move settled depth VERBATIM into a topical reference, leave the RULES plus a pointer, re-run
  `budget`. A batch's DOC cost is ~350-700 bytes of `NEXT_PROMPT.md` per new milestone block — measure
  headroom BEFORE choosing batch size.
- Two sessions can share this repo: commit notes/NAMED/scripts EARLY, keep untracked deliverables outside the
  worktree, and name the owner from the process table before arming a measurement.
- Unattended loop scheduling: `templates/cron-milestone-loop.md` (validated kickoff: takes the pick from
  `NEXT_PROMPT.md`, triages doc caps first, proves ownership, caps the batch, merges only on a real PASS).
  **Driving ONE fire by hand:** put the kickoff in a FILE and run `hermes chat --provider qwen125b -m <served-id>
  --query-file <path>` backgrounded with `persist_on_release=True` — a `delegate_task` child dies with the
  session, this one does not. The kickoff must itself demand persistence (branch + commit the skeleton early,
  rewrite `SESSION_CURSOR.md` <=600 B as it goes), so a kill at any moment leaves a resumable branch instead of
  lost context; then the PARENT verifies before merging (re-run the script, diff the evidence, read the gate
  for scope) — never trust the child's summary line.
- **A cron fire's `ok` is a SESSION status, not a CLOSE-OUT status** - a fire can be green on its acceptance and
  still owe the harness/evidence/notes/PR. Full text: `references/session-discipline.md` §taking over a cut-off fire.

### Verify the OUTCOME, not the mechanism — full text: `references/verify-outcome.md`
- Verify the OUTCOME, not the mechanism: compute rival predictions from the baseline, REFUSE a shape where model and null agree on every candidate, read the effect back from memory/state, encode the four exit states (0 measured / 4 never reached / 5 wedged / 8 dirty), and re-verify delegated scripts via a TEMP capture (never process-substitution diff against the script's own output file). Full bullet set VERBATIM: `references/verify-outcome.md` §s290 retirement.

### Evidence lifecycle — the rules live in `docs/EVIDENCE.md`
`python3 scripts/evidence.py budget` — `evidence/` warns at 20 MB, FAILs the gate at 30 MB. Text is never
pruned; an IMAGE stays hot only while the HOT WINDOW cites it — the newest 8 `## Session` sections of
`SESSION_NOTES.md` plus the live footing files (`NEXT_PROMPT.md`, `AGENTS.md`, `SESSION_CURSOR.md`) — or it is
younger than `--keep-days`; lookup/history docs (NAMED.md, pick-archive, named archives, docs/sessions/,
skill references) explain old findings but do NOT hold an image hot: its bytes stay in git and
`evidence.py log` gives the commit. Test-fixture images (named by `scripts/test_*.py`/`scripts/check_classes.py`/`sim/`) live in
`evidence/fixtures/`, which `budget` does not count and `prune` never touches. `prune --apply` moves the rest
to git-only, recorded path/sha256/bytes/commit in `.prune_log.jsonl`.
- Evidence lifecycle depth (sleep + downsample memory samplers BEFORE the first commit; recover the pruned `m53j_text.txt.gz` via `git show 733322c6:evidence/m53j_text.txt.gz`; delegated decodes are TESTIMONY - re-read store sites, address arithmetic and function boundaries from the cache): VERBATIM in `references/session-discipline.md` §s290 retirement.

## Code atlas — read `references/code-atlas.md` before opening Ghidra
The atlas (base-record offsets, terrain formula, faction + unit records, the global map, pointer-type scale
traps, VA→function recipe, the census-script family list, the PE section table) lives there. Open it when you
need a field offset — do not re-derive one from pseudocode: Ghidra types some DATs `short*`/`int*`, so a
pseudocode offset can be HALF or 4x the real byte offset. Unit-record type field: the u16 at `+10`
(`+4` = flags) — the full story + the two generalizing rules are in the reference.
Fast handles: full `.text` disassembly `evidence/m53j_text.txt.gz` (GZIP — `zgrep -n '  4e78e9:'` then
`gunzip -c … | sed -n 'A,Bp'`), or the unpacked aligned cache `scratch/m574/text.txt` (grep by address; parse
by TAB fields). **A hand-rolled field-split on that cache invents MISSING instructions (s272, cost ~8 iterations):**
the bytes column is space-padded and its width varies by encoding, so a `movsx` line's remainder
starts with a SPACE — `line.split(None,1)` parses the mnemonic as `''` and the operand as `movsx`,
and the instruction then "isn't there" for every filter. Read operands through the repo engine
(`scripts/m308_site_list.py:parse_text`) and never accuse a shared parser from a probe: print `ascii(operands)`
before concluding an instruction is absent (a filter matching an immediate by TEXT suffix misses the encoding's
actual form — `shl r,0x4` is the 16-B entry step, so `endswith("0x10")` silently returns zero sites), and ship
`n_insns` from `ghidra_out/index.csv` vs your parsed count in the window as a coverage gate.
**Never `objdump -d --start-address` at an arbitrary address**: a start landing INSIDE an
instruction silently misaligns the whole window — objdump re-synchronizes mid-encoding, invents `.byte` lines,
and poisons any reachability/def-use walk built on it (the witness is a `.byte` line where a `jmp` should be).
Disassemble from the function ENTRY (containment via index.csv) or read the cache. Parse objdump by TAB fields;
require `^[0-9a-f]{6,8}:\t` before int(x,16).
Owner of a VA: `awk -v A=0x… -F, 'NR>1 && strtonum($1)<=strtonum(A){n=$2;p=$1} END{print p,n}'
ghidra_out/index.csv` (commas, no spaces; strtonum REQUIRED — bare `$1<=A` is a STRING compare and you get the
file's LAST function; `awk -v lo=0x55df20` is also a STRING — awk parses hex only inside program code, pass
boundaries as literals in the program); pseudocode `scripts/fn.py 0xADDR`.
Two static instruments answer "what IS this field" with no box time: `scripts/name_global.py <addr> [--disp]`
(every reader/writer of a global + containment — use it BEFORE naming a global from the one reader that
mattered) and `scripts/field_census.py [stride|bit5|readonly|copy|dual]` (the five shape checks). The full
census family (one shape per script — ten census questions through one script is a legit batch; ten that each
need their own harness is ten batches) and the per-faction atlas generator (`m143_m162_atlas.py` ->
`docs/field-atlas-faction.md`, regenerate instead of re-censusing; read its `in NAMED?` dash as "genuinely
unnamed") are listed in `references/code-atlas.md`. Script-reuse + registry-gate traps: `NEXT_PROMPT.md`
TRAP 25. The six structural field laws (element-index multiply before "stride"; a switch is its jump TABLE
behind a bound check, not an address range; count a field in BOTH encodings; degree asymmetry names init-time
values; (function, base-register) reuse proves a struct, writer SETS split its parts; read the writer's SOURCE
before naming members — `setne`/`shr`/`and` chains mean booleans of ONE bitfield, and a many-write/no-test
displacement is a recomputed CACHE no gate may read) are VERBATIM in `references/code-atlas.md`
(§s242 retirement: code-atlas family + structural laws) — same for the chain-eval window law (start at the FOLD SEEDS, never
mid-chain: a window opened past the seeds published an index idiom that was pure truncation). The
chooser/dispatch state family is mapped in `references/ui-chooser-state.md` — read it before re-deriving.

## terran.exe PE layout — full table: `references/code-atlas.md`
Image base 0x400000; `.text` VA **0x401000–0x671000 with raw bytes present** (prologues verified); `.data`
vsize 0x316284 but rawsize 0x20000 ⇒ data above VA ≈0x6a9000 is BSS, no file bytes. Consequences: (1) **all
game CODE is in the file** — Ghidra's decompile of any `FUN_` is authoritative and breakpoints at those VAs
fire; (2) only *data* reads above ≈0x6a9000 need a runtime snapshot (`gdb -batch -ex 'dump binary memory …'`);
(3) `_SELFMOD` is a 0x415d-byte patch area, not an unpacker — the old "analyzed image ≠ file image" note was
an RVA/VA mix-up.

## Map + save container formats — canonical: `MAP_FORMAT.md`, `SAVE_FORMAT.md`; depth `references/data-formats.md`
The `.MP` size formula, the `.SAV` section list (strides 52 B / 304 B), the byte-exact anchors, the
read-wrapper caller trace and the zeros-fraction pitfall are all there. The save TRAILER law (last 156 B fixed, 152 identical across saves, the 6-site per-entity restore loop at stride 0x224B8 proved by POKING markers), and the PER-REGION save_diff mapping law: VERBATIM in `references/data-formats.md` §s290 retirement (the .SAV chain's two read paths stay in `references/ptrace-level-probes.md`). **Any file-vs-memory diff goes through `scripts/save_diff.py`, never an ad-hoc window** (it refuses ranges crossing a known boundary). Parsers: `scripts/decode_map.py`, `scripts/decode_save.py --sections --anchors`.
`FUN_00597a70` is the save/scenario block loader (NOT the map loader — the grid is read raw by `FUN_00582260`);
the .SAV chain's two read paths (kernel in-place vs ring-3 scratch): `references/ptrace-level-probes.md`.

## Format core (.cvr) — FULL SPEC: `references/cvr-format.md`
TLV chunks `u32 LE tag + u32 LE size incl. header`, outer `0x00525643` "CVR\0", palette group 6914 B, material
12292 B; VOXEL blob header 42 B, voxels 3 B with the 5-bit dir delta (0x1A STOP; the STOP-coded last voxel is
real) and the 11-bit normal code; regions end with 5 zero pad bytes; the single- vs multi-header count quirk;
chunk parse addresses loader 0x614acb / top loop 0x6446e0 / per-object 0x644f80 — voxel semantics are
wiki + corpus verified, NOT exe-verified. Decoder `cvr_decode.py` validates 113/113.

## Multiplayer netcode — mapped, secondary: full notes `references/netcode.md`
Codename **"jackal"**; DirectPlay via `FUN_006309aa`, DP object `DAT_0099d020`; packet = 12-B header, builder
`FUN_00584010` → router `FUN_0052a260` → dispatcher **`FUN_0052bce0`**; diplomatic types 0x2440-0x244e; turn
sync LOCK 0x2210 / DONE TURN 0x8301. File-name traps (treaty/killfaction pseudocode mislabels, the
UPPER_CASE band 0x68b000-0x691600 = voice-clip tokens, NOT opcodes) — read it before touching any of that.
## Goal (Paul's priority)

Play SMAC **single-player with working AI** on modern hardware **and recreate
the full menus + game UI** (reimplementation target). Multiplayer netcode is
mapped but secondary. UI groundwork: CPane/CWidget pane builders (e.g.
`FUN_00444140`, `FUN_0047c0e0`), PCX v3 art (`programs/*.pcx`/`.flc`), `.sc`
scenario files, voice/sound clip token strings 0x68b000–0x691600, UI widget-name
strings (TOUR1*, SOCTOUR*, DRONETOUR*).


## UI / asset pipeline — full notes: `references/ui-assets.md`
- **Script.txt IS the UI**: `programs/Script.txt` declares 1,357 dialog panes (`parse_script.py` ->
  `script_parsed.json`); grammar + menu-tree verification in the reference; spec `UI_MAP.md`.
- **alpha.txt is the rules file the exe loads** — 45 `#SECTION`s / 650 records: parse it
  (`scripts/parse_alpha.py` -> `data/alpha.json`, `ALPHA_RULES.md`) rather than RE-ing balance constants;
  field names recover from trailing `;` comments for only 4/45 sections, so bare sections' semantics come from
  the exe's parser, not guesswork.
- **PCX** SMAC variant (`0A 05 01 08`) decodes with Pillow 12; **FLIC** format is cracked (128-B header, frame
  chain 0xF1FA, the exe's loader FUN_0062ad73 / dispatch FUN_0062bdeb, decoder scripts) — full byte-level
  detail, the glsmac comparison and the still-open type-7 RLE pinning live in `references/ui-assets.md`.

## Running under Wine — hot rules (the FULL retired set, verbatim: `references/wine-pitfalls.md`;
driving/dialog state machines: `references/wine-operations.md`)
- **Preflight FIRST, one command:** `python3 scripts/smac_preflight.py` (read-only, exit 1 on FAIL) checks the
  address table, `terran.exe` alive with `TracerPid: 0`, no stray gdb, OUR bases by name with
  index/coords/pending/head/minerals/income + unit decode, /tmp room, evidence budget. `SMAC_PID=` overrides
  pgrep. Window id 10485761 (800x600); `xwd` needs **`-display :99`**. `session_brief.py`/`accept_ready.py`
  printing `BLOCKED: terran.exe not running` means relaunch; it reads the LIVE box so it runs MINUTES —
  request `timeout 400` and read a timeout as slow, not hung.
- Focus on :99: getactivewindow ALWAYS fails (no WM - red herring); check getwindowfocus getwindowname == the game title; windowfocus 10485761 works WITHOUT a WM; swallowed turn-end input with focus fine = a fresh save load (m54a_load --relaunch). Full text: `references/wine-operations.md` §s290 retirement.
- `scripts/m44_idle.py` asserts `TracerPid == 0` and its `--rounds 1` condition counts the CURRENT turn —
  exits rc=0 in 0 s doing nothing; use `scripts/m55_boundary.py` as the boundary driver. Any acceptance that
  needs a boundary must gate on a live year/round DELTA read from /proc/pid/mem first, or it "proves" its
  sites unreachable from a box that could not run them.
- **Vision-tool coordinates are SCALE-SHIFTED on 800x600 frames; click targets come from OCR word bboxes or
  pixel scans** (s137: vision's y~471 hit the recenter box, not the bar at y 405-427).
- The quit dialog is the killer: Escape = "Oops, no, wait!"; NEVER click OK (the next OK exits and the process vanishes silently); its banner IS the game title, so it reads as the title screen. Full text: `references/wine-operations.md` §s290 retirement.
- scripts/smac_play.py: no --mode stop; ordering is ON in the loop (an order counts as the unit+17 memory DELTA, never a screenshot); --no-escape N above --timeout; long runs in tracked background, never &-chains; kill stray pids by PID, never by name. Full text: `references/wine-headless-harness.md` §s290 retirement.
- A PROPOSAL vote pane stalls the AI phase: the YEA/NAY numbers are the TALLY, not key hints; click the true-window bars (coords + cadence VERBATIM in `references/wine-operations.md` §s290 retirement), windowfocus first, OK >= 1.2 s after selecting.
- **A round advancing while you watch is AUTO-END, not progress; a walk frozen on an AI faction is a MODAL
  dialog, not a livelock.** With all units HELD the engine closes our turn in 1-2 s; `cur_player == ours` is a
  window, not a state (heartbeat model: `references/solo-round-boundary.md`).
- Auto-end does NOT fire while any unit is actionable - and a unit built at the boundary IS: HOLD every record (+17=2, poked at TracerPid 0, read back) before a multi-boundary watch; ONE `h` closes the turn (orders mode 0x91b5b8 must be 1); the end-turn confirm takes clicks, not Return. Cadence/coords/queue rules: `references/production-queue.md`; full text: `references/wine-operations.md` §s290 retirement.
- **A stalled round can be a LIVELOCK:** `python3 scripts/m53q_livelock.py` (census of `unit+48`/`unit+50`
  chains, `--fix` repairs). Signature: `turn_flags` bit 1 + hot main thread + byte-identical screenshots.
- A turn that never advances can be a CLASSIFIER miss with no modal visible: OCR is unreliable both ways - the clean-HUD oracle is MEMORY (cur_player == player, turn_flags & 2 clear, no bar at y 145-200); accept_ready re-freezes and believes the BAR twice; peek one frame before any Escape-on-unknown loop. Full text: `references/screen-read.md` §s290 retirement.
- Label printed registers from the ENCODING; entry args come from `$esp`, not `$ebp`; a callee-saved reg holding arg 1 is a PARAMETER; print raw AND derived forms. Full text: `references/wine-pitfalls.md` §s290 retirement.
- Watchpoints: 4 hw slots, fire on VALUE CHANGE (break on STORE sites for same-value rewrites), never watch a display-read field, condition on the store's OWN encoding, pokes in Python not command lists, no `si` in commands. Full rules VERBATIM: `references/wine-pitfalls.md` §s290 retirement + `references/static-store-census.md` §9.
- The gdb command-list killer class (printf errors, memory writes, unguarded ARMED-time derefs, non-literal dumps - each aborts the sourced script at the FIRST hit and detaches, reading as a clean zero-event run): VERBATIM in `references/gdb-command-list.md` §s290 retirement. Command lists stay print-only.
- Never build the gdb command list with Python %-format (the template's %d/%x get eaten, silently rewriting breakpoints): bake literals or str.replace a unique token, diff the emitted scratch/<tag>.gdb before attaching, use stdbuf -o0, drain the pipe, drive + snapshot in ONE backgrounded job. Full text: `references/gdb-command-list.md` (§s290 retirement).
- A zero-event log is an INSTRUMENT verdict until proven otherwise: arm a control breakpoint whose hit is guaranteed, read back the watched event's preconditions BEFORE attaching, and echo the readiness FIX in the harness output ("gate unmet" != "mechanism refuted"). Full text: `references/instrument-laws.md` §s290 retirement.
- A hardware watchpoint cannot see a KERNEL write (copy_to_user lands bytes with zero events): change LAYER - strace `-e raw=` + soft-dirty/pagemap + maps; strace and gdb cannot both ptrace one task. Recipes: `references/ptrace-level-probes.md` (§s290 retirement).
- "No branch targets this call" != "the call is unconditional": walk the CFG with the call as a WALL and count reachable `ret`s; preds==0 alone is the vacuous-gate class. Full text: `references/instrument-laws.md` §s290 retirement.
- A rival that fails by crashing or producing nothing is NOT evidence until the crash is message-matched against the DECLARED law AND the same construction succeeds with the cause removed; retire degenerate rivals and GATE the retirement. Full text + B24's two degenerates: `references/verify-outcome.md` §s290 retirement.
- A WEAKENING is not a mutation (a dropped conjunct can only pass); mutate DATA so only the digest catches it; an over-broad mutant reads as a NO-OP - re-measure the declared set after EVERY review round. Full text: `references/instrument-laws.md` §s290 retirement.
- **Prove each gate is LOAD-BEARING by mutating the claim.** Ship `scripts/<id>_mutate.py`: re-introduce the defect
  the assertion exists to catch (a wrong immediate, a dropped term, a swapped operand, a filter deleted) and require
  that ONE specific check go red — then print N/N mutations reddened. A check that stays green under its own
  mutation is decorative, and prose that survives review can still be decoration: three sub-conditions written
  specifically to answer a reviewer were themselves unloadbearing, and only the mutation harness found it. This is
  the cheap cure for the project's dominant defect (an assertion that can pass on an unmeasured state). Write the
  harness BEFORE the closing docs — the closing order's first steps (rewrite `SESSION_CURSOR.md`, append the notes
  line) outrank further evidence when the budget runs low, because the next fire reads the cursor, not this branch.
  **A gate whose prose names a multi-instruction predicate needs a mutation that corrupts the ENGINE'S PARSED
  INSTRUCTION** (`M._INS[addr] = (...)` injected just before the gate's comparison), not one that edits a literal
  the assertion happens to read: a mutant flipping `jne`→`jle` passes untouched when the gate only compares branch
  TARGET strings, and it reports as rc=0/passing rather than as a red gate. Ship the harness with a
  baseline-green precondition (run the unmutated instrument first and refuse to score anything unless it exits 0)
  and reject any mutant whose output carries a traceback — rc==1 is also what an uncaught exception returns, and
  RED lines print before the death, so a crashing mutant otherwise credits itself. **The harness is state: re-run it
  after every edit that adds or rewrites a gate (anchors die and mutants go WEAK when constants move), and an
  unexplained WEAK blocks submission — commit WIP with the honest score rather than deleting a mutant.** Four
  outcomes must be classified, and a mutant reddening NOTHING is a NO-OP that fails the harness; the only legal
  CRASH is a DECLARED one matched on message text. Full mechanics:
  `references/instrument-laws.md` (mutation-harness scoring, §A mutation harness is STATE, §A mutation harness
  must CLASSIFY its four outcomes) and
  §Static text-cache parse traps.
- A mutation harness needs its OWN `--selftest`: one shared `verdict()`, then perturb only the DECLARED set (empty / superset / gate-declared NO-OP) and require rejection; code mutants need the instrument's printed `k/n patches applied` as contact proof (M319 4/4, `references/instrument-laws.md` §four outcomes).
- Decoration classes #294/#299 (inline-comment swallow, target fullmatch + case, multi-table vptr runs; mnemonic/operand split, de-duplicated owners, labels-only digests): VERBATIM in `references/instrument-laws.md` §s290 retirement. A gate that passes on an UNMEASURED state is the project's dominant defect.
- Answer "what is this field" by a STRUCTURAL partition (store/read/cmp census + def-walk + exact-complement classes), not by counting writers; carry the rival it kills. Full text + the measured 5..17 B pair-reach correction: `references/instrument-laws.md` §s290 retirement.
- **Concurrent fires can takeover mid-flight (s285):** isolation is verified at fire START, but a fixer fire can
  finish, post the review reply, merge the PR and merge its close-out while a verifier fire is still re-running
  acceptance. Detect via new commits appearing under a read file / clean status with foreign commits, and note a
  completion notice can arrive while the worker's FINAL sweep still writes: temp modules appearing/renaming/
  vanishing between two `git status` reads (or a harness line printed half-way) is churn from a live worker —
  re-read the branch state only after the process is gone (`pgrep`); never fight
  it - re-apply YOUR delta on a fresh branch off origin/main (content re-application, not cherry-pick, when the
  base history diverged) and keep the blind re-runs as INDEPENDENT VERIFICATION with committed records
  (`evidence/sN_reverify_*.txt` cited by path:line - prose claims of reruns without saved records are findings).
- **A review poll that prints only comment COUNTS is not a poll (s285, #303):** a docs PR merged on `comments=2`
  without reading the bodies = two untriaged P2s merged (missing evidence citations; a recorded 601 B vs actual
  594 B size claim). Before ANY merge - docs PRs included - print the comment BODIES (or explicitly record zero)
  and triage each; also re-`fetch`+status immediately before each doc write, not only at fire start.
- **When a gate's fact feeds several gates, the mutation harness must declare a SET of expected reds, not one.**
  Changing the refresh pair's callee, or tightening its 16-byte reach, reddens A3+A4+A9 at once - the memo set
  feeds all three. Demanding exactly-one red pushed me to retarget two mutants into WEAKENINGS (`==` -> `>=`),
  which then stayed GREEN: a weakening is not a mutation test, a mutation must be FALSE on the real bytes.
  Require `set(fails) == declared_set`: extra reds = an undeclared dependency, missing reds = decoration.
- **To close a number a PREVIOUS milestone cited, read that instrument's source for its DEFINITION before
  re-deriving one.** M311 wrote "only 3 of 22 stores fall inside an index-store window"; my first draft asserted
  its window was unspecified and that my +-32 B reading "coincidentally" matched - `m311_recidx.py:449` shows
  `0 <= a - b <= 32`, a FORWARD window, same 3 sites. Recomputing the closure on MY window gave arithmetic that
  the print contradicted (claimed 9 memo sites outside, measured 7). Quote the window with its reach in the claim.
- Decoration classes #301 (operand-text provenance, name-resolved spans going unbounded, subset window pins): VERBATIM in `references/instrument-laws.md` §s290 retirement. Classify by MOVING INSTRUCTION + SOURCE; bound def-walks explicitly; pin the COMPLETE ordered sequence.
- **Give the mutation harness a second family that edits the CODE.** Every expectation mutant rewrites a literal
  in the instrument, so an instrument that never really looks at the bytes passes them all. Add env-driven
  disassembly patches (`M315_PATCH="addr|mn ops;..."` applied to the parsed cache before measurement) and a few
  mutants that corrupt real instructions - a load turned into arithmetic, a guard cmp against an unrelated
  register, the second callee of a call pair deleted, a fold coefficient changed. Declare each one's gate SET
  (they legitimately span gates), and reject vacuous ones: if the patch target does not exist, that is a green
  lie. The census instrument prints `patches applied: n/m` for exactly this check.
- A leg census gates on PREDICTIONS computed from live memory, not on hits; tie every hit to a boundary; resolve the site's containment + caller count before blaming a breakpoint for a zero. Full text: `references/instrument-laws.md` §s290 retirement.
- To name a field's writer: hw watchpoint on the address PLUS a control watchpoint on a known-changing address; classify each store by how its SOURCE register was computed (register-level bit RMW vs whole-value assignment). Full text: `references/static-store-census.md` §s290 retirement.
- A gdb census >90 s goes through tracked background + wait loops (foreground caps at 420 s; killing mid-run hangs Wine - recover via m54a_load --relaunch); pair store-readback probes by EVENT ORDER; detach only after the window is really over; check TracerPid and kill stale gdb BY PID. Full text: `references/wine-operations.md` §s290 retirement.
- Vtable targets: check for a live INSTANCE first - scan writable /proc regions for the class's vptr; a class with no live instance logs zero hits at every method, whatever the window. Recipes: `references/code-atlas.md` (§s290 retirement).
- The readiness oracle's printed FIX can stay unsatisfied: `credit` (base+0xd0) is RECOMPUTED EVERY ROUND by FUN_004e93f0 and holds 0 when upkeep exceeds income - the reload chain will not clear it; it blocks only the PAY-SITE family (use the per-boundary storage poke). Full text: `references/production-queue.md` (§s290 retirement).
- A clean reload does NOT carry records created live in a previous session: re-census watched slots from /proc in the SAME invocation that arms the harness (armed == len(designed), not a floor); check the save can HOST the experiment before reloading; clear a stray modal itself - reloading costs the state AND the experiment. Full text: `references/wine-operations.md` §s290 retirement.
**Read `references/static-store-census.md` §9 before hand-writing a watcher script** — condition arithmetic,
log format and scorer gates are solved there (uppercase-`PTR` greps, pointer-form stores, operand width);
§1–§3 carry the traps that make the STATIC half complete. `references/instrument-laws.md` carries the header
order, the containment recipe, the DictReader trap, the watchpoint laws, the value-census laws, the
printf-escape law, the event-grouping law and the bit-leg census / per-site argument-tuple parse rules.
Depth: `references/wine-operations.md`, `references/wine-headless-harness.md` (turn automation, OCR/dialog
state machine), `references/wine-runnability.md` (what runs at all).

## Still open (leads) — `references/open-leads.md`; `NEXT_PROMPT.md` wins if they disagree
- **Dialog-family +0x4c dispatch CLOSED (M284-M288, s228-s233): do not re-open.** The slot (FUN_005f6aa3, the
  row-click dispatcher: FUN_005e7917 finder over 0x18-stride rows + [ecx+0xa8] dispatch) is reachable ONLY
  through a live family +0x4c dispatch and NO reachable path takes it — four live click paths + create-time +
  Return/WM_CHAR/WM_SYSKEYDOWN closure. Full registry blocks with every address: `NAMED.md` ## M284-M288; the
  in-game MENU drive recipe (the GAME row never OCRs; an open console bar INVERTS the MENU click; Escape on the
  bare HUD after the menu raises REALLYQUIT — safe 'oops' row, M37) is there too.
- **Band-flag gate CLOSED, do not re-open:** bit 0x40 of the per-faction flag word is tested but has no setter
  and no save carries it — `scripts/m118_flag_never_set.py` re-proves it offline.
