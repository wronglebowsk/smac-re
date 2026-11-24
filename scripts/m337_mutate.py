#!/usr/bin/env python3
"""M337 mutant harness — every gate in scripts/m337_item_order.py must redden on a real defect.

Each mutant copies terran.exe (and/or alpha.txt) to a temp dir, patches ONE anchor, runs the
instrument with --json in a fresh subprocess and checks the EXACT set of reddened gates against
the declared set.  A NO-OP mutant proves the gates are not oversensitive, and a control run on
the pristine copies proves the copy path is neutral.

    python3 -u scripts/m337_mutate.py            # PASS/FAIL HARNESS n/m
    python3 -u scripts/m337_mutate.py --selftest # the harness's own 3 checks
"""
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, "programs", "terran.exe")
ALPHA = os.path.join(ROOT, "programs", "alpha.txt")
TOOL = os.path.join(ROOT, "scripts", "m337_item_order.py")

IMG = 0x400000

# (name, kind, anchor, replacement, declared red set)
#   kind "exe-bytes": anchor is a VA, replacement is hex bytes of equal length
#   kind "alpha-line": anchor is (lineno, old_substr), replacement is the new substring
MUTANTS = [
    ("MU1", "exe-bytes", 0x57A811, "44 4d 98 00", {"G2", "G3", "G7"}),
    ("MU2", "exe-bytes", 0x57A85F, "24 55 98 00", {"G2", "G4"}),
    ("MU3", "exe-bytes", 0x57A895, "94 54 98 00", {"G2", "G3", "G7"}),
    ("MU4", "exe-bytes", 0x691CD4, "5a", {"G1"}),                    # FACILITIES -> FACILITIEZ
    ("MU5", "exe-bytes", 0x4F48D0, "4c 4d 98 00", {"G6"}),           # view disp +4
    ("MU6", "exe-bytes", 0x57A833, "89 46 08", {"G5", "G6"}),        # int2 lands at +0x14
    ("MU7", "exe-bytes", 0x5EAA40, "00 00 00 00", {"G5"}),           # converter call target
    ("MU8", "exe-bytes", 0x57A875, "89 46 28", {"G5"}),              # trailing read order
    ("MU9", "alpha-line", (596, "Recreation Commons,"), "Recreation Commons, 1,2,3,4,5,", {"G3", "G4", "G8"}),
    ("MU11", "exe-bytes", 0x4F4A35, "83 fe 48", {"G2"}),              # consumer bound -> 72
    ("MU12", "exe-bytes", 0x57A867, "2a", {"G7"}),                    # jl no longer skips the tail
    ("MU10", "exe-bytes", 0x9AC010, "90", set()),                    # NO-OP (.rsrc byte)
]


def exe_off(b):
    pe = struct.unpack_from("<I", b, 0x3C)[0]
    nsec = struct.unpack_from("<H", b, pe + 6)[0]
    optsz = struct.unpack_from("<H", b, pe + 20)[0]
    base = pe + 24 + optsz
    secs = []
    for i in range(nsec):
        o = base + i * 40
        vs, va, rs, rp = struct.unpack_from("<IIII", b, o + 8)
        secs.append((IMG + va, rs, rp))

    def off(va):
        for v, rs, rp in secs:
            if v <= va < v + rs:
                return rp + va - v
        raise KeyError("va %#x not mapped" % va)
    return off


def apply(kind, anchor, repl, exe_path, alpha_path):
    if kind == "exe-bytes":
        b = bytearray(open(exe_path, "rb").read())
        o = exe_off(b)(anchor)
        new = bytes.fromhex(repl)
        assert len(new) == len(repl.split()), "replacement length"
        old = bytes(b[o:o + len(new)])
        b[o:o + len(new)] = new
        open(exe_path, "wb").write(b)
        return "0x%x %s -> %s" % (anchor, old.hex(" "), repl)
    lineno, old_s = anchor
    lines = open(alpha_path, "r", errors="replace").read().splitlines(keepends=True)
    assert old_s in lines[lineno - 1], "alpha line %d lacks %r" % (lineno, old_s)
    lines[lineno - 1] = lines[lineno - 1].replace(old_s, repl, 1)
    open(alpha_path, "w").write("".join(lines))
    return "alpha:%d %r -> %r" % (lineno, old_s, repl)


def run_tool(exe_path, alpha_path):
    p = subprocess.run([sys.executable, "-u", TOOL, "--json", "--exe", exe_path,
                        "--alpha", alpha_path], capture_output=True, text=True)
    lines = [l for l in p.stdout.strip().splitlines() if l.startswith("{")]
    assert lines, "no JSON from the tool:\n%s\n%s" % (p.stdout[-1500:], p.stderr[-1500:])
    return json.loads(lines[-1])


def red_set(payload):
    return {k for k, v in payload["gates"].items() if v != "PASS"}


def main():
    selftest = "--selftest" in sys.argv
    ok = 0
    total = 0
    if selftest:
        checks = [
            ("selftest: exe_off maps 0x57a811 to a readable imm",
             lambda: (lambda b: exe_off(b)(0x57A811) > 0)(open(EXE, "rb").read())),
            ("selftest: red_set reads a FAIL row",
             lambda: red_set({"gates": {"G1": "PASS", "G2": "FAIL"}}) == {"G2"}),
            ("selftest: a pristine run is 8/8",
             lambda: all(v == "PASS" for v in run_tool(EXE, ALPHA)["gates"].values())),
        ]
        for name, fn in checks:
            try:
                assert fn()
                print("PASS %s" % name)
                ok += 1
            except AssertionError as e:
                print("FAIL %s %s" % (name, e))
            total += 1
        print("SELFTEST %d/%d" % (ok, total))
        return 0 if ok == total else 1

    tmp = tempfile.mkdtemp(prefix="m337_mut_")
    try:
        # control: pristine copies, no defect expected
        exe0, alp0 = os.path.join(tmp, "terran.exe"), os.path.join(tmp, "alpha.txt")
        shutil.copy(EXE, exe0)
        shutil.copy(ALPHA, alp0)
        ctl = run_tool(exe0, alp0)
        total += 1
        if not red_set(ctl):
            print("PASS control pristine copies: 8/8 gates, digest %s" % ctl["table_digest"])
            ok += 1
        else:
            print("FAIL control pristine copies reddened %s" % sorted(red_set(ctl)))

        for name, kind, anchor, repl, declared in MUTANTS:
            exe1, alp1 = os.path.join(tmp, name + ".exe"), os.path.join(tmp, name + ".txt")
            shutil.copy(EXE, exe1)
            shutil.copy(ALPHA, alp1)
            how = apply(kind, anchor, repl, exe1, alp1)
            got = red_set(run_tool(exe1, alp1))
            total += 1
            if got == declared:
                print("PASS %s %s -> red %s" % (name, how, sorted(got) or "[] (NO-OP)"))
                ok += 1
            else:
                print("FAIL %s %s -> red %s, declared %s" % (name, how, sorted(got), sorted(declared)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("HARNESS %s %d/%d" % ("PASS" if ok == total else "FAIL", ok, total))
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(main())
