# Session notes archive — sessions 95-96

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 95 (2026-10-25) — M57-3: the gate ran on a GAME-filled queue and got 1/2 — the model premise is falsified, nothing merges

**What changed.** `scripts/smac_preflight.py` (NEW, read-only orientation: authoritative address
table, game alive, TracerPid/gdb, our bases BY NAME with index/coords/pending/head/minerals/income,
unit decode, /tmp + evidence budget; `SMAC_PID` override is the negative test). `m56_build.py`:
credit arithmetic printed BEFORE a --ui-queued run; the boundary watch now breaks when the walk is
HOME (was a fixed settle, which either missed the walk or swallowed the next flip); and it answers
the "SOME OF OUR UNITS HAVE NOT YET MOVED" confirm via `smac_play.answer_confirm` (that dialog takes
NO Return — a 240 s run sat on it, year frozen). `m57_ui_enqueue.py` restores orders mode (0 makes
every order key a no-op and the turn never ends). Sampler throttled to 2 ms + the 1.4 GB of traces
downsampled to ~10 KB (the gate's 30 MB budget). Skill synced.

**The acceptance, unchanged.** `python3 scripts/m56_build.py --ui-queued 18 --boundaries 8 --timeout
240` on a fresh `m54b_clean.SAV` box (2154), Korolev Center [18] (29,42), queue filled by the GAME's
BUILD UI (pending 1, head 2, minerals 2, income 2, **0 memory writes**): **FAIL, exit 1**. Floors that
passed: 8/8 boundaries flipped +1 with the walk home, provenance GAME-filled/0 writes, storage below
price at start, per-round bookkeeping on r0-r2 (2->4->6->8, pend 1). Floors that failed:
- `1/2 positive predictions verified`. r3 predicted arrival (8 + income 2 = 10 >= price 10) and
  storage stayed **8 -> 8, pend 1**: the visit added NOTHING while the round-start income field read
  2. r4, with the identical round-start numbers, arrived: **8 -> 3, pend 0**.
- `r4 minerals debited by >= price` — net -5 from 8 (or -7 from the post-add 10), not -10.
- `r7 unexplained ORDER-0 arrival on OUR base 18` — storage **5 -> 0 with pending 0** and a new unit,
  i.e. a pay with an empty pending count (the queue slots never left-shifted: `[2,2,0]` all run).
So ONE queued Scout Patrol produced TWICE (r4 and r7) and the second production was paid at 5 < 10.

**Measured support (`m57_credit.py --base Korolev --boundaries 3 --tag m57k`).** 3 flips (2162->2165,
rounds 8.2/10.1/12.1 s — instant when everything is held), only 2 ADD hits and no GATE/PAY/CLMP for
the base; the register side-values are the known trap (the "d0" printed 18 = the base INDEX) but the
storage deltas agree with the sampler: an add of +1 while the field read 1, +2 while it read 2. **The
add uses the d0 current at the visit, which moves inside the round** — that is why an exact-round
prediction from the round-start snapshot is impossible, and why the same numbers produced no-arrival
then arrival one round later. The pay amount is also not the price at 0x4efed8 (5 paid, 8 paid) and a
produced unit's support is debited from the same field.

**Conclusion: NOTHING MERGES.** The M57 gate asserts a model the engine contradicts (one add per
round at the round-start income, one pay of exactly the price, pending as the queue truth). The
observed positive (1/2) is real but not enough, and no floor was weakened. Branch `milestone/m57`
holds: preflight, the arithmetic line, the confirm answer, the walk-home break, orders-mode restore,
2 ms sampler, and `scripts/m57_ui_enqueue.py` (UI queue fill with read-backs).

**Next pick (M57-4, the honest one): enumerate EVERY write to `base+0x40` inside one visit** —
breakpoints at all disasm write sites (0x4ef7f6 add, 0x4eff20 clamp B, 0x4efee3/0x4efeec pay,
0x4f0cc3 clamp-after-pay) over 3 boundaries on Korolev, with the queue filled by the UI, and record
(value_before, value_after, site, pending, head, d0) for each store. Only then can the gate's debit
floor and the second production be explained. Do NOT tune predict() to the observations.

## Session 96 (2026-10-26) — M57-4: **THE STORE ENUMERATION PASSES — every write to `base+0x40` in a 3-boundary window is attributed to a NAMED census site — and the engine's price is 9, not 10, which is why the M56 gate still FAILS with every floor intact**

**What changed.** `scripts/m57_stores.py` (NEW — 23 conditioned breakpoints + the visit marker +
a 2 ms sampler + the replay acceptance), `scripts/m57_ui_enqueue.py` (now closes the base display
it leaves open and verifies the class), scratch `scratch/m574/census.py` (the whole-image store
census + call-graph filter that GENERATED the site table), skill `references/production-queue.md`
and `references/wine-operations.md`, `NEXT_PROMPT.md`, this file.

**ACCEPTANCE MET (M57-4's own gate).** `python3 scripts/m57_stores.py --boundaries 3 --timeout 200
--tag m574c` -> `PASS store-sequence enumeration: 4 stores over 3 boundaries, every store
attributed to a named census site, every sampler value reproduced by the replay, per-boundary sums
equal the observed net changes` — Korolev Center idx 17 (0x95ee40), queue filled by the GAME's
BUILD UI (pending 1, the harness itself wrote nothing), 3 visits, 3 boundaries 2163->2166, sampler
value sequence [7, 0, 1, 2], per-boundary sums 0/-7/+1/+1 == the observed nets, zero unattributed
deltas. Trace `evidence/trace_m574c.jsonl`, gdb log `evidence/m574c.gdblog`.

**The enumeration (read back at the sites, each breakpoint conditioned on the store's OWN base
register == our record).** A visit is `FUN_004f5a70(index)`: it computes
`lea ecx,[index*304+0x95da10]`, stores it to the current-base global `DAT_0x8f0d60` at **0x4f5a99**
(the per-visit marker), and calls 0x4e8d60, 0x4e78e0, 0x4e92c0, 0x4e93f0, 0x4eaa10, **0x4ef6d0**
(the production visit) and **0x4f26e0**. Whole-image census: **65 stores to `[reg+0x40]` in
`.text`, 23 reachable** from the visit driver / the queue edit / the AI chooser; the
`lea reg,[reg2+0x40]` pointer-arithmetic shape has no store through it in those sets. In the
measured windows only two sites ever fire:
- **`0x4ef7f6` ADD** — the delta EQUALS the `+0xd0` field as it reads AT THE VISIT (+2 with d0 2;
  +1 with d0 1 twice; d0 itself moves with the garrison), gated `d0>=0 && head!=-38 &&
  !([base+0x30]&2)` at 0x4ef7db-0x4ef7f9.
- **`0x4efedd` PAY** — 9 -> 0 with pending 1 -> 0 in the same visit. The completion gate is
  `cmp [curbase+0x40], edi ; jge` at **0x4efa5e**, where `edi` is built at 0x4efa4b-0x4efa52:
  `edi = eax` from `call 0x4e40a0` (item cost for the faction) then `imul edi, eax` from
  `call 0x5ac950` (a factor). **edi measured 9 twice** (10->1 in `m574b`, 9->0 in `m574c`) — the
  deduction is 9, NOT the 10 the M56 model assumes.
- the clamp sites `0x4eff20`/`0x4f0ce9` (store `max(0, min([0x92a370], d0))` only when storage >
  that limit) NEVER fired; `0x4f2d7d` (the distribution store in `FUN_004f26e0`) never fired for
  our base. Session 94's unnamed "second movement inside one visit" (7->9 then 9->0) is now NAMED:
  the add at 0x4ef7f6 and the pay at 0x4efedd.

**The M56 gate, re-run unchanged per the footing.** `python3 scripts/m56_build.py --ui-queued 17
--boundaries 10 --timeout 300` on the UI-filled queue (pending 1 head 2, `memory writes: 0`, start
minerals 2 < price 10) -> **`FAIL production prediction accounting`**: `BAD at least 1 POSITIVE
prediction verified (non-vacuous) — 0/0` and `BAD r7 bookkeeping base 17: NOT predicted to arrive
-> queue held — pending 1->0 ... (minerals 0 vs price 10)` — the arrival came at minerals 8
(8 + income 1 = 9 >= the measured 9). 10/10 boundaries flipped; the provenance and
storage-below-price floors passed. Nothing was weakened.

**Traps found (all measured, all recorded in the skill).** (a) **`si` inside a breakpoint commands
list ends `gdb -batch`** — the first hit printed the step location then `[Inferior 1 ... detached]`
and the watch died after one store; the store's own source operand IS the after value for a plain
`mov [reg+0x40],src`. (b) **the base array reorders mid-watch**: Korolev walked index 18 -> 17
(0x95ef70 -> 0x95ee40) during a run, after which the baked address held ANOTHER faction's record
(storage 19, head -27) — the sampler now checks the NAME at the address every sample and ends the
watch at the move (the closing anchor is the last good sample, never a post-detach read-back: the
game keeps playing after the last flip). (c) **the enqueue recipe leaves the base display open and a
modal pane swallows every turn-end key** — a 90 s watch sat parked on `cur_player 3` through
Return/h/OK; Escape closes the pane (safe there, unlike the bare map). (d) `set print frame-quiet`
is not a command in this gdb and aborts the whole command file. (e) `os.pread` on `/proc/<pid>/mem`
EIOs here; seek+read works. (f) all our units must be HOLD (poke `+17`=2, read back) or the auto-end
never fires and a boundary watch burns its whole budget parked on our turn.

**Open.** (1) **The price**: name `0x4e40a0` (the cost) and `0x5ac950` (the factor) and reproduce
edi = 9 for a queued Scout Patrol — the M56 model's price constant is what is wrong, not its
floors. (2) Session 95's pay-with-pending-0 (its r7) was NOT reproduced in any measured window;
every pay seen had pending 1 at the store and popped in the same visit. (3) Whether a pay can fire
in a visit whose income add did not run (the `d0 > 0` guard). (4) The clamp sites' live behaviour
is still unmeasured. (5) **M57 stays UNMERGED** per the footing (the M56 gate is the merge
condition); `milestone/m57` holds everything, still unpushed (a pre-receive hook refused it earlier).

**Next pick (M58): the price.** Disassemble `0x4e40a0` and `0x5ac950`, reproduce `edi` for the
queued Scout Patrol from static tables, and re-run `m56_build.py --ui-queued` with the price
DERIVED rather than assumed. The floors do not move.
