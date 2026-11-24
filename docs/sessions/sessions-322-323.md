# Session notes archive — sessions 322-323

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-320-321.md` — the hot file cites only THIS archive, so
the chain onward lives here; without this line the older archives are orphans (s292).

## Session 322-chain2 (2026-11-24) — M341 merge land (PR #361)

- **UNBLOCKED, MERGED:** the "zero CI runs" blocker was the PR, not the workflow —
  GitHub schedules no `pull_request` run while `mergeable_state=dirty`. `git merge origin/main`
  (a0aa8fc, #362's 34 restored NAMED blocks) kept BOTH 321 sections and auto-merged
  NAMED/NEXT_PROMPT; one conflict (SESSION_NOTES, both appended at EOF) resolved keep-both.
- **VERIFIED at the branch head `179fef5`:** `gate.py --base origin/main` -> `GATE GREEN` (11 passes,
  1 branch-name warning — the documented `milestone/M341` vs `milestone/<id>` warn line, noise);
  `review_lint --id M341` -> PASS (8 V rows); `m341_hof_window.py` -> `PASS M341: 11/11 gates`,
  `digest=1cfdea39295dadce`, `table_sha256=b5820ac99801f8c4`, stdout byte-identical to
  `evidence/m341_hof_window.txt:45-58` (gates `:1-44`, harness `evidence/m341_mutate.txt:21`);
  `git diff 446958b 179fef5 -- scripts/m341_* evidence/m341_*` empty (same instrument bytes
  as the measured head). NOTE both printed names are **truncated sha256** — `m341_hof_window.py:520,524`
  take `.hexdigest()[:16]`, so "sha256" here means the first 16 hex of it, not a 64-char digest.
- **CI:** `gate` PASS 18 s, run 45324343569 (job 138210194052) on 179fef5 — the first run for a
  head newer than 03:38Z. The squash commit's tree IS the gated tree:
  `git rev-parse 179fef5^{tree} 185c394^{tree}` -> both `702938a3f8bef770f822c2c0e2db157deeb12276`.
  Merged `--squash` as **185c394**.
- **MAIN CHECK** (`git show origin/main:NAMED.md | grep -c '^## '` / `grep -c '^## M341'` / `wc -c`):
  NAMED 111 blocks (110 pre-merge + `## M341`), 248,127 B, `## M338` stub intact, no block lost
  (`comm -23` of main's block titles vs the merged file -> empty).
- PITFALL: `milestone.py merge` ends with `gh pr merge --delete-branch`, which dies on
  `'main' is already used by worktree at /home/paul/reverse/smac` — the merge itself SUCCEEDS
  server-side; verify with `gh pr view <n> --json mergeCommit,mergedAt` and leave the branch
  (older milestone/* branches linger anyway).
- **ABSENCE CLAIM is a LEAD, not a gate result:** `0x59f4 has NO named writer` is NAMED M341's
  OPEN row (kind `lead`, no mutant); the V half — "the only direct ref in 781,379 insns is the load
  0x44970f, 12 indexed hits are a different array" — names MU8. Byte-identity above is asserted
  against the committed file (`diff <(...) evidence/m341_hof_window.txt` -> empty), so it is
  reproducible from the repo, not from a transcript.

## Session 322-chain1 (2026-11-24) — M342: pick (x9) the COMPLETION SETTER, answered statically (milestone/m342)
- **Answer:** the `base+0x8c` bit is SET by `or` through mapper `FUN_00507410`'s mask at exactly **11 addresses** (`4e4528` = the API `FUN_004e44f0`, `4f0ec0` = base screen `FUN_004ef6d0`, `4f3ebc`/`4f3f4c` = regions the Ghidra index does not name, + `FUN_004e47d0`'s 7); CLEAR = 3 `and` (`4e4546`, `4f38bb`, `4f49e1` — the last inside the charge routine `FUN_004f47f0`).
- **Accept:** `python3 -u scripts/m342_completion_setter.py` -> `PASS M342: 7/7 gates`, digest `2b88df5da5aeafe1` (`evidence/m342_completion_setter.txt:200`), PASS `:218`, 2 runs byte-identical. Harness `scripts/m342_mutate.py` -> `PASS HARNESS M342: 9/9`, NO-OP `[]`, baseline green (`evidence/m342_mutate.txt:2,:12`).
- **Writer census (the pick's question):** the field has exactly 2 idioms — 11 direct constant-form stores in exactly 2 indexed functions, and 9 pointer-form `lea` sites, 9/9 resolved to a store through that register (2 copy / 4 `or` / 3 `and`) (`:86`). The API `FUN_004e44f0(item, base, set)` is a 92-B set/clear: `or BYTE PTR [eax],cl` @`0x4e4528`, `and` @`0x4e4546`, index = mapper out1 `[ebp+0x8]`, mask = out2 `[ebp-0x4]`, 27 call sites in 8 functions (16 set=1 / 7 set=0 / 4 variable).
- **The pop is a NON-writer:** `FUN_004ef5d0` (244 B) shifts slots (`0x4ef62c`), decrements pending (`0x4ef642`) and calls only `0x5a73f0`/`0x5a6e70`/`0x446250`/`0x473760`; 0 refs to the bitmap, 0 API calls, 3 callers all in `FUN_004ef6d0`. So B30's completion leg does not stamp the bit — the stamp belongs to whoever CALLS the API. OPEN next: which of the 27 sites is the production-completion call.
- **PITFALL (field arithmetic):** the array base is `0x95da10`, NOT `0x95da14` — `0x95da14` is the OWNER byte (+4). Reading the base as 0x95da14 makes the bitmap look like +0x88, a 4-byte error no count catches; G1 DERIVES the base from the owner site (MU1 reddens it).
- **PITFALL (RMW through a pointer):** `or BYTE PTR [..+0x95da9c]` only catches the *constant-form* stores; the pointer-form ones are `lea r,[base+0x95da9c]` then `or cl,dl; mov [r],cl`, so a store-mnemonic census counts them as copies. G2 classifies by the RMW in the 4 instructions before the store; MU8 turns that off and reddens G2.
- **NAMED headroom:** 248,127 B (1,873 under cap) -> M329 rotated VERBATIM to `docs/named-archive-m329-rows.md:5` (sha1 `ccee72a56f16b4b4`, `scripts/m342_named_rotate.py --verify` PASS, idempotent) -> 241,089 B before this block.

## Session 323-chain1 (2026-11-24) — M344: the COMPLETION CALLER (milestone/m344)
- **Answer:** NO API caller completes production. The `base+0x8c` stamp for a finished item is the **inline `or` at `0x4f0ec0`** inside `FUN_004ef6d0` (the base screen), in the same block that spends the base's `+0x40` counter by `edi` (`0x4f0ca4/6`) and then reads the item-table row `[edi*48+0x984d38]` (`0x4f0f6f`) and **pops the queue 0x86 bytes later** at `0x4f0f46` (`push ds:0x68cbb0`). `edi`/`[ebp-0x30]` = the completed item, `esi`/`ds:0x68cbb0` = the current base, 304-fold `0x4f0eaa-0x4f0eb6`.
- **Accept:** `python3 -u scripts/m344_completion_caller.py` -> `PASS M344: 8/8 gates`, digest `034bf0e1a1606d2c` (`evidence/m344_completion_caller.txt:148`), 2 runs byte-identical. Harness `python3 -u scripts/m344_mutate.py` -> `PASS HARNESS M344: 10/10`, NO-OP `[]`, gates G1-G8 all covered (`evidence/m344_mutate.txt:14`).
- **The 27 sites, resolved:** every item argument resolves (0 unresolved) to imm 18 / callret 3 / clamped 2 / loopctr 2 / param 2; **0/27 take the item from the queue window `+0x4c..+0x77`**, and **0 of the 8 caller functions calls the pop** (`:74-80`). The four set=1 sites with a REGISTER item are exactly `0x41c6f8` (call-ret from the modal runner `0x5f1394` + a bitmap pre-read = toggle), `0x41d8fc` (loop counter under the `0x5a6e70` predicate), `0x508c85`/`0x508cee` (the `1..0x26` clamp of a type-2 entry). Rivals RIV1-RIV3 all FAIL on printed numbers (`:84-88`).
- **RETRACTION (M342 row):** M342's "16 set=1 / 7 set=0 / 4 variable" is **16/8/3** — its 6-instruction push window stops one push short at `0x40dd3c`, where the `push 0x0` sits 7 instructions back (`:36-38`). G1 now gates both the re-derived split and that single divergence row.
- **PITFALL:** arg order is `push set; push base; push item; call` — the ITEM is the push NEAREST the call (M342's mapping). A "reversed to program order" reconstruction silently reads the set flag as the item.
