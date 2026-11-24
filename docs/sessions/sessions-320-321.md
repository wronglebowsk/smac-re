# Session notes archive — sessions 320-321

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-318-320.md` — the hot file cites only THIS archive, so
the chain onward lives here; without this line the older archives are orphans (s292).

## Session 320-chain2 (2026-11-24) — pick (x6): `0x5f1394` = the modal SCREEN RUNNER

- **ANSWER:** `FUN_005f1394` (11,207 B / 2,235 insns, `ret 0x8`, args = only
  `[ebp+0x8]`/`[ebp+0xc]`) is a modal-screen runner: SEH `0x66f786`, `sub esp,0x38c`, first
  `call [vtbl+0x170]`@0x5f13c6 with 0 -> `or eax,-1`; then CREATESTRUCT + `0x5e3ed9`, error
  returned VERBATIM.
- **RETURN (7 exits, one `ret 0x8`):** -1 x2, 0 x1, passthrough x2 (traced to their feeders
  `[vtbl+0x15c]` and `0x5e3ed9`), `ds:0x698d0c` x1, and **`[obj+0xa40]` x1** (0x5f3f45) — the
  only value-carrying exit; `+0xa40` is READ once and WRITTEN 0x in the body.
- **PAYOFF (closes M308's `0x4ddcf1` UNATTRIBUTED / M332's row):** `FUN_004ddaa0` stores
  `ds:0x985aec` into obj+0xa44 (0x4ddb3e/4d; the store is adjacent to the call, receiver = the
  same lea 0x4ddb47), calls the runner (0x4ddb53), and on `jge 0x4ddcf1` writes the return to
  `ds:0x985aec` + `[ecx]` each `add ecx,0x20bc` from 0x94d438 to 0x95da18 = 8 factions.
- **CENSUS:** 94 thiscall sites — 76 `lea ecx,[ebp-…]`, 14 pointer, 3 register, 1 global
  0x9210a8. **RIVAL killed:** "chooser" — 0 refs to 0x94d2ac/0x985aec inside vs 3 in the caller.
- ACCEPT `m339_modal_runner.py` -> **`PASS M339: 7/7`** `d76a5e83770b77bb` x2, `text_sha256`
  `eb9f463e…`; `m339_mutate.py` **13/13** `927a1c66c322709e`, ST 3/3.
- **Review #359 (10/10 fixed in the gates):** G0 extent (MU9), G2 exits = jumps to the ONE
  SEH-restore label + feeders traced, G4 exact census, G5 faction store/back-edge/receiver,
  G6 caller extent from the index; ALG_A1 fallthrough-only; the run prints `text_sha256`.
- **OPEN:** who writes `[screen+0xa40]`; 0x57dd45 pushes ONE dword vs `ret 0x8`; `DoModal`
  INFERRED.
- NAMED: `## M308` rotated VERBATIM to `docs/named-archive-m339-rows.md:8` (sha1
  `07cec1770614`, `m339_named_rotate.py --verify`): 249,287 -> 243,834 -> 246,196.
- PITFALL: objdump prints `[ebp-0x4]` and `DWORD PTR [ebp-0x4]` alike; long immediates
  leave 3 trailing bytes on their own line (14 gaps) — normalise both.

## Session 321-chain2 (2026-11-24) — pick (1): the HoF record-window page arithmetic (PR #361)

- **ANSWER:** the 0x983a10 record index is `5*n - 5 + s` at THREE .text sites:
  SITE A 0x449793/96 (n=[obj+0x59f4] @0x44970f, s=[obj+0xa918] @0x449715), SITE B
  0x44af9b/9e (n=[obj+0xa4c] <- ds:0x91b5b4 @0x44aeb9/0x44aed9, s from the 5-probe
  rank scan), SITE C 0x44b5a7..b9 insert-shift (src 5n+k-5 -> dst 5n+k-4, k in 0..3).
- **BOUND:** five zero-init/fault sites all measure base 0x983a10, stride 0x8c,
  inner 5, term 0x984d34 => 0x1324 = 35*0x8c = 7*0x2bc; {1..7}x{0..4} is a
  bijection onto 0..34 and index 35 lands ON the terminator: the buffer is
  7 blocks x 5 rows, not a flat 35-list.
- **NO CLAMP:** over 781,379 parsed insns the only direct 0x59f4 ref is the load
  0x44970f; all 12 further hits print as `[reg+reg*4+0x59f4]` (a different array);
  0 cmp/test on ebx between the load and the lea => the page's legality is its
  writer's job, and no named .text store to it exists (OPEN).
- **6 IS NOT ROWS:** six probes {1,2,4,8,0x10,0x20} at {0x449915,0x449985,
  0x4499f1,0x449a5c,0x449ac8,0x449b34} on byte +1 of ONE record (one ebx def:
  `mov ebx,[ebp-0x1c]` @0x449982).
