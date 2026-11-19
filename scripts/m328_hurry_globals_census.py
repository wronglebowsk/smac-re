#!/usr/bin/env python3
# M328: name the two HURRY-story globals M326 left OPEN.
#   A = ds:0x91c64c  (4 refs per M326 T6b: the immediate-pay path subtracts the
#       hurry cost from it IN PARALLEL with per-faction ENERGY; writer
#       FUN_00520540 @52065d sits beside M325's ENERGY income writer 520605)
#   B = ds:0x920434  (634 refs per M326 T6e; the deferral gate: mov eax,B;
#       test eax,eax; je pay-path. Boolean shape claimed, noun OPEN)
# STATIC, zero box. Footing: NAMED ## M326 / M325; evidence/m326_block224_census.txt:23,26.
# Law: table FIRST then ASSERT; >=1 RIVAL that FAILS on the printed numbers;
# digest hashes the MEASURED detail; declared sets MEASURED not authored.
# Resolver: REUSES M326's reviewed resolver (import m326_block224_census):
# its INS/owner/classify/memref/value_of/callers_of/scan_strings, subreg fix
# included. Limits DECLARED there (linear backward def-walk <=300 instrs
# depth<=4, affine over opaque runtime leaves, no CFG dataflow proof).
# Mutants: M328_PATCH addr|mn ops (applied to the shared INS after import),
# M328_ALGO 1=writer-values immediate-only (no def-walk) 2=width-blind
# 3=direct-mem-tests-only (misses load-then-test), M328_EVIDENCE_ROOT=<dir>.
import hashlib, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import m326_block224_census as m326

EV = os.environ.get("M328_EVIDENCE_ROOT", ROOT)
ALGO = os.environ.get("M328_ALGO", "0")
A, B = 0x91c64c, 0x920434

def apply_patch():
    p = os.environ.get("M328_PATCH")
    if not p: return 0
    n = 0
    for chunk in p.split(";"):
        chunk = chunk.strip()
        if not chunk: continue
        addr, rest = chunk.split("|", 1)
        mn, _, ops = rest.partition(" ")
        a = int(addr, 16)
        if a not in m326.INS:
            raise SystemExit("M328_PATCH address not in .text cache: %s" % addr)
        if m326.INS[a] == (mn, ops.strip()):
            raise SystemExit("M328_PATCH applied to nothing (already equal)")
        m326.INS[a] = (mn, ops.strip()); n += 1
    if n == 0: raise SystemExit("M328_PATCH applied to nothing")
    return n

NPATCH = apply_patch()

def abs_hits(addr):
    """Every instruction whose memref is the absolute ds:addr (any width),
    plus SUB hits (byte/word lanes addr+1..3) and DISP-form [reg+addr]."""
    hits, sub, disp = [], [], []
    for a in m326.ADDRS:
        w, r, width, mi, src = m326.classify(a)
        if mi is None: continue
        if mi[0] == "abs":
            if mi[1] == addr: hits.append((a, w, r, width, src))
            elif mi[1] in (addr + 1, addr + 2, addr + 3): sub.append(a)
        elif mi[0] == "brk" and mi[2] == addr and mi[4] is None:
            disp.append(a)
    return hits, sub, disp

def role(a, w, r):
    mn, _ = m326.INS[a]
    if w: return "W"
    if mn in ("cmp", "test"): return "T"
    return "R" if r else "?"

def writer_value(a, src):
    """Constant if immediate; else the reviewed backward def-walk.
    ALGO1 = immediate-only (the old blindness the walk exists to cure)."""
    if src is None: return ("rmw", None)
    m = re.fullmatch(r"0x([0-9a-f]+)", src.strip())
    if m: return ("const", int(m.group(1), 16))
    if ALGO == "1": return ("opaque", src)
    reg = m326.reg_of(src)
    if reg:
        v = m326.value_of(a, reg)
        return v if v else ("opaque", src)
    return ("opaque", src)

def census(addr):
    hits, sub, disp = abs_hits(addr)
    rows = []
    for a, w, r, width, src in hits:
        if ALGO == "2": width = 4
        rows.append({"a": a, "role": role(a, w, r), "w": width,
                     "fn": m326.owner(a), "ins": m326.INS[a], "src": src})
    return rows, sub, disp

def main():
    out = []
    def p(s=""):
        print(s); out.append(s)
    p("== M328 census: A=0x%x B=0x%x (ALGO=%s patch=%d) ==" % (A, B, ALGO, NPATCH))
    det = []
    for name, addr in (("A", A), ("B", B)):
        rows, sub, disp = census(addr)
        nw = sum(1 for r in rows if r["role"] == "W")
        nt = sum(1 for r in rows if r["role"] == "T")
        nr = sum(1 for r in rows if r["role"] == "R")
        widths = sorted({r["w"] for r in rows})
        p("%s 0x%x: hits=%d W=%d T=%d R=%d widths=%s sub=%d disp=%d" %
          (name, addr, len(rows), nw, nt, nr, widths, len(sub), len(disp)))
        det.append("%s|hits=%d|W=%d|T=%d|R=%d|w=%s|sub=%d|disp=%d" %
                   (name, len(rows), nw, nt, nr, widths, len(sub), len(disp)))
        fns = {}
        for r in rows: fns.setdefault(r["fn"], []).append(r)
        p("  owners(%d): %s" % (len(fns),
          ", ".join("%s:%d" % (f, len(v)) for f, v in
                    sorted(fns.items(), key=lambda kv: -len(kv[1]))[:12])))
        for r in rows:
            if r["role"] == "W":
                v = writer_value(r["a"], r["src"])
                p("  W %06x %-16s %s %s -> %s" %
                  (r["a"], r["fn"], r["ins"][0], r["ins"][1], v))
                det.append("W|%s|%06x|%s|%s|%s" % (name, r["a"], r["fn"],
                           r["ins"][0], r["ins"][1], v))
        if len(rows) <= 12:
            for r in rows:
                p("  %s %06x %-16s %s %s" %
                  (r["role"], r["a"], r["fn"], r["ins"][0], r["ins"][1]))
                det.append("%s|%s|%06x|%s|%s %s" % (r["role"], name, r["a"],
                           r["fn"], r["ins"][0], r["ins"][1]))
    # ---- structural gates (skeleton; hardened after first measurement) ----
    ga = census(A)[0]; gb = census(B)[0]
    checks = []
    def gate(gid, ok, msg):
        checks.append((gid, ok, msg))
        p("%s %s %s" % (gid, "PASS" if ok else "FAIL", msg))
    gate("G1", len(ga) > 0 and len(gb) > 0,
         "both globals referenced (A=%d B=%d)" % (len(ga), len(gb)))
    gate("G2", all(r["role"] in "WTR" for r in ga + gb), "all hits classified W/T/R")
    # RIVAL R1: 'A is a per-faction block field like ENERGY(220)/debt(224)'
    # -> would need block-fold accesses [base+k*20bc+off]; A is pure absolute.
    fold_a = [r for r in ga if r["ins"][1] and "[" in r["ins"][1]]
    gate("R1", len(ga) > 0 and not fold_a,
         "RIVAL 'A=per-faction block field' must FAIL: A bracket-refs=%d" % len(fold_a))
    npass = sum(1 for _, ok, _ in checks if ok)
    p("== M328 skeleton: %d/%d ==" % (npass, len(checks)))
    dig = hashlib.sha256("\n".join(det).encode()).hexdigest()[:16]
    p("digest %s" % dig)
    return 0 if npass == len(checks) else 1

if __name__ == "__main__":
    sys.exit(main())