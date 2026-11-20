#!/usr/bin/env python3
"""M329 mutation harness: every gate in scripts/m329_scratchtree.py must be able to FAIL
on a real state, and every mutant must redden exactly the gate set it declares.

One family only - `code`: M329_PATCH rewrites one instruction LINE of the .text cache
(scratch/m574/text.txt) IN MEMORY (several specs joined by ';;'). The exe is never touched
and the census writes its evidence into a temp M329_EV tree, never over the real one.
A crash is NOT a red gate: a run without the summary line scores ERROR.

    python3 -u scripts/m329_mutate.py                 # score against the declared sets
    M329_MUT_MEASURE=1 python3 -u scripts/m329_mutate.py   # print what each mutant reddens
"""
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENSUS = os.path.join(ROOT, "scripts/m329_scratchtree.py")
TMP = tempfile.mkdtemp(prefix="m329mut-")
GATE_RX = re.compile(r"^(G\d+) (PASS|FAIL) ", re.M)
SUM_RX = re.compile(r"^== M329: (\d+)/(\d+) ==$", re.M)
GATES = ["G%d" % i for i in range(1, 14)]

# (id, patch spec, declared reddened set)  - the sets were MEASURED with M329_MUT_MEASURE=1
MUTANTS = [
    ("MU1", "0x49b301|mov ecx,0x6a9480|mov ecx,0x6a9484", {"G1", "G13"}),
    ("MU2", "0x41a8fa|mov dword ptr [ebp-0x8],edi|mov dword ptr [ebp-0x18],edi",
     {"G1", "G12", "G13"}),
    ("MU3", "0x4a9e13|test eax,eax|test ebx,ebx", {"G1", "G13"}),
    ("MU4", "0x41a8fd|mov eax,dword ptr [edi+0x3ff3c]|mov eax,dword ptr [edi+0x3ff5c]",
     {"G2", "G12", "G13"}),
    ("MU5", "0x41a976|mov eax,dword ptr [edi+0x3ff3c]|mov eax,dword ptr [edi+0x3ff4c]",
     {"G2", "G13"}),
    ("MU6", "0x41a90a|shl edx,0x4|shl edx,0x3", {"G3", "G12", "G13"}),
    ("MU7", "0x41a90d|mov esi,dword ptr [edx+0x95da88]|mov esi,dword ptr [edx+0x95da90]",
     {"G3", "G13"}),
    ("MU8", "0x41a98d|mov eax,ds:0x91b5b4|mov eax,ds:0x91b5b8", {"G4", "G13"}),
    ("MU9", "0x41a996|test byte ptr ds:0x985ae8,0x80|test byte ptr ds:0x985ae8,0x40",
     {"G4", "G13"}),
    ("MU10", "0x41a9a0|mov eax,0x1|mov eax,0x2", {"G4", "G13"}),
    ("MU11", "0x41a9d2|mov ds:0x99aa38,eax|mov ds:0x99aa3c,eax", {"G5", "G6", "G13"}),
    ("MU12", "0x41a9da|test edx,0x200000|test edx,0x100000", {"G6", "G13"}),
    ("MU13", "0x41a9e2|or al,0x2|or al,0x4", {"G6", "G13"}),
    ("MU14", "0x41aaec|mov edi,0x8000|mov edi,0x9000", {"G6", "G13"}),
    ("MU15", "0x41ad4d|test dword ptr ds:0x99aa38,0x20000|nop", {"G6", "G13"}),
    ("MU16", "0x41abdc|and ecx,0xf000000|and ecx,0x80000000", {"G7", "G9", "G12", "G13"}),
    ("MU17", "0x59ed6c|mov dword ptr [ebx+0x94d600],0xdfbe41|"
             "mov dword ptr [ebx+0x94d600],0x1f000000", {"G9", "G12", "G13"}),
    ("MU18", "0x41ad8c|shl edx,0x4|shl edx,0x3", {"G8", "G13"}),
    ("MU19", "0x4e494c|mov ecx,dword ptr [edi+0x94d600]|mov ecx,dword ptr [edi+0x94d604]",
     {"G9", "G13"}),
    ("MU20", "0x41ade4|test byte ptr [eax+0x38],0x40|test byte ptr [eax+0x38],0x20",
     {"G10", "G13"}),
    ("MU21", "0x41adf7|mov dword ptr [edx+0x7c],ecx|mov dword ptr [edx+0x84],ecx",
     {"G10", "G13"}),
    ("MU22", "0x41aba5|push 0x6899ec|push 0x6899f0", {"G11", "G13"}),
    ("MU23", "0x41aba3|push 0x41|push 0x42", {"G11", "G13"}),
    ("MU24", "0x41abaa|call 0x6267a5|call 0x626634", {"G11", "G12", "G13"}),
    ("MU25", "0x41ae51|call dword ptr [edx+0xf0]|call 0x5e4afc", {"G10", "G13"}),
    # the out-of-scope control: a line inside the frame that NO measurement reads
    ("MU26", "0x41a903|push eax|nop", set()),
]


