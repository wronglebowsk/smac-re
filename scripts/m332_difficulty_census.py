#!/usr/bin/env python3
"""M332 — ds:0x985aec: the difficulty dword's NOUN and its complete STORE set.

PICK: NEXT_PROMPT.md (x2). Prior footing: `NAMED ## M308` row (`:1075`): "68 refs
(mov 44 / cmp 24), 0 arithmetic, compared ONLY against {1,2,3,4}, exactly 4
writers, 2 mirror ds:0x92bde8, 1 fed by movsx BYTE ds:0x8f0c11, 0x4ddcf1
UNATTRIBUTED — which option it encodes: OPEN"; `NAMED ## M330` G2/G4-6 (the
upkeep refund k-table reads it); `NAMED ## B27` (the k-table branch shape).

Every number below is COMPUTED from the static image (scratch/m574/text.txt =
objdump .text, terran.exe = the PE for VA-mapped string extraction,
ghidra_out/*.c = the independent decompiler view). Zero box time.

GATES (printed first, then asserted; every one has a named mutant in
scripts/m332_mutate.py):
  G1  reference census + ENCODING equivalence: the text grep set and the
      byte-level displacement scan set are the SAME instruction set, and no
      instruction materializes the address (mov/lea of the immediate) => the
      direct-reference set is complete, so "who writes it" is decidable.
  G2  the STORE set is exact (addresses + opcode form + containing function).
  G3  fall-in qualifier per store: is the preceding .text instruction a ret/jmp
      (no fall-through) and does ANY branch target the site => a writer count
      that is only defensible per-site, not per-path. RETAINS M308's "4 writers"
      but REFINES what "writer" means.
  G4  the copy map of the prefs block into the runtime band, built mechanically
      (load-reg-then-store-reg with no intervening clobber) => the mirror law is
      a computed pair, not a proximity claim.
  G5  the PREFERENCES NAME -> FIELD map, read side: every push of a name string
      (VA resolved from the PE) + its arg-count-classified call, paired with the
      first field store after that call; the map must be INJECTIVE (two names
      cannot share a field) for the pairing to discriminate anything.
  G6  the write side of the same table, independently paired, must agree with
      the read side by NAME TEXT (different string VAs, same text) on the field
      that carries "Difficulty". Two sites, one field.
  G7  the NOUN: ds:0x92bde8 is the field the game itself names "Difficulty"
      (G5+G6) and ds:0x985aec is its runtime mirror (G2/G4) => 0x985aec = the
      Difficulty preference. Plus the sibling fields the same map names, which
      patch NAMED ## M328's 0x92bdf8 row.
  G8  the RIVAL, measured and killed: "ds:0x92bde8 is not a field at all — it
      is the end-of-array sentinel of the stride-0xd4 record array (the
      `add edi,0xd4 ; cmp edi,0x92bde8 ; jl` loop at 0x579bc6), so the mirror
      claim is an offset coincidence". Numbers decide.
"""
import bisect
import hashlib
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
IDXCSV = os.path.join(ROOT, "ghidra_out/index.csv")
SHARDS = os.path.join(ROOT, "ghidra_out")
EXE = os.path.join(ROOT, "terran.exe")

TARGET = 0x985AEC          # the runtime dword under study
MASTER = 0x92BDE8          # the dword the two mirrors load from
BYTECELL = 0x8F0C11        # the byte cell fed by / feeding both
NAMEBAND = (0x6926B0, 0x692880)   # the .data block holding the pref name strings
# Declared sets the measurement must reproduce EXACTLY (measured == declared,
# both directions; this is also where a code mutant's address is read literally).
STORE_SET = {0x4DDCF1, 0x57C5AF, 0x57C7B5, 0x57F006}
COPY_SITES = {(MASTER, BYTECELL): [(0x484EF8, 0x484EFE), (0x488822, 0x488828)],
              (TARGET, BYTECELL): [(0x485028, 0x48502E)],
              (BYTECELL, 0x8F0090): [(0x488847, 0x48884D)],
              (MASTER, TARGET): [(0x57C59E, 0x57C5AF)],
              (BYTECELL, TARGET): [(0x57EFF3, 0x57F006)]}
PREF_PIN = {"Difficulty": (0x58E8A1, 0x58E8C6), "Map Type": (0x58E905,),
            "WRITE Difficulty": (0x58F159, 0x58F11D)}
REGS = ("eax", "ecx", "edx", "ebx", "esi", "edi", "ebp", "esp")

# M332_ALGO mutants of the SCANNER laws:
#   1 = the WRITE-side window uses the READ anchor (the direction law is off)
#   2 = the clean-copy rule never kills a register's provenance (liveness off)
#   3 = the encoding cross-check scans the displacement BIG-ENDIAN (proves G1
#       reads the bytes, not the objdump text it just matched)
ALGO = os.environ.get("M332_ALGO", "")

LINE = re.compile(r"^\s*([0-9a-f]{6,8}):\t([0-9a-f ]+?)\s*\t(.*?)(?:\t;.*)?$")
OPS = re.compile(r"^([a-z][a-z0-9]*)\s+(.*)$")
DSFORM = re.compile(r"\bds:0x([0-9a-f]{6,8})")
MOVTO = re.compile(r"^mov\s+ds:0x([0-9a-f]+),(\w+)$")


def insns():
    """Reads the .text dump.  M332_PATCH='addr|new text' rewrites ONE line in
    memory — the mutation harness's only lever on the instrument."""
    patch = os.environ.get("M332_PATCH")
    pa = pt = None
    if patch:
        pa, _, pt = patch.partition("|")
        pa = int(pa.strip(), 16)
    out = []
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
                    sys.stderr.write("M332_PATCH already equal at %s\n" % patch)
                    raise SystemExit(3)
                txt = pt
            mo = OPS.match(txt)
            out.append((a, by, txt, mo.group(1) if mo else txt.split()[0],
                        mo.group(2) if mo else ""))
    if patch and pa not in {x[0] for x in out}:
        sys.stderr.write("M332_PATCH %s not in .text cache\n" % patch)
        raise SystemExit(2)
    return out


