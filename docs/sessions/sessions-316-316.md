# Session notes archive — sessions 316-316

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-312-316.md` — the hot file cites only THIS archive, so
the chain onward lives here; without this line the older archives are orphans (s292).

## Session 316-chain2 sidecar (2026-11-23) — M334 merged + evidence completion

- **M334 MERGED as `fc2569d`** (PR #350, squash; CI `gate pass 15s` verified on the post-review head
  BEFORE merge; review triaged 10/10 accepted, 0 dismissed, one reply comment
  `#issuecomment-7102934036`; title REST-patched to the post-review numbers and read back). Merged
  tree == the reviewed head (`git diff --stat HEAD origin/main` empty).
- Evidence completion: `evidence/ai_review/pr350_20261123_131041.json` (the raw review payload) was
  left untracked when #350 merged — the repo convention is both `.md` and `.json` per review
  (24 json / 25 md before this). Added here; no claim changes, no re-measure needed (the instrument
  and its digests `5b5ece39af02baba` / `a5a5091e533f7883` are untouched).

## Session 316 (s316-chain1, B28 BUILD rung, zero box) — the UPKEEP FEEDER made EXECUTABLE; the container's own `+300` octet IS its full-price total

- track_mode said MODE=BUILD next_rung=B28 and the spine ended at B27, so §B28 was authored in `BUILD_SPINE.md` BEFORE implementation (commit de6a0ee), then built: `sim/feeder.py` = the law, `sim/composedfeeder.py` = the run + gates, `--b28` relays.
- ACCEPT `python3 -u -m sim.selftest --b28` -> **`PASS B28: 8/8 gates`** digest(rows) `705a4520c08c4062`, print_digest `8c87e05ffa2b80cc`, final container `38bba29ab857654b`, 2 runs byte-identical (`evidence/b28_feeder_exec.txt:18-19`); harness `python3 -u scripts/b28_mutate.py` -> **`HARNESS PASS 16/16`** digest `a2ba49fb9dd1056b` (12 CODE + 4 EXPECT, exact-set check 0 complaints, gates reddened 8/8, dead mutants [], NO-OP `[]`), `--selftest` 4/4 (`evidence/b28_mutate.txt:19-21`).
- THE FINDING: `ds:0x985ba0` is not a loose runtime pointer — it is CARRIED in the save's state header (`mem2file` → file offset 244) and reads **-1** in `m54b_clean.SAV`, so the 4f48dc sign skip fires and the halving runs 0 times. Executing the loop over the save's own 18 base records reproduces the container's own `+300` octet `[0,1,1,0,1,0,1,1]` **8/8** — but only once the own faction's recorded disabled id (8, parsed out of `docs/named-archive-m32-m84e.md:272`, never retyped) is applied: **7/8 without it**, and the single miss is faction 3 = `own_player`, whose only cost-1 facility IS item 8. Rivals measured: forced-halved 3/8, charge-every-row differs at 18/18 bases.
- The carry is live here: 6 of 8 factions have an odd full-price total; with the gate dword pointed at a base the charged faction owns, bit5 survives round 1 at 5 of 7 fixture factions and moves round 2's charge by exactly 1 at those and only those (`:7`). `block+0` is now a modeled span for this call; `savewriter.modeled_spans()` with no overrides still returns exactly the pre-B27 list and the unmutated build stays the identity.
- PITFALL (the rung's own defect class, caught by the harness): the first G4/G7 computed the price path and the totals with INLINE re-typings of the law (`sel >= 0 and owners[sel] == f`), so MU6/MU7/MU10 reddened ONLY the digest gate — a gate that re-derives the law instead of CALLING it measures nothing. Fixed by routing every number through `feeder.price_path` and adding two ties: run-vs-law (8/8) and "in a one-base fixture every OTHER faction stays at full price" (0 pairs).
- PITFALL: `owner_bytes[-1]` is Python's LAST element, not "nothing selected" — a dropped sign skip silently reads the last base's owner instead of failing (now measured, MU6).
- PITFALL: a printed-table digest that hashes the line printing its own anchor can never be re-pinned — the G8 line is excluded from the hashed region.
- DOCS: NAMED rotation `scripts/b28_named_rotate.py` (M246+M247+M248/M249, 3,507 B → `docs/named-archive-b28-rows.md:10` §rotation-1, sha1 `fcd4989fdf15`, own terminator, `--verify` byte-exact); NAMED 246,245 → 245,488 B BEFORE the `## B28` add — still under the 5 KB trigger, rotate again next fire. NEXT_PROMPT 11,798/12,000 (added (x8) = the item-table row-order lead; paid by trimming the stale §trim-s269(b) pointer, the CLOSED-enumeration sentence and the BOX last-touch parenthetical).
