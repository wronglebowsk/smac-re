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
`session-discipline.md` (budget, closing order, handoff, shadow-running the cron loop, and the full
s242-retired discipline/evidence text). `grep -n '^## \|^### ' SKILL.md` and the references, then
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
**Triage every Greptile finding; a re-push does NOT buy another review** (one review per PR, on OPEN). Read the
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
  `NEXT_PROMPT.md` -> submit/PR. Never leave the commit until after the handoff docs.
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

### Verify the OUTCOME, not the mechanism — full text: `references/verify-outcome.md`
- A gate that counts the harness's own work passes a run that LOST the game. Compute candidate predictions from
  the baseline first; refuse a shape where your model and the null agree on every candidate; read the effect
  back from memory/state.
- **Every number the prose quotes must be COMPUTED by the gate that ships with it**, derived from the SAME
  parser that produces the claim after any parser fix (a caps-blind grep counted 28 where the parser counted
  33; a draft's "12 scratch tests" became 17). Put the number in the assertion FIRST (print the table,
  `assert len(...) == N`), write the sentence from the printed table, never from draft prose.
- **Never assert an exact sorted list or exact count over a whole-function window**: a duplicate of the same
  idiom further down satisfies any set check and breaks equality; assert on the first N or between two known
  addresses, and PRINT the table. **A "makes no calls / has no writer / never fires" claim needs the WHOLE
  function body** — a `POS[a]:POS[b]` slice asserted "zero calls" for a function making ten.
- One instrument is a LEAD, never a finding: pair it with one that can fail DIFFERENTLY (a byte sum vs a
  poke-and-scan); assert the state the run leaves behind (`TracerPid`, counts, armed count), not the exit
  code; pre-register the falsifier.
- **Exit codes are claims — encode the four states and PRINT which applies**: 0 = measured (taken or not);
  4 = the site was never reached (inconclusive, not a gate result); 5 = driver wedged / no orders
  (NO MEASUREMENT — never file it as evidence the gate is inert); 8 = box left dirty (`TracerPid != 0`).
  A wedge and a negative result are different facts; conflating them is the stale-gdb-success failure class.
- **A script that prints NOTHING and dies on `-15` is a HANG, not a missing instrument.** The signature is a
  0-byte evidence file plus an empty stdout capture: `timeout N` sends SIGTERM and block-buffered `print`
  dies with it, so the run reads as "crashed with no output". Run `python3 -u` with stderr teed to a file,
  and look first for an unadvanced loop cursor — `while x < W:` with no `x += stride` is the real case, and
  the loop then appends until the box runs out of RAM. The same shape hides a one-group-off regex
  (`JCC_RX` captures the MNEMONIC as group 1 and the TARGET as group 2; assuming group 1 yields a
  `ValueError: invalid literal for int()` that only fires at the first backward jump).
- **Re-verify a delegated script by capturing stdout to a TEMP file, never `diff <(python3 scripts/<id>.py) evidence/<id>.txt`.**
  The script writes its own evidence file, so the process substitution truncates the target before `diff` reads
  it: a perfectly good run reports as `1,92d0` (the ENTIRE output "missing") and reads exactly like an empty
  evidence file. The only valid form is `python3 -u scripts/<id>.py > /tmp/x.out && diff /tmp/x.out
  evidence/<id>.txt`; run it twice and require 0 lines both times (before and after review fixes).

