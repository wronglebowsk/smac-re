#!/usr/bin/env python3
"""M382 - WHO ASKS THE 0xc00 CLUSTER: every reader of the faction-pair dword's
0x400/0x800 bits, classified from the instruction stream (zero box time).

The shortlist (NEXT_PROMPT pick (a)) named five field-inline tests
(0x4ec9c3 0x523a7c 0x563165 0x56a8a2 0x5859ae) and two "register readers"
(0x5468c7 / 0x5552ff).  This instrument measures the population instead of
taking the list: it censuses every site that asks the pair dword
`[owner*0x82f+other]*4 + 0x94d448` about 0x400 or 0x800, both as a field-inline
`test [mem],imm` and as a loaded-register `test reg,imm`, then classifies each.

  G0 parse     .text dump parses; field-ref counts pinned.
  G1 inline    every `test DWORD PTR [..+0x94d448],imm` whose mask meets 0xc00.
  G2 register  def-use: `mov r32,[..+0x94d448]` -> `test part,imm`, window 8.
  G3 shortlist the seven named sites, each classified; the 7th is measured
               NOT to ask 0xc00 (it asks bits 2 and 16).
  G4 algebra   each mask decomposed into named bits; the extras are enumerated.
  G5 polarity  for each site the jcc mnemonic + target: accord -> skip or act.
  G6 near     0x810-only sites and byte-split (+0x94d449) refs: measured misses.
  G7 rivals    five rival readings, each refuted on the printed numbers.
  G8 digest    the printed table digest, computed twice.

M382_PATCH='addr|text' rewrites one instruction line in memory (mutants).
M382_ALGO=n flips an algorithm law (10 part-shift, 11 no-overwrite-stop, 12 window).
"""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M382_TEXT", os.path.join(ROOT, "scratch/m574/text.txt"))

FIELD = 0x94D448
CORE = 0xC00                      # the pair under study
ALGO = int(os.environ.get("M382_ALGO", "0") or 0)
PATCH = os.environ.get("M382_PATCH", "")
DIGEST_PIN = "90cb89f84ce7feeb"

PAT = re.compile(r'^\s*([0-9a-f]+):\t([0-9a-f ]+?)(?:\t(.*))?$')
PART = {"al": ("eax", 8, 0), "ah": ("eax", 8, 1), "ax": ("eax", 16, 0), "eax": ("eax", 32, 0),
        "bl": ("ebx", 8, 0), "bh": ("ebx", 8, 1), "bx": ("ebx", 16, 0), "ebx": ("ebx", 32, 0),
        "cl": ("ecx", 8, 0), "ch": ("ecx", 8, 1), "cx": ("ecx", 16, 0), "ecx": ("ecx", 32, 0),
        "dl": ("edx", 8, 0), "dh": ("edx", 8, 1), "dx": ("edx", 16, 0), "edx": ("edx", 32, 0),
        "esi": ("esi", 32, 0), "edi": ("edi", 32, 0)}

# the seven shortlist addresses, in the order NEXT_PROMPT names them
SHORT = [0x4EC9C3, 0x523A7C, 0x563165, 0x56A8A2, 0x5859AE, 0x5468C7, 0x5552FF]

FAILS = []
TOTAL = [0]


def check(name, cond, detail=""):
    TOTAL[0] += 1
    print(("  ok   " if cond else "  FAIL ") + name + ((" — " + detail) if detail else ""))
    if not cond:
        FAILS.append(name)
    return cond


def load_text(path):
    ins = []
    for line in open(path, encoding="latin-1"):
        m = PAT.match(line.rstrip("\n"))
        if not m:
            continue
        body = (m.group(3) or "").strip()
        if body:
            ins.append((int(m.group(1), 16), body))
    return ins


def apply_patch(ins):
    if not PATCH:
        return ins
    addr, text = PATCH.split("|", 1)
    a = int(addr, 16)
    out = []
    for x, b in ins:
        out.append((x, text.strip() if x == a else b))
    return out


def effective_mask(part, imm):
    """Return (base_reg, mask in the dword's own bit positions)."""
    base, bits, hi = PART[part]
    if ALGO == 10:                      # law mutant: high bytes are not shifted
        return base, imm & ((1 << bits) - 1)
    if bits == 8 and hi:
        return base, (imm & 0xFF) << 8
    return base, imm & ((1 << bits) - 1) & (0xFFFFFFFF if bits == 32 else (1 << bits) - 1)


