# Session notes archive — sessions 54-54

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 54 (2026-10-23) — M53c: the dequeue IS A CALL, NOT A STORE — FUN_004ef5d0 pops the head; the pipeline calls it at 0x4f037b whenever the base's owner is in the event mask (otherwise it re-picks via 0x4e5ae0); +0x4c is the PENDING-entry count (entries = +0x4c + 1), and with +0x4c == 0 NOTHING consumes the head — a payable head re-completes every round

**Runs:** `scripts/m53c_drive.py --tag m53c --rounds 3 --budget 1100` — 3 rounds 2366→2369, **0 OCR
passes**, clean detach (`evidence/m53c_watch.log` last line, `evidence/m53c_drive.json`
`detached:true, ocr_passes:0`); confirmatory `scripts/m53c2_drive.py --tag m53c2 --rounds 2 --budget
700` — 2 rounds 2369→2371, 0 OCR, clean detach. Both poked (TracerPid 0, pre-arm) `+0x50=2` (Scout
Patrol), `+0x54=3` (Transport Foil), `+0x4c=1` (a legal TWO-entry queue), `+0x3c=500, +0xcc=1,
+0xd0=200, +0x40=200` (`evidence/m53c_drive.json` poke events). Our base = idx **70** @ 0x962d30
(`(0x962d30-0x95da10)/0x130 = 70`, `evidence/m53c_drive.json` final.base).

**0. M53a's "no +0x50 writer in the pipeline" was an artifact of a TRUNCATED dump** (VERIFIED).
`evidence/m53a_fn_disasm.txt` has 2601 lines and its last instruction is 0x4f1d5d — 2,600 insns cover
only 9,869 of the 12,298-byte function (avg 3.8 B/insn), so 0x4f1d5d-0x4f26da was never disassembled.
Re-dumped: `evidence/m53c_tail_disasm.txt` (0x4f1d50 → 0x4f299f, past the function end at 0x4f26da).
It exposes the tail re-pick call 0x4f1e01 (`evidence/m53c_tail_disasm.txt:61`), the tail clear
`mov DWORD PTR [eax+0x50],0xffffffda` @ **0x4f1e3f** (`:73-80`) and a third re-pick 0x4f21b8 (`:277`).
Pitfall: size the dump from `index.csv` size ÷ 3.8, or bound it by the NEXT function's address.

**1. THE POP PRIMITIVE = `FUN_004ef5d0(base_idx)`** (0x4ef5d0, 244 B, `evidence/m53c_fn4ef5d0_disasm.txt`,
Ghidra `shard_012.c:20538`), register-level:
- `esi = idx·0x130`; gate `eax = [base+0x4c]; test; je 0x4ef684 → return 0` (`:12,:16`) — **nothing
  pending ⇒ the head is NOT consumed**.
- if head ≥ 0: `dec BYTE PTR [0x94de84 + owner·0x20bc + head]` (`:20-27`) — the consumed item's
  per-player item count (the same count `0x4e5560` maintains).
- **the shift** `0x4ef628-0x4ef639`: `edx = [slot+4]; ++i; [slot] = edx; slot += 4; cmp i, count; jl`
  → runs `count` iterations, i.e. `slot[i-1] := slot[i]` for i = 1..count, writing **+0x50 first**
  (`:32,:34,:38`).
- `base+0x4c -= 1` @ 0x4ef642 (`:41`).
- validate the NEW head: `0x5a73f0(item, owner, base)` for items ≥ 0 (`:48`) / `0x5a6e70(|q|, owner,
  base, 0)` for negatives (`:58`); if unavailable → `jne 0x4ef5fa` (`:64`) **pop again** (discards
  stale/unavailable pending entries until one validates or the count hits 0).
- new head ≤ −39 → `0x446250(0x24)` (project command recorder, `:73`); then redraw
  `0x473760(base_x, base_y, 2, 2)` (`:82`) and `return 1` (`:84`).
Its callers are ONLY three sites inside the pipeline: **0x4ef992, 0x4f037b, 0x4f0f46**
(`evidence/m53a_fn_disasm.txt:195, :827, :1611`; Ghidra `shard_012.c:21026, 21283, 21493`).

