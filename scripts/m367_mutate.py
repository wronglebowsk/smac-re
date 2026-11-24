#!/usr/bin/env python3
"""M367 mutation harness - every VERIFIED row of scripts/m367_label_index.py names a mutant here.

A mutant is KILLED when its named gate turns red in a real run of the tool.  Three kinds:

  TEXT  rewrites ONE instruction line of the objdump cache (the tool reads it via M367_TEXT):
        the DISASSEMBLY is mutated and the tool must notice.
  LAB   rewrites ONE line of programs/labels.txt (M367_LABELS): the DATA FILE is mutated.
  SRC   rewrites ONE line of the tool's own algorithm (M367_LABELS/TEXT stay real): the
        instrument - its element tracer and its row classifier - is mutated.

Gate coverage is MEASURED from the tool's own gate rows, not authored here.  A NO-OP mutant
(target text absent) is reported, never counted as killed.

    python3 scripts/m367_mutate.py            # ~25 runs of the tool, one temp cache each
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
LABELS = os.path.join(ROOT, "programs/labels.txt")
TOOL = os.path.join(ROOT, "scripts/m367_label_index.py")
ADDR = re.compile(r"^\s*([0-9a-f]{6,8}):")

# (name, addr, old, new, gate that must go red, claim)
TEXT_MUT = [
    ("MU1", 0x614669, "mov DWORD PTR ds:0x997b20,0x0", "mov DWORD PTR ds:0x997b1c,0x0", "G0a",
     "the free path zeroes the array pointer; moved off it, only 1 store remains"),
    ("MU2", 0x6146BB, "shl eax,0x2", "shl eax,0x3", "G0b",
     "the array is sized count*4 (shl 2); shl 3 falsifies the dword array"),
    ("MU3", 0x614707, "mov DWORD PTR [edx+ecx*4],eax", "mov DWORD PTR [edx+ecx*8],eax", "G0c",
     "the fill loop stores a dword per element"),
    ("MU7", 0x4DB9EC, "call 0x604fd2", "call 0x6050d4", "G2a",
     "a label row must end in add_item; retargeted it is no longer one of the 13"),
    ("MU8", 0x4DB9B2, "mov ecx,DWORD PTR [eax+0xda0]", "mov ecx,DWORD PTR [eax+0xd9c]", "G2b",
     "every row owns its OWN element (13 distinct offsets)"),
    ("MU9", 0x4DB53C, "call 0x61482f", "call 0x614840", "G2c",
     "the title's clamp site is excluded only because it does not feed add_item (its operand)"),
    ("MU10", 0x4DB1E4, "push 0x8", "push 0x9", "G2d",
     "the sync and the builder ask the same 13 ids in the same order"),
    ("MU12", 0x614855, "cmp DWORD PTR [ebp+0x8],ecx", "add DWORD PTR [ebp+0x8],ecx", "G3a",
     "the clamp only COMPARES its argument (an add would make it an index computation)"),
    ("MU13", 0x4DB9B2, "mov ecx,DWORD PTR [eax+0xda0]", "mov ecx,DWORD PTR [eax+0xdb4]", "G3b",
     "the 13 elements form 3 maximal runs (4,8,1)"),
    ("MU14", 0x4DB535, "mov eax,DWORD PTR [eax+0xd88]", "mov eax,DWORD PTR [eax+0xd90]", "G3c",
     "the 10-element run 0xd88..0xdac is consumed exactly once each (title at its head)"),
    ("MU15", 0x4120C4, "test BYTE PTR [ecx*4+0x94d448],0x1", "test BYTE PTR [ecx*4+0x94d448],0x2",
     "G4a", "the status dam tests bit 0x1 of the plain relations dword"),
    ("MU16", 0x4120D4, "mov eax,DWORD PTR [edx+0xa14]", "mov eax,DWORD PTR [edx+0xa0c]", "G4b",
     "set -> element 0xa14 ('Pact'), clear -> 0xa10 ('Treaty')"),
    ("MU18", 0x4DB1D9, "mov eax,DWORD PTR [edx*4+0x94d448]", "mov eax,DWORD PTR [edx*4+0x94d468]",
     "G5a", "11 of the 13 ids anchor the plain dword, 2 the high one"),
    ("MU20", 0x4DB8AA, "mov ecx,DWORD PTR ds:0x997b20", "mov ecx,DWORD PTR ds:0x997b3c", "R1",
     "every row text is a load THROUGH 0x997b20 (another base is not the label array)"),
    ("MU25", 0x6146C7, "mov ds:0x997b20,eax", "mov ds:0x997b20,ecx", "G0d",
     "the alloc RESULT is what lands in 0x997b20 (the data flow, not just a store)"),
    ("MU26", 0x6146B1, "mov ds:0x997b24,eax", "mov ds:0x997b24,ecx", "G0e",
     "0x997b24 takes the 0x5ea484 return (the parsed count line)"),
    ("MU22", 0x4DB988, "push 0x2000000", "push 0x9", "R3",
     "the ids are bit masks, not row ordinals (only ~9 exceed 13)"),
]

# (name, 0-based line of labels.txt, replacement bytes, gate, claim)
LAB_MUT = [
    ("MU4", 8, b"#LABELZ", "G1a", "the section header line 8 is '#LABELS'"),
    ("MU5", 9, b"1090", "G1b", "the declared count equals the number of label lines that follow"),
    ("MU6", 10, b"Mission YearX", "G1c", "element 0 is the first line after the count line"),
    ("MU11", 876, b"Diplomacy 4", "G2e", "the title element reads 'Diplomacy for'"),
    ("MU17", 655, b"PactX", "G4c", "element 0xa14 reads 'Pact' (the set bit's own name)"),
    ("MU23", 885, b"Fight to the death", "R4",
     "the high ids do not reuse the low bit's text"),
    ("MU27", 880, b"I want revengeX", "G5c", "element 870 reads 'I want revenge'"),
    ("MU28", 884, b"Fight to the deathX", "G5c", "element 874 reads 'Fight to the death'"),
    ("MU29", 904, b"Fix current status as permanentX", "G5c",
     "element 894 reads 'Fix current status as permanent'"),
    ("MU21", 8, b"1089  #LABELS", "R2",
     "without the +10 shift the count would parse from the header line -> 0"),
]

# (name, old, new, gate, claim)  -- the tool's own algorithm
SRC_MUT = [
    ("MU19", "pid, lab, sreg = int(m.group(3), 16), ta, m.group(2)",
     "pid, lab, sreg = int(m.group(3), 16) + 4, ta, m.group(2)", "G5b",
     "the element is off/4 exactly - a +4 slip lands every row one text off"),
    ("MU24", "if e == runs[-1][-1] + 1:", "if True:", "R5",
     "the run splitter reports 3 runs, not one (adjacency is measured)"),
    ("MUA", 'rows = [r for r in allslots if r["dst"] == "call 0x604fd2" and r["src"] == "obj"]',
     'rows = [r for r in allslots if r["dst"] == "call 0x604fd2" and r["src"] == "other"]',
     "G2a", "the row classifier keys on the 0x997b20 base, not on the call target alone"),
]


def run(text, labels, tool):
    env = dict(os.environ, M367_TEXT=text, M367_LABELS=labels)
    p = subprocess.run([sys.executable, "-u", tool], capture_output=True, text=True, env=env)
    return p.returncode, p.stdout + p.stderr


def gates(txt):
    return {m.group(1): m.group(2) for m in
            re.finditer(r"^\s{2}([A-Z][0-9a-z]+)\s+(PASS|FAIL)", txt, re.M)}


def main():
    base = open(TEXT, "r", errors="replace").read().splitlines(True)
    labraw = open(LABELS, "rb").read()
    lablines = labraw.split(b"\r\n")
    out, killed, noop = [], [], []
    cache = {}
    gates_seen = set()

    def text_with(addr, old, new):
        key = (addr, old, new)
        if key in cache:
            return cache[key]
        d = os.path.join(ROOT, "scratch", "m367mut")
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "text_%x.txt" % addr)
        hit = False
        with open(p, "w") as f:
            for ln in base:
                m = ADDR.match(ln)
                if m and int(m.group(1), 16) == addr and not hit:
                    pat = re.compile(r"\s+".join(re.escape(w) for w in old.split()))
                    if pat.search(ln):
                        ln = pat.sub(new, ln, count=1)
                        hit = True
                f.write(ln)
        cache[key] = (p, hit)
        return p, hit

    def labels_with(idx, newbytes):
        d = os.path.join(ROOT, "scratch", "m367mut")
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "labels_%d.txt" % idx)
        L = list(lablines)
        hit = idx < len(L) and L[idx].strip() != newbytes
        if idx < len(L):
            L[idx] = newbytes
        open(p, "wb").write(b"\r\n".join(L))
        return p, hit

    out.append("M367 mutation harness - one mutant per VERIFIED gate")
    out.append("")
    for name, addr, old, new, gate, claim in TEXT_MUT:
        tp, hit = text_with(addr, old, new)
        rc, txt = run(tp, LABELS, TOOL)
        g = gates(txt)
        gates_seen |= set(g)
        ok = g.get(gate) == "FAIL"
        (killed if ok else noop).append((name, gate, ok, claim,
                                         "TEXT" if hit else "TEXT-noop-target"))
        out.append("  %-5s TEXT %-4s red=%-5s %s" % (name, gate, ok, " ".join(claim.split())[:88]))
    for name, idx, nb, gate, claim in LAB_MUT:
        lp, hit = labels_with(idx, nb)
        rc, txt = run(TEXT, lp, TOOL)
        g = gates(txt)
        gates_seen |= set(g)
        ok = g.get(gate) == "FAIL"
        (killed if ok else noop).append((name, gate, ok, claim,
                                         "LAB" if hit else "LAB-noop-target"))
        out.append("  %-5s LAB  %-4s red=%-5s %s" % (name, gate, ok, " ".join(claim.split())[:88]))
    src = open(TOOL).read()
    for name, old, new, gate, claim in SRC_MUT:
        if old not in src:
            noop.append((name, gate, False, "target absent", "SRC"))
            out.append("  %-5s SRC  %-4s NOOP      %s" % (name, gate, claim))
            continue
        tp = os.path.join(os.path.dirname(TOOL), ".m367_src_%s.py" % name)
        open(tp, "w").write(src.replace(old, new, 1))
        rc, txt = run(TEXT, LABELS, tp)
        os.unlink(tp)
        g = gates(txt)
        gates_seen |= set(g)
        ok = g.get(gate) == "FAIL"
        (killed if ok else noop).append((name, gate, ok, claim,
                                         "SRC" if ok else
                                         ("SRC-CRASH" if "Traceback" in txt else "SRC-green")))
        out.append("  %-5s SRC  %-4s red=%-5s %s" % (name, gate, ok, " ".join(claim.split())[:88]))

    allg = set(gates(run(TEXT, LABELS, TOOL)[1]))
    out.append("")
    nk = sum(1 for _, _, ok, _, _ in killed if ok)
    out.append("KILLED %d/%d   NO-OP %d" % (nk, len(killed), len(noop)))
    for n, g, _, claim, kind in noop:
        out.append("  noop %s (%s) gate %s: %s" % (n, kind, g, " ".join(claim.split())[:70]))
    missing = sorted(g for g in allg if g not in gates_seen)
    out.append("gate coverage: %d/%d gates have a mutant whose run reached it; unnamed: %s"
               % (len(allg) - len(missing), len(allg), " ".join(missing) or "-"))
    ok = nk == len(killed) and not noop and not missing
    out.append("%s M367-MUT: %d/%d killed, NO-OP %d, coverage %d/%d"
               % (("PASS" if ok else "FAIL"), nk, len(killed), len(noop),
                  len(allg) - len(missing), len(allg)))
    print("\n".join(out))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
