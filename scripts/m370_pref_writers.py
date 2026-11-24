#!/usr/bin/env python3
"""M370 - the (x6) OTHER writers of the preference block ds:0x92bde8..0x92bf14.

PICK: NEXT_PROMPT (x6).  Prior footing: `NAMED ## M332` (0x92bde8 = the win-INI key
`Difficulty`, ONE store in the loader), `## M355` (0x92befc/0x92bf00 = the two
`Laptop` bit-vectors, APPLY 0x492464/0x49246f), `## M357` (0x92bf04 = WARNINGS, own
key).  Those name 4 of the block's 11 cells and 4 of its 43 stores.  This unit
enumerates EVERY store in the span and says what each one sets.

Every number is COMPUTED from the static image (scratch/m574/text.txt = objdump
.text; programs/terran.exe = the PE for VA->string resolution; ghidra_out/index.csv
= function spans).  Zero box time.

THE ANCHOR (two-sided, independent): the block is what the game SERIALISES.  The
loader FUN_0058e7f0 reads an INI key -> a cell; the writeback FUN_0058f0d0 reads a
cell -> the SAME KEY TEXT at a different VA.  A cell named on both sides is a field,
not an offset coincidence.  11 cells carry a name; the names are read from the PE
strings, never typed in.

GATES (printed first, then asserted; every one has a named mutant in
scripts/m370_mutate.py):
  G0  the .text cache/PE/index all resolve; the span has refs.
  G1  reference census over CELLS+0x92bdfc: text set == byte disp32 set, with the
      rel32 filter ON (a call's relative operand is not an address reference), and
      the materialisation scan (an immediate in the span used outside a ds:
      operand) - the direct set is the complete set.
  G2  partition closed: every ref is exactly one of STORE / READ / BOUND (0x92bdfc
      is only ever the end-of-array compare), every store's cell is a named cell.
  G3  per-store reachability (fall-in or branch target) + owner resolved through
      the Ghidra span gap at 0x5108e0.
  G4  READ-side key pairing by CALL SHAPE (6-push GetPrivateProfileString, key at
      call-2; 3-push helper 0x58e760) - INJECTIVE for all 11 cells.  The naive
      "nearest string push" law is run too and is KILLED on 0x92befc (it names
      `Laptop`, the mask seed, not the key read).
  G5  WRITE-side key pairing by CALL SHAPE (4-push writer / helper 0x58f030); its
      text must equal the read-side text for all 11 cells, at different VAs.
  G6  writer families: every non-loader store's source is classified by a
      backward def-use walk (copy-of-cell / call-return / immediate / carried).
  G7  RIVALS killed on the printed numbers: "only the 3 UI cells are writable";
      "the INI loader is the only writer"; "0x92bde8 has one store".
  G8  the boundary: the loader's base-pointer sweep writes 0x92bf18..0x92bf30
      (7 dwords, key `Custom World`) - the span ENDS at 0x92bf14 and no
      materialisation in the block is a store.
"""
import bisect
import hashlib
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M370_TEXT", os.path.join(ROOT, "scratch/m574/text.txt"))
IDXCSV = os.path.join(ROOT, "ghidra_out/index.csv")
EXE = os.path.join(ROOT, "programs/terran.exe")
if not os.path.exists(EXE):
    EXE = os.path.join(ROOT, "terran.exe")

LO, HI = 0x92BDE8, 0x92BF14          # the span under study (inclusive)
BOUND_ONLY = 0x92BDFC                # an address the code only COMPARES against
LOADER = (0x58E7F0, 0x58F002)        # FUN_0058e7f0  INI -> cell
WRITEBACK = (0x58F0D0, 0x58F3C6)     # FUN_0058f0d0 cell -> INI
KEYBAND = (0x6926C0, 0x6928A0)       # the pref-name strings, same .data block

CELLS = [0x92BDE8, 0x92BDEC, 0x92BDF4, 0x92BDF8, 0x92BEFC,
         0x92BF00, 0x92BF04, 0x92BF08, 0x92BF0C, 0x92BF10, 0x92BF14]
CENSUS = CELLS + [BOUND_ONLY]

