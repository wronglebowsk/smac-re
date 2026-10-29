M96 RUNNING (branch milestone/m96, s151). Q: the human leg of the tech chooser FUN_005aa030.
STATIC DONE (bytes): 0x5aa164 gate ds:0x985ac4&0x200 -> score=(score<<8)/max(FUN_005a6d40(prereq1,1),prereq2,1);
human mask 0x985b10 bit guards ONLY the sibling early-return ([fac*8380+0x94d810]/[+0x94d818]!=0 && idx==WORD ds:0x98adee -> ret idx @0x5aa251);
0x5aa204 human -> FUN_00625af1(0,score+1) = thiscall FUN_00625a0f(&ds:0x999fa0): state=state*0x19660d+0x3c6ef35f, val=((state&0xffff)*(hi-lo))>>16+lo; non-human 0x5aa217 -> rand()%(score+1).
bVar14 (shard_009.c:9343) = (ds:0x985ac4 & 0x200)!=0 && param_3<=0 — what lets a mask-set faction take the 0x5aa030 leg.
RUNNING (do NOT start a competing measurement): scripts/m96_human_leg.py --tag m96human1 --rounds 3 (pid 739952, session proc_7bb16714413a) -> scratch/m96human1.out, evidence/m96human1.gdblog. Poll with process_manage.
Box: m54b_clean r61, screen hud (normalized), evidence 27.8 MB.
