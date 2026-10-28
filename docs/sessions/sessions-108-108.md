# Session notes archive — sessions 108-108

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 108 (2026-10-26) — M68: THE 212-RULE KEY IDENTIFIER IS BUILT, ITS GATE IS GREEN, AND THE ACCEPTANCE **FAILED** — INSERT APPENDED. NOTHING MERGED.

**What changed.** Nothing in the game's model is claimed. Tooling only:
- `scripts/m66_insert_slot.py`: the full candidate set is now machine-readable — `BYTE_KEY_SPECS`
  (52 offsets x desc/asc x ties after/before = 208) + `NAME_STR_SPECS` (4 whole-name rules) =
  `SORT_KEY_RULES` (212), `score_key_sequence(steps, keyf, direction, tie)` (scores a whole
  sequence of write read-backs, returns `None` when the read-back is not a legal shift),
  `key_rule_specs()` -> `(name, off, d, t)` tuples, `key_shape_predictions()`, and a
  `key_shape_gate()` that returns a **5-tuple** whose last element is the set of KEYS (byte
  offsets; `None` = the name string) predicting the landing sequence.
- `scripts/m68_typebytes.py` (read-only, `/proc/<pid>/mem`, clicks nothing): dumps every live
  52-byte type record for the chooser + queue ids and reports per-offset co-ordering.
- `scripts/m68_key_run.py`: the acceptance run. Pre-click shape gate from the baseline alone,
  one click per id, pending polled, landing extracted by `_shift_index`, all 212 rules scored,
  PASS only if exactly ONE key explains every write, `--trace` + `bail()` so every FAIL leaves
  evidence behind.
- `scripts/m68_cellprobe.py`: one click + INSERT, prints exactly what the queue received
  (guard field, clicked cell entry, shift pattern, stored id) and writes a jsonl trace.
- `scripts/test_m68_key_rules.py`: 35 pinned cases — `PASS 35/35 m68 key-identifier cases`.
  The three M67 read-backs fit **11, 17 and 15** of the 212 rules across **4-6 different keys**,
  which is the quantified proof that M67's two-item shapes could not identify a byte.

**The run, with its numbers.**
`python3 scripts/m68_key_run.py --base-name "University Base" --items 2,1,194,192,193
--trace evidence/m68_key_run.jsonl` -> **exit 1**, after `SMAC_SAVE='m54b_clean.SAV' python3
scripts/m54a_load.py --relaunch` + `python3 scripts/smac_play.py --turns 1 --timeout 200
--no-escape 3000 --orders-per-turn 1 --verbose --tag m68t2` (round 51 -> 52, year 2151 -> 2152,
60 s) + `python3 scripts/accept_ready.py` (READY, University Base idx 0, minerals 0, `+0xd0` 0,
pending 0, head slot 2).
- The gate accepted the shape: only `+42` predicts the plan-descending landing `1,1,3,4,3`
  (`key_gate` row) — 12 of the 53 keys were decidable on it at all.
- The engine wrote slots **1,2,3,4,5** — one append per click. Integrity True: every click
  verified `guard == cell`, cell entry == intended id, stored id == intended id, pending +1.
- **55 of 212 rules** predict `[1,2,3,4,5]` for this shape: every byte constant over these five
  ids, plus `+45` (0xff, 0xff, 8, 8, 8) and `+50` (0xff, 6, 0, 0, 0), whose values are monotone
  in click order. So the run cannot name a key — and nothing else is claimed.

**The conflict (recorded, not resolved).** M67 measured sorted landings with this same driver and
this same INSERT button; M68 measured appends. The runs differ in base (Korolev Center and a
round-60 University Base vs the save's round-51 University Base), minerals (3 and 1 vs 0), queue
occupancy at start (2/4/6 vs 0) and the chooser's candidate list (4-7 entries vs 67). One
variable at a time was not achieved here: the reload changed all of them together. **Confounded —
not "because".** M67's read-backs remain real and unexplained.

**Two live rules found on the way.**
- The engine **refuses to enqueue an id the queue already holds**: a second INSERT of 193 left
  pending 5 and every slot unchanged (`evidence/m68_cellprobe_193.jsonl:4`).
- The driver's chooser cell -> pixel mapping (5 columns) is **unreliable past the first row**:
  cell 6 (255,160) and cell 4 (636,60) failed to register in three probes (guard stayed on the
  previous selection, INSERT did nothing), and the one time the cell-6 click registered the queue
  received **-3 (0xfffffffd)** instead of 195, after which the next INSERT appended a plan-9 item
  at the end of the region.

**Open.** (1) Why the enqueue sorts in one state and appends in another — the cheapest decisive
instrument is a gdb breakpoint on the enqueue (`0x418afd-0x418b29`) printing the index and the
value the engine stores, plus a watchpoint on `base+0x54`: it answers "sorted scan or
`pending + 1`" and "where does -3 come from" in one run, without guessing. (2) The chooser cell
mapping. (3) Whether a deferred paint/round-boundary sort rewrites the region (read the region
again minutes later with the queue widget provably open).

**Next pick.** S109 = instrument the enqueue with gdb (the `m63_pop.py` recipe), not another
click-order search: the click-only method has now told us all it can — on THIS state the engine
appends, and no click shape can identify a key an append engine does not use.
