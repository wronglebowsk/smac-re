## Findings (most important first)

1. **P1 — `NAMED.md` (M317 SHAPE row)** — claim `1 ret` is marked `V`, but no gate pins ret count.  
   What is wrong: `scripts/m317_engine_decides.py:128` prints `ret sites`, but the only G2 assertion is `assert not indirect` (`:134`). A second `ret`, or a mutation deleting the sole `ret`, stays green.  
   Why it matters: repo law requires each VERIFIED claim to be read by a shipped gate and made red by mutation. `1 ret` is not.

2. **P1 — `NAMED.md` (M317 CONTEXT row)** — claim `upkeep FUN_005208f0: 005551e0->ENGINE->005a1ad0, 985ae8-gated` is marked `V` on C5 evidence, but C5 does not read any of that.  
   What is wrong: C5 (`scripts/m317_engine_decides.py:270-286`) only prints that `FUN_005208f0` is the containing function, its size, instruction window length, and pushes before `0x52094f`. It does not check `005551e0`, `005a1ad0`, ordering around the engine, or any `0x985ae8` gate.  
   Why it matters: the claim describes caller context/control-flow/gate behavior; the cited evidence only identifies the caller. This is a false VERIFIED citation.

3. **P1 — `NAMED.md` (M317 ISSUE row)** — claim `a/d/s coords=base+0/+2` is marked `V`, but only one of the three sites is actually traced.  
   What is wrong: the coordinate assertion is only at `0x556820` for `ebx/edi` from `[esi+0x95da12]`/`[esi+0x95da10]` (`scripts/m317_engine_decides.py:245-246`). Evidence for `0x556831` and `0x55698e` prints `<crosses-call>` for the coordinate registers (`evidence/m317_engine_decides.txt:124-138`).  
   Why it matters: the claim says `a`, `d`, and `s` goals all use base coordinates at `+0/+2`, but the harness only proves the `d`-site. A mutation changing the `a`/`s` coordinate loads would not redden this gate.

4. **P1 — `NAMED.md` (M317 ISSUE row)** — claim `n6@556e79(p [94d430+blk*8380])` is marked `V`, but the block scaling / source array is not gated.  
   What is wrong: C4 pins the kind at `0x556e79` as `0x6` via `KIND_AT` (`scripts/m317_engine_decides.py:213-215, 222-226`) and prints that one register came from `[ebx+0x94d430]` (`evidence/m317_engine_decides.txt:170-177`), but it does not assert that `ebx` is `block*0x20bc` or that the operand really resolves to `0x94d430 + block*8380`.  
   Why it matters: the measured fact is “some store site mentions displacement `0x94d430`,” not the prose claim “priority is `[94d430 + blk*8380]`.” The scale and base are outside the instrument’s proof.

5. **P1 — `NAMED.md` (M317 SHAPE row)** — claim `abs x20` is marked `V` from C1, but the instrument never reads `abs`.  
   What is wrong: C1 only enumerates direct call targets and asserts total callee/call-site counts (`scripts/m317_engine_decides.py:156-165, 307`). It prints `FUN_0064b870 x20`, but does not pin `0x64b870` as `abs()` or assert its count.  
   Why it matters: the byte-level measurement is “20 calls to FUN_0064b870,” not “20 `abs()` calls.” If the `FUN_0064b870 = abs` identification is not itself part of this milestone’s gate, the SHAPE claim is not VERIFIED by C1.

6. **P2 — `scripts/m317_mutate.py` / `scripts/m317_engine_decides.py` (C5 caller context)** — mutation harness cannot prove the caller-context claim.  
   What is wrong: `C5` prints caller A context (`scripts/m317_engine_decides.py:275-285`), but no mutant alters `0x52094f` context, `FUN_005208f0`, `0x985ae8`, `005551e0`, or `005a1ad0`. The only C5-related assertion is the loop-bound containment at `0x59dd43` (`:272`), and no listed mutant targets that either.  
   Why it matters: under the mutation rule, a gate that stays green under its own mutation is decoration. This makes the CONTEXT row’s “985ae8-gated / upkeep chain” claim especially weak.

7. **P2 — `scripts/m317_engine_decides.py:189-207`** — the backward reaching-def tracker is too crude to support “direct” / “read back from band” claims in general.  
   What is wrong: `reg_source()` scans backward only for `mov`, `lea`, `movsx`, `movzx`, `pop` where the first operand equals the target register, and stops only at `call`/`ret`. It does not treat arithmetic/logical/shift/string/call-clobbering effects as defs, does not stop at other writes to the register, and inspects the register at call time rather than at push time.  
   Why it matters: C4 uses this helper to claim coordinate/base/owner sources (`NAMED.md` ISSUE/CANCEL rows). If a real code path clobbers `edi`, `ebx`, `esi`, etc., via an unmodeled instruction or after the push but before the call, the printed source is not a sound reaching definition. A mutation changing such a def could remain green or produce a misleading “proof.”

8. **P2 — `NAMED.md` (M317 CANCEL row)** — claim “56d890@5597a5 (1 local arg)” is marked `V`, but the local-arg provenance is not pinned.  
   What is wrong: evidence shows `arg1 = eax <- mov eax,DWORD PTR [ebp-0x4] @0x5597a1` (`evidence/m317_engine_decides.txt:180-182`), but the gate only asserts `0x559E8E` and `0x559809` are in `issue_sites` (`scripts/m317_engine_decides.py:237-238`) and checks kinds/owner/knockout/remover for other sites. It does not assert that `0x5597a5` calls `0x56d890`, nor that its single pushed value comes from `[ebp-0x4]`.  
   Why it matters: the claimed “1 local arg” is a specific decoded fact; the shipped assertions only prove that some issue-site count contains the knockout/remover sites.

9. **P2 — `NAMED.md` (M317 ISSUE row)** — phrase “cost gate 4cc7b0 first” is marked `V`, but C4 does not pin the cost-gate ordering.  
   What is wrong: C1 prints `FUN_004cc7b0` calls at `0x556a0f` and `0x558ab3` (`evidence/m317_engine_decides.txt:33`), but the instrument does not assert the local sequence around `0x556a4a` / `0x558adc`, does not tie those calls to the `^41` goal issue sites, and does not check that the gate precedes the goal push/call.  
   Why it matters: “first” is an ordering/control-flow claim. Counting callee sites elsewhere in a 14 kB function does not read the claimed fact from bytes.

10. **P2 — `evidence/m317_mutate.txt` + `scripts/m317_mutate.py