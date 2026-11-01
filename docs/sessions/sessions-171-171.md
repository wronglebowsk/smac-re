# Session notes archive — sessions 171-171

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 171 (cont. 16) — doc restructure: the footing file is now an index, the narrative is archived

`NEXT_PROMPT.md` was 15,305 B against a 15,500 cap — 195 B of headroom, and every milestone needs ~600 B of pick text,
so the next batch could not be recorded without deleting findings (three consolidations today were exactly that).
Split instead of shaved: `docs/pick-archive.md` (10,957 B) now holds the M90-M123 milestone narrative and the FULL trap
text; `NEXT_PROMPT.md` (12,936 B) keeps the RULES as 22 one-liners plus the live footing and the closing order.
Headroom 195 B -> 2,564 B (13x). Verified nothing was lost: 21 identifier tokens checked across both files, all present
(0x5a7e7f/0x94d6a4/probe3.py/0x4efe60/TAILOUT/0x93325c/0x6a9480/0x59666d ...); the only "missing" hits were a typo in my
own check (0x93ff3c vs 0x3ff3c) and a name written as FUN_005a6d40 rather than 0x5a6d40.
Also recorded the batch-size finding in BUDGET: 3 milestones comfortable, 5 max when they share one instrument,
box-time milestones 1 per batch.

## Session 171 (cont. 17) — NAMED.md split: the historical middle is archived, the live registry has headroom again

`NAMED.md` was 249,762 B against a 250,000 budget (238 B free), so the next milestone could not be recorded. The
registry's bulk is HISTORY: blocks M32-M84e (sessions 32-133, 52 blocks) are settled findings nobody re-reads to pick
work. Moved byte-identically to `docs/named-archive-m32-m84e.md` (182,747 B); `NAMED.md` keeps the method, `Not yet
named`, and every block from M89 on, and now carries an ARCHIVED pointer telling the reader to grep both files.
**249,762 -> 68,064 B** (181,936 free). Integrity checked line by line: 0 of the moved lines absent from the archive.
Rules that keep this honest: the move is a rename across files in one commit (git records it, nothing is deleted from
history), and the archive names its block order in its own header.

## Session 171 (cont. 18) — M124-M126, three names settled statically (all PASS, zero box time)

`python3 scripts/m124_state_and_memo.py` — SUMMARY M124=PASS M125=PASS M126=PASS (evidence/m124_m126.log).

- **M124 ds:0x926bd4 = the UPKEEP-SYNCH PHASE CODE.** 4 writes and 2 tests in the whole image. `= 1` at the loop entry
  (0x5210aa, right after 0x744f24 / 0x91c658 / 0x91c630 are zeroed), `= 2` after the message at 0x521297 (0x68ea94 =
  **"Skipping upkeep synch"**), back to `esi`=0 at 0x5213c7 after the second (0x68eacc = the same string) with the
  counter `0x91c630` incremented, and `= setne al` (0/1) at 0x57f8c5. **Both readers are `cmp ...,0x1`**: 0x5aaa6f (in
  FUN_005aaa20, after the "Earning a Tech" print) and **0x5aafe4 inside FUN_005aadf0** — the band-flag function, where
  `phase == 1` OR `[fab+0x94d7fc] < 0` skips the tail. So the reason that tail is skipped during upkeep synch is now
  named, not inferred.
- **M125 ds:0x920434 = the ID the window-reset entry publishes, NOT a faction field.** 15 writes, 619 reads, and **12 of
  the 15 writes sit inside a reset sequence** (`mov ecx,0x91db70; call 0x4e25e0` clears the widget object, preceded by
  `[0x91f738]=0xff`, `[0x91f6e0]=esi`, `rep stos`, `call 0x581280`); the stored value is the caller's id (esi/ebx/edi)
  or a constant; **0 references use a faction-scaled base**; the readers compare it against ids (0x546887:
  `if ([eax+0x94d448] & 0x8000000) && (0x920434 != ebx) && ([esi*4+0x92044c] & 2)`).
- **M126 0x59f0c7 = the INVALIDATION of the memoized advance threshold.** `mov [ebx+0x94d800],-1` inside FUN_0059ec90,
  immediately after `[ebx+0x94d650] += [eax+0x927a78]+ecx+ds:0x985afc` and `[ebx+0x94d654] = 0`. Its 3 call sites are
  0x5a0b39 (FUN_005a0aa0), 0x5a123e and 0x5a1277 (FUN_005a0fa0); the first zeroes the DIVISOR `[edx*4+0x94e488]` just
  before the call — so the memo dies exactly when a faction's base count changes.
Method law added to the skill: a small state code is named by the STRINGS printed around its writers.
