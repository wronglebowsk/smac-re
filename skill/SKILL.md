---
name: smac-cvr-format
description: "Use for SMAC .cvr Caviar voxel decode/render or SMAC RE."
---

# SMAC .cvr = Caviar voxel models

Sid Meier's Alpha Centauri (1999) `terran.exe` + `programs/*.cvr` live in
`~/reverse/smac/` (durable). Full writeup: `~/reverse/smac/FINDINGS.md`.
**Versioned at `github.com/wronglebowsk/smac-re` (private)**; a copy of this skill is tracked
in-repo under `skill/` — after editing the skill, refresh it there and push. Game binaries,
`programs/`, `smac.iso`, `glsmac/` and regenerable Ghidra/FLIC output are gitignored: never
`git add -f` them.
Decoder + iso renderer: `~/reverse/smac/cvr_decode.py` (validates 113/113).

**This file is ~70 KB and the repo copy budget FAILs at 70,000 chars — grep it, do not load it whole,
and when you add a pitfall, delete a superseded session block in the same edit.** `grep -n '^## \|^- \*\*' SKILL.md`, then
`sed -n 'A,Bp'` the one or two sections you need (the pitfalls block + the code area for the current
milestone). Loading it whole costs ~14k tokens a session and buries the pitfall you came for.
Master plan / exit gates (G1–G4) / phase list: **`~/reverse/smac/ROADMAP.md`** — read it before picking
a milestone. Phase 0 = harness + state reader + full Ghidra export + coverage ledger; do it before more
RE. Five spines (boot, solo turn, unit orders/combat, research/tech, save/load) drive Phases 1–2.

```bash
cd ~/reverse/smac
python3 cvr_decode.py "programs/*.cvr" "programs/*.CVR"   # validate corpus
python3 cvr_decode.py --list Apsid.cvr                    # voxel/frame listing
python3 cvr_decode.py --render programs/Drop.cvr          # -> Drop.render.png in cwd
```

## Git workflow (2026-10-22)

Repo `github.com/wronglebowsk/smac-re` (private). One milestone per branch, landed as one PR:

```bash
python3 scripts/milestone.py brief     # state, open PRs (with CI verdict), queued options
python3 scripts/milestone.py start M51a
python3 scripts/gate.py --base origin/main   # must be GREEN
python3 scripts/milestone.py submit     # commit, push, open PR (refuses red gate)
python3 scripts/milestone.py merge <n>  # refuses anything but GREEN
```

**`submit` commits before it checks the branch.** Run it on `main` and it writes a
`main: checkpoint` commit into the tree, then refuses. Undo with `git reset --soft HEAD~1`, branch,
and commit with a real message; always `start <ID>` (or `git checkout -b`) first — but `start` refuses a
dirty tree and an existing branch, so a crashed session's milestone (its branch + untracked `evidence/`)
is resumed by checking it out and finishing that work, never by re-running `start`.

**Context discipline (262k tokens ≈ 1.05M chars).** Never read a whole `evidence/*.log`:
`python3 scripts/evidence.py show <file>:<line>` prints the cited window, `evidence.py digest
<file>` writes a ~2KB summary to `evidence/digests/`. `evidence.py budget` reports what each doc
costs in context (target: always-loaded ≤6%). `SESSION_NOTES.md` is rotated by
`scripts/session_rotate.py --apply` once it passes 110k chars; `evidence.py prune` removes
uncited screenshots (git keeps history, `.prune_log.jsonl` records them). Policy:
`~/reverse/smac/docs/EVIDENCE.md`.

**Budget gotcha that passes locally and goes RED in CI (M53d).** `evidence.py budget` FAILs
`NEXT_PROMPT.md` above **16,000** chars (warn 12,000; SKILL.md 70k, SESSION_NOTES 150k, NAMED 250k),
and the CI gate runs `scripts/test_loop.py`, whose case 4 appends **7 chars** to `NEXT_PROMPT.md` — a
prompt at 15,99x is GREEN locally, RED in CI. Keep `NEXT_PROMPT.md` at ≤ ~15,500 (working target; 16,000 is the FAIL) and run
`python3 scripts/test_loop.py` on the anchored branch (never detached HEAD) before `submit`.
`submit` also prunes `SESSION_NOTES.md` and adds a `<MILE>: checkpoint` commit; `merge <pr>` rebuilds
the semantic index.

**The gate has two more checks that silently cost a run.** (1) *Address registry*: a milestone that names
a function or pins an address must add `NAMED.md` rows in the same commit, otherwise the gate prints
`[WARN] address registry: NAMED.md untouched` — the verdict stays GREEN and merge still proceeds, so a
WARN is easy to shrug off; the milestone protocol wants 0 warnings, so treat every WARN as an artifact
missing from the same commit.
`NAMED.md` is append-only and too big to rewrite — write the rows to a scratch file and
`cat scratch.md >> NAMED.md` (`write_file` refuses to overwrite a file it has not fully read in the current task — for a whole-file
rewrite write the new text to a scratch path and `mv` it over the target, or do the rewrite in one python
pass; `patch` needs a unique anchor);
rows are `| addr | proposed name | conf | evidence-with-file:line |` and the row is what makes the
function searchable in the semantic index. (2) *Evidence citations*: every `evidence/<file>` cited in the
findings doc must exist on disk, or the citation check drops it (the regex covers only
`.log/.txt/.gdb/.json/.png/.csv`, so an `evidence/x.md:NN` cite is never checked and only your own care
keeps it pointing at the right line). (3) **Poll CI by SHA**: after a follow-up
push (skill sync, `NAMED.md` rows) `gh pr checks <n>` can still report the earlier run — use
`gh pr view <n> --json headRefOid,statusCheckRollup` and merge only when SUCCESS is on the current head
commit.

When a doc is over budget, **delete whole bullets/blocks** (cut from the offending line to the next
`- ` or `## `) — rewording saves ~0 bytes — and re-measure with `wc -c`, not character count. These docs
**wrap mid-clause**, so an `old_string` copied from a rendered view misses the line break and the edit
fails: do the trim in ONE python pass that either splices whole line ranges (process ranges in
DESCENDING order so earlier line numbers stay valid) or regex-matches with `\s*\n\s*` wherever a wrap can
sit, and assert each pattern matched exactly once (`subn(..., count=1)`, check `n == 1`) rather than
assuming it did.

**Semantic search** (`docs/SEARCH.md`): `python3 scripts/index.py search "<question>"`
returns `file:line` / addresses for notes and named functions; `merge` rebuilds it
(incremental ~1 s, cold ~35 s) and is fail-soft when the embedding endpoint on
192.168.1.213:8000 is down. A hit is a lead, never evidence.
Only **2,786 of 10,284** functions are indexed — those carrying a `NAMED.md` row, string refs,
data refs or ≥6 callees. Boilerplate bodies (`FUN_x calls FUN_x`) embed to near-identical vectors
and are excluded; `--all` adds them back and makes results worse. **Naming a function in
`NAMED.md` is what makes it findable** — the build folds the row into the chunk. Scores run
0.65–0.81 for anything, so read the rank, not the absolute number. Build/index design rules:
> skill `semantic-search-index`. Unnamed functions are labelled once by the local 125B
> (`scripts/summarize.py`, cache `index/summaries.jsonl`, ~1.7 h for 2,786, resumable); rerun
> only when bodies change.

A session that finds an open PR lands it instead of starting new work. Branch protection is
unavailable (GitHub Pro needed for private repos), so `merge` is the enforcement point — never
merge by hand in the web UI without a green `gate` check. After editing this live skill, copy it
to `~/reverse/smac/skill/` and commit: the gate fails on drift. Protocol detail:
`~/reverse/smac/AGENTS.md` and `docs/WORKFLOW.md`.

## Session discipline (this project is context-heavy)

Paul wants SMAC RE broken into **small pieces**: complete ONE milestone, write it to a
file, append one dated line to `~/reverse/smac/SESSION_NOTES.md`, then STOP — ending
after a single milestone is a success, not a shortfall.

Exception: when he says **"keep going until you finish <chapter>"**, that overrides the
stop-after-one rule. Work through that chapter's milestones, writing the doc + evidence
after each, and report once at the end — including what is still open. Do not relabel a
partial result as done to make the chapter look finished (see `MILESTONES.md` F2).

When a session turns heavy he asks for a **paste-ready resume prompt** for the next one.
Write it as a self-contained block, not a chat summary: first actions (skill_view + which
files to read), current footing (what is proven, do not re-derive), in-flight work with the
exact verify/rerun command, ONE-milestone options, the operational kit (launch command,
preflight, coordinates/OCR rules), and the report style. It must work for an agent that has
none of this conversation. Keep every tool result small:
grep the **`ghidra_out/` corpus** or the saved `*.pseudocode.txt` / `*.json` dumps in
`~/reverse/smac/` instead of re-dumping; page Ghidra facets in small slices; reuse saved
screenshots and take a new one only after a real state change.

## Code atlas — read this before opening Ghidra

Every function is already decompiled on disk: `ghidra_out/index.csv` (one row per
function: addr, name, size, insns, callers, callees, string refs) plus 42
`ghidra_out/shard_NNN.c` files, 250 functions each, bodies delimited by
`// ==== NAME @ 0xADDR size=N`. Use it instead of an import+decompile session.

```bash
cd ~/reverse/smac
python3 scripts/fn.py 0x51e700            # decompiled C for one function
python3 scripts/fn.py --grep 'turn'       # find functions by name
python3 scripts/fn.py 0x51e700 --max 60   # top of a big function
python3 scripts/coverage.py               # index.csv -> COVERAGE.md (hubs, monsters, read-next)
python3 scripts/parse_alpha.py            # programs/alpha.txt -> data/alpha.json + ALPHA_RULES.md
```

