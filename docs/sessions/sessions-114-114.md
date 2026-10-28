# Session notes archive — sessions 114-114

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 114 (2026-10-27) — M73: WHAT `edi` AT THE `0x4efa5e` GATE IS MADE OF. ACCEPTANCE PASS on one real invocation, and the split is MEASURED, not inferred.

**What changed.** `edi` is `A x B`. `A = FUN_004e40a0(owner,1,-1)` (measured 9 = Python
`cost_multiplier`), `B = FUN_005ac950(head,[0x68cbb0],0)`. For a DESIGNED head `B` is NOT the
cost byte: `B = byte(+0x29) + trunc_div(C*P+50,100)`, `C = FUN_00595ad0(type)`, `P` the option
dword picked by `[0x92ae81 + 144*type[+0x24]]`. Measured live: head 194 `C 3`, `P 50` -> markup 2
-> `B 5` -> `edi 45` where `price_of` says 27. The markup is skipped WHOLE when `type < 0x40` OR
`type[+0x30] & 4` (test at `0x5ac99c`, early return `0x5aca9c`), and that flag is live STATE: in
the accepted run 193 read `0x41` at arm and `0x45` at its first visit, giving `edi 18` = `price_of`
— M72's 27 and this run's 18 are one id in two states, and neither contradicts the other.
Two writers of the bit are known statically (`0x4eec30`, `0x4d20f0`, both unit-transformation
paths); neither is yet correlated with the observed flip (next pick).

**Acceptance.** `python3 scripts/m73_price_split.py --ids 193,194 --boundaries 4 --tag m73split4`
-> **PASS, 10/10 gates**, `evidence/m73split4.gdblog`: head 2 `A 9 B 1 edi 9` pay+create, then
head 194 `FLAG f30=0x41` -> `PRICE_C P=50 byte=3 C=3 ret=0x4efa52` -> `PRICE_M Mpre=2` ->
`FACTORB A=9 B=5` -> `POSAFF storage=111 edi=45` -> `PAYA` + `CREATE`, then head 193
`FLAG f30=0x45` -> `FACTORB A=9 B=2` -> `POSAFF edi=18` -> `PAYA` + `CREATE`. Queue
`[2,194,193]`, storage re-poked and read back before every boundary.

**Tooling.** `scripts/m73_price_split.py` (11 breakpoints incl. the `0x5ac99c` decision point,
pre-attach candidate set read from live memory, per-boundary storage re-poke, controlled
`type[+0x30]` poke with read-back, 10 gates) and `scripts/test_m73_split.py` -> **28/28**. Three
runs failed on the INSTRUMENT, not the game (no `PRICE_B` rows; the flag flipping mid-window),
which is what forced the decision-point breakpoint; the claim was then built only from rows that
exist. `scripts/m73_price_split.py --help` documents `--no-repoke` / `--no-poke-flags`.

**Open / next pick.** (1) M74: WHO sets `type[+0x30] & 4` and when — conditional breakpoints on
`0x4eec30`/`0x4d20f0`, the 8 flagged ids read before/after ONE designed completion. (2) The
facility path's three no-pay exits (`0x4f0a42`/`0x4f0b86`/`0x4f0c28`) still need a NEGATIVE head.
(3) M68 (acceptance failed) and M63 (no PR) remain unmerged. (4) The `income 1` accrual case from
104/105 is still open.

**Process (this is the new part).** The session before this one died in the closing, not in the
milestone: context reached 259,232/262,144 tokens and Hermes could not compact (`auxiliary.
compression: provider: auto` -> the same 262k model, summaries `finish_reason=length`,
`summary_truncated_failure`, aborted after 132 s, 4x). `NEXT_PROMPT.md` now opens with a BUDGET
section (tool-call checkpoints at 25/30-40/40-50, terse closing past 150k tokens, doc writes <= 2 KB
appended, `SESSION_CURSOR.md` written before any long step) and the closing order was rewritten to
match. `SESSION_CURSOR.md` is new and is the resume record a cut turn leaves behind.
