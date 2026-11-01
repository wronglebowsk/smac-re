S192 M241 IN FLIGHT (box-first: the M181 falsifier) — this run owns the measurement.
acceptance: `sudo -n python3 scripts/m241_m181_control.py` -> `PASS M241: 5/5 gates`
-> evidence/m241_m181_control.txt. Two UI saves: A = no-tracer 2 ms sampler over the 16 staging
dwords at 0x99aa1c; B = 41 silent counting bps (33 census stores of ds:0x99aa38, the 4
`call 0x41a8f0` sites, 0x41a8f0 entry, 0x41abd4 post-pack, GOVERNORCONTROL writer 0x512020 +
0x512069). Verdict = CONFIRMED (stores fired) or REFUTED (0 stores with G1/G2/G4 passing).
merged? no. box time owed: M181 until a verdict prints. terran.exe 319926 TracerPid 0 at arm.