- ACCEPT `m341_hof_window.py` -> **`PASS M341: 11/11`** `1cfdea39295dadce`, two runs
  diff-identical (`evidence/m341_hof_window.txt:45-58`); `m341_mutate.py` **19/19**
  `e1c003e81552f53f`, ST 4/4 (`evidence/m341_mutate.txt:21`).
- RIVALS (review-round fixed): R1 0-based page covers 0..34 as well, so bounds do
  NOT discriminate — it dies on the decoded const -5 (MU2); R2 a coherent 6-row
  page (step 6, 6 pages) reaches index 35 = terminator (MU3); R3 flat list needs
  coef_n == 1, all three sites decode (5,-5) (MU11); R4 base 0x983984 ends at
  0x984ca8 (MU4).
- NAMED: `## M338` rotated VERBATIM to `docs/named-archive-m341-rows.md:5`
  (sha1 `b82cddad74c8`, `m341_named_rotate.py --verify`).
- PITFALL: decode chains must track EVERY lea destination AND `sub reg,reg` —
  SITE B is a two-register chain (edx=slot+4n, then esi=n+edx-5), SITE C's source
  lands in edx (not ecx) and its address chains are formed by *8/sub/*5/*4. The
  address-chain eval must use the INDEX symbols (edx/ecx), not the (n,k) symbols.
- MERGE STATUS: PR #361 is OPEN with a green LOCAL gate at head; GitHub created ZERO
  workflow runs after 03:40Z (empty commit + PR close/reopen did not fire `gate`), so
  the standing "gh pr checks PASS" rule cannot be met. Left unmerged on purpose.
- PITFALL: `690k` insn counts are parser-dependent — the count is len(image()),
  printed, never hardcoded from an earlier session (790,695 vs 781,379).
- MERGE RESOLUTION (2026-11-24, round 3): the zero-runs blocker was the PR state, not the
  workflow — GitHub does not schedule `pull_request` runs while `mergeable_state=dirty`.
  Merged origin/main (a0aa8fc, #362 restores the 34 NAMED blocks) into the branch keeping
  BOTH chains' sections; push re-arms the run.

## Session 321-chain1 (2026-11-24) — B30: the COMPLETION leg executable (queue item -> +0x8c -> writer -> reload -> bill)

- **ANSWER:** a paid queue item becomes a facility the base HAS. `sim/composedfacility.py`
  reads the completion from the container's OWN queue (18 records, own player 3, 2 eligible;
  target base 0 'University Base', item 2 'Children's Creche', rule delta 1), applies the
  reader's inverse (byte `item>>3`, bit `1<<(item&7)`), and the write is ONE byte: diff
  `[140]` = `0x8c+0`, delta 4. The writer carries it (`base_writes=`, B30's byte-granular
  companion to B27's `block_writes`), 1 file byte differs, the RELOAD owns `[1,2,8]`, 17/17
  other records byte-identical, identity build byte-identical (hook inert). B29's DERIVED
  table reprices the bill 0 -> 1 (delta == rule); the "table value always" rival differs at
  exactly `[8]` (M46's disabled list), the no-write rival at 26 ids, the swapped-orientation
  setter lands on only 4/32 ids, id 39 is REFUSED.
- ACCEPT `python3 -u -m sim.selftest --b30` -> **`PASS B30: 6/6`** rows `234ab3d83a88dbea`
  print `29f408c79329a5a8` img `3a503c638ba45330` (`evidence/b30_facility_completion.txt:35-36`),
  2 runs + relay byte-identical. Harness `scripts/b30_mutate.py` -> **`10/10`**
  `76a481b5d8a7d8b0` (`evidence/b30_mutate.txt:12`), every gate G1-G6 reddened, NO-OP `[]`, ST 4/4, baseline tree green.
- **ASSUMED / census pick:** the game routine that SETS the bit is not in this rung's evidence;
  the setter is the mapper's inverse (`FUN_00507410` = the one 39-bit splitter). G2 measures the
  bijection (32/32) that makes it the only candidate.
- NAMED: M310 rotated VERBATIM to `docs/named-archive-b30-rows.md:5` (sha1
  `ca3caf3785c9d6e9`, `scripts/b30_named_rotate.py --verify`): 246,635 -> 244,146 -> 246,098.
- PITFALL: measuring the bit law on the TARGET record is confounded when the base already owns
  the id (base 0 owns 1 and 8) — the first run read 2/32; measure on a zeroed-window reference.
- PITFALL: a cross-record check must compare each record to ITS OWN original bytes (my first G3
  compared every other record to the target's and read 0/17 — a false red); and a digest must
  never hash a placeholder line appended for context, or it can never be re-pinned.
