# Session notes archive — sessions 174-174

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 174b (2026-10-31) — process pass (no new findings; one claim corrected)

- **SKILL.md cap triage (it sat 36 B under its 70,000-BYTE hard cap).** Split, not shaved: the two procedural
  subsections "The context ceiling is part of the task" and "Close before you hand off" moved VERBATIM into
  `references/session-discipline.md`; SKILL.md keeps a 6-bullet RULES digest (budget bands, 3-invocation cap,
  close order, doc-write laws, split-dont-shave, sibling sessions) plus the pointer. 69,964 -> 54,902 bytes,
  ~15.1 KB of headroom; the reference carries the full trap text. Skill synced to `skill/` (gate: skill sync PASS).
- **The s174 writer-call claim was overdrawn and is now corrected + asserted.** The call is `(name, size, extra)`
  and the sizes are NOT uniform: of the 9 stores that feed `0x6267a5`, 7 pass size **0x41** and the TECHRANDOM
  pair passes **0x1** (0x510289 / 0x5170ae), all with extra=0; EDITVEH is a SECOND record write in FUN_004dde00,
  not the call that follows its store (that store's next call is 0x64b9e0). `m178_m180_scratchband.py` now prints
  the triple table and gates `0x41 x7, 0x1 x2` — re-run: `SUMMARY M178=PASS M179=PASS M180=PASS`, rc 0.
  SESSION_NOTES/NAMED.md M178-M180 and NEXT_PROMPT's pick paragraph carry the corrected text.

## Session 174c (2026-10-31) — box relaunched, first live probe of the M178 staging dword (inconclusive)

- **Box up** after a relaunch that took >9 min on a cold prefix: terran.exe pid 319926, year 2153 round 53,
  University Base (28,42), 6 units HELD, TracerPid 0; `sudo -n python3 scripts/smac_preflight.py` PASSes every
  invariant.
- **New operational law:** the relaunch was killed at a tool timeout and the game came up parented to wineserver,
  not to this session; `yama ptrace_scope=1` then refuses `/proc/<pid>/mem` to the SAME uid
  (`PermissionError` at `smac_preflight.py:56`). Read under `sudo -n`, or relaunch from a tracked background job.
  Written into skill `references/wine-operations.md` ("A relaunched game is NOT your child").
- **M181 probe (live, NOT a finding):** a 2 ms sampler (`scratch/m181/pair.py`: `ds:0x99aa38`, `ds:0x920720`,
  `ds:0x9204b0`, `[0x94d600+3*8380]`, `ds:0x8f0d60`, round/year/cur_player) ran across one boundary driven by
  `m55_boundary.py --settle 0.4`: round 52->53 (+1 exactly), year 2152->2153, cur_player walked the whole player
  loop 3->4->5->6->7->0->...->3, `selobj` churned 11 values. `ds:0x99aa38` stayed **00000000** the whole window —
  consistent with M178's static reading (a UI/scenario writer) — but `ds:0x920720` and `ds:0x9204b0` were also 0
  and static, so the aggregate pass had nothing to aggregate and the probe has NO positive control.
  `m55_boundary.py` itself exited rc=1 on its accounting gates. Falsifier for the next run: arm the sampler, then
  trigger a save or a governor-options OK — a staging change there confirms the writer's trigger; no change
  anywhere means the address or the sampler is wrong.

## Session 174d (2026-10-31) — M182-M184, all PASS (static batch of three, one instrument)

`python3 scripts/m182_m184_bandrecord.py` -> `evidence/m182_m184_bandrecord.txt`, `SUMMARY M182=PASS M183=PASS
M184=PASS`, rc 0.
- **M182 — ds:0x99aa1c is the BASE of the record 0x6267a5 emits.** 14 dwords are referenced in
  [0x99aa1c, 0x99aa5c]; the 13 packers touch exactly FOUR (+0x0 0x99aa1c 637 stores = the generic write-bytes
  argument, +0x4 0x99aa20 637, +0x1c 0x99aa38 33 = the flag dword M178/M179 mapped, +0x20 0x99aa3c 5) and
  +0xc..+0x18 (0x99aa28/2c/30/34) are written ONLY by the emitter FUN_00626b46 (+0x24 by it plus the 0x626xxx
  siblings; +0x30..+0x40 by the 0x627xxx serializers). The 0x41 size pushed with GOVOPTIONS equals the span
  0x99aa1c..0x99aa5c — INFERRED alignment, not proven.
- **M183 — the four whole-value writers are not packers** (each stores the scratch once, vs 9-19 legs): 0x4dc390
  is a RESTORER (17 `test al/ah,imm` scratch-bit tests, 1 mask op) — the mirror of 0x4dc100's 24 pack ops;
  0x4d9ae0 copies bits 0..11 of 0x58e760's return through `shl edx,cl / test eax,edx / or|and esi,edx / inc
  ecx / cmp ecx,0xc` (12 iterations); 0x512b40 computes a `setne` boolean and asks FUN_00518c50 with indices
  1/2/3 (3 call sites) instead of building a mask; 0x4dde00 builds from [esi+0x93327c] tests and pushes EDITVEH.
- **M184 — FUN_00535c60 is a per-faction VISIT wrapper**: 3 call sites in 2 owners (FUN_004266c0 x2 passing
  ds:0x91b5b4 + [ebp-0x14] + eax; FUN_00545c50 x1 with (esi, 0, ebx, eax)); its first 40 insns call 0x531df0 ->
  0x530e30 -> 0x535940 IN THAT ORDER, then fold arg1 with the 2095-dword chain into [ebp-0x14] and test
  `[eax*4+0x94d448] & 0x40030`.
