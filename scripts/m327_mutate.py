#!/usr/bin/env python3
# M327 mutation harness: every gate in scripts/m327_typeband_census.py must be able
# to FAIL on a real state, and every mutant must redden exactly the gate set it
# declares. Families:
#   `code`  M327_PATCH rewrites one instruction LINE of the .text cache
#           (scratch/m574/text.txt) IN MEMORY - the exe is never touched;
#   `save`  a temp copy of programs/saves/m54b_clean.SAV with bytes poked (spec
#           "fileoff/width=value"), passed as M327_SAVE;
#   `poked` a temp copy of programs/saves/m113map.SAV with one marker dword
#           restored to its m54b_clean value (spec "fileoff=-"), M327_POKED;
#   `algo`  M327_ALGO turns one measurement off inside the instrument
#           (1=chain window whole-file, 2=band//32, 3=poke alignment 16,
#            4=every branch counts as a store guard, 5=every slot counts as named,
#            6=variant B becomes the shipped rule, 8=owner read from +15,
#            9=type-array offset -4).
# A crash is NOT a red gate: a run without the summary line scores ERROR.
# The declared sets below were MEASURED by this file with M327_MUT_MEASURE=1.
import os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENSUS = os.path.join(ROOT, "scripts/m327_typeband_census.py")
SAVE = os.path.join(ROOT, "programs/saves/m54b_clean.SAV")
POKED = os.path.join(ROOT, "programs/saves/m113map.SAV")
TYPE0 = 192063                      # T0's type record (Table T0, measured)
UNIT0 = 222783                      # the unit array (Table T0, measured)
TMP = tempfile.mkdtemp(prefix="m327mut-")
GATE_RX = re.compile(r"^(G\d+) (PASS|FAIL) $")
SUM_RX = re.compile(r"^== M327: (\d+)/(\d+) ==$")

MUTANTS = [
    # ---- the .exe chain law (G2) ----
    ("MU1", "code", "0x4bded1|imul   ecx,ecx,0x33", {"G2", "G10"}),
    ("MU2", "code", "0x5ab3a2|movsx  eax,WORD PTR [esi+0x933280]", {"G2", "G10"}),
    ("MU3", "code", "0x4bdeca|movsx  ecx,WORD PTR [eax+0x933284]", {"G2", "G10"}),
    ("MU17", "algo", "1", {"G2", "G10"}),
    # ---- the tile-writer straight line (G7) ----
    ("MU4", "code", "0x5ab369|jl     0x5ab356", {"G7", "G9", "G10"}),
    ("MU5", "code", "0x5ab355|mov    WORD PTR [esi+0x93327c],bx", {"G7", "G10"}),
    ("MU19", "algo", "4", {"G7", "G9", "G10"}),
    # ---- the 67-record census (G3); save pokes move the poke law (G6) too ----
    ("MU6", "save", "%d/1=3" % (UNIT0 + 4 * 52 + 14), {"G3", "G6", "G9", "G10"}),
    ("MU7", "save", "%d/2=497" % (UNIT0 + 4 * 52 + 10),
     {"G3", "G5", "G6", "G9", "G11", "G10"}),
    ("MU8", "save", "%d/2=196" % (UNIT0 + 10), {"G3", "G5", "G6", "G9", "G11", "G10"}),
    ("MU11", "save", "%d/2=300" % UNIT0, {"G3", "G5", "G6", "G10"}),
    ("MU16", "algo", "8", {"G3", "G9", "G10"}),
    ("MU18", "algo", "2", {"G3", "G9", "G10"}),
    # ---- the named-slot / type +0x2d law (G4) ----
    ("MU9", "save", "%d/1=0" % (TYPE0 + 0x2D), {"G4", "G6", "G10"}),
    ("MU12", "save", "%d/1=255" % (TYPE0 + 128 * 52 + 0x2D), {"G4", "G6", "G10"}),
    ("MU22", "algo", "7", {"G4", "G10"}),
    # ---- the predicate variants (G5) and the poke law (G6) ----
    ("MU13", "algo", "6", {"G5", "G10"}),
    ("MU10", "poked", "%d=-" % 223408, {"G6", "G10"}),
    ("MU14", "algo", "3", {"G6", "G10"}),
    # ---- the M80 cross-check (G8), rivals (G9), layout (G1), density (G11) ----
    ("MU15", "algo", "5", {"G4", "G8", "G11", "G10"}),
    ("MU20", "algo", "9", {"G1", "G3", "G4", "G8", "G9", "G11", "G10"}),
    # ---- declared NO-OP: an out-of-scope .text byte change reddens NOTHING, which
    #      proves G1-G9 read measured bytes and not prose.
    ("MU21", "code", "0x5ab345|test   eax,0x40", set()),
]


