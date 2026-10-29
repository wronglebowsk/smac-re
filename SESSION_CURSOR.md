M99 GATE FIXES APPLIED, RE-RUN: scripts/m99_param2.py --tag m99p3 --boundaries 2.
m99p2 FAIL 11/13 (floors untouched; the ANSWER is already proven: G5 sole caller 38/38 ret
0x4f35d0, G6 model 38/38, G13 carry poke discriminates, G9 read-back, G10 static writers).
The 2 FAILs were MY gates: (a) G7 seeded fac3's carry from the pre-run read (60) but the
harness POKES it to 0 between the read and the hit -> first hit per round now expects the poked
value; (b) G8 paired C1/A1 per faction but FUN_005aadf0 returns early when param_2 <= 0 (one C1
at r64 fac6 p2 0 has no A1) -> filter p2 > 0. LIVE FACT: ebx == param_2 on 37/37 calls - the
AI "double param_2" leg NEVER runs in single-player (FUN_005312d0 returns 0) -> M98 framing
retracted. Not merged. Next: read the ACCEPTANCE line.
