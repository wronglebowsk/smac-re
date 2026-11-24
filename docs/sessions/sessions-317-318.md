# Session notes archive — sessions 317-318

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-316-316.md` — the hot file cites only THIS archive, so
the chain onward lives here; without this line the older archives are orphans (s292).

## Session 317 (s316-chain1, REVIEW ROUND on PR #351 / B28, zero box)

- All 10 findings (3 P1 / 7 P2) answered IN THE GATES; no threshold weakened, none dismissed. P1(a)'s premise was half wrong (the full-price path never reads the carry) — the zero-carry baseline is now MEASURED by an all-ones carry-seed tie.
- ACCEPT `python3 -u -m sim.selftest --b28` → **PASS B28: 8/8 gates**, digest(rows) `705a4520c08c4062`, print `99c52201f073499d` (pre-review `8c87e05ffa2b80cc`), container `38bba29ab857654b`, 2 runs byte-identical (`evidence/b28_feeder_exec.txt:9`); harness `python3 -u scripts/b28_mutate.py` → **HARNESS PASS 18/18** digest `3974d739da3af55f`, 8/8 gates, NO-OP `[]`, dead `[]` (`evidence/b28_mutate.txt:20-23`); `--selftest` 4/4; both evidence files re-captured, diffed byte-identical.
- G4 ASSERTS the dword from container bytes (offset 244, value -1, offset < block A), not a derived path property; G3 asserts the inert window and runs the SAME scan as a CONTROL over `+0x8c..+0x8f` (nonzero 14/18); G7 asserts the no-list rival at exactly 7/8 with miss `[own_player=3]`; G6 measures exactness over the differing set and measures the HONEST run (touch set `[]`, bit5 unchanged).
- RETRACTION in place: "the carry persists through the writer" is **FIXTURE-ONLY** (`NAMED ## B28` row + spine §B28 qualified); this save's run writes no carry.
- New mutants ME5 (full-price reads the carry-in → G6,G8), ME6 (control window moved → G3,G8); MU6 grew to {G4,G6,G7,G8}. PITFALL: every prose edit re-pins the print digest (`434b…` then `99c5…`).
- Merge: origin/main `c0f5e2a` (M334) merged; BOTH chains' sections kept; main did not touch `sim/feeder.py`, digests unchanged post-merge.
- DOCS: NAMED **248,734 B** (1,266 under the fail line) — headroom UNDER 5 KB: next fire ROTATES M250-M254 before adding a block.

## Session 317-chain2 (2026-11-23) — M335: the difficulty ladder's INDEX->LABEL order

- **ANSWER (pick (x6), first clause):** the six difficulty names are alpha.txt's `#DIFF` rows,
  loaded at `0x57ac56` (`push "DIFF"` -> `call 0x5ea431`) into `0x94d2ac`, one dword per row,
  `add esi,4` up to the hard-coded `cmp esi,0x94d2c4` => 6 rows, file order
  Citizen/Specialist/Talent/Librarian/Thinker/Transcend. `ds:0x985aec` is that index: at
  `0x599405` it loads the label (`mov ecx,ds:0x985aec; mov edx,[ecx*4+0x94d2ac]`), and the
  chooser `0x4ddaf8` walks the table forward passing `push edi` (=k) as the item index, after
  seeding the dialog with `ds:0x985aec` before `call 0x5f1394`.
- **M330 refined, not retracted:** the refund's cmps are `cmp eax,3/jle` (none at <=3) and
  `cmp eax,4/jne` => k=1 at exactly 4 (Thinker), k=2 at >=5 -- with six rows that arm is
  TRANSCEND (index 5), i.e. live, not a hypothetical.
- **New measured oddity:** the only `0x8f0c11`-fed clamp on the index is `FUN_00423af0(lo=0,hi=6)`
  at `0x486f30-0x486f40` (1 of the 169 `call 0x423af0` sites); its hi is INCLUSIVE and equals the
  array LENGTH (`hi*4 == end-base` read out of the bytes), so a difficulty of 6 would read
  `0x94d2c4`, one row past the table. Reachability is OPEN.
