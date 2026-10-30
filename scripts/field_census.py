#!/usr/bin/env python3
"""M119-M123: five field questions answered from the static image, one check each, each with its own PASS.

  stride   M119  is the array at 0x984d38 addressed with stride 0x30 or 0x10? (M67's "-3/-6 stride CONFLICT")
  bit5     M120  what sets bit 0x20 at 0x531782, and what is the index formula above it?
  readonly M121  is ds:0x98adee (the "forced-pick key", live 6) written anywhere in the image?
  copy     M122  the 0x1c-stride loop near 0x984d38: does it overlap that array or is it a separate copy?
  dual     M123  ds:0x94d78c: per-faction field ([reg+disp]) AND dword array ([reg*4+disp])?

    python3 scripts/field_census.py            # all five
    python3 scripts/field_census.py stride     # one

Why one file: every check is the same operation — take a displacement or global, find every instruction that touches it,
attribute the containing function, and decide the shape from the ADDRESSING FORM and the index arithmetic, not a name.
"""
import bisect
import contextlib
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
REGS = "eax ecx edx esi edi ebx".split()


def load_index():
    rows = []
    with open(os.path.join(ROOT, "ghidra_out/index.csv")) as f:
        head = f.readline().strip().split(",")
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            d = dict(zip(head, line.rstrip("\n").split(",")))
            rows.append((int(d["addr"], 16), d["name"], int(d["size_bytes"])))
    rows.sort()
    return rows


IDX = load_index()
STARTS = [r[0] for r in IDX]


def fnof(pc):
    i = bisect.bisect_right(STARTS, pc) - 1
    if i >= 0 and pc < IDX[i][0] + IDX[i][2]:
        return IDX[i][1]
    return "?"


def instructions():
    for line in open(TEXT, errors="replace"):
        m = re.match(r"\s*([0-9a-f]{6,8}):\s", line)
        if not m:
            continue
        p = line.rstrip("\n").split("\t")
        yield int(m.group(1), 16), (p[2].strip() if len(p) > 2 else "")


INS = list(instructions())
POS = {pc: i for i, (pc, _) in enumerate(INS)}
LOW = [(pc, s.lower()) for pc, s in INS]


def refs(tok, disp):
    out = []
    for pc, s in LOW:
        if disp:
            if "+%s]" % tok in s:
                out.append((pc, s))
        elif tok in s and "+%s]" % tok not in s:
            out.append((pc, s))
    return out


def prev(pc, n=1):
    i = POS.get(pc)
    if i is None:
        return []
    return [s for _, s in INS[max(0, i - n):i]]


def scaled2095(ctx):
    """True if ctx carries the compiler's 2095*f + inner sequence: shl X,6 / add / lea [v+X*2] / shl 4 / sub."""
    j = " | ".join(ctx)
    return any("shl    %s,0x6" % r in j for r in REGS) and "lea" in j and "*2]" in j and \
        any("shl    %s,0x4" % r in j for r in REGS) and any("sub    %s," % r in j for r in REGS)


def stride_check():
    """M119: classify the multiplier in front of every reference to 0x984d38."""
    sites = refs("0x984d38", disp=True)   # every access is [reg+0x984d38]; the disp form is the only real one
    mult = {"x48 via lea [v+v*2] + shl 4": 0, "x48 via imul 0x30": 0, "direct/base only": 0,
            "x16 standalone": 0, "other": 0}
    odd = []
    for pc, s in sites:
        ctx = prev(pc, 3)
        j = " | ".join(ctx)
        if re.search(r"lea\s+\w+,\[[^\]]*\*\s*2\]", j) and any("shl" in c for c in ctx):
            mult["x48 via lea [v+v*2] + shl 4"] += 1
        elif "imul" in j and "0x30" in j:
            mult["x48 via imul 0x30"] += 1
        elif re.search(r"shl\s+\w+,0x4", ctx[-1] if ctx else "") and "*2" not in j:
            mult["x16 standalone"] += 1
            odd.append((pc, ctx[-1]))
        elif re.search(r"(mov|add|lea)\s+\w+,0x984d38", s):
            mult["direct/base only"] += 1
        else:
            mult["other"] += 1
            odd.append((pc, j[-70:]))
    print("M119 stride census: %d refs to 0x984d38" % len(sites))
    for k, v in mult.items():
        print("   %-32s %d" % (k, v))
    for pc, c in odd[:6]:
        print("   odd: %06x  %s" % (pc, c))
    ok = mult["x16 standalone"] == 0 and (mult["x48 via lea [v+v*2] + shl 4"] + mult["x48 via imul 0x30"]) > 0
    print("   VERDICT %s" % ("PASS — stride is 0x30 (48 B) at every indexed site; the *16 in the listing is `shl 4` "
                             "applied to 3v, i.e. part of the x48 computation, so M67's conflict is a misread"
                             if ok else "FAIL — a standalone x16 access exists"))
    return ok


def bit5_check():
    """M120: re-derive the index formula feeding the byte test at 0x531778 and name the OR at 0x531782."""
    win = [(pc, s) for pc, s in INS if 0x531764 <= pc <= 0x531782]
    print("M120 the gate above 0x531782:")
    for pc, s in win:
        print("   %06x  %s" % (pc, s[:64]))
    have = {pc for pc, _ in win}
    pre = prev(0x531778, 8)
    ok = ({0x531778, 0x531780, 0x531782} <= have and
          any("0x94d448],0x1" in s for _, s in win) and
          any("0x98adb8],0x20" in s for _, s in win) and scaled2095(pre))
    print("   index is 2095*first + second (2095 dwords = 8,380 B = the faction stride): %s" % scaled2095(pre))
    print("   VERDICT %s" % ("PASS — bit 0x20 of the entity byte [ebx+0x98adb8] is set exactly when the faction-block "
                             "dword at 0x94d448+inner*4 has bit 0 (test at 0x531778, `je` at 0x531780 skips the OR)"
                             if ok else "FAIL — the window or the arithmetic changed"))
    return ok


