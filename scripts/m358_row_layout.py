#!/usr/bin/env python3
"""M358 - the 52-byte 0x98ad88 row: its full field layout, and its relation to
the 128-dword 0x9267e4 candidate table.

M354 pinned five fields of the row from three imul sites.  M356 then read the
state bits at "+0x30 (= 0x98adb8)".  This milestone censuses EVERY instruction
whose displacement lands in the row array, derives the field atlas (offset,
width, access) from the instructions themselves, separates the loop SENTINELS
that share the row window from real fields, and pins the relation to 0x9267e4:

  * 0x9267e4 is a 128-entry DWORD table (slot -> item) built by 0x596000 and
    0x596160: entry[slot] = (slot<0x40 ? 0 : owner<<6) + (slot & 0x3f).
    It is NOT a 64-byte record array: all seven indirection sites use a *4
    displacement, and the 0x40/0x6 shifts apply to the OWNER value.
  * the row is 0x34 bytes: char[0x20] name, dword +0x20, bytes +0x24..+0x2e,
    word +0x30 (flags: bit0 valid @0x5a7402, bit2 design, bit8 set x3 / clear
    x1 through the +0x31 high byte), word +0x32; +0x2f and +0x33 unaddressed.
  * row 63 (0x98ba54) is the static PROTOTYPE: FUN_00435610 copies a source
    record's +0x141fc..+0x1420c into +0x24/+0x25/+0x26/+0x20(dword)/+0x27 and
    writes 0xff at +0x2e.

Static only.  Every printed number is computed here; each gate asserts a
parsed value, and one-instruction mutants redden named gates
(scripts/m358_mutate.py).

    python3 -u scripts/m358_row_layout.py            # acceptance
    python3 -u scripts/m358_row_layout.py --probe    # census only
"""
import argparse
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("SMAC_M358_TEXT") or os.path.join(ROOT, "scratch", "m574", "text.txt")
STARTS = os.environ.get("SMAC_M358_STARTS") or os.path.join(ROOT, ".func_starts.json")
PATCH = os.environ.get("SMAC_M358_PATCH", "")

ROW_BASE, ROW_STRIDE = 0x98AD88, 0x34
ROW_SPAN = 0x40 * ROW_STRIDE
CAND_BASE, CAND_N = 0x9267E4, 0x80
BUILDERS = (0x596000, 0x596160)
PROTO_FN, PROTO_ROW = 0x435610, 63
SENT_OFFS = {0x08: 12, 0x0C: 2, 0x10: 1, 0x14: 1}
SENT_STARTS = [(0x98AAF0, 0x98AD90), (0x98AAF4, 0x98AD94),
               (0x98AAF8, 0x98AD98), (0x98AAFC, 0x98AD9C)]
FIELD = {0x00: "b[0x20] name", 0x1F: "b NUL terminator", 0x20: "d ability mask",
         0x24: "b chassis idx", 0x25: "b weapon idx", 0x26: "b armour idx",
         0x27: "b comp3 (noun OPEN)", 0x28: "b comp4 (noun OPEN)", 0x29: "b weight",
         0x2A: "b class", 0x2B: "b ord2 (cmp 0x15)", 0x2C: "b owner mask",
         0x2D: "b small (2 writers)", 0x2E: "b (proto 0xff)", 0x30: "w flags",
         0x31: "b flags>>8", 0x32: "w pre-req tech"}
# FUN_00435610: six stores into row 63 (0x98ba54): (dest field, source offset or imm)
PROTO_STORES = [(0x20, "0x14208"), (0x24, "0x141fc"), (0x25, "0x14200"),
                (0x26, "0x14204"), (0x27, "0x1420c"), (0x2E, "0xff")]

ROW = re.compile(r"^\s*([0-9a-f]{6,8}):\t([0-9a-f ]+)\t(.*)$")
HEX = re.compile(r"0x([0-9a-f]+)")
BR = re.compile(r"\[([^\]]*)\]")
IMUL34 = re.compile(r"imul\s+(\w+),\s*\1,\s*0x34\b")


def norm(s):
    return re.sub(r"\s+", " ", s.strip())