def bits_of(mask):
    return [0x400, 0x800, 0x10, 0x20, 0x1, 0x40000, 0x0] and \
           [b for b in (0x1, 0x2, 0x4, 0x8, 0x10, 0x20, 0x40, 0x80, 0x100, 0x200,
                        0x400, 0x800, 0x1000, 0x2000, 0x4000, 0x8000, 0x10000,
                        0x20000, 0x40000, 0x80000, 0x100000, 0x200000, 0x400000,
                        0x800000, 0x1000000, 0x2000000, 0x8000000) if mask & b]


def census_inline(ins):
    out = []
    for a, b in ins:
        if not b.startswith("test ") or "DWORD PTR" not in b or "94d448" not in b:
            continue
        m = re.search(r",(0x[0-9a-f]+)$", b)
        if not m:
            continue
        out.append((a, int(m.group(1), 16), b))
    return out


def census_register(ins):
    out = []
    window = 8
    for i, (a, b) in enumerate(ins):
        if not b.startswith("mov ") or "DWORD PTR" not in b or "94d448" not in b:
            continue
        m = re.match(r"mov\s+(\w+),DWORD PTR", b)
        if not m or m.group(1) not in PART:
            continue
        base = PART[m.group(1)][0]
        for j in range(i + 1, min(i + 1 + window, len(ins))):
            a2, b2 = ins[j]
            tm = re.match(r"test\s+(\w+),(0x[0-9a-f]+)$", b2)
            if tm and PART.get(tm.group(1), ("", 0, 0))[0] == base:
                bb, mask = effective_mask(tm.group(1), int(tm.group(2), 16))
                out.append((a, a2, mask, b2))
                break
            mw = re.match(r"(?:mov|or|xor|add|sub|and|lea|imul|pop|inc|dec)\s+(\w+),", b2)
            if mw and PART.get(mw.group(1), ("", 0, 0))[0] == base:
                break
    return out


def fold_2095(ins, site):
    """Prove the 2095-fold and that it is the index the site actually uses.

    The sequence is `mov A,B / shl A,6 / add A,B / lea C,[B+A*2] / shl C,4 / sub C,B`,
    which computes B*((2^(s1+1)+3)*2^s2 - 1).  The seed `mov A,B` is REQUIRED (without it
    the coefficient of A and B differ); the result is accepted only if the site's memory
    operand is `[C*4+0x94d448]`.  Returns (coefficient, C) or None.
    """
    k = [i for i, (x, b) in enumerate(ins) if x == site][0]
    for i in range(max(1, k - 14), k):
        m = re.match(r"shl\s+(\w+),0x6$", ins[i][1])
        if not m:
            continue
        A = m.group(1)
        if i + 4 >= len(ins):
            continue
        seed = re.match(r"mov\s+(\w+),(\w+)$", ins[i - 1][1])
        m1 = re.match(r"add\s+(\w+),(\w+)$", ins[i + 1][1])
        m2 = re.match(r"lea\s+(\w+),\[(\w+)\+(\w+)\*2\]$", ins[i + 2][1])
        m3 = re.match(r"shl\s+(\w+),0x4$", ins[i + 3][1])
        m4 = re.match(r"sub\s+(\w+),(\w+)$", ins[i + 4][1])
        if not (seed and m1 and m2 and m3 and m4):
            continue
        B = seed.group(2)
        C = m3.group(1)
        if seed.group(1) != A or m1.group(1) != A or m1.group(2) != B \
                or m2.group(3) != A or m2.group(2) != B or m4.group(1) != C or m4.group(2) != B:
            continue
        used = ins[k][1]
        if ("[%s*4+0x94d448]" % C) not in used:
            continue
        s1 = int(re.search(r",0x([0-9a-f]+)$", ins[i][1]).group(1), 16)
        sc = int(re.search(r"\*\s*(\d+)\]$", ins[i + 2][1]).group(1))
        s2 = int(re.search(r",0x([0-9a-f]+)$", ins[i + 3][1]).group(1), 16)
        return (((2 ** s1) + 1) * sc + 1) * (2 ** s2) - 1, C
    return None


