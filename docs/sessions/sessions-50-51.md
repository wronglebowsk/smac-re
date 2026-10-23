# Session notes archive — sessions 50-51

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 50 (2026-10-22) — M51a: FUN_004ee410 IS THE WRITER — our base hits the 0x4f271e flag test and never reaches PASTFLAG, so 0x4f26e0 is not its income source; the +0x3c field is set to 40 and then decremented by cc (−3/round) elsewhere

Instrument: `scripts/m51a_drive.py`, 26 breakpoints — gate `0x4f2705`, flag test `0x4f271e`, PASTFLAG,
CONVST `0x4f2d7d`, candidate writers probing `+0x3c`/`+0x40`, and VISIT printing the base **name**.
Runs: `evidence/m51e_*` (1 round, partial: year tick landed after p=7, our pass not captured) and
`evidence/m51f_*` (2 rounds, 2356→2358, 0 OCR passes, clean detach).

**VERIFIED — our base is visited and named every round.**
`VISIT 49 p=3 idx=70 owner=3 nb=74 ours=1 f3c=500 st=200 f38=0xdfbe41 name=Climactic Research`
(evidence/m51f_watch.log:209; again at :504 and :771). The name is printed at each visit, so the array
slide M50b inferred is now directly observable rather than deduced — the record identity follows the
name, and the index moved 71 → 70 between sessions.

**VERIFIED — the gate diverts us; M50a's early-return is real.**
Our base reaches the gate (evidence/m51f_watch.log:228) and the flag test
`FLAGTEST 1 eip=0x4f271e ecx=0x20` (evidence/m51f_watch.log:229), and **never** reaches PASTFLAG:
197 gate hits vs 194 past-flag hits across the run, with zero PASTFLAG lines carrying `ours=1`.
So exactly three bases take the early-return path and ours is one of them.

**VERIFIED — and yet the field changes, from a different function.**
`+0x3c` is rewritten inside `FUN_004ee410` (0x4ee410, 2076 bytes), not inside the converter:
- `W3C_E410D 1 eip=0x4ee82f ... old=500 new=40 pop=7` (evidence/m51f_watch.log:230)
- `W3C_E410ACCR 2 eip=0x4ee8c7 ... old=40 new=37 cc=-3` (evidence/m51f_watch.log:238), then 34 and 31
  in the following rounds (evidence/m51f_watch.log:771)
Static confirmation at the store itself: `0x4ee8c7: mov DWORD PTR [edi+0x3c],esi`, with
`mov ebx,ds:0x8f0d60` (current-base global), `mov eax,[ebx+0xcc]`, `cmp eax,edx; jge 0x4eec23` nearby.

**The M50a/M50b contradiction dissolves.** Both observations were correct about different code:
the converter really does early-return for our base at the flag test, while `FUN_004ee410` separately
maintains `+0x3c`. "Poke survived ⇒ unprocessed" (M50a) and "fields are rewritten" (M50b) are not in
conflict; they were looking at two different writers, and neither invalidates the other.

**OPEN.**
- What produces 40 at `0x4ee82f`: the disassembly near `0x4ee7fa` starts `mov esi,0x19` (25) and then
  does arithmetic with the pop byte at `[base+6]`; read it from the function entry 0x4ee410, not from
  a mid-instruction address (the first attempt at 0x4ee7e0 decoded garbage).
- The gate line prints `st=0` at the same instant VISIT prints `st=200`; the gate's register is not
  `+0x40`. Do not read storage from GATE until that register is identified.
- No `+0x40` writer fired in this run, so M50b's 200→7 is still unexplained. A dedicated watchpoint on
  `+0x40` with the same name printing is the next measurement.

**Harness lessons (both cost real time).**
- The 125B agent session died at ~101k tokens: it crossed the 86,016 compression threshold, compaction
  was refused on cooldown, the model returned empties, and the failure fell through to the configured
  `openvino` fallback at 192.168.1.125:8000, which has been dead since the 258v box moved to .213.