- If `scripts/fn.py` prints 0 bytes for an address `index.csv` lists as ok, don't retry arg
  variants — read the body from the cached objdump window (`zgrep -n '  ADDR:'
  evidence/*_text.txt.gz` + sed window) instead.
- **Filter compiler helpers before ranking anything by in-degree.** CRT stubs
  (`__security_check_cookie`, `_ftol2`, …) have 300–2000 callers and a few hundred bytes and
  top every raw caller ranking; `coverage.py` excludes `callers≥300 & size<400` and lists them
  separately. Ghidra's function count also runs ~2× the real body count because of `Unwind@…`
  pseudo-functions (most are <16 B).
- **Naming a function from the corpus:** read the shape first (params, globals touched, which
  fields it writes — `this+0x18`/`+0x1c` as sizes usually means layout/drawing), then follow
  ONE callee to classify the primitive (a callee that saves/restores a graphics global around a
  rect call makes the caller a drawing routine). Ported string literals are the fast path when
  they exist (`grep -oE '"[^"]{4,40}"'` on the body); many hub functions have none, so field
  offsets are the evidence. Record each name with the offsets that justify it in `NAMED.md` so a
  later session can falsify it in one command.
- **Clean 32-bit disassembly without attaching (M49a recipe)**: `gdb -batch -nx -q -ex "set
  architecture i386" -ex "set disassembly-flavor intel" -ex "file programs/terran.exe" -ex "x/Ni
  0xADDR"` — gdb maps the PE image (file offset = VA − 0x400000), read-only, TracerPid stays 0.
  **Whole-image store census: `objdump -d -M intel --section=.text programs/terran.exe`** — printed
  addresses are VAs (file offset = VA − 0x400000), ~40 MB and regenerable: grep it, extract the windows
  you cite into small `evidence/` files, never commit it. `evidence/` carries a hard **disk** budget that
  the gate enforces through `evidence.py budget` (warn 20 MB, FAIL 30 MB), and one 40 MB dump blows past
  it: delete it once the census is written up, or `gzip -9` it in place (~40 MB → ~6 MB, still searchable
  with `zgrep`) when a later milestone will re-census the same address range — and record the rebuild
  command in `NEXT_PROMPT.md` so the next session knows the file is regenerable, not data. A `-b binary -m i386:x86-64`
  slice MISALIGNS on SEH blocks (garbage/movabs in SEH-heavy regions like the 0x4efxxx pipeline) — for
  one function use the gdb recipe; Ghidra lumps edi/esi away.
    **Coverage-check every dump**: instructions average 3.8 B here, so `x/2600i` silently stopped 2.4 KB
    short of a 12,298-byte function and M53a drew a WRONG conclusion ("no +0x50 writer in the pipeline")
    from the truncated window — compute the count from `index.csv` size ÷ 3.8 and confirm the last address
    printed equals the next function's start.
### Store census, table reads and model rewrites — what misleads

- **Grep store SHAPES on the linear disassembly, not offsets**: literal `&DAT_… =`, indexed stores,
  `rep movs`, AND **negative pointer arithmetic off a register base**. For a `ds:`-global store census use the mnemonic-comma test but **exclude `cmp`/`test`** — they carry the same comma shape as stores and flood the hit list (the dest-bracket test likewise must exclude `cmp`/`test`/`lea`). A loader that walks a pointer
  initialised to `record + 50` writes its tail fields as `*(char *)(p + -4)` / `(int)p + -9`; Ghidra
  renders them exactly that way, so neither a `DAT_` grep nor a disp32 byte-scan surfaces them. Scan for
  disp8 stores whose base register is a table/record pointer.
- **Never cite a field offset out of pseudocode without checking the pointer's element type.** Ghidra
  types many globals as `short *` (here: the current-base pointer `DAT_008f0d60` and every copy of it),
  and pointer arithmetic scales by element size — `p + 0x20` is byte **+0x40**, `p[0x1c]` is +0x38,
  `idx * 0x98` is the 0x130 stride. The machine-code twin is a loop cursor that starts INSIDE the record
  (`mov esi,0x95da14` = base + 4, `add esi,0x130`), so every `[esi+disp]` is shifted from the record
  start. Recompute each offset from the pointer's init instruction (`mov reg,imm` / `lea`) and the index
  math (`neg`, `sub 0x27`, `lea e,[i+i*2]; shl e,4`) before writing it down: a "mystery field" whose
  offset is exactly 2× — or +4 from — a field you already have is this artifact, not a new field. Every
  offset derived from that pointer inherits the error, so re-audit the whole cluster, not just the one in
  question, and restate the finding in real byte offsets. The same address can also serve as a VALUE: `DAT_x + off` in pseudocode bases on the pointer STORED at `DAT_x`, while `&DAT_x + off` bases on the address itself — machine `mov reg,ds:ADDR` followed by `[reg+off]` proves value-based (here the tile array hangs off the pointer at 0x92ae14, which is also the address of the faction-record block).
- **`[eax*4+0x985b3c]` and `*(int *)(&DAT_00985aa0 + idx*4)` can be the SAME array.** The compiler folds
  `base + (idx − k)·stride` into a different displacement, so one table acquires several `DAT_` names and
  a base-only grep finds only some of its accesses. Census the whole address **window** and classify by
  operand shape, then pin base and extent from the code that walks it: a loop bound expressed as an
  address (`while ((int)p < 0x985bc0)` = end), a loop that **branches on the pointer address instead of
  the value** (that branch is proof the flat range spans two different things), and live contents — slots
  that hold a known unrelated global (year, `n_bases`, faction mask) are not table entries.
  Recipe: `references/static-store-census.md` §8.
- **Strip the MSVC C++ frame noise before reading a big body.** `[ebp-0x4]` is the exception-state byte;
  a block that stores vtable-constant addresses (0x67xxxx in this exe) into stack locals and calls
  `0x406720` / `0x406060` / `0x5f6de9` is a scope-exit/destructor block, not game logic. Real branches
  jump OVER these blocks, so an address-ordered read puts the logic in the wrong order; skip them, but
  log where each one jumps, because many bodies funnel every early return to one shared cleanup label.
- A single-writer claim needs the census printed both ways: total references **and** the store count
  (`grep <hex-addr> <dump> | grep -c ',al'`), not "the corpus shows one writer".
- **Census a DAT's stores in EVERY objdump print form.** Accumulator-form stores print
  `mov ds:ADDR,eax` — no `DWORD PTR`, and operand filters like `',al'` miss them; a single-render
  grep can miss the only true writer and produce a false "zero direct stores". Instructions printed
  after a `ret` may be cold branch targets (a jcc/jmp earlier in the same body jumps past the ret
  into them, inside the same Ghidra function) — grep backward jump refs before calling such a
  store dead.
- **Jump tables: dump the raw dwords before "correcting" Ghidra's case labels.**
  `struct.unpack_from('<I', img, va - 0x400000)` across the table, entry count checked against the guard
  (`add idx,7` / `cmp idx,6` / `ja`), each target mapped to its body first. A hand-decoded table that
  silently drops one entry yields a mapping that is shifted, self-consistent and wrong — it looks exactly
  like "the case labels are off by one", and only the raw dump (or live data) falsifies it.
- **Keep a superseded model reachable behind a flag** (`--legacy`) when rewriting one that already matched
  live memory: every new mismatch must be attributable to exactly one change; if the rewrite breaks rows
  the old model matched, the rewrite is wrong until raw bytes prove otherwise.
- **Fit the unknown intermediate instead of guessing variants**: per mismatch row compute everything but
  the one unknown internal value, then enumerate it and read off which reproduces live. Variant fitting
  belongs in a subagent, never the main thread — and make every child **write its own notes file under
  `evidence/`**: a child's final summary is a self-report, so confirm that file exists and spot-check two
  or three of its addresses against the disassembly before citing anything from it. For a whole-function
reconstruction, hand the child a pinned structure map (line-cites into the extracted asm window), literal
live addresses, read-only safety rules, and expected values with known downstream adds already subtracted
— the child iterates formulas, it does not rediscover structure. Two children sharing one live game need
an explicit state contract each: only ONE may attach gdb or drive turns, and a child diffing
`/proc/<pid>/mem` must be told no-gdb / no-pokes / no-turn-driver, because a sibling's driven turn mutates
the memory it is diffing and turns its matches into noise.
- **To model a function's output from live post-state, reconcile field lifecycles first.** Grep the
field's disp inside the function's OWN asm: a field mutated at ENTRY and rewritten at EXIT is
cross-visit state — the input your model must feed is the observed post-state with the entry mutation
applied (e.g. a scan-skip mask cleared `&= (~pop|1)` at entry), and strip any later-stage add that runs
after the target function before comparing (driver-log breakpoint order says which stage is later).
Systematic mismatch: try the raw post-state variant before widening the model.
- **Label snapshot columns from true byte offsets, not from a field wish list.** In a `/proc/<pid>/mem` dump script unpack CONTIGUOUS ranges: skipping unknown gap fields silently shifts every later column, and the mislabeled deltas then appear to contradict proven formulas and send you re-deriving settled facts. Before interpreting any cross-snapshot diff, verify one known record against direct per-offset reads.
- **Before counting a live-memory mismatch, check the row is a real record**: histogram the discriminator
  fields across the whole table — rows whose indices run past the shipped data or whose fields hold
  impossible values are stale/unallocated records, not model failures. Counting them as mismatches sends
  you hunting a writer that does not exist. Same for a pipeline accumulator that never changes:
  histogram the gating fields of the input records first — a filter no record satisfies makes the
  accumulator structurally zero (silent sweeps and watchpoints), not a hidden writer.
