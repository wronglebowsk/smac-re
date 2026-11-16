# Session notes archive — sessions 250-251

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 250 (2026-11-11, zero box time) - #262 finished: attestation v2 + all PR reviews disposed, MERGED

s249 died mid-close-out before running scripts/s249_attestation.py, leaving
PR #262 (M297 LIVE-MAP census) open with two unread reviews (Greptile 1xP1
snapshot-vs-history + 4xP2; hermes-review 4xP1 + 2xP2). Dispositions, all in
the PR body: (1) hermes P1 starttime bug CONFIRMED - /proc/PID/stat split on
") " leaves idx 0 = state letter, starttime = idx 19; fixed in
scripts/s249_livecensus.py (S0/S8 + attestation A6 amendment: the hygiene
claim stands WITHOUT the token - pins 2212/3 + TracerPid 0->0 + map identity
2100/2321). (2) hermes P1 S7 gate(True) CONFIRMED - now asserts independent
recounts of both no-go counters + owner coverage + t7-dist == 8482. (3) hermes
P1 S3 attestation CONFIRMED - drift_taxonomy(): a miss is attested ONLY by a
machine grading event LATER on the same tile (the 97-row/9-tile multival set
was a lower bound; bit4 flips are val-invisible). (4) hermes P1 owner-silent
CONFIRMED in code (row_no_owner/pool_no_owner counted + gated) but machine-
CLEAN on the shipped run: all 115 visit units in [0,2500), owners loaded for
exactly that set. (5) Greptile P1 caveat made explicit in addendum A5 + NAMED
rows + PR body: every live verdict is END-WINDOW - a tie NOW != a tie at the
skip. (6) Greptile/hermes P2s: attestation v2 DERIVES the A1 scorecard from
the shipped gate lines - now prints P6 PARTIAL-MISS (R2 42/R3 42 vs predicted
>=50 floors, save-side 124/119, live mask 0x8 shrinks mask-gated collisions);
the hermes P2#1 "P4 printed 0" claim was WRONG (shipped line shows 2434; its
dead `if False` line removed anyway). `python3 scripts/s249_attestation.py`
once: **A0 shipped-verify PASS 25/25** - every bin-derivable number on the
shipped gate lines reproduces exactly under the fixed instruments (2102/0/
134/85, 201 attested/18 unattested, 7518/287/677/0/0, t7-dist, identity
2100/2321, (19,6) 0x5/0x10/value 0, tie ROWS 0, owner coverage). Census gate
state unchanged: FAIL M297 1/7, S3 = the documented finding (floor NOT
weakened). Merged #262 after the MERGE-RULE wait. Next: s251 small statics.

## Session 251 (2026-11-11, STATIC, zero box) - M298 SMALL STATICS pair CLOSED

No /proc, no gdb, no box contact (s244 state untouched since s249's read-only pass).
Milestone: the two holes M294 left OPEN in FUN_0051dcb0 (sole site_gate writer).

- (a) 0x582cc0 body pinned (19 insns): push/pop ebp + eax/ecx/edx only, ZERO
  edi/esi/ebx writes => edi (0x5aff90 return, copied 0x51df9f) SURVIVES the call into
  the slot-max 0x51dfc3 and the cell-max 0x51dfee-51dff3 (no reload; both maxes); 0x51dfac reloads eax over only the
  DISCARDED return (rec base, lea 0x582ce6). Effect = CACHE WRITE-BACK: BYTE[rec2+2] =
  (old&0x0F)|(param_3<<4), rec2 = [0x92ae14]+0x2c*([0x692184]*param_2+sar(param_1,1)) -
  the same +2 high nibble the cached-path test 0x51df85 reads: next walk skips
  0x5aff90 (525 insns).
- (b) [ebp-0xc] caller hypothesis REFUTED: own frame (0x51dcb1 mov ebp,esp; 0x51dcb3
  sub esp,0x1c), void/0-args; EXACTLY ONE store in 386 insns: 0x51dd57
  mov [ebp-0xc],ecx = zero-extended BYTE[rec+3] (xor ecx 0x51dd48; mov cl,[edi+3]
  0x51dd4f); record cursor base [0x92ae14] 0x51dd1e, +0x2c at 0x51e128/0x51e133; the
  other 5 refs (0x51dd9f/df28/dfac/e021/e0cc) loads; store precedes first load.
  Site/region index is record byte +3, not caller-supplied.
- FINDING (phrasing fix): M294's `cell addr = 0x94eca8+[ebp-0xc]+4*min(...)` wrong -
  max(edi,slot) STORED 0x51dfcb to the 28B/site slot (jle 0x51dfc5 keeps old when edi<=old) [28*[ebp-0xc]+0x989ce8] (esi via
  (x*8-x)<<2 0x51dfb1-ba); addr 0x51dfe2 = 0x94eca8+4*(2095*ebx)+[ebp-0xc] (0x51dfd3-e0
  65x/131x/<<4/-x; 4*2095 = 8380 = M297 faction block stride); cell = max(edi,old)
  0x51dfeb-f3; ebx = scan idx (xor 0x51ddf5; -1 clamp 0x51df22-24); ebx==0 skips the
  cell store (test/je 0x51dfd1), slot-max store survives. ebx's walked table
  (0x51de2c-0x51df1d) = recorded LEAD, not chased.
Evidence: evidence/s251_statics_fn51dcb0.txt (162 lines verbatim); dump
scratch/s251_fn51dcb0.txt. NAMED M298 block + line-1711 status closed. Gate GREEN.