- The driver's pane handlers missed the leader-profile pane, whose stylised font OCRs as garbage
  ("SCO*=CO#D'IPLLMATI¢"), so it fell into the colour row+bar cycle that re-opens the same pane.
  Escape leaves it; keyboard Down+Return closes the 3-row COMM pane. Both are now in the driver.

## Session 51 (2026-10-23) — M52a: the 40 is HALF THE THRESHOLD — `+0x3c := trunc_div2(FUN_004e40a0(owner,0,idx) × (pop+1))` = (10×8)/2 with pop=7; FUN_004ee410 has ZERO +0x40 references in its 2076 B and the armed +0x40 watchpoint caught only the pipeline stores 0x4efee0 / 0x4eff23

**(a) what makes 40 — VERIFIED three ways (static disasm, live-memory recomputation, live bp print).**
- `FUN_004ee410` disassembled from its ENTRY 0x4ee410 (evidence/m52a_fn4ee410_disasm.txt; index.csv row
  `0x004ee410,FUN_004ee410,2076,662`). The store at `0x4ee82f` is `mov DWORD PTR [ecx+0x3c],eax` with
  `movsx edx,BYTE PTR [ecx+0x6]` (pop) → `inc edx` → `imul eax,edx` → `cdq; sub eax,edx; sar eax,1` = signed
  truncating ÷2 (evidence/m52a_fn4ee410_disasm.txt:334-341). **The `mov esi,0x19` at 0x4ee7fa is not the source of
  the 40** — esi (0x18/0x19 from the two `call 0x421fe0` sites) only indexes the message path
  `lea eax,[esi+esi*2]; shl eax,4; mov ecx,[eax+0x984d38]` at 0x4ee832.
- eax there is the return of `call 0x4e40a0(owner, 0, DAT_0068cbb0)` (DAT_0068cbb0 = the current-base INDEX, 70 for
  us). Decomposed (evidence/m52a_fn4e40a0_disasm.txt): event-owner test `(1<<p)&DAT_00985b10` ⇒ esi=10; rescaled by
  `DAT_0092a290` (10, ×/10) and `DAT_0092ada8` (2 ⇒ neither the ×0.9 nor the ×0.8 branch); then
  `score = clamp(faction[p].int[17] (@0x94d694+p·0x20bc) + 2·(base+0x30 byte0 & 4) + 2·(arg2 ∧ facility byte), −2, 5)`
  and `return = (esi·(10−score)+9)/10` (0x4e41f8-0x4e4219). For us fac17=0, f30 byte0=0x00, arg2=0 ⇒ score 0 ⇒
  **factor = 10**.
- So `+0x3c := trunc_div2(10 × (pop+1))`. Live `/proc/PID/mem` at year 2358: pop(+6) = **7** ⇒ (10×8)/2 = **40**, the
  exact value m51f captured (evidence/m51f_watch.log:230 `W3C_E410D ... old=500 new=40 pop=7`).
- Fresh run m52a printed every input at the store itself:
  `W3C_E410D 1 eip=0x4ee82f target=0x962d30 name=Climactic Research old=500 new=40 pop=7 scale=10 ada8=2 fac17=0 f30b=0`
  (evidence/m52a_watch.log:329). 2 rounds, 2358→2360, 0 OCR passes (evidence/m52a_run.out final line).
- The threshold that gates the store: `0x4ee58f` calls the SAME `0x4e40a0` and `imul ebx,edx` at 0x4ee5aa gives
  **ebx = factor × (pop+1) = 80**, and `0x4ee71a cmp [edi+0x3c],ebx; jl 0x4ee8ba` routes progress below 80 straight
  to the accrual tail `0x4ee8c7 ([+0x3c] += [+0xcc])`. **The reset store therefore writes half the threshold**: 40,
  then −3/round (cc = −3): 40→37→34→31 (evidence/m52a_watch.log:337, :608; evidence/m51f_watch.log:238, :509, :777).
