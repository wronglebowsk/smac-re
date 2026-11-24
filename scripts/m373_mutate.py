#!/usr/bin/env python3
"""M373 mutation harness - every V row of NAMED ## M373 names a mutant killed here.

A mutant is KILLED when its named gate turns RED in a REAL run of scripts/m373_pending_vendetta.py.
A NO-OP mutant (its target line is absent) is reported and never counted.

  TEXT  rewrites ONE instruction of the objdump cache (M373_TEXT) - the DISASSEMBLY is the input.
  ALG   rewrites ONE line of the tool (a temp copy) - the instrument itself.

    python3 scripts/m373_mutate.py
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
TOOL = os.path.join(ROOT, "scripts/m373_pending_vendetta.py")

# (name, addr, old, new, gate, claim)
TEXT_MUT = [
    ("MU1", 0x55573C, "test eax,0x80000000", "test eax,0x40000000", "G1a",
     "the pass READS bit 31 (pending) as 0x80000000, not a neighbouring bit"),
    ("MU2", 0x555809, "and ah,0xdf", "and ah,0xff", "G2a",
     "the skip path scrubs bit 13 (`and ah,0xdf` = 0xffffdfff) - not a no-op"),
    ("MU3", 0x555741, "je 0x555809", "je 0x55580f", "G2a",
     "both escapes of the pending test land on the SAME scrub block at 0x555809"),
    ("MU4", 0x555747, "test ah,0x20", "test al,0x20", "R3",
     "the pending protector is bit 13 (ah), not bit 5 (al)"),
    ("MU5", 0x5558DA, "push 0x80000000", "push 0x80000004", "G1a",
     "the ARM push carries bit 31 (the pending mask) through FUN_00551a20"),
    ("MU6", 0x555758, "mov DWORD PTR [edi+0x94d448],eax", "mov DWORD PTR [edi+0x94d44c],eax",
     "G5a", "0x555758 stores the CLEARED word back into the relations dword (own direction)"),
    ("MU7", 0x551988, "and edi,edx", "and edi,0x7fffffff", "G5b",
     "FUN_005518f0's AND takes the CALLER's mask, not a literal"),
    ("MU8", 0x5230F0, "test DWORD PTR [ecx*4+0x94d448],0x8000000",
     "test DWORD PTR [ecx*4+0x94d448],0x800000", "G3b",
     "bit 27 is read off the relations word at 0x5230f0 as 0x08000000"),
    ("MU9", 0x59F176, "push 0x9000ff48", "push 0x9000ff49", "G5c",
     "the elimination sweep's mask carries bit 31 (0x9000ff48)"),
    ("MU10", 0x4DA404, "push 0xdd9bc3c0", "push 0x5d9bc3c0", "G5c",
     "the flag-dependent call's mask (0xdd9bc3c0) carries bit 31"),
    ("MU11", 0x551B17, "and edx,0xfaeef378", "and edx,0x0aeef378", "G4a",
     "the war clear mask KEEPS bit 31 (0xfaeef378) - pending survives a war write"),
    ("MU12", 0x551A88, "and edx,0xffee7faf", "and edx,0x7fee7faf", "G4a",
     "the peace clear mask KEEPS bit 31 (0xffee7faf)"),
    ("MU13", 0x55578A, "and ecx,0x7fffffff", "and ecx,0xfffffffe", "G1b",
     "the mirror clear uses the same 0x7fffffff mask"),
    ("MU14", 0x551C0D, "mov DWORD PTR [eax],edx", "mov DWORD PTR [eax+0x4],edx", "G5a",
     "the setter's store really writes the relations dword (store census sensitivity)"),
]

# (name, old, new, gate, claim)
ALG_MUT = [
    ("MU15", "BIT31, BIT27, BIT13 = 0x80000000, 0x08000000, 0x2000",
     "BIT31, BIT27, BIT13 = 0x80000000, 0x08000000, 0x20", "G2b",
     "the protector bit is 0x2000 (bit 13), not 0x20 (bit 5)"),
    ("MU16", "if word & BIT31:", "if word & BIT27:", "G2b",
     "the guard tests the pending bit 31, not bit 27"),
]


def run(tool, text, evid):
    env = dict(os.environ, M373_TEXT=text, M373_EVID=evid)
    p = subprocess.run([sys.executable, "-u", tool], env=env, capture_output=True, text=True)
    return p.stdout + p.stderr


def gate_state(out, gid):
    m = re.search(r"^\s+%s\s+(PASS|FAIL)" % gid, out, re.M)
    return m.group(1) if m else "ABSENT"


def main():
    tmpd = tempfile.mkdtemp(prefix="m373mut_")
    lines = open(TEXT, "r", errors="replace").read().split("\n")
    rows, nop = [], []
    for name, addr, old, new, gid, claim in TEXT_MUT:
        pat = re.compile(r"^\s*%06x:" % addr)
        # the dump pads mnemonics with runs of spaces: match the operand text whitespace-flexibly
        flex = re.compile(r"\s+".join(re.escape(p) for p in old.split()))
        hit = None
        for i, ln in enumerate(lines):
            if pat.match(ln) and flex.search(ln):
                hit = i
                break
        if hit is None:
            nop.append(name)
            continue
        mut = list(lines)
        mut[hit] = flex.sub(new, lines[hit], count=1)
        path = os.path.join(tmpd, "%s.txt" % name)
        open(path, "w").write("\n".join(mut))
        out = run(TOOL, path, os.path.join(tmpd, "ev_%s.txt" % name))
        st = gate_state(out, gid)
        rows.append((name, gid, st, claim))
    for name, old, new, gid, claim in ALG_MUT:
        src = open(TOOL).read()
        if old not in src:
            nop.append(name)
            continue
        # keep the altered copy INSIDE scripts/ so ROOT (and the ghidra shard paths) resolve
        path = os.path.join(ROOT, "scripts", "_m373_alg_%s.py" % name)
        open(path, "w").write(src.replace(old, new, 1))
        try:
            out = run(path, TEXT, os.path.join(tmpd, "ev_%s.txt" % name))
        finally:
            os.unlink(path)
        rows.append((name, gid, gate_state(out, gid), claim))
    print("M373 mutation harness - %d mutants, %d no-op %s"
          % (len(rows) + len(nop), len(nop), nop))
    killed = 0
    for name, gid, st, claim in rows:
        ok = st == "FAIL"
        killed += ok
        print("  %-5s %-5s %-6s %s" % (name, gid, st, claim))
    bad = [r[0] for r in rows if r[2] != "FAIL"]
    print("")
    if rows and not bad and not nop:
        print("RUN PASS %d mutants, NO-OP %s" % (killed, nop))
        return 0
    print("RUN FAIL survivors %s no-op %s" % (bad, nop))
    return 1


if __name__ == "__main__":
    sys.exit(main())