- Commands + patterns: `references/static-store-census.md`.
- Rebuild recipe, pitfalls and export stats: `references/ghidra-batch-export.md`.
- What the install ships (rules text, map format, graphics containers) and what to parse vs
  what to RE: `references/data-formats.md`.

## terran.exe PE layout (verified 2026-10-20 via section table + byte reads)

Image base 0x400000. Sections (RVA): `.text` 0x1000 + vsize 0x26f3f4 ⇒ VA **0x401000–0x671000 with
raw bytes present** (`55 8b ec` prologues verified at 0x520e70, 0x51e700, 0x5d0c33 WNDPROC, 0x62ad73
FLIC, 0x6309aa DP-init); `.data` RVA 0x289000 vsize 0x316284 but **rawsize only 0x20000** ⇒ data above
VA ≈0x6a9000 (`DAT_0091f6c4`, `DAT_00985b10`, `DAT_0099d020`, …) is uninitialized/BSS at runtime and has
**no bytes in the file**; then unnamed/UVA_DATA/_SELFMOD/.rsrc/.reloc, last section ends RVA 0x5e4000
(VA 0x9e4000).

Consequences — this **corrects the earlier "self-modifying, analyzed image ≠ file image" note, which
mixed RVA with VA**: (1) **all game CODE is in the file**; Ghidra's decompile of any `FUN_` (including
0x5dxxxx–0x66xxxx) is authoritative, and runtime breakpoints at those VAs fire (M7/M8 proved it); (2)
only *data* reads above ≈0x6a9000 need a runtime snapshot (`gdb -batch -ex 'dump binary memory …'`);
(3) `_SELFMOD` is a 0x415d-byte section — a small patch area, not a whole-image unpacker, so there is no
"import of the wrong image" problem.

## Map + save container formats (verified 2026-10-20 — see MAP_FORMAT.md / SAVE_FORMAT.md)

`.MP` map — `15 + 2724 + W*H*22 + trailer == file size`, checked on both shipped maps:
```
0        15 B   b"TERRANMAP\0" 0x1A u32 version(=5)
15     2724 B   header struct: u32 width, u32 height, ... (word 5 = land cells = W*H/2)
2739    W*H*22  raw cell records, row-major (no XOR)
+      var      trailer, starts b"????????" (128 B @80x80, 338 B @128x128)
```
planet.MP 80x80 143,667 B; planetx.MP 128x128 363,525 B. Parser `scripts/decode_map.py`.

`.SAV` save — `b"TERRAN\0" 0x1A u32 version(=86)`, 796 B header, mission year u16 at **+0x54**;
then sections read in a fixed order (see SAVE_FORMAT.md). Section *sizes* come from header counts
and shrink as the game progresses, so arbitrary saves can't be split yet.

**`FUN_00597a70` is the save/scenario block loader, not the map loader** — an earlier note here
claimed otherwise. The map grid is read raw by `FUN_00582260`.

`.SAV` section sizes (from the `push` sites in `FUN_00596850`): 796, 67,040, 11,488, 16,000, 3,584,
26,624, 4,096, 256, 152, 10,144 are immediates; three are computed — one raw count (`DAT_00927538`),
one **52 B/record** (`edx` records), one **304 B/record** (`DAT_00985af4` records). Two are skipped
outright under version/count conditions, so the section list is conditional.
`.SAV` is fully splittable from the file alone — `scripts/decode_save.py --sections` sums to the byte.
Key facts: u32 **own player at file offset 808**; a **u32 count prefix immediately before** one
variable section; the other two variable sections are `n × 52 B` and `m × 304 B` records, split by
solving `52n + 304m = region` and choosing on zeros-fraction (304 B records ~80% zero, 52 B ~40%).
Caller-scoped gdb condition that makes small reads loggable without flooding:
`break *0x64cc00 if *(void**)$esp >= 0x596850 && *(void**)$esp <= 0x597a6b`.
Anchors that pin a save's layout byte-exact (verified on two saves of different ages): map dims
`50 00 00 00 50 00 00 00` at **79,372** and `????????` at **222,896**; gap 143,524 = 2,724 + 140,800.
`scripts/decode_save.py --anchors` checks it.
**Pitfall:** never validate an offset by "fraction of identical bytes" — these files are mostly
zeros, so the match rate is flat across wrong offsets. Use a unique content signature instead.

### Technique that cracked both: runtime read trace, not static reading
Break on the read wrapper and log the **caller** and size:
```
break *0x64cc00 if *(int*)($esp+8) >= 64      # 0x64c9a0 is the sibling wrapper
commands
silent
printf "R3 caller=%#x size=%d count=%d file=%#x\n", *(void**)$esp, *(int*)($esp+8), *(int*)($esp+12), *(void**)($esp+16)
continue
end
```
- Unconditional breakpoints here fire **34,000+ times** (the game reads 1-2 bytes constantly) and
  slow it to a crawl; the `>= 64` condition is what makes the run usable.
- The caller address maps each read to its function, so the section order falls out in one run.
- Then close the arithmetic against the file size: if `sum(reads) + known_prefix == filesize`, the
  layout is complete. That is the check that distinguishes a real format from a guess.

## Format core (verified; details in FINDINGS.md)

- TLV chunks `u32 LE tag + u32 LE size incl. header`; outer tag `0x00525643`
  ("CVR\0"), size == file size. Children: 0x01000000 version float (10.0/10.1 —
  NOT a scale), 0x02000000 .MAX scene name, 0x03000000 palette group
  (0x01010000 name, 0x01020000 palette data 6914 B = u8 first + u8 last +
  256×RGB24 + 24×256 shade table, 0x01030000 material 12292 B = 4-byte header +
  24×256 u16 R5G5B5), 0x04000000 scene group (0x4010000 name, 0x4020000 object
  count, 0x4030000 frame count, 0x4040000 per object).
- Object: 0x4040100 name, 0x4040200→0x4040201 VOXEL blob, 0x4040300 animation
  (0x4040301 frame flags 1B/frame, 0x4040302 float32 locations **Z,X,Y**,
  0x4040303 3×3 float32 matrices) — animation-only files exist (Asas.cvr).
- VOXEL blob: VOXEL_HEADER 42 B (flags, size, units-per-pixel float, next, end,
  int16 ZXY scale/position/rotation-center, count). flags&1 = header chain at
  h+next; flags&2 = JUMP_HEADERs (32/36 B, run starts at position+offset).
  Voxels = 3 B: (dir<<3|normal_hi), normal_lo, color index; dir = 5-bit delta
  over 27 steps, 0x1A STOP (STOP-coded last voxel is real); normal = 11-bit
  angle code `((dir&7)<<8|lo)+88`, a1=88−n%89, a2=n/89 → unit vector.
  Regions end with 5 zero pad bytes. Count quirk: single-header jumps
  Σjc=count+groups, multi-header jumps Σjc=count.
- Chunk parse addresses in terran.exe: loader 0x614acb, top loop 0x6446e0,
  per-object 0x644f80, blob stored opaquely by 0x645170. Voxel semantics are
  wiki (alphacentauri2.info/wiki/Caviar) + corpus verified, not exe-verified.

## Multiplayer netcode (mapped — details in FINDINGS.md)

- Internal netcode codename **"jackal"** (debug strings `jackal` +
  `NET_SENDTIMEDOUT`, title "Message from the Net Underworld").
- DirectPlay via COM-style init `FUN_006309aa` (GUID {9d460580-a822-11cf-…}
  @0x67bcf0); DP object global **`DAT_0099d020`**, vtable +0x14 GetMessages,
  +0x68 SendData, +0x28 CreatePlayer. DPLAYX IAT slots have zero Ghidra xrefs.
- Packet: 12-B header (u8 DP flags, u32 seq, payload u16 type @+0, sender
  u32 @+2); builder `FUN_00584010` → router `FUN_0052a260` (type&0x4000=
  guaranteed broadcast, &0x8000=directed, 0x2000=server-originated) →
  `Net::send FUN_00635407` (16×0x58 slot table @this+0x150, seq
  this+0xe0, adaptive ack/timeout). Anti-replay gate `FUN_00639787`.
- Receive: thread `FUN_00638d5c` → `FUN_00638ddd` (GetMessages + gate +
  queue `FUN_0063af12` + PostThreadMessage 0x402) → main drains
  `FUN_005262e0` (in-game queues)/`FUN_00526e10` (synch queues 0x80–0x8d)
  via `FUN_0052a720`+`FUN_006361ff` → dispatcher **`FUN_0052bce0`**.
- Diplomatic types 0x2440–0x244e = DOUBLE CROSS/TREATY ON/OFF/SET/AGENDA
  ×3/ENERGY/TRADE MAPS/CEDE/WITHDRAWAL/TECH/LOAN, one wrapper each
  FUN_00530640–0x530c40 (asm-verified). AI hub `FUN_00546800` (34 send
  sites). Turn sync: client LOCK(0x2210)/DONE TURN(0x8301) → server
  EXEC DONE/NEXT TURN via 0x1240/0x1501/0x4301/0x4303.
- File-name traps in ~/reverse/smac: `treaty.pseudocode.txt` = FUN_00546800
  (not 54d5f4); `killfaction.pseudocode.txt` = FUN_0047c0e0 (UI pane);
  FUN_0047e846 has no callers/pointers — KILLFACTION is a voice-clip token,
  not a message type. UPPER_CASE tokens 0x68b000–0x691600 are sound/voice
  clip names, not protocol opcodes.

## Goal (Paul's priority)

