M118 ACCEPTED (m118flag PASS): bit 0x40 has NO setter and 0 of 12 saves carry it -> the M89 second ask is inert BY CONSTRUCTION (byte test 0x5aaf7f, take 0x5aaf88, 17 hits/turn). The only or al,0x40 reaching a store (0x4dc226->0x4dc296) writes a DERIVED copy into ds:0x99aa38 after reload+mask 0xfc3fffff.
main efa4aa2 after #116-#128; branch milestone/m118 NOT merged. BOX: terran.exe loaded m54b_clean (67/18), TracerPid 0.
next: the second ask is closed by construction; pick from STILL OPEN (chooser case 7 / bit 5 at 0x531782 / when 0x59f0c7 runs).
