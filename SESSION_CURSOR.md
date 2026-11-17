B22 GREEN post-review on `milestone/b22` (501a3be code, a286e59 docs, 026200a submit checkpoint,
b2b357d review round). PR **#286** open; Greptile PASSED the first head with 4 inline comments and ALL
FOUR WERE ACCEPTED:
1. (P1) my G5 "count and shape DISAGREE by exactly the unit growth" was MY ARITHMETIC - image A's count
   formula (`units_off + 52*(n_units+1)`) compared against image B's scan anchor. `sim/save` derives
   `units_off` FROM `bases_off`, so per-image `bases_pred == bases_off` and `closes` is True on
   orig/B21/B22. The gate text now states the retraction instead of the false claim.
2. (P2) G9 re-read the corrupted image at its own call site, so a regression making the real leg read the
   MODEL stayed green. Fixed: ONE shared producer `record_from_image(image, idx, head)`; corruption of
   tile AND faction; assert the created unit CARRIES the perturbed bytes.
3. (P2) NAMED evidence citations were one line off after the evidence regenerated; rewritten and now
   machine-resolved (every cited line must contain the gate label its row names) - CITATIONS_RESOLVED.
4. (P2) a skill law I wrote THIS fire claimed `milestone.py start` can branch off a stray worktree tip;
   `cmd_start` checks out main, pulls --ff-only, THEN branches, so it never can. Rewritten to "query
   `git merge-base --is-ancestor`, never assert either way".

ACCEPT CONFIRMED after the fixes (re-run it yourself before merging - a green line from a stale module is
worthless): `python3 -m sim.selftest --b22 programs/saves/m54b_clean.SAV` -> PASS B22: 12/12;
`python3 -u -m sim.composedgrowth` -> the same 12 labels, two runs byte-identical (report digest
06dd4ac599fd0..., written image sha256 f7d90eb77ca7abac); `evidence/b22_composedgrowth.txt` equals a fresh
rerun; G12 runs the mutation experiment in-process on every invocation.

NEXT FOR THIS FIRE (budget-tight - `git add -A && git commit` before anything else):
1. b2b357d shipped corrected CODE with stale SESSION_NOTES / NEXT_PROMPT / SESSION_CURSOR (my patch
   script aborted on a wrapped anchor and the commit ran anyway). Commit the corrected trio, push, then
   `gh pr checks 286` and wait for BOTH gate and Greptile green on the NEW head;
   `gh api repos/wronglebowsk/smac-re/pulls/286/comments --jq length` to confirm no new comments; then
   `python3 scripts/milestone.py merge 286`.
2. Cursor handoff to main via its own PR, then author **B23**: the queue's PER-TURN progress composed
   through the WRITER (B11's law exercised in the written container, not in memory). Rung text goes in
   BUILD_SPINE.md first, the module second.

LAWS THIS FIRE EARNED (all already in the skill): measure a locator PER IMAGE, never cross-image; ONE
shared producer for a falsifier and corrupt EVERY claimed input source; PROVE the falsifier discriminates
inside a gate (mutate the source, assert the mutant's signature, declare which gates are blind and why);
grep a module for duplicate `def`s after adding one (the later def wins and the test stays green on the
wrong path); for a grown container print a BAND MAP, never a single lift amount; count the diff instead of
deriving it from a model of the fields; re-resolve every evidence citation after regenerating evidence;
never let `git commit` follow a failed patch step in the same chain.