### Evidence lifecycle — the rules live in `docs/EVIDENCE.md`
`python3 scripts/evidence.py budget` — `evidence/` warns at 20 MB, FAILs the gate at 30 MB. Text is never
pruned; an IMAGE stays hot only while the HOT WINDOW cites it — the newest 8 `## Session` sections of
`SESSION_NOTES.md` plus the live footing files (`NEXT_PROMPT.md`, `AGENTS.md`, `SESSION_CURSOR.md`) — or it is
younger than `--keep-days`; lookup/history docs (NAMED.md, pick-archive, named archives, docs/sessions/,
skill references) explain old findings but do NOT hold an image hot: its bytes stay in git and
`evidence.py log` gives the commit. Test-fixture images (named by `scripts/test_*.py`/`scripts/check_classes.py`/`sim/`) live in
`evidence/fixtures/`, which `budget` does not count and `prune` never touches. `prune --apply` moves the rest
to git-only, recorded path/sha256/bytes/commit in `.prune_log.jsonl`.
- **A memory sampler is the fastest way to blow the evidence budget, and pruning cannot save it.** A
  `/proc/<pid>/mem` poll loop with no sleep runs tens of thousands of samples/s — a 150 s run wrote a
  **1.4 GB** trace and turned the gate RED *after* the milestone work was already done. Sleep the loop (2 ms
  is the sampling cadence the footing asks for anyway), and downsample before the first commit: keep the first
  sample, every sample where a watched field CHANGES, one heartbeat per second, and the last — 1.29M samples
  collapse to 68 lines / ~10 KB with the boundary sequence intact. A giant blob also stays in the branch's
  HISTORY once committed, so a later delete does not un-poison a push (see `references/git-workflow.md`).
- The full-disassembly cache `evidence/m53j_text.txt.gz` (~5.7 MB, what the zgrep method runs on) is PRUNED
  from the worktree when the gate nears 30 MB; it is git-kept — recover with
  `git show 733322c6:evidence/m53j_text.txt.gz > evidence/m53j_text.txt.gz` (repo root) before zgrep.
- **Delegated decodes: a child's claims are TESTIMONY, not evidence.** A child can map a 1450-line function in
  minutes; re-read from the cached disassembly: (1) every store site it cites, with its immediate; (2) the
  address arithmetic that lets the value REACH the field — a store guarded to an index past the array is dead
  code, so check the guard before believing the value exists; (3) the function boundary (`zgrep` the `ret`)
  before accepting any "written in the caller, not the callee" attribution, where decodes drift. Write the
  audit to `evidence/<id>_verify.md`; label instruction-stream facts VERIFIED and branch semantics INFERRED.

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
read-wrapper caller trace and the zeros-fraction pitfall are all there. **The last 156 B of every save is a
fixed TRAILER, not game data** — the final 152 B are identical across nine saves, only the trailing dword
varies and its offset moves with file size, so no hard-coded leg can index it; its reader is the 6-site
per-entity loop restoring rows into heap records (stride `0x224B8`), proved by POKING markers, never by a byte
sum. **Any file-vs-memory diff goes through `scripts/save_diff.py`, never an ad-hoc window**: the mapping
constant `k = dest - off` is PER REGION, so a window straddling a section boundary manufactures hundreds of
fake "diffs"; the script refuses a range crossing a known boundary and names it (`scripts/test_save_diff.py`
PASS 7/7 is the guard). Parsers: `scripts/decode_map.py`, `scripts/decode_save.py --sections --anchors`.
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
- **Focus:** `xdotool getactivewindow` ALWAYS fails on :99 (no WM; red herring — s136 lost a session on it).
  The check is `xdotool getwindowfocus getwindowname` == the game title; `xdotool windowfocus 10485761` works
  WITHOUT a WM. Proof keys land: one Escape on an open base pane flips classify base->hud. If the box swallows
  turn-end input with focus fine (s135: Return AND a click on TURN COMPLETE did nothing), the repair is a
  fresh save load (`m54a_load.py --relaunch`).
- `scripts/m44_idle.py` asserts `TracerPid == 0` and its `--rounds 1` condition counts the CURRENT turn —
  exits rc=0 in 0 s doing nothing; use `scripts/m55_boundary.py` as the boundary driver. Any acceptance that
  needs a boundary must gate on a live year/round DELTA read from /proc/pid/mem first, or it "proves" its
  sites unreachable from a box that could not run them.