Play SMAC **single-player with working AI** on modern hardware **and recreate
the full menus + game UI** (reimplementation target). Multiplayer netcode is
mapped but secondary. UI groundwork: CPane/CWidget pane builders (e.g.
`FUN_00444140`, `FUN_0047c0e0`), PCX v3 art (`programs/*.pcx`/`.flc`), `.sc`
scenario files, voice/sound clip token strings 0x68b000–0x691600, UI widget-name
strings (TOUR1*, SOCTOUR*, DRONETOUR*).

## UI / asset pipeline

- **Script.txt IS the UI**: `programs/Script.txt` declaratively defines
  1,357 dialog panes (`parse_script.py` → `script_parsed.json`). Grammar:
  `#NAME` pane start (UPPER id), `#xs` width, `#x/#y`, `#caption`,
  `#button`, `#itemlist`, `#listbox`, `#wave N` sound, `^`/`^^` newline/
  center, `{}` bold `[]` italic, `$NAME123` substitution, `$<n:a:b>` gender.
  Menu trees (TOPMENU/MAPMENU/MULTIMENU/SCENARIOMENU/setup chain/RULES/
  SCENRULES/victory/editor/intro) verified. Spec: `~/reverse/smac/UI_MAP.md`.
- **alpha.txt = the rules file the exe loads** ("reads the rules of the game from this
  file"): 45 `#SECTION`s / 650 comma-separated records (`#RULES`, `#TERRAIN`, `#TECHNOLOGY`,
  `#CHASSIS`, `#WEAPONS`, `#UNITS`, `#FACILITIES`, `#SOC*`, `#DIFF`, `#FACTIONS`…). Parse it
  (`scripts/parse_alpha.py` → `data/alpha.json`, section map in `ALPHA_RULES.md`) rather than
  RE-ing balance constants. Field names are recoverable from the trailing `;` comments for only
  4/45 sections — `#CHASSIS`/`#UNITS` etc. are bare data, so their semantics must come from the
  exe's parser, not from guesswork.
- **`maps/*.MP` = the map format** — now fully decoded, see "Map + save container formats"
  above and `~/reverse/smac/MAP_FORMAT.md`. (This bullet used to claim the loader was
  `FUN_00597a70` and that the 796-byte header's offsets were unresolved; both were wrong —
  that function is the save path and the map header is a 2,724-byte struct at offset 15.)
  `FUN_00598340` is still the magic/version dispatcher.
- **PCX**: SMAC variant starts `0A 05 01 08`; Pillow 12 decodes all 378
  correctly (`assets.py pcx programs png`; sheets in `sheets/`). Hand RLE
  decoder unsolved; glsmac hits same wall (SDL_image + procedural fixes).
- **FLIC format cracked** (not standard Autodesk): 128-B header u16
  words: w2=0xAF12, W=u16@+8, H=u16@+10 (monument.flc 1024×768 ✓),
  w6=8; frame chain @128 = `u32 LE size` + u16 0xF1FA + u16 subchunk
  count, sizes tile to EOF (turn.flc 1081+18×196+16=4473 ✓). Exe:
  loader FUN_0062ad73, dispatch FUN_0062bdeb (chunk=u32 size+u16 type;
  F1FA=container recurse; types 4/0xb/0xc/0x12 no-op stubs incl. the
  772-B color table; 7=16-bit small-brun FUN_0062b68e; 0xf=8-bit brun
  FUN_0062b3da: per row u8 width then s8 packets (>=1 literal, <0 RLE
  w/ next byte, +ref variant); 0x10=raw rows FUN_0062bc1d; 0xd=clear;
  delta table flag|2: 7→FUN_0062c36f (copies unchanged runs from prev
  buffer @this+0x4ac when run color == transparency)). Decoder scripts
  `flc_decode*.py`; type-7 RLE word color semantics + per-object ref/trans
  still being pinned. See UI_MAP.md.
- **glsmac** (afwbkbc/glsmac, cloned at `~/reverse/smac/glsmac`): working
  SDL2/GL SMAC reimplementation; hardcodes UI (does NOT parse Script.txt);
  resource enum names master atlases (palette/interface 750×900/icons/
  units/console_x/moon1-3/S{s}L{l}C{c}/arialn.ttf). Useful reference.

## Running under Wine

SMAC reaches a **live, interactive single-player game** under a pure 32-bit Wine
(wine-10.20-staging-tkg-x86) on Xvfb :99 + llvmpipe; the Script.txt UI panes
render and respond to clicks. Launch command, i386 prereqs, xdotool click coords,
the i386-libpulse audio fix, the exe-verified input routing (a map click pans the view and cannot order a move until the pane is in destination mode 9, so drive
units with arrow keys),
Script.txt dialog geometry and the DirectPlay hypothesis are in **`references/wine-runnability.md`**.
- **Clean stale Wine before measuring:** orphaned `winedevice.exe` from dead sessions (ppid = systemd
  --user, same WINEPREFIX) burn ~40% CPU each (load 12 on 4 cores) and make the intro crawl so blind
  clicks mistime — `kill -TERM` them first.
- **Preflight every boot — two silent killers.** `kernel.yama.ptrace_scope` resets to 1 on reboot, which
  breaks BOTH `gdb -p` and `/proc/<pid>/mem` with EACCES: run `sudo sysctl -w kernel.yama.ptrace_scope=0`
  before any measurement (a "ptrace ok" note from an earlier session only holds until the next reboot).
  A reboot also wipes `/tmp`, so write evidence under `~/reverse/smac/evidence/`, never `/tmp`.
- **Locate widgets by TEXT, never by remembered pixels.** Capture with `xwd -root -silent -out f.xwd &&
  ffmpeg -i f.xwd -vf crop=800:600:0:0 -y f.png` (no ImageMagick here), then read it with
  `tesseract --psm 6 tsv` on a **2×** nearest-neighbour upscale and click the OCR box centre
  (2× costs 0.94 s where 3× costs 1.85 s and reads nothing extra; region crops are slower still). Fixed coords
  drift between UI states and blind clicks open ABOUT popups or base screens. Working pair:
  `~/reverse/smac/scripts/smac_state.py` (live memory: mission year `DAT_00985b00`, mode flags
  `DAT_00985dc8`) and `scripts/smac_play.py` (turn servicer); depth in
  `references/wine-headless-harness.md`. Fallback coords (800×600 window at 0,0): TURN COMPLETE (650,410),
  base-naming OK (400,171). After a `smac_play.py --turns` run returns, `cur_player` may still sit on an
  AI faction (a driver "turn" is counted as a year tick) — re-read `smac_state.py` and keep driving until
  control is back with the player before assuming our-turn state.
- **`xdotool` keys are dropped unless the window has focus** — call `xdotool windowfocus <win>` first (Xvfb
  has no WM to grant it). Without focus `Return`/`Escape` silently do nothing and every dialog looks
  undismissable, which reads exactly like a game hang.
- **Modal = key sink (M32 mechanism):** while a Script.txt modal is up the pump does not
call the key router at all — every key is silently dropped (looks like dead input). Run
`scripts/smac_probe.py --quiet` and require `screen=hud` before any key sequence; dismiss modals
first (M29 rules: `Return` for DATALINKS/PSI/event pages, one `Escape` for OPERATIONS DIRECTOR).
Advisor panes are TRANSIENT (auto-dismiss 1–2 s, faster than one OCR poll) and while up they
swallow the NEXT input event (echoes as menu code `0x20011`) — a rejected order looks like a
dropped keypress. **Never press a key to dismiss a transient pane:** it is already closing, so
the key lands on whatever replaced it — an `Escape` aimed at a caption pane CANCELS the
picker that opened behind it, and the game reports a plain "declined", which reads as the
option not being offered. Wait for the next pane (poll the tracer log or re-OCR) and answer
that one. gdb attach itself can drop X events: re-press the key after arming.
- **`/proc/<pid>/mem` pokes are ghosts while a tracer (gdb) is attached (M33).** Readbacks
lie: a poke reads back the new value, then shows a different one after attach. Poke only
with TracerPid 0, arm gdb AFTER poking, verify state after `kill -CONT`. M34 reconfirmed:
writes are fully dead under a live tracer (poked sel=46 → setter fired on the cycle's unit
50). Selection globals
(`0x91b5bc`/`0x91b5c4`) are additionally game-owned: the pump revalidates them and reverts
to the cycle's choice within ~1 frame when the poked unit fails the gate — press the key
IMMEDIATELY after the poke (no sleep) or use the game's own select (`FUN_0040c8d0`,
PICKUNIT picker via map click; calibrate clicks via the HUD tile-info panel OCR, not the
48×36 lattice formula). Under a tracer, steer selection only by completing actions
(HOLD-walk, see M34 footing); gdb bp conditions must cast `*(int *)($esp+4)` — bare
`$esp[1]` kills the batch script at the first hit.
- **Stop at a title/menu screen; never click it.** `Escape` there opens `Do you really want to quit?`
  and the next OK exits the game (process vanishes, nothing in the Wine log). Classify
  `SID MEIER'S ALPHA CENTAURI` / `really want to quit?` as a fatal state: save a screenshot and stop.
  Exception: the quit prompt also pops MID-DRIVE after `--turns` runs (session 65) while the game is
  otherwise healthy — Escape back to "Oops, no, wait!", never click OK.
  Dark/unrecognized frames get ~20 s of grace before a single Escape — cinematics end themselves.
