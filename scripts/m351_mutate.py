#!/usr/bin/env python3
"""M351 mutation harness - every VERIFIED row of the `## M351` block must name a mutant
that REDDENS it.  Mutants are applied to the objdump listing text (one instruction each),
so the acceptance script runs unmodified apart from SMAC_M351_TEXT; a model mutant flips
the script's own sign classifier through SMAC_M351_MUTANT.

    python3 -u scripts/m351_mutate.py            # full run, writes evidence/m351_mutate.txt

Scoring: a mutant is SCORED when the acceptance run exits non-zero AND the FAIL set is
non-empty.  NO-OP mutants must stay green.  Coverage is the set of gates the mutants
actually reddened (measured, not authored).
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")
SCRIPT = os.path.join(ROOT, "scripts", "m351_type_producer.py")
OUT = os.path.join(ROOT, "evidence", "m351_mutate.txt")
TMP = os.path.join(ROOT, "scratch", "m351_mut")

ROW = re.compile(r"^(\s*)([0-9a-f]{6,8}):\t([0-9a-f ]+)\t(.*)$")

# (id, addr, old-mnemonic-substring, new-mnemonic, gate it must redden, why)
MUTANTS = [
    ("MU1", 0x49772A, "and eax,0x20", "and eax,0x10", "G1", "sign test -> 0x10"),
    ("MU2", 0x49777C, "neg eax", "not eax", "G1", "the negation itself"),
    ("MU3", 0x494E83, "and eax,0x20", "and eax,0x10", "G2", "second site's sign test"),
    ("MU4", 0x495BC8, "imul eax,eax,0x30", "imul eax,eax,0x34", "G3", "type stride 0x30 -> 0x34"),
    ("MU5", 0x495C0E, "[esi+0x984d44]", "[esi+0x984d48]", "G3", "cost field +0xc -> +0x10"),
    ("MU6", 0x495DFF, "or al,0x10", "or al,0x20", "G3", "unit rows get the facility bit"),
    ("MU7", 0x495E0A, "[ebp-0x24]", "[ebp-0x2c]", "G3", "append the design id, not the type"),
    ("MU8", 0x49613B, "mov eax,0x1", "mov eax,0x21", "G4", "flag fn returns 0x20"),
    ("MU9", 0x495A8D, "or al,0x20", "or al,0x10", "G5", "facility rows lose the +bit"),
    ("MU10", 0x401217, "[edx+0x4]", "[edx+0x8]", "G6", "node item stored at +8"),
    ("MU11", 0x49549D, "[eax+0x8]", "[eax+0x4]", "G7", "flags read the item field"),
    ("MU12", 0x418B57, "[edx+0x50]", "[edx+0x54]", "G8", "store to queue slot 1"),
    ("MU13", 0x418B54, "mov eax,DWORD PTR [ebp-0x10]", "neg eax", "G9", "negate at the store"),
    ("MU14", 0x495B00, "[eax+0xa774]", "[eax+0xa778]", "G13", "cell <- a different field"),
    ("MU15", 0x495AEF, "[ebp-0x30]", "[ebp-0x34]", "G14", "facility compare off the slot"),
    ("MU16", 0x495B39, "0x48", "0x47", "G3", "unit loop bound 72 -> 71"),
    ("MU17", 0x59601F, "shl eax,0x6", "shl eax,0x5", "G15", "owner tag 6 bits -> 5"),
    ("MU18", 0x4956C6, "0x80", "0x40", "G5", "facility loop bound 128 -> 64"),
    ("MU19", 0x495E5C, "neg edx", "not edx", "G14", "queue compare uses +i"),
    ("MU20", 0x495B30, "[ebp-0x24]", "[ebp-0x20]", "NOOP", "an instruction no gate pins"),
]
MODEL = [("MU21", "sign", "G11", "classifier: sign bit 0x20 -> 0x10")]


def load():
    with open(TEXT, "r", errors="replace") as f:
        return f.read().split("\n")


def patch(lines, addr, old, new):
    hit = 0
    for i, l in enumerate(lines):
        m = ROW.match(l)
        if not m:
            continue
        if int(m.group(2), 16) != addr:
            continue
        body = re.sub(r"\s+", " ", m.group(4).strip())
        if old not in body:
            return None, "target text %r not at 0x%x (%r)" % (old, addr, body)
        lines[i] = "%s%s:\t%s\t%s" % (m.group(1), m.group(2), m.group(3),
                                      body.replace(old, new, 1))
        hit += 1
    return hit, ("patched %d line(s)" % hit if hit else "address 0x%x absent" % addr)


def run(env_extra):
    env = dict(os.environ)
    env.update(env_extra)
    p = subprocess.run([sys.executable, "-u", SCRIPT], capture_output=True, text=True, env=env)
    red = sorted(set(re.findall(r"^FAIL\s+(G\d+)", p.stdout, re.M)), key=lambda s: int(s[1:]))
    return p.returncode, red, p.stdout


def main():
    os.makedirs(TMP, exist_ok=True)
    base = load()
    rc0, red0, _ = run({"SMAC_M351_TEXT": TEXT})
    print("M351 mutation harness - %d declared mutants, baseline row %s"
          % (len(MUTANTS) + len(MODEL), "MU0"))
    print("MU0   baseline (unmutated listing): exit %d reds %s" % (rc0, red0 or "[]"))
    ok_base = rc0 == 0 and not red0
    lines_out = []
    lines_out.append("M351 mutation harness (scripts/m351_mutate.py) - baseline row MU0")
    lines_out.append("MU0 baseline exit=%d reds=%s" % (rc0, red0))
    lines_out.append("")
    scored, noop, missed, uncovered = 0, [], [], set()
    covered = set()
    for mid, addr, old, new, want, why in MUTANTS:
        lines = list(base)
        hit, msg = patch(lines, addr, old, new)
        if hit is None or not hit:
            missed.append((mid, msg))
            print("  %-5s SKIP  %s" % (mid, msg))
            lines_out.append("%-5s SKIP  %s" % (mid, msg))
            continue
        path = os.path.join(TMP, "%s.txt" % mid)
        with open(path, "w") as f:
            f.write("\n".join(lines))
        rc, red, _ = run({"SMAC_M351_TEXT": path})
        bad = rc == 0 or not red
        tag = "NOOP" if want == "NOOP" else "SCORE"
        if want == "NOOP":
            if rc == 0 and not red:
                noop.append(mid)
                print("  %-5s ok    NO-OP stays green (%s)" % (mid, why))
                lines_out.append("%-5s ok    NO-OP stays green (%s)" % (mid, why))
            else:
                missed.append((mid, "NO-OP mutant reddened %s" % red))
                print("  %-5s BAD   NO-OP reddened %s" % (mid, red))
            continue
        if bad:
            missed.append((mid, "did not redden (exit %d, reds %s)" % (rc, red)))
            print("  %-5s BAD   exit %d reds %s" % (mid, rc, red))
            lines_out.append("%-5s BAD   exit %d reds %s  <- %s" % (mid, rc, red, why))
            continue
        hit_ok = want in red
        if hit_ok:
            scored += 1
            covered |= set(red)
        print("  %-5s %s  reds %-18s expected %-4s %s"
              % (mid, "ok   " if hit_ok else "BAD  ", ",".join(red), want, why))
        lines_out.append("%-5s %s  reds %-18s expected %-4s %s"
                         % (mid, "ok   " if hit_ok else "BAD  ", ",".join(red), want, why))
        if not hit_ok:
            missed.append((mid, "expected %s, reddened %s" % (want, red)))
    for mid, mode, want, why in MODEL:
        rc, red, _ = run({"SMAC_M351_TEXT": TEXT, "SMAC_M351_MUTANT": mode})
        bad = rc == 0 or not red
        if bad:
            missed.append((mid, "model mutant did not redden"))
            print("  %-5s BAD   model mutant exit %d reds %s" % (mid, rc, red))
            lines_out.append("%-5s BAD   model mutant exit %d reds %s" % (mid, rc, red))
            continue
        hit_ok = want in red
        if hit_ok:
            scored += 1
            covered |= set(red)
        print("  %-5s %s  reds %-18s expected %-4s %s"
              % (mid, "ok   " if hit_ok else "BAD  ", ",".join(red), want, why))
        lines_out.append("%-5s %s  reds %-18s expected %-4s %s"
                         % (mid, "ok   " if hit_ok else "BAD  ", ",".join(red), want, why))
        if not hit_ok:
            missed.append((mid, "expected %s, reddened %s" % (want, red)))
    # measured universe of gates, from a clean run
    universe = sorted(set(re.findall(r"^ok\s+(G\d+)", _last_stdout[0] if _last_stdout else "", re.M)),
                      key=lambda s: int(s[1:]))
    uncovered = sorted(set(universe) - covered, key=lambda s: int(s[1:]))
    print()
    print("scored %d, missed %d, NO-OP %s, covered %d/%d, uncovered %s"
          % (scored, len(missed), noop or "[]", len(covered), len(universe), uncovered or "[]"))
    lines_out.append("")
    lines_out.append("scored=%d missed=%d NO-OP=%s covered=%d/%d uncovered=%s"
                     % (scored, len(missed), noop or "[]", len(covered), len(universe), uncovered or "[]"))
    for mid, msg in missed:
        lines_out.append("MISS %s: %s" % (mid, msg))
    ok = ok_base and scored >= len(MUTANTS) + len(MODEL) - 1 and not missed and not uncovered
    lines_out.append(("PASS HARNESS M351: %d/%d scored, NO-OP %s, uncovered %s"
                      % (scored, scored + len(missed), noop or "[]", uncovered or "[]"))
                     if ok else ("FAIL HARNESS M351: scored %d missed %d uncovered %s"
                                 % (scored, len(missed), uncovered)))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        f.write("\n".join(lines_out) + "\n")
    print(lines_out[-1])
    return 0 if ok else 1


_last_stdout = []

if __name__ == "__main__":
    # capture a clean run's gate list (for the measured universe)
    _rc, _red, _out = run({"SMAC_M351_TEXT": TEXT})
    _last_stdout.append(_out)
    sys.exit(main())