- **Vision-tool coordinates are SCALE-SHIFTED on 800x600 frames; click targets come from OCR word bboxes or
  pixel scans** (s137: vision's y~471 hit the recenter box, not the bar at y 405-427).
- **"Do you really want to quit?" is the killer dialog:** Escape = "Oops, no, wait!"; never click OK (the
  next OK exits and the process vanishes silently); its banner IS the game title, so it reads as the title
  screen — and the driver's own Escape press can pop it mid-drive.
- `scripts/smac_play.py`: no `--mode stop`; ordering is ON in the loop (each turn pokes the selection slot,
  fires one hotkey, services the pane, verifies `unit+17` moved into the byte set that key produces — an
  order counts as that memory DELTA, never a screenshot). `--no-escape N` = press no Escape for N seconds: set
  N above `--timeout`. Launch long runs in tracked background mode, **never `nohup … &` nor ANY `&`-backgrounded
  chain in a foreground call**; find stray pids with `pgrep -f smac_play.py` then `kill <pid>` — never signal
  by name (pkill -f matches your own argv).
- **A PROPOSAL vote pane stalls the AI phase.** `YEA: 2  NAY: 3` is the TALLY, not a key hint. True-window bars:
  YEA (310,495) / NAY (398,495) / ABSTAIN (485,495) / OK (393,495); `windowfocus` first, OK >= 1.2 s after
  selecting; capture `xwd -display :99 -root -silent` + 2x upscale + tesseract, region-constrained.
- **A round advancing while you watch is AUTO-END, not progress; a walk frozen on an AI faction is a MODAL
  dialog, not a livelock.** With all units HELD the engine closes our turn in 1-2 s; `cur_player == ours` is a
  window, not a state (heartbeat model: `references/solo-round-boundary.md`).
- **Auto-end does NOT fire while any unit is actionable — and a unit built at the boundary is.** HOLD every
  record (`+17` = 2, poked at TracerPid 0, read back) BEFORE arming a multi-boundary watch. The produced unit
  parks the cursor at order 0 and Return for 150 s changes nothing: ONE `h` closes the turn — and `h` needs
  orders mode `0x91b5b8` = 1 (at 0 every order key is a silent no-op that looks exactly like a wedge). A popup
  whose default row is not OK does not close on Return (Return CYCLES options) — click OK. The end-turn confirm
  ("SOME OF OUR UNITS HAVE NOT YET MOVED…") takes NO Return: click YES then the OK ~26 px below, 1.2 s apart
  (`smac_play.answer_confirm`). When the year stops: take ONE frame and `classify` it (returns `confirm`)
  before pressing anything else. Cadence/coords/queue rules: `references/production-queue.md` — including why
  an arrival round predicted from ROUND-START fields is not exact (the visit recomputes `+0xd0`).
- **A stalled round can be a LIVELOCK:** `python3 scripts/m53q_livelock.py` (census of `unit+48`/`unit+50`
  chains, `--fix` repairs). Signature: `turn_flags` bit 1 + hot main thread + byte-identical screenshots.
- **A turn that never advances can be a CLASSIFIER miss with no modal visible.** OCR is unreliable both ways:
  a clean HUD reads `unknown` when the TURN COMPLETE row garbles (measured: `complete` in the button row 3/8
  passes while the bottom status bar read 8/8) — which is why `accept_ready.py` re-freezes up to 4 times and
  believes the BAR twice (`smac_play.hud_status_bar`, `test_hud_bar.py`); with the production line drawn in the
  message box even the chrome goes illegible, so the clean-HUD oracle is MEMORY: `cur_player == player`,
  `turn_flags & 2` clear, no bar at y 145-200. An advisor dialog reads `hud` when too few words land in the
  dialog band (caption tell: a word of 6+ chars or two of 4+ at y 90-118 = something drawn OVER the HUD). Peek
  one frame before any Escape-on-`unknown` clearing loop (a garbled-but-clean HUD raises the quit prompt).
- **Label a printed register from the ENCODING; entry args come from `$esp`, not `$ebp`** (a bp at the first
  instruction sits before the prologue, so `$ebp` is the CALLER's frame: args at `*(int *)($esp+4)`, caller at
  `*(int *)$esp` — the return-address field is the cheapest caller census). Check the prologue for
  `mov reg,[ebp+8]`-style loads + reassignments: a callee-saved register holding arg 1 for the whole body is a
  PARAMETER, not a cursor. Print raw AND derived forms (`$ebx`, `$ebx/52`, `$ebx%52`) so a mislabel is visible
  in the log. (Full text: `references/wine-pitfalls.md`.)
- **Watchpoints:** x86 gives 4 hw slots (an 8-byte window needs 8-alignment = 2 slots); they fire on VALUE
  CHANGE, so a same-value rewrite is invisible — count stores with silent bps AT the store and keep the
  watchpoint as the "any other writer" check. **Never watch a field the display reads constantly**
  (`base+0x40`): the inferior crawls — break on the STORE sites instead and condition each on the address the
  store's OWN encoding computes (`[reg*4+disp]` holds `(index*stride)/4`, `[reg+disp]` the byte address —
  comparing the register against the bare index never fires; §9.3 of `static-store-census.md`). Side-values at
  a store site are not evidence. **A bp on a LOAD prints the register's PREVIOUS value; a bp on a skipped loop
  body never fires (a zero there is the gate); round-mutated values cannot come from a round-start snapshot.**
  **Do not `si` for the after value** — `si` inside a commands list makes `gdb -batch` stop and DETACH after one
  hit; for `mov [reg+disp],src` the source operand IS the value, and the sleeping /proc sampler proves it. A
  hw watch reports `$pc` PAST the writing instruction — disassemble BACKWARDS from a hit. When the governing
  field is a UI cursor/selection, POKE it and prove the write lands (and refuse the shape when the poked value
  and the rival prediction agree).
