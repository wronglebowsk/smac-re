#!/usr/bin/env python3
"""M370 mutation harness - every VERIFIED row of scripts/m370_pref_writers.py names a
mutant here.  A mutant is KILLED when its named gate turns red in a real run.

  TEXT  rewrites ONE instruction line of the objdump cache (M370_PATCH): the
        DISASSEMBLY is mutated and the instrument must notice.
  ALGO  selects a mutated law of the classifier/tracer (M370_ALGO): the instrument
        itself is wrong and the gates must redden.
  INPUT drops the input entirely (M370_TEXT=/dev/null): the precondition gate must
        fire and the run must ABORT rather than print a meaningless PASS.

Gate coverage is MEASURED from the tool's own gate rows.  A NO-OP mutant (target
text absent/already equal) is reported, never counted as killed.

    python3 scripts/m370_mutate.py
"""
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "scripts/m370_pref_writers.py")
GATE = re.compile(r"^(G\w+)\s+(ok|FAIL)\b", re.M)

# (name, addr, old, new, gate, claim)
TEXT_MUT = [
    ("MU1", 0x58E8C6, "mov    ds:0x92bde8,eax", "mov    ds:0x92bdf0,eax", "G2a",
     "the loader's Difficulty store is the only one to 0x92bde8's cell; moved to the pad dword, that cell loses its only INI writer"),
    ("MU2", 0x58EC20, "mov    ds:0x92bf00,eax", "mov    eax,ds:0x92bf00", "G6b",
     "the loader STORES More Preferences (a load would leave the cell unwritten)"),
    ("MU3", 0x58E8A1, "push   0x692718", "push   0x6927fc", "G5a",
     "the read-side key VA is a DIFFERENT copy from the write-side one (same text)"),
    ("MU4", 0x58F159, "push   0x6927fc", "push   0x692808", "G5a",
     "the writeback pairs the Difficulty cell with the key `Difficulty`, not `Map Type`"),
    ("MU5", 0x58E9CD, "push   0x69273c", "push   0x692724", "G4a",
     "the loader reads 11 DISTINCT keys; a duplicated one breaks the injection"),
    ("MU6", 0x492464, "mov    ds:0x92befc,eax", "mov    ds:0x92befd,eax", "G2a",
     "the APPLY store targets the named cell itself, not a byte inside it"),
    ("MU7", 0x57C7B0, "mov    ds:0x92bde8,eax", "mov    ds:0x92bdf0,eax", "G7a",
     "0x92bde8 has TWO stores (the rival 'one store' dies on the count)"),
    ("MU8", 0x58E98E, "mov    ds:0x92bdf8,eax", "mov    ds:0x92bdf4,eax", "G1a",
     "the text census and the byte-encoded census are the same instruction set"),
    ("MU9", 0x4DC8B7, "and    ecx,0x1800000", "ret", "G3a",
     "the Semaphore store at 0x4dc8bd is reached by fall-through (a ret makes it dead)"),
    ("MU10", 0x48AEA9, "cmp    eax,0x92bdfc", "cmp    eax,ds:0x92bdfc", "G2c",
     "0x92bdfc is only ever an immediate bound, never a memory operand"),
    ("MU11", 0x579BC6, "cmp    edi,0x92bde8", "mov    ds:0x92bde8,edi", "G1b",
     "every use of the base as an immediate outside a ds: operand is a cmp"),
    ("MU12", 0x5109F8, "mov    ds:0x92befc,eax", "nop", "G3b",
     "all four 0x5108e0-gap stores are resolved by the pad-delimited sub-function scan"),
    ("MU14", 0x57C914, "mov    ds:0x92bf14,eax", "mov    ds:0x92bf14,es", "G6a",
     "every non-loader store's source is classified (a segment register is not)"),
    ("MU15", 0x58E922, "mov    ds:0x92bdf4,eax", "mov    BYTE PTR ds:0x92bdf4,al", "G2b",
     "the block's cells are written as full dwords (a byte store is a different field)"),
    ("MU16", 0x58EFC4, "mov    esi,0x92bf18", "mov    esi,0x92bf14", "G8a",
     "the loader's sweep starts at 0x92bf18, past the span end"),
    ("MU17", 0x58EC20, "mov    ds:0x92bf00,eax", "mov    eax,ds:0x92bf00", "G2d",
     "the same store->load mutation moves the census off 85/43/39/3 (the literals are gated)"),
    ("MU18", 0x57C914, "mov    ds:0x92bf14,eax", "mov    ds:0x92bf14,es", "G6c",
     "the same unclassifiable source moves the family distribution off its pin"),
]
# (name, algo value, gate, claim)
ALGO_MUT = [
    ("MA1", "1", "G4b", "the read-side pairing is BACKWARD; forward is not injective"),
    ("MA2", "2", "G2a", "`mov mem,reg` is a STORE (the store/load split)"),
    ("MA3", "3", "G1a", "the byte scan reads the disp32 little-endian"),
    ("MA4", "4", "G1a", "a rel32 operand is not an address reference"),
    ("MA5", "5", "G4c", "the pairing uses the CALL SHAPE, not the nearest string push"),
    ("MA6", "6", "G9a", "every site a mutant patches is exercised by the census"),
]


