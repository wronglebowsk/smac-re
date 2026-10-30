#!/usr/bin/env python3
"""M169-M171: the table the rank is computed from, the aggregator that reads it, and the bit-decoder that fills a struct.

  M169  0x926a7c — a 7-entry dword array read by only two functions. What the second reader does with it.
  M170  FUN_00531df0 — 6459 B / 1884 insns / 17 callers: the per-faction AGGREGATOR around that read.
  M171  FUN_004dc100 (647 B / 189 insns / 2 callers) — writes the 20-byte struct's header AND payload; read the writes.

    python3 scripts/m169_m171_aggregate.py
"""
import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("field_census", os.path.join(HERE, "field_census.py"))
FC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(FC)

INS, fnof, IDX = FC.INS, FC.fnof, FC.IDX
ROOT = FC.ROOT
LOW = [(pc, s.lower()) for pc, s in INS]
INDEX = {n: (a, z) for a, n, z in IDX}
R = {}


def ok(mid, cond, text):
    R[mid] = cond
    print("%s  %s — %s" % (mid, "PASS" if cond else "FAIL", text))


def body(a, size, lo=0, hi=0):
    return [(pc, s) for pc, s in INS if a <= pc < a + size]


def m169():
    refs = [(pc, s) for pc, s in LOW if "0x926a7c" in s]
    win = [(pc, s) for pc, s in INS if 0x53213D <= pc <= 0x532190]
    j = " | ".join(s.lower() for _, s in win)
    stride = "0x20bc" in j
    acc = "0x9204c4" in j and "0x9204ac" in j
    idx4 = "add    eax,edi" in j and "mov    edi,0x4" in j
    print("M169 0x926a7c: %d refs; loop window has stride 0x20bc=%s accumulators=%s dword index step=%s" %
          (len(refs), stride, acc, idx4))
    for pc, s in win:
        print("   %06x  %s" % (pc, s[:60]))
    ok("M169", len(refs) == 2 and stride and acc and idx4,
       "0x926a7c is a PER-FACTION dword array (7 entries per the rank scan): its second reader, in FUN_00531df0, walks "
       "the faction blocks at stride **0x20bc (8,380)** while advancing the table index by 4, and does "
       "`ds:0x9204ac++` / `ds:0x9204c4 += [eax+0x926a7c]` — so the table is TOTALLED (count + sum), not flagged")


def m170():
    a, size = INDEX["FUN_00531df0"]
    b = body(a, size)
    j = " | ".join(s.lower() for _, s in b)
    callers = [pc for pc, s in INS if re.search(r"call\s+0x531df0\b", s.lower())]
    facts = {
        "rank gate vs 5": "0x94d434],0x5" in j,
        "sum accumulator": "0x9204c4" in j,
        "count accumulator": "0x9204ac" in j,
        "stride 0x20bc": "0x20bc" in j,
        "faction bit mask (shl 1)": "shl    edi,cl" in j,
    }
    print("M170 FUN_00531df0: %d B, %d insns, %d call sites; %s" % (size, len(b), len(callers), facts))
    ok("M170", size == 6459 and len(callers) >= 10 and all(facts.values()),
       "FUN_00531df0 (6459 B, %d insns, %d call sites) is the per-faction AGGREGATOR: it walks the 8,380-byte faction "
       "blocks, builds a 1<<faction mask (`shl edi,cl`), gates on `cmp [ebx+0x94d434],0x5` — the RANK of M163/M166 used "
       "as a threshold — and accumulates into ds:0x9204ac (count) and ds:0x9204c4 (sum of the 0x926a7c table). So the rank "
       "is consumed here as `rank < 5`, which is what its 92 comparisons looked like"
       % (len(b), len(callers)))


def m171():
    a, size = INDEX["FUN_004dc100"]
    b = body(a, size)
    j = [s.lower() for _, s in b]
    J = " | ".join(j)
    payload = [d for d in ("0x94d810", "0x94d814", "0x94d818", "0x94d81c")
               if any(re.search(r"\+%s\],edx" % d, s) for s in j)]
    bits = all(("and    ecx,%s" % m) in J for m in ("0x1", "0x2", "0x4", "0x8"))
    setne = J.count("setne  dl") >= 4
    header = all(("0x94d80c],%s" % v) in J for v in ("0x1", "0xffffffff", "0x0"))
    flag = "0x94d430],0x800000" in J
    print("M171 FUN_004dc100: %d B, %d insns; payload written from edx: %s; bit masks 1/2/4/8=%s setne x%d header "
          "tristate=%s rank-flag OR=%s" % (size, len(b), payload, bits, J.count("setne  dl"), header, flag))
    for pc, s in [(pc, s) for pc, s in b if 0x4DC2A0 <= pc <= 0x4DC340]:
        print("   %06x  %s" % (pc, s[:58]))
    ok("M171", len(payload) == 4 and bits and setne and header and flag,
       "FUN_004dc100 is a BIT-DECODER, not a copier: it reads one byte in AL and writes the struct as FOUR BOOLEAN "
       "dwords — `[esi+0x94d810/14/18/1c] = setne(al & 1/2/4/8)` — then sets the header `[esi+0x94d80c]` to the "
       "TRISTATE 1 / -1 / 0 from the al&0x10 and al&0x20 tests, and finally `or [esi+0x94d430],0x800000` when al&0x40. "
       "So the 20-byte 'struct' is a decoded BITFIELD: 4 booleans, a tristate and a flag side-effect")


def main():
    m169(); m170(); m171()
    print("\nSUMMARY " + " ".join("%s=%s" % (k, "PASS" if v else "FAIL") for k, v in R.items()))
    with open(os.path.join(ROOT, "evidence", "m169_m171.log"), "w") as fh:
        fh.write("SUMMARY " + " ".join("%s=%s" % (k, "PASS" if v else "FAIL") for k, v in R.items()) + "\n")
    return 0 if all(R.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