def load_fn_index():
    rows = []
    with open(IDXCSV) as f:
        head = f.readline().strip().split(",")
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            d = dict(zip(head, line.rstrip("\n").split(",")))
            try:
                rows.append((int(d["addr"], 16), d["name"], int(d["size_bytes"])))
            except ValueError:
                pass
    rows.sort()
    return rows


ROWS = load_fn_index()
STARTS = [r[0] for r in ROWS]


def fnof(a):
    i = bisect.bisect_right(STARTS, a) - 1
    if i < 0:
        return ("?", 0, 0)
    addr, name, size = ROWS[i]
    return (name, addr, size)


def fnrange(a):
    name, addr, size = fnof(a)
    return (addr, addr + size) if size else (a, a)


def pe_sections():
    d = open(EXE, "rb").read()
    import struct
    pe = struct.unpack_from("<I", d, 0x3C)[0]
    opt = pe + 24
    imgbase = struct.unpack_from("<I", d, opt + 28)[0]
    p = opt + struct.unpack_from("<H", d, pe + 20)[0]
    secs = []
    for i in range(struct.unpack_from("<H", d, pe + 6)[0]):
        vs, va, rs, ra = struct.unpack_from("<IIII", d, p + 8)
        secs.append((imgbase + va, vs, ra, rs))
        p += 40
    return d, imgbase, secs


def va_of(d, secs, off):
    for va, vs, ra, rs in secs:
        if ra <= off < ra + rs:
            return va + (off - ra)
    return None


def off_of(d, secs, va):
    for v, vs, ra, rs in secs:
        if v <= va < v + vs:
            return ra + (va - v)
    return None


def pref_names(d, secs):
    """NUL-terminated ASCII inside NAMEBAND -> {va: text}."""
    out = {}
    lo = off_of(d, secs, NAMEBAND[0])
    hi = off_of(d, secs, NAMEBAND[1] - 1) + 1
    cur, start = b"", lo
    for o in range(lo, hi + 1):
        b = d[o]
        if 32 <= b < 127:
            if not cur:
                start = o
            cur += bytes([b])
        else:
            if len(cur) >= 3:
                out[va_of(d, secs, start)] = cur.decode("ascii")
            cur = b""
    return {k: v for k, v in out.items() if v.strip()}


MEM = re.compile(r"^(?:([A-Z]+) PTR )?ds:0x([0-9a-f]{6,8})$")
IMM = re.compile(r"^0x([0-9a-f]{1,8})$")
SUBREG = {}
for _full, _subs in (("eax", ("eax", "ax", "al", "ah")), ("ecx", ("ecx", "cx", "cl", "ch")),
                     ("edx", ("edx", "dx", "dl", "dh")), ("ebx", ("ebx", "bx", "bl", "bh")),
                     ("esi", ("esi", "si", "sil")), ("edi", ("edi", "di", "dil")),
                     ("ebp", ("ebp", "bp", "bpl")), ("esp", ("esp", "sp", "spl"))):
    for _s in _subs:
        SUBREG[_s] = _full
CLOBBERS = {"eax", "ecx", "edx"}


def split_ops(ops):
    """-> (dst, src) text operands of a two-operand instruction, or (None, None)."""
    parts = ops.split(",")
    if len(parts) < 2:
        return (parts[0].strip() if parts and parts[0].strip() else None), None
    return parts[0].strip(), ",".join(parts[1:]).strip()


def mem_of(op):
    if op is None:
        return None
    m = MEM.match(op)
    return int(m.group(2), 16) if m else None


def reg_of(op):
    if op is None:
        return None
    return SUBREG.get(op)


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


