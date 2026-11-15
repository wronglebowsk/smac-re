M299 | decode + ship a gate script with cited windows - ACHIEVED:
m299_visitgate.py PASS 7/7 (evidence/m299_visitgate.txt:183):
the slot[site].counter++ (0x989ce8+4, 28*site esi) runs ONLY when
FUN_005832b0(x,y)!=0 (je 0x51e11d skips the lone inc/store; esi kept);
0x5832b0 PURE: 44-B tile_record ladder (occ 0x102000, flag 0x985ac4-2000,
0xc000000, 0x10000000, rand+1==0 ds:0x92a380) + parity (h&3)+4*(d&3);
s249 grade 481/16/12/5/1087 | MERGED #265 | next: s255 ANALYSE
(collision check, track_mode) | leads: 0x51e02c 0x94ed28 byte,
0x5832b0's 23 other callers, /proc 0x989ce8/0x94eca8, seed