def run(env):
    e = dict(os.environ)
    e.update(env)
    e["M327_EVIDENCE_ROOT"] = TMP
    p = subprocess.run([sys.executable, "-u", CENSUS], cwd=ROOT, env=e,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    txt = p.stdout.decode("utf-8", "replace")
    lines = txt.splitlines()
    gates = {}
    for l in lines:
        m = re.match(r"^(G\d+) (PASS|FAIL) ", l)
        if m:
            gates[m.group(1)] = m.group(2)
    s = None
    for l in lines:
        m = re.match(r"^== M327: (\d+)/(\d+) ==$", l)
        if m:
            s = (m.group(1), m.group(2))
    if not gates or not s:
        return None, txt[-500:], p.returncode
    return {g for g, v in gates.items() if v == "FAIL"}, s, p.returncode


def temp_save(base, pokes, tag):
    dst = os.path.join(TMP, "mut-%s.SAV" % tag)
    shutil.copyfile(base, dst)
    d = bytearray(open(dst, "rb").read())
    for spec in pokes.split(","):
        where, val = spec.split("=")
        off, width = (where.split("/") + ["1"])[:2]
        pos, w = int(off), int(width)
        d[pos:pos + w] = int(val).to_bytes(w, "little")
    open(dst, "wb").write(bytes(d))
    return dst


def main():
    measure = os.environ.get("M327_MUT_MEASURE") == "1"
    selftest = "--selftest" in sys.argv
    bad, rows = 0, []
    OUT = []

    def P(line):
        OUT.append(line)
        print(line)
    base_red, base_sum, _ = run({})
    P("== M327 mutation harness: %d mutants, TMP=%s ==" % (len(MUTANTS), TMP))
    P("base: reddened=%s summary=%s" % (sorted(base_red or []), base_sum))
    if base_red is None:
        P("HARNESS FAIL: the unmutated census run does not report gates")
        return 1
    if selftest and base_red:
        P("SELFTEST FAIL: the unmutated instrument is not green")
        return 1
    for (mid, fam, spec, declared) in MUTANTS:
        env = {}
        if fam == "code":
            env["M327_PATCH"] = spec
        elif fam in ("save", "poked"):
            src = POKED if fam == "poked" else SAVE
            if spec.endswith("=-"):
                off = int(spec.split("=")[0])
                a = open(SAVE, "rb").read()
                dst = os.path.join(TMP, "unpoke-%d.SAV" % off)
                d = bytearray(open(src, "rb").read())
                d[off:off + 4] = a[off:off + 4]
                open(dst, "wb").write(bytes(d))
                env["M327_POKED"] = dst
            else:
                env["M327_SAVE"] = temp_save(src, spec, mid)
        elif fam == "algo":
            env["M327_ALGO"] = spec
        red, summ, rc = run(env)
        if red is None:
            P("%-5s %-5s %-42s ERROR rc=%s %s" % (mid, fam, spec, rc, summ))
            bad += 1
            continue
        ok = (red == declared)
        rows.append((mid, fam, spec, sorted(red), sorted(declared), ok))
        if measure:
            P("%-5s %-5s %-42s measured=%s summary=%s" %
              (mid, fam, spec, ",".join(sorted(red)), summ))
        else:
            P("%-5s %-5s %-42s reddened=%-40s declared=%-40s %s" %
              (mid, fam, spec, ",".join(sorted(red)) or "-",
               ",".join(sorted(declared)), "OK" if ok else "MISMATCH"))
        if not ok:
            bad += 1
    n = len(MUTANTS) - bad
    noops = [m for (m, _f, _s, d) in MUTANTS if not d]
    P("gate coverage: every gate reddened by >=1 mutant: %s" %
      (all(any(gname in d for (_m, _f, _s, d) in MUTANTS)
           for gname in ["G%d" % i for i in range(1, 10)] + ["G11"])))
    P("declared NO-OPs: %s" % (noops,))
    P("HARNESS %s %d/%d mutants redden exactly their declared gate set" %
      ("PASS" if bad == 0 else "FAIL", n, len(MUTANTS)))
    if not measure:
        dst = os.path.join(ROOT, "evidence/m327_mutate.txt")
        open(dst, "w").write("\n".join(OUT) + "\n")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