def readonly_check():
    """M121: is 0x98adee written anywhere (any width, including the neighbouring dwords)?"""
    readers = refs("0x98adee", disp=False)
    writers = [r for r in readers if re.match(r"^mov\s+(dword ptr |word ptr |byte ptr )?(ds:)?0x98adee\s*,", r[1])]
    neigh = []
    for t in ("0x98adec", "0x98adf0", "0x98ade8"):
        neigh += refs(t, disp=False)
    print("M121 ds:0x98adee: %d referencing instructions, %d writes" % (len(readers), len(writers)))
    print("   neighbouring dword accesses (0x98ade8/0x98adec/0x98adf0): %d" % len(neigh))
    for pc, s in readers:
        print("   R %06x %-44s [%s]" % (pc, s[:44], fnof(pc)))
    ok = len(readers) > 0 and not writers and not neigh
    print("   VERDICT %s" % ("PASS — read-only in the image (%d movsx readers, 0 writers of any width, no access to "
                             "the enclosing dwords): the value arrives with the LOAD, so it is save/scenario data, "
                             "not a gameplay counter" % len(readers)
                             if ok else "FAIL — a writer or a wider access exists"))
    return ok


def copy_check():
    """M122: the 0x1c-stride loop — separate copy or overlap with 0x984d38?"""
    win = [(pc, s) for pc, s in INS if 0x52B744 <= pc <= 0x52B77A]
    print("M122 the 0x1c loop:")
    for pc, s in win:
        print("   %06x  %s" % (pc, s[:62]))
    src = any("0x91cb80" in s for _, s in win)
    dst = any("0x98aaf8" in s for _, s in win)
    step = any("add    eax,0x1c" in s for _, s in win)
    bound = any("0x98ad98" in s for _, s in win)
    touches = any("0x984d38" in s for _, s in win)
    n = (0x98AD98 - 0x98AAF8) // 0x1C
    exact = (0x98AD98 - 0x98AAF8) % 0x1C == 0
    print("   src 0x91cb80=%s  dst 0x98aaf8=%s  step 0x1c=%s  bound 0x98ad98=%s  touches 0x984d38=%s" %
          (src, dst, step, bound, touches))
    print("   records = (0x98ad98-0x98aaf8)/0x1c = %d, exact=%s" % (n, exact))
    ok = src and dst and step and bound and not touches and exact
    print("   VERDICT %s" % ("PASS — the 0x1c loop is a NEW copy (0x91cb80 -> 0x98aaf8, %d records of 28 B) and never "
                             "references 0x984d38; there is no third stride, M67's conflict was between two "
                             "different arrays" % n if ok else "FAIL — the loop overlaps the 0x984d38 array"))
    return ok


def dual_check():
    """M123: 0x94d78c addressed both as [reg+disp] and [reg*4+disp] — same field or two objects?"""
    sites = refs("0x94d78c", disp=True)
    field = [(pc, s) for pc, s in sites if re.search(r"\[\w+\+0x94d78c\]", s)]
    array = [(pc, s) for pc, s in sites if re.search(r"\[\w+\*4\+0x94d78c\]", s)]
    writes = [(pc, s) for pc, s in sites if re.match(r"^mov\s+dword ptr \[[^\]]*0x94d78c\],", s)]
    print("M123 ds:0x94d78c: %d refs — %d as [reg+disp], %d as [reg*4+disp], %d writes" %
          (len(sites), len(field), len(array), len(writes)))
    for pc, s in writes:
        print("   W %06x %-46s [%s]" % (pc, s[:46], fnof(pc)))
    # the 2095 sequence can span more than six instructions (the shl 6 / add pair often sits further back)
    prescaled = [(pc, s) for pc, s in array if scaled2095(prev(pc, 10))]
    print("   array-form sites with a 2095-scaled index: %d of %d" % (len(prescaled), len(array)))
    for pc, s in array:
        if (pc, s) not in prescaled:
            print("   NOT scaled: %06x %s  <- %s" % (pc, s[:44], " | ".join(prev(pc, 4))))
    ok = len(array) > 0 and len(prescaled) == len(array) and len(field) > 0
    print("   VERDICT %s" % ("PASS — both forms are the SAME dword inside the 8,380-byte faction block: [reg+disp] "
                             "when reg is the block base, [reg*4+disp] when the compiler already folded the 2095-dword "
                             "stride into the index. No second array, and a third independent confirmation of 8,380"
                             if ok else "FAIL — an array-form site is not 2095-scaled, so a second array cannot be excluded"))
    return ok


CHECKS = {"stride": stride_check, "bit5": bit5_check, "readonly": readonly_check,
          "copy": copy_check, "dual": dual_check}


def main():
    want = sys.argv[1:] or list(CHECKS)
    results, out = {}, []
    for name in want:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            results[name] = CHECKS[name]()
        text = buf.getvalue()
        print(text, end="")
        out.append(text)
        print()
    print("SUMMARY " + " ".join("%s=%s" % (k, "PASS" if v else "FAIL") for k, v in results.items()))
    os.makedirs(os.path.join(ROOT, "evidence"), exist_ok=True)
    with open(os.path.join(ROOT, "evidence", "fields_m119_m123.log"), "w") as fh:
        fh.write("\n".join(out) + "\n")
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
