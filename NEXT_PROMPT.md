# NEXT_PROMPT.md - footing (B38 s342 `e0bb2deb53ecb96c`; M376 s339 `f22d2b46cc7e9507`. STATE: B1-B38 + M54A-M381; (ix) box-GATED; (x) OPEN-LEADS; #180 pre-existing FAIL.)
Overflow: `docs/nextprompt-archive-m299-b20.md`, `docs/pick-archive.md`, NAMED §CHAIN-BUILDS/PICKS, skill instrument-laws.md.

## BUDGET — read before anything else (compression CANNOT be relied on)

The main model is also Hermes' compressor; its summaries die on the output cap. **Whatever is not
finished by ~150k tokens is not finished at all.** Counted in TOOL CALLS:
- **0-6** brief, this file, notes tail, `accept_ready.py`. No shard reading "for background".
- **6-30** the milestone, one variable at a time; **commit by call 15** (s187: call 25 = 167k, zero commits).
- JSON only, no XML. A write over ~4 KB that drifts -> `missing path`: retry as pure JSON, never fragment. Branch +
  skeleton commit BEFORE probing (s189).
- **30-40** STOP: an ungreen acceptance IS the finding — number + blocker, merge nothing.
- **40-50** closing order, TERSE (see CLOSING ORDER; the caps there bind).

Survivability: cursor <=600 B before any >2-min step; never `rm`/`git checkout --`; doc writes patch/append.
**Batch: 5 static per census script, 1 box — doc headroom is the cap.** Caps (BYTES, what `budget` prints): NEXT_PROMPT warn 12,000/fail 16,000 — CLOSE at <= 12,000; SKILL.md
warn 55,000 (keep near 44 k, always-loaded under the 60 k ritual); SESSION_NOTES warn 110 k. Split rule: settled text
VERBATIM to a reference / `NAMED.md` section; RULES + pointer stay; re-run `budget`.

## BUILD TRACK — every 4th fire builds (full text VERBATIM: `docs/pick-archive.md` §s194)

`python3 scripts/track_mode.py` prints `MODE=BUILD|ANALYSE` + `next_rung=B<n>`. BUILD ⇒ build
that rung from `BUILD_SPINE.md` in `sim/` (runnable acceptance, parity vs a recorded trace, never a censusim; no
box/`/proc`/gdb time; PR titled `B<n>`); ANALYSE ⇒ pick from this file. **B1-B38 MERGED** (per-rung cmds `NAMED` §CHAIN-BUILDS; `## B34`-`## B38` govern).
**B39**: `track_mode.py` decides; author the rung in `BUILD_SPINE.md` BEFORE probing.
**DOC CAP: NAMED 247,600/250,000 (2.4k free - ROTATE FIRST next fire; `b38_named_rotate.py` = pattern).**

## THE LEDGER

Merged M54A-M327 + B0-B26 + hygiene #254-#280. UNMERGED: the six ids in `§trim-s202`, of which **M241 (#180, 2/5, documented FAIL, gates stand)** is live.
Full list + reasons: `docs/pick-archive.md` §trim-s202; per-id semantics in `NAMED.md`.

## THE INSTRUMENTS (run FIRST)

1. **accept_ready.py** = readiness oracle (`test_accept_ready.py`): screen, running gdb, evidence headroom, then per
   base `pending > 0`, `minerals < price`, `credit > 0` — **re-read it before you arm**.
2. Writer/flag chain (BOX ONLY) - VERBATIM `docs/pick-archive.md` §trim-s295 (b): m94/m97/m100/m102/m103
   + m92/m95/m98/m117.
3. Static-first kit (zero box time): `field_census.py`, `name_global.py`, `m118_flag_never_set.py`
   (gate satisfiability), `fn.py 0xADDR`, `scratch/m71/dis.py LO HI [cap]`, `evidence.py audit|budget|prune`.

## THE PICK — index (detail: `docs/pick-archive.md`, `NAMED.md` §CHAIN-PICKS)

- **Where things live:** map/terrain = `MAP_FORMAT.md`; faction fields = `docs/field-atlas-faction.md`
  (read §M297 first - the 0x94d104 phrasing is WRONG).