- **The gdb command-list killer class (all of it aborts the sourced script at the FIRST hit and detaches — the
  log reads as a clean zero-event run while the turn driver exits 0):** a printf ERROR in a commands block (so:
  no inferior strings — `%.20s` of an inferior pointer errors; expressions go in printf ARGUMENTS, specs must
  match; a format-pasted expression prints ITSELF and the stream parses as zero events); a MEMORY WRITE in a
  commands list (`set {int}ADDR = 1` is "not an lvalue") — **put pokes in Python: `os.pwrite(fd, ...)` on
  `/proc/<pid>/mem` succeeds while gdb is attached** — keep command lists print-only; an UNGUARDED ARMED-time
  deref (`ds:0x8f0d60` reads 0 until a pane opens — `if $reg != 0 … end` or print the register alone; a /proc
  reader must return -1 on OSError, EIO not 0); a `dump binary memory` with a non-literal target, arithmetic
  range, or `python … end` block — bake literal paths + literal addresses, remember gdb convenience-variable
  arithmetic is 32-bit SIGNED (compute lengths in Python), one dump per run with an `off=` field, and
  **`append binary memory` is what makes a per-hit series work** (full rules: `references/gdb-command-list.md`).
- **Never build the gdb command list with Python `%`-format** — the template is full of `%d`/`%x` and Python
  eats the first ones, silently rewriting the breakpoints. Bake literals or `str.replace()` a unique token, and
  diff the emitted `scratch/<tag>.gdb` before attaching. Use `stdbuf -o0`, drain gdb's pipe, drive + snapshot in
  ONE backgrounded job (`scripts/m53n_drive.py` is the template).
- **A zero-event log is an INSTRUMENT verdict until proven otherwise:** arm one control breakpoint whose hit is
  guaranteed in the window and require its rows; read back BEFORE attaching that the watched event can even
  happen (queue head is the armed id, `pending >= 1`, storage above the gate's demand) — an unusable window is
  not a negative result. **A whole subsystem path can be gated on another subsystem's state** (empty queues ⇒
  research upkeep never runs); satisfy the printed readiness FIX and echo the precondition in the harness's own
  output so "gate unmet" reads different from "mechanism refuted".
