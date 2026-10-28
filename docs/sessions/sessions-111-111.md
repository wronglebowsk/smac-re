# Session notes archive — sessions 111-111

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 111 (2026-10-27) — M71: WHAT THE COMPLETION'S POP DOES TO THE QUEUE REGION AND THE CURSOR. ACCEPTANCE PASS on one real invocation, reproduced.

**What changed.** New instrument `scripts/m71_pop_watch.py` (pokes minerals and reads it back
BEFORE attaching, arms 4 hw watchpoints — the cursor field `0x6e93dc` + slots 1..3 — and 10
breakpoints on the pop/pay/create/visit sites, drives real round boundaries itself, detaches,
then reads the region back from `/proc/pid/mem`), `scripts/test_m71_pop.py` (**PASS 34/34**:
the shift composition, the parser, both committed real logs, and 10 negative fixtures that
must and do fail), and the NAMED.md M71 block. No threshold, floor or economic term moved;
the only post-run edit to the acceptance was to make gate 2 test the ROUND counter alone
(year is derived from it), which is STRICTER, and both committed logs still pass it.

**Acceptance (one real invocation).** `python3 scripts/m71_pop_watch.py --boundaries 2 --tag
m71pop` -> **PASS** (exit 0). Shape at arm: pending 2, slots `[2,193,192,0,...]`, minerals
poked 0 -> 9 read back, head price 9, cursor field 0, round 51. The window logged, in order:
`VISIT idx=0` -> `PAYA base=0x95da10 storage=9 edi=9` -> `CREATE id=2` -> `POPIN idx=0 pend=2`
-> `POPDEC count=0x9540ba byte=1 head=2` -> `POPAFT byte=0` -> `SLOT1WRITE pc=0x4ef62e` (the
pop shift store `0x4ef62c`) `now=192` -> `POPCNT newpend=1 s0=193 s1=192 s2=192` ->
`POPRES head=193 r=1` -> `POPEXIT`. Round 51 -> 53. READ BACK after detach: pending 2 -> 1,
region `[2,193,192,0,...] -> [193,192,192,0,...]`, cursor 0 -> 0, minerals 9 -> 0, `de84[2]`
1 -> 0. K = 1 = the SINGLE model; the DRAIN candidate predicted `[192,192,192,...]` with
pending 0 — a different region, so the shape discriminated and the read-back chose SINGLE.
**Reproduced**: the same command with `--tag m71pop3` on a freshly reloaded save
(`SMAC_SAVE='m54b_clean.SAV' scripts/m54a_load.py --relaunch` -> `smac_play.py --turns 1` ->
`m66_insert_slot.py --item-a 193 --item-b 192`) -> **PASS**, identical except `PAYA storage=10
edi=9` (the round's `+1` add at `0x4ef7f6` landed before the gate) and minerals 9 -> 1.

**A PASS is not an outcome — read back.** The armed region was written by exactly ONE store
in the window, the pop shift at `0x4ef62c`; `queue[pending]` (slot 2) kept its stale 192
rather than being written, which is why the read-back shows a duplicate. ZERO cursor writes
happened across the whole window, so the completion neither moves the widget's cursor nor
reorders the queue — it left-shifts it, and the `0x4194b3` handler does not fire there. The
queued-count byte was read back at the address the game itself computed (`0x9540ba`).

**The third run is an honest FAIL.** `--tag m71pop2` (head 193, a DESIGNED id, minerals poked
to its price 18 and read back) FAILed its window gate: two boundaries (round 53 -> 55) gave
ONE `VISIT` of the base with `min=18` and NO `PAY`/`POP`/`CREATE`; at the end `+0x3c` = 5,
`+0xcc` (rate) = 0, `+0x30` = `0x80007020`, `+0x98` = 18. Confounded (head id 2 vs 193,
progress, rate) — no mechanism claimed, nothing merged on it.

**Side observations (not gated).** A "the minerals output of University Base is not sufficient
to support Scout" dialog was swallowing chooser clicks: two scripts each clicked cell 1 (194)
and cell 3 (2) and read guard 0 with pending unchanged; after `scripts/m70_clear_dialog.py`
the same cell-3 click read guard 3 and the INSERT worked. Type records read live: `+0x30` =
192 `0x0001`, 193 `0x0041`, 194 `0x0041`; `+0x2c` (owner mask) = 0 for all three — which is
exactly the shape that makes `0x5a73f0` return nonzero and stops the pop's drain.

**Open.** (1) why a designed head did not complete at storage == price; (2) who calls the
`0x4194b3` handler and what widget message `0x4d00` is (it did NOT fire at a completion);
(3) M67's plan-descending LIST order still has no code behind it; (4) the `-3 / -6` table
stride conflict; (5) the pay-site conflict is narrowed, not closed — `0x4efedd` with `edi` =
price is what fires for a UI-queued base-type head at index 0, `0x4f0ca6` is still unexamined.

**Next pick.** M72 = watch the completion GATE, not the pop: arm `0x4f0a37` (`cmp
[base+0x40], edi`), `0x4f0abb`, `0x4f0b4f`, `0x4f0b78` and `0x4efe41` (`cmp ebx,0x40`) on a
base whose head is a DESIGNED id with storage >= its price, and name which test sends the
visit home without paying and what `edi` holds at each. That explains `m71pop2` and closes the
pay-site conflict for the designed branch. Do not re-litigate the pop: it is measured twice.