def main():
    raw = load_text(TEXT)
    ins = apply_patch(raw)
    print("M382 0xc00-cluster readers — field = DWORD [pair*4 + 0x%x]" % FIELD)

    # ---------------- G0 parse -------------------------------------------
    print("\nG0  parse")
    refs = [(a, b) for a, b in ins if "94d448" in b or (ALGO == 14 and "94d449" in b)]
    byte_refs = [(a, b) for a, b in ins if "94d449" in b]
    print("  insns=%d  refs(+0x94d448)=%d  refs(+0x94d449)=%d" % (len(ins), len(refs), len(byte_refs)))
    check("G0 insn count 781429", len(ins) == 781429, str(len(ins)))
    check("G0 field refs 653", len(refs) == 653, str(len(refs)))
    check("G0 byte refs 5", len(byte_refs) == 5, str(len(byte_refs)))

    # ---------------- G1 inline census ------------------------------------
    inline = census_inline(ins)
    hit = [(a, m, b) for a, m, b in inline if m & CORE]
    print("\nG1  field-inline test sites: %d total, %d meet 0x%x" % (len(inline), len(hit), CORE))
    for a, m, b in hit:
        print("  0x%-8x mask=0x%-6x %s" % (a, m, b))
    dyn = [a for a, b in ins if b.startswith("test ") and "DWORD PTR" in b
           and "94d448" in b and not re.search(r",(0x[0-9a-f]+)$", b)]
    print("  plus %d dynamic-mask inline sites (mask in a register) — a LIMIT, not read" % len(dyn))
    check("G1 inline immediate-mask total 36", len(inline) == 36, str(len(inline)))
    check("G1 dynamic-mask inline sites 9", len(dyn) == 9, str(len(dyn)))
    check("G1 five 0xc00-paired sites", sum(1 for a, m, b in hit if (m & CORE) == CORE) == 5,
          str(sum(1 for a, m, b in hit if (m & CORE) == CORE)))

    # ---------------- G2 register census ----------------------------------
    reg = census_register(ins)
    rhit = [(l, t, m, b) for l, t, m, b in reg if m & CORE]
    print("\nG2  loaded-register readers: %d loads test the dword, %d meet 0x%x" % (len(reg), len(rhit), CORE))
    for l, t, m, b in rhit:
        print("  load 0x%-8x test 0x%-8x mask=0x%-6x %s" % (l, t, m, b))
    check("G2 loads scanned 144", len(reg) == 144, str(len(reg)))
    check("G2 register readers 8", len(rhit) == 8, str(len(rhit)))
    print("  (scan: 8-instruction bounded, stops on any write to the base register — a HEURISTIC, not full def-use)")

    # ---------------- G3 shortlist ----------------------------------------
    cluster = set(a for a, m, b in hit if m & CORE) | set(t for l, t, m, b in rhit)
    print("\nG3  shortlist classification (%d named)" % len(SHORT))
    named = {}
    for a in SHORT:
        if a in cluster:
            row = [(m, b) for x, m, b in hit if x == a] or \
                  [(m, b) for l, t, m, b in rhit if t == a]
            named[a] = ("CLUSTER", row[0][0])
            print("  0x%-8x CLUSTER mask=0x%-6x %s" % (a, row[0][0], row[0][1]))
        else:
            # what does it actually ask? first test of the dword near the site
            k = [i for i, (x, b) in enumerate(ins) if x == a][0]
            near = [b for x, b in ins[k:k + 3]]
            print("  0x%-8x NOT-0xc00  %s" % (a, " / ".join(near[:2])))
            named[a] = ("OTHER", 0)
    in_short = sum(1 for a in SHORT if named[a][0] == "CLUSTER")
    check("G3 six of seven are cluster readers", in_short == 6, str(in_short))
    k7 = [i for i, (x, b) in enumerate(ins) if x == 0x5468C7][0]
    t1 = ins[k7][1]
    t2 = next(b for x, b in ins[k7 + 1:k7 + 4] if b.startswith("test"))
    print("  0x5468c7 gate: %s / %s" % (t1, t2))
    check("G3 0x5468c7 asks bits 2|16 otherwise", named[0x5468C7] == ("OTHER", 0))
    check("G3 0x5468c7 tests al,0x4 (bit 2)", t1 == "test   al,0x4", t1)
    check("G3 0x5468c7 then tests eax,0x10000 (bit 16)", t2 == "test   eax,0x10000", t2)
    check("G3 0x5552ff is the sole 0x400-only reader", named[0x5552FF] == ("CLUSTER", 0x400),
          str(named[0x5552FF]))
    check("G3 cluster total 15", len(cluster) == 15, str(len(cluster)))

    # ---------------- G4 mask algebra -------------------------------------
    print("\nG4  mask algebra")
    for a in sorted(cluster):
        m = next((mm for x, mm, b in hit if x == a), None)
        if m is None:
            m = next((mm for l, t, mm, b in rhit if t == a), None)
        print("  0x%-8x 0x%06x = %s" % (a, m, "+".join("0x%x" % b for b in bits_of(m))))
    paired = [m for x, m, b in hit if (m & CORE) == CORE]
    check("G4 every 0xc00-paired inline mask carries both 0x400 and 0x800",
          all((m & 0x400) and (m & 0x800) for m in paired), str(["0x%x" % m for m in paired]))
    reg_only = [m for l, t, m, b in rhit if m in (0x400, 0x800)]
    check("G4 register readers may ask one bit alone", len(reg_only) == 3,
          str(["0x%x" % m for m in reg_only]))
    extras = sorted(set(m & ~CORE for m in paired))
    check("G4 paired-mask extras are 0x10|0x11|0x30|0x40030", extras == [0x10, 0x11, 0x30, 0x40030],
          str(["0x%x" % e for e in extras]))
    inline_pin = {0x4EC9C3: 0xC30, 0x523A7C: 0x40C30, 0x563165: 0xC30, 0x56A8A2: 0xC10,
                  0x5859AE: 0xC11, 0x558CBD: 0x810, 0x56C153: 0x810}
    got_inline = {a: m for a, m, b in hit}
    check("G4 inline masks equal the pinned per-site table", got_inline == inline_pin,
          str({hex(k): hex(v) for k, v in got_inline.items()}))
    reg_pin = {0x503727: 0x800, 0x546CDE: 0x800, 0x5552FF: 0x400, 0x5567BB: 0xC10,
               0x558B9D: 0xC14, 0x559D04: 0xC10, 0x560B77: 0xC00, 0x56B652: 0xC10}
    got_reg = {t: m for l, t, m, b in rhit}
    check("G4 register masks equal the pinned per-site table", got_reg == reg_pin,
          str({hex(k): hex(v) for k, v in got_reg.items()}))
    all_masks = list(got_inline.values()) + list(got_reg.values())
    check("G4 exactly one reader asks 0x400 alone (0x5552ff)",
          [a for a in got_reg if got_reg[a] == 0x400] == [0x5552FF], str([hex(a) for a in got_reg]))
    check("G4 exactly one reader asks 0xc00 alone (0x560b77)",
          [a for a in got_reg if got_reg[a] == 0xC00] == [0x560B77], str([hex(a) for a in got_reg]))

    # ---------------- G5 polarity -----------------------------------------
    print("\nG5  branch polarity (accord -> ?)  [jcc must be the branch of THAT test]")
    pol = {}
    for a in sorted(cluster):
        if a in got_inline:
            k = [i for i, (x, b) in enumerate(ins) if x == a][0]
        else:
            k = [i for i, (x, b) in enumerate(ins) if x == a][0] + 0   # register: site IS the test
        nxt = ins[k + 1][1]
        jm = re.match(r"(j\w+)\s+0x([0-9a-f]+)$", nxt)
        ok_adj = bool(jm)
        mn, tgt = (jm.group(1), int(jm.group(2), 16)) if jm else ("NONE", 0)
        nz_taken = mn.startswith("jn") or mn in ("ja", "jb", "jg", "jl")
        if ALGO == 15:                       # law mutant: polarity read backwards
            nz_taken = not nz_taken
        pol[a] = (mn, tgt, nz_taken)
        print("  0x%-8x %-4s 0x%-8x accord %s%s" % (a, mn, tgt,
              "TAKES the branch" if nz_taken else "FALLS THROUGH",
              "" if ok_adj else "   <-- NOT ADJACENT"))
    check("G5 all 15 sites' jcc is the instruction right after the test", len(pol) == 15 and
          all(re.match(r"j\w+$", v[0]) for v in pol.values()))
    pol_pin = {0x4EC9C3: True, 0x503727: False, 0x523A7C: False, 0x546CDE: True,
               0x5552FF: False, 0x5567BB: False, 0x558B9D: False, 0x558CBD: False,
               0x559D04: True, 0x560B77: True, 0x563165: False, 0x56A8A2: False,
               0x56B652: True, 0x56C153: False, 0x5859AE: False}
    check("G5 polarity equals the pinned per-site table",
          {a: v[2] for a, v in pol.items()} == pol_pin,
          str({hex(a): v[2] for a, v in pol.items()}))

    # ---------------- G6 near misses --------------------------------------
    print("\nG6  near misses")
    only800 = [(a, m) for a, m, b in hit if not (m & 0x400)]
    for a, m in only800:
        print("  0x%-8x mask=0x%-4x asks 0x800 alone" % (a, m))
    check("G6 two 0x810-only inline sites", [a for a, m in only800] == [0x558CBD, 0x56C153],
          str(["0x%x" % a for a, m in only800]))
    check("G6 no byte-split ref asks 0xc00",
          all(not (int(m.group(1), 16) & CORE) for a, b in byte_refs
              for m in [re.search(r",(0x[0-9a-f]+)$", b)] if m))

    # ---------------- G7 rivals -------------------------------------------
    print("\nG7  rivals")
    check("R1 'the cluster is one bit' — refuted: masks include 0x400 alone at 0x5552ff",
          any(m == 0x400 for l, t, m, b in rhit))
    paired_sites = [x for x, m, b in hit if (m & CORE) == CORE]
    folds = [fold_2095(ins, x) for x in paired_sites]
    check("R2 each inline site folds 2095*owner+other AND indexes the field with that register",
          len(folds) == 5 and all(f is not None and f[0] == 2095 for f in folds),
          str([(f[0], f[1]) if f else None for f in folds]))
    check("R3 '0x5468c7 asks 0xc00' — refuted: it asks 0x4 and 0x10000",
          named[0x5468C7] == ("OTHER", 0))
    check("R4 'every reader is field-inline' — refuted: 8 register readers",
          len(rhit) == 8)
    check("R5 'the seven named are the population' — refuted: 15 readers, 6 named",
          len(cluster) == 15 and in_short == 6)

    # ---------------- G9 attribution --------------------------------------
    idx = os.environ.get("M382_INDEX", os.path.expanduser("~/reverse/smac/ghidra_out/index.csv"))
    fns = []
    with open(idx) as f:
        import csv
        for d in csv.DictReader(l for l in f if not l.startswith("#")):
            fns.append((int(d["addr"], 16), int(d["size_bytes"]), d["name"]))
    fns.sort()

    def owner(a):
        best = None
        k = None
        for j, (addr, size, name) in enumerate(fns):
            if addr <= a < addr + size:
                best, k = name, j
            elif addr > a:
                break
        if ALGO == 13 and k is not None and k > 0:      # law mutant: previous function
            return fns[k - 1][2]
        return best

    print("\nG9  function attribution (index.csv: %d functions)" % len(fns))
    attr = {a: owner(a) for a in sorted(cluster)}
    for a in sorted(cluster):
        print("  0x%-8x %s" % (a, attr[a]))
    want = {0x4EC9C3: "FUN_004ebef0", 0x523A7C: "FUN_00523a20", 0x563165: "FUN_0055f650",
            0x56A8A2: "FUN_0055f650", 0x5859AE: "FUN_00585720", 0x5552FF: "FUN_005551e0",
            0x5468C7: "FUN_00546800", 0x503727: "FUN_00502cd0", 0x546CDE: "FUN_00546800",
            0x5567BB: "FUN_00556690", 0x558B9D: "FUN_00556690", 0x559D04: "FUN_00556690",
            0x560B77: "FUN_0055f650", 0x56B652: "FUN_0055f650"}
    check("G9 five distinct host functions for the 6 named cluster sites",
          len({attr[a] for a in SHORT if a in cluster}) == 5,
          str(sorted(x for x in {attr[a] for a in SHORT if a in cluster} if x)))
    check("G9 every named site sits in its pinned function",
          all(attr.get(a) == n for a, n in want.items() if a in attr))
    check("G9 the 15 readers span 8 host functions",
          len({attr[a] for a in cluster}) == 8,
          str(sorted({attr[a] for a in cluster})))
    check("G9 the AI hub FUN_0055f650 hosts five readers",
          sum(1 for a in cluster if attr[a] == "FUN_0055f650") == 5,
          str(sum(1 for a in cluster if attr[a] == "FUN_0055f650")))

    # ---------------- G8 digest -------------------------------------------
    rows = ["0x%x:0x%x:%s" % (a, pol[a][1], pol[a][0]) for a in sorted(pol)]
    body = "\n".join(rows)
    d1 = hashlib.sha1(body.encode()).hexdigest()[:16]
    print("\nG8  digest of 15 (site,target,mnemonic) rows = %s" % d1)
    check("G8 digest pinned (whole printed table; re-run identity is evidence/m382_twice.txt)",
          d1 == DIGEST_PIN, d1)

    print("\n%s M382: %d/%d" % ("PASS" if not FAILS else "FAIL", TOTAL[0] - len(FAILS), TOTAL[0]))
    if FAILS:
        print("failing: " + ", ".join(FAILS))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