- **ISOLATION (s254)**: if a fire is live (`ps` + `gh pr list` + `git status`), use `git worktree add ~/reverse/wt-s<N> -b milestone/<id> origin/main` and work ONLY there (`ln -sfn ~/reverse/smac/scratch scratch`); NEVER `git add -A`.
- **THE PICK: pick from the OPEN shortlist below** (collision check FIRST per ISOLATION). track_mode is AUTHORITATIVE.
  **NO STATIC PICKS LEFT** except **(ix)** (box-GATED); the analysis-only option is the OPEN-LEADS list, each with a NAMED
  question. STILL OPEN: (x6) other writers of the 0x92bde8..0x92bf14 pref block (chain-3); `ds:0x985ba0`'s WRITER (M334).
  ANSWERED (do not re-derive): M227-M340,M344,M346 + B1-B38 (M241 FAIL 2/5 #180); x1 M333, x7 M334, x8 M337,
  x9 M342+M344+M346+M348, `0x999fa4` M353. Closed enumeration + pick rows + open-lead census VERBATIM:
  `docs/pick-archive.md` §trim-s270 / §trim-s313-chain1 (sha1 `8332dd50ba16`, `scripts/m333_nextprompt_trim.py --verify`).
  Lists live in NAMED ## M310-M391. READER LAWS still BIND: every kickoff + skill `instrument-laws.md` + §CHAIN-PICKS.

## LIVE FACTS / KIT

- **BOX**: UP, last touch s258 (TracerPid 0, yama=0; `pgrep -x terran.exe`). RE-CHECK `accept_ready.py`:
  credit 0 is d0-gated STRUCTURAL (walk/scan kinds run anyway); `sudo -n python3 scripts/smac_preflight.py`
  before arming. **ptrace law (s211): restore yama PRE; harness stays uid 1000 — skill `wine-operations.md`.**

## TRAPS — rules (FULL s241 text verbatim: `docs/pick-archive.md` §s242-traps; detail §trim-s205/§s198; laws: skill
`instrument-laws.md` + `wine-pitfalls.md`)

1. A `fired=` list is the MODEL's prediction, not events; a no-event is evidence only once the bp is CONFIRMED
   to exist there; a gate may only read a field the harness SETS. (FULL: pick-archive §s242-traps)
2. Check the instrument before believing a no-event: deref-conditions silently never fire; a return-site bp
   prints the OLD eax; ZERO CALLS can be the GAME - scan /proc for the vptr first. (FULL: §s242-traps)
3. Register semantics live in the ENCODING (scaled vs byte addressing never compare equal; an RMW through a
   COPIED register evades store-shape greps - a hw watchpoint on the FIELD answers "who writes it"). (FULL: §s242-traps)
4-11. (VERBATIM `docs/pick-archive.md` §trim-s256: gdb printf/script + call-frame; >90 s census never
   foreground; a PASS on a non-discriminating shape is no PASS; hw-watchpoint read-back.)
12-13. Both gdb-detach laws (a census can leave gdb ATTACHED; the turn driver returns rc=0 while AI
    upkeep plays). FULL VERBATIM: `docs/pick-archive.md` §trim-s268.
14-23. (VERBATIM `§trim-s262`: queue-tail STALE ids + id-0 sentinel + negatives-belong-to-TYPE; PRODFLAG
   0x4efe60 attribute the sweep by its predecessor; list cursor read BEFORE seek = PREVIOUS cursor;
   dirty-tree start = stash/start/pop. `§trim-s245`: objdump UPPERCASE; ARM BEFORE ANY SCREEN; SIGUSR1/
   SIGPIPE `handle` tails; byte-field BIT OPS vs dword scans; a VALUE SAMPLER is NOT a STORE CENSUS.)
24. **A PASSING ASSERTION IS NOT A GATE** — an assert that can pass on an UNMEASURED state is a defect, not a
   gate; every gate needs a NAMED mutant that reddens it, and the fixes get mutated too. FULL text + the
   `m308_mutate.py` 8/8 reference: `docs/pick-archive.md` §trim-s296 (a); worked defect list, skill mechanics:
   §trim-s292 (b) at `docs/pick-archive.md:996`.