- **A hardware watchpoint cannot see a KERNEL write** (user DR breaks carry the exclude-kernel bit; bytes
  landing via `copy_to_user` inside a `read()` change with zero events — that is what a "silent census" means
  when a file read's destination IS the watched region). The fix is a different LAYER: strace `-e raw=` (prints
  the read's BUFFER POINTER) + `clear_refs=4`/pagemap soft-dirty + maps before/after; strace and gdb cannot both
  ptrace one task — `references/ptrace-level-probes.md`.
- **A "no branch targets this call" result is NOT "the call is unconditional".** `preds == 0` at a call site proves
  only that no branch lands on it; whether it RUNS on every invocation is a separate measurement. Walk the CFG
  with the call as a WALL (refuse to expand it) and count the `ret`s still reachable: if any, early exits skip the
  call and a rival claiming "the only gate is the enclosing loop's `jl`" must FAIL. Closing a guard question on
  `preds == 0` alone is the vacuous-gate class and has now cost two review rounds (M305 A14, M306 RIVAL4).
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
  unexplained WEAK blocks submission — commit WIP with the honest score rather than deleting a mutant.** Full
  mechanics: `references/instrument-laws.md` (mutation-harness scoring, §A mutation harness is STATE) and
  §Static text-cache parse traps.
- **Three #294 (M313) decoration classes - all reviewer-found, all silent:** (1) an inline `#` comment placed
  after the FIRST term of a multi-line parenthesized boolean swallows the rest of that physical line - the
  push-opcode check vanished with zero trace; never trail-comment inside a condition, split into its own gate.
  (2) target parsing must be `re.fullmatch(r"0x[0-9a-f]+", t)` before `int(...,16)`: far-calls print as
  `call 0x43:0x955e0043` and a `startswith("0x")` filter CRASHES on them; and case-matter - comparing
  "0x5186B0" against the lowercase cache makes any zero-reference census decorative by construction.
  (3) a "vtable" found by walking .text-pointers to a stop may cross MULTIPLE class tables (the run from
  0x672290 contains the chooser FAMILY table, base 0x6728c0) - pin pointers BY ADDRESS, cite the ledger for
  each table's identity, and the word "slot" is banned unless a ledger entry or a constructor vptr-store
  establishes the table's base (search for `mov [reg],imm` of the base as an immediate in .text to find one).
- **Three more decoration classes, reviewer-found on #299:** (1) a disassembly cache that stores MNEMONIC and
  OPERAND in separate fields makes a regex like `^push 0x..$` applied to the operand match NOTHING, so
  `all(cond for ...)` passes over an empty set - match the bare operand (`^0x[0-9a-f]+$`) and print the size of
  the scanned census so an empty population is visible. (2) A count claim ("exactly N sites") that compares
  DE-DUPLICATED OWNERS stays green when an (N+1)-th site lands inside an already-listed owner - pin the site
  ADDRESSES. (3) A digest is evidence only if it hashes name+verdict+detail; hashing the check NAMES, or
  keying a `detail` dict by short ids while the digest loop iterates full check names, lets two different
  measurement sets share one digest - and only mutations can catch that, so mutate the numbers, not the labels.
- **Answer "WHAT IS THIS FIELD" by a STRUCTURAL partition, not by counting writers** (`m315_bb4_census.py`,
  pick (ii), `ds:0x68cbb4`). Census every store/read/cmp; def-walk each store's value source inside its own
  function; then classify stores by WHAT FOLLOWS the store (for a memo: a fixed two-call pair within 16 B) and
  assert the two classes are EXACT COMPLEMENTS of each other - "12 of 22 stores are followed by the pair, 10 are
  the -1 sentinel, and the 10 are exactly the sentinel-valued ones" is a claim that can be false, which "22 stores
  exist" is not. Carry the rival it kills and the number that kills it (a store fed from a NEIGHBOURING index
  would survive the pair law, so the def-walk census, not the pair law, refutes "second cursor").
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
- **Three decoration classes found by review on #301 (all reviewer-caught, all silent on real bytes):**
  (1) a PROVENANCE classifier that keys on OPERAND TEXT ALONE is decoration - `add r,ds:IDX` reads like a load
  of the index and `lea r,[ebp+0x8]` looks like a stack load; set the class from MOVING INSTRUCTION + SOURCE
  OPERAND, and prove it with a mutant that REWRITES the instruction, not the expected count. (2) A def-walk that
  bounds itself by a function span looked up by name silently becomes UNBOUNDED when that name resolves to
  nothing (`(0,0)` spans) - bound by the measured span when claimed, by an explicit instruction cap when not,
  and pin how many stores needed the cap (a coverage number worth reporting in its own right). (3) A window pin
  that checks a LISTED SUBSET of addresses does not pin the window: a change to an instruction BETWEEN the
  listed ones (the record-address fold sat exactly there) survives. Pin the COMPLETE ordered sequence between
  the bounds, including its length, and make the bound inclusive of the last instruction.