def run(patch=None):
    env = dict(os.environ)
    env["M329_EV"] = TMP
    env.pop("M329_PATCH", None)
    env.pop("M329_PIN", None)
    if patch:
        env["M329_PATCH"] = patch
    p = subprocess.run([sys.executable, "-u", CENSUS], capture_output=True, text=True,
                       env=env, timeout=900)
    txt = p.stdout
    gates = {m.group(1): m.group(2) for m in GATE_RX.finditer(txt)}
    s = SUM_RX.search(txt)
    s = (s.group(1), s.group(2)) if s else None
    if not gates or not s:
        return None, (txt[-400:] or p.stderr[-400:]), p.returncode
    return {g for g, v in gates.items() if v == "FAIL"}, s, p.returncode


def main():
    measure = os.environ.get("M329_MUT_MEASURE") == "1"
    selftest = "--selftest" in sys.argv
    rows, bad = [], 0
    OUT = []

    def P(line):
        OUT.append(line)
        print(line)

    sys.stderr.write("harness run dir: %s\n" % TMP)
    P("== M329 mutation harness: %d mutants, TMP=<mkdtemp m329mut-XXXXXX under $TMPDIR, "
      "see stderr> ==" % len(MUTANTS))
    base_red, base_sum, rc = run({})
    P("base: reddened=%s summary=%s rc=%s" % (sorted(base_red or []), base_sum, rc))
    if base_red is None:
        P("HARNESS FAIL: the unmutated census run does not report gates")
        return 1
    if base_red:
        P("SELFTEST FAIL: the unmutated instrument is not green") if selftest else None
        return 1
    for (mid, spec, declared) in MUTANTS:
        red, summ, rc = run(spec)
        if red is None:
            P("%-5s %-58s ERROR rc=%s %s" % (mid, spec[:58], rc, summ))
            bad += 1
            continue
        ok = (red == declared)
        rows.append((mid, sorted(red), sorted(declared), ok))
        if measure:
            P("%-5s %-58s measured=%s summary=%s" %
              (mid, spec[:58], ",".join(sorted(red)) or "NO-OP", summ))
        else:
            P("%-5s %-58s reddened=%-34s declared=%-34s %s" %
              (mid, spec[:58], ",".join(sorted(red)) or "NO-OP",
               ",".join(sorted(declared)) or "NO-OP", "OK" if ok else "MISMATCH"))
        if not ok:
            bad += 1
    # gate coverage, from the measured rows collected above
    covered = set()
    for (_mid, red, _declared, _ok) in rows:
        covered |= set(red)
    uncov = [g for g in GATES if g not in covered]
    n = len(MUTANTS) - bad
    P("gate coverage: every gate reddened by >=1 mutant: %s (uncovered=%s)" %
      (not uncov, uncov or "-"))
    P("declared NO-OP (out-of-scope) mutants: %s" %
      ", ".join(m for (m, _s, d) in MUTANTS if not d) or "-")
    P("HARNESS %s %d/%d" % ("PASS" if bad == 0 else "FAIL", n, len(MUTANTS)))
    dst = os.path.join(ROOT, "evidence", "m329_mutate.txt")
    if not measure:
        open(dst, "w").write("\n".join(OUT) + "\n")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