- **A PROPOSAL vote pane stalls the AI turn phase (M53n):** `YEA: 2  NAY: 3` is the vote TALLY, not a
  key hint (keys 2/3 do nothing; `smac_play.py --turns 1` returns STUCK while it is up). Click the bottom
  bars (true window coords) YEA (310,495) / NAY (398,495) / ABSTAIN (485,495), then the single OK bar
  (393,495). Find the bars by cropping the ROOT capture (`xwd -root -silent` + ffmpeg
  `crop=420:180:230:370,scale=iw*3:ih*3` + vision) — `xwd -id <win>` reads blank to tesseract. Focus
  (`xdotool windowfocus`), click, wait ≥2 s, re-capture to confirm the pane advanced.
- **Instrumentation lessons (M53n, `scripts/m53n_drive.py`):** a breakpoint at a function ENTRY hands you
  the caller free (`*(int *)$esp`); mid-body hits print 8 stack words in the same printf, post-matched
  against the call sites' return addresses (a fixed 5-byte `call` run makes the set derivable from
  disasm) — caller census with zero breakpoints inside the callee. And an accumulator that nets +1
  despite N accumulation-fires is being REBUILT, not added to: watch the field across the whole block,
  not just the accumulate site (4e78e0 zeroes +0xbc/+0xc0 at 0x4e79a5 and re-adds a per-item vector
  0x4e7be3-0x4e7c28 before 4e92c0/4e93f0 add the crawler terms); watchpoint `new=` sequences (0 then a
  ramp) are the tell. And a value-change watchpoint UNDERCOUNTS calls: a callee that rewrites the same
  value is invisible, so hits are state SWITCHES, not call counts (M53o: `4e3470` 19 hits vs 55 calls,
  every one from `4f6030`).
