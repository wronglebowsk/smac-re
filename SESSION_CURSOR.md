M79 | acceptance scripts/m79_netgame_poke.py --tag m79net1 (g1-g9) | NOT RUN YET | merged? no
| next command: python3 scripts/m79_netgame_poke.py --tag m79net1  (reload m54b_clean.SAV ->
| enqueue 194 idx 0 -> storage 200 -> 11 silent breakpoints incl. POKE 0x4f05a5
| (`set var *(int *)0x920434 = 1`) and RESTORE 0x4f0637 -> 4 boundaries, census APPENDED to the
| gdb log). If a gdb attach is live when this cursor is read, do NOT start a competing run.
| static+live so far (no acceptance yet): gate 0x4f0591-0x4f0637 admits the clear pass iff
| `0x920434 == 0 || !(0x985b10 & (1<<owner))`; MARKSET 0x4f05bd (`or BYTE [tid*52+0x98adb9],1`)
| needs BOTH, so it is dead in solo. Live reads: 0x920434=0, 0x985b10=0x08, 0x985b11=0xff,
| cur_player(0x985dcc)=3, 0x91e2d0=0.
