#!/usr/bin/env python3
"""M361 (chain2, STATIC): the A/V radio flag dwords — every reader.

M360 left the three/four two-state dwords at dialog-object offsets
0x136d4 / 0x14220 / 0x14d6c / 0x158b8 with only the relabel dispatcher
0x493ec0 known.  This script answers: who READS them, what the relabel path
does with the answer (0x493ec0 -> 0x61482f -> 0x5fa1e8), and whether any
other consumer exists.

Method: census the literal displacements in the full objdump
(scratch/m574/text.txt), attribute each site to its containing function,
classify the addressing form (field load / field store / pointer arithmetic),
then resolve the dispatcher's jump table at 0x493fe0 out of the image and
derive the widget-stride family (base + k*0xb4c; flag at +0xa18, text buffer
at +0xa7c).

Gates are printed as a table FIRST, then asserted; every VERIFIED row has a
mutant in scripts/m361_mutate.py.
"""
import bisect
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
IMAGE = os.path.join(ROOT, "programs/terran.exe")

FLAGS = [0x136D4, 0x14220, 0x14D6C, 0x158B8]
WIDGET0 = 0x12CBC
STRIDE = 0xB4C
FLAG_OFF = 0xA18
TEXT_OFF = 0xA7C

rows = []
with open(os.path.join(ROOT, "ghidra_out/index.csv")) as f:
    head = f.readline().strip().split(",")
    for line in f:
        if not line.strip() or line.startswith("#"):
            continue
        d = dict(zip(head, line.rstrip("\n").split(",")))
        rows.append((int(d["addr"], 16), d["name"], int(d["size_bytes"])))
rows.sort()
STARTS = [r[0] for r in rows]


def fnof(pc):
    i = bisect.bisect_right(STARTS, pc) - 1
    if i >= 0 and pc < rows[i][0] + rows[i][2]:
        return rows[i]
    return (0, "?", 0)


def instructions():
    """yield (addr, mnemonic, operand_text, raw) from the objdump window file"""
    pat = re.compile(r"^\s*([0-9a-f]{6,8}):\s+([0-9a-f ]+?)\s{2,}(.+?)\s*$")
    for line in open(TEXT, errors="replace"):
        m = pat.match(line)
        if not m:
            continue
        addr = int(m.group(1), 16)
        asm = m.group(3)
        parts = asm.split(None, 1)
        yield addr, parts[0].lower(), (parts[1] if len(parts) > 1 else ""), m.group(0)


def field_sites(insns, disp):
    """every instruction whose OPERAND TEXT carries +0x<disp> as a memory field"""
    out = []
    needle = "0x%x" % disp
    for addr, mn, ops, raw in insns:
        if needle not in ops:
            continue
        # field access = [reg+0xdisp] with nothing else added; reject [reg*4+0xdisp]
        if re.search(r"\[\s*[a-z0-9]+\s*\+\s*" + needle + r"\s*\]", ops):
            out.append((addr, mn, ops))
    return out


def main():
    insns = list(instructions())
    print("# M361 — A/V radio flag dwords: readers")
    print("corpus: %d instructions, %d functions in index" % (len(insns), len(rows)))

    # ---- 1. literal field census -------------------------------------------
    print("\n-- G1 literal field census (exact [reg+0x<disp>] addressing) --")
    fam = {}
    for disp in FLAGS:
        sites = field_sites(insns, disp)
        fns = {}
        for addr, mn, ops in sites:
            f = fnof(addr)
            fns.setdefault((f[0], f[1]), []).append((addr, mn, ops))
        print("0x%x: %d sites in %d functions" % (disp, len(sites), len(fns)))
        for (fa, fname), lst in sorted(fns.items()):
            kinds = {}
            for addr, mn, ops in lst:
                k = "load" if re.match(r"mov\s+(e[a-z]{2}|[abcd]l|[sd]i)\s*,", mn + " " + ops) else mn
                kinds[k] = kinds.get(k, 0) + 1
            print("   %-20s %-14s %2d  %s" % (fname, hex(fa), len(lst),
                  ",".join("%s:%d" % kv for kv in sorted(kinds.items()))))
        fam[disp] = {fa for fa, _ in fns}

    # ---- 2. family partition ----------------------------------------------
    print("\n-- G2 family partition: functions touching >=2 of the four --")
    allfn = set().union(*fam.values())
    for fa in sorted(allfn):
        hit = [d for d in FLAGS if fa in fam[d]]
        print("   %-20s %s %s" % (fnof(fa)[1], hex(fa),
              " ".join("0x%x" % d for d in hit)))
    family = {fa for fa in allfn if sum(1 for d in FLAGS if fa in fam[d]) >= 2}
    loners = sorted(allfn - family)
    print("   family=%d loners=%d %s" % (len(family), len(loners),
          " ".join(hex(x) for x in loners)))

    # ---- 3. jump table -----------------------------------------------------
    print("\n-- G3 dispatcher jump table @0x493fe0 --")
    tgt = []
    with open(IMAGE, "rb") as fh:
        for k in range(4):
            fh.seek(0x493FE0 - 0x400000 + k * 4)
            tgt.append(struct.unpack("<I", fh.read(4))[0])
    for k, t in enumerate(tgt):
        print("   cmd 0x%x -> 0x%x" % (0x4B + k, t))

    # ---- 4. relabel chain --------------------------------------------------
    print("\n-- G4 relabel chain 0x493ec0 block -> 0x61482f -> 0x5fa1e8 --")
    blocks = []
    for k, t in enumerate(tgt):
        win = [(a, m, o) for a, m, o in insns if t <= a < t + 0x40]
        flag = None
        wid = None
        for a, m, o in win:
            fm = re.search(r"\[e[a-z]{2}\+0x(136d4|14220|14d6c|158b8)\]", o)
            if fm and m == "mov":
                flag = int(fm.group(1), 16)
            wm = re.search(r"\[e[a-z]{2}\+0x([0-9a-f]+)\]", o)
            if m == "lea" and wm:
                wid = int(wm.group(1), 16)
        sids = re.findall(r"\[e[a-z]{2}\+0x(10e[0-9a-f]|10f[0-9a-f])\]", " ".join(o for _, _, o in win))
        blocks.append((0x4B + k, t, flag, wid, sids))
        print("   cmd 0x%x @0x%x flag=0x%x widget=0x%x strings=%s" %
              (0x4B + k, t, flag or 0, wid or 0, [hex(int(s, 16)) for s in sids]))

    # ---- 5. widget stride --------------------------------------------------
    print("\n-- G5 widget geometry (base = 0x%x + k*0x%x) --" % (WIDGET0, STRIDE))
    for k, (cmd, t, flag, wid, sids) in enumerate(blocks):
        want = WIDGET0 + k * STRIDE
        print("   cmd 0x%x widget=0x%x expect=0x%x %s flag_expect=0x%x %s" %
              (cmd, wid or 0, want, "OK" if wid == want else "MISMATCH",
               want + FLAG_OFF, "OK" if flag == want + FLAG_OFF else "MISMATCH"))

    # ---- 6. setter 0x5fa1e8 ------------------------------------------------
    print("\n-- G6 setter 0x5fa1e8: callers --")
    callers = []
    for a, m, o in insns:
        if m == "call" and "0x5fa1e8" in o:
            f = fnof(a)
            callers.append((a, f[0], f[1]))
    print("   %d call sites in %d functions" % (len(callers), len({c[1] for c in callers})))


if __name__ == "__main__":
    main()
