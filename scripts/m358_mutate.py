#!/usr/bin/env python3
"""M358 mutation harness - every VERIFIED row of `## M358` names a mutant that
REDDENS its gate.  A mutant edits ONE instruction of the parsed listing through
SMAC_M358_PATCH (`0xADDR|old|new`); the acceptance script is not modified.
PATCH REJECTED (exit) counts as a harness failure, never a pass.

    python3 -u scripts/m358_mutate.py        # writes evidence/m358_mutate.txt

Scoring: SCORED = acceptance exits non-zero AND the declared gate is in the
FAIL set.  NO-OP mutants must stay green.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "m358_row_layout.py")
OUT = os.path.join(ROOT, "evidence", "m358_mutate.txt")

# (id, addr, old, new, gate, why, claim row)
MUTANTS = [
    ("MU1", 0x49571B, "imul edx,edx,0x34", "imul edx,edx,0x30", "G1", "one 0x34 imul -> 0x30", "stride 0x34 / 756 sites"),
    ("MU2", 0x595CE7, "[esi+0x98adb1]", "[esi+0x98ada1]", "G2", "the +0x29 writer lands at +0x19", "field set == 17 offsets"),
    ("MU3", 0x40CFCD, "mov al,BYTE PTR [edx*4+0x98adac]", "mov eax,DWORD PTR [edx*4+0x98adac]", "G3", "+0x24 read widened to dword", "+0x24..2e are byte-only"),
    ("MU4", 0x5741E9, "mov BYTE PTR [ebx+0x98ada7],0x0", "mov BYTE PTR [ebx+0x98ada7],0x1", "G4", "name terminator is no longer NUL", "name char[0x20] + NUL at +0x1f"),
    ("MU5", 0x40EC2B, "cmp edi,0x98ad90", "cmp edi,0x98ad91", "G5", "a sentinel moves off +0x08", "16 cmp sentinels"),
    ("MU6", 0x4D2423, "add edi,0x1c", "add edi,0x18", "G5", "the sentinel scan advances by 0x18", "0x1c scan advance"),
    ("MU7", 0x596037, "[ecx*4+0x9267e4]", "[ecx*8+0x9267e4]", "G6", "candidate store index widens to *8", "all 7 mem refs *4"),
    ("MU8", 0x596017, "cmp ecx,0x40", "cmp ecx,0x30", "G7", "builder band split 0x40 -> 0x30", "builder band sequence"),
    ("MU9", 0x596028, "and ebx,0x8000003f", "and ebx,0x8000007f", "G7", "mod-64 mask widened to mod-128", "builder band sequence"),
    ("MU10", 0x4956C6, "cmp DWORD PTR [ebp-0x28],0x80", "cmp DWORD PTR [ebp-0x28],0x40", "G8", "candidate loop bound 0x80 -> 0x40", "A: 0x80 slots -> cand -> imul"),
    ("MU11", 0x4F05BD, "or BYTE PTR [eax+0x98adb9],0x1", "or BYTE PTR [eax+0x98adb9],0x2", "G9", "a bit8 setter becomes bit9", "bit8: 1 clear + 3 set"),
    ("MU14", 0x59612A, "cmp ecx,0x80", "cmp ecx,0x7c", "G6", "builder loop bound 0x80 -> 0x7c", "table = 128 dwords"),
    ("MU15", 0x435634, "mov ds:0x98ba79,al", "mov ds:0x98ba7a,al", "G10", "prototype +0x25 store lands on +0x26", "source->dest pairs"),
    ("MU16", 0x4EF398, "and BYTE PTR [ebx+0x98adb9],0xfe", "and BYTE PTR [ebx+0x98adb9],0xfc", "G9", "the bit8 clearer becomes bit9", "1 and 0xfe + 3 or 0x1"),
    ("MU12", 0x43565A, "mov eax,DWORD PTR [edx+0x14208]", "mov eax,DWORD PTR [edx+0x14210]", "G10", "prototype dword source +0x14208 -> +0x14210", "proto stores into row 63"),
]
NOOP = ("MU13", 0x4956F9, "add esp,0xc", "add esp,0x10", "NOOP", "an instruction no gate pins", "no claim")


def run(patch=None):
    env = dict(os.environ)
    if patch:
        env["SMAC_M358_PATCH"] = patch
    p = subprocess.run([sys.executable, "-u", SCRIPT], capture_output=True, text=True, env=env)
    red = sorted(set(re.findall(r"^FAIL (G\d+b?):", p.stdout, re.M)), key=lambda s: int(s[1:]))
    return p.returncode, red, p.stdout + p.stderr


def main():
    lines, rows, cov = [], [], set()
    rc0, red0, out0 = run()
    lines.append("M358 mutation harness - %d declared mutants" % (len(MUTANTS) + 1))
    lines.append("MU0 baseline: exit %d reds %s" % (rc0, red0 or "[]"))
    ok_base = rc0 == 0 and not red0
    for mid, addr, old, new, gate, why, claim in MUTANTS + [NOOP]:
        rc, red, out = run("0x%x|%s|%s" % (addr, old, new))
        if "PATCH REJECTED" in out:
            score = "PATCH-FAIL"
        elif gate == "NOOP":
            score = "NO-OP " if (rc == 0 and not red) else "BAD-NOOP"
        else:
            score = "SCORED" if (rc != 0 and gate in red) else "MISSED"
            cov.update(red)
        lines.append("%-5s 0x%06x %-34s -> %-34s gate %-3s %s reds=%s  [%s]" % (
            mid, addr, old, new, gate, score, red or "[]", claim))
        rows.append((mid, gate, score))
    bad = [r for r in rows if r[2] not in ("SCORED", "NO-OP ")]
    lines.append("")
    lines.append("covered gates (measured): %s" % sorted(cov, key=lambda s: int(s[1:])))
    lines.append("scored %d/%d, NO-OP %s, bad %s" % (
        sum(1 for r in rows if r[2] == "SCORED"), len(rows),
        [r[0] for r in rows if r[2] == "NO-OP "], [r[0] for r in bad]))
    ok = ok_base and not bad
    scored = sum(1 for r in rows if r[2] == "SCORED")
    noop = [r[0] for r in rows if r[2] == "NO-OP "]
    gcov = sorted(cov, key=lambda s: int(s[1:]))
    if ok:
        lines.append("PASS HARNESS M358: %d/%d scored, NO-OP %s, covered %s"
                     % (scored, len(rows), noop, gcov))
    else:
        lines.append("FAIL HARNESS M358: bad %s" % ([r[0] for r in bad],))
    text = "\n".join(lines) + "\n"
    print(text, end="")
    with open(OUT, "w") as f:
        f.write(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