# Every site a TEXT mutant patches.  G9a asserts each of them is EXERCISED by this
# run (a store/read site, a key push, a materialisation, or within +-2 insns of one),
# so the mutation harness cannot pass by patching an address the census never reads.
PINS = {
    0x58E8C6: "loader Difficulty store", 0x58EC20: "loader More-Preferences store",
    0x58E8A1: "read key `Difficulty` push", 0x58F159: "write key `Difficulty` push",
    0x58E9CD: "read key `Faction` push", 0x492464: "APPLY Preferences store",
    0x57C7B0: "second 0x92bde8 store", 0x58E98E: "loader Top-Menu store",
    0x4DC8B7: "predecessor of the Semaphore store", 0x48AEA9: "0x92bdfc bound cmp",
    0x579BC6: "0x92bde8 bound cmp", 0x5109F8: "gap handler Preferences store",
    0x57C914: "Customize store", 0x58E922: "Map-Type store",
    0x58EFC4: "Custom-World sweep base",
}

# M370_ALGO mutants of the CLASSIFIER / TRACER laws:
#   1 = the leaning of the pairing is flipped (backward <-> forward)
#   2 = `mov mem,reg` is read as a LOAD (the store/load split is off)
#   3 = the byte-encoding scan reads the disp32 BIG-endian
#   4 = the rel32 filter is off (a call's relative operand counts as a reference)
#   5 = the pairing uses the nearest string push instead of the call shape
ALGO = os.environ.get("M370_ALGO", "")

LINE = re.compile(r"^\s*([0-9a-f]{6,8}):\t([0-9a-f ]+?)\s*\t(.*?)(?:\t;.*)?$")
OPS = re.compile(r"^([a-z][a-z0-9]*)\s+(.*)$")
IMM = re.compile(r"^0x([0-9a-f]{1,8})$")
MEM = re.compile(r"^(?:([A-Z]+) PTR )?ds:0x([0-9a-f]{6,8})$")
HEX = re.compile(r"0x([0-9a-f]{6,8})")
JMPC = re.compile(r"^(j[a-z]+|call)$")
SUBREG = {}
for _full, _subs in (("eax", ("eax", "ax", "al", "ah")), ("ecx", ("ecx", "cx", "cl", "ch")),
                     ("edx", ("edx", "dx", "dl", "dh")), ("ebx", ("ebx", "bx", "bl", "bh")),
                     ("esi", ("esi", "si")), ("edi", ("edi", "di")),
                     ("ebp", ("ebp", "bp")), ("esp", ("esp", "sp"))):
    for _s in _subs:
        SUBREG[_s] = _full
RMW = {"add", "sub", "and", "or", "xor", "inc", "dec", "neg", "not", "shl", "shr", "sar", "xchg"}
WRITERS = {"mov", "movsx", "movzx", "movbe"}

_T = []


class _Tee:
    def __init__(self, stream):
        self.s = stream
        self.buf = ""

    def write(self, s):
        self.s.write(s)
        self.buf += s
        while "\n" in self.buf:
            line, self.buf = self.buf.split("\n", 1)
            _T.append(line)

    def flush(self):
        self.s.flush()


def dig():
    return hashlib.sha1("\n".join(_T).encode()).hexdigest()[:16]


def insns():
    """Read the objdump .text cache.  M370_PATCH='addr|new text' rewrites ONE line
    in memory - the mutation harness's lever on the instruction stream."""
    patch = os.environ.get("M370_PATCH")
    pa = pt = None
    if patch:
        pa, _, pt = patch.partition("|")
        pa = int(pa.strip(), 16)
        pt = pt.strip()
    out, hit = [], False
    with open(TEXT, "r", errors="replace") as f:
        for line in f:
            m = LINE.match(line)
            if not m:
                continue
            a = int(m.group(1), 16)
            by = m.group(2).split()
            txt = m.group(3).strip()
            if a == pa:
                if txt == pt:
                    sys.stderr.write("M370_PATCH already equal at %s\n" % hex(a))
                    raise SystemExit(3)
                txt = pt
                hit = True
            mo = OPS.match(txt)
            out.append((a, by, txt, mo.group(1) if mo else txt.split()[0],
                        mo.group(2) if mo else ""))
    if patch and not hit:
        sys.stderr.write("M370_PATCH %s not found in .text cache\n" % hex(pa))
        raise SystemExit(2)
    return out


def load_fn_index():
    rows, head = [], None
    with open(IDXCSV) as f:
        for line in f:
            if line.startswith("addr,"):
                head = line.strip().split(",")
                continue
            if not line.strip() or line.startswith("#"):
                continue
            d = dict(zip(head, line.rstrip("\n").split(",")))
            try:
                rows.append((int(d["addr"], 16), d["name"], int(d["size_bytes"])))
            except (KeyError, ValueError):
                pass
    rows.sort()
    return rows


