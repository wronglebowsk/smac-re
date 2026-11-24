#!/usr/bin/env python3
"""M372 - cell 0x92bf0c: `& 0x1800000` vs the INI key `Semaphore`; and the gap 0x92bdf0.

M370 left two opens: (a) 0x92bf0c serialises under the key `Semaphore` yet every
in-game store writes `x & 0x1800000` - is the cell a PACKED FIELD (bit 23/24 of a
bitset relocated to bits 0/1) or a REUSED NAME (a slot whose two occupants keep
their absolute bit positions)?  (b) 0x92bdf0 was never referenced.

Everything is COMPUTED from the static image: scratch/m574/text.txt (objdump .text),
programs/terran.exe (VA->string, address-dword and section resolution),
ghidra_out/index.csv (function spans), programs/Alpha Centauri.Ini (the game's own
shipped INI, a live text anchor for the serialised form).  Zero box time.

THE METHOD
  G1  census of the cell: text operands AND byte disp32 encodings must give the SAME
      (site,cell) set (a call's rel32 is not an address reference); partition
      STORE/READ; each site resolved to its owner function.
  G2  the WRITE side: the writeback helper 0x58f030 is disassembled for the branch its
      flag argument selects; the flag=1 branch's loop constants are READ OUT of the
      instruction stream and emulated.  The emulator must reproduce the value the
      shipped INI carries for `Semaphore` byte-for-byte.  Rival: decimal.
  G3  the READ side: the loader's parse helper is resolved per cell from the
      instruction stream (nearest 0x5ea48x call before the store); the base-2 parser
      0x628720 is emulated and must INVERT G2 for every value the cell can hold.
      Rival: one parse flavour for the whole block.
  G4  the SHAPE: every store's mask is read from its `and` prelude and its carrier is
      traced (register chain -> `ds:0x985a..` load, or call return); the restore site's
      clear-mask and whole-cell OR are read the same way.  Rival: a packed field
      (bits relocated by a shift) - measured shift count must be zero.
  G5  the NAME: every occurrence of the string `Semaphore` in the image, with the site
      that pushes it.  Rival: a UI label exists.
  G6  the occupants: every read of the two bits out of the bitset, and what follows.
  G7  the GAP 0x92bdf0: text references, address-dword occurrences in the WHOLE image
      (a pointer table would show), and every base-pointer sweep that could reach it.
      Positive controls: the same scan finds the neighbours.

M372_PATCH='addr|new text' rewrites one instruction line in memory (the mutation
harness's lever).  M372_ALGO=n flips a classifier/tracer law (see ALGO below).
"""
import hashlib
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M372_TEXT", os.path.join(ROOT, "scratch/m574/text.txt"))
IDXCSV = os.path.join(ROOT, "ghidra_out/index.csv")
EXE = os.path.join(ROOT, "programs/terran.exe")
INI = os.path.join(ROOT, "programs/Alpha Centauri.Ini")
if not os.path.exists(EXE):
    EXE = os.path.join(ROOT, "terran.exe")

CELL = 0x92BF0C                 # the cell under study
GAP = 0x92BDF0                  # M370's unreferenced hole
SPAN = (0x92BDE8, 0x92BF14)     # M370's pref block, inclusive
LOADER = (0x58E7F0, 0x58F002)   # FUN_0058e7f0  INI -> cells
WRITEBACK = (0x58F0D0, 0x58F3C6)  # FUN_0058f0d0 cells -> INI
EMIT = 0x58F030                 # 0x58f030(key, value, flag): flag=1 -> bit string
PARSE_BIN = 0x628720            # base-2 parser
PARSE_HEX = 0x62876B            # base-16 parser (the block's other flavour)
BITSETS = (0x985AC4, 0x985AE8)
MASK = 0x1800000                # the two bits the cell always carries
KEY_SEM = 0x692780              # loader key push `Semaphore`
KEY_SEM_W = 0x692848            # writeback key push `Semaphore`

# MEASURED by this run, not authored (G1..G7 assert them):
PINS = {
    "stores": 5, "reads": 3, "refs": 8,
    "loader": 0x58ECC9, "writeback_read": 0x58F2FE, "restore_read": 0x57C990,
    "struct_read": 0x48882E,
    "torch_sites": (0x4DC77C, 0x4DC8C3, 0x57CB1E, 0x57CC66),
    "bit23_readers": (0x59EF11, 0x5A1446), "bit24_readers": (0x5A1150,),
    "bit23_owners": ("FUN_0059ec90", "FUN_005a0fa0"), "bit24_owners": ("FUN_005a0fa0",),
    "shapes": {0x4DC77C: "ZERO-BY-CLEAR", 0x57CB1E: "ZERO-BY-CLEAR",
               0x4DC8C3: "LIVE-BITS", 0x57CC66: "LIVE-BITS"},
    "gap_refs": 0, "gap_dwords": 0, "sweeps": 1, "sweep_base": 0x92BF18,
    "sweep_bound": 0x92BF34, "semaphore_strings": 2,
}
# M372_ALGO mutants of the CLASSIFIER / TRACER laws:
#   1 = the disp32 scan reads the operand BIG-endian
#   2 = the store/read partition is flipped (mov mem,reg read as a LOAD)
#   3 = the formatter is forced onto the decimal branch (flag ignored)
#   4 = the parse emulator uses base 16 instead of base 2
#   5 = the carrier trace follows register-to-register moves only one hop
#   6 = the address-dword scan is misaligned by one byte
ALGO = os.environ.get("M372_ALGO", "")

