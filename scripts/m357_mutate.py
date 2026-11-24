#!/usr/bin/env python3
"""M357 mutation harness — every VERIFIED row of scripts/m357_pref_bits.py names a
mutant here; a mutant KILLS a gate when the run drops below 23/23.

Each mutant rewrites ONE instruction line of the .text cache (or one line of
Script.txt) and must turn PASS into FAIL.  NO-OP mutants (target text already
equal) are reported, never counted as killed.
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
TOOL = os.path.join(ROOT, "scripts/m357_pref_bits.py")
TMP = os.path.join(ROOT, "scratch")

# (name, addr, old text, new text, gate that must go red, claim)
MUT = [
    ("MU1", 0x4904F3, "call   0x604fd2", "call   0x604c8f", "G2a",
     "the row boundary is the add_item call"),
    ("MU2", 0x4904EC, "push   0x5", "push   0x6", "G1b", "BASIC row0 id == 5"),
    ("MU3", 0x4904C6, "push   0x68b678", "push   0x68b67c", "G2a",
     "BASIC row0 slot == 0x68b678"),
    ("MU4", 0x49043B, "push   0x68b66c", "push   0x68b698", "G0a",
     "page BASIC reads section BASICPREFS"),
    ("MU5", 0x4929A1, "or     al,0x20", "or     al,0x21", "G7c",
     "Preferences bit 5 == the Tutorial row"),
    ("MU6", 0x4929A1, "or     al,0x20", "or     al,0x20", "NOOP", "duplicate guard"),
    ("MU7", 0x492A0B, "or     al,0x2", "or     al,0x4", "G6b",
     "Autosave row -> bit 1 (bit 2 is taken)"),
    ("MU8", 0x492AD7, "or     al,0x8", "or     al,0x9", "G6b",
     "id16 -> a38 bit 3 only"),
    ("MU9", 0x492A55, "mov    ebx,0x8000", "mov    ebx,0x9000", "G6b",
     "id11 -> a30 bit 15 (the ebx constant is measured)"),
    ("MU10", 0x492464, "mov    ds:0x92befc,eax", "mov    ds:0x92bf04,eax", "G5c",
     "APPLY stores the A union into 0x92befc"),
    ("MU11", 0x49246F, "mov    ds:0x92bf00,eax", "mov    ds:0x92befc,eax", "G5a",
     "APPLY stores the B union into 0x92bf00"),
    ("MU12", 0x49240E, "mov    edx,DWORD PTR [esi+0xa38]",
     "mov    edx,DWORD PTR [esi+0xa48]", "G5a",
     "0x92befc does NOT include a48"),
    ("MU13", 0x4929D2, "or     DWORD PTR [esi+0xa34],0x100000",
     "or     DWORD PTR [esi+0xa40],0x100000", "G6b",
     "Auto-prune id 64 -> a34 bit 20 (a40 bit 20 is taken)"),
    ("MU17", 0x4911CC, "push   0x68b764", "push   0x6926fc", "G1a",
     "BASEWARNINGS row0 copies into table slot 0x68b764"),
    ("MU18", 0x492A5C, "or     DWORD PTR [esi+0xa30],ebx",
     "or     DWORD PTR [esi+0xa30],ecx", "G4a",
     "every id decodes to a field AND a bit (id 11's ebx form)"),
    ("MU19", 0x492E3A, "push   0x26", "push   0x66", "G4b",
     "id 0x26 is the rebuild's WARN row 1"),
    ("MU20", 0x49247A, "ds:0x92bf04,ecx", "ds:0x92bf00,ecx", "G5d",
     "a28|a48 lands in 0x92bf04"),
    ("MU21", 0x492E4D, "or     al,0x1", "or     al,ch", "G6a",
     "WARN row 0's store form is parseable"),
    ("MU22", 0x492DA0, "or     al,0x80", "or     al,0x40", "G7a",
     "the Laptop delta's A bit 7 is the movies row (bit 6 is unwritten)"),
    ("MU23", 0x58EB38, "add    esi,0x3a7168", "add    esi,0x3b7168", "G7d",
     "the More Preferences default word is 0x3a7168"),
]

SCR_MUT = [
    ("MU14", "Tutorial messages.\r\n", "", "G3b",
     "BASICPREFS offers 8 lines (row count == text count)"),
    ("MU15", "Tutorial messages.", "Messages tutorial.", "G7c",
     "Preferences bit 5 names the Tutorial row"),
    ("MU18b", "#BASICPREFS\r\n", "#BASIC_PREFS\r\n", "G3a",
     "the BASIC page's section is named BASICPREFS"),
    ("MU16", "Stop for random events.\r\n", "Stop for random events.\r\nStop for extra.\r\n", "G3b",
     "BASEWARNINGS offers 17 labelled lines"),
]


def run(text=None, script=None):
    env = dict(os.environ)
    if text:
        env["M357_TEXT"] = text
    if script:
        env["M357_SCRIPT"] = script
    p = subprocess.run([sys.executable, "-u", TOOL], capture_output=True,
                       text=True, env=env, cwd=ROOT)
    red = re.findall(r"^\[FAIL\] (\w+)", p.stdout, re.M)
    tail = [l for l in p.stdout.splitlines() if l.startswith(("PASS M357", "FAIL M357"))]
    return p.returncode, red, (tail[-1] if tail else "?"), p.stdout


def patch_text(addr, old, new, dst):
    lines = open(TEXT, "r", errors="replace").read().split("\n")
    hit = 0
    for i, l in enumerate(lines):
        m = re.match(r"^\s*([0-9a-f]{6,8}):", l)
        if not m or int(m.group(1), 16) != addr:
            continue
        if old not in l:
            return None
        lines[i] = l.replace(old, new, 1)
        hit += 1
        break
    if not hit:
        return None
    open(dst, "w").write("\n".join(lines))
    return dst


def patch_script(old, new, dst):
    s = open(SCRIPT, "rb").read()
    o, n = old.encode("latin-1"), new.encode("latin-1")
    if o not in s:
        return None
    open(dst, "wb").write(s.replace(o, n, 1))
    return dst


def main():
    rc, red, tail, out = run()
    print("baseline: %s  red=%s" % (tail, red))
    if rc != 0:
        print("BASELINE NOT GREEN — abort")
        return 1
    killed = noop = missed = 0
    for name, addr, old, new, want, claim in MUT:
        dst = os.path.join(TMP, "m357_%s_text.txt" % name.lower())
        if old == new:
            print("%-5s NO-OP  (%s)" % (name, claim))
            noop += 1
            continue
        if patch_text(addr, old, new, dst) is None:
            print("%-5s MISSED (text not found at 0x%x) %s" % (name, addr, claim))
            missed += 1
            continue
        rc2, red2, tail2, out2 = run(text=dst)
        ok = rc2 != 0
        if not red2 and rc2 != 0:
            red2 = ["CRASH:" + (out2.strip().splitlines() or ["?"])[-1][:60]]
        hit = want in red2
        ok = ok and hit
        print("%-5s %-7s want=%s red=%s  %s" % (name, "KILLED" if ok else "SURVIVED",
                                                want, red2[:4], claim))
        killed += 1 if ok else 0
        if not ok:
            missed += 1
        os.unlink(dst)
    for name, old, new, want, claim in SCR_MUT:
        dst = os.path.join(TMP, "m357_%s_script.txt" % name.lower())
        if patch_script(old, new, dst) is None:
            print("%-5s MISSED (Script.txt text not found) %s" % (name, claim))
            missed += 1
            continue
        rc2, red2, tail2, out2 = run(script=dst)
        ok = rc2 != 0
        if not red2 and rc2 != 0:
            red2 = ["CRASH:" + (out2.strip().splitlines() or ["?"])[-1][:60]]
        hit = want in red2
        ok = ok and hit
        print("%-5s %-7s want=%s red=%s  %s" % (name, "KILLED" if ok else "SURVIVED",
                                                want, red2[:4], claim))
        killed += 1 if ok else 0
        if not ok:
            missed += 1
        os.unlink(dst)
    total = len(MUT) + len(SCR_MUT)
    print("\n%d/%d killed, %d NO-OP, %d survived/missed"
          % (killed, total - noop, noop, missed))
    print("%s M357-mutate" % ("PASS" if missed == 0 else "FAIL"))
    return 0 if missed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