def main():
    sys.stdout = _Tee(sys.__stdout__)
    ins = insns()
    by_addr = {a: (b, t, mn, ops) for a, b, t, mn, ops in ins}
    order = [a for a, _, _, _, _ in ins]
    idx = {a: i for i, a in enumerate(order)}
    exe, imgbase, secs = pe_sections()

    # ---------- branch-target set (for G3 reachability) ----------
    branch_targets = {}
    for a, b, t, mn, ops in ins:
        if mn.startswith("j") or mn == "call":
            # ONE operand: the target text is the whole operand string (objdump
            # prints absolute addresses for rel8/rel32).  split_ops() would put
            # it in `dst` and leave src None — using src silently finds nothing.
            m = IMM.match((ops or "").strip())
            if m:
                branch_targets.setdefault(int(m.group(1), 16), []).append(a)

    # ---------- G1: reference census + encoding equivalence ----------
    le = ["%02x" % x for x in (TARGET & 0xFF, (TARGET >> 8) & 0xFF,
                               (TARGET >> 16) & 0xFF, (TARGET >> 24) & 0xFF)]
    textrefs, encrefs, matrefs = [], [], []
    for a, b, t, mn, ops in ins:
        if "ds:0x%x" % TARGET in t:
            textrefs.append(a)
        elif "0x%x" % TARGET in t:
            matrefs.append((a, t))
        key = " ".join(le[::-1]) if ALGO == "3" else " ".join(le)
        if " ".join(b).find(key) >= 0 or " ".join(b) == key:
            encrefs.append(a)
    part = {"store": [], "load": [], "cmp": [], "rmw": [], "other": []}
    for a in textrefs:
        b, t, mn, ops = by_addr[a]
        dst, src = split_ops(ops)
        if mn == "cmp":
            part["cmp"].append(a)
        elif mn in ("add", "sub", "and", "or", "xor", "inc", "dec", "neg", "not",
                    "shl", "shr", "sar", "xchg"):
            part["rmw"].append(a)
        elif mn in ("mov", "movsx", "movzx", "movbe") and mem_of(dst) == TARGET:
            part["store"].append(a)
        elif mn in ("mov", "movsx", "movzx", "push", "test"):
            part["load"].append(a)
        else:
            part["other"].append((a, t))
    print("== G1 reference census ds:0x%x ==" % TARGET)
    print("  text-form refs %d  byte-enc refs %d  set-identical %s" %
          (len(textrefs), len(encrefs), sorted(textrefs) == sorted(encrefs)))
    print("  address-materialization forms (mov/lea/push of the immediate): %d %s" %
          (len(matrefs), [hex(a) for a, _ in matrefs][:6]))
    print("  partition: store=%d load=%d cmp=%d rmw=%d other=%d" %
          tuple(len(part[k]) for k in ("store", "load", "cmp", "rmw", "other")))
    cmps = sorted({split_ops(by_addr[a][3])[1] for a in part["cmp"]})
    print("  cmp operands: %s" % cmps)

    # ---------- G2: the store set ----------
    print("== G2 store set ==")
    for a in part["store"]:
        b, t, mn, ops = by_addr[a]
        nm, fa, sz = fnof(a)
        print("  %-9s %-30s bytes=%-16s fn=%s @0x%x+0x%x" %
              (hex(a), t, " ".join(b), nm, fa, sz))

    # ---------- G3: fall-in qualifier per store ----------
    print("== G3 per-site fall-in ==")
    fallin = {}
    for a in part["store"]:
        i = idx[a]
        prev = order[i - 1] if i else None
        ptxt = by_addr[prev][1] if prev is not None else "?"
        hit = branch_targets.get(a, [])
        mn = by_addr[prev][2] if prev is not None else "?"
        state = "FALL-IN" if mn not in ("ret", "jmp", "hlt") else "no-fall-in(%s)" % mn
        fallin[a] = (state, len(hit), [hex(x) for x in hit][:4])
        print("  %s  prev=%s(%s)  %s  branch-targets=%d %s" %
              (hex(a), hex(prev) if prev is not None else "-", ptxt, state, len(hit),
               [hex(x) for x in hit][:4]))

    # ---------- G4: mechanical clean-copy map across the cells ----------
    # rule: live[reg] = (cell, load-site) while the ONLY thing that has touched
    # reg since is that load; a store `mov ds:cell2, reg` with live[reg] = cell1
    # and cell1 != cell2 is a computed cell1->cell2 copy.  Any write to reg (or
    # a call, for caller-saved regs) kills it, so a reported copy can only be
    # real if the load and the store are in one straight line of code.
    cells = {TARGET, MASTER, BYTECELL, 0x8F0090}
    cellrefs = [a for a, b, t, mn, ops in ins
                  if any("ds:0x%x" % c in t for c in cells)]
    fns = sorted(set(fnrange(a) for a in cellrefs))
    copies = []
    for (lo, hi) in fns:
        i0 = bisect.bisect_left(order, lo)
        i1 = bisect.bisect_left(order, hi)
        live = {}
        for a in order[i0:i1]:
            b, t, mn, ops = by_addr[a]
            dst, src = split_ops(ops)
            dmem, smem = mem_of(dst), mem_of(src)
            dreg, sreg = reg_of(dst), reg_of(src)
            if mn == "mov" and dmem in cells and sreg and sreg in live and live[sreg][0] != dmem:
                copies.append((live[sreg][0], dmem, live[sreg][1], a, "reg"))
            if mn == "mov" and dmem in cells and smem in cells and dmem != smem:
                copies.append((smem, dmem, a, a, "mem2mem"))
            if mn == "call" or mn.startswith("rep"):
                if ALGO != "2":            # MU14: forget the clobber law
                    for r in CLOBBERS:
                        live.pop(r, None)
                continue
            if dreg:
                if ALGO != "2":            # MU14: provenance survives redefinition
                    live.pop(dreg, None)
                if smem in cells and mn in ("mov", "movsx", "movzx"):
                    live[dreg] = (smem, a)
    print("== G4 clean-copy map among %s ==" % sorted(hex(c) for c in cells))
    seen = set()
    for s, d, ss, ds, how in copies:
        k = (s, d, ss, ds)
        if k in seen:
            continue
        seen.add(k)
        print("  %s -> %s   (load %s, store %s, %s)" % (hex(s), hex(d), hex(ss), hex(ds), how))

    # ---------- pref name strings + push sites ----------
    names = pref_names(exe, secs)
    namepos = {}
    for a, b, t, mn, ops in ins:
        if mn != "push":
            continue
        m = IMM.match((ops or "").strip())
        if not m:
            continue
        v = int(m.group(1), 16)
        if v in names and NAMEBAND[0] <= v < NAMEBAND[1]:
            namepos.setdefault(a, []).append(v)

    # classify every name-push by the call that consumes it (cdecl arg count =
    # the run of pushes immediately before the call).  6 = GetPrivateProfileStringA
    # (section,key,default,buf,size,file); 4 = WritePrivateProfileStringA
    # (section,key,string,file).  Anything else is a format-string/other use.
    callsites = [a for a, b, t, mn, ops in ins if mn == "call"]
    cpos = {a: i for i, a in enumerate(callsites)}
    pushes_sorted = sorted(namepos)
    use = []
    for a in pushes_sorted:
        j = bisect.bisect_left(callsites, a)
        call = callsites[j] if j < len(callsites) else None
        if call is None or call - a > 64:
            use.append((a, None, 0, None))
            continue
        i = idx[call]
        argc = 0
        k = i - 1
        while k >= 0 and by_addr[order[k]][2] == "push":
            argc += 1
            k -= 1
        # no other call may sit between the push run and the call
        if any(a < c < call for c in callsites):
            use.append((a, call, -1, None))
        else:
            kind = "READ" if argc == 6 else ("WRITE" if argc == 4 else "other")
            use.append((a, call, argc, kind))
    reads = [(a, names[namepos[a][0]], c) for a, c, n, k in use if k == "READ"]
    writes = [(a, names[namepos[a][0]], c) for a, c, n, k in use if k == "WRITE"]
    print("== pref-name push sites: %d pushes, %d READ(6-arg), %d WRITE(4-arg), "
          "%d other ==" % (len(use), len(reads), len(writes),
                           len(use) - len(reads) - len(writes)))

    def band(x):
        return NAMEBAND[0] <= x < NAMEBAND[1]

    def window(lo, hi, want):
        """globals STORED in [lo,hi) ('store') or LOADED in [lo,hi) ('load'),
        outside the pref-name band.  A load is a mov whose dst is a register."""
        out = []
        i0 = bisect.bisect_left(order, lo)
        i1 = bisect.bisect_left(order, hi)
        for a in order[i0:i1]:
            b, t, mn, ops = by_addr[a]
            if mn not in ("mov", "movsx", "movzx"):
                continue
            dst, src = split_ops(ops)
            dmem, smem = mem_of(dst), mem_of(src)
            if want == "store":
                g = dmem
            else:
                if dmem is not None or reg_of(dst) is None:
                    continue
                g = smem
            if g is not None and not band(g):
                out.append((g, a))
        return out

    def pairing(items, want, anchor):
        """name -> candidate fields in its window; then the EXCLUSIVE field.
        anchor='after'  (READ side)  : a field store belongs to the call that
                                       PRECEDES it -> window = [this call, next push)
        anchor='before' (WRITE side) : the value is formatted BEFORE the key push
                                       -> window = [previous call, this push)"""
        res, where = {}, {}
        for n, (a, name, call) in enumerate(items):
            lo = call if anchor == "after" else (items[n - 1][2] if n else a - 0x400)
            hi = (items[n + 1][0] if n + 1 < len(items) else a + 0x400) if anchor == "after" else a
            hits = window(lo, hi, want)
            res[name] = sorted({g for g, _ in hits})
            per = {}
            for g, sa in hits:
                per.setdefault(g, []).append(sa)
            where[name] = per
        from collections import Counter
        cnt = Counter(f for v in res.values() for f in v)
        return res, {k: [f for f in v if cnt[f] == 1] for k, v in res.items()}, where

    rc, rex, rwh = pairing(reads, "store", "after")
    wc, wex, wwh = pairing(writes, "load", "after" if ALGO == "1" else "before")
    print("-- READ side: name -> fields stored in its window -> exclusive --")
    for k in sorted(rc):
        print("   %-18s cand=%s excl=%s" % (k, [hex(x) for x in rc[k]],
                                            [hex(x) for x in rex[k]]))
    print("-- WRITE side: name -> fields loaded before its call -> exclusive --")
    for k in sorted(wc):
        print("   %-18s cand=%s excl=%s" % (k, [hex(x) for x in wc[k]],
                                            [hex(x) for x in wex[k]]))
    both = sorted(set(rex) & set(wex))
    agree = {k for k in both if set(rex[k]) & set(wex[k])}
    print("-- both-sides names=%d  agreeing on at least one field=%d  %s" %
          (len(both), len(agree), sorted(agree)))
    print("   Difficulty read-excl=%s write-excl=%s" %
          ([hex(x) for x in rex.get("Difficulty", [])],
           [hex(x) for x in wex.get("Difficulty", [])]))

    # ---------- decompiler view (s312 review: PER FUNCTION, `==`-safe) ----------
    # #346 P2: the s311 map merged the two function bodies, so "the pseudocode
    # pairs it a third way" could have been the writer polluting the reader.  The
    # map is now keyed per function; the THIRD VIEW is the reader's OWN body, and
    # the writer's body is printed separately so "it adds no exclusive field" is
    # a measurement, not a merge.  `(?<![=!<>])...=(?!=)` excludes `==`/`!=` so a
    # comparison can no longer masquerade as an assignment.  GH counts Ghidra's
    # own RESOLVED API calls per body — G9.5 cross-checks them against the
    # push-run arity counts, which is the only thing that makes the API names in
    # the prose measured rather than assumed.
    de_per = {}
    GH = {}
    for shard in sorted(os.listdir(SHARDS)):
        if not shard.endswith(".c"):
            continue
        txt = open(os.path.join(SHARDS, shard), errors="replace").read()
        for fname in ("FUN_0058e7f0", "FUN_0058f0d0"):
            m = re.search(r"// ==== %s @[^\n]*\n(.*?)(?=\n// ==== |\Z)" % fname, txt, re.S)
            if not m:
                continue
            body = m.group(1)
            gh = GH.setdefault(fname, {"Get": 0, "Write": 0})
            gh["Get"] += len(re.findall(r"GetPrivateProfileStringA\s*\(", body))
            gh["Write"] += len(re.findall(r"WritePrivateProfileStringA\s*\(", body))
            per = de_per.setdefault(fname, {})
            pend = None
            for line in body.splitlines():
                nm = re.search(r"\bs_([A-Za-z0-9_ ]+?)_(00[0-9a-f]{6})\b", line)
                if nm and int(nm.group(2), 16) in names:
                    pend = names[int(nm.group(2), 16)]
                asg = re.search(r"(?<!_)(?<![=!<>])DAT_(00[0-9a-f]{6})\s*=(?!=)", line)
                if asg and pend is not None:
                    per.setdefault(pend, set()).add(int(asg.group(1), 16))
    for fname in sorted(de_per):
        print("== decompiler map, body %s: %d names, GetPrivateProfileStringA=%d, "
              "WritePrivateProfileStringA=%d ==" % (fname, len(de_per[fname]),
                                                    GH[fname]["Get"], GH[fname]["Write"]))
    de = de_per["FUN_0058e7f0"]
    dwr = de_per.get("FUN_0058f0d0", {})
    from collections import Counter as _C
    wr_cnt = _C(f for v in dwr.values() for f in v)
    wr_ex = {k: sorted(x for x in v if wr_cnt[x] == 1) for k, v in dwr.items()}
    print("   the WRITER body alone contributes %d exclusive name->field pairs %s "
          "(so the third view is the reader's own body, not a merge of both)" %
          (sum(1 for v in wr_ex.values() if v),
           {k: [hex(x) for x in v] for k, v in sorted(wr_ex.items()) if v}))
    decnt = _C(f for v in de.values() for f in v)
    deex = {k: sorted(f for f in v if decnt[f] == 1) for k, v in de.items()}
    print("-- DECOMPILER side: name -> DAT assigned after its call -> exclusive --")
    for k in sorted(de):
        print("   %-18s cand=%s excl=%s" % (k, sorted(hex(x) for x in de[k]),
                                            sorted(hex(x) for x in deex[k])))
    tri = sorted(set(rex) & set(wex) & set(deex))
    agree3 = [k for k in tri if rex[k] and wex[k] and deex[k]
              and set(rex[k]) == set(wex[k]) == set(deex[k])]
    print("-- three-way names=%d fully agreeing=%d %s" % (len(tri), len(agree3), agree3))

    # ---------- G3b: image-wide LE-dword occurrences (jump-table reach) ----------
    print("== G3b per-site reachability triple ==")
    sites = part["store"] + [0x57C7B0]
    for a in sites:
        pat = struct.pack("<I", a)
        n = exe.count(pat)
        i = idx[a]
        prev = order[i - 1]
        pmn = by_addr[prev][2]
        print("  %-9s prev=%s(%s) branch-targets=%d table-entries=%d" %
              (hex(a), hex(prev), by_addr[prev][1], len(branch_targets.get(a, [])), n))

    # ---------- G8 rival: is MASTER only an array-end sentinel? ----------
    enduses = []
    for a, b, t, mn, ops in ins:
        if mn != "cmp":
            continue
        dst, src = split_ops(ops)
        m = IMM.match((src or "").strip())
        if m and int(m.group(1), 16) == MASTER:
            enduses.append(a)
    print("== G8 the array-end rival ==")
    print("  MASTER used as a cmp IMMEDIATE (loop bound) at: %s" % [hex(x) for x in enduses])
    for a in enduses:
        i = idx[a]
        reg = split_ops(by_addr[a][3])[0]
        base = stride = None
        basewhy = stridewhy = None
        for k in range(i - 1, max(0, i - 600), -1):
            aa = order[k]
            b, t, mn, ops = by_addr[aa]
            dst, src = split_ops(ops)
            if dst != reg:
                continue
            m = IMM.match((src or "").strip())
            if stride is None and mn in ("add", "sub") and m:
                stride, stridewhy = int(m.group(1), 16), hex(aa)
            if base is None and mn == "mov" and m:
                base, basewhy = int(m.group(1), 16), hex(aa)
                break
            if base is None and mn == "mov" and not m:
                base, basewhy = None, "%s(%s) non-immediate init" % (hex(aa), t)
                break
        ok = bool(base and stride and (MASTER - base) % stride == 0)
        print("    site %s reg=%s base=%s(%s) stride=%s(%s) count=%s integral=%s" %
              (hex(a), reg, hex(base) if base else "?", basewhy,
               hex(stride) if stride else "?", stridewhy,
               ((MASTER - base) // stride) if ok else "?", ok))
    mloads = [a for a, b, t, mn, ops in ins if "ds:0x%x" % MASTER in t and mn in
              ("mov", "movsx", "movzx") and mem_of(split_ops(ops)[0]) != MASTER]
    mstores = [a for a, b, t, mn, ops in ins if mn == "mov"
               and mem_of(split_ops(ops)[0]) == MASTER]
    print("  MASTER scalar loads=%d %s  scalar stores=%d %s" %
          (len(mloads), [hex(x) for x in mloads], len(mstores), [hex(x) for x in mstores]))

    # ---------- gate table: measured numbers, then the asserts ----------
    READ_MAP = {"Announce": 0x92BF04, "Custom World": 0x92BF10, "Customize": 0x92BF14,
                "Difficulty": 0x92BDE8, "Faction": 0x92BDEC, "Map Type": 0x92BDF4,
                "More Preferences": 0x92BF00, "Preferences": 0x92BEFC, "Rules": 0x92BF08,
                "Semaphore": 0x92BF0C, "Top Menu": 0x92BDF8}
    AGREE6 = {"Difficulty", "Faction", "Map Type", "More Preferences", "Preferences",
              "Top Menu"}
    COPIES = {(MASTER, BYTECELL), (TARGET, BYTECELL), (BYTECELL, 0x8F0090),
              (MASTER, TARGET), (BYTECELL, TARGET)}
    gates = []

    def gate(gid, ok, detail):
        gates.append((gid, bool(ok), detail))

    gate("G1", len(textrefs) == 68 and sorted(textrefs) == sorted(encrefs)
         and len(set(encrefs)) == len(set(textrefs)) and len(matrefs) == 0
         and len(part["store"]) == 4 and len(part["load"]) == 40
         and len(part["cmp"]) == 24 and len(part["rmw"]) == 0 and len(part["other"]) == 0
         and {split_ops(by_addr[a][3])[1] for a in part["cmp"]
              if IMM.match(split_ops(by_addr[a][3])[1] or "")} ==
             {"0x1", "0x2", "0x3", "0x4"},
         "68 refs, enc-scan identical, 0 address materializations, 4 store/40 load/24 cmp/"
         "0 rmw, cmp immediates exactly {1,2,3,4}. SCOPE (s312 #346 P1): the two scans agree "
         "on every reference objdump can print and on every immediate-byte materialization, "
         "so NO writer that names 0x985aec in the image exists; a store through a REGISTER "
         "POINTER whose value was computed at runtime is invisible to both scans and is NOT "
         "excluded by this gate (G9.1 pins the cmp arms)")

    forms = {a: " ".join(by_addr[a][0]) for a in part["store"]}
    want = " ".join(["a3"] + le)
    gate("G2", set(part["store"]) == STORE_SET
         and all(forms[a] == want for a in part["store"])
         and sorted(fnof(a)[0] for a in part["store"]) == sorted(
             ["FUN_004ddaa0", "FUN_0057c550", "FUN_0057c550", "FUN_0057ecf0"]),
         "store set exact %s, all moffs form '%s', funcs FUN_004ddaa0 / "
         "FUN_0057c550 x2 / FUN_0057ecf0" % (sorted(hex(x) for x in STORE_SET), want))

    tr = {}
    for a in sorted(STORE_SET | {0x57C7B0, 0x4DDB5A}):
        i = idx.get(a)
        prev = order[i - 1] if i else None
        tr[a] = (by_addr[prev][2] if prev is not None else "SITE-GONE",
                 branch_targets.get(a, []), exe.count(struct.pack("<I", a)))
    gate("G3", set(part["store"]) == STORE_SET
         and tr[0x4DDCF1][0] == "ret" and [x for x in tr[0x4DDCF1][1]] == [0x4DDB5A]
         and tr[0x4DDCF1][2] == 0 and by_addr[0x4DDB5A][2] == "jge"
         and all(tr[a][0] == "mov" for a in (0x57C5AF, 0x57C7B5, 0x57F006))
         and tr[0x57C7B5][1] == [] and tr[0x57C5AF][1] == [] and tr[0x57F006][1] == []
         and [x for x in tr[0x57C7B0][1]] and all(tr[a][2] == 0 for a in tr),
         "0x4ddcf1: no fall-in (prev=ret) but branch-entered by 'jge' at 0x4ddb5a => its "
         "eax is the callee-0x5f1394 return on that edge (M308's UNATTRIBUTED CLOSED); "
         "0x57c7b0 branch-entered from %s; 0 jump-table entries anywhere in the image "
         "for any of the 5 sites" % sorted(hex(x) for x in tr[0x57C7B0][1]))

    pairs = sorted({(s, d) for s, d, _, _, _ in copies})
    sites = sorted({(s, d, ss, ds) for s, d, ss, ds, _ in copies})
    sitetable = {}
    for x, y, ss, ds in sites:
        sitetable.setdefault((x, y), []).append((ss, ds))
    gate("G4", pairs == sorted(COPIES) and sitetable == COPY_SITES and len(sites) == 6
         and (MASTER, TARGET) in pairs and (BYTECELL, TARGET) in pairs
         and (TARGET, MASTER) not in pairs and (TARGET, BYTECELL) in pairs,
         "clean-copy map among the 4 cells = %s (%d sites); NO direct 0x985aec->0x92bde8 "
         "copy exists, so the mirror direction is master->runtime" %
         (sorted("%s->%s" % (hex(a), hex(b)) for a, b in pairs), len(sites)))

    rex1 = {k: v for k, v in rex.items() if len(v) == 1}
    rpush = {name: a for a, name, _ in reads}
    wpush = {name: a for a, name, _ in writes}
    fc = {}
    for k, v in rex1.items():
        fc.setdefault(v[0], []).append(k)
    gate("G5", {k: v[0] for k, v in rex1.items()} == READ_MAP
         and all(len(x) == 1 for x in fc.values())
         and len(rex1) == 11 and rex.get("Difficulty") == [MASTER]
         and rpush.get("Difficulty") == PREF_PIN["Difficulty"][0]
         and sorted(rwh.get("Difficulty", {}).get(MASTER, [])) == [PREF_PIN["Difficulty"][1]]
         and rpush.get("Map Type") == PREF_PIN["Map Type"][0],
         "READ side (FUN_0058e7f0): 11 names carry EXACTLY ONE exclusive field, the map "
         "is injective (no field shared by two names), Difficulty->0x92bde8: %s" %
         sorted("%s=0x%x" % (k, v[0]) for k, v in rex1.items()))

    nw = sum(1 for _, _, _, k in use if k == "WRITE")
    wdiff = [hex(x) for x in wex.get("Difficulty", [])]
    gate("G6", nw == 8 and wex.get("Difficulty") == [MASTER] and agree == AGREE6
         and len(both) == 8
         and wpush.get("Difficulty") == PREF_PIN["WRITE Difficulty"][0]
         and PREF_PIN["WRITE Difficulty"][1] in wwh.get("Difficulty", {}).get(MASTER, []),
         "WRITE side (FUN_0058f0d0): %d 4-arg key pushes == the 8 "
         "WritePrivateProfileStringA calls Ghidra resolves in that function; "
         "Difficulty's exclusive field is 0x92bde8 there too (%s); read/write agree on "
         "%d names %s" % (nw, wdiff, len(agree), sorted(agree)))

    de1 = {k: v for k, v in deex.items() if len(v) == 1}
    gate("G7", deex.get("Difficulty") == [MASTER] and set(agree3) == AGREE6
         and "Difficulty" in agree3 and len(tri) == len(agree3) == 6
         and de1.get("Top Menu") == [0x92BDF8] and de1.get("Map Type") == [0x92BDF4]
         and de1.get("Faction") == [0x92BDEC]
         and de1.get("Time Controls") == [0x92BF10] and de1.get("00000000") == [0x92BF0C]
         and "Custom World" not in deex and "Semaphore" not in deex
         and not any(fnrange(a)[0] == 0x58E7F0 for a in part["store"]),
         "NOUN: the third view is the READER body's own pseudocode map. s312 correction: "
         "the s311 map merged the reader's and the writer's bodies and printed 7 three-way "
         "names; the writer body contributes 0 exclusive pairs, so the 7th key was an "
         "artifact of the merge — the honest count is 6 three-way names and all 6 agree "
         "fully %s. All three views give 'Difficulty' -> ds:0x92bde8. The pairing slips "
         "exactly twice, both pinned here: the pseudocode's proximity pairing keys "
         "0x92bf10 as 'Time Controls' and 0x92bf0c as '00000000' (a later name mention "
         "moves the pend), where the raw READ-window scan keys them 'Custom World' and "
         "'Semaphore' — same single field either way, so this is a naming artifact of the "
         "third view, not a contradiction of it; no store to 0x985aec sits in the prefs "
         "reader, so 0x985aec is the RUNTIME MIRROR of the preference the game itself calls "
         "Difficulty (siblings: Top Menu=0x92bdf8, Map Type=0x92bdf4, Faction=0x92bdec)"
         % sorted(agree3))

    endbase = []
    for a in enduses:
        reg = split_ops(by_addr[a][3])[0]
        base = stride = None
        i = idx[a]
        for k in range(i - 1, max(0, i - 600), -1):
            aa = order[k]
            b, t, mn, ops = by_addr[aa]
            dst, src = split_ops(ops)
            if dst != reg:
                continue
            m = IMM.match((src or "").strip())
            if stride is None and mn in ("add", "sub") and m:
                stride = int(m.group(1), 16)
            if base is None and mn == "mov" and m:
                base = int(m.group(1), 16)
                break
        endbase.append((a, base, stride, base is not None and stride is not None
                        and base <= MASTER and (MASTER - base) % stride == 0))
    gate("G8", sorted(enduses) == [0x579BC6, 0x57AB57]
         and all(x[3] and x[1] == 0x92BA98 and x[2] == 0xD4 and
                 (MASTER - x[1]) // x[2] == 4 for x in endbase)
         and mstores == [0x57C7B0, 0x58E8C6] and len(mloads) == 6,
         "RIVAL KILLED: 0x92bde8 is BOTH the exact end of the 4x0xd4 record array at "
         "0x92ba98 (2 loop-bound uses, count=4 integral) AND a scalar pref cell with 2 "
         "stores %s + 6 loads; 'it is only an array-end sentinel, so the mirror is an "
         "offset coincidence' fails on 0 stores" % [hex(x) for x in mstores])

    # ---------- G9: the s312 review round (#346).  The reviewer listed six facts
    # that `## M332`/`## M308` assert and that G1..G8 print around without ever
    # READING.  Each is measured here on the same parse, and each can go red:
    # MU18 (the edge call's target), MU19 (the co-store's register), MU20 (the
    # array loop's back edge), MU21 (the ebx cmp arm) are aimed at exactly these.
    DEFMN = {"mov", "movsx", "movzx", "movbe", "lea", "add", "sub", "and", "or",
             "xor", "sbb", "adc", "shl", "shr", "sar", "inc", "dec", "neg",
             "not", "xchg", "pop", "bswap"}

    def imm_of(op):
        m = IMM.match((op or "").strip())
        return m.group(1) if m else None

    def callee_of(a):
        return (by_addr[a][3] or "").strip()

    def defs_of(reg, lo, hi):
        """(lo,hi) EXCLUSIVE: instructions that write `reg`, plus every `call`
        (a call writes the caller-saved set, so it breaks register provenance)."""
        out = []
        for a in order[bisect.bisect_left(order, lo) + 1:bisect.bisect_left(order, hi)]:
            mn, ops = by_addr[a][2], by_addr[a][3]
            if mn == "call":
                out.append((a, mn))
            elif mn in DEFMN and reg_of(split_ops(ops)[0]) == reg:
                out.append((a, mn))
        return out

    print("== G9.1 the cmp arms (the ebx half of the '1,2,3,4 + ebx' claim) ==")
    arms = [split_ops(by_addr[a][3])[1] for a in part["cmp"]]
    imm_arm = sorted({x for x in arms if x and IMM.match(x)})
    reg_arm = sorted({x for x in arms if x and not IMM.match(x)})
    ebx_sites = [a for a in part["cmp"] if split_ops(by_addr[a][3])[1] == "ebx"]
    print("   immediate arm %s   register arm %s   the ebx cmp sits at %s and nowhere else"
          % (imm_arm, reg_arm, [hex(x) for x in ebx_sites]))
    g91 = (imm_arm == ["0x1", "0x2", "0x3", "0x4"] and reg_arm == ["ebx"]
           and ebx_sites == [0x4F9B5A])

    print("== G9.2 whose eax does 0x4ddcf1 store (the callee-attribution claim) ==")
    CE, CJ, CS = 0x4DDB53, 0x4DDB5A, 0x4DDCF1
    win_mn = [by_addr[a][2] for a in order[idx[CE] + 1:idx[CJ]]]
    win_ops = [by_addr[a][3] for a in order[idx[CE] + 1:idx[CJ]]]
    eax_defs = defs_of("eax", CE, CJ)
    print("   %s '%s %s' -> window %s %s -> %s '%s %s' -> %s stores eax; "
          "writes-to-eax inside the window=%s"
          % (hex(CE), by_addr[CE][2], callee_of(CE), win_mn, win_ops, hex(CJ),
             by_addr[CJ][2], by_addr[CJ][3], hex(CS), eax_defs))
    g92 = (by_addr[CE][2] == "call" and callee_of(CE) == "0x5f1394"
           and win_mn == ["test"] and win_ops == ["eax,eax"] and not eax_defs
           and by_addr[CJ][2] == "jge" and callee_of(CJ) == "0x4ddcf1"
           and by_addr[CS][2] == "mov"
           and mem_of(split_ops(by_addr[CS][3])[0]) == TARGET
           and reg_of(split_ops(by_addr[CS][3])[1]) == "eax")

    print("== G9.3 the 0x57c7b0/0x57c7b5 co-store (M308: 'same eax, no intervening write') ==")
    A, B = 0x57C7B0, 0x57C7B5
    adj = order[idx[A] + 1] == B
    dA, sA = split_ops(by_addr[A][3])
    dB, sB = split_ops(by_addr[B][3])
    same_reg = (by_addr[A][2] == by_addr[B][2] == "mov" and sA == sB and reg_of(sA) == "eax"
                and mem_of(dA) == MASTER and mem_of(dB) == TARGET)
    pcall = max([a for a in order[:idx[A]] if by_addr[a][2] == "call"])
    ndef = defs_of("eax", pcall, B)
    mstores_in = [a for a in order[idx[A]:idx[B] + 1]
                  if mem_of(split_ops(by_addr[a][3])[0]) == MASTER]
    print("   adjacent=%s both-store-plain-eax=%s (%s | %s) nearest-preceding-call=%s "
          "writes-to-eax-since=%d stores-to-0x92bde8-inside-the-pair=%s"
          % (adj, same_reg, by_addr[A][3], by_addr[B][3], hex(pcall), len(ndef),
             [hex(x) for x in mstores_in]))
    print("   -> M308's wording is CORRECTED: the master cell IS written inside the "
          "pair, by 0x57c7b0 itself from the same eax. 'No intervening write' is a law "
          "about the REGISTER, not about 0x92bde8.")
    g93 = adj and same_reg and pcall == 0x57C7A2 and not ndef and mstores_in == [A]

    print("== G9.4 the pinned copy windows (stored register never redefined, source cell "
          "never written between load and store) ==")
    g94 = True
    for (s_, d_), plist in sorted(COPY_SITES.items()):
        for (ssite, dsite) in plist:
            mn = by_addr[dsite][2]
            reg = reg_of(split_ops(by_addr[dsite][3])[1])
            nd = defs_of(reg, ssite, dsite) if reg else [("non-register store", 0)]
            srcw = [a for a in order[bisect.bisect_left(order, ssite) + 1:
                                      bisect.bisect_left(order, dsite) + 1]
                    if mem_of(split_ops(by_addr[a][3])[0]) == s_]
            ok = mn in ("mov", "movsx", "movzx") and reg is not None and not nd and not srcw
            g94 = g94 and ok
            print("   %s->%s  load %s  store %s (%s: %s)  redefs-of-%s=%d  "
                  "writes-to-source=%d  %s"
                  % (hex(s_), hex(d_), hex(ssite), hex(dsite), mn, by_addr[dsite][3],
                     reg, len(nd), len(srcw), "ok" if ok else "FAIL"))

    print("== G9.5 the API identity: my push-run arity vs Ghidra's resolved calls ==")
    def argc_callees(lo, hi, want):
        from collections import Counter
        c = Counter()
        for a in order[bisect.bisect_left(order, lo):bisect.bisect_left(order, hi)]:
            if by_addr[a][2] != "call":
                continue
            j = idx[a]
            k = j - 1
            argc = 0
            while k >= 0 and by_addr[order[k]][2] == "push":
                argc += 1
                k -= 1
            if any(by_addr[x][2] == "call" for x in order[k + 1:j]):
                continue
            if argc == want:
                c[callee_of(a)] += 1
        return c
    rlo, rhi = fnrange(0x58E7F0)
    wlo, whi = fnrange(0x58F0D0)
    c6, c4 = argc_callees(rlo, rhi, 6), argc_callees(wlo, whi, 4)
    print("   .text FUN_0058e7f0[0x%x,0x%x) argc==6 callees %s | Ghidra in that body "
          "Get=%d Write=%d" % (rlo, rhi, dict(c6), GH["FUN_0058e7f0"]["Get"],
                                GH["FUN_0058e7f0"]["Write"]))
    print("   .text FUN_0058f0d0[0x%x,0x%x) argc==4 callees %s | Ghidra in that body "
          "Get=%d Write=%d" % (wlo, whi, dict(c4), GH["FUN_0058f0d0"]["Get"],
                                GH["FUN_0058f0d0"]["Write"]))
    g95 = (c6.get("edi") == 18 == GH["FUN_0058e7f0"]["Get"] and len(c6) == 1
           and c4.get("edi") == 8 == GH["FUN_0058f0d0"]["Write"]
           and GH["FUN_0058e7f0"]["Write"] == 0 and GH["FUN_0058f0d0"]["Get"] == 0)
    print("   -> the 11 keyed READ windows sit inside these 18 argc-6 calls, ALL through "
          "the one indirect callee 'edi'; the 8 keyed WRITE windows are 8 of the argc-4 "
          "calls through 'edi' (the 9th argc-4 call goes to 0x5a6330 and is NOT keyed). "
          "Arity parse and Ghidra's import-resolved names agree on both counts.")

    print("== G9.6 the two array-end uses are real loop bounds (stride add + back edge) ==")
    g96 = True
    for a in sorted(enduses):
        reg = split_ops(by_addr[a][3])[0]
        i = idx[a]
        up = [aa for aa in order[max(0, i - 12):i]
              if by_addr[aa][2] == "add" and split_ops(by_addr[aa][3])[0] == reg
              and imm_of(split_ops(by_addr[aa][3])[1]) == "d4"]
        back = [aa for aa in order[i + 1:i + 8]
                if by_addr[aa][2].startswith("j") and imm_of(by_addr[aa][3])
                and int(imm_of(by_addr[aa][3]), 16) < a]
        ok = len(up) == 1 and len(back) == 1 and (MASTER - 0x92BA98) % 0xD4 == 0
        g96 = g96 and ok
        print("   cmp %s (%s): stride-add %s  back-edge %s  -> %s"
              % (hex(a), by_addr[a][3], [hex(x) for x in up], [hex(x) for x in back],
                 "loop" if ok else "NOT A LOOP"))
    gate("G9", g91 and g92 and g93 and g94 and g95 and g96,
         "s312 review tightening, six claims now read by a gate: (1) the cmp arms are "
         "exactly {0x1,0x2,0x3,0x4} + register arm exactly {ebx}, the ebx cmp unique at "
         "0x4f9b5a; (2) 0x4ddb53 'call 0x5f1394' then 'test eax,eax' with ZERO writes to "
         "eax before 'jge 0x4ddcf1', which stores eax => the stored value IS that callee's "
         "return; (3) 0x57c7b0/0x57c7b5 are ADJACENT plain-eax stores to 0x92bde8 then "
         "0x985aec, zero eax-writes since the call at 0x57c7a2, and the only master store "
         "in the pair is 0x57c7b0 itself (so M308's 'no intervening write' is narrowed to "
         "the register); (4) all 6 pinned copy windows have 0 redefinitions of the stored "
         "register AND 0 writes to the source cell between load and store; (5) argc==6 "
         "call count in FUN_0058e7f0 is 18, all through the single indirect 'edi', == "
         "Ghidra's 18 GetPrivateProfileStringA there, and argc==4 through 'edi' is 8 == "
         "Ghidra's 8 WritePrivateProfileStringA in FUN_0058f0d0 (0 of the other API in "
         "either body); (6) both array-end cmps sit in a loop with 'add reg,0xd4' and a "
         "backward jl, so the 4x0xd4 array-end reading is a loop, not an immediate walk")

    sys.stdout = sys.__stdout__
    tbl = "\n".join(_T)
    digest = hashlib.sha256(tbl.encode()).hexdigest()[:16]
    lines = []
    nfail = 0
    for gid, ok, detail in gates:
        lines.append("%s %s: %s" % ("PASS" if ok else "FAIL", gid, detail))
        nfail += 0 if ok else 1
    lines.append("digest(table)=%s  (the sha256/16 of every printed measurement "
                 "line above, gates excluded)" % digest)
    lines.append("%s M332: %d/%d gates" % ("PASS" if nfail == 0 else "FAIL",
                                           len(gates) - nfail, len(gates)))
    for l in lines:
        print(l)
    if "--no-evidence" not in sys.argv:
        ev = os.path.join(ROOT, "evidence", "m332_difficulty_census.txt")
        with open(ev, "w") as f:
            f.write(tbl + "\n" + "\n".join(lines) + "\n")
    return 0 if nfail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
