# NAMED.md `## M330` — ROTATED VERBATIM (byte-exact) by scripts/m388_named_rotate.py

## M330 (s307-chain2, STATIC 13/13) - block+300 = UPKEEP SPEND ACCUMULATOR

| claim | evidence | conf |
|---|---|---|
| 25->11 FIELD (4W/7R STRIDE)+2 arg-fed; 14 excl | G1/G12 `evidence/m330_block300_census.txt:2,31,64` | V MU12-14,17-19,28-30 |
| W={4f4962,52056d 0,52078f resid,59f26a reset}; refund 520714-78f: 985aec>3,x!=0: r=trunc(kx/3) k=1(==4)/2(>=5); E+=r,x-=r; magic 55555556; mask VACUOUS | G2/G4-6 `:43,45-51` | V MU1-8,25,26,32 |
| feeder 4f47f0 ROUND>1: v=[984d48+48*slot] (bits 95da9c); CONDITIONAL halving (owner-match +bit5 parity /2 else FULL); E-=v,+300+=v | G10 `:58-59` | V MU9,10,22-24 |
| entry zeroes +2fc/300/308/3f8; +310:=+2fc; +30c:=+308-300+2fc; carry (M324) vals=[0,1,1,0,1,0,1,1] | G7-9/11 `:52-57,61` | V MU8,11,15,16,21,27 |
| ACCEPT 13/13 digest 470d844054b1b101 x2 (`:67-68`,`_rerun.txt:67-68`); 31/31+1 digest cf85092dea6baa93 (`evidence/m330_mutate.txt:36-38`); ST 5/5 (`evidence/m330_mutate_selftest.txt:6`) | cite | V |
| OPEN: slot; ~~985aec~~ ANSWERED M332 (runtime mirror of the INI pref "Difficulty", master 0x92bde8); ~~+2fc/+308~~ ANSWERED M331 (income siblings); profile+300 | - | lead |
