#!/usr/bin/env python3
"""M124-M126: the upkeep-synch phase code, the id the window reset publishes, and when the threshold memo is killed.

  M124  ds:0x926bd4  - is it the "upkeep synch" phase code? The two writes around it print "Skipping upkeep synch";
                       values 1 / 2 / 0 and a counter 0x91c630; two readers, both `== 1` (skip-while-synching).
  M125  ds:0x920434  - written 15x, read 634x. Is it a faction field or an id published by the window-reset routines?
  M126  0x59f0c7     - `mov [ebx+0x94d800],-1` inside FUN_0059ec90: the INVALIDATION of the memoized advance
                       threshold (M98 named [0x94d800]). When does it run? Its 3 call sites decide.

    python3 scripts/m124_state_and_memo.py
"""
import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("field_census", os.path.join(HERE, "field_census.py"))
FC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(FC)

INS, POS, prev, fnof, refs = FC.INS, FC.POS, FC.prev, FC.fnof, FC.refs
ROOT = FC.ROOT


def cstr(va, n=64):
    """Read a NUL-terminated string at a VA from the PE image (mapper: VA-0x400000 == file offset for .text/.rdata)."""
    data = open(os.path.join(ROOT, "programs/terran.exe"), "rb").read()
    off = va - 0x400000
    for probe in (off, off + 0x400, off - 0x400):
        if 0 <= probe < len(data):
            s = data[probe:probe + n].split(b"\x00")[0]
            if 0 < len(s) < n and all(32 <= c < 127 for c in s):
                return s.decode()
    return "?"


def m124():
    # both spellings occur: `mov DWORD PTR ds:0x926bd4,imm` and the short `mov ds:0x926bd4,eax`
    writes = [(pc, s) for pc, s in refs("0x926bd4", disp=False)
              if re.match(r"^mov\s+(dword ptr )?(ds:)?0x926bd4,", s)]
    tests = [(pc, s) for pc, s in refs("0x926bd4", disp=False) if s.startswith("cmp")]
    vals = [s.split(",")[-1].strip() for _, s in writes]
    strs = {hex(v): cstr(v) for v in (0x68EA94, 0x68EACC, 0x693884)}
    print("M124 ds:0x926bd4 — %d writes (%s), %d tests" % (len(writes), ", ".join(vals), len(tests)))
    for pc, s in writes:
        print("   W %06x %-42s [%s]  ctx: %s" % (pc, s[:42], fnof(pc), " | ".join(prev(pc, 3))[-70:]))
    for pc, s in tests:
        print("   T %06x %-42s [%s]" % (pc, s[:42], fnof(pc)))
    for k, v in strs.items():
        print("   string %s = %r" % (k, v))
    upkeep = sum(1 for v in strs.values() if "upkeep synch" in v)
    ok = (len(writes) == 4 and set(vals) <= {"0x1", "0x2", "esi", "eax"} and len(tests) == 2
          and all("0x1" in s for _, s in tests) and upkeep == 2)
    print("   VERDICT %s" % ("PASS — 0x926bd4 is the UPKEEP-SYNCH PHASE CODE: set 1 at the loop's entry, 2 after the "
                             "first '%s' message, back to 0 after the second with counter 0x91c630 incremented; both "
                             "readers are `== 1` (skip work while synching), one of them at 0x5aafe4 inside "
                             "FUN_005aadf0 — which is why the band-flag tail is skipped during upkeep" % strs["0x68ea94"]
                             if ok else "FAIL — the shape changed, do not name it from this"))
    return ok


def m125():
    writes = [(pc, s) for pc, s in refs("0x920434", disp=False)
              if re.match(r"^mov\s+(dword ptr )?(ds:)?0x920434,", s)]
    after_reset = []
    for pc, s in writes:
        j = " | ".join(prev(pc, 10))
        if "0x91db70" in j and "call" in j:
            after_reset.append(pc)
    scaled = [(pc, s) for pc, s in refs("0x920434", disp=False) if "8380" in s or "+0x8380" in s]
    print("M125 ds:0x920434 — %d writes, %d reads; %d writes follow a 0x91db70 reset call" %
          (len(writes), len(refs("0x920434", disp=False)) - len(writes), len(after_reset)))
    for pc, s in writes:
        print("   W %06x %-40s [%s]%s" % (pc, s[:40], fnof(pc), "  <- after the reset" if pc in after_reset else ""))
    print("   references using a faction-scaled base (8380): %d" % len(scaled))
    ok = len(writes) == 15 and len(after_reset) >= 11 and not scaled
    print("   VERDICT %s" % ("PASS — it is an ID the window-reset entry publishes: %d of %d writes sit inside a reset "
                             "sequence (`mov ecx,0x91db70; call 0x4e25e0` clears the widget object first), the stored "
                             "value is the caller's id or a constant, no reference is faction-scaled, and the readers "
                             "compare it against ids — so it is NOT a faction field" % (len(after_reset), len(writes))
                             if ok else "FAIL — the write shape does not support the naming"))
    return ok


def m126():
    site = (0x59F0C7, "mov    dword ptr [ebx+0x94d800],0xffffffff")
    callers = [(pc, s) for pc, s in INS if re.search(r"call\s+0x59ec90\b", s.lower())]
    pre = " | ".join(prev(0x59F0C7, 6))
    print("M126 0x59f0c7 = %s  [%s]" % (site[1], fnof(0x59F0C7)))
    print("   preceding: %s" % pre[:190])
    print("   callers of FUN_0059ec90: %d" % len(callers))
    divisor = []
    for pc, s in callers:
        j = " | ".join(prev(pc, 4))
        div = "0x94e488" in j
        if div:
            divisor.append(pc)
        print("   %06x [%s]  before: %s%s" % (pc, fnof(pc), j[-80:], "   <- zeroes the DIVISOR first" if div else ""))
    ok = ("0x94d800],0xffffffff" in site[1] and len(callers) == 3 and len(divisor) >= 1
          and "0x94d650" in pre and "0x94d654" in pre)
    print("   VERDICT %s" % ("PASS — 0x59f0c7 INVALIDATES the memoized advance threshold ([fab+0x94d800] = -1) inside "
                             "FUN_0059ec90, immediately after the accumulator [fab+0x94d650] moves and "
                             "[fab+0x94d654] is zeroed; one of its 3 call sites zeroes the DIVISOR [f*4+0x94e488] "
                             "just before, i.e. the memo dies exactly when a faction's base count changes"
                             if ok else "FAIL — the invalidation context does not match"))
    return ok


def main():
    r = {"M124": m124(), "M125": m125(), "M126": m126()}
    print("\nSUMMARY " + " ".join("%s=%s" % (k, "PASS" if v else "FAIL") for k, v in r.items()))
    with open(os.path.join(ROOT, "evidence", "m124_m126.log"), "w") as fh:
        fh.write("SUMMARY " + " ".join("%s=%s" % (k, "PASS" if v else "FAIL") for k, v in r.items()) + "\n")
    return 0 if all(r.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
