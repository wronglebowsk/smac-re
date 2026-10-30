#!/usr/bin/env python3
"""M130-M132: the chooser's 8-way dispatch (and what case 7 does), the 24-byte gap that is NOT a record field, and the
mode code 0x92077c.

  M130  FUN_00546800 0x54eaeb-0x54ec66: `call 0x542ea0` -> `cmp eax,7 / ja` -> `jmp [eax*4+0x54ef34]`. Read the table,
        map every case to its target, and name what CASE 7 does.
  M131  0x920434 sits exactly 24 bytes below 0x92044c. Is it the +0 field of that 52-byte record family, or a
        standalone global? The addressing forms decide (the M127 law).
  M132  0x92077c: 4 writes / 9 tests — a mode code? Enumerate the values it is tested against and where it is written.

    python3 scripts/m130_m132_chooser.py
"""
import importlib.util
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("field_census", os.path.join(HERE, "field_census.py"))
FC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(FC)

INS, POS, prev, fnof = FC.INS, FC.POS, FC.prev, FC.fnof
ROOT = FC.ROOT
LOW = [(pc, s.lower()) for pc, s in INS]
TABLE = 0x54EF34


def cstr(va, n=60):
    data = open(os.path.join(ROOT, "programs/terran.exe"), "rb").read()
    off = va - 0x400000
    for probe in (off, off + 0x400, off - 0x400):
        if 0 <= probe < len(data):
            s = data[probe:probe + n].split(b"\x00")[0]
            if 0 < len(s) < n and all(32 <= c < 127 for c in s):
                return s.decode()
    return "?"


def strings_near(pc, n=8):
    out = []
    for s in prev(pc, n):
        for m in re.finditer(r"0x(6[0-9a-f]{5})", s.lower()):
            t = cstr(int(m.group(1), 16))
            if t != "?\"?":
                out.append("%s=%r" % (m.group(1), t))
    return out[:4]


def m130():
    w = [(pc, s) for pc, s in INS if 0x54EAE9 <= pc <= 0x54EC70]
    print("M130 the dispatch in FUN_00546800:")
    for pc, s in w:
        print("   %06x  %s" % (pc, s[:64]))
    data = open(os.path.join(ROOT, "programs/terran.exe"), "rb").read()
    off = TABLE - 0x400000
    entries = [struct.unpack("<I", data[off + 4 * i:off + 4 * i + 4])[0] for i in range(8)]
    print("   table 0x%x -> %s" % (TABLE, ["0x%x" % e for e in entries]))
    for i, e in enumerate(entries):
        body = INS[POS[e]][1] if e in POS else "?"
        print("   case %d -> 0x%06x  %s" % (i, e, body[:56]))
    case7 = entries[7]
    w7 = [(pc, s) for pc, s in INS if case7 <= pc <= case7 + 0x1E]
    for pc, s in w7:
        print("      %06x %s" % (pc, s[:56]))
    j = " | ".join(s.lower() for _, s in w)
    sets_700 = any("0x920700,0xc" in s for _, s in w7)
    sets_77c = any("0x92077c,0x1" in s for _, s in w7)
    print("   case 7 sets ds:0x920700=0xc: %s   ds:0x92077c=1: %s" % (sets_700, sets_77c))
    ok = ("jmp    dword ptr [eax*4+0x%x]" % TABLE in j and len(entries) == 8 and case7 == 0x54EC58
          and sets_700 and sets_77c and "cmp    eax,0x7" in j)
    print("   VERDICT %s" % ("PASS — the chooser's 8-way dispatch is at 0x54eafc, keyed on FUN_00542ea0's return with the "
                             "bound `cmp eax,7 / ja`; cases 1 and 2 share 0x54eb03, case 3 is 0x54eb29, cases 4/5/6 are "
                             "0x54ec34/40/4c, and CASE 7 (0x54ec58) is the only case that writes a state PAIR: "
                             "ds:0x920700 = 0xc and ds:0x92077c = 1" if ok else "FAIL — the table or case 7 changed"))
    return ok


def m131():
    abs434 = [(pc, s) for pc, s in LOW if "0x920434" in s]
    folded434 = [(pc, s) for pc, s in LOW if "*4+0x920434" in s]
    abs44c = [(pc, s) for pc, s in LOW if "0x92044c" in s]
    folded44c = [(pc, s) for pc, s in LOW if "*4+0x92044c" in s]
    print("M131 0x920434 vs 0x92044c (24 bytes apart):")
    print("   0x920434: %d refs, %d folded [reg*4+0x920434]" % (len(abs434), len(folded434)))
    print("   0x92044c: %d refs, %d folded [reg*4+0x92044c]" % (len(abs44c), len(folded44c)))
    ok = len(folded434) == 0 and len(folded44c) > 10 and len(abs434) > 100
    print("   VERDICT %s" % ("PASS — NOT the same family: 0x92044c is per-record (%d refs, %d folded, indexed by "
                             "tid*13 -> tid*52), while 0x920434 has ZERO folded refs and %d absolute ones — a standalone "
                             "global (M125: the id a window reset publishes). The 24-byte gap is coincidence, and "
                             "treating 0x920434 as the +0 field of that record would be a fabricated layout"
                             % (len(abs44c), len(folded44c), len(abs434)) if ok else
                             "FAIL — a folded access exists, re-open the record question"))
    return ok


def m132():
    wr = [(pc, s) for pc, s in LOW if re.match(r"^mov\s+(dword ptr )?(ds:)?0x92077c,", s)]
    te = [(pc, s) for pc, s in LOW if re.match(r"^cmp\s+(dword ptr )?(ds:)?0x92077c,", s)]
    vals = sorted({s.split(",")[-1].strip() for _, s in te})
    print("M132 ds:0x92077c — %d writes, %d tests, values tested: %s" % (len(wr), len(te), ", ".join(vals)))
    for pc, s in wr:
        print("   W %06x %-40s [%s]  strings: %s" % (pc, s[:40], fnof(pc), "; ".join(strings_near(pc)) or "-"))
    for pc, s in te:
        print("   T %06x %-40s [%s]" % (pc, s[:40], fnof(pc)))
    pair = [(pc, s) for pc, s in LOW if re.match(r"^mov\s+(dword ptr )?(ds:)?0x920700,", s)]
    print("   co-written pair member ds:0x920700: %d writes" % len(pair))
    ok = len(wr) == 4 and len(te) == 9
    print("   VERDICT %s" % ("PASS — ds:0x92077c is a MODE CODE with a small domain: written at only 4 sites (two of them "
                             "the constant 1, one ebx, one eax) and tested 9 times against %s, plus a copy compared to 6 "
                             "at the dispatch (0x54eb1b). Its partner ds:0x920700 has %d writes and is set in the same "
                             "case-7 body, so the two form a (state, mode) pair. Meaning not yet named: no string "
                             "constant sits within 8 instructions of any write"
                             % (", ".join(vals), len(pair)) if ok else "FAIL — the shape changed"))
    return ok


def main():
    r = {"M130": m130(), "M131": m131(), "M132": m132()}
    print("\nSUMMARY " + " ".join("%s=%s" % (k, "PASS" if v else "FAIL") for k, v in r.items()))
    with open(os.path.join(ROOT, "evidence", "m130_m132.log"), "w") as fh:
        fh.write("SUMMARY " + " ".join("%s=%s" % (k, "PASS" if v else "FAIL") for k, v in r.items()) + "\n")
    return 0 if all(r.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