def run(env_extra):
    env = dict(os.environ)
    env.pop("M370_PATCH", None)
    env.pop("M370_ALGO", None)
    env.pop("M370_TEXT", None)
    env.update(env_extra)
    p = subprocess.run([sys.executable, "-u", TOOL], capture_output=True, text=True, env=env)
    return p.returncode, p.stdout + p.stderr


def gates(txt):
    return {m.group(1): m.group(2) for m in GATE.finditer(txt)}


def main():
    out, killed, noop = [], [], []
    rc, txt = run({})
    base = gates(txt)
    out.append("base run: rc=%d gates=%d %s" % (rc, len(base),
                                                 "PASS" if rc == 0 else "FAIL"))
    if rc != 0:
        out.append("BASE IS RED - nothing to mutate against")
        print("\n".join(out))
        return 1
    allg = set(base)

    # TEXT mutants
    src = open(TOOL).read()
    for name, addr, old, new, gate, claim in TEXT_MUT:
        rc, txt = run({"M370_PATCH": "0x%x|%s" % (addr, new)})
        g = gates(txt)
        verb = "red" if g.get(gate) == "FAIL" else ("absent" if gate not in g else "green")
        ok = verb == "red"
        (killed if ok else noop).append((name, gate, ok, claim, "TEXT-" + verb))
        out.append("  %-5s TEXT %-5s %-4s %-8s %s" % (name, hex(addr), gate, verb,
                                                      " ".join(claim.split())[:84]))

    # ALGO mutants
    for name, val, gate, claim in ALGO_MUT:
        rc, txt = run({"M370_ALGO": val})
        g = gates(txt)
        verb = "red" if g.get(gate) == "FAIL" else ("absent" if gate not in g else "green")
        ok = verb == "red"
        (killed if ok else noop).append((name, gate, ok, claim, "ALGO-" + verb))
        out.append("  %-5s ALGO %-5s %-4s %-8s %s" % (name, val, gate, verb,
                                                      " ".join(claim.split())[:84]))

    # INPUT mutant: the precondition gate must fire and the run must abort
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write("")
        empty = f.name
    rc, txt = run({"M370_TEXT": empty})
    os.unlink(empty)
    ok = rc != 0 and gates(txt).get("G0a") == "FAIL" and "ABORT" in txt
    (killed if ok else noop).append(("MG0", "G0a", ok, "an empty .text cache aborts before any census",
                                     "INPUT-" + ("red" if ok else "green")))
    out.append("  %-5s INPUT %-29s %s" % ("MG0", "empty cache", "ok" if ok else "FAIL"))

    # NO-OP control: a patch that changes nothing must be refused, not counted
    rc, txt = run({"M370_PATCH": "0x58e8c6|mov    ds:0x92bde8,eax"})
    noop_ok = rc == 3 and "already equal" in txt
    (killed if noop_ok else noop).append(("MU0", "-", noop_ok, "NO-OP control: identical text is refused",
                                          "NOOP-" + ("detected" if noop_ok else "missed")))
    out.append("  %-5s NOOP  %-29s %s" % ("MU0", "identical patch", "detected" if noop_ok else "MISSED"))

    seen = set(g for _, g, _, _, _ in killed)
    missing = sorted(g for g in allg if g not in seen)
    nk = sum(1 for _, _, ok, _, _ in killed if ok)
    out.append("")
    out.append("KILLED %d/%d   NO-OP %d" % (nk, len(killed), len(noop)))
    for n, g, _, claim, kind in noop:
        out.append("  noop %s (%s) gate %s: %s" % (n, kind, g, " ".join(claim.split())[:70]))
    out.append("gate coverage: %d/%d gates have a mutant whose run reached it; unnamed: %s"
               % (len(allg) - len(missing), len(allg), " ".join(missing) or "-"))
    ok = nk == len(killed) and not noop and not missing
    out.append("%s M370-MUT: %d/%d killed, NO-OP %d, coverage %d/%d"
               % ("PASS" if ok else "FAIL", nk, len(killed), len(noop),
                  len(allg) - len(missing), len(allg)))
    print("\n".join(out))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
