#!/usr/bin/env python3
"""M372 mutation harness: every VERIFIED row of the M372 block names a mutant here,
and this harness proves each named mutant actually reddens its gate.

Two mutant families:
  TEXT  M372_PATCH='<addr>|<new instruction text>' rewrites one line of the .text
        cache in memory (the instruction stream the instrument reads).
  ALGO  M372_ALGO=n flips a CLASSIFIER / TRACER law: the disp32 endianness, the
        store/read partition, the emitter branch, the parser base, the register-chain
        depth, the address-dword alignment.
  ENV   M372_TEXT=<truncated cache> - an INPUT mutant: the loader function is removed
        from the cache, so G0's anchor check must fail.

A mutant is KILLED iff the instrument exits non-zero AND the expected gate is named
in its RED list.  A mutant that leaves the run green is a SURVIVOR and fails this
harness (a check that cannot be reddened is not a gate).
"""
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts/m372_semaphore_cell.py")
CACHE = os.path.join(ROOT, "scratch/m574/text.txt")

# (id, lever, value, gate that must go RED)
MUTANTS = [
    ("MU1", "TEXT", "0x58f303|push 0x0", "G2"),
    ("MU2", "TEXT", "0x58f306|push 0x692854", "G2"),
    ("MU3", "TEXT", "0x628731|cmp ecx,0x31", "G3"),
    ("MU4", "TEXT", "0x57cb18|and ecx,0x1000000", "G4"),
    ("MU5", "TEXT", "0x57c99b|and esi,0xffffffff", "G4"),
    ("MU6", "TEXT", "0x4dc740|and ecx,0xffffffff", "G4"),
    ("MU7", "TEXT", "0x58ecc9|mov ds:0x92bf10,eax", "G1"),
    ("MU8", "TEXT", "0x5a1150|test DWORD PTR ds:0x985ae8,0x2000000", "G6"),
    ("MU9", "TEXT", "0x59ef11|test eax,0x400000", "G6"),
    ("MU10", "TEXT", "0x58efc4|mov esi,0x92bdf0", "G7"),
    ("MU11", "TEXT", "0x4dc77c|mov ds:0x92bf0c,edx", "G4"),
    ("MU12", "TEXT", "0x58eca8|push 0x69278c", "G5"),
    ("MU13", "TEXT", "0x58ee0f|call 0x5ea484", "G3"),
    ("A1", "ALGO", "1", "G1"),
    ("A2", "ALGO", "2", "G1"),
    ("A3", "ALGO", "3", "G2"),
    ("A4", "ALGO", "4", "G3"),
    ("A5", "ALGO", "5", "G4"),
    ("A6", "ALGO", "6", "G7"),
    ("A7", "ENV", None, "G0"),
]
GATES = ["G0", "G1", "G2", "G3", "G4", "G5", "G6", "G7"]


def truncated_cache():
    """A cache with FUN_0058e7f0's body removed - the loader anchor disappears."""
    dst = os.path.join(tempfile.gettempdir(), "m372_notloader.txt")
    line = re.compile(r"^\s*([0-9a-f]{6,8}):")
    with open(CACHE, "r", errors="replace") as f, open(dst, "w") as g:
        for ln in f:
            m = line.match(ln)
            if m and 0x58E7F0 <= int(m.group(1), 16) < 0x58F002:
                continue
            g.write(ln)
    src = os.path.getsize(CACHE)
    assert os.path.getsize(dst) < src, "truncated cache is not smaller than the source"
    return dst


def run(env_add):
    env = dict(os.environ)
    env.pop("M372_PATCH", None)
    env.pop("M372_ALGO", None)
    env.pop("M372_TEXT", None)
    env.update(env_add)
    p = subprocess.run([sys.executable, "-u", SCRIPT], capture_output=True, text=True, env=env)
    reds = []
    m = re.search(r"RED gates: (\[.*\])", p.stdout)
    if m:
        reds = re.findall(r"'(G\d)'", m.group(1))
    return p.returncode, p.stdout, reds, p.stderr


def main():
    print("== M372 mutation harness ==")
    rc, out, reds, err = run({})
    base_pass = "PASS M372: 8/8" in out
    print("  baseline: rc=%d PASS=%s" % (rc, base_pass))
    if not base_pass:
        print("  baseline is not green - refusing to score mutants")
        raise SystemExit(1)
    killed = 0
    rows = []
    for mid, kind, val, want in MUTANTS:
        if kind == "TEXT":
            env = {"M372_PATCH": val}
        elif kind == "ALGO":
            env = {"M372_ALGO": val}
        else:
            env = {"M372_TEXT": truncated_cache()}
        rc, out, reds, err = run(env)
        hit = (rc != 0) and (want in reds)
        applied = "not found in .text cache" not in err and "already equal" not in err
        ok = hit and applied
        killed += 1 if ok else 0
        rows.append((mid, kind, want, reds, rc, ok))
        print("  %-4s %-4s %-28s want=%s red=%s rc=%d %s"
              % (mid, kind, (val or "truncated cache")[:28], want,
                 ",".join(reds) or "-", rc, "KILLED" if ok else "SURVIVOR"))
    cov = {g: [r[0] for r in rows if g in r[3] and r[5]] for g in GATES}
    print("\n  coverage (gate -> mutants that redden it):")
    for g in GATES:
        print("   %s %s" % (g, ",".join(cov[g]) or "NONE"))
    uncover = [g for g in GATES if not cov[g]]
    print("\n%s M372 harness: %d/%d killed, %d survivors, coverage %d/%d"
          % ("PASS" if killed == len(MUTANTS) and not uncover else "FAIL",
             killed, len(MUTANTS), len(MUTANTS) - killed,
             len(GATES) - len(uncover), len(GATES)))
    if uncover:
        print("  uncovered gates: %s" % uncover)
    if killed != len(MUTANTS) or uncover:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
