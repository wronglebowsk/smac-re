"""Scan terran.exe for the chooser bar-button param table {0,-1,7,5,4,-2}."""
import struct

d = open("programs/terran.exe", "rb").read()
target = [0, -1, 7, 5, 4, -2]


def enc(vals, sz):
    out = b""
    for v in vals:
        if sz == 4:
            out += struct.pack("<I", v & 0xffffffff)
        elif sz == 2:
            out += struct.pack("<H", v & 0xffff)
        else:
            out += struct.pack("<b", v)
    return out


found = []
seqs = [target] + [target[k:] + target[:k] for k in range(1, 6)]
for k, seq in enumerate(seqs):
    for sz in (4, 2, 1):
        pat = enc(seq, sz)
        i = d.find(pat)
        while i != -1:
            found.append(("rot%d" % (k - 1), sz, hex(i + 0x400000)))
            i = d.find(pat, i + 1)
print("contiguous matches:", found[:14])

vals = set(v & 0xffffffff for v in target)
hits = []
for off in range(0, len(d) - 64, 4):
    w = struct.unpack_from("<16I", d, off)
    if vals.issubset(set(w)):
        hits.append((hex(off + 0x400000), w))
print("16-dword window hits:", len(hits))
for h in hits[:12]:
    print(h[0], h[1])
