#!/usr/bin/env python3
"""M356 mutation harness - every VERIFIED row of `## M356` names a mutant that
REDDENS its gate.  A mutant edits ONE instruction of the parsed listing through
SMAC_M356_MUTANT (`0xADDR|old|new`); the acceptance script is not modified.
PATCH REJECTED (exit) counts as a harness failure, never a pass.

    python3 -u scripts/m356_mutate.py        # writes evidence/m356_mutate.txt

Scoring: SCORED = acceptance exits non-zero AND the declared gate is in the
FAIL set.  NO-OP mutants must stay green.  Coverage = the gates actually
reddened, measured (never authored).
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "m356_prototype_stamp.py")
OUT = os.path.join(ROOT, "evidence", "m356_mutate.txt")
BASELINE = "MU0"

# (id, addr, old, new, gate, why)
MUTANTS = [
    ("MU1", 0x4EED18, "],0x4", "],0x8", "G1", "owner-band setter loses bit 2"),
    ("MU2", 0x4EFE60, "[esi+0x98adb8],ax", "[esi+0x98adb9],ax", "G1", "decoder store moves to +0x31"),
    ("MU3", 0x4EFE41, "cmp ebx,0x40", "cmp ebx,0x41", "G4", "owner-band guard 0x40 -> 0x41"),
    ("MU4", 0x4D2FF3, "test al,0x4", "test al,0x8", "G15", "second latch tests the wrong bit"),
    ("MU5", 0x4D2FF7, "or al,0x4", "or al,0x8", "G15", "second latch ORs the wrong bit"),
    ("MU6", 0x574107, "],0x4", "],0x40", "G1", "a 0x573a90 setter loses bit 2"),
    ("MU7", 0x595F91, "],0x105", "],0x101", "G3", "init constant 0x105 loses bit 2"),
    ("MU8", 0x595F9C, "],0x115", "],0x111", "G3", "init constant 0x115 loses bit 2"),
    ("MU9", 0x5745CC, "cmp eax,0x92baa0", "cmp eax,0x92bab0", "G9", "offense scan bound +1 record"),
    ("MU10", 0x5746B3, "cmp eax,0x92fdb8", "cmp eax,0x92fdc8", "G10", "armor scan bound +1 record"),
    ("MU11", 0x595EF0, "shl eax,0x4", "shl eax,0x3", "G11", "chassis stride 9*16 -> 9*8"),
    ("MU12", 0x595E9E, "[edx+0x92b950]", "[edx+0x92fd18]", "G12", "finalizer reads the armor table as offense"),
    ("MU13", 0x595D1C, "[esi+0x98adb0],al", "[esi+0x98adb1],al", "G14", "+0x28 writer becomes a +0x29 writer"),
    ("MU14", 0x5741F0, "],0xfd", "],0xfb", "G2", "an AND now CLEARS bit 2"),
    ("MU15", 0x5729D5, "],0x104", "],0x100", "G1", "word setter loses bit 2"),
    ("MU16", 0x59D432, "],0x4", "],0x8", "G1", "production-loop setter loses bit 2"),
    ("MU17", 0x4EFE59, "or al,0x4", "add al,0x4", "G1", "ALGORITHM: RMW setter no longer an `or`"),
    ("MU18", 0x595EAA, "cmp al,bl", "cmp al,bh", "G12", "finalizer comparison register swapped"),
    ("MU19", 0x595EA4, "[eax+0x92fd18]", "[eax+0x92b950]", "G12", "finalizer armor load repointed"),
    ("MU20", 0x595F82, "],0x1", "],0x5", "G3", "init constant 0x1 gains bit 2"),
    ("MU21", 0x4EFE7E, "call 0x572800", "call 0x572810", "G5", "decoder's 0->1 follow-up call retargeted"),
    ("MU22", 0x595EF3, "[eax+0x92ae80]", "[eax+0x92ae00]", "G8", "one chassis-table read leaves the table"),
    ("MU23", 0x595E8C, "[esi+0x98adad]", "[esi+0x98adaf]", "G13", "+0x25 read becomes a +0x27 read"),
    ("MU25", 0x4396E6, "xor dx,0x4", "xor dx,0x8", "G2", "the one bit-2 toggler moves to bit 3"),
    ("MU26", 0x4393BB, "and cl,0xfd", "and cl,ch", "G2", "an immediate AND becomes a REGISTER mask"),
    ("MU27", 0x4EFE50, "[edx+0x98adb8]", "[edx+0x98adb4]", "G1b", "setter loses its flags-word load provenance"),
    ("MU28", 0x5732CA, "cmp dl,BYTE PTR [eax+0x98adb0]", "mov dl,BYTE PTR [eax+0x98adb0]", "G16", "+0x28 cmp becomes a load (reference census shifts)"),
]
NOOP = ("MU29", 0x4F05BD, "or BYTE PTR [eax+0x98adb9],0x1", "or BYTE PTR [eax+0x98adb9],0x2", "NOOP",
        "a +0x31 write no gate pins")


def run(env_extra):
    env = dict(os.environ)
    env.update(env_extra)
    p = subprocess.run([sys.executable, "-u", SCRIPT], capture_output=True,
                       text=True, env=env)
    red = sorted(set(re.findall(r"^FAIL (G\d+[a-z]?)\b", p.stdout, re.M)))
    return p.returncode, red, p.stdout + p.stderr


def main():
    lines = []
    rc0, red0, out0 = run({})
    ok0 = rc0 == 0 and not red0
    lines.append("%s baseline %s: rc=%d red=%s" % ("PASS" if ok0 else "FAIL", BASELINE, rc0, red0))
    scored, missed, noop_bad, cov = 0, [], [], set()
    for mid, addr, old, new, gate, why in MUTANTS:
        spec = "0x%x|%s|%s" % (addr, old, new)
        rc, red, out = run({"SMAC_M356_MUTANT": spec})
        if "PATCH REJECTED" in out:
            missed.append((mid, gate, "PATCH REJECTED", why))
            lines.append("FAIL %s %s -> PATCH REJECTED (%s)" % (mid, gate, why))
            continue
        hit = rc != 0 and gate in red
        cov.update(red)
        if hit:
            scored += 1
            lines.append("PASS %s -> %s %s" % (mid, gate, why))
        else:
            missed.append((mid, gate, "rc=%d red=%s" % (rc, red), why))
            lines.append("FAIL %s -> %s not reddened (rc=%d red=%s) %s" % (mid, gate, rc, red, why))
    mid, addr, old, new, _, why = NOOP
    rc, red, out = run({"SMAC_M356_MUTANT": "0x%x|%s|%s" % (addr, old, new)})
    if rc == 0 and not red:
        lines.append("PASS %s -> NO-OP stayed green (%s)" % (mid, why))
    else:
        noop_bad.append(mid)
        lines.append("FAIL %s -> NO-OP reddened %s" % (mid, red))
    lines.append("")
    lines.append("scored %d/%d, missed %s, noop_bad %s"
                 % (scored, len(MUTANTS), [m[0] for m in missed] or "none", noop_bad or "none"))
    lines.append("MEASURED gate coverage: %s (%d gates)"
                 % (sorted(cov, key=lambda s: (int(re.sub(r"[a-z]","",s[1:])), s)), len(cov)))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if (ok0 and not missed and not noop_bad) else 1


if __name__ == "__main__":
    sys.exit(main())
