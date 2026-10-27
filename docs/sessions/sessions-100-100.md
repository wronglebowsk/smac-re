# Session notes archive — sessions 100-100

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 100 (2026-10-26) — M61: **THE CREATE IS IN THE SAME VISIT AS THE PAY, THE ROUND ORDER IS MEASURED, AND `base+0x10` IS THE BASE NAME. ACCEPTANCE PASS on one real invocation.**

**THE ROUND ORDER, read out of one ordered stream.** `python3 scripts/m60_guard.py --stage watch
--boundaries 2 --timeout 400 --tag m61a` (the watch stage was extended this session: conditioned
breakpoints on the visit `0x4ef6d0`, the pay store `0x4efedd` and the create call `0x4eff4e`,
hardware watchpoints on the guard `0x8f0d70`, the year `0x985b00` and `cur_player` `0x985dcc`, each
command list `silent` + tagged printf + `continue`, gdb stdout straight to a file) ->
`events {"YEARW": 2, "PLAYERW": 16, "VISIT": 52, "PAY": 8, "CREATE": 8, "GUARDWRITE": 0}`,
`events_at_our_bases {"Korolev Center/VISIT": 2, "Korolev Center/PAY": 1, "Korolev Center/CREATE": 1,
"University Base/VISIT": 2}`, `visits 52`, `guard_values_at_visits ["0"]`, `guard_writes 0`,
`turn_rcs [0, 0]`. One round of `evidence/m61a_seq.jsonl` (`evidence/m61a_watch.gdblog`):

```
== YEAR FLIP to 2183 (round 83) while cur_player=7
   cur_player -> 0 -> 1 -> 2 -> 3
y2183 r83 cp3 VISIT  University Base   min=6 pend=0 head=2 guard=0
y2183 r83 cp3 VISIT  Korolev Center    min=9 pend=0 head=2 guard=0
y2183 r83 cp3 PAY    Korolev Center    9->0 (edi=9)
y2183 r83 cp3 CREATE Korolev Center    min=0
   cur_player -> 4 -> 5 -> 6 -> 7
== YEAR FLIP to 2184 (round 84) while cur_player=7
```

The year store is `0x51f54f` (`a3 00 5b 98`, right after the round store `0x51f53c`); NAMED.md's
"the year store `0x51f554`" is the `call 0x478530` AFTER the store — reported conflict, bytes win.
Our bases are visited while `cur_player == 3`, in ARRAY order (University idx 0, then Korolev idx
18), four player switches after the flip, in the round whose year has just flipped. The pay and the
create are ONE visit invocation: `grep -n '0x4efedd\|0x4eff32\|0x4eff4e' scratch/m574/text.txt`
returns only the three instruction addresses plus the `jne 0x4eff5c`, so no control flow enters
that block from elsewhere, and the log prints PAY then CREATE with nothing between. **An arrival is
never a round late — a snapshot can be early.** Setup for that run was ONE variable:
`m59_head.py --stage poke --base "Korolev Center" --minerals 9 --hold` -> `POKE ... +0x40: 0 -> 9
(read back 9) OK`, `poke_hold: 0 units poked, all_held=True`, armed before attaching. The first
run's CREATE line printed `guard=3`: at `0x4eff47` eax holds `[ebp-0x28]`, which `0x4ef71a` set
from `BYTE [eax+4]` — the base OWNER byte, not the guard; the printf now reads the global and
prints `owner=` separately.

**F1 IS ATTRIBUTED, NOT TOLERATED.** `ds:0x8f0d60` names the record the round processor is visiting
(`0x4f5a70` stores it per base before the pipeline that reaches `0x4ef6d0`), so it says which base
has been reached. `m56_build.py` now reads it at every after-snapshot (`cur_base()`, logged as
`cur_base` in the `round_after` event and carried in `rounds[r]["cur_base_after"]`) and REFUSES the
deferral when that pointer already named the predicted base — the visit had run, so a still-missing
arrival is a model gap. Run-layer fixtures built from the real PASS trace by
`scratch/m61/mkfix.py` (they differ in that ONE field): `python3 scripts/m56_build.py --fixture
scratch/m61/fixture_defer_ok.json` -> **exit 0**, `PASS production prediction: 1 verified unit
arrivals over 2 boundaries ...`; `python3 scripts/m56_build.py --fixture
scratch/m61/fixture_beat_visit.json` -> **exit 1**, `BAD r0 prediction base 18 (29,42) type 2 —
... NOT deferred: at the after-snapshot ds:0x8f0d60 already named this base, so its visit had run
and the predicted arrival really was absent`. Fixture timelines now also replay the guard samples
(the guard floor cannot be vacuously true on a replayed run).