- **OCR targets must be ≥4 characters and region-constrained.** `yes` matches `Moyes:` (the unit
  panel's `Moves:`) and `ok` matches `Prokhor`, so a naive matcher clicks the map forever and the
  dialog looks undismissable. Same for dialog phrases: squash the joined OCR text to `a-z` and require
  the question body (`endtheturn`), never a similarity ratio — difflib fires on title/map text.
- **Click the OK bar ≥1.2 s after selecting a dialog row.** Faster and the confirm applies the
  previous selection ("No, let me move them"), the same question reappears, and it reads as a hang.
- `kill -TERM gdb` (batch) leaves terran.exe stopped (state `T`); `kill -CONT <pid>` revives it.
- **Script confirms queued behind a screen's widgets are UNREACHABLE** (M48d): CONFIRM DISBAND
  opened from the base screen slid behind base-panel chrome — rows/OK landed on chrome hitboxes,
  keys dead (M32), row clicks never moved the highlight: a modal that swallows input but whose own
  OK bar is occluded. Each menu-item click QUEUES another identical confirm; each OK click cancels
  one — a cycling look-alike pane is a draining queue, not a frozen pane. Recovery when trapped:
  relaunch + load autosave (saves at `<game>/saves/auto/Alpha Centauri Autosave N.SAV`, mission
  year u16 @ file 0x54 — read before trusting the slot number; slots rotate in place; zero progress
  lost since last round). `xdotool key BackSpace --repeat N` FAILS on this xdotool — loop it.
  TOUR hint popup (auto-opens on a screen's first view): Continue ≈(325,585); Social Engineering
  screen: OK ≈(240,368) commits, CANCEL does not close.
- **A python driver whose argv contains its run tag matches the bracketed `pkill -f [t]ag_...`
  pattern and SIGINTs ITSELF** at startup (the bracket only protects pkill's own cmdline).
  Kill stale copies with pgrep + os.kill skipping os.getpid() (fixed in `scripts/m49a_drive.py`).
- **A gdb watchpoint with no `commands … continue end` block ENDS a `-batch` run**: on the first hit the
  script has nothing left, gdb falls to its prompt and DETACHES — silently un-instrumenting the rest of
  the session (reads as a truncated log, not as an error). Give every watchpoint a printing `continue`
  block. **x86 gives 4 hardware watchpoints total** (8-byte windows need 8-alignment and cost 2 DRs
  each; 4-byte windows cost 1): watch at most 4 globals and cover the remaining addresses with a
  10 Hz `/proc/pid/mem` poller (`scripts/m53m_poll.py` pattern). And gdb's own messages are unbuffered while breakpoint `printf` output is block-buffered: the
  two streams interleave in the log, so attribute events by CONTENT (counters, an `off=0x50..0x74` run),
  never by line order, and read the log only after the driver's `--mode stop` (SIGINT drops the tail). Worse, a SHORT run can lose
  the whole buffered tail silently and read as "no breakpoint ever fired" (m53e1: the clicks clearly
  worked, the log had zero events) — **spawn gdb through `stdbuf -o0`** (fixed in
  `scripts/m53e_drive.py`). Separately: a command-list expression that uses a convenience variable
  which isn't a number aborts the sourced script and DETACHES silently ("Argument to arithmetic
  operation not a number or boolean", `m53e5_watch.log:50`) — bake the base pointer as a literal
  (`set $b = 0x962d30`) instead of reading `*(int *)0x8f0d60` per hit.
- **Vision-tool pixel numbers ARE true window coordinates; tesseract TSV numbers are internally
  rescaled** — never halve TSV values to get click coordinates. Settle any disagreement with
  `ffmpeg -vf crop=W:H:X:Y` + OCR on the crop before driving clicks (M53d wasted three runs on this).
- **Base production UI plumbing (M53d)**: pane-object fields `+0x3ff5c` = selected queue slot and
  `+0xb194` = chooser mode **but nothing stores through `pane+0xb194`** — the pane (static BSS
  0x6a9480) exposes the chooser sub-object at `+0xa1c` (0x6a9e9c) and the mode is stored as
  `[sub+0xa778]` = 0x6b4614 = pane+0xb194 (a byte scan of .text for disp32 `94b10000` finds exactly
  one instruction: the read at 0x4186ec); `FUN_00416080(this)` = pane redraw; `FUN_00496ad0(pane+0xa1c, base, owner,
  scratch)` = the modal item chooser (returns an item id or −9999); `FUN_00417ee0(slot, …)` = the
  dispatcher; `FUN_00417d20(item, insert_flag)` = the queue-slot writer. **Digit keys 1-9 pass a nonzero
  param_1 and only PREVIEW — nothing is written**; a real queue edit needs the QUEUE-row path.
  **Chooser bars (label-verified, M53e)**: HELP 153-233, OK 252-311, REPLACE 364-421, INSERT 472-523,
  DELETE 556-636, CANCEL 659-705 at y 336-352 (labels drawn inside the bars, fill RGB 103,91,181 —
  pixel (160,343) is the instant chooser-open test; 2x OCR cannot read the labels). **M53g corrected
  the handler**: the bar switch is `FUN_00496950` = **vtable+0xa8** of the chooser class (live vptr
  0x672298), jump table 0x496a9a indexes `param+2`; cases 0=HELP(gate)→1, 2=(gate)→7, 5=INSERT(gate)→5,
  **7→7 UNGATED**, −1=OK→0, −2=CANCEL→0+guard−1; gate = `cmp [this+0xa774],-1; je 0x496a91`, and
  **0x496a91 is the shared epilogue return — mode-storing paths reach it too (BAR_IGNORED there is NOT
  a refusal)**; **one handler run per click** (press; release dispatches nothing). `[sub+0xa774]`
  (pane+0xb190) IS the selection: a cell index in a 5-col grid (rows y~60/160/260 = cells 0-14, bar
  row = phantom cells 15-19, col3 = x 381-421); paint `FUN_004954e0` clears it to −1 (0x495541) then
  sets it to the enum index of the selected slot's item (0x495b00); icon/cell click → setter 0x4962ec
  (vtable+0x48). **Clickable rects ≠ drawn bars**: REPLACE = param 7 fires at (345/365,343) — its
  drawn body 381-421 is dead phantom-cell territory (setter path, handler never called); INSERT 5
  fires at 425/440/497. **OK = mode 0: writes
  nothing and does NOT restore the snapshot** (a committed edit survives OK); **CANCEL =
  `[sub+0xa774] = -1`** → returns −9999 → rewrites +0x50..+0x74 from the stack snapshot and exits
  without consulting the mode (makes armed REPLACE probes non-destructive); **HELP** opens the unit-design pane (bars y 356, CANCEL x≈614) whose
  CANCEL re-opens the chooser. QUEUE rows 1..8 = pending slots +0x54..+0x70 (row text y =
  439+12·(row−1)); the 9th pending slot +0x74 has no row; the head +0x50 is the LEFT panel.
- **Type-record `+41` is the COST FACTOR (M53b), not a weight and not turns.** `0x98ad88 + type·52 + 0x29`,
  one writer: `FUN_00595b10` (`ghidra_out/shard_015.c:9358`) = `FUN_00595820(chassis, weapon, armor,
  ability, reactor)` summing the alpha tables' cost fields (chassis `0x92ae80`/0x90 +4, weapons
  `0x92b950`/16 +3, armor `0x92fd10`/16 +0xa). Every price is `FUN_004e40a0(owner,1,-1) * +41` (10 = 100 %;
  printed in `FUN_00577280`, debited at `0x4efee0`), so `+41 = 1` costs 10 minerals; `+42` = the alpha
  Plan, `+43` = auto-calculated AI role (`weapon mode + 0x20` for noncombat packages). Proof pattern:
  `scripts/m53b_costcalc.py` + `scripts/m53b_types.py` re-implement the formula and diff it against live
  memory — every populated row accounted for, none left as "explained elsewhere". **Alpha comment headers name the columns** of sections whose
  rows are bare data (#CHASSIS/#WEAPONS/#DEFENSES/#UNITS) — read them before guessing a table's fields; enum gates decode the same way — index the alpha enum
sections by value (PLANS 10 = "Supply Convoy", ORDERS 3 = "Convoy", only 9 entries: live order
bytes 24/28 are engine-internal) before guessing what a small-int gate in sweep code means.
- **The alpha `#UNITS` loader (`FUN_00579f40`) overrides the type builder AFTER it runs**: Plan→`+42`,
  Cost→`+41` (0 = Autocalculate), Carry→`+40`, Icon→`+46` — all as disp8 stores off a `record + 50`
  register, row-capped at 0x40 so designed units are never overridden; the save loader restores
  `+41`/`+42` verbatim, so a loaded scenario can carry bytes the formula never produced. The ability
  table `0x98aaf4` (stride 28) is the 24 `#ABILITIES` rows: `int[0]` = the cost rule (rule switch = jump
  table indexed `rule + 7`, in Ghidra's case order), `int[2]` (**+8**, not +16) = the flag word whose bit
  0x400 adds a +1 surcharge on land chassis — the classic off-by-one field-offset trap.
- **COMM OFFICER 3-row variant** ("Yes..."/"No, close the channel."/"Display faction leader
  profile."): the colour row-click (bar_y−25) can select profile → UNIVERSITY INTELLIGENCE FILES
  table with CLOSE/DATALINKS bars at y≈345-360, OUTSIDE the 430-520 OK-bar band; the
  rightmost-bar row+bar cycle drains it but slowly (~8 min / 43 OCR passes once). OCR the row y
  and click it directly instead.
- **Colour-only pane driver works** (m48d_drive.py, 3 rounds 0 OCR 0 stalls): for any flat blue bar
  in y 150-430 click (bar_x, bar_y−25) [option row above] wait 1.3 s then click the bar; single OK
  bars live in the 430-520 band (find_ok_bar); TURN_BTN only when hud_up; tesseract only as a ≥35 s
  stuck fallback. A driver-generated gdb script (baked literal watch addrs from a content-based
  base re-scan + SELFTEST printf block) beats hand-edited scripts across process restarts.
- **A gdb `call` into game code is a last resort, never a first move.** Injecting
  `FUN_004cffa0(unit,x,y)` reached the callee twice (its `unit+4 |= 0x40` appeared in memory) but never
  moved a unit; once, fired **while a modal dialog was up**, it SIGSEGV'd and left the process alive with
  a completely dead UI (every click inert, main thread `R` with climbing `utime`) — recoverable only by
  relaunch + reload. If a breakpoint fires *inside* an injected call, gdb abandons the expression,
  detaches, and the inferior returns to gdb's dummy frame.
- **Production vector (M53o):** `base+0xbc/0xc0/0xc4/0xc8` = NUTRIENT/MINERAL/ENERGY/PSI, REBUILT on
  every block execution by `FUN_004e78e0` (seed from faction+0x2e20, live 0; exactly 7 add sites
  0x4e7c15, 0x4e7ea3, 0x4e85bd, 0x4e8739, 0x4e883b, 0x4e8951, 0x4e8a32; per-tile values = alpha
  `#RESOURCEINFO` verbatim @0x926bd8; its tail loop 0x4e8b6f-0x4e8d48 writes only +0x48); read-only
  model `scripts/m53o_recon.py` reproduces 36/76 bases.
- **Production chooser internals (M53h).** Candidate array `DAT_009267e4` (128 dwords, count `0x9267e0`) is
  built by `FUN_00596000(faction)` — ids = shared 0-63 then `faction<<6` designed units — and ordered by
  `FUN_005a29a0` (lockstep bubble sort, swaps only on strict `<` ⇒ stable) on
  `((ch_tbl[+1] + Plan*0x10)*0x40000) + (0x20 - weapon_power)*0x200 + (8 - chassis_class)*0x40 + (8 - 2*armor)`,
  `ch_tbl = 0x92ae80`/0x90 (`+0` class, `+1` naval flag), Plan = record+42, unavailable ⇒ key 999999999 ⇒
  last: **the order is Plan-major, never icon order**. Per-base filter `FUN_005a73f0(id, faction, base)`
  (record+0x30 bit 0, faction mask +0x2c, naval gate `FUN_004e4620(x,y)==0` when the chassis table says
  naval, prereq word +50 for alpha ids), then secret projects 1..0x47 via `FUN_005a6e70`.
- **Chooser return sign = record kind.** `FUN_00496ad0` returns `+item` when the selected node's detail
  flags (detail+8) have bit 0x20, else **`-item` where item is the index into the secret-project table
  `0x984d38`** (stride 48: +0 name, +4 effect ptr, +12 cost factor) — a queued project is a negative
  index, not an offset into a record.
- **Chooser bars are embedded controls, not Script.txt buttons.** Six children at
  `chooser_sub + 0xb74 + i*0xb4c` (sub = pane+0xb18c), param at control+0xa78, rect at
  +0x13c/+0x140/+0x144; (re)built per open by `FUN_00496ad0` right-to-left with params -2 CANCEL,
  7 REPLACE, 5 INSERT, 4 DELETE, -1 OK, 0; `x = ((W-0x20) - 103*count)/2 + (count-1)*103` (W =
  `sub+0xa824`, pitch 103, width `sub+0xb70` = 100, count = `sub+0xb6c`, y = `rows*cellh+8`). Release
  `FUN_005fab08` forwards control+0xa78 to **owner vtable+0xa8** — that param is the mode selector, and
  the factory `FUN_005f9e85(caption, param, x, y, w, h, owner, 0)` is where any dialog's bar params get
  set (caption `*(DAT_00997b20+off)`, `CharUpperA` — so bar text never appears in Script.txt).
- **Live list walks take count from header+0x10** (+8 head, +0xc cursor): using the cursor as the loop
  bound iterates ~79M times and looks like a hang. The chooser's item list is `sub+0xa780` = 0x6b461c and
  **survives the close**, so a cancelled chooser can still be read to see what was enumerated.
- **Secret-project table (M53i).** `0x984d38` IS the alpha `#FACILITIES` section verbatim (72×48 B;
  **live index = alpha row + 1**, row 0 null placeholder): +0 name / +4 effect string ptrs into a
  ~0x2100000 arena, +0xc cost factor, +0x14 prereq tech (−1 = None), +0x18 = −2 constant. A queue
  value < 0 is **−project index**; its price = `(&DAT_00984d44)[(−q)·0xc] × 0x4e40a0` — `0x5ac950`
  does NOT handle negative ids. `0x984d44` is dword 3 of the SAME record, not a second table.
  **Grep the DAT prefix (`984d`), never just the base**: Ghidra splits one table into
  `DAT_00984d38/44/4c/...` renderings by field offset, so a base-only grep silently misses refs.
  **Claim array (M53j):** the per-project claim table is **33 dwords at `0x985b3c`, index =
  project_idx − 0x27** — only projects ≥ 0x27 have a slot (`< 0x23` ones are tracked in the base
  facility bitmap at base+0x8c instead); value = the base INDEX that completed it, −1 = unclaimed, and
  it is written with the pane-loop's current-base global, not a per-loop index. The flat rendering
  `*(int *)(&DAT_00985aa0 + idx*4)` is the compiler folding that subtraction, and `0x985aa0..0x985b38`
  are unrelated globals (year, `n_bases`, mask) — not early claim slots.

## Still open (leads)

Current footing (M39, 2026-10-21): **second terraform mode proven — Road (`r`) issues with
the whole cost block skipped (no picker, no debit; no-pay modes jump `0x4d5496..0x4d5634`)
and completed in 2 executions at elev 6: tile (45,7) mask 0x108002→**0x108006** (road bit
0x4), year 2295 (`scripts/m39_issue.py`, 45-bp concatenated gdb).** **Key model corrected:
`Tab` = cycle (empty cycle ⇒ ENDOFTURN1), `l` = SENTRY order key** (oops-proof); cycle skips
MP-exhausted units (poke `+40=0` first); menu-pending `0x91b5c4` sticks — poke 0; mid-turn
start (cur==me, panel up, black map ⇒ classify lies) ⇒ go straight to selection. M38 core
(still true): issue cost `0x4cc7b0` = `(|elev−3|+2)²` (9@elev4, 16@elev5, 25@elev6 > our 15
energy; economy-gated); M37 core: execute chain + multi-turn accumulator. Tile (45,7) elev 6
with road; `0x2101` queue still no solo consumer. `~/reverse/smac/` is durable. Execution chain + terraform engine + tile/tech-gate facts: `references/terraforming-order-path.md`.
Selection rules hold: HOLDed (order 2) units are not cycle candidates; empty cycle
**auto-ends the turn**; a map click selects a unit **and** sets orders mode `0x91b5b8=1`;
`Tab` re-opens CUSTOMIZE mid-game. UI: **ENDOFTURN1** pane → **Return** (never Escape); Escape
on a bare HUD opens **REALLYQUIT** (oops row y≈260, OK ≈307) — `answer_confirm` CANNOT service
it (`find_yes_row` scans y 160–220, defaults to 196 = pane artwork); use
`scripts/m37_recover.py` (oops row then OK +47 px). Harnesses: `scripts/m37_exec41.gdb` (11 bps:
REFRESH/ORDEREXEC/TERRAFEXEC/CHECK/NOTYET/CANCEL/COMPLETE/RAISE/LOWER/SETELEV/MASKSET) +
`scripts/m37_exec41.py` (multi-round completion runner — **must click TURN COMPLETE every round**
on a bare HUD, else stalls; snapshots `+37`/elev; REALLYQUIT special-case),
`scripts/m37_recover.py`, plus the M35/M36 set (`m36_store.gdb`/`m36_dismiss.py`,
`m36_exec.gdb`/`m36_exec.py`, `m35_pay.gdb`/`m35_paypicker.py`, `m35_gate.py`,
`m33_scan.py`/`m33_state.py`); **M38: `scripts/m38_issue.gdb` (34 bps, full issue chain incl.
PACTCHK/REFUND/DIPLO/EPILOGUE) + `scripts/m38_issue.py`** — selection recipe (poke `+40=255`
on other own order-0 units → `Escape` → pump auto-selects the Former), `]`, pane servicing,
`COST 16 → DEBIT 31→15 → STORE 0x14 → BCAST` live; elev-5 footprint = **49 tiles 7×7** (81 =
elev-6's 9×9), diplomacy branch armed **silent** (no foreign tiles); completion `m38run2` →
`SETELEV new=6` year 2293, re-erosion lifted 8 neighbours 4→5; energy 15, income ≈ upkeep ≈
+0/turn ⇒ next terraform (25) economy-gated. Depth:
`references/terraforming-order-path.md` (the M39 Road-mode proof, thresholds and keys duplicate the footing paragraph above). Next
(M40 DONE, live 2026-10-22): MagTube remap + first TECHFAIL — `r` on a roaded tile: TERRAF 0x5
→ remap rewrites the mode arg inside `0x4d44d0` (TECHCHK sees 0x6; gated on cap table `0x6938e8`
idx `mode*8+tile-seafloor`, MagTube land 18/sea −2 ⇒ land-only) → gate 0 → TECHFAIL `0x4d486e` →
**mode-specific advisory dispatch 6→HASROAD / 1→HASFARM / else NOTUNTILTECH** (HASROAD text
substitutes $TECH0 → tech 18 "Monopole Magnets" live via `0x5a69f0` (tech names at
`0x92fdb4+id*44`) + `0x626634` slot table `0x99a01c`; scratch buffers `0x997120`/`0x99a01c` are
NOT state); rejected cleanly — the runner's STORE timeout IS the expected reject terminal state.
Cap table is the gate source (terrain `+18` garbage 527 for cheap modes); MagTube table k=6:
maskSET 0x8, work 3. **As of M41 (live, 2026-10-22): MagTube third mode proven end-to-end**
(`evidence/m41a_*`, `m41b_*`): unlock poke byte `0x985c1c+18 |= 0x08` (TracerPid 0 first) → `r` on
the roaded (45,7) → `TECHCHK mode=0x6 unlocked=1` (gate-pass path = NO advisory, straight to
AFTERLATCH/STORE) → **STORE 0x0a — the STORE writes the REWRITTEN mode** → 4 execs 2295→2298
(`CHECK 2/8→4/8→6/8→8/8`) → `COMPLETE mode=6` → tile mask **0x108006→0x10800e** (magtube bit
0x8), elev untouched (mask swap only), energy 15 flat. **Threshold @ elev 6 = 8 = 2×3+2 ⇒ case-5/6
elev bump is +2 FLAT, not ×2** (road 2→4 fits the same rule). AI side-obs: base 2×`+8` holds
(condenser 24, raise 24, bunker 10, sensor 8, RemoveFungus 12); AI accum +3 on 7 formers, **+2 on
one (idx 51) — not universal**. MASKSET print cap (300) hit for real in m41b (299 prints, our swap
silent — mem readback authoritative). Both runners ran unmodified on the new mode. M42–M44 (same session, 2026-10-22): generic NOTUNTILTECH proven live (`n` →
TECHFAIL → ADVISOR/PANE NOTUNTILTECH; $TECH0 + $TERRAFORMTYPE6 slots closed; tech record +0 =
display-name POINTER, +4 = short token; op-name table `0x94d2f8` = 14 × (land, sea, key-char STRING)
stride 12 — k=8 is **Airbase**, k=9 Sensor Array). M43: base `+4`/`+5` IS the owner player index
(identity, 167/167) — **we own ZERO bases**, all our units `home_base=0xffff`, ~45 orphan-border
tiles; `0x4e3700` works fine (Ghidra short* math), inert for us. M44 (economy idle run,
`scripts/m44_idle.py` v2 + `scripts/m44_probe.py`, evidence `m44d_*`): **our income is 0 AND upkeep is
never charged to energy — energy flat 15 over 12 rounds (2304→2315)**, the HUD agrees (Gross
Income/Total Costs/NET INCOME all 0/turn) ⇒ the 25-cost elev-6 raise is unpayable until a base
exists; AI rates/round Δenergy {1:-1.4 2:-1.3 4:+10.9 5:-0.5 6:+5.3 7:-0.9}, Δminerals {1:+2.3
2:+8.3 4:-11.2 5:-1.9 6:+31.2 7:+1.1} (player 4's near-exact anti-correlation ⇒ unspent base minerals
→ energy ≈1:1, O); **our units 5→2 in that window — the Formers unit (type 1, cls 9) is DEAD**,
survivors = Colony Pod (type 0) @ (45,11) + Laser Squad (type 195) @ (43,11). Four reusable
corrections: (1) **Council/PROPOSAL panes block the pump and their bottom-centre blue OK bar is
unreadable to tesseract** — find it BY COLOUR (band x 240-560, y 430-520, lowest contiguous blue bar
≥8 rows; calibrated rows 488-507 × 268-532, rgb (103,91,181)); the HUD chrome's 1-px blue line at
y 526 exists in EVERY frame, so cap the band at 520. (2) runtime tile record == the map file's two 22-B cells byte-exact; accessors (`0x582ed0`,
`0x5831a0`) are parity-blind on `*(int*)0x92ae14 + (40*y + x>>1)*0x2c` (+0 elev, +8 mask shared by
the pair); a second mask-shaped dword at +0x18 is open. (3) tile **mask bit 0x2 = a unit standing on the
record** (3193/3200, 0 false negatives); full vocabulary from table × op names (farm 0x8000, enricher
0x80000, mine 0x10, solar 0x40, forest 0x200000, road 0x4, magtube 0x8, bunker 0x800, airbase 0x40000,
sensor 0x80000000, fungus 0x20, condenser 0x400000, echelon 0x8000000). (4) **unit type-record base
is 0x98ad88** (name +0[34], ability +32 = 0x98ada8, domain +36 = 0x98adac, plan +42 = 0x98adb2 (the alpha Plan byte — see the M53b type-record bullet; "class" was a misnomer) — the
standing ABSOLUTE addresses are right, but treating 0x98ada8 as the record base pairs each class byte
with the NEXT record's name; type 0 Colony Pod (cls 8), 1 Formers (cls 9), 193 Scout Rover, 195 Laser
Squad; ≥196 runtime types vs 15 alpha `#UNITS` rows. Also **autosaves rotate over all 8 slots**
(30/20/10 every 10 y, then 5/4/3/2/1 yearly) — the "slot 2 = 2198" load note is stale; read the u16 at
file `0x54`. M45 (session 42, 2026-10-22, `scripts/m45_base.py` + `scripts/m45_base.gdb`, evidence
`m45a_*`/`m45c_idle.json`/`m45f_idle.json`): **FIRST BASE FOUNDED** — `b` on the Colony Pod (cls 8)
@ (45,11): `SETTER 0x4d1280` → `BORDERRET -1` → `LIMITRET 12` → `PANE NEWBASE` → `0x4cca50` →
`CREATERET base=73` → `PANE BASEFOUNDED`; n_bases 73→74, our base pop 5→4 (nutrient shortfall =
attrition, not eco-damage), name auto-generated, kit HQ/RecyclingTank/RecreationCommons/EnergyBank/
NetworkNode. Five reusable rules: (1) **Ghidra callee names `FUN_<addr>` are VERBATIM** —
`FUN_005abb40` is 0x5abb40, not 0x45abb40; a +0x400000-shifted bp still ARMS (memory is mapped) and
just never fires, so a silent missing trace line means check the address. (2) **can-act `0x5acc00`
refuses when `unit+4 & 0x4200 == 0` AND order byte `+17` ∈ {1,2,3}** ⇒ poke `+17 = 0` to make a Hold
unit key-able; owner check is `unit+14 == 0x91b5b4`, MP is `0x5ac650(unit) − unit+40`. (3) the
**NEWBASE name pane accepts the generated default with a plain Return** (no typing/click). (4) after
founding the game opens the **BASE screen** (classify kind `base`; RENAMEd/OK row y≈365, outside the
430-520 OK-bar band) — `service_pane` needs a `kind=="base"` → Escape branch (patched; without it a
run spins forever). (5) `objdump` needs `--section=.text` (M49a recipe); file offset = VA − 0x400000 despite the bogus
0x270000 ImageBase header field — pin call sites with a raw E8 rel32 scan. Also: **mask1(+8) bit 0x1000 = "inside a base's claimed
border"** (12-31 pairs per base, hex radius ≈3, pop-independent, 74/74 bases, ocean included) while
the tile owner NIBBLE is a different layer — `0x4e3b50` returned −1 for our nibble-3 tile, i.e. the
~45 inherited orphan nibble-3 tiles are NOT borders; mask bit 0x1 = base-on-pair (74/74, it is what
`0x4e34f0` requires); base `+56` is the constant `0x00dfbe41` (M44's "copied from home base" was
wrong). Economy after founding (16 snapshots 2315→2329): energy 15 ×5 → **19 once at 2320** → flat
19 (0.0/round over the last 9), ≈+0.8/round vs the base screen's own +003 energy/+007 minerals/−001
nutrients; units 1→6 (produced units carry `unit+46` = home base idx ✓) while
energy stays flat ⇒ **unit upkeep never debits faction energy**; a pod base does not make us solvent.
Open: HUD Gross Income/Total Costs/NET INCOME never OCR-able when dialogs/unit panel are up — find
the panel's source fields in memory; and M44's "autosave record == two 22-B cells at +2724" did NOT
reproduce (3200/3200 differ, located pairs fit no stride model) — save-map layout unverified.
M46 (session 43, 2026-10-22): **ECONOMY DECOMPOSED** — upkeep pipeline `0x521070` → `0x5208f0(p)`
(tail `energy -= faction+4; faction+4 = 0` ⇒ **faction `int[1]` is a within-round spending ledger**)
→ income core `0x520540` (gifts, per-base `0x4f5a70`, AI stockpile gated `DAT_00985aec > 3`, trait
bonus) → `0x4f5a70` does `energy += base+0x7e` (transient field, reader only in export, writer = O
computed pointer); facility upkeep is charged DIRECTLY by `0x4f47f0` (auto-sells on shortfall). HUD
Gross/Costs/NET are scratch globals recomputed per redraw by `FUN_00445900` (`0x745734 = Σ base+0xfc`,
`0x744f28 = Σ upkeep`, `0x7457dc` net) and the faction pane `0x49fee0` prints them verbatim ⇒ read
the globals, never OCR those rows. Item upkeep table `0x984d48 + item·0x30` (int0 upkeep, int1 tech),
runtime item = alpha `#FACILITIES` idx + 1, bitmap base+0x8c; the disabled list lives in the player
trait record `0x927a7c + p·0x59c` (+0x20 count/+0x24 types/+0x44 items) and ours zeroes Network Node
(3 − 1 = 2 ✓). Faction records are **2095 ints**, not 2111 (int[2095] = next player's energy). Our
net 0 ⇒ 25 energy never disposable; Corner Market is surplus-gated (energy > max(Σ rivals,1000)).
Blocker that cost 4 runs: the **OPERATIONS DIRECTOR end-turn pane** (Cancel default, OK bar y 215-350,
outside the 430-520 band) — click `(cx,cy+24)` then `(cx,cy+49)` from the OCR Cancel centre; HUD test
is `hud_up` (orange pixels in 600,395,800,425 > 300), not `classify()`. `pkill -f <pat>` matches the
killing shell's own cmdline — bracket the pattern.
M47 (session 44, 2026-10-22): **ENERGY WRITE PROVENANCE** — hw watchpoints DO work here; the
positive control is the year store `0x51f554` in `FUN_0051f320`. Income = `energy += base+0xfc` at
`0x4f5c8c` in `FUN_004f5a70`; facility upkeep = `0x4f4952` in `FUN_004f47f0` (`energy -= cost`, then
`faction+0xe0 += cost`); AI per-base spend = `0x4f2dc2` in `FUN_004f26e0` (direct `add %eax,(%ecx)`,
bypasses the ledger) + a final recompute at `0x506d2b`. **`base+0x7e` does not exist** — Ghidra's
`*(int *)(DAT_008f0d60 + 0x7e)` is typed `short *`, so `+0x7e` = `0xfc` bytes; nothing ever wrote
that region (2 armed rounds, 0 hits). `faction+4` ledger = ACTION-time writers (zero writes over an
idle round for us and for Morgan) — still open. Two hard-won operational rules: (1) six panes block
input while `classify()` still says `hud` — advisor advisory ("Mindworm boil spotted") → Return,
story page / "Book of Planet" → click (400,470), council convenes page → Return, ballot → click the
ABSTAIN word, "MEASURE FAILS" → Return, faction-info table (Tech:/Population:/… ) → click (400,580);
(2) a watchpoint's `$eip` sits just PAST the store (log buffering: see the watchpoint bullet above).
Next (M48): mineral economy (queue a build, watch `base+0x40`); ledger writers on a spending round;
`faction+0x1b8` + research points; player↔faction NAME mapping; the 2320 +4 credit.
**M48d (session 45-46, `scripts/m48d_drive.py`, evidence `m48d2_*`): MINERAL ECONOMY TRACED** —
storage `base+0x40` grows `+= d0` per round UNCLAMPED between completions (AI stockpiles 111→121);
at EVERY production completion storage is then clamped; **M53j/M53k supersede the arithmetic —
completion debits `base+0x40 −= price` (cost factor × `0x4e40a0`) then clamps.**
Scout Patrol cost 10; pop-growth units go through the SAME completion path and need storage ≥ cost
(26 years of storage 0 ⇒ pop grew, unit never spawned); NOSUPPORT disband fires while `d0<0`,
one unit/round, stable at d0=0; `d0=base+0xd0` recomputed every round at `0x4e955d` (pokes die);
`+0x50` carries transient scratch mid-visit; PROGDIV `0x4efd49`/QDRAIN `0x4f1e3f` never fire in
solo; sweep = 75 visits ours LAST, can end early on the year store (open: truncations observed at
21/28/28 visits — the last-visited base, ours, can skip a whole round). Pane printer
`0x483470` = advisories only (Script confirms don't route through it).

**Correction (M28): a plain map click never issues a move.** `FUN_00476580` writes `+17 = 0x18` only when
the map pane's mode is 9 (`[0x8f79e0+0x1ef4c] == &DAT_0091cae4`), which is 0 on the HUD; live clicks
fire `MAPH` and nothing else. Mode 9 is chosen in `FUN_0050a770` as Ctrl held ∧ `0x91b5b8 == 0` ∧
`0x91b6fc == 0`; it stays unreachable under xdotool because `DAT_0068d84c` (active pane index) is −1 —
the pointer never registers as inside a pane even though clicks arrive. That hit-test is the next
cheap test. Clicking a stacked tile still only raises SELECT UNIT TO ACTIVATE.

- **Poking a unit's order fields does not issue the order.** `+17 = 0x18, +20 = dest_x, +28 = dest_y`
poked via `/proc/<pid>/mem` (writable, no tracer) survives a full turn with the unit unmoved: the
executor consumes orders through its own dispatch path, so order fields are outputs, not inputs (a gdb
`call` into the issuer behaves the same — see the last-resort rule above). M53m refinement: order fields
ARE inputs to the ECONOMY sweep — a poked order 3 (Convoy) on a plan-10 type persisted 4 rounds and
drove production accumulation while the movement executor ignored the route-less convoy. Unit slots
SHUFFLE (array compaction) mid-run: locate records by content (faction byte@14), restore pokes at the
record's NEW home.

- **Turn cycle: solved as a harness problem (~100 turns unattended; `references/wine-headless-harness.md`).**
  It was never a game hang — every observed stall was a blocking UI element (units-not-moved confirm,
  OPERATIONS DIRECTOR speech, NETFLASH, tech-breakthrough screen, base screen, Secret Project movie) that a
  one-shot click-then-wait loop cannot answer. Chain of netcode findings:
  (`~/reverse/smac/dplay_solo.md`, `turn_stall.md`): (M3) solo opens NO DirectPlay session, so DP shims
  (dgVoodoo2/nGage/glsmac) can't fix anything; (M5) the idle main thread is a normal yielding PeekMessage
  pump, not a clock-spin or deadlock; (M6b/M7/M8) solo never calls the netcode packet builder `FUN_00584010`
  nor dispatcher `FUN_0052bce0`, **nor the MP end-turn machinery** `FUN_00522240` ("Clearing turn semaphore",
  DONE TURN 0x8301) → `FUN_00521ee0` (end-of-turn semaphore wait loop) → `FUN_00527ca0` (its in-loop pump):
  zero hits across 7 completed turns. **Solo's turn advance runs under `FUN_0050f420`/`FUN_0050ef60` →
  `FUN_0051e700`** (hot: 0 hits idle, ~220–560/s while a turn resolves; drives the `DAT_0091f69x` turn
  semaphore directly, no packets). The old "turn stall" = periodic MODAL dialogs and full-screen interruptions (ABOUT RESEARCH, OPERATIONS
  DIRECTOR speech, NETFLASH, tech breakthrough, base screen, Secret Project movie) blocking the TURN
  COMPLETE click while the game idles in its pump. Next: make the driver give unit/base orders
  (Script.txt-driven) so the AI actually plays; decompile `FUN_0051e700` only if the counters it drives
  stop tracking.
- **Diagnosing a Wine game stall (reusable method)**: sample per-thread wait-state via
  `/proc/<pid>/task/<tid>/{stat,syscall,wchan}` (state=R + climbing utime ⇒ busy-loop, not blocked);
  `gdb -batch -p <pid> -ex 'thread apply all bt' -ex 'info proc mappings'` — but **Wine's stack won't
  unwind past ntdll** (bt stops at ~2 frames: `__kernel_vsyscall` → a libc poll/select wrapper), so use
  gdb `info registers eip` sampling as a poor-man's profiler and map a hot terran.exe `$pc` to a Ghidra
  `FUN_` by subtracting terran.exe's runtime base from `info proc mappings`. Breakpoints on
  `GetTickCount`/`QueryPerformanceCounter`/`timeGetTime`/`GetMessage` reveal what the loop polls.
  `WINEDEBUG=+<dll>` trace helps for some DLLs (`+dplayx` works; `+timer` emitted nothing here). Detail:
  `references/wine-runnability.md`, `~/reverse/smac/turn_stall.md`.
- AI decision logic: diplomacy hub `FUN_00546800` (3924 lines) vs UI plumbing;
  psi-meter gate `FUN_004d6fb0`; turn upkeep `FUN_00520e70`; the host-side
  action-exec branch of dispatcher `FUN_0052bce0` (case 0x4404) is the single
  source of truth for action rules — server and solo alike.
- 0x4040400/0x4050000 cvr chunk handlers exist in exe but in no shipped file.
- Caviar voxel rasterizer exe-verification (27-dir table, normal decoder,
  shade-table light levels) still wiki/corpus-level.