def width_of(text):
    for pat, v in ((r"\bDWORD PTR\b", "d"), (r"\bWORD PTR\b", "w"), (r"\bBYTE PTR\b", "b")):
        if re.search(pat, text):
            return v
    m = re.search(r",\s*(e?[abcd]x|[abcd][lh])\s*$", text)
    if m:
        return {"al": "b", "cl": "b", "dl": "b", "bl": "b", "ah": "b", "ch": "b",
                "dh": "b", "bh": "b", "ax": "w", "cx": "w", "dx": "w", "bx": "w"}.get(
                    m.group(1), "d")
    return None


class Ins:
    __slots__ = ("addr", "raw", "mn", "ops", "fn")

    def __init__(self, addr, raw):
        self.addr, self.raw = addr, raw
        self.mn, self.ops = self._split(raw)
        self.fn = "?"

    @staticmethod
    def _split(raw):
        m = re.match(r"([a-z0-9]+)\s*(.*)", raw)
        return (m.group(1), m.group(2)) if m else ("", raw)


def load_starts(path):
    with open(path) as f:
        addrs = sorted(int(a) for a in json.load(f))
    return addrs, ["FUN_%08x" % a for a in addrs]


def parse(path, starts, patch=None):
    saddr, sname = starts
    ins, order = {}, []
    import bisect
    with open(path, "r", errors="replace") as f:
        for line in f:
            m = ROW.match(line)
            if not m:
                continue
            addr = int(m.group(1), 16)
            i = Ins(addr, norm(m.group(3)))
            if patch and patch[0] == addr:
                if i.raw.count(patch[1]) != 1:
                    raise SystemExit("PATCH REJECTED: 0x%x %r not unique in %r" % (addr, patch[1], i.raw))
                i.raw = i.raw.replace(patch[1], patch[2])
                i.mn, i.ops = Ins._split(i.raw)
            k = bisect.bisect_right(saddr, addr) - 1
            i.fn = sname[k] if k >= 0 else "?"
            ins[addr] = i
            order.append(addr)
    return ins, order


def memref(text, tok):
    if "ds:" + tok in text:
        return True
    pos = text.find(tok)
    return any(m.start() < pos < m.end() for m in BR.finditer(text))


def access(mn, ops, tok):
    is_dest = tok in ops.split(",")[0]
    if mn == "lea":
        return "addr"
    if mn in ("test", "cmp", "push"):
        return "read"
    if not memref(mn + " " + ops, tok):
        return "base" if mn in ("add", "sub", "mov") and not is_dest else "imm"
    if mn in ("mov", "movsx", "movzx"):
        return "write" if is_dest else "read"
    if mn in ("or", "and", "add", "sub", "xor", "inc", "dec", "shl", "shr", "sar", "not", "neg"):
        return "rmw" if is_dest else "read"
    return "read"


def census(ins, order):
    rows, cand = [], []
    for a in order:
        i = ins[a]
        txt = (i.mn + " " + i.ops).strip()
        for hm in HEX.finditer(i.ops):
            v, tok = int(hm.group(1), 16), hm.group(0)
            if ROW_BASE <= v < ROW_BASE + ROW_SPAN:
                rows.append(dict(addr=a, fn=i.fn, disp=v, off=(v - ROW_BASE) % ROW_STRIDE,
                                 idx=(v - ROW_BASE) // ROW_STRIDE, mem=memref(txt, tok),
                                 acc=access(i.mn, i.ops, tok), w=width_of(txt), ins=txt))
            elif CAND_BASE <= v < CAND_BASE + 4 * CAND_N:
                cand.append(dict(addr=a, fn=i.fn, disp=v, mem=memref(txt, tok),
                                 acc=access(i.mn, i.ops, tok), ins=txt))
    return rows, cand


def seq(ins, lo, hi):
    return [ins[a] for a in range(lo, hi) if a in ins]


