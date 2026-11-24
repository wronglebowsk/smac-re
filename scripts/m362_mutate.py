#!/usr/bin/env python3
"""M362 mutation harness — every VERIFIED row of scripts/m362_sibling.py names a mutant here;
a mutant is KILLED when its named gate turns red in a real run of the tool.

Each mutant rewrites ONE instruction line of the .text cache (the tool reads it through
M362_TEXT) or one gate constant of the tool.  A NO-OP mutant (target text absent) is
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
TOOL = os.path.join(ROOT, "scripts/m362_sibling.py")
TMP = os.environ.get("M362_TMP") or os.path.join(ROOT, "scratch")

# (name, [(addr, old, new)] edits, gate that must go red, claim)
MUT = [
    ("MU1", [(0x4DB1E4, "push   0x8", "push   0x9")], ("G1b", "R2"),
     "row 1's id is 0x8 (id==mask); a 0x9 id breaks id==mask and the single-bit count"),
    ("MU2", [(0x4DB1E0, "and    eax,0x8", "and    eax,0x9")], "G1b",
     "row 1's mask is 0x8, equal to its id"),
    ("MU3", [(0x4DB40D, "mov    eax,DWORD PTR [edx*4+0x94d468]",
              "mov    eax,DWORD PTR [edx*4+0x94d448]")], "G1c",
     "id 0x80000008 reads the SECOND dword 0x94d468, so the high-bit set is the B-row set"),
    ("MU4", [(0x4DB1C2, "shl    ecx,0x6", "shl    ecx,0x5")], "G2a",
     "the index idiom multiplies by 2^6 first (2095 = 2^11 - 1)"),
    ("MU5", [(0x4DB1C7, "lea    edx,[eax+ecx*2]", "lea    edx,[eax+ecx*4]")], "G2c",
     "all 13 blocks carry the same instruction sequence (one block differs here)"),
    ("MU6", [(0x4DB1D1, "mov    eax,DWORD PTR [esi+0xa20]",
              "mov    eax,DWORD PTR [esi+0xa24]")], "G3b",
     "the index addend is the dialog's +0xa20 (target faction) field"),
    ("MU7", [(0x4DB1BA, "lea    edi,[esi+0x15a0]", "lea    edi,[esi+0x5974]")], "G3a",
     "the checkbox group is the INLINE sub-object at +0x15a0, not the preferences widget"),
    ("MU8", [(0x4DB46B, "call   DWORD PTR [eax+0xf0]", "call   DWORD PTR [eax+0xf4]")], "G3c",
     "the sync ends with the +0xf0 vtable call through the +0x15a0 object"),
    ("MU9", [(0x4DB86C, "push   0x8", "push   0x10")], "G4a",
     "the builder's row order equals the sync order (row 1 = id 0x8)"),
    ("MU10", [(0x4DBA23, "mov    ecx,DWORD PTR [eax+0xdf8]",
               "mov    ecx,DWORD PTR [eax+0xdac]")], "G4b",
     "each of the 13 rows has its own label slot in the 0x997b20 text object"),
    ("MU11", [(0x4DAD58, "call   0x6051fa", "call   0x6050d4")], "G5a",
     "every toggle handler ASKS the widget (is_checked) before writing"),
    ("MU12", [(0x4DAD4C, "or     eax,0x80000000", "or     eax,0x40000000")], "G5b",
     "the high-array handler queries id|0x80000000, which is what selects 0x94d468"),
    ("MU13", [(0x551DBA, "add    ecx,edx", "add    ecx,eax")], "G6a",
     "0x551d70's one-way index adds param_2 after subtracting param_1"),
    ("MU14", [(0x551D52, "lea    eax,[edx*4+0x94d448]", "lea    eax,[edx*4+0x94d468]")], "G6b",
     "0x551cf0's last store targets 0x94d448 (its primary base)"),
    ("MU15", [(0x4DB20A, "mov    eax,DWORD PTR [edx*4+0x94d448]",
               "mov    eax,DWORD PTR [edx*4+0x92befc]")], "R1",
     "no sync row reads the preferences flag block 0x92befc.. (rival R1 fails)"),
    ("MU16", [(0x55194F, "add    esi,ecx", "add    esi,eax")], "R4",
     "0x5518f0 writes the pair in BOTH directions; the second arm adds param_1"),
    ("MU18", [(0x4DB1E6, "call   0x6050d4", "call   0x6050d8")], "G1a",
     "13 set-by-id calls (not 12) carry the 13 rows"),
    ("MU19", [(0x4DAD8C, "call   0x551d70", "call   0x551a20")], "G5c",
     "the 4th handler's one-way writer is 0x551d70, distinct from every other handler's"),
]

# tool-source mutants: (name, old, new, gate, claim) - a gate constant is flipped, never the
# measurement, so the gate itself is shown to be load-bearing.
SRC_MUT = [
    ("MU17", """        for k in range(n - 1, max(0, n - 14), -1):
            b = INS[k]
            if rid is None and b["op"] == "push" and imm(b["arg"]) is not None and imm(b["arg"]):""",
     """        for k in range(max(0, n - 14), n):
            b = INS[k]
            if rid is None and b["op"] == "push" and imm(b["arg"]) is not None:""", "G4a",
     "the row parser scans BACKWARD from the call, so the id push outranks the item flag push"),
]

GATE = re.compile(r"^\s+(G\d[a-z]?|R\d)\s+(PASS|FAIL)\s")


def run(text_path, tool_path):
    env = dict(os.environ, M362_TEXT=text_path)
    p = subprocess.run([sys.executable, "-u", tool_path], capture_output=True,
                       text=True, env=env)
    ok, red = [], []
    for line in p.stdout.splitlines():
        m = GATE.match(line)
        if not m:
            continue
        (ok if m.group(2) == "PASS" else red).append(m.group(1))
    return p.returncode, ok, red, p.stdout


def main():
    work = tempfile.mkdtemp(prefix="m362mut_", dir=TMP)
    base = os.path.join(work, "text.txt")
    shutil.copyfile(TEXT, base)
    rc0, gates, red0, out0 = run(base, TOOL)
    if rc0 != 0 or red0:
        print("BASELINE NOT GREEN: rc=%d red=%s" % (rc0, red0))
        return 1
    print("baseline: %d gates PASS, %d FAIL" % (len(gates), len(red0)))
    killed, noop, missed = [], [], []
    for name, edits, gate, claim in MUT:
        p = os.path.join(work, "t_%s.txt" % name)
        shutil.copyfile(TEXT, p)
        src = open(p, encoding="latin-1").read()
        hit = True
        for addr, old, new in edits:
            pat = "  %x:\t" % addr
            i = src.find(pat)
            if i < 0:
                hit = False
                break
            j = src.find("\n", i)
            line = src[i:j]
            if old not in line:
                hit = False
                break
            src = src[:i] + line.replace(old, new, 1) + src[j:]
        if not hit:
            noop.append((name, gate))
            print("%-5s NO-OP  (target instruction text not found)" % name)
            continue
        open(p, "w", encoding="latin-1").write(src)
        rc, ok, red, out = run(p, TOOL)
        gl = (gate,) if isinstance(gate, str) else gate
        if any(g in red for g in gl):
            killed.append(name)
            print("%-5s KILLED %-4s %s" % (name, "/".join(gl), claim))
        else:
            missed.append((name, gl))
            print("%-5s MISS   %-4s rc=%d red=%s" % (name, "/".join(gl), rc, red))
    for name, old, new, gate, claim in SRC_MUT:
        p = os.path.join(work, "t_%s.py" % name)
        src = open(TOOL, encoding="utf-8").read()
        if old not in src:
            noop.append((name, gate))
            print("%-5s NO-OP  (target source line not found)" % name)
            continue
        open(p, "w", encoding="utf-8").write(src.replace(old, new, 1))
        rc, ok, red, out = run(base, p)
        gl = (gate,) if isinstance(gate, str) else gate
        if any(g in red for g in gl):
            killed.append(name)
            print("%-5s KILLED %-4s %s" % (name, "/".join(gl), claim))
        else:
            missed.append((name, gl))
            print("%-5s MISS   %-4s rc=%d red=%s" % (name, "/".join(gl), rc, red))
    named = set()
    for m in MUT:
        named |= set((m[2],) if isinstance(m[2], str) else m[2])
    named |= set(m[3] for m in SRC_MUT)
    named = sorted(named)
    print("")
    print("scored: %d/%d killed, NO-OP %s, MISSED %s"
          % (len(killed), len(MUT) + len(SRC_MUT), [n for n, _ in noop] or "none",
             [n for n, _ in missed] or "none"))
    print("coverage: gates %d, named by a mutant %d -> %s" % (len(gates), len(named), named))
    print("unnamed gates: %s" % sorted(set(gates) - set(named)))
    shutil.rmtree(work, ignore_errors=True)
    return 0 if not missed else 1


if __name__ == "__main__":
    sys.exit(main())
