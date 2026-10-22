#!/usr/bin/env python3
"""Scan terran.exe on-disk sections for little-endian dword pointers to given VAs.
Complements callgraph.py (which only sees E8 direct calls): this finds function
POINTERS stored in tables/vtables, i.e. how an indirect-only function gets invoked.

  python3 ptr_xref.py 0x522240 0x521070 ...
Prints each hit as the VA of the pointer slot + which section it lives in.
"""
import struct, sys
sys.path.insert(0, '/home/n100/reverse/smac')
import exe_strings as S

EXE = open('/home/n100/reverse/smac/terran.exe', 'rb').read()

def scan(va):
    hits = []
    pat = struct.pack('<I', va)
    for name, va0, vsz, rp, rsz in S.SECS:
        if name == '.reloc':
            continue
        blob = EXE[rp:rp + rsz]
        i = 0
        while True:
            j = blob.find(pat, i)
            if j < 0:
                break
            if j % 4 == 0:
                hits.append((S.off2va(rp + j), name))
            i = j + 1
    return hits

for spec in sys.argv[1:]:
    va = int(spec, 0)
    h = scan(va)
    print(f'== pointer slots containing {va:#07x}: {len(h)}')
    for slot, sec in h[:40]:
        print(f'   slot {slot:#07x} in {sec}')
    if len(h) > 40:
        print(f'   (+{len(h)-40} more)')