- Which branch runs is `pop − flag + trait[p][0]` vs `DAT_0092a2ac` (7) / `DAT_0092a2b0` (14), where flag = 2 iff
  `owner(base[max(DAT_00985b9c,0)]) == owner(ours)`. Live: DAT_00985b9c = −1 → base[0] = "The Rapture" owner 2 ⇒ flag
  0; 7−0+0 = 7 ≥ 7 ⇒ NOT the zero branch ⇒ `call 0x421fe0(24, idx, 0)` (facility byte at base+0x8c+24 = +0xa4 = 0) ⇒
  reset store. The sibling branch (`0x4ee869 [+0x3c]:=0` then `0x4ee875 pop++`, then the 0x4e8d60/0x4e78e0/0x4e92c0/
  0x4e93f0/0x4eaa10 recompute chain) is the pop-growth side.

**(b) who owns +0x40 — VERIFIED.**
- Static: the full 2076-byte body of `FUN_004ee410` contains **no `+0x40` reference at all**; its only non-stack
  stores are `[reg+0x3c]` ×6, `[reg+0x6]` (pop) ×3 and `[ecx+0x7]` ×1 (store inventory over
  evidence/m52a_fn4ee410_disasm.txt). M49a/M50a's "0x4ee410 never touches base+0x40" now holds over the whole
  function, not just the sampled region.
- Live: hardware watchpoint on our base's `+0x40` (name-anchored; 2 DR slots in use, +0x40 and +0x3c) — **2 hits in
  2 rounds, both known pipeline stores**: `WP40 1 eip=0x4efee0 new=190 name_at=Climactic Research ours_at=1`
  (SPENDA, whose store is `0x4efedd sub esi,edi`) and `WP40 2 eip=0x4eff23 new=0` (the CLAMP store), with the static
  writer bps agreeing: `W40_IADD ... old=200 new=200 d0=0` (evidence/m52a_watch.log:310),
  `W40_SPENDA ... old=200 new=190 edi=10` (:311), `W40_CLAMP1 ... old=190 new=0 cap=10 ownmask=3 d0=0` (:319).
  Nothing outside the known writer set fired. m51f logged the same two hits
  (evidence/m51f_watch.log:212, :219, :220, :227) — **session 50's "no +0x40 writer fired in this run" was a log
  misread, not a finding.**
- The clamp is `storage := max(0, min(base+0xd0, cap 10))`, re-confirmed statically at 0x4efee6-0x4eff20
  (`ecx=cap; eax=[esi+0xd0]; edx=min; cmp [esi+0x40],edx; jle skip; event-owner test 0x4eff02; store 0x4eff20`).
  Hence M50b's "200 → 7" (evidence/m50c_watch.log:117 `VISIT ... ours=1 st=7`) is THIS CLAMP1 store with **d0 = 7**
  in that round (min(7,10) = 7); in today's state d0 = 0, so the clamp pins storage to 0. INFERRED for that round —
  m50c armed no d0 print.

**Corrections and opens.**
- `W40_SPENDA ... edi=10` (:311) while the sweep-entry index of that record is 70 (:307 `VISIT 74 ... idx=70`): on
  this path the SPENDA subtrahend is NOT the base index, and `0x4eaa10` is called 20 bytes earlier at 0x4efec4, so
  edi is fair game there. M49a's "index quirk" needs its edi provenance re-pinned (**M52b**).
- IADD fired once in 2 rounds (d0 = 0, a no-op write): the "storage += d0 every round" step is gated upstream
  (IGATE 0x4ef7db), not unconditional.
- GATE still prints `st=0` at the instant VISIT prints `st=200` (:327 vs :307) — the GATE register is not +0x40.
  Unchanged warning: do not read storage from GATE.

Next: **M52b** — edi provenance at 0x4efedb (0x4eaa10 residue vs the 0x4f5aa9 index) and the d0 source at 0x4e955d.
Footing rewritten in NEXT_PROMPT.md (session 52).
