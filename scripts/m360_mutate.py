#!/usr/bin/env python3
"""M360 mutation harness — every VERIFIED row of scripts/m360_orphans.py names a mutant
here; a mutant is KILLED when its named gate turns red in a real run of the tool.

Each mutant rewrites ONE instruction line of the .text cache (or one line of Script.txt,
or four lines for the page-inventory mutant).  A NO-OP mutant (target text absent) is
reported, never counted as killed.  Coverage is MEASURED: the gate ids are read from the
tool's own PASS lines, not authored here.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
SCRIPT = os.path.join(ROOT, "programs/Script.txt")
TOOL = os.path.join(ROOT, "scripts/m360_orphans.py")
TMP = os.environ.get("M360_TMP") or os.path.join(ROOT, "scratch")

# (name, [(addr, old, new)] edits, gate that must go red, claim)
MUT = [
    ("MU1", [(0x49047A, "lea    edi,[esi+0x5974]", "lea    edi,[esi+0x5978]")], "G1a",
     "the builder's first widget is +0x5974"),
    ("MU2", [(0x49047A, "lea    edi,[esi+0x5974]", "mov    edi,DWORD PTR ds:0x5974")], "G1b",
     "widgets are addressed as object members, never absolutely"),
    ("MU3", [(0x491677, "call   0x604fd2", "call   0x604c8f")], "G2a",
     "66 add_item calls fill 66 rows"),
    ("MU4", [(0x492992, "call   0x6051fa", "call   0x6052bd")], "G2b",
     "REBUILD issues 70 is_checked queries"),
    ("MU5", [(0x492CEA, "push   0x37", "push   0x36")], "G2c",
     "the A/V block queries 0x37 (not a real row id)"),
    ("MU6", [(0x493002, "push   0x50", "push   0x30")], "G2d",
     "the seventh widget queries 0x50, not the built 0x30"),
    ("MU7", [(0x49294C, "push   0x5", "push   0x1a")], "G2f",
     "the BASIC widget's query set equals its rows"),
    ("MU8", [(0x605239, "mov    DWORD PTR [ebp-0x4],0x0",
              "mov    DWORD PTR [ebp-0x4],0x1")], "G3a",
     "the row scan starts at index 0 (algorithm mutant)"),
    ("MU9", [(0x605251, "cmp    eax,DWORD PTR [edx+0x10]",
              "cmp    eax,DWORD PTR [edx+0x14]")], "G3a",
     "the scan exits at the row count [node+0x10] (algorithm mutant)"),
    ("MU10", [(0x605100, "mov    DWORD PTR [eax+0x14],0x0",
               "mov    DWORD PTR [eax+0x14],0x1")], "G3b",
     "set-by-id also starts its scan at 0 -> a miss lands on count"),
    ("MU11", [(0x49355B, "push   0x4e", "push   0x4d")], "G4a",
     "id 0x37's radio relabels control 0x4e"),
    ("MU12", [(0x493457, "mov    edi,0x800", "mov    edi,0x400")], "G4b",
     "id 0x37's mask is a4c bit 11 (0x800)"),
    ("MU13", [(0x493529, "and    ecx,edi", "call   0x6050d4")], "G4c",
     "radio handlers never call set-by-id"),
    ("MU14", [(0x493685, "mov    edi,0x1000", "mov    edi,0x2000")], "G4d",
     "the A/V-tail block's last mask is 0x1000 (the stale operand's value)"),
    ("MU15", [(0x4936C9, "mov    edi,0x8000", "mov    edi,0x1000")], "G4e",
     "no mask in the seventh block overlaps the stale 0x1000"),
    ("MU16", [(0x605008, "call   0x6052bd", "call   0x6052be")], "G5a",
     "add_item's bit write is set_bit 0x6052bd"),
    ("MU17", [(0x493709, "call   0x6050d4", "call   0x493ec0")], "G5b",
     "id 0x50 is written by set-by-id (an absent-id write)"),
    ("MU18", [(0x491670, "push   0x30", "push   0x50")], "G6a",
     "the seventh widget's 4th built row is id 0x30"),
    ("MU21", [(0x605254, "jge    0x605286", "jg     0x605286")], "G3c",
     "the scan exits on `jge` (index >= count) so a miss lands exactly on count"),
    ("MU19", [(0x4915A7, "lea    ecx,[esi+0x913c]", "lea    ecx,[esi+0x8614]"),
              (0x4915E8, "lea    ecx,[esi+0x913c]", "lea    ecx,[esi+0x8614]"),
              (0x491629, "lea    ecx,[esi+0x913c]", "lea    ecx,[esi+0x8614]"),
              (0x491669, "lea    ecx,[esi+0x913c]", "lea    ecx,[esi+0x8614]")], "G7a",
     "the seventh widget IS built (rival R1 fails)"),
]
SCR_MUT = [
    ("MU20", "Whole unit blinks.", "G7b",
     "the A/V section offers exactly 3 more lines than the exe builds"),
]

PASS = re.compile(r"^\[PASS\] (\S+) ")
FAIL = re.compile(r"^\[FAIL\] (\S+) ")


def run(text_path, script_path):
    env = dict(os.environ, M360_TEXT=text_path, M360_SCRIPT=script_path)
    p = subprocess.run([sys.executable, "-u", TOOL], capture_output=True, text=True, env=env)
    gates, red = [], []
    for line in p.stdout.splitlines():
        m = PASS.match(line)
        if m and not m.group(1).endswith(":"):
            gates.append(m.group(1))
        m = FAIL.match(line)
        if m and not m.group(1).endswith(":"):
            red.append(m.group(1))
    return p.returncode, gates, red, p.stdout


def main():
    work = tempfile.mkdtemp(prefix="m360mut_", dir=TMP)
    base = os.path.join(work, "text.txt")
    shutil.copyfile(TEXT, base)
    rc0, gates, red0, out0 = run(base, SCRIPT)
    if rc0 != 0 or red0:
        print("BASELINE NOT GREEN: rc=%d red=%s" % (rc0, red0))
        return 1
    print("baseline: %d gates PASS, %d FAIL" % (len(gates), len(red0)))
    all_gates = [g for g in gates]
    killed, noop, missed = [], [], []
    for name, edits, gate, claim in MUT:
        p = os.path.join(work, "t_%s.txt" % name)
        shutil.copyfile(TEXT, p)
        src = open(p, encoding="latin-1").read()
        ok = True
        for addr, old, new in edits:
            pat = "  %x:\t" % addr
            i = src.find(pat)
            if i < 0:
                ok = False
                break
            j = src.find("\n", i)
            line = src[i:j]
            if old not in line:
                ok = False
                break
            src = src[:i] + line.replace(old, new, 1) + src[j:]
        if not ok:
            noop.append((name, gate))
            print("%-5s NO-OP  (target instruction text not found)" % name)
            continue
        open(p, "w", encoding="latin-1").write(src)
        rc, g, red, out = run(p, SCRIPT)
        if gate in red:
            killed.append((name, gate, red))
            print("%-5s KILL   %-4s  red=%s" % (name, gate, ",".join(red)))
        else:
            missed.append((name, gate))
            print("%-5s MISS   %-4s  red=%s" % (name, gate, ",".join(red) or "-"))
    for name, needle, gate, claim in SCR_MUT:
        p = os.path.join(work, "s_%s.txt" % name)
        src = open(SCRIPT, encoding="latin-1").read()
        if needle not in src:
            noop.append((name, gate))
            print("%-5s NO-OP  (Script.txt line absent)" % name)
            continue
        open(p, "w", encoding="latin-1").write(src.replace(needle, "", 1))
        rc, g, red, out = run(base, p)
        if gate in red:
            killed.append((name, gate, red))
            print("%-5s KILL   %-4s  red=%s" % (name, gate, ",".join(red)))
        else:
            missed.append((name, gate))
            print("%-5s MISS   %-4s  red=%s" % (name, gate, ",".join(red) or "-"))
    covered = {g for _, _, red in killed for g in red}            # MEASURED, not authored
    uncovered = [x for x in all_gates if x not in covered]
    print("\n%d/%d mutants killed, %d NO-OP, %d missed" % (len(killed), len(MUT) + len(SCR_MUT), len(noop), len(missed)))
    print("gate coverage: %d/%d asserted gates have a named mutant" % (len(all_gates) - len(uncovered), len(all_gates)))
    if uncovered:
        print("uncovered gates:", ",".join(uncovered))
    ok = not missed and not noop and not uncovered and len(killed) == len(MUT) + len(SCR_MUT)
    print("VERDICT: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
