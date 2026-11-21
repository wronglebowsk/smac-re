#!/usr/bin/env python3
"""M332 mutation harness — every VERIFIED gate of m332_difficulty_census.py must be
reddened by >=1 named mutant, and every mutant's reddened set must be EXACTLY what
it declares (both directions measured, not the author's word).

Levers on the instrument (its only two inputs):
  M332_PATCH='addr|new text'   rewrite ONE line of the .text cache in memory
  M332_ALGO=n                  weaken ONE named law of the scanner itself
       1 = the WRITE-side window uses the READ anchor (direction law off)
       2 = the clean-copy rule forgets the call-clobber law
       3 = the encoding scan truncates the displacement to 3 bytes
MU16 is the declared NO-OP: the same edge text with different spacing — the
instrument parses mnemonic+operands, so it must redden nothing, and if it ever
does, a gate is reading formatting instead of measurement.

Usage: python3 -u scripts/m332_mutate.py [--selftest]
"""
import hashlib, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENSUS = [sys.executable, "-u", os.path.join(ROOT, "scripts", "m332_difficulty_census.py"),
          "--no-evidence"]
GATES = ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9"]

MUTANTS = [
    # ---- the store set and the reference census (a removed writer must move
    # G1's counts, G2's set and G3's per-site triple; the KeyError path is a
    # CRASH, and a CRASH is scored as a failure, so the gate must fail first).
    # s312/#346: each of these ALSO reddens G9 now, and it is not incidental —
    # G9.2 re-reads the 0x4ddcf1 store, G9.4 re-reads the pinned copy windows
    # (0x57c5af, 0x57f006, 0x48502e) and G9.2 re-reads the jge edge.
    ("MU1",  "code", "0x4ddcf1|nop", {"G1", "G2", "G3", "G9"}),
    ("MU2",  "code", "0x57c5af|nop", {"G1", "G2", "G3", "G4", "G9"}),
    ("MU3",  "code", "0x57f006|nop", {"G1", "G2", "G3", "G4", "G9"}),
    # ---- value origins: retarget a load and the mirror copy changes identity;
    # a MASTER load also feeds G8's scalar-load count, so G8 moves with it.
    ("MU4",  "code", "0x57c59e|mov eax,DWORD PTR ds:0x92bdf4", {"G4", "G8"}),
    ("MU5",  "code", "0x57eff3|movsx eax,BYTE PTR ds:0x8f0c1c", {"G4"}),
    ("MU6",  "code", "0x484ef8|mov cl,BYTE PTR ds:0x92bdf4", {"G4", "G8"}),
    # 0x48502e stores the BYTE cell, not TARGET: G1's census must NOT move.
    # G9 does move, because G9.4 pins that store as the (TARGET,BYTECELL) copy.
    ("MU7",  "code", "0x48502e|nop", {"G4", "G9"}),
    # ---- reachability: the jge edge that attributes the 4th writer (G9.2
    # reads the same edge, so it dies with it)
    ("MU8",  "code", "0x4ddb5a|jmp 0x4ddef1", {"G3", "G9"}),
    # ---- the pref pairing: name side, field side, both functions.
    # MU13 nops a KEY push, which turns a 6-arg call window into a 5-arg one,
    # so G9.5's argc==6 count moves from 18 to 17 — exactly the arity law it pins.
    ("MU9",  "code", "0x58e8a1|push 0x692724", {"G5", "G6", "G7"}),
    ("MU10", "code", "0x58e8c6|nop", {"G5", "G6", "G7", "G8"}),
    ("MU11", "code", "0x58f159|push 0x692808", {"G6", "G7"}),
    ("MU12", "code", "0x58f11d|mov edx,DWORD PTR ds:0x92bdf4", {"G6", "G7", "G8"}),
    ("MU13", "code", "0x58e905|nop", {"G5", "G6", "G7", "G9"}),
    # ---- scanner-law mutants (the algorithms, not the image)
    ("MU14", "algo", "2", {"G4"}),      # provenance survives redefinition
    ("MU15", "algo", "1", {"G6", "G7"}),  # the direction law is off
    ("MU16", "code", "0x4ddb5a|jge 0x4ddcf1", set()),   # declared NO-OP
    ("MU17", "algo", "3", {"G1"}),      # enc key truncated to 2 bytes
    # ---- s312 review round (#346): the four levers aimed at G9, the gate the
    # reviewer's findings produced.  Each one breaks ONLY the fact it names.
    # the edge whose eax G9.2 attributes to callee 0x5f1394
    ("MU18", "code", "0x4ddb53|call 0x5f1395", {"G9"}),
    # the co-store pair: a different source register keeps every address, the
    # moffs bytes and the store set, so only the register-identity law dies
    ("MU19", "code", "0x57c7b5|mov    ds:0x985aec,ecx", {"G9"}),
    # the array-end use: forward jmp instead of the back edge = not a loop bound
    ("MU20", "code", "0x579bcf|jmp 0x579bd3", {"G9"}),
    # the cmp arms: a 5th immediate moves G1's arm set and G9.1 together
    ("MU21", "code", "0x4f9b5a|cmp DWORD PTR ds:0x985aec,0x5", {"G1", "G9"}),
]


def env_for(kind, payload):
    if kind == "code":
        return {"M332_PATCH": payload}
    return {"M332_ALGO": payload}