LINE = re.compile(r"^\s*([0-9a-f]{6,8}):\t([0-9a-f ]+?)\s*\t(.*?)(?:\t;.*)?$")
OPS = re.compile(r"^([a-z][a-z0-9]*)\s+(.*)$")
MEMDS = re.compile(r"^(?:[A-Z]+ PTR )?ds:0x([0-9a-f]{6,8})$")
REGS = ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp", "esp")
DEFOPS = {"mov", "movzx", "movsx", "lea", "pop", "call", "and", "or", "xor",
          "add", "sub", "not", "neg", "shl", "shr", "sar", "inc", "dec"}
BRANCH = re.compile(r"^(j[a-z]+|call|ret|retn)$")

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
    patch = os.environ.get("M372_PATCH")
    pa = pt = None
    if patch:
        pa, _, pt = patch.partition("|")
        pa = int(pa.strip(), 16)
        pt = " ".join(pt.split())
    out, hit = [], False
    with open(TEXT, "r", errors="replace") as f:
        for line in f:
            m = LINE.match(line)
            if not m:
                continue
            a = int(m.group(1), 16)
            by = [int(x, 16) for x in m.group(2).split()]
            txt = " ".join(m.group(3).split())
            if a == pa:
                if txt == pt:
                    sys.stderr.write("M372_PATCH already equal at %s\n" % hex(a))
                    raise SystemExit(3)
                txt, hit = pt, True
            mo = OPS.match(txt)
            out.append((a, by, txt, mo.group(1) if mo else txt.split()[0],
                        mo.group(2) if mo else ""))
    if patch and not hit:
        sys.stderr.write("M372_PATCH %s not found in .text cache\n" % hex(pa))
        raise SystemExit(2)
    return out


def load_index():
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


def pe():
    d = open(EXE, "rb").read()
    p = struct.unpack_from("<I", d, 0x3C)[0]
    opt = p + 24
    base = struct.unpack_from("<I", d, opt + 28)[0]
    q = opt + struct.unpack_from("<H", d, p + 20)[0]
    secs = []
    for _ in range(struct.unpack_from("<H", d, p + 6)[0]):
        vs, va, rs, ra = struct.unpack_from("<IIII", d, q + 8)
        secs.append((base + va, vs, ra, rs))
        q += 40
    return d, base, secs


def pe_names():
    """(image_base+VA, vsize, name) per PE section - used to tell an instruction operand
    (inside .text) from a data pointer candidate (outside it)."""
    d = open(EXE, "rb").read()
    p = struct.unpack_from("<I", d, 0x3C)[0]
    opt = p + 24
    base = struct.unpack_from("<I", d, opt + 28)[0]
    q = opt + struct.unpack_from("<H", d, p + 20)[0]
    out = []
    for _ in range(struct.unpack_from("<H", d, p + 6)[0]):
        name = d[q:q + 8].rstrip(b"\x00").decode("latin1")
        vs, va = struct.unpack_from("<II", d, q + 8)
        out.append((base + va, vs, name))
        q += 40
    return out


def off_of(secs, va):
    for v, vs, ra, rs in secs:
        if v <= va < v + vs:
            return ra + va - v
    return None


def va_of(secs, off):
    for v, vs, ra, rs in secs:
        if ra <= off < ra + rs:
            return v + off - ra
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