## CLOSING ORDER (exactly — the kickoff carries the same list, and the full 7-step text lives
VERBATIM at `docs/pick-archive.md` §trim-s269). Order: 1 `SESSION_CURSOR.md` (<=600 B) BEFORE the
rest, in case of compression. 2 `## Session <N+1>` APPENDED to `SESSION_NOTES.md` (<=2 KB, numbers
WITH the command that produced them). 3 the `<ID>` block in `NAMED.md` (<=1 KB) + patch IN PLACE any
earlier block this round qualifies; every VERIFIED row names the mutation that reddens it
(no mutant = INFERRED/OPEN, or pin it + mutate it before submit). 4 `NEXT_PROMPT.md` patched BY SECTION to <=12,000 B (budget's
warn), every addition paired with a deletion. 5 sync the skill ONLY if edited (`diff -rq skill/
~/.hermes/skills/smac-cvr-format/` then `rsync`). 6 `git add <explicit paths>` + commit, then
`python3 scripts/gate.py --base main` GREEN + `python3 scripts/review_lint.py --id <id>` PASS.
7 submit -> `python3 scripts/ai_review.py <n>` (Strata local review; Greptile if credits return) ->
triage ALL findings in one reply, re-measure at head -> merge ONLY on a real PASS (docs/AI-REVIEW.md).
Results: `docs/pick-archive.md` §trim-s313-chain1 region-B (sha1 `6f2ddbe32478`); per-id `NAMED ## <id>` GOVERN.
- M348 (s326) MERGED: slots 1/2 <- Script.txt `#PRODUCEXQ/G`; M346 `drainer` RETRACTED.
- Retired result lines (B34-B38, M368-M376, VERBATIM + sha1 check): `docs/pick-archive.md` §trim-s343-chain4 (sha1 `dfe9d7b2173a`); per-id `NAMED ## <id>` governs.
- M377 (s339-c3): 0x8000 rides the WAR stamp (0x8010@0x507d1a), 0x10000 the first-contact TRUCE (0x10004, rel&0x8==0); M375's 1-reader claim RETRACTED. 8/8 `c9e99e3b7e9f0a31`.
- OPEN LEADS: who SETS 0x400 (M382); ds:0x985ba0's writer (M334); the two peace writers (pick above).
- M379 (s340-c2): +0x594 = 2 AI readers; M376 8th write RETRACTED (7 bodies; 0x92a7fc = terminal). 31/31.
- M380 (s340-c3): 0x94e48c = MIGHTY/MEEK scalar; 2/27 rel rewrites drop a stamp; hub 3 = TREATY validator. 7/7 `5dfd436fe4093015`, 19/23 mutants.
- M382 (s341-c2): 0xc00 cluster = 15 readers (0x5468c7 is NOT one - bits 2|16). 35/35 `90cb89f84ce7feeb`. Next: who SETS 0x400.
- M381 (s341-c3): 0x2000 = PEACE; setter A 0x50393d (PACT third party + peace/commlink + strict might(ecx) > might(esi), peer's own scalar); setter B 0x506cf1 = not-at-war only; both rows. 9/9 `2fa1a4100ec6f4f6`, 20/20.
- M383 (s341-c3): 0x94e48c = per-unit (OFF+ARM) sum; 12/14 rewrites resolve. 9/9 `1d419b65323aec6c`, 29/29.
- B38 (s342) MERGED: `#SOCIO` 4x4x11 grid in `sim/socio.py` - M376's two vectors reproduced field-for-field, settings -> 11 totals, signature 12 add/4 reject; `0x92babc` does NOT feed `0x94e48c`. 9/9 `e0bb2deb53ecb96c`, 12 mutants. NEXT: pick (a).
- M388 (s342-c6): slot 0's agenda pair has NO writer — M376's randomizer starts at record 1 (7 records), the SE commit 0x4b2570 writes only the 0x94d658 grid; slot0 (0,0) = 'no agenda' (37/37 `bb2f4329dd2467f2`, 15/15). NEXT: slot 0's owner (which faction id the 0x59c block indexes).
- M386 (s342-c4): +0x94d820 = X of a per-faction (x,y) marker PAIR (+0x94d824 = Y) at +0x3d8 — not a deadline/counter; M378's 0x20000 guard reads the PARTNER row. 55/55 `3e6d87261b7fe88e`, 15/15 mutants.
- M385 (s342-c3): nine dyn-mask 0xc00 sites resolved (7 PROVEN, 2 DEAD-INF) - no 0x800, no 0xc00 pair, but 0x400 ALONE at 0x4dacf7/0x4dad22 (M382 sole-0x400 RETRACTED). 44/44 `0103209f070e60f7`, 33/33 mutants.

- M384 (s342-c2): 0x400 has 7 setters - `0x5534ae`/`0x555a6b` inline, plus 5 callers of the pair-mask API FUN_00551a20/FUN_00551cf0 passing 0x400 (95/106 masks resolved); `PASS M384: 39/39` `evidence/m384_bit400_writer.txt:280`, 23 mutants. Next: the 7 runtime mask args (0x4dadxx family) or what `0x551a20`'s `and 0xfaeef378` blanket clear means for the 0xc00 cluster.
- M387 (s342-c5): M380's last 2 = a verbatim pair-dword copy gated by arg7; arg7==0 writes UNWRITTEN (store unguarded), only msg 0x16 reaches it. 11/11 `c0e46fd18f2fc313`, 20/20.
- M391 (s343-c4): `and 0xfaeef378` is 3 masks x 2 rows gated on mask-arg bits 0x7/0x10/0x17, not a blanket; 0xc00 clearers = 5 instr / 2 fns, and both explicit 0xc00 clears are the `not`+`and` half (0x4db11b 0xc20, 0x519bb5 0xc00); 0 of 65 masks carry 0xc00 -> 24 WAR-arm callers always drop it. 51/51 `76148839fd85b66e`, 12/12. NEXT: the 3 opaque set=0 masks (0x4dad30/0x4db02d/0x4db08d).
