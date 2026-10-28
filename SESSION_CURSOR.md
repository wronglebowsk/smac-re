M77 | acceptance m77gate1 NOT RUN YET | not merged | static done: gate block 0x4f0591-0x4f05de;
sweep entered only by fall-through 0x4f05e0; live DAT_00920434=0, DAT_00985b10=0x08 (owner 3
bit SET), DAT_00985abc bit20=1 -> route B admits; else-branch 0x4f05bd MARKSET dead while
0x920434==0. Instrument scripts/m77_gate_trace.py written.
next: timeout 500 python3 scripts/m77_gate_trace.py --tag m77gate1
