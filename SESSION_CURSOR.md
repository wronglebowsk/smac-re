M311 GREEN, NOT SUBMITTED. Branch milestone/m311, commit 445cf02. ACCEPT:
`python3 -u scripts/m311_recidx.py` -> PASS M311: 7/7, two runs identical, digest dd0ddccb5a1bcad4.
FINDING: 0x68cbb0 = CURRENT-RECORD INDEX of the 304-B array at 0x95da10; 0x8f0d60 its derived
POINTER (6 stores each, paired 1:1 at +6..25 B). Picks (a) AND (b) are ONE object: 0x95da40 =
0x95da10+48 (pinned by 0x4f5aab). Setter FUN_004e3470 = 34B/11 insns/57 callers.
OPEN: scripts/m311_mutate.py (11 mutants) running in background proc_cb6fa7552e98 — READ ITS
OUTPUT before quoting N/N in docs (5/8 was pre-fix). THEN close order: gate -> Session 274 ->
commit -> NAMED M311 -> NEXT_PROMPT (retire picks a AND b) -> submit -> read every Greptile
inline -> merge. Docs NOT yet written. Zero box time.