**2. LIVE, run 1 (m53c):** QPIPE st=200 head=2 count=1 (`evidence/m53c_watch.log:144`) → QCOMPLET
(`:145`) → SPENDA cost_edi=10 (`:146`) → CLAMP1 st=190 (`:147`) → **WP50 `eip=0x4ef62e` Old 2 → New
3** (`:154`, gdb's own Old/New block at `:151-153`) → **WP4C `eip=0x4ef648` Old 1 → New 0** (`:161`).
Later visits of the same run: head **3**, count 0, st 0 (`:260`, `:312`) — the promoted slot-1 item is
what the base now builds, and `+0x44` mirrors it (`f44=3`). ZERO hits at all six re-pick sites and at
the tail clear 0x4f1e3f (counts in the log: REPICK_* 0, QDRAIN 0).

**3. LIVE, run 2 (m53c2) pinned the call site:** `POP_MID 1 f50=2 f4c=1` at **0x4f037b**
(`evidence/m53c2_watch.log:38`) fires immediately after CLAMP1 (`:37`) and immediately before the
shift store (`Old value = 2 / New value = 3 / 0x004ef62e`, `:42-45`); `POP_EARLY` (0x4ef992) and
`POP_LATE` (0x4f0f46): 0 hits. Year 2370→2371, next visit head 3 / count 0 (`:47`).
**The fork that chooses pop vs re-pick** (file-target gdb disasm, 0x4f033e-0x4f037b):
`[base+0x30] |= 0x800000`, `[base+0x30] &= 0x7fffffff`, then `mov bl,[ebp-0x2c]` (= 1<<owner, set at
0x4ef815) `mov al,[0x985b10]` `test bl,al` → **nonzero (owner IN the event mask) → 0x4f0375 `push
base_idx; call 0x4ef5d0` (POP); zero → 0x4f0367 `push 0; push base_idx; jmp 0x4f0589` → `FUN_004e5ae0`
(RE-PICK)**. Our owner 3 ∈ mask 0xff08 ⇒ pop path ✓ (and REPICK_A @ 0x4f0589 = 0 hits in run 1).

**4. +0x4c REINTERPRETED — it is the PENDING-entry count, not a "last used index"** (M53a's label,
corrected). Total entries = **+0x4c + 1**: head at +0x50, pending at +0x54 … +0x54+4·(count−1); the UI
caps count at 9 ⇒ 10 entries = the +0x50..+0x73 array ✓. Every drain agrees: `0x4ef5d0` shifts
`count` slots then decrements; `FUN_004f4060` iterates `[+0x4c]+1` dwords from +0x50
(`evidence/m53c_fn4f4060_pseudocode.txt:269-278`), and `FUN_005437d0` (`evidence/m53c_setters_pseudocode.txt:176-198`)
and `FUN_00507ef0` (`:199-217`) both loop `base+0x4c + 1` times over the same window decrementing item
counts. Consequence, **closes M53a open (a)**: with `+0x4c == 0` nothing consumes the head — 0x4ef5d0
returns 0 at its gate — so a payable head re-completes EVERY round (M45's units 1→6 off one standing
queue; M53a's head=2 unchanged over 3 rounds). The standing item a player sees IS the repeat-build
state; the queue only advances when the player has appended pending entries.

**5. Census of +0x50 writers** (static, `evidence/m53c_setters_pseudocode.txt`; live counts from
`evidence/m53c_watch.log`):
- `FUN_004e5560` (`shard_012.c:14625`, excerpt `evidence/m53c_setters_pseudocode.txt:1-44`) = the ONLY
  setter: head := new, early-return if unchanged, item count old−1 / new+1; its only callers are the
  3 sites inside `FUN_004e5ae0`.
- `FUN_004e5ae0(base, param2)` = "re-pick the head" via `FUN_004f6030` (the 30,475-byte AI build
  planner, `shard_012.c:24338`) — excerpt `:45-129`. Live: 122 SET_REPICK + 122 SET_HEAD hits in 3
  rounds over 40+ bases (idx 47 ×29, 46 ×9, 74 ×6 …), **0 for idx 70 (ours)**. New heads observed:
  85/153/149/72/84/164/152 (facility ids ≥ 0x40) and **−29 ×7** — a negative outside the −(39+project)
  band, unexplained.
- `FUN_004e46f0` (base-creation autocalc: writes 2, then scans the 52-B type records for the best
  pick, excerpt `:130-175`) and `FUN_004e47d0` (base init) seed +0x50.
- Clears/re-picks that did NOT fire for us: `0x507ef0` 1 hit, base 46, not ours
  (`evidence/m53c_watch.log:247`); `0x5437d0` 0 hits; tail clear 0x4f1e3f 0 hits (needs head == −|q|
  ∧ +0x4c == 0); pipeline re-pick sites 0x4ef87e / 0x4f0589 / 0x4f08d4 / 0x4f09b6 / 0x4f1e01 /
  0x4f21b8 all 0 hits (0x4f1e01 needs (f38&1 ∧ f38 sign) ∨ owner ∉ mask; ours f38 = 0x00dfbe41).
- UI enqueue `FUN_00417ee0` (0 live hits — no base-screen interaction this run) writes ONLY slot 0
  (`shard_001.c:9452`, excerpt `:218-251`) and adjusts +0x4c (`:9258` dec, `:9429/:9434` set/inc, cap 9).

**6. Ops lessons.** (i) The `ours=` flag printed at the 0x4e5ae0/0x4e5560 entries is USELESS: while
those run, `*(int*)0x68cbb0` (cur base index) IS their param_1, so it is always 1 — compare against
the located base INDEX (ours = 70). (ii) Both drivers ran clean with 2 hw watchpoints + 17 soft bps
(`scripts/m53c_drive.py`, `scripts/m53c2_drive.py`); the +0x50/+0x4c watches replaced +0x3c/+0x40 and
gave gdb's own Old/New pairs, which is the cheapest possible writer proof.

**7. Opens.** (a) **Who writes the PENDING slots +0x54..+0x73?** No function in the corpus writes
base+0x54 by symbol (`DAT_0095da64`: 0 hits) or by short-alias (`DAT_008f0d60 + 0x2a`: 0 hits); the
append must come through a walked pointer. Leads: `FUN_00417ee0`'s pane callers
(`shard_001.c:2155, 2204, 8535, 12265`) and `FUN_0059ce10` (`shard_015.c:14416, 14770`), which seeds
`+0x4c = pop·10/2` (= 35 at pop 7 — over the UI cap 9, so either that path is scenario/load setup or
the cap means something else). (b) the −29 head value. (c) the branches at 0x4ef992 / 0x4f0f46 (never
fired in either run). (d) base+0xc0 = 7 == pop, still unresolved.

Next: **M53d** (the queue APPEND: who writes the pending slots, via the base-production pane callers of
`FUN_00417ee0`), or **M53b** (the +41 byte: production weight vs the autocalculated +43 cost). Footing
rewritten in NEXT_PROMPT.md (session 55).