**`base+0x10` IS THE NAME, NOT A FLAG.** The base name starts at record byte **+19** (NAMED.md
`base_array` row, `M.parse_base`), so a dword read at `+0x10` is bytes +16, +17, +18 (three small
unnamed bytes) plus the name's FIRST CHARACTER in the top byte. Census
`python3 scratch/m61/census10.py` over all 24 live bases: `topbyte==name[0]: 24 / 24` — Korolev
Center `0x4b000000` = 'K', University Base `0x55000000` = 'U', both with +16..+18 = 0; the other 22
have small values there (e.g. People's Endeavor +16=1 +17=5 +18=2, Fallow Time +16=4). +17 == 1 on
all 8 faction-6 bases and +18 is nonzero on several faction-2/7 bases — an OBSERVATION, unnamed.
The old `[base+0x10] == 0` guard note was wrong twice over: Ghidra's `short *` offsets, and this
straddle.

**THE PAY SITE CONFLICT RESOLVES TO `0x4efedd` for this shape.** The live PAY stamp reads
`before=9 edi=9 after=0` with the derived price 9 (`m58_price.py --owner 3 --type 2` -> `DERIVED
price = factor_tenths 9 * type_cost 1 = 9`), immediately before the create. The `0x4f0ca1/0x4f0ca6`
site in NAMED.md's "completion path" is a different branch of the same function and is still unread.

**ACCEPTANCE — PASS on one real invocation, with the PATCHED script.** Reload recipe
(`SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` -> HUD, `difficulty level:
talent`) -> `m54g_prep.py` -> `smac_play.py --turns 1 ... --tag m61t` (`Korolev Center founded in
2150`, `turn 0: 2150->2151 OK`) -> Korolev located BY NAME (idx 18, minerals 2, income 2) ->
`m57_ui_enqueue.py --base-index 18 --cell-item 2 --inserts 1` (`after INSERT 1 (try 1): pending=1
head=2 slots=[2, 2, 0, 0, 0, 0] minerals=2 d0=2`) -> `m59_head.py --stage read --hold` (`poke_hold:
6 units poked, all_held=True`) ->

`python3 scripts/m56_build.py --ui-queued 18 --boundaries 10 --timeout 400 --no-poke-hold` ->
**`PASS production prediction: 3 verified unit arrivals over 10 boundaries, every prediction and
every observed arrival accounted, queue bookkeeping exact — queue filled by the GAME's BUILD UI (0
memory writes), paid by income at 2/round`**, **56 checks, 0 bad**; `boundaries observed >= 2 — 10
of 10 rounds flipped`; `at least 1 POSITIVE prediction verified — 3/3`; `create guard ds:0x8f0d70
read 0 in every sampled row — 18619 sampled rows, values [0]`; `memory writes: 0`; `completion NOT
armed: minerals 4 < price 9`. Trace `evidence/trace_m56_build_20261026_162511.jsonl`. Read back in
memory after the run: ours **6 -> 9**, Korolev minerals 3, pending 0, head 2, guard 0. No deferral
was needed (no `ATTRIBUTED` line in the log). An earlier PASS the same session, with the
pre-patch script and the same UI shape, printed `PASS ... 1 verified unit arrivals over 10
boundaries` with **51 checks, 0 bad** (`evidence/trace_m56_build_20261026_160325.jsonl`): in that
trace the arrival is inside window r0 (ours 9 -> 10, Korolev tile 4 -> 5) — F1's deferral was not
exercised there either.

**Rule cases.** `python3 scripts/test_m56_predict.py` -> `PASS 17/17 production-prediction cases`;
`python3 scripts/m56_build.py --fixture scratch/m56_fixture_bad.json` -> exit 1; plus the two new
fixtures above.

**Open.** (1) The pop did NOT visibly left-shift Korolev's slot array while pending went 1 -> 0
(`slots [2, 2, 2, 2]` at r0 and at r1 of `trace_m56_build_20261026_160325.jsonl`) — the documented
"left-shift + pending--" is unverified for the slot array. (2) What writes base bytes +16/+17/+18
is unknown (no runtime watchpoint was armed on them); the dword-level answer is settled. (3) The
failure path `0x4eff5c` (guard-skip and the `0x5ab650` cap share it) is unread. (4) The chooser's
~25 score terms are still a shape, not an enumeration — enemy heads stay REPORTED. (5) The harness
could close its window deterministically after our upkeep (the walk leaving our slot, or
`ds:0x8f0d60` naming our last base) instead of polling on `cur_player == 3`; the deferral is now
attributed but the window race itself is still open. (6) A writer for `0x8f0d70` outside `.text` is
still not excluded. (7) The queued-count byte conflict (`0x94dc84` vs `0x94de84`) is untouched.

**Harness lessons.** A dialog left on screen swallows every UI click: `m57_ui_enqueue` failed twice
on University Base with `INSERT never landed` because an Operations Director "the minerals output of
Korolev Center is not sufficient to support Scout Patrol ... the unit has been disbanded" dialog
(`classify()` == `dialog`) was over the BUILD pane; Return cleared it, one Escape closed the pane.
And producing a unit zeroes the base's mineral credit (`+0xd0` 1 -> 0 or -1) while the income add is
gated `d0 > 0`, so both our bases sat at minerals 0 / credit 0 and no positive prediction was
possible — the reload was the fix, not a poke.

**Next pick (M62): what the POP actually does to the queue slots.** Pending went 1 -> 0 with the
slot array unchanged; arm `m60_guard --stage watch`-style breakpoints on the pop `FUN_004ef5d0`
(`0x4ef5f4` gates pending == 0, the shift/pending store, the `0x4ef613/0x4ef641 stores) and on the
slot dwords `base+0x50..0x74`, run over 2-3 boundaries with a queued base, and state from the
stores what the queue's representation really is — then re-check M59's "the head slot is the truth"
against it. Acceptance stays `m56_build.py --ui-queued <idx> --boundaries 10 --timeout 400
--no-poke-hold` printing PASS on one real invocation.