def main():
    sys.stdout = _Tee(sys.__stdout__)
    ins = insns()
    order = [a for a, _, _, _, _ in ins]
    by = {a: (b, t, mn, ops) for a, b, t, mn, ops in ins}
    idx = {a: i for i, a in enumerate(order)}
    exe, base, secs = pe()
    rows = load_index()
    starts = [r[0] for r in rows]
    gates = []

    def fnof(a):
        import bisect
        i = bisect.bisect_right(starts, a) - 1
        if i < 0:
            return "?", 0, False
        ad, nm, sz = rows[i]
        return nm, ad, ad <= a < ad + sz

    def owner(a):
        nm, fa, ok = fnof(a)
        if ok:
            return nm
        i = idx[a]
        for k in range(i - 1, max(-1, i - 16), -1):
            if by[order[k]][2] in ("ret", "jmp"):
                j = k + 1
                while j < i and by[order[j]][2] == "nop":
                    j += 1
                return "SUB_%x" % order[j]
        return nm + "?"

    def gate(name, ok, msg):
        gates.append((name, bool(ok)))
        print("%-4s %-4s %s" % (name, "ok" if ok else "FAIL", msg))

    def defof(txt):
        m = OPS.match(txt)
        if not m:
            return None, None, None
        op, rest = m.group(1), m.group(2)
        if op not in DEFOPS:
            return None, None, None
        p = rest.split(",")
        dst = p[0].strip()
        src = ",".join(p[1:]).strip() if len(p) > 1 else ""
        return op, dst, src

    def memds(op):
        m = MEMDS.match(op or "")
        return int(m.group(1), 16) if m else None

    # ---------------- G0 ----------------
    print("== G0 inputs ==")
    print("  .text cache insns=%d  PE sections=%d  fn index=%d" % (len(ins), len(secs), len(rows)))
    print("  cell=0x%x  gap=0x%x  span=[0x%x,0x%x] (%d dwords)  bitsets=%s"
          % (CELL, GAP, SPAN[0], SPAN[1], (SPAN[1] - SPAN[0]) // 4 + 1,
             "/".join("0x%x" % b for b in BITSETS)))
    anchors = [EMIT, PARSE_BIN, PARSE_HEX, LOADER[0], WRITEBACK[0], 0x5EA493, 0x5EA484,
               0x58ECC9, 0x58F2FE]
    # the NAMED rotation this unit performed: the stub's sha1/size are re-computed HERE,
    # so "VERBATIM" is a measured claim and not a decorative one.
    named = open(os.path.join(ROOT, "NAMED.md"), encoding="utf-8").read()
    rot = re.search(r"## M303 .*?`(docs/named-archive-[a-z0-9-]+\.md)` \(sha1 ([0-9a-f]{16}), "
                    r"(\d+) B\)", named)
    rot_ok = False
    if rot:
        arch_txt = open(os.path.join(ROOT, rot.group(1)), encoding="utf-8").read()
        body = arch_txt.split("\n\n", 1)[1]
        rot_ok = (hashlib.sha1(body.encode()).hexdigest()[:16] == rot.group(2)
                  and len(body.encode()) == int(rot.group(3)))
        print("  rotation %s: %d B sha1 %s (stub %s/%s) match=%s"
              % (rot.group(1), len(body.encode()),
                 hashlib.sha1(body.encode()).hexdigest()[:16], rot.group(2), rot.group(3), rot_ok))
    else:
        print("  rotation stub NOT FOUND in NAMED.md")
    gate("G0", len(ins) > 200000 and len(rows) > 5000 and len(secs) >= 4
         and all(a in by for a in anchors) and rot_ok,
         "cache/index/PE resolve; %d/%d anchors in the stream; NAMED rotation sha1+size verified"
         % (sum(a in by for a in anchors), len(anchors)))
    print("  ini=%s present=%s" % (os.path.basename(INI), os.path.exists(INI)))

    # ---------------- G1 census ----------------
    def census(cell, filt=True):
        tset, bset = [], []
        pat = struct.pack(">I" if ALGO == "1" else "<I", cell)
        for a, byts, txt, mn, ops in ins:
            if memds(ops.split(",")[-1].strip()) == cell or \
               (ops.split(",")[0].strip().endswith("0x%x" % cell)):
                tset.append(a)
            raw = bytes(byts)
            i = raw.find(pat)
            if i >= 0:
                if filt and BRANCH.match(mn) and i == len(raw) - 4 and mn != "call":
                    continue
                if filt and mn == "call" and i == len(raw) - 4:
                    continue
                bset.append(a)
        return sorted(set(tset)), sorted(set(bset))

    def part(site):
        mn, ops = by[site][2], by[site][3]
        if mn != "mov":
            return "OTHER"
        p = ops.split(",")
        if ALGO == "2":                     # the partition law flipped
            if memds(p[0].strip()) is not None:
                return "READ"
            if memds(p[-1].strip()) is not None:
                return "STORE"
            return "OTHER"
        if memds(p[0].strip()) is not None:
            return "STORE"
        if memds(p[-1].strip()) is not None:
            return "READ"
        return "OTHER"

    ts, bs = census(CELL)
    print("\n== G1 census, cell 0x%x ==" % CELL)
    print("  text sites=%d  byte-disp32 sites=%d  equal=%s" % (len(ts), len(bs), ts == bs))
    for a in sorted(set(ts) | set(bs)):
        kind = part(a) if a in by else "?"
        print("   %x %-5s %-28s owner=%s%s"
              % (a, kind, by[a][1] if a in by else "?", owner(a),
                 "" if a in ts and a in bs else "  <-ONE-SIDED"))
    stores = [a for a in ts if part(a) == "STORE"]
    reads = [a for a in ts if part(a) == "READ"]
    others = [a for a in ts if part(a) == "OTHER"]
    print("  partition: STORE=%d READ=%d OTHER=%d fns=%d"
          % (len(stores), len(reads), len(others), len({owner(a) for a in ts})))
    gate("G1", ts == bs and len(stores) == PINS["stores"] and len(reads) == PINS["reads"]
         and not others and len(ts) == PINS["refs"] and PINS["loader"] in ts,
         "text set == byte set (%d sites); %d STORE / %d READ / 0 OTHER"
         % (len(ts), len(stores), len(reads)))

    # ---------------- G2 the write side ----------------
    print("\n== G2 the serialised form (writeback 0x58f0d0 -> helper 0x%x) ==" % EMIT)
    # the writeback sequence for CELL: mov <r>,ds:CELL ; push flag ; push r ; push key ; call EMIT
    seq = None
    i = idx[0x58F2FE]
    for k in range(i, i + 6):
        a = order[k]
        if by[a][2] == "call" and by[a][3].strip() == "0x%x" % EMIT:
            seq = (i, k)
            break
    flag = None
    keyva = None
    if seq:
        for k in range(seq[0], seq[1]):
            t = by[order[k]][1]
            m = re.match(r"push\s+0x([0-9a-f]+)$", t)
            if m and flag is None:
                flag = int(m.group(1), 16)
            m = re.match(r"push\s+(0x[0-9a-f]+)$", t)
            if m and keyva is None and int(m.group(1), 16) > 0x690000:
                keyva = int(m.group(1), 16)
    keytxt = cstr(exe, secs, keyva) if keyva else None
    print("  writeback read=%x  flag push=0x%x  key push=0x%x -> %r"
          % (0x58F2FE, flag or 0, keyva or 0, keytxt))

    # disassemble EMIT: which branch does flag=1 select, and what are its constants?
    ei = idx[EMIT]
    body = [order[k] for k in range(ei, ei + 64)]
    lo_br = lo_tgt = lo_site = None
    for a in body:
        mn, ops = by[a][2], by[a][3]
        if mn in ("je", "jne", "jz", "jnz") and lo_br is None:
            lo_site = a
            lo_tgt = int(ops.replace("0x", ""), 16)
            lo_br = lo_site
            break
    hi_start = lo_tgt
    bit_chunk = [a for a in body if lo_site < a < hi_start] if lo_br else []
    dec_chunk = [a for a in body if hi_start <= a < 0x58F0D0]
    hi_bit = None
    min_width = None
    one_s = zero_s = None
    for a in bit_chunk:
        mn, ops = by[a][2], by[a][3]
        m = re.match(r"(\w+),(0x[0-9a-f]+)$", ops)
        if mn == "mov" and m and m.group(1) in ("esi", "ebx") and hi_bit is None:
            hi_bit = int(m.group(2), 16)
        if mn == "cmp" and m and m.group(2) == "0x8" and min_width is None:
            min_width = 8
        if mn == "push" and re.match(r"0x[0-9a-f]+$", ops.strip()):
            v = int(ops.strip(), 16)
            s = cstr(exe, secs, v, 8)
            if s == "1" and one_s is None:
                one_s = v
            if s == "0" and zero_s is None:
                zero_s = v
    dec_arg = None
    for a in dec_chunk:
        if by[a][2] == "call" and by[a][3].strip().startswith("0x64f980"):
            dec_arg = 10
    print("  emit: flag test at 0x%x -> je 0x%x ; flag=1 block (0x%x,0x%x) ; flag=0 block [0x%x,0x58f0d0)"
          % (lo_site or 0, lo_tgt or 0, lo_site or 0, hi_start or 0, hi_start or 0))
    print("  flag=1 constants read from the stream: hi_bit=0x%x min_width=%d one=%r zero=%r"
          % (hi_bit or 0, min_width or 0, cstr(exe, secs, one_s, 4) if one_s else None,
             cstr(exe, secs, zero_s, 4) if zero_s else None))
    print("  flag=0 path: decimal converter 0x64f980 radix=%s" % (dec_arg,))

    def emit_bits(v, hi, wid):
        out, seen = [], 0
        for b in range(hi, -1, -1):
            if (v >> b) & 1:
                seen = 1
                out.append("1")
            elif seen or b < wid:
                out.append("0")
        return "".join(out)

    inivals = {}
    with open(INI, "r", errors="replace") as f:
        for line in f:
            if "=" in line:
                k, _, v = line.partition("=")
                inivals[k.strip()] = v.strip()
    ini_sem = inivals.get("Semaphore")
    use_dec = (flag == 0) or ALGO == "3"
    if use_dec:
        form = {0: "0", MASK & 0x800000: "8388608", 0x1000000: "16777216", MASK: "25165824"}
        fmt0 = "0"
    else:
        form = {v: emit_bits(v, hi_bit, min_width)
                for v in (0, 0x800000, 0x1000000, MASK)}
        fmt0 = form[0]
    print("  emulated form of the 4 reachable values: %s" % form)
    print("  shipped INI `Semaphore`=%r  emulated fm(0)=%r  match=%s  (decimal fm(0)='0')"
          % (ini_sem, fmt0, ini_sem == fmt0))
    gate("G2", flag == 1 and keytxt == "Semaphore" and hi_bit == 0x1f and min_width == 8
         and one_s == 0x6927E4 and zero_s == 0x6927E8
         and not use_dec and ini_sem is not None and ini_sem == fmt0 and len(fmt0) == 8
         and form[MASK & 0x800000] == "1" + "0" * 23,
         "flag=1 -> BINARY emitter (hi_bit=0x1f, min width 8); emulation == shipped INI %r; "
         "decimal rival produces '0' != %r" % (ini_sem, ini_sem))

    # ---------------- G3 the read side ----------------
    print("\n== G3 the parse side ==")
    # per-cell parse helper: nearest 0x5ea48x call before each loader store
    table = []
    for a in order:
        if not (LOADER[0] <= a <= LOADER[1]):
            continue
        m = re.match(r"mov\s+(?:DWORD PTR )?ds:(0x[0-9a-f]+),", by[a][1])
        if not m:
            continue
        cell = int(m.group(1), 16)
        if not (SPAN[0] <= cell <= SPAN[1]):
            continue
        helper = None
        k = idx[a] - 1
        while k >= 0 and idx[a] - k <= 40:
            t = by[order[k]][1]
            if t.startswith("call"):
                tgt = t.split()[-1]
                if tgt in ("0x5ea493", "0x5ea484"):
                    helper = int(tgt, 16)
                    break
            k -= 1
        table.append((a, cell, helper))
    kinds = {}
    for a, cell, h in table:
        kinds[h] = kinds.get(h, 0) + 1
    print("  loader stores=%d  parse helpers: %s"
          % (len(table), ", ".join("0x%x x%d" % (k, v) for k, v in sorted(kinds.items(), key=lambda z: -z[1]))))
    for a, cell, h in table:
        print("   %x -> 0x%-8x %s" % (a, cell, {0x5EA493: "base-2", 0x5EA484: "base-16"}.get(h, "?")))
    sem_helper = [h for a, c, h in table if c == CELL]
    # disassemble PARSE_BIN
    pbody = [order[k] for k in range(idx[PARSE_BIN], idx[PARSE_BIN] + 26)]
    digits, shift = [], None
    for a in pbody:
        mn, ops = by[a][2], by[a][3]
        m = re.match(r"(\w+),(0x[0-9a-f]+)$", ops)
        if mn == "cmp" and m and m.group(1) in ("ecx", "eax"):
            digits.append(chr(int(m.group(2), 16)))
        if mn == "shl" and shift is None:
            shift = int(ops.split(",")[-1], 16)
    hbody = [order[k] for k in range(idx[PARSE_HEX], idx[PARSE_HEX] + 24)]
    hshift = None
    for a in hbody:
        if by[a][2] == "shl" and hshift is None:
            hshift = int(by[a][3].split(",")[-1], 16)
    print("  parser 0x%x accepts charset=%s  shift=%s  (hex sibling 0x%x shifts %s)"
          % (PARSE_BIN, "".join(digits), shift, PARSE_HEX, hshift))
    base = 16 if ALGO == "4" else 2

    def parse(s, b):
        v = 0
        okcs = set("01") if b == 2 else set("0123456789abcdefABCDEF")
        for c in s:
            if c not in okcs:
                break
            v = v * b + int(c, b)
        return v

    rt = {v: parse(emit_bits(v, hi_bit, min_width), base)
          for v in (0, 0x800000, 0x1000000, MASK)}
    print("  round-trip (emitter -> parser): %s" % rt)
    print("  clauses: helper=%s charset=%s shift=%s hshift=%s hexcells=%d rt=%s"
          % (sem_helper == [0x5EA493], set(digits) == {"0", "1"}, shift == 1, hshift == 4,
             kinds.get(0x5EA484, 0) >= 1, rt == {v: v for v in rt}))
    gate("G3", sem_helper == [0x5EA493] and set(digits) == {"0", "1"} and shift == 1
         and kinds.get(0x5EA493) == 5 and kinds.get(0x5EA484) == 6 and len(table) == 11
         and hshift == 4 and kinds.get(0x5EA484, 0) >= 1 and rt == {v: v for v in rt}
         and parse("00000000", base) == 0 and parse("1101000001110", base) == 0b1101000001110,
         "0x%x is base-2 (%d of %d cells use it, %d use base-16 0x%x); round-trip exact; "
         "RULES string 1101000001110 -> %d" % (PARSE_BIN, kinds.get(0x5EA493, 0), len(table),
                                               kinds.get(0x5EA484, 0), PARSE_HEX,
                                               parse("1101000001110", 2)))

    # ---------------- G4 the shape ----------------
    print("\n== G4 the shape: masked copy or packed field ==")

    def trace(reg, k, depth=0):
        """Carrier trace: walk back to the definition of reg; follow mov reg,reg chains
        (bounded by ALGO 5), accumulate and/or immediates, and stop at a ds: bitset load,
        an immediate, or a call return."""
        cleared = ored = 0
        steps = 0
        hops = 0
        while k >= 0 and steps < 200:
            a = order[k]
            t = by[a][1]
            if BRANCH.match(by[a][2]) and by[a][2] != "call":
                return {"origin": "CASE-ENTRY", "cleared": cleared, "ored": ored, "site": a}
            op, dst, src = defof(t)
            if op and dst == reg:
                if op == "mov":
                    mds = re.search(r"ds:(0x[0-9a-f]{6,8})$", src)
                    if mds:
                        return {"origin": int(mds.group(1), 16), "cleared": cleared,
                                "ored": ored, "site": a}
                    if src in REGS:
                        hops += 1
                        if ALGO == "5" and hops > 0:
                            return {"origin": "CARRIED", "cleared": cleared, "ored": ored, "site": a}
                        reg = src
                        steps += 1
                        k -= 1
                        continue
                    if re.match(r"^0x[0-9a-f]+$", src):
                        return {"origin": "IMM", "val": int(src, 16), "cleared": cleared,
                                "ored": ored, "site": a}
                    return {"origin": "OTHER", "src": src, "cleared": cleared, "ored": ored, "site": a}
                if op == "and" and re.match(r"^0x[0-9a-f]+$", src):
                    cleared |= (~int(src, 16)) & 0xFFFFFFFF
                elif op == "or" and re.match(r"^0x[0-9a-f]+$", src):
                    ored |= int(src, 16)
                elif op in ("xor", "sub", "not", "shl", "shr", "sar", "lea", "movzx", "movsx"):
                    return {"origin": "COMPUTED", "op": op, "site": a, "cleared": cleared, "ored": ored}
                elif op == "call":
                    return {"origin": "CALLRET", "site": a, "cleared": cleared, "ored": ored}
                elif op == "pop":
                    return {"origin": "POP", "site": a, "cleared": cleared, "ored": ored}
            steps += 1
            k -= 1
        return {"origin": "UNKNOWN", "cleared": cleared, "ored": ored, "site": None}

    # the last write to a bitset before `upto`, and whether it provably cleared MASK
    def last_bitset_clear(bitset, upto):
        i = idx[upto]
        for k in range(i - 1, max(-1, i - 40), -1):
            a = order[k]
            op, dst, src = defof(by[a][1])
            if op == "mov" and re.search(r"ds:0x%x$" % bitset, dst or ""):
                tr = trace(src, k - 1) if src in REGS else {}
                cleared = tr.get("cleared", 0)
                return a, cleared
        return None, 0

    shapes = []
    for a in PINS["torch_sites"]:
        if a not in by:
            shapes.append((a, "MISSING", 0, {}))
            continue
        kind = part(a)
        src = by[a][3].split(",")[-1].strip()
        # 1) immediate predecessor def of the stored register = the mask
        k = idx[a] - 1
        mask = None
        while k >= 0 and idx[a] - k <= 8:
            op, dst, s2 = defof(by[order[k]][1])
            if op and dst == src:
                if op == "and":
                    mask = int(s2, 16)
                break
            k -= 1
        tr = trace(src, idx[a] - 1)
        live = (tr.get("origin") in BITSETS) or tr.get("origin") == "CALLRET"
        zero = False
        if tr.get("origin") in BITSETS:
            w, cleared = last_bitset_clear(tr["origin"], a)
            zero = (tr["origin"] == 0x985AE8 and (cleared & MASK) == MASK
                    and (tr.get("ored", 0) & MASK) == 0)
        shapes.append((a, kind, mask, {"reg": src, "origin": tr.get("origin"),
                                       "cleared": tr.get("cleared"), "ored": tr.get("ored"),
                                       "zero": zero, "live": live}))
    for a, kind, mask, info in shapes:
        print("   %x %-5s mask=%-10s reg=%s origin=%s cleared=%s ored=%-9s -> %s"
              % (a, kind, hex(mask) if mask is not None else "?",
                 info.get("reg", "?"),
                 hex(info["origin"]) if isinstance(info.get("origin"), int) else info.get("origin"),
                 hex(info.get("cleared", 0)), hex(info.get("ored", 0)),
                 "ZERO-BY-CLEAR" if info.get("zero") else "LIVE-BITS"))
    # shifts anywhere in the cell's windows
    shifts = 0
    for a in PINS["torch_sites"] + (PINS["restore_read"],):
        if a not in by:
            continue
        for k in range(idx[a] - 6, idx[a] + 6):
            if 0 <= k < len(order) and by[order[k]][2] in ("shl", "shr", "sar"):
                shifts += 1
    # the restore site: clear-mask on the bitset, then whole-cell OR
    ri = idx[PINS["restore_read"]]
    clear_mask = or_reg = None
    for k in range(ri, ri + 8):
        t = by[order[k]][1]
        m = re.match(r"and\s+(\w+),(0x[0-9a-f]+)$", t)
        if m and clear_mask is None:
            clear_mask = int(m.group(2), 16)
        m = re.match(r"or\s+(\w+),(\w+)$", t)
        if m and clear_mask is not None and or_reg is None:
            or_reg = m.group(2)
    cellreg = by[PINS["restore_read"]][3].split(",")[0].strip()
    print("   restore @%x: clear-mask=%s (== ~0x%x ? %s) ; whole-cell OR uses reg %s (cell reg %s) ? %s"
          % (PINS["restore_read"], hex(clear_mask or 0), MASK, (clear_mask or 0) == (~MASK & 0xFFFFFFFF),
             or_reg, cellreg, or_reg == cellreg))
    print("   shifts inside the cell's windows: %d" % shifts)
    direct = sum(1 for s in shapes if s[3].get("origin") in BITSETS)
    bad = [s[0] for s in shapes if s[3].get("origin") not in BITSETS + ("CASE-ENTRY",)]
    measured = {a: ("ZERO-BY-CLEAR" if info.get("zero") else "LIVE-BITS")
                for a, kind, mask, info in shapes}
    gate("G4", all(s[2] == MASK for s in shapes) and shifts == 0 and direct >= 2 and not bad
         and clear_mask == (~MASK & 0xFFFFFFFF) and or_reg == cellreg
         and measured == PINS["shapes"],
         "all %d in-game stores mask exactly 0x%x with NO shift (2 write a provably-zero value, 2 "
         "carry live bits; %d carriers are the bitsets themselves); restore clears ~0x%x then ORs the "
         "whole cell -> the cell is a bit-shadow of 0x985ae8 bits 23/24, not a packed field"
         % (len(shapes), MASK, direct, MASK))

    # ---------------- G5 the name ----------------
    print("\n== G5 the name ==")
    # EVERY occurrence of the C string in the WHOLE image (file bytes, then mapped):
    hits, pos = [], exe.find(b"Semaphore\x00")
    while pos >= 0:
        va = va_of(secs, pos)
        if va is not None and (pos == 0 or exe[pos - 1] == 0):
            hits.append(va)
        pos = exe.find(b"Semaphore\x00", pos + 1)
    # EVERY reference to those addresses: any mnemonic (push/mov/lea/cmp), not just push,
    # plus any 4-byte dword anywhere in the image (a dialog/table pointer would show).
    uses, dwords, textdw = [], 0, 0
    names = pe_names()
    for va in hits:
        pat = struct.pack("<I", va)
        q = exe.find(pat)
        while q >= 0:
            dva = va_of(secs, q)
            sec = next((nm for v0, vs0, nm in names if v0 <= (dva or 0) < v0 + vs0), "?")
            if sec.startswith(".text"):
                textdw += 1          # an instruction's own imm32 (the push we already count)
            else:
                dwords += 1          # a data pointer / table entry - would be a second consumer
            q = exe.find(pat, q + 1)
        for a2, _, txt2, mn2, ops2 in ins:
            if ("0x%x" % va) in ops2:
                uses.append((va, a2, owner(a2), mn2))
    print("  image-wide C-string occurrences of \"Semaphore\": %d at %s"
          % (len(hits), [hex(h) for h in hits]))
    for va, a2, ow, mn2 in uses:
        print("   referenced at %x (%s) in %s" % (a2, mn2, ow))
    print("  address-dword occurrences: .text imm32=%d (the two pushes) ; data/table=%d" % (textdw, dwords))
    gate("G5", len(hits) == PINS["semaphore_strings"] and len(uses) == len(hits) and dwords == 0
         and {u[2] for u in uses} == {owner(0x58ECC9), owner(0x58F2FE)}
         and {u[3] for u in uses} == {"push"} and textdw == len(hits),
         "%d image-wide string occurrences, each referenced exactly ONCE (a push) by the loader and "
         "the writeback; 0 data/table pointer entries -> no other consumer" % len(hits))

    # ---------------- G6 the occupants ----------------
    print("\n== G6 who reads bits 23/24 of 0x985ae8 ==")
    # Four idioms are recognised, so the census is not an artefact of one encoding:
    #   (a) test/and/bt/cmp against the bit imm with a DIRECT ds:0x985ae8 operand
    #   (b) the same, carrying the bitset in a register loaded within the block
    #   (c) `shr reg,23|24` (or bt reg,23|24) after such a load, then a mask of 1
    #   (d) an immediate test on a register whose last def is that load
    SHIFTS = {0x800000: 23, 0x1000000: 24}

    def readers_for(bit):
        out = []
        for i, (a2, _, txt2, mn2, ops2) in enumerate(ins):
            if mn2 in ("test", "and", "bt", "cmp") and re.search(r"0x%x\b" % bit, ops2) \
                    and "ds:0x985ae8" in ops2:
                out.append((a2, "direct-" + mn2))
                continue
            if "ds:0x985ae8" not in txt2:
                continue
            m = re.match(r"mov\s+(\w+),\s*(?:DWORD PTR )?ds:0x985ae8", txt2)
            if not m:
                continue
            reg = m.group(1)
            for k in range(i + 1, min(len(ins), i + 12)):
                t3, mn3, ops3 = ins[k][2], ins[k][3], ins[k][4]
                if mn3 in ("test", "and", "bt", "cmp") and re.search(r"0x%x\b" % bit, ops3) \
                        and re.search(r"\b%s\b" % reg, ops3):
                    out.append((ins[k][0], "reg-" + mn3))
                    break
                if mn3 in ("shr", "sar", "bt") and ops3.strip() == "%s,0x%x" % (reg, SHIFTS[bit]):
                    out.append((ins[k][0], "shift-" + mn3))
                    break
                mb = re.match(r"^(\w+)\s+%s\b," % reg, t3)   # the carrier is redefined?
                if mb and mb.group(1) in DEFOPS:
                    break
        return sorted(set(out))

    found = {b: readers_for(b) for b in SHIFTS}
    for b in found:
        print("   bit 0x%-8x readers: %s" % (b, ["0x%x(%s)" % (x, idiom) for x, idiom in found[b]]))
    own = {b: tuple(owner(x) for x, _ in found[b]) for b in found}
    for b in found:
        print("   bit 0x%-8x owner fns: %s" % (b, list(own[b])))
    print("   bit23 @0x59ef11 -> %s" % " | ".join(by[a2][1] for a2 in order[idx[0x59EF11]:idx[0x59EF11] + 7]))
    print("   bit24 @0x5a1150 -> %s" % " | ".join(by[a2][1] for a2 in order[idx[0x5A1150]:idx[0x5A1150] + 4]))
    gate("G6", tuple(x for x, _ in found[0x800000]) == PINS["bit23_readers"]
         and tuple(x for x, _ in found[0x1000000]) == PINS["bit24_readers"]
         and own[0x800000] == PINS["bit23_owners"] and own[0x1000000] == PINS["bit24_owners"],
         "bit 23 read at %s, bit 24 at %s (owners %s / %s); every reader sits in the "
         "game-start initialiser or the new-game faction setup"
         % (", ".join("0x%x" % x for x, _ in found[0x800000]),
            ", ".join("0x%x" % x for x, _ in found[0x1000000]),
            "/".join(own[0x800000]), "/".join(own[0x1000000])))

    # ---------------- G7 the gap ----------------
    print("\n== G7 the gap 0x%x ==" % GAP)
    gap_text = [a for a, _, txt, mn, ops in ins
                if "0x%x" % GAP in ops]
    endian = ">" if ALGO == "6" else "<"   # A6: the dword scan byte-swapped
    pat = struct.pack(endian + "I", GAP)
    gap_dw, gap_data, gap_aligned = [], [], []
    secnames = pe_names()
    pos = exe.find(pat)
    while pos >= 0:
        dv = va_of(secs, pos)
        gap_dw.append(dv or pos)
        sec = next((nm for v0, vs0, nm in secnames if v0 <= (dv or 0) < v0 + vs0), "?")
        if not sec.startswith(".text"):
            gap_data.append((pos, dv, sec))
            if dv is not None and dv % 4 == 0:
                gap_aligned.append((pos, dv, sec))
        pos = exe.find(pat, pos + 1)
    ctl = {}
    for name, tgt in (("cell", CELL), ("neighbour", 0x92BDE8)):
        p2 = struct.pack(endian + "I", tgt)
        n, q = 0, exe.find(p2)
        while q >= 0:
            n += 1
            q = exe.find(p2, q + 1)
        ctl[name] = n
    sweeps = []
    for i, (a, byts, txt, mn, ops) in enumerate(ins):
        m = re.match(r"mov\s+(\w+),(0x[0-9a-f]+)$", txt)
        if not m or mn != "mov":
            continue
        v = int(m.group(2), 16)
        if not (SPAN[0] <= v <= 0x92BF34):
            continue
        reg = m.group(1)
        step = bound = None
        for k in range(i + 1, min(len(ins), i + 14)):
            t2 = ins[k][2]
            m2 = re.match(r"add\s+%s,(0x[0-9a-f]+)$" % reg, t2)
            if m2 and step is None:
                step = int(m2.group(1), 16)
            m2 = re.match(r"cmp\s+%s,(0x[0-9a-f]+)$" % reg, t2)
            if m2 and step is not None:
                bound = int(m2.group(1), 16)
                break
        if step and bound:
            sweeps.append((a, v, step, bound, (bound - v) // step))
    print("  text references to 0x%x: %d" % (GAP, len(gap_text)))
    print("  address-dword occurrences, MOST PERMISSIVE scan (every byte offset, every section,"
          " one-byte alignment): %d ; outside .text: %d ; 4-aligned outside .text: %d"
          % (len(gap_dw), len(gap_data), len(gap_aligned)))
    print("  positive controls on the same scan: 0x%x=%d, 0x%x=%d (their .text hits are the"
          " instruction operands G1 already censuses)" % (CELL, ctl["cell"], 0x92BDE8, ctl["neighbour"]))
    for a, v, step, bound, n in sweeps:
        print("  base-pointer sweep at %x: [0x%x, 0x%x) step 0x%x -> %d dwords, covers 0x%x ? %s"
              % (a, v, bound, step, n, GAP, v <= GAP < bound))
    gate("G7", not gap_text and not gap_dw and not gap_data and not gap_aligned
         and ctl["cell"] == PINS["refs"]
         and ctl["neighbour"] == 11 and len(sweeps) == PINS["sweeps"]
         and sweeps[0][1] == PINS["sweep_base"] and sweeps[0][3] == PINS["sweep_bound"]
         and not any(s[1] <= GAP < s[3] for s in sweeps),
         "0x%x: 0 text refs and 0 address dwords under the most permissive scan (every offset, "
         "every section) - so no aligned pointer table can hide one; the only sweep in the region "
         "starts at 0x%x and stops at 0x%x, above it"
         % (GAP, PINS["sweep_base"], PINS["sweep_bound"]))

    # ---------------- verdict ----------------
    print("\n== VERDICT ==")
    print("  The cell is a BIT STRING slot, not a packed field: its bits keep their")
    print("  absolute positions 23/24 (no shift anywhere), the writer emits a binary")
    print("  digit string (min width 8) and the loader parses one back.  The shipped")
    print("  INI's `Semaphore=%s` is that string for value 0.  The name is the INI" % ini_sem)
    print("  KEY; the string is never used as a UI label (G5).  Occupants: bits 23")
    print("  (2 readers) and 24 (1 reader) of 0x985ae8; every read sits in the")
    print("  game-start / new-game path (G6).")
    ok = all(o for _, o in gates)
    print("\n%s M372: %d/%d gates digest %s"
          % ("PASS" if ok else "FAIL", sum(1 for _, o in gates if o), len(gates), dig()))
    print("  evidence: evidence/m372_semaphore_cell.txt")
    if not ok:
        print("  RED gates: %s" % [n for n, o in gates if not o])
        raise SystemExit(1)


if __name__ == "__main__":
    main()