ROWS = load_fn_index()
STARTS = [r[0] for r in ROWS]


def fnof(a):
    i = bisect.bisect_right(STARTS, a) - 1
    if i < 0:
        return ("?", 0, 0, False)
    addr, name, size = ROWS[i]
    return (name, addr, size, addr <= a < addr + size)


def pe_sections():
    d = open(EXE, "rb").read()
    pe = struct.unpack_from("<I", d, 0x3C)[0]
    opt = pe + 24
    imgbase = struct.unpack_from("<I", d, opt + 28)[0]
    p = opt + struct.unpack_from("<H", d, pe + 20)[0]
    secs = []
    for _ in range(struct.unpack_from("<H", d, pe + 6)[0]):
        vs, va, rs, ra = struct.unpack_from("<IIII", d, p + 8)
        secs.append((imgbase + va, vs, ra, rs))
        p += 40
    return d, imgbase, secs


def off_of(secs, va):
    for v, vs, ra, rs in secs:
        if v <= va < v + vs:
            return ra + va - v
    return None


def cstr(d, secs, va, lim=96):
    o = off_of(secs, va)
    if o is None:
        return None
    try:
        e = d.index(b"\x00", o, o + lim)
    except ValueError:
        return None
    t = d[o:e].decode("latin1")
    return t if t and all(32 <= ord(c) < 127 for c in t) else None


def split_ops(ops):
    parts = ops.split(",")
    if len(parts) < 2:
        return (parts[0].strip() if parts and parts[0].strip() else None), None
    return parts[0].strip(), ",".join(parts[1:]).strip()


def mem_of(op):
    if op is None:
        return None
    m = MEM.match(op)
    return int(m.group(2), 16) if m else None


def span(addr):
    return LO <= addr <= HI


