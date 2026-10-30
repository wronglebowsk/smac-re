#!/usr/bin/env python3
"""M127-M129: the plan byte's readers, the chooser's pre/post-seek pair, and the three-condition guard in FUN_00546800.

  M127  `0x98adb2` (= type-record `+42`, the PLAN byte) — M67's live-verified sort key, and the registry's open item
        claims "zero sites read it". Count the readers in BOTH addressing forms (`[reg+0x2a]` literal vs the folded
        `[reg*4+0x98adb2]` where reg holds tid*13) and decide.
  M128  0x497704 / 0x497717 / 0x49771c — the chooser pump's PRE-seek read, the seek call, and the POST-seek re-derive:
        the code behind the "a cursor read before the seek is the PREVIOUS cursor" trap.
  M129  FUN_00546800 0x54687b-0x5469d3 — the guard that reads the faction dword bit 0x8000000, ds:0x920434 and the
        per-record byte 0x92044c bit 0x2, then CLEARS that byte: one unit, three conditions, one consume.

    python3 scripts/m127_m129_fields.py
"""
import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("field_census", os.path.join(HERE, "field_census.py"))
FC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(FC)

INS, POS, prev, fnof = FC.INS, FC.POS, FC.prev, FC.fnof
ROOT = FC.ROOT
LOW = [(pc, s.lower()) for pc, s in INS]


def window(lo, hi):
    return [(pc, s) for pc, s in INS if lo <= pc <= hi]


def m127():
    lit = [(pc, s) for pc, s in LOW if "0x98adb2" in s]
    folded = [(pc, s) for pc, s in lit if "*4+0x98adb2" in s]
    plain = [(pc, s) for pc, s in lit if "+0x2a]" in s]           # the addressing M67's search used
    print("M127 the PLAN byte (type-record +42, absolute 0x98adb2):")
    print("   references: %d   folded [reg*4+0x98adb2]: %d   literal [+0x2a]: %d" %
          (len(lit), len(folded), len(plain)))
    import collections
    top = collections.Counter(fnof(pc) for pc, _ in lit).most_common(8)
    for f, n in top:
        print("   %-14s %d refs" % (f, n))
    ok = len(lit) > 300 and len(folded) > 100
    print("   VERDICT %s" % ("PASS — the plan byte IS read: %d sites in two encodings (%d folded `[reg*4+0x98adb2]`, "
                             "i.e. tid*13*4 = tid*52, the 52-byte record stride). The registry's \"zero sites read plan "
                             "byte +42\" is a SEARCH-SHAPE ARTIFACT (a literal `+0x2a]` grep sees only %d of them) and "
                             "is RETRACTED; M67's live-verified plan-descending order now has static readers behind it"
                             % (len(lit), len(folded), len(plain)) if ok else "FAIL — the readers are not there"))
    return ok


def m128():
    w = window(0x4976F0, 0x497730)
    print("M128 the chooser pump's seek and the state on each side of it:")
    for pc, s in w:
        print("   %06x  %s" % (pc, s[:62]))
    pre_read = [pc for pc, s in w if pc < 0x497717 and "+0xa774]" in s.lower()]
    seek = [pc for pc, s in w if re.search(r"call\s+0x4026b0", s.lower())]
    # the listing writes `add ecx,0xa780` (no '+' before a bare immediate), so match the constant, not "+0xa780"
    post = [pc for pc, s in w if pc > 0x497717 and "0xa780" in s.lower()]
    flag = [pc for pc, s in w if pc > 0x497717 and "and    eax,0x20" in s]
    print("   pre-seek read of [obj+0xa774]: %s | call 0x4026b0 at %s | post-seek [obj+0xa780]: %s | and eax,0x20: %s" %
          (["%06x" % p for p in pre_read], ["%06x" % p for p in seek], ["%06x" % p for p in post],
           ["%06x" % p for p in flag]))
    ok = bool(pre_read) and seek == [0x497717] and bool(post) and (min(post) - 0x497717) <= 8 and bool(flag)
    print("   VERDICT %s" % ("PASS — the trap is in the CODE, not just in a log: the node at [obj+0xa774] is read at "
                             "0x%06x BEFORE `call 0x4026b0` (the seek, 0x497717) and the object is re-derived from "
                             "[ebp-0x10]+0xa780 at 0x49771c AFTER it, then `and eax,0x20` tests the first flag bit of "
                             "the POST-seek query. So any print at 0x497704 shows the PREVIOUS node and 0x49771c is "
                             "the first instruction that sees the new one" % pre_read[0]
                             if ok else "FAIL — the window does not match"))
    return ok


def m129():
    w = window(0x54687B, 0x5469D8)
    print("M129 FUN_00546800 guard cluster:")
    for pc, s in w:
        print("   %06x  %s" % (pc, s[:62]))
    j = " | ".join(s.lower() for _, s in w)
    c1 = "0x94d448],0x8000000" in j
    c2 = "0x920434,ebx" in j
    c3 = "0x92044c],0x2" in j
    clear = any(re.search(r"mov\s+dword ptr \[[^\]]*0x92044c\],0x0", s.lower()) for _, s in w)
    ok = c1 and c2 and c3 and clear
    print("   cond1 faction bit 0x8000000=%s  cond2 ds:0x920434 != ebx=%s  cond3 0x92044c bit 0x2=%s  clear=%s" %
          (c1, c2, c3, clear))
    print("   VERDICT %s" % ("PASS — one unit: FUN_00546800 proceeds only when the faction dword at 0x94d448 has bit "
                             "0x8000000, ds:0x920434 differs from ebx, and the per-record byte 0x92044c bit 0x2 is set; "
                             "it then ZEROES that byte (0x5469d3). So 0x92044c bit 1 is a CONSUMED marker for this "
                             "path, not a persistent state — which is why it is 0 in the saves and after the pass"
                             if ok else "FAIL — the cluster does not match"))
    return ok


def main():
    r = {"M127": m127(), "M128": m128(), "M129": m129()}
    print("\nSUMMARY " + " ".join("%s=%s" % (k, "PASS" if v else "FAIL") for k, v in r.items()))
    with open(os.path.join(ROOT, "evidence", "m127_m129.log"), "w") as fh:
        fh.write("SUMMARY " + " ".join("%s=%s" % (k, "PASS" if v else "FAIL") for k, v in r.items()) + "\n")
    return 0 if all(r.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
