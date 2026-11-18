s276 cont.: M312 review round DONE on #292 (3 Greptile P2s all fixed at the
second head; ONE PR comment answers them). Now 27/27 digest 8751c5af18c5a8f8
(x2 identical), mutate 23/23. Fixes: A9a literal 16-insn windows x5 arms;
A8b scope = entry zero only + zero indexed band stores (M262 owns 1..7, do
NOT re-derive); fan-out 0..7 bound exclusive; A5f every x-store = 469010
result. NEXT: gate, push, poll CI ~200s, milestone.py merge 292, then
s275-style docs follow-up PR (merged cursor + LANDED line + new ## Session).
