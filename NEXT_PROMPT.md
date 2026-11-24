# NEXT_PROMPT.md - footing (B38 s342 `e0bb2deb53ecb96c`; M376 s339 `f22d2b46cc7e9507`. STATE: B1-B38 + M54A-M390; (ix) box-GATED; (x) OPEN-LEADS; #180 pre-existing FAIL.)
Overflow: `docs/nextprompt-archive-m299-b20.md`, `docs/pick-archive.md`, NAMED §CHAIN-BUILDS/PICKS, skill instrument-laws.md.

## BUDGET — read before anything else (compression CANNOT be relied on)

Compression CANNOT be relied on: whatever is not done by ~150k tokens is not done. TOOL CALLS:
**0-6** brief + this file + notes tail; **6-30** the milestone, **commit by call 15** (s187);
**30-40** STOP (an ungreen acceptance IS the finding); **40-50** CLOSING ORDER, terse. JSON only,
no XML; branch + skeleton commit BEFORE probing (s189). Survivability: cursor <=600 B before any
>2-min step; never `rm`/`git checkout --`; doc writes patch/append. **Batch: 5 static per census
script, 1 box.** Caps (what `budget` prints): NEXT_PROMPT warn 12,000/fail 16,000 - CLOSE under
12,000; SKILL.md warn 55,000 (keep near 44 k); SESSION_NOTES warn 110 k. Split rule: settled text
VERBATIM to a reference / `NAMED.md`; RULES + pointer stay.

## BUILD TRACK — every 4th fire builds (full text VERBATIM: `docs/pick-archive.md` §s194)

`python3 scripts/track_mode.py` prints `MODE=BUILD|ANALYSE` + `next_rung=B<n>`. BUILD ⇒ that rung
from `BUILD_SPINE.md` in `sim/` (runnable acceptance, parity vs a recorded trace, no box/`/proc`/gdb;
PR titled `B<n>`); ANALYSE ⇒ pick from this file. **B1-B38 MERGED** (cmds `NAMED` §CHAIN-BUILDS).
**B39**: `track_mode.py` decides; author the rung in `BUILD_SPINE.md` BEFORE probing.
**DOC CAP: NAMED 246,041/250,000 (3.9k free - ROTATE FIRST next fire; `b38_named_rotate.py` = pattern).**
**DOC CAP: NAMED 244,408/250,000 (5.6k free; `b38_named_rotate.py` = rotate pattern).**

## THE LEDGER

Merged M54A-M327 + B0-B26 + #254-#280. UNMERGED: six ids in `§trim-s202`; **M241 (#180, 2/5, documented FAIL)** is live.
Full list + reasons: `docs/pick-archive.md` §trim-s202; per-id semantics in `NAMED.md`.

## THE INSTRUMENTS (run FIRST)

1. **accept_ready.py** = readiness oracle (`test_accept_ready.py`): screen, running gdb, evidence headroom, then per
   base `pending > 0`, `minerals < price`, `credit > 0` — **re-read it before you arm**.
2. Writer/flag chain (BOX ONLY) — `docs/pick-archive.md` §trim-s295 (b), verbatim.
   + m92/m95/m98/m117.
3. Static-first kit (zero box time): `field_census.py`, `name_global.py`, `m118_flag_never_set.py`
   (gate satisfiability), `fn.py 0xADDR`, `scratch/m71/dis.py LO HI [cap]`, `evidence.py audit|budget|prune`.

## THE PICK — index (detail: `docs/pick-archive.md`, `NAMED.md` §CHAIN-PICKS)

- **Where things live:** map/terrain = `MAP_FORMAT.md`; faction fields = `docs/field-atlas-faction.md`
  (§M297 first - the 0x94d104 phrasing is WRONG).
- **ISOLATION (s254)**: if a fire is live (`ps`/`gh pr list`/`git status`), work only in your own
  `git worktree add ~/reverse/wt-s<N> -b milestone/<id> origin/main`; NEVER `git add -A`.