- **Give the mutation harness a second family that edits the CODE.** Every expectation mutant rewrites a literal
  in the instrument, so an instrument that never really looks at the bytes passes them all. Add env-driven
  disassembly patches (`M315_PATCH="addr|mn ops;..."` applied to the parsed cache before measurement) and a few
  mutants that corrupt real instructions - a load turned into arithmetic, a guard cmp against an unrelated
  register, the second callee of a call pair deleted, a fold coefficient changed. Declare each one's gate SET
  (they legitimately span gates), and reject vacuous ones: if the patch target does not exist, that is a green
  lie. The census instrument prints `patches applied: n/m` for exactly this check.
- **A leg census gates on PREDICTIONS, not on hits:** compute each site's expected hit count from live memory
  first (gate globals, args off `$esp`, the table values the branch loads), print the predictions, gate on
  agreement with the counters (`m86_helper_legs.py`, `m87_aaa20_trigger.py`). Demanding a hit at a site the
  TAKEN leg cannot reach FAILs the milestone, not the game — fix the leg map, never the floor. Tie every hit to
  a boundary; a window count is not a cadence. **Before blaming a breakpoint for a zero, resolve the SITE's
  containment and its function's caller count** from `ghidra_out/index.csv` — one read splits "unreachable BY
  DESIGN" from "UNTAKEN BRANCH".
- **To name who writes a field: hw watchpoint on the address PLUS a control watchpoint on an address you know
  changes** — a mnemonic grep misses stores through pointer-form `lea`; and **classify each store by how its
  SOURCE register was computed** (scan back for `or`/`and`/`lea`): 23 of 27 memory-form stores to one field
  were the write half of a register-level bit RMW, so the field IS bit-set and only whole-value assignments can
  deliver an untouched bit — a store-shape census sees the operand, never the provenance.
- **A gdb census >90 s goes through tracked background + wait loops: the foreground caps at 420 s and killing a
  census mid-run leaves Wine hung** (round frozen after detach too — recover via `m54a_load --relaunch`). Pair
  store-readback probes by EVENT ORDER (RB follows ST) — a {addr: last-mem} dict mis-pairs an address rewritten
  later. **Detach only after the window is really over:** the turn driver returns rc=0 while other factions'
  upkeep still executes, so the last stores land after the detach and log NOTHING (`instrument-laws.md`). A
  census can also leave gdb ATTACHED after printing its verdict: check `TracerPid` and kill the stale gdb BY
  PID before calling the box clean.
- **Vtable targets: check for a live INSTANCE first** — scan writable `/proc/<pid>/mem` regions for the class's
  vptr; a class with no live instance logs zero hits at every method, whatever the window (recipes:
  `references/code-atlas.md`).
- **The readiness oracle's printed FIX can stay unsatisfied:** `credit` = `base+0xd0` is RECOMPUTED EVERY ROUND
  by FUN_004e93f0 (`[+0xc0]-[+0xf0]-[+0xe0]`; the "init-only" claim is RETRACTED) and holds 0 when upkeep
  exceeds income — the reload chain will not clear it. That line blocks only the PAY-SITE family (their gates
  need storage >= price: use the per-boundary storage poke); rebuild/upkeep censuses run green at credit 0.
- **A clean reload does NOT carry records created live in a previous session** — yesterday's census is fiction
  after a reload: re-census the watched slots from `/proc/pid/mem` in the SAME invocation that arms the harness,
  and assert armed == len(designed watch list), not a fixed floor (arming fewer watchpoints than the design
  silently drops half the slots). **Check the save can HOST the experiment before reloading for it:**
  `m54b_clean.SAV` loads at 2150 r50 (University Base only, credit 0); the chooser candidate array is
  ERA-DEPENDENT (after `m54g_prep` + one turn the INSERT lands even at minerals 0 / credit 0), and the FIRST
  enqueue right after a turn-end can transiently print `item 2 not in candidate array []` — retry once before
  blaming the save; reloading to clear a stray modal costs the later state AND the experiment — clear the modal
  itself; gate any reload on `accept_ready.py` READY plus a non-empty candidate array.
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
