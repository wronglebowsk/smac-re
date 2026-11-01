<!-- Moved verbatim from SKILL.md (M53Q1, 2026-10-24) to keep the always-loaded file small. -->

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
  evidence/*_text.txt.gz` for the line, then `gunzip -c … | sed -n 'A,Bp'` — plain `sed -n` on a `.gz`
  matches nothing and prints an empty window) instead.
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
  it: delete it once the census is written up, or `gzip -9` it in place (~40 MB → ~5.7 MB, still searchable
  with `zgrep`, but still over the gate's 5 MB per-file WARN — that check scans ALL tracked files, not only
  the changed ones; recompress from the decompressed stream, since `gzip` on a `.gz` double-compresses, and
  `xz -9` lands ~3.3 MB if the dump must stay tracked) when a later milestone will re-census the same range
  command in `NEXT_PROMPT.md` so the next session knows the file is regenerable, not data. A `-b binary -m i386:x86-64`
  slice MISALIGNS on SEH blocks (garbage/movabs in SEH-heavy regions like the 0x4efxxx pipeline) — for
  one function use the gdb recipe; Ghidra lumps edi/esi away.
    **Coverage-check every dump**: instructions average 3.8 B here, so `x/2600i` silently stopped 2.4 KB
    short of a 12,298-byte function and M53a drew a WRONG conclusion ("no +0x50 writer in the pipeline")
    from the truncated window — compute the count from `index.csv` size ÷ 3.8 and confirm the last address
    printed equals the next function's start. The same check applies to every WINDOWED reader over a
    saved dump — `scratch/m71/dis.py LO HI` caps its output (400 lines) and stops mid-range with no
    warning, so a grep of a wider range reports "no call site / no writer here" when the sites sit past
    the cut. Require the window's LAST printed address to reach the range end, and re-grep the remainder
    in sub-windows before writing any absence claim.
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
  question, and restate the finding in real byte offsets. The same address can also serve as a VALUE: `DAT_x + off` in pseudocode bases on the pointer STORED at `DAT_x`, while `&DAT_x + off` bases on the address itself — machine `mov reg,ds:ADDR` followed by `[reg+off]` proves value-based (here the tile array hangs off the pointer STORED at 0x92ae14; the faction-record block is a different address, **0x94ae14 + fac*0x20bc**, pinned by two DAT identities: `&DAT_0094d694` = record +0x2880 and `0x94dc2c` production total = +0x2e18, seed dwords `0x94dc34` = +0x2e20 — a footing note that puts faction records at 0x92ae14 is a typo). The same DAT family renders BOTH ways depending on the emitted cast: `(&DAT_0094e488)[fac*0x82f]` is x4-scaled while `&DAT_0094d67c + fac*0x20bc` is a plain byte add — pin every record base with two independent identities before writing a pread script.
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
- **Pseudocode line adjacency is not control flow.** Ghidra merges one variable name across branches, so
  the assignment that feeds a test can sit hundreds of instructions away, in another basic block; reading
  the two adjacent lines as producer-and-test names the wrong producer (and a value read as "the queue
  head" can be a callee's return). Locate the producer in the disassembly: enumerate EVERY write to that
  stack slot (`[ebp-0xNN]`) across the whole function range **in sub-windows** (a window printer caps its
  output), then read the branch that reaches the test. Two corpus handles settle ownership in one command:
  the function owning a pseudocode line — `awk 'NR<=LINE && /^\/\/ ====/ {last=NR": "$0} NR==LINE {print last; exit}' ghidra_out/shard_NNN.c`
  — and a body's line range — `grep -n '^// ====' ghidra_out/shard_NNN.c | awk -F: '$1>N' | head -1`.
- **A sentinel appears in BOTH signed print forms.** `cmp reg,0xffffd8f1` and `cmp reg,0x270f` are the
  same constant (−9999 / +9999): grep the negative AND the positive immediate before concluding a value
  has one consumer, or the branch that acts on the sentinel — usually the one you are hunting — is missed
  while its error path is found.
- A single-writer claim needs the census printed both ways: total references **and** the store count
  (`grep <hex-addr> <dump> | grep -c ',al'`), not "the corpus shows one writer".
- **Census a DAT's stores in EVERY objdump print form.** Accumulator-form stores print
  `mov ds:ADDR,eax` — no `DWORD PTR`, and operand filters like `',al'` miss them; a single-render
  grep can miss the only true writer and produce a false "zero direct stores". Conversely, **zero** stores
  across the whole `.text` census means the DAT is scenario/save-loaded: it cannot vary between visits,
  so stop modelling it as visit-time state and stop arming watchpoints on it. Instructions printed
  after a `ret` may be cold branch targets (a jcc/jmp earlier in the same body jumps past the ret
  into them, inside the same Ghidra function) — grep backward jump refs before calling such a
  store dead.
- **Answer "who owns this function" from the image bytes, not from the pseudocode.** A function that
  `index.csv` gives `n_callers` but that appears in `ghidra_out/` ONLY as its own `FUN_` definition is
  reached through a POINTER, not a `call`: scan the PE file for the little-endian dword of its VA — read
  the section table (`objdump -h programs/terran.exe` gives VMA / vsize / file offset per section) and
  search each loaded section for `struct.pack('<I', va)` in Python. One hit in `.rdata` means it is a
  slot in a dispatch/vtable array; grow the run outward while neighbours still look like code addresses
  to get the table's extent and the slot index. Then scan for pointers INTO that region: hits inside
  `.text` are instructions carrying the table base as an immediate — usually the constructors that store
  the vptr at `[obj]` and, under multiple inheritance, a second one at `[obj+0xNNN]` (the matching thunk
  starts `sub ecx,0xNNN`), which is what turns "no caller" into "slot N of this class".
  If `.text` contains no `call DWORD PTR [reg+0xoffset]` for that slot either, the dispatch computes the
  index at run time (message router / widget handler table) and the caller set is NOT resolvable by
  grepping a displacement — say so instead of grepping three more shapes.
- **Name a pointer argument by reading the string at its VA out of the PE image in Python — no gdb, no box.**
  Parse the section table from Python (`pe = struct.unpack_from('<I', b, 0x3c)[0]`; section headers start at
  `pe + 24 + SizeOfOptionalHeader`, with the size read from `pe + 20` — omitting the optional-header size lands
  the table inside it and yields garbage 'sections'), each entry's `VirtualAddress` is an **RVA** so compare
  against `0x400000 + va`, and only the first 0x20000 bytes of `.data` ship in the file: file bytes cover VA
  0x689000-0x6a9000, everything above is BSS with none. Then `b[PointerToRawData + (va - (0x400000 + rva))]`
  up to the NUL. Run it on every `push 0x…` that feeds a writer call: the pointers pushed before
  `call 0x6267a5` (the tagged record writer) resolve to the exe's record-type NAME table — GOVOPTIONS,
  ASSEMBLEGROUP, AIEDITOR, AIEDITOR2, RULES, SCENRULES, SCENVICTORY, TECHRANDOM, EDITVEH around
  0x6899xx-0x68c8xx / 0x68db28 / 0x691exx — which is what says WHICH record a given staging-slot writer emits
  (`ds:0x99aa38` is the staging dword all of them pack; `FUN_00518c50` is its set/clear-bit helper, arg1 = bit
  index). Before calling such a name a FILE tag, grep the save/scenario files for it: these do NOT appear as
  ASCII in a `.SAV`, which stores numeric tags, so label them the exe's name table.
- **When a multi-gate census script FAILs, find WHICH gate failed before editing anything.** Do not re-run the
  whole script on a hunch: `exec` its source up to the driver loop in a probe namespace
  (`ns = {"__name__": "probe", "__file__": <path>}`, cutting the text at the `only = (sys.argv…` line) and
  recompute each gate condition, printing one boolean per condition. Two reasons this is the fast route: the
  driver loop is not `__main__`-guarded, so a plain import runs every milestone and its `sys.exit(1)` raises
  SystemExit inside your cell — silently, with the prints after it never reached; and a live-box acceptance must
  never be re-spent on an instrument question. Expect the failing conjunct to be your own expectation rather than
  the game's — recount the derived number from the table the last run already printed before touching a floor.
- **Prove an instance exists before spending a live acceptance on a virtual.** Scan every writable
  region of the running process (`grep -E 'rw-p' /proc/<pid>/maps`, read in ~2 MB chunks) for the vptr
  value: zero hits means the class is not instantiated in the current mode, so a window of genuinely
  normal play produces ZERO hits at any of its methods and the acceptance fails for a reason that is
  neither the game nor the instrument. A giant private region is exactly where a big manager object
  lives, so never skip a region for being large. Confirm the object is the one you think it is by
  reading the SECONDARY vptr `[obj+0x444]` (or whichever offset the constructor stores) at the
  breakpoint, and gate on it.
- **Name a global by census, in one read-only probe.** Read the global from `/proc/<pid>/mem`, then walk
  the array the code indexes with it — the stride comes from the disassembly (`imul reg,0x130`,
  `*0x20bc`, `*0xb4c`) and the bound from its own loop guard — and print each record's ASCII name. A
  19-entry stride-0x130 table reading "University Base", "Gaia's Landing", "The Hive" … is the base
  table, and a global compared against those records' first byte is a FACTION index; the comparison site
  plus the names settle the semantics in one call, with no gdb and no pseudocode read. Do this BEFORE
  writing the model that consumes the global — a global guessed as a count when it is an index silently
  inverts every index arithmetic downstream.
- **Jump tables: dump the raw dwords before "correcting" Ghidra's case labels.**
  `struct.unpack_from('<I', img, va - 0x400000)` across the table, entry count checked against the guard
  (`add idx,7` / `cmp idx,6` / `ja`), each target mapped to its body first. A hand-decoded table that
  silently drops one entry yields a mapping that is shifted, self-consistent and wrong — it looks exactly
  like "the case labels are off by one", and only the raw dump (or live data) falsifies it.
- **Re-read the instructions a "dead code" claim rests on — yours or a child's.** `test`/`cmp` set FLAGS
  only, so a `test eax,ecx` followed by `mov [ebp-0x54],eax` stores eax UNCHANGED (the operand, e.g. `1<<j`),
  NOT the comparison result; reading the store as the result manufactures a false "this block never
  executes", and the implementer you hand it to codes out a path the game uses. Verify a dead-block verdict
  against the specific instructions in the disassembly, and **steer the running child with the correction**
  rather than waiting for it to finish and re-dispatching.
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
the memory it is diffing and turns its matches into noise — and the PARENT must not drive a turn or poke
either while read-only children run: schedule any driven before/after re-run for after they return. Give
every implementer child an explicit tool-call cap and output discipline in its spec (no cat over ~150 lines;
long output redirected to `evidence/` then grepped; **append to its notes file after each experiment** so
partial work survives a context truncation) — a child that overruns leaves a patched script and raw run
files but NO notes, so `ls evidence/<tag>_*` and `diff` its script before re-dispatching, and label that
inherited state unverified in the successor's spec.
- **Attribute a model residual to ONE stage before editing any stage.** When the model prints
  per-step contribution tokens per output field, test — for every mismatch row and every field, in a
  script — whether the delta equals the sum of that row's own tokens for one stage. Rows whose delta
  equals their own stage tokens are explained by that stage firing when the game's did not; mismatch
  rows carrying NO tokens from any stage are that stage failing to fire. One such test retires every
  downstream hypothesis (missing branch, wrong multiplier, wrong faction rule) at once, and a
  faction-correlated residual is usually stage geometry (those factions' tiles cluster), not a faction
  bonus. Re-run the test after every model change.
- **Re-run a live-fit model on a driven next round before trusting its residual set.** Snapshot, drive one
  round, snapshot, re-run: unchanged per-field mismatch counts and an unchanged exact-row set while many
  underlying values moved ⇒ the residuals are structural (a missing rule); a residual set that moves ⇒ the
  model was fitting state, not rules.
- **Check whether the code you model RECOMPUTES an input global at its own entry.** A global stamped by the
  first call of the function under study (SMAC: `FUN_004e63b0` rebuilding the scan-pool table `0x8f0ccc`
  → `DAT_008f0d30` at 0x4e78e9, first call of `FUN_004e78e0`) describes only the LAST record the game
  processed, so every other row's snapshot-read input is stale and its deltas are contamination, not rule
  gaps. Discriminate by self-consistency: model's computed output mask == the stored mask it read as input
  (SMAC `mask_in == processed`): report how many rows pass it, and which dump refresh produced the run,
  never a raw exact-match count — that count tracks snapshot coherence, not model quality (19/76 and
  40/76 on consecutive rounds of the same build). Corollary: a
  "scenario constant" label is only earned by a `.text` store census AND a two-snapshot read.
- **Build the mismatch census with a script that opens the report file directly** (`open(path)` inside
  python, not a regex over a line-numbered tool view), and validate the FIELD SET against a real sample
  line before trusting any count: a field regex like `c[0-9]` silently drops `bc` and any field outside
  its class, and a silently dropped field flips a conclusion ("that field matches everywhere"). Print
  per-field mismatch counts and the exact-row count from the same parse so they cross-check, and let the
  script emit the findings table — never hand-transcribe it.
- **To model a function's output from live post-state, reconcile field lifecycles first.** Grep the
field's disp inside the function's OWN asm: a field mutated at ENTRY and rewritten at EXIT is
cross-visit state — the input your model must feed is the observed post-state with the entry mutation
applied (e.g. the base scan-skip mask `&= (~DAT_008f0d30|1)` at entry — read the mask's source from its
`mov reg,ds:ADDR` init, never from a counter computed two instructions earlier; a wrong mask source
shifts every row of the model), and strip any later-stage add that runs
after the target function before comparing (driver-log breakpoint order says which stage is later).
Systematic mismatch: try the raw post-state variant before widening the model.
- **Label snapshot columns from true byte offsets, not from a field wish list.** In a `/proc/<pid>/mem` dump script unpack CONTIGUOUS ranges: skipping unknown gap fields silently shifts every later column, and the mislabeled deltas then appear to contradict proven formulas and send you re-deriving settled facts. Before interpreting any cross-snapshot diff, verify one known record against direct per-offset reads.
- **Before counting a live-memory mismatch, check the row is a real record**: histogram the discriminator
  fields across the whole table — rows whose indices run past the shipped data or whose fields hold
  impossible values are stale/unallocated records, not model failures. Counting them as mismatches sends
  you hunting a writer that does not exist. Same for a pipeline accumulator that never changes:
  histogram the gating fields of the input records first — a filter no record satisfies makes the
  accumulator structurally zero (silent sweeps and watchpoints), not a hidden writer.
- **The unit TYPE table is `0x98ad88 + tid*52`** (stride `0x34`) and it holds **512 records = 8 FACTION
  bands of 64**: `tid = faction*64 + slot`, a faction's designed types fill `band_start..` contiguously
  and every slot past its created count reads all-zero (band 0 = 0..13 shipped types, band 3 = 192..
  ours). A scan/production helper walks `counter < 0x40 ? counter : (counter & 0x3f) + faction*64` over
  0..0x80 and REJECTS a record unless `tid/64` is 0 (shared) or the faction it is processing — so indices
  above 255 are other factions' records, not anomalies, and a census capped at 255 never saw them. The
  sweep `FUN_00572800` takes `(faction, tid, mode)` and its band walk bases on `param_1*0xd00` =
  `faction*64*52`; at `0x5741fe` / `0x574203` `esi` is the **FACTION** (arg 1) while the tid is the second
  argument, so a value printed from `esi` there is not a record index. The flags WORD sits at `+0x30`,
  i.e. byte `tid*0x34 + 0x98adb8`, and bit 2 there is the production-markup switch.
   WHO WRITES IT ON A CREATED RECORD (M81, 4 hw watchpoints, tag `m81write4`): the sweep itself, in the
   visit BEFORE its own 32 B copy at `0x5741e1` — `0x5740f7 call 0x595b10` -> `0x595f82 mov WORD PTR
   [esi+0x98adb8],0x1` (reset to bit 0; the same function also holds `0x105` at 0x595f91 and `0x115` at
   0x595f9c, so the 0x100 marker is an init-time possibility), then `0x574125 or BYTE PTR
   [ebx+0x98adb8],0x40` (bit 6, iff the local `[ebp-0xc]` != 0) and `0x57412c or ...,0x80` (bit 7,
   unconditional on that path); bit 2's ORs are 0x574107 (`eax == -2`) and 0x574117 (`DWORD [0x985aec]
   > 1`). Bits 6/7 semantics are still unexplained. Read it in gdb as
  `*(unsigned char *)($ebx * 0x34 + 0x98adb8)` when `$ebx` holds the tid — `*4` lands in a neighbouring
  record and prints 0, which is misrecorded as "flag clear".
- Commands + patterns: `references/static-store-census.md`.
- Rebuild recipe, pitfalls and export stats: `references/ghidra-batch-export.md`.
- What the install ships (rules text, map format, graphics containers) and what to parse vs
  what to RE: `references/data-formats.md`.

## Byte-exact caller chains (the scan Ghidra shard greps miss)

Containment comes from `ghidra_out/index.csv` (`addr,name,size_bytes,n_callers,shard`); the call
sites come from a regex over `scratch/m574/text.txt` that matches WHOLE call instructions:
`^\s*([0-9a-f]{6,8}):\s+e8\s+((?:[0-9a-f]{2} ){3}[0-9a-f]{2})\s+call\s+0x<addr>$` — the rel32 is
printed as four space-separated bytes, NOT one 8-hex token (an 8-hex group matches nothing and a
"zero callers" verdict from that shape is an instrument defect). Walk up level by level, printing
each site's container + its size + its caller count. Exact for direct calls; misses indirect and
vtable entries, so a zero result must be checked against `n_callers` in index.csv.

## The 0x94d7fc per-faction slot: writers, stride, and the upkeep path into the helper

Static, byte-backed (s139-parallel run; these facts are NOT yet in git main as of PR #92 — the
next closing that rsyncs this skill carries them in):

- `FUN_004f34b0` has EXACTLY ONE call site: `4f5c2e: e8 7d d8 ff ff call 0x4f34b0`, inside
  `FUN_004f5a70` (base-round processor) at +0x1be, 0x5e before its energy-income store 0x4f5c8c.
  Up-chain (each link a matched call): 0x5206d3 in 0x520540 -> 0x52091a in 0x5208f0 -> {0x520d02 in
  0x520c10, 0x521169 in 0x521070 stage 1} -> 0x522a16 in 0x522850 -> 0x46652e in 0x466400 ->
  0x64dd01 in entry (0x64dbe0). So M87's trigger path 4f34b0 -> 5aadf0 -> 5aaa20 -> 5a7970 is a
  PER-BASE UPKEEP tail, not a load path. The call is gated (0x4f34c0 `jne 0x4f35d6`, further gates
  0x4f3511/0x4f3544/0x4f354b, unread) — "runs for every base" is NOT claimed.
- `FUN_005aa880` (pick-next-tech) has 4 call sites: 0x52132f (0x521070 stage 3, "Set Research"),
  0x5aaaab + 0x5aab58 (0x5aaa20: the slot<0 allocate leg, and just before its own store 0x5aab60),
  and 0x5aafee (0x5aadf0, just before that function's slot read at 0x5aaf07).
- The other DIRECT slot writer is `FUN_005102f0` (177 B): esi = faction*8380 (0x5102f8-0x510307),
  calls `FUN_005ab000(faction, 0, -1, 0)` at 0x51035f and stores the returned kind at 0x51038c,
  guarded 0x510369 `jl` / 0x510375 `jl` (slot < 0) / 0x510379 `je` (skip when new == stored). Its
  call sites: 0x499fe3 (0x499e70), 0x51376f (0x512b40), 0x51718b (0x516b80) — two of the nine
  aaa20 callers. `FUN_005ab000` (frame 0xc5c, calls 0x489fd0 then 0x48b9a0 with 4 args) has no
  NAMED row yet.
- Stride: the slot is `0x94d7fc + faction*8380` (2095 dwords/record), confirmed by three lea chains
  (0x5aaa29-0x5aaa45 edi, 0x5102f8-0x510307 esi, 0x5aa8c6-0x5aa8d5 edx=2095f used as
  `[edx*4+0x94d7fc]`). `scripts/m87_aaa20_trigger.py`'s docstring "stride 191 dwords = 764 B" is a
  mis-decode (191 = 2095/11): a /proc read at `0x94d7fc + f*764` returns zeros for f=1..7 where
  `f*8380` returns live kinds.
- Harness trap: `scripts/m54a_load.py` has NO argparse — `python3 scripts/m54a_load.py --help`
  LAUNCHES A LOAD (it relaunched the box mid-M88 in the s139-parallel run). Probe harness scripts
  with `sed -n '1,40p'` or grep their `add_argument` lines, never with `--help`.


## The work-item slot provider chain (M89, byte- and live-backed)

- `FUN_005aa880(faction)` never invents its value: on a solo box (`ds:0x920434 == 0`, so 0x5aa892
  `je 0x5aa9a5`) it pushes 0/-1/0/edi, `call 0x5ab000` at 0x5aa9ac, then 0x5aa9b3 `mov ebx,eax`,
  0x5aa9c5 `lea esi,[eax*4+0x94d7fc]`, 0x5aa9d3 `mov [esi],ebx`, and returns the same value
  (0x5aaa1a `mov eax,ebx`). `FUN_005ab000(faction, 0, -1, 0)` IS the answer to "what value": it
  reserves a 0xc5c-byte local (0x5ab018 `sub esp,0xc5c`), initializes it through 0x489fd0 (0x5ab025),
  then re-pushes its own four args to 0x48b9a0 — a candidate scan, not a constant.
- WHO ASKS and WHEN (`FUN_005aadf0` tail): 0x5aafcf reads `[esi+0x94d7f8]` (exit if < 0), 0x5aafda
  `mov eax,[esi+0x94d7fc] / 85 c0 / 7d 18 jge 0x5aaffc` — asks ONLY when the slot is NEGATIVE — then
  0x5aafe4 `cmp DWORD PTR ds:0x926bd4,1 / je 0x5aaffc`, 0x5aafee `call 0x5aa880`, 0x5aaff6 stores the
  returned value a second time. Because `FUN_005aaa20` writes -1 at 0x5aaac1 right before calling the
  helper, the ask is in the SAME 5aadf0 invocation: live order AAA(fac 2, ret 0x5aaf4b) -> CONS(slot2,
  kind 13) -> ENT(fac 2, ret 0x5aaff3) -> CHR(eax 36) -> ST(slot2, 36).
- 5aadf0 calls aaa20 a SECOND time at 0x5aafbb, after testing `[esi+0x94d430]` bit 0x40 at 0x5aaf7f and
  clearing it at 0x5aafb1 (`and al,0xbf`); it fills a SIBLING slot `[esi+0x94d800]` from
  `FUN_005aab70(faction)` (0x5aaf67 stores -1, 0x5aaf79 stores eax, 0x5aaf02 calls the same provider).
- The value is NOT a type record id: 36, 44, 32, 48, 45 are EMPTY records at 0x98ad88 + id*52, while 3
  Transport Foil, 5 Supply Crawler, 8 Mind Worms, 10 Locusts of Chiron, 13 Unity Foil are real
  ANY-faction units (owner mask 0xff00). Every observed value is < 50; 0x5aaf10 `cmp ecx,0x59` (= 89)
  bounds the domain at >= 89; 0x93325c/68/74 (shorts 10/25/26) is what FUN_005a7970 accepts.
- Harness: `scripts/m89_alloc_census.py` — poke -1 from /proc, 8 print-only breakpoints, /proc read-back
  per boundary. A gdb breakpoint CAN carry convenience variables across stops, which is how the caller's
  return site (`[esp]` at entry) pairs with the store 12 instructions later. Args at a post-`ret` stop
  are at `[esp] .. [esp+0xc]` (cdecl, caller pops at 0x5aa9ba) — printing esp+4..+16 shifts every label.


## The 89-entry TECH TABLE: what the work-item slot value means (M90, live-verified)

- `0x92fdd4 + i*44`, **i < 0x59 (89 entries)** — SMAC's technology table. 8-char key at **+16**,
  prerequisite indices at **+0** and **+4** (-1 / -2 = none / placeholder). Names read from live
  memory (`scratch/m90/txthex.py PID 10 13 25 26 36 45`): 5 Ecology, 10 Alloys, 13 Surface,
  22 AGrav, 25 SingMec, 26 ConSing, 32 DigSent, 36 Integ, 44 IndEcon, 45 IndAuto, 48 Gene, ... User0..User9, TranT.
  Corroboration: Alloys' prereqs are 30 (Solids) + 7 (Chaos) = Alloy Theory <- Solid State Physics +
  Chaos Theory, i.e. the real SMAC tree. `FUN_005a7970`'s table `0x93325c/68/74` (shorts 10/25/26) is
  therefore Alloys/SingMec/ConSing — which is why M86/M87 saw WALK 3, LOOP 0 for ordinary choices.
- The chooser is **`FUN_005aa030(faction)`** (554 B, 3 call sites: 0x48bae4, 0x59cfc8, 0x5a0113): it
  loops `iVar4 < 0x59`, gates each candidate with `FUN_005a6cd0(prereq, faction)`, scores with
  `FUN_005a90a0(index, faction, 0)`, tie-breaks `_rand() % (score+1)` for non-humans (the human faction
  uses `FUN_00625af1`), keeps the max (`local_c`) and returns the INDEX; markers -999 / -1. **M96
  (s151, live 13/13 + 7/7 + 2/2): the max is over the DRAW, not the score — a score-weighted LOTTERY
  (idx72 scaled 2133 drew 5 and lost to idx13 scaled 1408 draw 835); every candidate's score is first
  scaled `<< 8 / max(FUN_005a6d40(prereq1,1), FUN_005a6d40(prereq2,1))` (prereq-CHAIN DEPTH) under the
  gate `ds:0x985ac4 & 0x200` at 0x5aa164 — that gate is NOT the human mask (it fires for AI factions
  too); the human mask byte 0x985b10 only arms the forced pick ([fac*8380+0x94d810]/[+0x94d818] != 0 ->
  the candidate == WORD ds:0x98adee returns un-drawn at 0x5aa251) and swaps the draw to the 0x999fa0
  LCG. Harness: `scripts/m96_human_leg.py`.**
- **`FUN_005ab000` is a thin wrapper**, not a candidate scan: 0x5ab047 `call 0x48b9a0`, 0x5ab04c
  `mov esi,eax`, 0x5ab0bf `mov eax,esi`, ret. Its 0xc5c frame is SEH + 4 C++ locals (destructors
  0x6170f3) — do not read it as a "candidate array". `FUN_0048b9a0` (8514 B, 1 caller) picks the leg:
  `((param_2==0 && (round==0 || !(0x985b10 & (1<<param_1))) || bVar14) && param_3<0)` -> return
  `FUN_005aa030()`'s eax verbatim; `bVar14` = `((ds:0x985ac4 & 0x200) != 0 && param_3 <= 0)`
  (shard_009.c:9343-9347; live ebc 0x1a0e, bit 0x200 SET) — that is what lets a mask-set (human)
  faction take the leg anyway (s151, A030 fac=3 observed landing 0x48bae9). Its call site 0x48bae4, landing **0x48bae9** — the cheapest live probe of the choice.
- Harness: `scripts/m90_tech_choice.py` — poke a slot to -1, 8 print-only breakpoints, then read the
  NAME from `/proc` at 0x92fdd4+idx*44+16. **Pair events by their index in the WHOLE event list, not by
  the index within a filtered sub-list** (m90tech1 FAILed G6 exactly there). A census interleaved into a
  gdb log needs O_APPEND on GDB's own fd; a census snapshots a STOPPED engine, so order events by VISIT.
  A clean reload does NOT carry records created live in the previous session: census before arming.
- Box state that blocks queue acceptances: with University Base minerals 0 / credit 0,
  `m57_ui_enqueue` prints "INSERT 1 never landed" and pending stays 0 — poke minerals/storage first.

## M93 footing: FUN_005a90a0's POST-tail leg 0x5a9698 -> 0x5aa022 (the SCORE minus TAILOUT)

M92 (`m92tail18` PASS 8/8): TAILOUT at 0x5a9698 == BASE + the tail simulated from the per-faction
block; cat byte blk+0x920+esi, mult blk+0x120+esi, div blk+0 read live at 0x5a9503 (je 0x5a9698 = no
tail); cat7 `mult*Tc/div` gated bc!=0 AND non-human (gate fail FALLS THROUGH to the band leg); cat2
`mult*Tc*4/(div*(1+human))`; cat0 `mult*c*Tc/(div*(1+human))`, c=2 iff [0x94dc44]>=[0x94dc58] (at
+0x7fc/+0x810 from 0x94d448) else 4; else band edi=1..7 gated [esi+0x950664+edi*0x8380]!=0 and ctrl
[0x94d448+fac*8380+4*edi] bit8 set and not (bits0-1 set w/o bit5), adds `mult*Tc/(div*(1+human))`.
The block is FROZEN within a round (0/39 + 0/19 per-TAIL-hit 64+64 B dumps differ from the
candidate's own round snapshot; div cross-check 39/39 bad=0) and moves BETWEEN rounds.

STATIC (bytes read s146 via scratch/m71/dis.py): 0x5a9698 `mov eax,[ebp+0xc]` (fac) `mov ebx,[ebp+8]`
(idx) `test eax; jle 0x5a96e6`; `cmp ebx,-1; je 0x5aa022`; `cmp ebx,0x58; jge 0x5a96e6`; eax = rec
prereq1 (`[ecx+0x92fdd4]`, ecx=[ebp-0x10]): `cmp eax,-1; jl 0x5a96e6`; `cmp [ecx+0x92fdd8],-1` then
`cmp eax,-1; jne 0x5a96e6`; 0x5a96d0 `mov al,[ebx+0x985c1c]; and al,dl (fac bit); neg; sbb; neg;
test; jne 0x5aa022` — the leg is SKIPPED when [0x985c1c+idx] carries the faction's bit; else 0x5a96e6
`call 0x5312d0; test eax; je 0x5a9744`; 0x5a96ef `mov eax,ds:0x985a9c`, `test ebx; jl 0x5a9744`,
`test eax; jl 0x5a9744`, `cmp ebx,eax; je 0x5a9735`, else `lea ecx,[eax+eax*4]; lea esi,[eax+ecx*2];
shl esi,2` (= eax*44 record stride — the s146 "48-vs-44 conflict" was a misread: 11*4 = 44),
`mov edx,[esi+0x92fdd4]; push 1; push edx; push ebx; call 0x5a9020` (a comparator), 0x5a9718
`add esp,0xc; test eax`.
RETRACTION (s147, from full bytes 0x5a9747-0x5aa022): the s146 note "the 0x5aa022 block makes
final = tailout*5, the +4 lands only when idx==0" is WRONG — those bytes are 0x5a9ff8 (human x3/x2)
and 0x5aa014 (x2+4 when ebx!=0, ebx being a scan flag by then, not idx); the apparent x5 deltas are
the CASCADE below. 0x5aa022 is just `mov eax,[ebp-0x4]; pop; ret`.

THE CASCADE (s147+s148, ACCEPTED m93post3 PASS 9/9 — 13/13 finals, nulls split 11/13; full table in
NAMED.md M93 block): from 0x5a9747 the acc = tailout runs a chain of apply-if-INSIDE gates;
`0x5a9020(a,X,f) != 0` iff a is in the depth-f prereq expansion of X (f=0 equality, f=1 {X,pr1,pr2},
f=0x270e full closure). Stages in address order: A x3 (47, cl 0x9305e8/ec) B x2 (61, 0x930850/854)
C x2 (64, d2 0x9308d4/8d8) — all behind [0x94d71c]>0 AND [blk+0x94d810]!=0; D x2 (35, d1 0x9303d8/
0x9303dc); E x2 (59, cl 0x9307f8/7fc; entered when [blk+0x94d818]!=0 OR [0x92adbc]==0); FIM
x(2*(1+[blk+0x94d81c])) (validator rec+4 bit1, mask[0x985c1c+idx]==0, ac4 bit 0x200 clear); then
[0x927a8c+fac*1436]>0 -> x2 via 0x98582c closures, else 0x93325c/0x933268 (x2,x2) + +1@0x5a99cc +
x2@0x5a9a21 (closure legs); q=[blk+0x94dc28]/clamp([blk+0x94e488],1,0x270f) ADDED if q>[blk+0x94d81c]
and idx in closure(0x984fec/0x984fbc/0x98531c/0x98534c); K1 x2 key [0x9851cc] / K2 x3/2 key
[0x9851fc] (K2 also needs round>250) behind [0x927a80+arg2] > 0 — arg2=0 at tail calls, live 0;
era table 0x92b954 x21 (flag=[e-4], id-word=[e]): idx==id -> x3 (x4 if ebc&hmask) ELSE idx==pr1/pr2
(id) -> x2 (x3 if ebc) — legs EXCLUSIVE per entry, constants not table words; x3@0x5a9df3 when the
89-tech scan (runs when [blk+0x94d814]!=0 or [blk+0x94d81c]==0) hits esi==idx with validator+mask
clear; x2@0x5a9eb5 (x4 if ebc&hmask) when idx in {0x98adee + its prereq closures}; band region
0x5a9f83+ (x3/x6 human @0x5a9ff8, x2+4 @0x5aa014 when ebx!=0): contributed x1 in every traced run
(PBH 5 events, PS2p4 0). TIMING LAW (m93post2 FAIL 8/9 -> post3 PASS): 0x92adbc, the era table,
designed prereq fields and demand dwords move BETWEEN the 0x51f320 boundary snap and the ladder —
dump 0x927a00-0x933300 + 0x984f00-0x98b000 AT each TAIL hit (m93_post_census tailx1/tailx2) and
re-read demand there (d814t/d818t/d81ct); M92's within-round freeze covers only the 0x94e488 block.

CENSUS LAWS (s146, m92 harness): a gate may only read a field the harness SETS (G8 read c["tdiv"],
never assigned -> structurally False for 4 runs); pair tailout/tailbyidx FIRST-wins (a re-scan in a
later round has a different block); simulate each candidate from the round LIVE at its own BASE hit
(windows opened by a CALL can span rounds); the tail census needs a FRESH load — at r59 only 3 AI
factions had queued items -> 0 qualifying windows.

## Unit-record type field — settled (moved from SKILL.md s150)
**Unit-record type field — SETTLED: the u16 at `+10`. `+4` is the flags dword.** An earlier
version of this paragraph claimed type@`+4` and `+10`=flags; that was wrong, and `FOOTING.md`
("type byte@4") and `SAVE_FORMAT.md` ("`+10` is a flag word") have been corrected to match.
Proof is the accessor, not a screen correlation: the class table is indexed with
`*(short *)((int)&DAT_00933282 + rec_off) * 0x34` (`shard_012.c:2150`; same shape at `:2117`,
`:2148`, `shard_001.c:4153`, `:4312`, `:9466`) and `DAT_00933282` is `UNIT_ARR + 0x0A`. The
screen agrees — a selected record reads "Scout Patrol" on the panel with `+10 = 2`. `+10`
values of 128/256/320 mark EMPTY STALE SLOTS: filter `type < 24` (and x/y in range) before
counting a record as a unit. Movement/order fields (`+0/+2`, `+17`, `+20..+35`, `+40`) were
never in doubt — pokes the game obeyed validated them.

Two rules that generalise from how this one went wrong:
- **Settle a field's identity from the binary accessor, not from which candidate looks plausible
  on a dump.** Grep the table base (`grep -n '98adb2\|933282' ghidra_out/*.c`), then read the
  cast: `*(short *)((int)&DAT_x + off)` gives the WIDTH and the OFFSET at once, and the code that
  consumes it names the semantics. A correlation over live records only ranks candidates.
- **Never compare candidate offsets on a state you already know is degraded.** The "`+4` wins
  117/119" measurement was taken on records sitting in limbo after the faction lost its bases,
  where the flags byte reads 0 on most records. Re-run layout questions on a freshly loaded,
  healthy save, and do not let a format doc outvote code that demonstrably works.


## Objdump/census parse rules (moved from SKILL.md s150)
**Parse an objdump line by its TAB fields, never by the text after the colon:** the machine-code bytes
- Write census gates as `\s+` regexes, never exact padding: exact single-space patterns miss objdump's mnemonic padding, so a gate written with literal spaces silently matches nothing (s174 hit this while writing `m178_m180_scratchband.py`).
- **objdump prints the operand decorations in CAPS and the address WITH its `0x`:** a class of `[0-9a-f]+` stops at the `x`, so `dword ptr ds:[0-9a-f]+` never matches `DWORD PTR DS:0x985ac4` — write `ds:0x[0-9a-f]+`. And lowercase the whole line before a store census: a case-sensitive `^mov dword ptr ds:X,` silently drops the uppercase stores. s174's hand census of `0x99aa38` reported 28 stores in 10 functions; the corrected instrument found 33 in 14, and the 4 missed writers are the AIEDITOR2 / ASSEMBLEGROUP / EDITVEH / TECHRANDOM whole-value restorers — an undercount is what makes "nothing else writes this field" look true.
sit between the address and the mnemonic, so `line.split(":")[1].startswith("mov")` matches NOTHING and a
whole-function scan silently reports zero stores — take the LAST tab field for the mnemonic. An
address-keyed scan must require the shape `^[0-9a-f]{6,8}:\t` before `int(x, 16)`: the section header
line `00401000 <.text>:` also starts with hex and raises `ValueError` mid-parse, killing the census
before it arms. Import
`scratch/m71/dis.py` under a non-clashing module name (`importlib.util.spec_from_file_location`), because
stdlib `dis` shadows the plain `import dis`.

**Match instruction TEXT with `\s+`, never with the padding you see in the raw dump.** The census helpers
(`field_census.INS`, `name_global.py`) normalize mnemonic padding — raw objdump prints `test   eax,eax`
(3 spaces) where the corpus holds `test    eax,eax` (4), and a `jmp`/`je` row is indistinguishable from a
`jmp`-suffixed register by exact string. So a gate written as an exact-string `in` test silently never
matches and the milestone FAILs on its own harness: write gates as regexes with `\s+` between mnemonic and
operands (`re.search(r"test\s+eax,eax", window)`), and when a gate does fail while every printed number is
right, suspect a spacing or format-string bug in the harness before touching the floor. The sibling trap: a
finding sentence built with `"%d" % x` needs exactly as many conversions as arguments — one extra `%d` in a
concatenated string raises `TypeError: not enough arguments for format string` mid-run and loses the whole
census printout, so count conversions in the SAME pass that writes the script.


## Production pass FUN_004ef6d0 dispatch + pay sites (M95, s150, VERIFIED m95pay4)
Queue loop at 0x4ef88b: q0==-38 return; q0>=0 -> branch A: price 0x4efa4d/0x4efa52 (edi), gate 0x4efa5e
cmp [base+0x40],edi; tid<0x40 skips the M74 mark block (0x4efe41); pay 0x4efed8-0x4efedd `sub esi,edi;
mov [ecx+0x40],esi` (storage!); clamp 0x4eff20 = min(cap 0x92a370, credit d0)/0 iff storage>max(cap,d0)
&& human owner; mirror +0x98 0x4eff2c; create 0x4eff4e -> 0x5ab650; POP call 0x4ef5d0 at 0x4f037b
(pending store 0x4ef648). q0<0 -> typecode=-q0 (0x4ef89f); branch B (gate 0x4f0a3d) iff tc>=39 &&
claim[tc-39](0x985b3c)==-1, or tc>34 (0x4ef94a), or 0x507410 mask fails (0x4ef985); race scan
0x4f0af0-0x4f0b72 (+4-shifted reads: [esi+0x4c]=queue0, [esi+0xcc]+[esi+0x3c]=credit+storage) defers
(0x4f0c28, no store) when a competing human base can pay; 0x4f0b80 jg 0x4f0ca1 SOLE B-pay entry; B pay
0x4f0ca6 SAME field; claim store 0x4f0d83; B POP 0x4f0f46. No back-edge B->A. Credit +0xd0 feeds only
the income add 0x4ef7f6 (gated q0!=-38 && !(flag30&2) && d0>=0) + the clamp. Stale tail: non-sentinel
q0 with pending 0 re-pays + CREATEs phantom units while storage>=price; POP then stores no pending.

## Base income recompute FUN_004e93f0 — base+0xd0 credit (M97, s152, VERIFIED m97credit3 PASS 11/11)
eax = ds:0x8f0d60 = the CURRENT BASE RECORD pointer. Called per base EVERY ROUND from FUN_004f5a70 (the
per-base turn stage: call 0x4f5ad2 after the queue pass 0x4ef6d0, call 0x4f5b46 after 0x4e8d60/0x4e78e0/
0x4e92c0; FUN_004f5a70 itself called at 0x5206d3) and from the recalc helper FUN_004eb6b0 (call
0x4eb6db; runs whenever arg1 != 0, many UI callers from 0x40b232). Stores: 0x4e953e [+0xf0] =
DAT_008f0c38 + DAT_008f0c4c (WHOLE-FACTION upkeep — one facility anywhere raises every base's upkeep);
0x4e9557 [+0xd0] = [+0xc0] - [+0xf0]; 0x4e9562 [+0xe0] = 0; 0x4e957f [+0xd0] -= [+0xe0]; 0x4e9590
[+0x94] = [+0xd0] (display copy). GROSS [+0xc0] is rebuilt from 0 every call by FUN_004e78e0 (reset
0x4e79a8, +1 per facility 0x4e7c19, +1 at 0x4e85c1) then 0x4e9525 = ((facCount+2)*[+0xc0])/2. Only SIX
stores to `[reg+0xd0]` exist in .text: these two + 0x5ba9e8 (base-creation zero sweep +0xa0..+0xe8),
0x6310c6/0x631154 (record init), 0x6315e2 (=0) — so 0x4ef7f6/0x4eff20 (which write [+0x40] storage) are
NOT credit writers. gdb LAW: a hardware watchpoint only REPORTS a VALUE CHANGE; count stores with silent
bps AT the store instruction — scripts/m97_credit_watch.py (4 hw watchpoints on a row's income chain +
bps at 0x4e9557/0x4e957f, register-only condition `$eax==row`).

## M98 (s153): `[fac*8380+0x94d800]` is the ADVANCE THRESHOLD — a memo of FUN_005aab70(faction)

- FIVE references to 0x94d800 in all of .text: reads 0x593483 (FUN_0058fa40,
  `FUN_005aab70()/2 <= [fac*8380+0x94d7f8]`, shard_013.c:35399) and 0x5aab8f (aab70's own cache
  read); writes 0x59f0c7 `= -1` (FUN_0059ec90), 0x5aaf67 `= -1` and 0x5aaf79 `= eax`
  (FUN_005aadf0's grant path, `call 0x5aab70` at 0x5aaf71 between them).
- `FUN_005aadf0(faction, p)` (per-base upkeep tail 0x4f5c2e FUN_004f34b0 <- FUN_004f5a70 <-
  0x5206d3): `[+0x94d7f8] += p` — the AI legs 0x5aae04-0x5aae71 WOULD double p, the human never, but NO
  faction doubles live (M99 retraction: 0x5aae1a `call 0x5312d0` returns 0 single-player);
  if (netgame || slot >= 0) { t = aab70(fac); if (slot > 0x58) acc += p; if (t <= acc) {
  print "Researched Advance"; FUN_005aaa20(fac) consumes the work-item slot; FUN_0047f590(fac,
  item); acc = 0 @0x5aaf5c; field = -1 @0x5aaf67; field = aab70(fac) @0x5aaf79 } }; the
  `[+0x94d430] & 0x40` leg prints "Secret Advance", clears the bit and consumes a SECOND item.
- aab70(fac) returns the memo UNCHANGED when it is >= 0; only the -1 leg recomputes:
  L = clamp([+0x94d804]*2 - [+0x94d790] + [+0x94d78c], 2, 9999); v5 = L/2; human =
  (1<<fac)&[0x985b10]: x = [+0x94d438] -> 4x+8, mul = 3; AI: x = era (+1 if < 3) -> 29-3x,
  mul = era; v2 = 12-v5 replaced by min(x, v5+12) when it is <= both; cap = ((v2+x2)*mul)/10+1
  with x2 = ((ac4&0x20|0x40)>>5 * v2)>>1 clamped by v5 - [0x985afc]/((ac4&0x20|0x40)>>3);
  m2 = (((max7/2 - mul) - v5)+7)/(8-mul) clamped by cap, max7 = max over facs 1..7 of
  ([+0x94d78c] + 2*[+0x94d804]); v5b = clamp(v5 - sign([+0x94d728]), 1, 99999);
  res = clamp([0x92a390]*v5b*((v2+x2)-m2)/56, 1, 99999999) after the [0x92a298] and
  [0x927a88+fac*1436] percent legs and +50% iff ac4&0x20.
- GHIDRA REASSIGNS local_8 to 3 (human) / era (AI) before the `*local_8/10+1` cap AND the
  `(8-local_8)` divisor — using the clamped L there gave 68/101/151 where the game holds
  64/77/166. Two other C translations that bite: the comma test
  `((v2 <= x && v2 <= v4) && (v2 = x, v4 < x))` ASSIGNS x to v2 and then tests v4 < x; and
  `iVar7 + (uint)(iVar7 < 3)` is a +1 when the value is below 3.
- Harness `scripts/m98_advance_budget.py`: silent bps at 0x5aaf5c/0x5aaf67/0x5aaf79 + 0x59f0c7
  + the aab70 ENTRY (arg is `[esp+4]` — the prologue has not run, ebp+8 is the CALLER's frame),
  one HARDWARE watchpoint on a faction's field, `--arm-facs 1-7 --arm-by 1` pokes the
  accumulator to field+1 per boundary to arm the grant, `--predict` prints the model table
  without touching the game, and gdb is detached only after cur_player returns to the human.
- Three laws this milestone paid for: a watchpoint REPORTS `store_pc + instruction length`
  (0x5aaf67+10 = 0x5aaf71, 0x5aaf79+6 = 0x5aaf7f, 0x59f0c7+10 = 0x59f0d1) — gate on those, not
  on the store addresses; the turn driver RETURNS WHILE THE AI UPKEEP IS STILL PLAYING, so a
  detach at rc=0 loses the last recomputes (unlogged stores, read-back mismatch); and gdb's
  detach noise `Thread N "terran.exe" received signal SIGINT` + `[Switching to LWP n]` has to
  be whitelisted before a parse gate can be green.


## M99 — the advance accumulator's input (FUN_005aadf0's param_2)
`FUN_004f34b0` (per-base upkeep tail, called at 0x4f5c2e from FUN_004f5a70, once per base per
round) is the ONLY caller of `FUN_005aadf0` in .text (call 0x4f35cb; the callee's return pc is
0x4f35d0). Chain: raw = `[base_record+0x104]` (0x4f34d9, DAT_008f0d60) -> halved 0x4f3513 when the
`FUN_00507410(0x17)` policy leg fires (`[0x95da9c + fac*0x130 + idx] & mask`) -> zeroed 0x4f3546
(round < mult*-5) or 0x4f3556 (round < 5 && `[fac*8380+0x94d438]` < 2) -> `[fac*8380+0x94dc30] +=`
raw (0x4f3560) -> `scaled = (clamp([fac*8380+0x94d6a4],-5,5)+10) * raw * 10` (0x4f3582-0x4f3590) ->
`[fac*8380+0x94d808] += scaled%100`, and if that exceeds 99 `scaled += 100` (0x4f3597-0x4f35b2) ->
`param_2 = scaled/100` (magic 0x51eb851f imul + sar 5 at 0x4f35b8) -> push, call. Inside
FUN_005aadf0 `param_2 <= 0` returns at 0x5aaffc (no store); otherwise `[fac*8380+0x94d7f8] +=`
(0x5aaeeb) — **no doubling live**: 0x5aae1a `call 0x5312d0` returns 0 single-player, so 0x5aaec1
never runs. Second live writer of the accumulator: `FUN_0056df40` 0x56e024 `inc [ebx+0x94d7f8]`.
`[fac*8380+0x94d6a4]` and `[base+0x104]` are RECOMPUTED every round (pokes undone; +0x104 by
FUN_004eaa10 called at 0x4f5ad7). Harness `scripts/m99_param2.py --tag t --boundaries 2`.

## M100 — the research multiplier [fac*8380+0x94d6a4] = SLOT 10 (last) of the 11-dword block `&DAT_0094d67c + fac*0x20bc`
- WRITER **FUN_005a15a0**(p1 = `[fac*8380+0x94d658]`, p2 = the block, p3 = fac, 0, p5): reset `rep stos`
  0x5a15b3 (a watchpoint reports 0x5a15b5); category accumulate `mov [edi],eax` 0x5a16d9 (reports
  0x5a16db); source accumulate `add [eax],edi` 0x5a179e (reports 0x5a17a0, only when p5 == 0); clamps
  over `&DAT_00927ac0` rows (type 4 -> clamp 0..999, type 10 -> halve if <0); +1 to slot 5 iff
  DAT_00985b70's base is this faction, +2 to slot 2 iff DAT_00985b98's is.
- ROWS: 11 dwords at `&DAT_0092babc + cat*0xd4 + rec*0x2c`, rec = `*(int*)(p1 + cat*4)`, cat = 0..3.
- SOURCE ARRAY: `[fac*8380+0x94d700]` (11 dwords). Blocks: A 0x94d67c (mult = slot 10), B 0x94d6a8,
  C 0x94d6d4; FUN_005a1830 also shifts 4 dwords at 0x94d668 and calls 15a0 on A, B and C (p5 = 1).
- CALLER **FUN_005a1830(fac)** — `call 0x5a1830` at 0x4dbf8e and 0x520904 inside **FUN_005208f0** (the
  per-player turn sequence, the family of FUN_00556690 @0x52094f). Runs once per faction per round, in
  that faction's own segment (live cp == fac 16/16 at 0x520909).
- CONSUMERS (all LOADS, which is why no store mentions 0x94d6a4): 0x445abf, 0x4aac96 (clamp(-5,5)*10+100
  build-time scale), 0x4f352e/0x4f3566 (FUN_004f34b0's param_2 scale, M99), 0x56dffa (FUN_0056df40's
  `mult*-5 <= round` gate on the acc +1 at 0x56e024).
- HARNESS: `scripts/m100_mult_watch.py` (4 hw watchpoints on the multiplier + CALL bp 0x520909 + READ bp
  0x4f352e; pokes facs 1-7 to live+10 before each boundary; `--predict` prints the baseline table).
  `m100mult2` PASS 13/13, m54b_clean r52->54.

## M102 — FUN_005a15a0 internals at slot 10, verified AT the store sites (m102hit3 PASS 14/14)

- LOOP SHAPE: after the `rep stos` reset, a 4-category outer loop (cat 0..3, idx = p1[cat]) wraps an
  11-slot inner loop (`edi` and the row pointer `[ebp-0x8]` both `add 4` per iteration, counter
  `[ebp-0x10]` = 0xb), so 0x5a16d9 executes 44 times per rebuild — once per (slot, category); a
  register condition on the slot-10 BYTE address selects exactly 4 hits. At the hit `edi` = dest byte
  address, `ecx` = the row dword, `eax` = old + ecx (add at 0x5a16d7). D-add loop 0x5a1799-0x5a17a4:
  11 iterations, `eax` walks the block, `edi` = the D dword; at 0x5a179e `eax` = dest, `edi` = value.
- CLAMP/ADJUST TABLE at `0x927a9c + fac*1436`: count dword, then three PARALLEL dword arrays — types at
  `+0x20`, keys at `+0x40`, values at `+0x60`. Type 4 = clamp block[key] 0..999 (ALWAYS stores, even
  unchanged), type 10 = halve-if-negative (ceil; stores only when < 0); types 5/6 are per-category
  ADJUST legs: `key == cat && value == idx` mutates the CURRENT slot by -/+ row[slot] BEFORE the
  0x5a16d9 add, so adjustments are baked into `old` read at the hit. param_5 != 0 skips the D-add, era
  and clamp legs together (0x5a1712 jumps to the ret tail at 0x5a181d).
- CATEGORY-SKIP leg (0x5a1601-0x5a1671): a category skips its slot add iff row[slot] < 0 AND
  (cat,idx) in {(3,1),(3,3),(2,1)} AND the era byte matches the faction — (3,1) tests
  `*(uint8 *)(0x95da14 + 304*ds:0x985b90)`, (3,3) and (2,1) test `... * ds:0x985b9c`. Those globals are
  BASE INDICES; `0x95da14 + 304*b` is base record b (rows at 0x95da10, stride 304) byte `+4` = its OWNER
  FACTION. Era globals read -1 live (r50-r57), which makes the leg inert.
- LIVE (m102hit3, m54b_clean r55->57, 15 silent bps, NO pokes — bps fire on EXECUTION, so watchpoint
  suppression is moot): 36 CAT + 9 DADD events, every stored == old + src AT the hit, every chain
  0 -> final, cp == fac 45/45, CLAMP 0 events == predicted (no key-10 entry on any faction), final ==
  /proc {1:-2,2:0,3:2,6:-2}. Harness `scripts/m102_rebuild_at_hit.py` (`--predict` prints live inputs +
  prediction table; M102_WFACS=; group events BACKWARD from the CALL bp — see instrument-laws).
- **THE D ACCUMULATOR DOES NOT ACCRUE PER-ROUND**: 0x59ec00/0x59ec90 — the only displacement stores to
  `[fac*8380+0x94d700]` — logged ZERO events across two complete rounds while every D slot held its
  value. A "+10 per faction per 2 rounds" drift seen on the idle box came from a trigger the driver does
  not reproduce, or from a POINTER-form writer the displacement census cannot see: the writer of
  `[fac*8380+0x94d700]` is OPEN — answer it with watchpoints on the D slots, not greps.

## The per-faction record block (M104: bytes + live reads + the save image)
`0x927a9c + fac*1436` = the count dword, then three PARALLEL stride-4 arrays of 8 slots each: TYPE at +0x04, KEY at +0x24, VAL at +0x44 (FUN_0059ec00 anchors on +0x24 and reads TYPE at [p-0x20], VAL at [p+0x20]; the 0x20 spacing is what caps the list at 8 entries). TYPE==3 -> D[KEY] += VAL (M103); TYPE 4/10 are FUN_005a15a0 clamps; TYPE 7/8 do inc on D slots 17/18 at 0x5a78e7/0x5a78f2. NO store in .text reaches count/TYPE/KEY/VAL by displacement — all 46 mentions are scan-loop loads or cmps (0x40d9f4 0x4e4cd9 0x4f37b3 0x4f3e5d 0x4f47ba 0x4fcdf3 0x508c50 0x522ad4 0x589089 0x5a0087 0x5a0443 0x5a1689 0x5a78d0), so ask who-writes-it of a HARDWARE WATCHPOINT on the count dword. The list is LOAD-TIME data: a .SAV carries the block verbatim at the same stride (m54b_clean.SAV fac0 base 0x10e18, fac1 0x113b4, fac3 0x11eec, fac6 0x12fc0) and nothing appends it during rounds (m104w3 PASS 12/12: 0 count-change events over 3 boundaries while a control watchpoint on the same faction logged 6 writes), so D — and the research multiplier D leg — is FROZEN after scenario setup.

## The DIALOG class (M201-M202): ctor FUN_00405ef0, vtable 0x67164c, run method FUN_005f1394

`FUN_00405ef0` (99 ctor sites in 90 functions) is the constructor: `call 0x5ee350` (the this+0 subobject),
`add ecx,0x3230; call 0x5f6b8c`, then `mov [eax],0x67164c` (0x405f31) and `mov [ecx+0x444],0x671644`
(0x405f3a) — the object carries a SECOND (CPane) vtable at byte +0x444. `FUN_005f1394` (11,207 B, 94
direct calls, 0 data references to its own address image-wide, one exit `ret 0x8` at 0x5f3f58) is the run
method, and at 90/94 sites `this` is the CALLER'S STACK OBJECT. It is the only reader of the label pool at
0x698e40 ('OK' 'OK' 'Cancel' 'OK', alternating) — i.e. it is the OK/CANCEL dialog. Fields: flags dword
+0x30a8 (18 mentions, all loads — the tests are `and reg,imm` after the load), sub-dialog pointer +0x285
(byte +0xa14), item count +0x858 (byte +0x2160), result dword +0x290 (byte +0xa40) read ONCE at 0x5f3f45
and written by no site inside the pump (37 candidate writers image-wide — the writer is OPEN). Slots
dispatched on *this, read out of 0x67164c: +0x4=0x406750, +0x8=0x4068a0, +0x30=0x406970, +0xdc=0x5ce5bd,
+0x15c=0x406990, +0x160=0x404e70, +0x164=0x407060, +0x16c=0x407280, +0x170=0x407660 — but the table also
holds the class's `return 0` stub 0x404ed0 in ~40 slots, so "that slot is a stub" is a live possibility:
READ the entry, do not assume. The +0xdc method FUN_005ce5bd (`ret 0xc`, 3 args) CALLS its arg2
(`cmp [ebp+0xc],0` 0x5ce6bd, `call dword ptr [ebp+0xc]` 0x5ce6c3), so the pump's arg2 is a caller-supplied
callback; only 17/94 sites supply one and both addresses (0x530d70 x16, 0x530db0 x1) are code islands in
the 0x530d45-0x530df0 gap — no index row contains them, `fnof()` answers "?" and a containment census
loses them, so grep the gap by address. Return domain {0, -1, [this+0x290], pass-through}: 0
`mov eax,imm` in 11,207 bytes, 5 `xor eax,eax`, 2 `or eax,0xffffffff`, and `mov eax,ds:0x698d0c` whose
dword IS 0xffffffff (the image has exactly 1 reader of that dword and it is here).
