M79 | acceptance m79net5 PASS (g1-g9) | submitted? not yet | next: git add -A && git commit, scripts/gate.py
--base main, milestone.py submit, gh pr checks <n>, milestone.py merge <n>
| finding: the 0x100 marker gate is `netgame(0x920434)==0 || !(human-mask 0x985b10 & 1<<owner)`;
| poking netgame=1 at 0x4f05a5 fired MARKSET tid=194 and skipped the clear pass (end census
| 192=0x105 193=0x145 194=0x145). next pick M80: the record indices >= 256 + FUN_00573a90 sweep.