- ACCEPT `python3 -u scripts/m335_difficulty_ladder.py` -> `PASS M335: 7/7 gates`, digest
  `fb58bdc3307d6258`; re-run diff-identical (`evidence/m335_difficulty_ladder.txt:9-10`).
  Harness `python3 -u scripts/m335_mutate.py` -> `PASS HARNESS 20/20`, digest `6e0e05a8ffb388d8`
  (includes an ALGORITHM mutant); `--selftest` 3/3 (`evidence/m335_mutate_selftest.txt:4`).
- **REVIEW ROUND (Strata, PR #353): 10 findings (3 P1 / 7 P2), 10 accepted, 0 dismissed.** Fixes:
  G4 became an ORDERED fragment walk (edi starts at 0, seed before `call 0x5f1394`); G2 reads the
  loader's actual store; G3 uses token-boundary matching (+ MU20 algorithm mutant); G5 proves both
  readers are counting loops; G6 READS base/bound/clamp-hi out of the code instead of comparing to
  the script's constants and censuses all 169 clamp sites. MU1's declared set corrected to
  {G2,G3,G6}. Two P2s were about MY doc-cap rotation -- **which is now moot: chain 1 landed the
  same M246-M254 rotation on main as `docs/named-archive-b28-rows.md` (sha1 fcd4989fdf15)**, so the
  duplicate archive and `scripts/m335_named_rotate.py` were dropped in the merge; the P1 rotation
  cite bug it exposed (a key that ate a digit on `## M248/M249`) is recorded above as a finding.
- PITFALL: this census's `gates()` originally wrapped all seven checks in ONE try/except, so a
  vanished site reddened every gate (MU6 measured {G1..G7} instead of {G3,G5}). Per-gate
  try/except is what makes a declared mutant SET measurable at all.

## Session 318-chain1 (2026-11-24) — M337: item table row order = alpha `#FACILITIES` file order, record i = alpha row i-1 (pick x8)

- **ANSWER (x8):** the "39-row item table" at `0x984d48` is the `+0x10` dword of the 72-record array
  at `0x984d38` (M53i). Loader `0x57a7ef..0x57a899` pushes `FACILITIES` (`0x691ccc`) and
  walks `esi = record+0xc`: start `0x984d74` (rec 1), branch `cmp esi,0x985494` (rec 39), `+0x30`,
  end `cmp esi,0x985ac4` (rec 72) => recs 1..71 written, rec 0 untouched; 1 line-read + 1 record step
  per iter => k-th line -> rec k. Recs 1..38 take 6 tokens, 39..71 take 11,
  and alpha's FIRST 11-token row is idx 38 (`The Human Genome Project`, alpha.txt:629).
- **'39' is the consumers' bound** (`cmp esi,0x27` @`0x4f4a35`), not the array size; recs 39..71
  (projects) keep the same order, so B28's +300 parity covers ids 1..38 by construction.
- **Column order (V):** `0x5ea985` takes one comma token per call; all three converters call it, so
  the decoded store seq `+00,+0c,+10,+14,+18,+04,+18,+1c,+2c,+24,+28,+20` is column order =>
  **M53i's `+0x20`/`+0x28` labels are swapped**.
- ACCEPT `python3 -u scripts/m337_item_order.py` -> `PASS M337: 8/8`, digest `39d82f0771690e15`,
  diff-identical (`m337_item_order.txt:90-91`); `scripts/m337_mutate.py` `HARNESS PASS 13/13` incl. NO-OP MU10
  (`evidence/m337_mutate.txt:14`), `--selftest` 3/3.
- **REVIEW (#354, Strata): 10 findings (3 P1/7 P2), all answered IN THE GATES, none dismissed.** G5
  DECODES the 12 stores from the bytes (no hand list); G2 reads the consumer bound (39 != 72); G4
  proves the k-th-line->k-th-record mapping; G7's R2 is a decoded control-flow read and R4 prints a
  computed offset; the table build is input-safe.
- **PITFALL:** `;` starts a comment, so 6 later rows carry tails as text; the loader still reads 11
  tokens and re-syncs per row (`0x5ea448` -> fgets).
- Chain 2 owns `milestone/m336` (wt-chain2); NAMED rotation = M277 ->
  `docs/named-archive-m337-rows.md:8` (sha1 `653c93cda817`, pinned in `m337_named_rotate.py`).