- **THE PICK: pick from the OPEN shortlist below** (collision check FIRST per ISOLATION). track_mode is AUTHORITATIVE.
  Next (ANALYSE, static, zero box): **(a) the LAST peace writer `0x53fcb3` - B39 executed `0x523f4c`; `0x53fcb3` is `push 1; push 2; call 0x551d70`, i.e. `551d70(a,b,0x2,mode=1)` = SET 0x2 on word B**.
  ANSWERED: M227-M340,M344,M346 + B1-B39 (M241 FAIL 2/5 #180).
  ANSWERED: M227-M348, M368-M389 + B1-B39 (M241 FAIL 2/5 #180); no static pick left below.
  CLOSED enumeration + pick rows + open-lead census VERBATIM at `docs/pick-archive.md`
  §trim-s270 / §trim-s313-chain1 region-A (sha1 `8332dd50ba16`, `scripts/m333_nextprompt_trim.py --verify`).
  **NO STATIC PICKS LEFT** except **(ix)** (box-GATED); else the OPEN-LEADS list, each with a
  NAMED question. STILL OPEN: `ds:0x985ba0`'s WRITER (M334). ANSWERED (do not re-derive): x1 M333,
  x7 M334, x8 M337, x9 M342+M344+M346+M348, `0x999fa4` M353, x6 M390. Lists in NAMED ## M310-M391.
  READER LAWS still BIND: every kickoff + skill `instrument-laws.md` + §CHAIN-PICKS.
  Trimmed result lines: `docs/pick-archive.md` §trim-s343-chain4 (sha1 `dfe9d7b2173a`).
## LIVE FACTS / KIT

- **BOX**: UP (s258; TracerPid 0, yama=0). RE-CHECK `accept_ready.py`; credit 0 is d0-gated
  STRUCTURAL; `sudo -n python3 scripts/smac_preflight.py` before arming. **ptrace law (s211): restore
  yama PRE; harness stays uid 1000 — skill `wine-operations.md`.**
- **BOX**: RE-CHECK `accept_ready.py` + `sudo -n python3 scripts/smac_preflight.py` before arming (credit 0 is
  d0-gated STRUCTURAL). **ptrace law (s211): restore yama PRE; harness uid 1000 — skill `wine-operations.md`.**

## TRAPS — rules (FULL s241 text verbatim: `docs/pick-archive.md` §s242-traps; detail §trim-s205/§s198; laws: skill
`instrument-laws.md` + `wine-pitfalls.md`)

1. A `fired=` list is the MODEL's prediction, not events; a no-event is evidence only once the bp is CONFIRMED
   to exist there; a gate may only read a field the harness SETS. (FULL: pick-archive §s242-traps)
2. Check the instrument before believing a no-event: deref-conditions silently never fire; a return-site
   bp prints the OLD eax; ZERO CALLS can be the GAME - scan /proc for the vptr. (FULL: §s242-traps)
3. Register semantics live in the ENCODING (an RMW through a COPIED register evades store-shape greps -
   a hw watchpoint on the FIELD answers "who writes it"). (FULL: §s242-traps)
4-11. (VERBATIM `docs/pick-archive.md` §trim-s256: gdb printf/script + call-frame; >90 s census never
   foreground; a PASS on a non-discriminating shape is no PASS; hw-watchpoint read-back.)
12-13. Both gdb-detach laws (a census can leave gdb ATTACHED; the turn driver returns rc=0 while AI
    upkeep plays). FULL VERBATIM: `docs/pick-archive.md` §trim-s268.
14-23. (VERBATIM `§trim-s262`: queue-tail STALE ids + id-0 sentinel + negatives-belong-to-TYPE; PRODFLAG
   0x4efe60 attribute the sweep by its predecessor; list cursor read BEFORE seek = PREVIOUS cursor;
   dirty-tree start = stash/start/pop. `§trim-s245`: objdump UPPERCASE; ARM BEFORE ANY SCREEN; SIGUSR1/
   SIGPIPE `handle` tails; byte-field BIT OPS vs dword scans; a VALUE SAMPLER is NOT a STORE CENSUS.)
24. **A PASSING ASSERTION IS NOT A GATE** — an assert that can pass on an UNMEASURED state is a
   defect; every gate needs a NAMED mutant that reddens it (fixes mutated too). FULL text + the
   `m308_mutate.py` 8/8 reference: `docs/pick-archive.md` §trim-s296 (a), `:996`.
## CLOSING ORDER — the kickoff carries the 7-step list, full text VERBATIM
`docs/pick-archive.md` §trim-s269. Bind: 1 `SESSION_CURSOR.md` FIRST (<=600 B); 2 `## Session`
APPENDED (<=2 KB, each number WITH its command); 3 `<ID>` block in `NAMED.md` (<=1 KB), patch
earlier blocks IN PLACE, every VERIFIED row names its mutant; 4 `NEXT_PROMPT.md` BY SECTION to
<=12,000 B, every addition paired with a deletion; 5 skill sync only if edited (`diff -rq` then
`rsync`); 6 `git add <explicit paths>` + commit, gate GREEN + review_lint PASS; 7 submit ->
`ai_review.py <n>` -> triage ALL findings in one reply, re-measure at head, merge ONLY on a
verified PASS. Region-B pointers: §trim-s313-chain1 (sha1 `6f2ddbe32478`); per-id `NAMED` GOVERN.
- M348 (s326) MERGED: slots 1/2 <- Script.txt `#PRODUCEXQ/G`; M346 `drainer` RETRACTED.
- Retired result lines (B34-B38, M368-M376, VERBATIM + sha1 check): `docs/pick-archive.md` §trim-s343-chain4 (sha1 `dfe9d7b2173a`); per-id `NAMED ## <id>` governs.
- M377 (s339-c3): 0x8000 rides the WAR stamp (0x8010@0x507d1a), 0x10000 the first-contact TRUCE (0x10004, rel&0x8==0); M375's 1-reader claim RETRACTED. 8/8 `c9e99e3b7e9f0a31`.
- OPEN LEADS: who SETS 0x400 (M382); ds:0x985ba0's writer (M334); the two peace writers (pick above).
- M379 (s340-c2): +0x594 = 2 AI readers; M376 8th write RETRACTED (7 bodies; 0x92a7fc = terminal). 31/31.
- M381 (s341-c3): 0x2000 = PEACE; setter A 0x50393d (PACT third party + peace/commlink + strict might(ecx) > might(esi), peer's own scalar); setter B 0x506cf1 = not-at-war only; both rows. 9/9 `2fa1a4100ec6f4f6`, 20/20.
- B38 (s342) MERGED: `#SOCIO` 4x4x11 grid in `sim/socio.py` - M376's two vectors reproduced field-for-field, settings -> 11 totals, signature 12 add/4 reject; `0x92babc` does NOT feed `0x94e48c`. 9/9 `e0bb2deb53ecb96c`, 12 mutants. NEXT: pick (a).
- B39 (s343-c1) MERGED: `sim/relapi.py` - four relation APIs, TWO words (A `0x94d448` / B `0x94d468`, 8 dwords apart, same 2095 row scale); `0x551c40` writes B both ways, the peace block `0x523f3c/4c/58` = `551a20(0x50)`+`551a20(0x1)`+`551c40(0x2000)`, `0x2000000` skips only when A-row bit0 is set. 12/12 `1c0a06e178521ef3`, 12 mutants. NEXT: `0x53fcb3`.

- M387 (s342-c5): M380's last 2 = a verbatim pair-dword copy gated by arg7; arg7==0 writes UNWRITTEN (store unguarded), only msg 0x16 reaches it. 11/11 `c0e46fd18f2fc313`, 20/20.
- M390 (s343-c3): 0x4dabb0 DEAD-INF under every PE32 dispatch form (non-rebasable PE, 0 stored VA); 0x551cf0 arg4 = SET/CLEAR (26 one / 6 zero / 4 reg of 36). 47/47 `bafd75107d142bc4`, 16/16 mutants.
- M389 (s343-c2): 0x4dadxx CLOSED - the 5 OPEN mask args are verbs: FUN_004dadd0's 7 arms {1,2,4,8,0x10,0x1000,0x2000} (4 `mov ebx/edi,imm` at 0x4daea3/0x4daf07/0x4dafcf/0x4db035), each a FUN_0x6051fa-keyed SET/CLEAR (0x551a20/0x5518f0; 0x551cf0 flag for 0x1000/0x2000); FUN_004dacc0(owner,other,{0x20,0x2000000,0x400,0x40000}) = the only 0x400 host; no arm can ask 0x400/0x800. 60/60 `05a36a50540466f3`, 27/27. NEXT: the .rdata slot VA 0x677ff8's table owner.
- M391 (s343-c4): `and 0xfaeef378` is 3 masks x 2 rows gated on mask-arg bits 0x7/0x10/0x17, not a blanket; 0xc00 clearers = 5 instr / 2 fns, and both explicit 0xc00 clears are the `not`+`and` half (0x4db11b 0xc20, 0x519bb5 0xc00); 0 of 65 masks carry 0xc00 -> 24 WAR-arm callers always drop it. 53/53 `76148839fd85b66e`, 14/14. NEXT: 0x4dad30 can carry 0x400 (M389) - a 6th dynamic bit10 clear; 0x4db02d/0x4db08d remain UNKNOWN.
- M392 (s343-c5): the UNINIT leg is LIVE - 64/65 callers push guard=1, 0x52d873 pushes 0 with its id from `mov ax,WORD PTR [ebx+0x10]` (no static filter; the only literal 0x16, 0x58459d, pushes 1). 10/10 `3b27a4bd7c31181b`, 22/22 mutants. NEXT: the record's +0x10 writer.
- M393 (s342-c6): the second agenda pair +0x588/+0x590 has NO producer — 0 stores in four censuses (disp32 incl. RMW, folded, string ops, seeds), the image is loader-zero and only the save/load byte mover touches it; 2 of 3 consumers cannot fire and the 3rd reduces to `A.pair1==(0,0)`, which FIRES via slot 0. 31/31 `72f86628daea0dd9` (`evidence/m393_pair2.txt:106`), 19/19. NEXT: the agenda readers / slot 0's owner.