def main():
    sys.stdout = _Tee(sys.__stdout__)
    ins = insns()
    by = {a: (b, t, mn, ops) for a, b, t, mn, ops in ins}
    order = [a for a, _, _, _, _ in ins]
    idx = {a: i for i, a in enumerate(order)}
    exe, imgbase, secs = pe_sections()
    gates = []

    def gate(name, ok, msg, claim=""):
        gates.append((name, bool(ok), claim))
        print("%-5s %-4s %s" % (name, "ok" if ok else "FAIL", msg))

    def owner(a):
        """function name; a Ghidra span GAP is resolved to the nearest preceding
        pad-delimited sub-function start (ret/nop then a real insn)."""
        nm, fa, sz, ok = fnof(a)
        if ok:
            return nm, False
        i = idx[a]
        for k in range(i - 1, max(-1, i - 14), -1):
            b2, t2, mn2, o2 = by[order[k]]
            if mn2 in ("ret", "jmp"):
                j = k + 1
                while j < i and by[order[j]][2] == "nop":
                    j += 1
                return "SUB_%x" % order[j], True
        return nm + "?", True

    # ---------------- G0 ----------------
    keytext = {}
    for va in range(KEYBAND[0], KEYBAND[1]):
        o = off_of(secs, va)
        if o is None or va == KEYBAND[0] or exe[o - 1] != 0:
            continue
        t = cstr(exe, secs, va)
        if t and len(t) >= 2 and not re.match(r"^[0-9,\s]+$", t):
            keytext[va] = t
    print("== G0 inputs ==")
    print("  .text cache lines=%d  PE sections=%d  fn index=%d  key strings in %s..%s=%d"
          % (len(ins), len(secs), len(ROWS), hex(KEYBAND[0]), hex(KEYBAND[1]), len(keytext)))
    print("  loader=%s  writeback=%s  span=[0x%x,0x%x] inclusive = %d dwords"
          % (hex(LOADER[0]) + ".." + hex(LOADER[1]), hex(WRITEBACK[0]) + ".." + hex(WRITEBACK[1]),
             LO, HI, (HI - LO) // 4 + 1))
    print("  cell=0x%x (never a ds: operand)  named cells=%d" % (BOUND_ONLY, len(CELLS)))
    gate("G0a", len(ins) > 200000 and len(ROWS) > 5000 and len(keytext) >= 15
         and all(a in by for a in (LOADER[0], WRITEBACK[0], 0x58E8C6, 0x49246F)),
         "cache/index/strings resolve and the four anchor sites exist")
    if not gates[-1][1]:
        print("ABORT: precondition failed; the census would be meaningless")
        print("FAIL M370: 0/%d gates" % 1)
        return 1

    # ---------------- G1 census + encoding equivalence ----------------
    refs, encrefs, matrefs, relfalse = [], [], [], []
    tpair, epair = set(), set()
    for a, b, t, mn, ops in ins:
        hs = [int(v, 16) for v in HEX.findall(t) if span(int(v, 16))]
        if hs:
            refs.append(a)
            for v in hs:
                tpair.add((a, v))
                pos = t.find("0x%x" % v)
                pre = t[max(0, pos - 4):pos]
                if not pre.endswith("ds:"):
                    matrefs.append((a, t, v))
        if JMPC.match(mn) and ALGO != "4":
            continue          # a rel32 operand is not an address reference
        for c in CENSUS:
            le = [c & 0xFF, (c >> 8) & 0xFF, (c >> 16) & 0xFF, (c >> 24) & 0xFF]
            k = " ".join("%02x" % x for x in (le[::-1] if ALGO == "3" else le))
            if (" ".join(b)).find(k) >= 0:
                encrefs.append(a)
                epair.add((a, c))
                if not hs:
                    relfalse.append((a, t))
                break
    refs = sorted(set(refs))
    encrefs = sorted(set(encrefs))
    print("== G1 reference census, span 0x%x..0x%x (CELLS + one bound address) ==" % (LO, HI))
    print("  text-form refs %d  byte-encoded disp32 refs %d  PAIR set-identical %s"
          % (len(refs), len(encrefs), tpair == epair))
    print("  rel32 false positives caught by the filter: %s"
          % [hex(a) + ":" + t for a, t in relfalse[:4]])
    print("  address materialisations OUTSIDE a ds: operand: %d" % len(matrefs))
    for a, t, v in matrefs:
        print("    %-9s %-30s -> 0x%x" % (hex(a), t, v))
    print("  by target: " + ", ".join("0x%x=%d" % (x, len([1 for _, _, v in matrefs if v == x]))
                                      for x in sorted({v for _, _, v in matrefs})))
    gate("G1a", tpair == epair and not relfalse,
         "the (site,cell) PAIR set is identical in text and bytes with the rel32 filter on")
    gate("G1b", len(matrefs) == 5 and len({v for _, _, v in matrefs}) == 2 and
         all(by[a][2] == "cmp" for a, _, _ in matrefs),
         "all %d materialisations are cmp loop bounds (no store uses the base)" % len(matrefs))

    # ---------------- G2 partition ----------------
    stores, reads, bounds, other = [], [], [], []
    for a in refs:
        b, t, mn, ops = by[a]
        dst, src = split_ops(ops)
        dcell, scell = mem_of(dst), mem_of(src)
        if ALGO == "2" and mn in WRITERS and mem_of(src) is None:
            dcell, scell = None, mem_of(dst)
        if BOUND_ONLY in [int(v, 16) for v in HEX.findall(t)] and BOUND_ONLY not in CELLS \
                and mem_of(dst) != BOUND_ONLY and mem_of(src) != BOUND_ONLY:
            bounds.append((a, t))
        elif mn in WRITERS and dcell is not None and span(dcell):
            stores.append((a, dcell, "mov", t))
        elif mn in RMW and dcell is not None and span(dcell):
            stores.append((a, dcell, "rmw", t))
        elif mn in ("mov", "movsx", "movzx", "movbe", "cmp", "test", "push", "imul") or \
                (mn in RMW and scell is not None):
            reads.append((a, dcell if mn in WRITERS else scell, t))
        elif mn in WRITERS and scell is not None and span(scell):
            reads.append((a, scell, t))
        else:
            other.append((a, t))
    print("== G2 partition ==")
    print("  refs=%d  STORE=%d  READ=%d  BOUND=%d  other=%d %s"
          % (len(refs), len(stores), len(reads), len(bounds), len(other),
             [hex(a) for a, _ in other]))
    print("  BOUND rows (0x%x, cmp only): %s" % (BOUND_ONLY, [hex(a) for a, _ in bounds]))
    per = {}
    for a, c, k, t in stores:
        per.setdefault(c, []).append(a)
    print("  named cells=%d  with >=1 store=%d  without=%s"
          % (len(CELLS), len([c for c in CELLS if c in per]),
             [hex(c) for c in CELLS if c not in per]))
    for c in CELLS:
        print("  0x%06x stores=%2d  %s" % (c, len(per.get(c, [])),
                                           " ".join(hex(a) for a in sorted(per.get(c, [])))))
    gate("G2a", len(per) == len(CELLS) and len(stores) + len(reads) + len(bounds) == len(refs)
         and not other, "partition closed; all 11 named cells have a store")
    narrow = [(a, t) for a, c, k, t in stores
              if re.match(r"^(BYTE|WORD) PTR ", t.split(",")[0].split(" ", 1)[-1].strip())
              or t.split(",")[0].startswith(("BYTE", "WORD"))]
    print("  stores with a BYTE/WORD destination: %d %s" % (len(narrow), [hex(a) for a, _ in narrow]))
    gate("G2b", all(span(c) for c in per) and not narrow,
         "every store is a full-dword store of a span cell")
    dsbound = [a for a in refs if mem_of(split_ops(by[a][3])[0]) == BOUND_ONLY
               or mem_of(split_ops(by[a][3])[1]) == BOUND_ONLY]
    print("  ds: references to 0x%x (the bound address): %d %s"
          % (BOUND_ONLY, len(dsbound), [hex(a) for a in dsbound]))
    gate("G2c", len(dsbound) == 0,
         "0x%x is never addressed as memory (only compared as an immediate)" % BOUND_ONLY)

    # ---------------- G3 reachability + owner ----------------
    br = {}
    for a, b, t, mn, ops in ins:
        if JMPC.match(mn) and ops:
            m = IMM.match(ops.strip())
            if m:
                br.setdefault(int(m.group(1), 16), []).append(a)
    print("== G3 per-store reachability / owner ==")
    gapsite = 0
    fallin = {}
    for a, c, k, t in stores:
        i = idx[a]
        prev = order[i - 1] if i else None
        pmn = by[prev][2] if prev is not None else "?"
        st = "FALL-IN" if pmn not in ("ret", "jmp", "hlt") else "CARRIED"
        fallin[a] = (st, br.get(a, []))
        nm, gap = owner(a)
        gapsite += 1 if gap else 0
        print("  %-9s 0x%06x %-4s %-8s %-30s fn=%s%s targets=%s" % (
            hex(a), c, k, st, t, nm, "(GAP-RESOLVED)" if gap else "",
            [hex(x) for x in br.get(a, [])]))
    print("  owners: %s" % sorted({owner(a)[0] for a, _, _, _ in stores}))
    print("  span-gap sites resolved to a pad-delimited sub-function: %d" % gapsite)
    gate("G3a", all(st == "FALL-IN" or tg for st, tg in fallin.values()),
         "every store is reachable (fall-in or branch target)")
    gate("G3b", gapsite == 4 and "?" not in " ".join(o for o, _ in (owner(a) for a, _, _, _ in stores)),
         "the 0x5108e0 handlers are named through the Ghidra span gap")

    # ---------------- call-shape key extraction ----------------
    def call_key(ci):
        """ci = instruction index of a call.  Returns (key VA, form) by SHAPE."""
        a = order[ci]
        mn, ops = by[a][2], (by[a][3] or "").strip()
        if ALGO != "5":
            win = [order[k] for k in range(max(0, ci - 14), ci)]
            if any(by[x][2] == "push" and (by[x][3] or "").strip() == "0x100" for x in win):
                k = order[ci - 2]
                m = IMM.match((by[k][3] or "").strip())
                if by[k][2] == "push" and m and int(m.group(1), 16) in keytext:
                    return int(m.group(1), 16), "API-6PUSH"
            if mn == "call" and ops in ("0x58e760", "0x58e790", "0x58f030"):
                for k in range(ci - 1, max(-1, ci - 4), -1):
                    x = order[k]
                    if by[x][2] == "push":
                        m = IMM.match((by[x][3] or "").strip())
                        if m and int(m.group(1), 16) in keytext:
                            return int(m.group(1), 16), "HELPER"
            # 4-push writer form: file, buf, key, app, call -> key at call-2
            n4 = [order[k] for k in range(max(0, ci - 6), ci)]
            npush = [x for x in n4 if by[x][2] == "push"]
            if len(npush) == 4:
                k = order[ci - 2]
                m = IMM.match((by[k][3] or "").strip())
                if by[k][2] == "push" and m and int(m.group(1), 16) in keytext:
                    return int(m.group(1), 16), "API-4PUSH"
        # the naive law is kept runnable ONLY as the killed rival (ALGO 5)
        if ALGO == "5":
            for k in range(ci - 1, max(-1, ci - 8), -1):
                x = order[k]
                if by[x][2] == "push":
                    m = IMM.match((by[x][3] or "").strip())
                    if m and int(m.group(1), 16) in keytext:
                        return int(m.group(1), 16), "NEAREST"
        return None, ""

    def find_key(site, direction, lo, hi):
        if ALGO == "5":                  # the naive law: nearest key push, no call shape
            i = idx[site]
            rng = range(i - 1, -1, -1) if direction == "back" else range(i + 1, len(order))
            j = 0
            for k in rng:
                a = order[k]
                if not (lo <= a < hi):
                    break
                j += 1
                if j > 60:
                    break
                if by[a][2] == "push":
                    m = IMM.match((by[a][3] or "").strip())
                    if m and int(m.group(1), 16) in keytext:
                        return int(m.group(1), 16), "NEAREST", abs(k - i)
            return None, "", -1
        i = idx[site]
        rng = range(i - 1, -1, -1) if direction == "back" else range(i + 1, len(order))
        j = 0
        for k in rng:
            a = order[k]
            if not (lo <= a < hi):
                break
            j += 1
            if j > 60:
                break
            if by[a][2] == "call":
                va, form = call_key(k)
                if va is not None:
                    return va, form, abs(k - i)
        return None, "", -1

    # ---------------- G4 read side ----------------
    loader_stores = [s for s in stores if LOADER[0] <= s[0] < LOADER[1]]
    print("== G4 READ side: loader store -> the key of the nearest preceding key CALL ==")
    d = "back" if ALGO != "1" else "fwd"
    rmap = {}
    for a, c, k, t in sorted(loader_stores):
        va, form, dist = find_key(a, d, LOADER[0], LOADER[1])
        rmap[c] = (va, keytext.get(va), a, dist, form)
        print("  store %-9s cell 0x%06x <- %-10s %-10s %-18r dist=%d" % (
            hex(a), c, hex(va) if va else "-", form, keytext.get(va), dist))
    rtext = [v[1] for v in rmap.values()]
    print("  loader stores=%d  distinct key texts=%d  injective=%s"
          % (len(rmap), len(set(rtext)), len(set(rtext)) == len(rmap) and None not in rtext))
    alt = "fwd" if d == "back" else "back"
    amap = {c: find_key(a, alt, LOADER[0], LOADER[1])[1] for a, c, k, t in loader_stores}
    atext = [v for v in amap.values() if v]
    print("  opposite (%s) pairing: distinct=%d/%d -> %s"
          % (alt, len(set(atext)), len(amap),
             "not injective (direction measured)" if len(set(atext)) < len(amap) else "also injective"))
    # rival: the naive nearest-push law, from the SAME sites
    naive = {}
    for a, c, k, t in loader_stores:
        i = idx[a]
        for kk in range(i - 1, max(-1, i - 20), -1):
            x = order[kk]
            if by[x][2] == "push":
                m = IMM.match((by[x][3] or "").strip())
                if m and int(m.group(1), 16) in keytext:
                    naive[c] = keytext[int(m.group(1), 16)]
                    break
    bad = [c for c in CELLS if naive.get(c) != rmap.get(c, (None, None))[1]]
    print("  RIVAL 'nearest string push': wrong on %d/%d cells: %s"
          % (len(bad), len(CELLS), [(hex(c), naive.get(c), rmap[c][1]) for c in bad]))
    gate("G4a", len(rmap) == len(CELLS) and len(set(rtext)) == len(rmap) and None not in rtext,
         "read side: one distinct key per cell (%d/11)" % len(set(rtext)))
    gate("G4b", len(atext) < len(amap), "the direction is forced: %s pairing is not injective" % alt)
    gate("G4c", len(bad) >= 1, "the naive nearest-push law is killed on %d cell(s)" % len(bad))

    # ---------------- G5 write side ----------------
    wb_loads = [(a, mem_of(split_ops(ops)[1])) for (a, b, t, mn, ops) in ins
                if WRITEBACK[0] <= a < WRITEBACK[1]
                and mn in WRITERS and mem_of(split_ops(ops)[1]) in CELLS]
    print("== G5 WRITE side: writeback load -> the key of the nearest FOLLOWING call ==")
    dw = "fwd" if ALGO != "1" else "back"
    wmap = {}
    for a, c in wb_loads:
        va, form, dist = find_key(a, dw, WRITEBACK[0], WRITEBACK[1])
        wmap[c] = (va, keytext.get(va), a, dist, form)
        print("  load  %-9s cell 0x%06x -> %-10s %-18r dist=%d" % (
            hex(a), c, hex(va) if va else "-", keytext.get(va), dist))
    agree = [c for c in CELLS if c in rmap and c in wmap and rmap[c][1] == wmap[c][1]]
    same_va = [c for c in agree if rmap[c][0] == wmap[c][0]]
    print("  cells on both sides=%d  TEXT agrees=%d/11  shared VA=%d (separate copies)"
          % (len(wmap), len(agree), len(same_va)))
    print("  NAMES (read from the PE, never typed):")
    for c in CELLS:
        if c not in rmap or c not in wmap:
            print("    0x%06x  MISSING on %s side" % (c, "read" if c not in rmap else "write"))
            continue
        print("    0x%06x %-17s read %s %-10s write %s" % (
            c, rmap[c][1], hex(rmap[c][0]), rmap[c][4], hex(wmap[c][0])))
    gate("G5a", len(agree) == len(CELLS) and not same_va,
         "two-sided: every cell's key TEXT agrees, no VA is shared")

    # ---------------- G6 writer families ----------------
    def defof(reg, site, lim=30):
        """Backward def-use with ONE extra hop through a register-to-register
        mov/or/and: -> (kind, insn text, source cell or None)."""
        i = idx[site]
        fa = fnof(site)[1]
        hop = 0
        chain = []
        while hop < 2:
            found = None
            for k in range(i - 1, max(-1, i - lim), -1):
                a = order[k]
                if a < fa:
                    break
                b, t, mn, ops = by[a]
                dst, src = split_ops(ops)
                if mn == "call":
                    if reg in ("eax", "ecx", "edx"):
                        found = ("CALLRET", t, a, None)
                        break
                    continue
                if dst is not None and SUBREG.get(dst) == reg:
                    found = ("DEF", t, a, src)
                    break
            if found is None:
                return ("UNRESOLVED", " ".join(chain), None)
            kind, t, a, src = found
            if kind == "CALLRET":
                return ("CALLRET", " ".join(chain), None)
            scell = mem_of(src)
            if scell is not None:
                return ("COPY", t, scell)
            sreg = SUBREG.get(src or "")
            if sreg and sreg != reg and hop == 0 and mn in ("mov", "or", "and", "xor"):
                chain.append(by[a][2])
                reg, i = sreg, idx[a]
                hop += 1
                continue
            return ("DEF", t, None)
        return ("DEF", " ".join(chain), None)

    print("== G6 writer families (every store, source by a backward def-use walk) ==")
    fam, rows6 = {}, []
    for a, c, k, t in stores:
        if LOADER[0] <= a < LOADER[1]:
            sh = "INI-LOADER"
        else:
            dst, src = split_ops(by[a][3])
            if IMM.match(src or ""):
                sh = "IMM(" + src + ")"
            else:
                reg = SUBREG.get(src or "")
                if reg is None:
                    sh = "OTHER(" + str(src) + ")"
                elif fallin[a][0] == "CARRIED":
                    sh = "CARRIED"
                else:
                    dt, dtext, dcell = defof(reg, a)
                    if dt == "UNRESOLVED":
                        sh = "UNRESOLVED"
                    elif dt == "CALLRET":
                        sh = "CALLRET"
                    elif dt == "COPY":
                        sh = "COPY(0x%x)" % dcell
                    elif re.match(r"^(and|or|xor)\s+\w+,0x[0-9a-f]+$", dtext):
                        sh = "MASKED(%s)" % dtext
                    else:
                        sh = "DEF(%s)" % dtext.split()[0]
        fam.setdefault(sh, []).append(a)
        rows6.append((c, a, sh))
    for k in sorted(fam):
        print("  %-24s %2d  %s" % (k, len(fam[k]), " ".join(hex(x) for x in sorted(fam[k]))))
    nl = [a for a, c, k, t in stores if not (LOADER[0] <= a < LOADER[1])]
    print("  non-loader stores=%d in %d functions" % (len(nl), len({owner(a)[0] for a in nl})))
    print("  COPY families name the SOURCE CELL: %s" % sorted({k for k in fam if k.startswith("COPY")}))
    gate("G6a", not any(k.startswith(("UNRESOLVED", "OTHER")) for k in fam),
         "every non-loader source is classified")
    gate("G6b", len(fam.get("INI-LOADER", [])) == len(CELLS),
         "the loader stores exactly once per cell (%d)" % len(fam.get("INI-LOADER", [])))

    # ---------------- G7 rivals ----------------
    print("== G7 rivals ==")
    ui3 = {0x92BEFC, 0x92BF00, 0x92BF04}
    live = [c for c in CELLS if c in per]
    r1 = len(live) > len(ui3)
    print("  R1 'only the 3 UI cells are writable' -> %d cells carry stores (predicted 3) %s"
          % (len(live), "KILLED" if r1 else "survives"))
    r2 = len(nl) > 0
    print("  R2 'the INI loader is the only writer' -> %d non-loader stores (predicted 0) %s"
          % (len(nl), "KILLED" if r2 else "survives"))
    n_e8 = len(per.get(0x92BDE8, []))
    r3 = n_e8 != 1
    print("  R3 '0x92bde8 has ONE store' -> %d %s" % (n_e8, "KILLED" if r3 else "survives"))
    gate("G7a", r1 and r2 and r3, "all three rivals killed on the measured numbers")

    # ---------------- G8 boundary ----------------
    sweep = [a for a in order if 0x58EFC0 <= a <= 0x58EFE6]
    esi0 = [by[a][3] for a in sweep if by[a][2] == "mov" and "0x92bf18" in by[a][3]]
    bound = [by[a][3] for a in sweep if by[a][2] == "cmp" and "0x92bf34" in by[a][3]]
    wbsweep = [a for a in order if WRITEBACK[0] <= a < WRITEBACK[1] and by[a][3]
               and ("0x92bf18" in by[a][3] or "0x92bf34" in by[a][3])]
    print("== G8 boundary: the 7-dword `Custom World` sweep ==")
    print("  loader: %s ... %s" % (esi0, bound))
    print("  writeback mirrors it: %s" % [hex(a) for a in wbsweep])
    print("  span END 0x%x < sweep start 0x92bf18" % HI)
    gate("G8a", len(esi0) == 1 and len(bound) == 1 and len(wbsweep) >= 2 and HI < 0x92BF18,
         "the block ends at 0x92bf14; the sweep is a separate 7-dword group")

    # ---------------- G9 mutation-pin coverage ----------------
    kpush = {a for a in order if by[a][2] == "push" and by[a][3]
             and IMM.match(by[a][3].strip())
             and int(by[a][3].strip(), 16) in keytext}
    used = ({a for a, _, _, _ in stores} | {a for a, _, _ in reads}
            | {a for a, _, _ in matrefs} | kpush
            | {a for a in order if 0x58EFC0 <= a <= 0x58EFE6})
    near = set()
    for a in used:
        i = idx[a]
        for k in range(max(0, i - 2), min(len(order), i + 3)):
            near.add(order[k])
    pins = PINS if ALGO != "6" else {}
    print("== G9 mutation-pin coverage (every mutated site is read by this run) ==")
    bad = []
    for p in sorted(pins):
        ok = p in near
        if not ok:
            bad.append(p)
        print("  %-9s %-40s %s" % (hex(p), pins[p], "exercised" if ok else "NOT EXERCISED"))
    gate("G9a", len(pins) == len(PINS) and not bad,
         "%d/%d mutated sites are exercised by the census" % (len(pins) - len(bad), len(PINS)))

    # ---------------- summary ----------------
    npass = sum(1 for _, ok, _ in gates if ok)
    print("== SUMMARY ==")
    print("  cells=%d stores=%d reads=%d bounds=%d loader=%d writeback=%d non-loader=%d fns=%d"
          % (len(CELLS), len(stores), len(reads), len(bounds), len(loader_stores),
             len(wb_loads), len(nl), len({owner(a)[0] for a in nl})))
    print("  per cell (stores / writers):")
    for c in CELLS:
        nm1 = rmap[c][1] if c in rmap else "?"
        print("    0x%06x %-17s %2d  %s" % (c, nm1, len(per.get(c, [])),
                                            " ".join("%s:%s" % (hex(a), sh) for cc, a, sh in rows6
                                                     if cc == c)))
    print("  digest %s" % dig())
    print("%s M370: %d/%d gates" % ("PASS" if npass == len(gates) else "FAIL", npass, len(gates)))
    return 0 if npass == len(gates) else 1


if __name__ == "__main__":
    sys.exit(main())
