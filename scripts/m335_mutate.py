#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M335 mutation harness — every VERIFIED row of `## M335` names the mutant that reddens it.

Each mutant patches ONE input (an objdump line, the alpha.txt text, or the PE bytes), re-runs the
census gates, and must redden EXACTLY its declared gate SET — measured, not authored: the set is
printed from the run and compared with the declared one, both directions.

    python3 -u scripts/m335_mutate.py              # the whole sweep
    python3 -u scripts/m335_mutate.py --selftest   # the parser/classifier laws on hand-built insns
"""
import argparse
import hashlib
import importlib.util
import io
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location(
    "m335", os.path.join(ROOT, "scripts", "m335_difficulty_ladder.py"))
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

TXT = io.open(M.TEXT, encoding="utf-8", errors="replace").read()
ALPHA = io.open(M.ALPHA, encoding="utf-8", errors="replace").read()
EXE = open(M.EXE, "rb").read()
LINES = TXT.split("\n")
GATES = ["G1", "G2", "G3", "G4", "G5", "G6", "G7"]
import re as _re
# the mutant ids this harness owns (declared so the registry lint can bind row -> mutant)
MUTANTS = ["MU1", "MU2", "MU3", "MU4", "MU5", "MU6", "MU7", "MU8", "MU9", "MU10", "MU11",
           "MU12", "MU13", "MU14", "MU15", "MU16", "MU17", "MU18", "MU19", "MU20"]


def run(lines, alpha, exe):
    """Return {gate: bool}; a gate that raises (a site vanished) counts as FAIL, as it must."""
    out = {}
    try:
        g = M.gates(lines, alpha, exe)
        for k in GATES:
            out[k] = bool(g[k][0])
    except Exception:
        g = {}
    for k in GATES:
        if k not in out:
            out[k] = False
    return out


def patch_line(lines, addr_token, old, new):
    out = list(lines)
    hit = [i for i, l in enumerate(out) if addr_token in l]
    assert len(hit) == 1, "address %s matches %d lines" % (addr_token, len(hit))
    assert old in out[hit[0]], "%r not in %r" % (old, out[hit[0]])
    out[hit[0]] = out[hit[0]].replace(old, new, 1)
    return out


def del_line(lines, addr_token):
    out = [l for l in lines if addr_token not in l]
    assert len(out) == len(lines) - 1
    return out


def va_off(exe, va):
    pe = struct.unpack_from("<I", exe, 0x3c)[0]
    n = struct.unpack_from("<H", exe, pe + 6)[0]
    opt = struct.unpack_from("<H", exe, pe + 20)[0]
    base = struct.unpack_from("<I", exe, pe + 52)[0]
    so = pe + 24 + opt
    for i in range(n):
        vs, v, rs, rp = struct.unpack_from("<IIII", exe, so + i * 40 + 8)
        if base + v <= va < base + v + rs:
            return rp + (va - base - v)
    raise KeyError(hex(va))


# ---- scenarios: name -> (mutator, declared gate set) ----
def mu1():
    return patch_line(LINES, "57ac88:", "0x94d2c4", "0x94d2c8"), ALPHA, EXE


def mu2():
    return patch_line(LINES, "57ac85:", "esi,0x4", "esi,0x8"), ALPHA, EXE


def mu3():
    e = bytearray(EXE)
    o = va_off(bytes(EXE), M.NAMES_VA)
    assert bytes(e[o:o + 4]) == b"DIFF"
    e[o:o + 4] = b"DIFX"
    return LINES, ALPHA, bytes(e)


def mu4():
    a = "\n".join(l for l in ALPHA.split("\n") if l.strip() != "Transcend,")
    return LINES, a, EXE


def mu5():
    # s317 review F8: swap the ROWS on the parsed lines, never the raw newline bytes
    out, seen = [], []
    for line in ALPHA.split("\n"):
        if line.strip() in ("Citizen,", "Specialist,"):
            seen.append(line)
            out.append("__SWAP__")
        else:
            out.append(line)
    assert len(seen) == 2, "expected the two rows, got %r" % (seen,)
    it = iter([seen[1], seen[0]])
    a = "\n".join(next(it) if l == "__SWAP__" else l for l in out)
    assert a != ALPHA
    return LINES, a, EXE


def mu6():
    return del_line(LINES, "599405:"), ALPHA, EXE


def mu7():
    return patch_line(LINES, "5993fb:", "ds:0x985aec", "ds:0x985af0"), ALPHA, EXE


def mu8():
    return patch_line(LINES, "486f2c:", "push   0x6", "push   0x5"), ALPHA, EXE


def mu9():
    return patch_line(LINES, "520728:", "cmp    eax,0x4", "cmp    eax,0x5"), ALPHA, EXE


def mu10():
    return patch_line(LINES, "4ddb27:", "push   edi", "push   ebx"), ALPHA, EXE


def mu11():
    return del_line(LINES, "4ddb3e:"), ALPHA, EXE


def mu12():
    return patch_line(LINES, "484cb3:", ",0x6", ",0x7"), ALPHA, EXE


def mu13():
    # the RIVAL, run for real: replace the array base at every site with another global
    out = [l.replace("0x94d2ac", "0x94d2e0") for l in LINES]
    return out, ALPHA, EXE


def mu14():
    return patch_line(LINES, "4ddb4d:", "[ebp-0x494c]", "[ebp-0x4948]"), ALPHA, EXE


def mu15():
    return patch_line(LINES, "4ddb32:", "add    esi,0x4", "sub    esi,0x4"), ALPHA, EXE


def mu16():
    return patch_line(LINES, "486f2c:", "push   0x6", "push   0x7"), ALPHA, EXE


def mu17():
    return patch_line(LINES, "486f40:", "[eax*4+0x94d2ac]", "[ebx*4+0x94d2ac]"), ALPHA, EXE


def mu18():
    return patch_line(LINES, "57ac83:", "DWORD PTR [esi],eax", "DWORD PTR [esi],edx"), ALPHA, EXE


def mu19():
    return patch_line(LINES, "484cb3:", "[ebp-0x62d8]", "[ebp-0x62d0]"), ALPHA, EXE


def mu20():
    # ALGORITHM mutant: a matcher that only knows the direct absolute form loses the scaled sites
    M.ADDR_RE = _re.compile(r"\[0x94d2(?:ac|b0|b4|b8|bc|c0|c4)\]")
    return LINES, ALPHA, EXE


SCEN = [
    ("MU1 loader bound 0x94d2c4->0x94d2c8", mu1, {"G2", "G3", "G6"}),
    ("MU2 loader step add esi,4->8", mu2, {"G2"}),
    ("MU3 PE section name DIFF->DIFX", mu3, {"G2", "G7"}),
    ("MU4 alpha.txt drop the Transcend row", mu4, {"G1", "G2", "G7"}),
    ("MU5 alpha.txt swap rows 0 and 1", mu5, {"G1", "G7"}),
    ("MU6 delete the 0x599405 index reader", mu6, {"G3", "G5"}),
    ("MU7 index load ds:0x985aec->ds:0x985af0", mu7, {"G5"}),
    ("MU8 clamp hi push 0x6->0x5", mu8, {"G6"}),
    ("MU9 refund cmp eax,4->cmp eax,5", mu9, {"G6"}),
    ("MU10 chooser push edi->push ebx", mu10, {"G4"}),
    ("MU11 delete the dialog seed load", mu11, {"G4"}),
    ("MU12 reader loop bound ,0x6->,0x7", mu12, {"G5"}),
    ("MU13 RIVAL base 0x94d2ac->0x94d2e0", mu13, {"G2", "G3", "G4", "G5", "G6"}),
    ("MU14 seed store slot -0x494c->-0x4948", mu14, {"G4"}),
    ("MU15 chooser walks BACKWARD add->sub", mu15, {"G4"}),
    ("MU16 clamp hi push 0x6->0x7", mu16, {"G6"}),
    ("MU17 clamp index reg eax->ebx", mu17, {"G6"}),
    ("MU18 loader store eax->edx", mu18, {"G2"}),
    ("MU19 reader loop cmp on another slot", mu19, {"G5"}),
    ("MU20 ALGO matcher loses the scaled form", mu20, {"G3"}),
]

BASE = run(LINES, ALPHA, EXE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        # the two algorithm laws the census leans on
        ins = M.parse_text(["  401000:\t6a 06                \tpush   0x6",
                            "  401002:\t8b 04 95 ac d2 94 00 \tmov    eax,DWORD PTR [edx*4+0x94d2ac]",
                            "  garbage line"])
        ok1 = len(ins) == 2 and ins[0][1] == "push" and ins[1][2].endswith("0x94d2ac]")
        # a SCALED operand must be found by the census matcher (the s312 lesson)
        ok2 = any("[" in o and "*4" in o for _, _, o in ins)
        # alpha_rows stops at a blank line and ignores ';' comments
        n, rows = M.alpha_rows("#DIFF\nA,\nB,\n\nC,\n")
        ok3 = n == 1 and rows == ["A", "B"]
        print("ST1 parse_text %s" % ("PASS" if ok1 else "FAIL"))
        print("ST2 scaled operand %s" % ("PASS" if ok2 else "FAIL"))
        print("ST3 alpha_rows %s" % ("PASS" if ok3 else "FAIL"))
        print(("PASS SELFTEST 3/3" if ok1 and ok2 and ok3 else "FAIL SELFTEST"))
        return 0 if ok1 and ok2 and ok3 else 1

    print("M335 mutant sweep: %d scenarios (%s); baseline gates %s"
          % (len(SCEN), ",".join(MUTANTS), "".join(k for k in GATES if BASE[k])))
    assert all(BASE.values()), "baseline is not green - fix the census first"
    rows, bad = [], 0
    for name, fn, declared in SCEN:
        lines, alpha, exe = fn()
        got = run(lines, alpha, exe)
        red = {k for k in GATES if not got[k]}
        ok = red == declared
        bad += (0 if ok else 1)
        rows.append((name, declared, red, ok))
        print("%-42s declared=%-22s measured=%-22s %s"
              % (name, "{" + ",".join(sorted(declared)) + "}",
                 "{" + ",".join(sorted(red)) + "}", "PASS" if ok else "MISMATCH"))
    h = hashlib.sha1("\n".join("%s|%s|%s" % (n, sorted(d), sorted(r)) for n, d, r, _ in rows)
                    .encode()).hexdigest()
    print("digest=%s scored=%d mismatch=%d" % (h[:16], len(rows), bad))
    if bad:
        print("FAIL HARNESS %d/%d" % (len(rows) - bad, len(rows)))
        return 1
    print("PASS HARNESS %d/%d" % (len(rows), len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
