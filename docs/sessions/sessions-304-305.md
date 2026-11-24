# Session notes archive — sessions 304-305

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: Session 307 lives in `docs/sessions/sessions-307-307.md`; that archive points to
`docs/sessions/sessions-300-305.md`. The hot file cites only THIS archive, so
the chain onward lives here; without this line the older archives are orphans (s292).

## Session 304-chain2 (2026-11-19, M328 CLOSED, STATIC: the two HURRY globals named)

- milestone/m328 (main b362948). A=0x91c64c = TURN-START ENERGY SNAPSHOT of the upkeep faction: 520540@52065d A:=ENERGY[8380*arg] after debt pay, before interest; HURRY mirrors cost (41a551/41a563); INFRASTRUCTURE warn 51fe90 (11E-10A<0 && E<100, DERIVED) deadness INFERRED: post-snapshot stores 520743/770/7d9/7ff+4f5c8c all additions, clobber-aware (deeper callees OPEN). B=0x920434 = 'MULTI' SESSION FLAG (noun INFERRED, lifecycle V): 634 refs 15W/133T/486R, {0x14,1x1} all mov; sole 1=57ed04 first stmt 57ecf0 via menu case4@580070/auto-start 5229b7; SP 57c550+load never set; blob [91f750,+ce0) ends B-4 (A/B uncarried); opener opts 0x10c0 iff filename!='multi' && B==0; B!=0 -> diplo sync 584010 (546800:40); clear=Retire/REALLYQUIT/YOULOSE2/MULTIDEBUG/opening/SAVEFAILED/RESET. M326 deferral = multi-only.
- `python3 -u scripts/m328_hurry_globals_census.py` -> **14/14** **030a6fc12e4a7cd7** x2 identical (`evidence/m328_hurry_globals.txt:85-86`,`_rerun.txt:85-86`; pre-review 79deb5e6c5c501ff, review-round fc6b8c0db4ef4cef). Resolver=M326 import + sole-def fallback (512b40 pair 0: sole xor@512b63) + seed scan (0 indirect).
- Sweep found 2 REAL gate defects, fixed: G2 hardcoded eax (MU3 invisible) -> actual src; G5 stray A-count (MU24) -> removed. `python3 -u scripts/m328_mutate.py` -> **38/38 (37 scored+MU26 NO-OP)** **36259eee0736d9c1** (`evidence/m328_mutate.txt:41-43`; pre-review 27/27 50f6aa12d28d4b2f, review-round d3d1e9b563f55dd7); `--selftest` **5/5** (`_selftest.txt:7`).
- NAMED rotation VERBATIM sha1-asserted: B10 rows 1,988 B d298981e8ece0d6e -> docs/named-archive-b10-rows.md; founding table 8,112 B 5e1635282e3cf2c9 (19 names kept) -> docs/named-archive-founding-table.md; 248,242 -> 242,777 B. M326 one-liner -> pick-archive §trim-s304-chain2 (a) f6691830bcd4c739.
- Env: git 2.53 ignores worktree info/exclude -> extensions.worktreeConfig + worktree core.excludesFile (symlinks ignored; start unblocked).
- OPEN: B menu label (script-driven; MULTIMENU 692018 no push); 92bdf8 mode; +300 upkeep refund 1/3 (diff4) 2/3 (diff5+) 520714-78f (M325 lead); facprofile+4ec interest.

## Session 305-chain2 (2026-11-19, M328 mechanical landing + L2b pin round; STATIC, zero box)

- Confirmation run #3 of the review-round census (post int(x,0) shl-parse fix): 14/14 fc6b8c0db4ef4cef, stdout BYTE-IDENTICAL to the then-worktree evidence (diff rc=0).
- Gate/lint then caught what the reviews missed: review_lint L2b — 5 review-round mutants (MU29/31/32/37/38) patch sites the instrument reads only via computed walks (prologue, add-def backscan, fread push-window, lifecycle enumeration, opener gap), so the patch addresses were not LITERAL-read. FIX = strengthen, not weaken: 5 exact-address pins (prologue tuples 57ecf0..57ed03 incl 57ecf3; G4 def sites 520741/52076e/5207d7/5207fe+4f5c85; G9 fread branch pair 596aed/596af2/596af3/596af5/596afc; G7 the 9 lifecycle sites incl 51f267; gap tuples 5981dc/5981e2/5981ec). Skill drift from chain 1: rsynced LIVE -> skill/ (legal content sync).
- Re-measured suite: `python3 -u scripts/m328_hurry_globals_census.py` **14/14** **030a6fc12e4a7cd7** x2 byte-identical (`evidence/m328_hurry_globals.txt:85-86`,`_rerun.txt:85-86`); harness **37/37 scored + 1/1 NO-OP, 0 MISMATCH/CRASH** **36259eee0736d9c1** (`evidence/m328_mutate.txt:41-43`) — MU29={G5,G6,R2} MU31={G4} MU32={G9,R3} MU37={G6,G7} MU38={G9} all redden EXACTLY declared; `--selftest` **5/5** (`_selftest.txt:7`). Supersedes fc6b8c0db4ef4cef/d3d1e9b563f55dd7 (review-round) and 79deb5e6c5c501ff/50f6aa12d28d4b2f (pre-review). NAMED ACCEPT + s304 + NEXT_PROMPT M328 line carry the final numbers; s304 DEAD->INFERRED downgrade kept.
- Reviews: run 1 (`evidence/ai_review/pr336_20261119_233753.md`) TRUNCATED at 16384 (7 findings) -> re-run at 32768 (`pr336_20261119_234443.md`, 10 = 4 P1 + 6 P2) = completion, not second opinion. All 10 accepted + fixed (s304 round); run 1's 7 map onto the same fixes. ONE triage reply on #336 covers both + the L2b round; 4 sidecars folded.