def run(env_extra):
    env = dict(os.environ)
    for k in ("M332_PATCH", "M332_ALGO"):
        env.pop(k, None)
    env.update(env_extra)
    p = subprocess.run(CENSUS, env=env, capture_output=True, text=True, timeout=900)
    gates = {}
    for line in p.stdout.splitlines():
        m = re.match(r"^(PASS|FAIL) (G\d+):", line)
        if m:
            gates[m.group(2)] = (m.group(1) == "PASS")
    fin = [l for l in p.stdout.splitlines() if re.match(r"^\S+ M332: \d+/\d+ gates$", l)]
    return p.returncode, gates, "\n".join(fin), p.stdout, p.stderr


def selftest():
    rows, ok = [], True
    rc, g, fin, out, err = run({"M332_PATCH": "deadbeef|mov eax,0x1"})
    s1 = rc != 0 and "not in .text cache" in err
    rows.append(("ST1 bad-address rejected", s1)); ok &= s1
    rc, g, fin, out, err = run({"M332_PATCH": "0x4ddb5a|jge    0x4ddcf1"})
    s2 = rc != 0 and "already equal" in err
    rows.append(("ST2 equal-patch rejected", s2)); ok &= s2
    union = set().union(*[d for _, _, _, d in MUTANTS])
    s3 = union >= set(GATES)
    rows.append(("ST3 every gate has >=1 mutant", s3)); ok &= s3
    noops = [i for i, _, _, d in MUTANTS if not d]
    s4 = noops == ["MU16"]
    rows.append(("ST4 exactly one declared NO-OP (MU16)", s4)); ok &= s4
    rc, g, fin, out, err = run({})
    s5 = rc == 0 and len(g) == len(GATES) and all(g.values())
    rows.append(("ST5 base run %s" % (fin or "no final line"), s5)); ok &= s5
    # #346 P2: "1 NO-OP inert" must mean FORMATTING-inert, never "a site no gate
    # reads".  The declared NO-OP's address is therefore required to be an
    # address a scored mutant also patches and reddens (MU16/MU8 share 0x4ddb5a).
    noop_site = {p.split("|")[0] for _, k, p, d in MUTANTS if k == "code" and not d}
    scored_site = {p.split("|")[0] for _, k, p, d in MUTANTS if k == "code" and d}
    s6 = bool(noop_site) and noop_site <= scored_site
    rows.append(("ST6 the NO-OP's site is a site a scored mutant reddens %s"
                 % sorted(noop_site), s6)); ok &= s6
    for name, good in rows:
        print("%s %s" % ("PASS" if good else "FAIL", name))
    print("== selftest: %d/%d ==" % (sum(1 for _, x in rows if x), len(rows)))
    return 0 if ok else 1


def main():
    if "--selftest" in sys.argv:
        return selftest()
    rows = []
    rc, g, fin, out, err = run({})
    base_ok = rc == 0 and len(g) == len(GATES) and all(g.values())
    rows.append(("BASE", "-", "-", fin or "BASE BROKEN", base_ok))
    scored = noop = mismatch = crash = 0
    for mid, kind, payload, declared in MUTANTS:
        rc, g, fin, out, err = run(env_for(kind, payload))
        if len(g) != len(GATES):
            crash += 1
            rows.append((mid, kind, payload, "CRASH rc=%s gates=%d %s" %
                         (rc, len(g), err.strip().splitlines()[-1:]), False))
            continue
        reddened = {k for k, v in g.items() if not v}
        good = reddened == declared
        if not good:
            mismatch += 1
        if declared:
            scored += 1 if good else 0
        elif good:
            noop += 1
        rows.append((mid, kind, payload, "reddens %s%s" %
                     (sorted(reddened) or "[]",
                      "" if good else "  DECLARED %s" % sorted(declared)), good))
    for r in rows:
        print("%-5s %-5s %-45s %-58s %s" % (r[4] and "PASS" or "FAIL", r[0],
                                            r[1] + " " + r[2], r[3], ""))
    n = len(rows)
    print("measured: %d mutants scored, %d NO-OP inert, %d MISMATCH, %d CRASH" %
          (scored, noop, mismatch, crash))
    tbl = "\n".join("%s %s %s %s" % (r[0], r[1], r[2], r[3]) for r in rows)
    print("digest(rows)=%s" % hashlib.sha256(tbl.encode()).hexdigest()[:16])
    allok = base_ok and mismatch == 0 and crash == 0 and scored == sum(
        1 for m in MUTANTS if m[3]) and noop == sum(1 for m in MUTANTS if not m[3])
    print("%s HARNESS %d/%d" % ("PASS" if allok else "FAIL",
                                sum(1 for r in rows if r[4]), n))
    if allok:
        ev = os.path.join(ROOT, "evidence", "m332_mutate.txt")
        with open(ev, "w") as f:
            f.write("\n".join("%s %s %s %s %s" % (
                r[4] and "PASS" or "FAIL", r[0], r[1], r[2], r[3]) for r in rows))
            f.write("\nmeasured: %d mutants scored, %d NO-OP inert, %d MISMATCH, %d CRASH\n"
                    % (scored, noop, mismatch, crash))
            f.write("digest(rows)=%s\n" % hashlib.sha256(tbl.encode()).hexdigest()[:16])
            f.write("PASS HARNESS %d/%d\n" % (sum(1 for r in rows if r[4]), n))
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