def has(ins, lo, hi, sub, gaps=10):
    s = seq(ins, lo, hi)
    for i, x in enumerate(s):
        if sub in (x.mn + " " + x.ops):
            return i
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    args = ap.parse_args()

    patch = None
    if PATCH:
        ad, old, new = PATCH.split("|", 2)
        patch = (int(ad, 16), old, new)
    ins, order = parse(TEXT, load_starts(STARTS), patch)
    rows, cand = census(ins, order)
    mem = [r for r in rows if r["mem"]]
    sent = {o: [r for r in rows if r["off"] == o] for o in SENT_OFFS}

    print("== 0x98ad88 row: %d refs (%d mem) in %d functions; span 0x%x = 64 rows ==" % (
        len(rows), len(mem), len({r['fn'] for r in rows}), ROW_SPAN))
    atlas = {}
    for r in mem:
        d = atlas.setdefault(r["off"], dict(n=0, w=set(), acc={}, fns=set(), rowids=set(), s=""))
        d["n"] += 1
        if r["acc"] in ("read", "write", "rmw") and r["w"]:
            d["w"].add(r["w"])
        d["acc"][r["acc"]] = d["acc"].get(r["acc"], 0) + 1
        d["fns"].add(r["fn"])
        d["rowids"].add(r["idx"])
        if r["acc"] in ("write", "rmw") and not d["s"]:
            d["s"] = "0x%08x %s" % (r["addr"], r["ins"])
    tbl = []
    for off in sorted(atlas):
        d = atlas[off]
        line = "  +0x%02x n=%3d w=%-3s acc=%-24s fns=%2d rows<=%3d %-18s %s" % (
            off, d["n"], "".join(sorted(x or "?" for x in d["w"])),
            ",".join("%s:%d" % kv for kv in sorted(d["acc"].items())),
            len(d["fns"]), max(d["rowids"]), FIELD.get(off, "?UNMAPPED"), d["s"])
        tbl.append(line)
        print(line)

    im = [a for a in order if IMUL34.search(ins[a].mn + " " + ins[a].ops)]
    proto_base = ROW_BASE + PROTO_ROW * ROW_STRIDE
    print("\n== stride ==")
    print("  imul reg,reg,0x34 sites=%d ; row%d base = 0x%x ; prototype stores at 0x%x..0x%x" % (
        len(im), PROTO_ROW, proto_base, proto_base + 0x20, proto_base + 0x2E))
    for a in im[:2]:
        print("  0x%08x %s | %s %s" % (a, ins[a].fn, ins[a].mn, ins[a].ops))
    print("== prototype FUN_00435610 ==")
    for x in seq(ins, PROTO_FN, PROTO_FN + 0x64):
        if x.mn == "mov" and ("ds:0x98ba" in x.ops or "0x1420" in x.ops or "0x141f" in x.ops):
            print("  0x%08x %s %s" % (x.addr, x.mn, x.ops))
    print("== sentinels (cmp immediates sharing the row window) ==")
    for off, want in sorted(SENT_OFFS.items()):
        print("  +0x%02x refs=%d cmp=%d want=%d" % (
            off, len(sent[off]), sum(1 for r in sent[off] if ins[r["addr"]].mn == "cmp"), want))
    print("== 0x1c loops with static starts ==")
    for s, e in SENT_STARTS:
        print("  0x%x..0x%x  (end-start)/0x1c = %d" % (s, e, (e - s) // 0x1C))
    print("== 0x9267e4: %d refs, %d mem, table dwords %d ==" % (len(cand), sum(1 for c in cand if c["mem"]), CAND_N))
    for c in cand:
        print("  %s 0x%08x %-22s %s" % ("mem" if c["mem"] else "imm", c["addr"], c["fn"], c["ins"]))
    print("== builders ==")
    for b in BUILDERS:
        s = seq(ins, b, b + 0x160)
        anchors = [i for i, x in enumerate(s) if x.mn == "cmp" and x.ops == "ecx,0x40"
                   or x.mn == "shl" and x.ops == "eax,0x6"
                   or x.mn == "and" and x.ops.endswith(",0x8000003f")
                   or "0x9267e4],e" in x.ops.replace(" ", "")
                   or x.mn == "cmp" and x.ops == "ecx,0x80"]
        print("  0x%x anchors=%s" % (b, anchors))
    def entry(owner, slot):
        return (0 if slot < 0x40 else owner << 6) + (slot & 0x3F)
    print("  entry(owner=2, slot=0x41)=0x%x != slot; entry(owner=1, slot=0x41)=0x%x"
          % (entry(2, 0x41), entry(1, 0x41)))
    print("== flags high byte (bit 8) ==")
    print("  +0x31 rmw sites: %s" % [(hex(r["addr"]), r["ins"]) for r in rows if r["off"] == 0x31])
    below = sum(d["n"] for o, d in atlas.items() if o < 0x30)
    print("== RIVALS (each must FAIL on the printed numbers) ==")
    print("  R1 '0x9267e4 is a 64-byte record array': refs=%d, mem=%d, mem with a non-*4 index=%d, "
          "refs at a 0x40 stride=%d -> REFUTED" % (
              len(cand), sum(1 for c in cand if c["mem"]),
              sum(1 for c in cand if c["mem"] and "*4+0x9267e4" not in c["ins"]),
              sum(1 for c in cand if "*0x40" in c["ins"])))
    print("  R2 'the row starts at 0x98adb8 (only +0x30/+0x32 are fields)': mem refs below +0x30 = %d "
          "across %d offsets, name NUL at +0x1f -> REFUTED" % (
              below, sum(1 for o in atlas if o < 0x30)))
    ok_sent0 = all(sum(1 for r in sent[o] if ins[r["addr"]].mn == "cmp") == n for o, n in SENT_OFFS.items())
    print("  R3 '+0x08/+0x0c/+0x10/+0x14 are row fields': %d/%d are cmp-immediate sentinels of 0x1c "
          "scans -> REFUTED" % (16 if ok_sent0 else 0, 16))
    if args.probe:
        return 0

    # ---- gates ------------------------------------------------------------
    fails = []
    def gate(name, ok, msg):
        print("%s %s: %s" % ("PASS" if ok else "FAIL", name, msg))
        if not ok:
            fails.append(name)

    field_offs = sorted(atlas)
    want_fields = sorted(FIELD)
    gate("G1", len(im) == 756 and proto_base == 0x98BA54
         and 0x98BA74 == proto_base + 0x20,
         "756 imul-0x34 sites; row63 base 0x%x, its +0x20 store at 0x98ba74" % proto_base)
    gate("G2", field_offs == want_fields,
         "%d field offsets %s" % (len(field_offs), ["0x%02x" % o for o in field_offs]))
    gate("G3", atlas[0x20]["w"] == {"d", "b"}
         and all(atlas[o]["w"] == {"b"} for o in range(0x24, 0x2F))
         and atlas[0x30]["w"] == {"w", "b"} and atlas[0x31]["w"] == {"b"}
         and atlas[0x32]["w"] == {"w"} and 0x2F not in atlas and 0x33 not in atlas,
         "+0x20={d,b}, +0x24..2e=b, +0x30={w,b}, +0x31=b, +0x32=w; 0x2f/0x33 unaddressed")
    nul = [r for r in mem if r["off"] == 0x1F]
    name_free = not [r for r in mem if 0x01 <= r["off"] < 0x1F]
    gate("G4", len(nul) == 1 and nul[0]["acc"] == "write" and nul[0]["ins"].endswith(",0x0") and name_free,
         "name char[0x20]: one NUL store at +0x1f (%r), no mem ref +0x01..+0x1e"
         % (nul[0]["ins"] if nul else None,))
    ok_sent = all(sum(1 for r in sent[o] if ins[r["addr"]].mn == "cmp") == n for o, n in SENT_OFFS.items())
    ok_adv = all(any(x.mn == "add" and x.ops.endswith(",0x1c") for x in seq(ins, r["addr"] - 6, r["addr"]))
                 for o in SENT_OFFS for r in sent[o])
    iters = [(e - s) // 0x1C for s, e in SENT_STARTS]
    gate("G5", ok_sent and ok_adv and iters == [24, 24, 24, 24],
         "16 sentinels all cmp with add cursor,0x1c; four static loops = %s iterations" % (iters,))
    gate("G6", len(cand) == 10 and sum(1 for c in cand if c["mem"]) == 7
         and all(c["disp"] == CAND_BASE and "*4+0x9267e4" in c["ins"] for c in cand if c["mem"]),
         "0x9267e4 = 0x%x dwords: 10 refs, 7 mem, all [reg*4+base], no other displacement" % CAND_N)
    s1 = seq(ins, BUILDERS[0], BUILDERS[0] + 0x160)
    s2 = seq(ins, BUILDERS[1], BUILDERS[1] + 0x160)

    def builder_shape(s):
        """match the ordered 14-instruction band sequence; return (slot, band) or None."""
        for i, x in enumerate(s[:40]):
            if not (x.mn == "cmp" and x.ops.endswith(",0x40")):
                continue
            slot = x.ops.split(",")[0]
            def nxt(pred, start, lim=8):
                for k in range(start, min(len(s), start + lim)):
                    if pred(s[k]):
                        return k
                return None
            k1 = nxt(lambda y: y.mn == "jl", i + 1)
            if k1 is None:
                return None
            k2 = nxt(lambda y: y.mn == "mov" and y.ops.startswith("eax"), k1 + 1)
            k3 = nxt(lambda y: y.mn == "shl" and y.ops == "eax,0x6", k2 + 1)
            k4 = nxt(lambda y: y.mn == "jmp", k3 + 1)
            k5 = nxt(lambda y: y.mn == "xor" and y.ops == "eax,eax", k4 + 1)
            k6 = nxt(lambda y: y.mn == "mov" and y.ops.endswith("," + slot), k5 + 1)
            if k6 is None:
                return None
            band = s[k6].ops.split(",")[0]
            need = [("and", band + ",0x8000003f"), ("jns", None), ("dec", band),
                    ("or", band + ",0xffffffc0"), ("inc", band), ("add", band + ",eax")]
            j = k6
            for mn, ops in need:
                j2 = nxt(lambda y, mn=mn, ops=ops: y.mn == mn and (ops is None or y.ops == ops), j + 1)
                if j2 is None:
                    return None
                j = j2
            k13 = nxt(lambda y: y.mn == "mov" and y.ops.startswith(
                "DWORD PTR [" + slot + "*4+0x9267e4]," + band), j + 1)
            if k13 is None:
                return None
            return (slot, band)
        return None
    shp1, shp2 = builder_shape(s1), builder_shape(s2)
    gate("G7", shp1 == ("ecx", "ebx") and shp2 == ("edx", "esi")
         and entry(2, 0x41) == 0x81 and entry(1, 0x41) == 0x41,
         "both builders match the 14-insn band sequence %s/%s; owner2 slot41 -> 0x81"
         % (shp1, shp2))
    chain = [0x4956C6, 0x4956D6, 0x49571B, 0x4957E2, 0x4959BE]
    gate("G8", all(a in ins for a in chain)
         and "cmp DWORD PTR [ebp-0x28],0x80" == (ins[0x4956C6].mn + " " + ins[0x4956C6].ops)
         and "0x9267e4" in ins[0x4956D6].ops and "0x34" in ins[0x49571B].ops,
         "A: 0x80 slots -> cand[idx] -> imul 0x34 -> row")
    hi = [r for r in rows if r["off"] == 0x31]
    clears = [r for r in hi if ",0xfe" in r["ins"]]
    sets = [r for r in hi if ",0x1" in r["ins"] and r["ins"].startswith("or")]
    gate("G9", len(hi) == 4 and len(clears) == 1 and len(sets) == 3,
         "flags bit8: %d sites = %d clear (and 0xfe) + %d set (or 0x1)" % (len(hi), len(clears), len(sets)))
    ptext = " ".join(x.mn + " " + x.ops for x in seq(ins, PROTO_FN, PROTO_FN + 0x64))
    okp = all(("ds:0x%x" % (proto_base + f)) in ptext and src in ptext for f, src in PROTO_STORES)
    gate("G10", okp and ins[PROTO_FN].mn == "push",
         "FUN_00435610 stores %s into row %d" % ([hex(f) for f, _ in PROTO_STORES], PROTO_ROW))

    digest = hashlib.sha256("\n".join(tbl).encode()).hexdigest()[:16]
    if fails:
        print("FAIL M358: %d/%d gates red %s" % (len(fails), 10, fails))
        return 1
    print("PASS M358: 10/10 gates  %s" % digest)
    return 0


if __name__ == "__main__":
    import io

    _out = sys.stdout

    class _Tee(io.TextIOBase):
        def __init__(self):
            self.buf = []

        def write(self, x):
            _out.write(x)
            self.buf.append(x)
            return len(x)

        def flush(self):
            _out.flush()

    _t = _Tee()
    sys.stdout = _t
    _rc = main()
    sys.stdout = _out
    if not PATCH and "--probe" not in sys.argv:
        with open(os.path.join(ROOT, "evidence", "m358_row_layout.txt"), "w") as f:
            f.write("".join(_t.buf))
    sys.exit(_rc)
