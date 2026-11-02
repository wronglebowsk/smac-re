#!/usr/bin/env python3
"""M262-M264: three static census questions on terran.exe through ONE instrument
(the whole-image instruction corpus + the image-derived vtable map + containment via
ghidra_out/index.csv — imported from scripts/m235_m237_records.py, as in M259-M261).

  M262  who writes the view-table entries 1..7 (DAT_007cdec8..0x7cdee8) — no store in the
        image names them (M260); find every reference shape and any pointer derivation
  M263  does the LOAD path re-derive the per-faction terrain band (+16..+43) or trust the
        file — the codec's map leg vs the two refresh loops' reachability from the loader
  M264  FUN_005be090: which of the 13 image-wide `call [reg+4]` sites dispatch to it and
        with what arg sizes; which of the 3 loaders of ds:0x9965b8 fills its records;
        and who calls FUN_005f3f5b (6102 B)

    python3 scripts/m262_m264_census.py    # -> SUMMARY M262/M263/M264: n/N gates PASS
Static only: no box, no /proc, no gdb.
"""
import os, re, sys, collections, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
_spec = importlib.util.spec_from_file_location("m235", os.path.join(HERE, "m235_m237_records.py"))
M = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(M)
NM, fnof, IDXMAP, IMG = M.NM, M.fnof, M.IDXMAP, M.IMG
dw, body, VT = M.dw, M.body, M.VT
PC2T = dict(NM)
def at(pc): return PC2T.get(pc, "<missing>")
def texts(fn): return [s for _, s in body(fn)]
def has(fn, *pats):
    b = body(fn); return all(any(re.match(p, s) for _, s in b) for p in pats)
def seq(fn, pat): return [hex(pc) for pc, s in body(fn) if re.match(pat, s)]
GATES = []
def G(desc, cond, numbers): GATES.append((desc, bool(cond), numbers))

def m262():
    G("M262 G1 (TBD) every reference to the view-table band 0x7cdecc..0x7cdee8, classified", False, "TBD")
    G("M262 G2 (TBD) the writer of entries 1..7", False, "TBD")
    G("M262 G3 (TBD) what the entries are for", False, "TBD")

def m263():
    G("M263 G4 (TBD) the codec's map leg: what it reads/writes per terrain record", False, "TBD")
    G("M263 G5 (TBD) reachability of the two band-refresh loops from the load path", False, "TBD")

def m264():
    G("M264 G6 (TBD) the 13 `call [reg+4]` sites: which dispatch to FUN_005be090", False, "TBD")
    G("M264 G7 (TBD) which loader of ds:0x9965b8 fills the records", False, "TBD")
    G("M264 G8 (TBD) who calls FUN_005f3f5b", False, "TBD")

def main():
    print("# SMAC M262-M264 | terran.exe static image %d B, corpus %d insns, %d indexed functions" % (len(IMG), len(NM), len(IDXMAP)))
    m262(); m263(); m264()
    npass = sum(1 for d, ok, n in GATES if ok)
    for d, ok, n in GATES:
        print(("PASS " if ok else "FAIL ") + d)
        print("    " + str(n))
    print("SUMMARY M262/M263/M264: %d/%d gates PASS" % (npass, len(GATES)))
    return 0 if npass == len(GATES) else 1

if __name__ == "__main__":
    sys.exit(main())
