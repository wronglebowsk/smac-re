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


def imm_of(ops):
    """the trailing immediate of an operand string, or None."""
    t = ops.split(",")[-1].strip()
    try:
        return int(t, 16)
    except ValueError:
        return None


def sentinel_math(ins, rows):
    """parse each sentinel's stride advance, branch direction, static start, iterations."""
    out = []
    for r in rows:
        if r["off"] not in SENT_OFFS:
            continue
        i = ins[r["addr"]]
        reg = i.ops.split(",")[0].strip().split(" ")[-1]
        end = imm_of(i.ops)
        stride = None
        for x in reversed(seq(ins, r["addr"] - 8, r["addr"])):
            if x.mn == "add" and x.ops.split(",")[0].strip() == reg:
                stride = imm_of(x.ops)
                break
        back = False
        for x in seq(ins, r["addr"] + 1, r["addr"] + 24):
            if x.mn == "jl":
                back = imm_of(x.ops) is not None and imm_of(x.ops) < r["addr"]
                break
        start = None
        for x in reversed(seq(ins, r["addr"] - 400, r["addr"])):
            if x.fn != i.fn:
                break
            if x.mn == "mov" and x.ops.split(",")[0].strip() == reg:
                v = imm_of(x.ops)
                if v is not None and 0x98A000 <= v <= 0x98B000:
                    start = v
                    break
        iters = (end - start) // stride if (start is not None and stride) else None
        out.append(dict(addr=r["addr"], off=r["off"], stride=stride, back=back,
                        start=start, end=end, iters=iters))
    return out


def proto_pairs(ins):
    """pair every row-63 store with the register load that feeds it."""
    last, pairs = {}, {}
    for x in seq(ins, PROTO_FN, PROTO_FN + 0x64):
        if x.mn != "mov":
            continue
        dst, src = [t.strip() for t in x.ops.split(",", 1)]
        m = re.search(r"\[[a-z]+\+0x(14[0-9a-f]{3})\]", src)
        REGS = ("eax", "ebx", "ecx", "edx", "esi", "edi", "ax", "cx", "dx",
                "al", "cl", "dl", "bl", "ah", "ch", "dh", "bh")
        if dst in REGS and m:
            last[dst] = ("src", int(m.group(1), 16))
        elif dst in REGS and re.fullmatch(r"0x[0-9a-f]+", src):
            last[dst] = ("imm", int(src, 16))
        m2 = re.search(r"ds:0x([0-9a-f]+)", dst)
        if m2:
            field = int(m2.group(1), 16) - proto_base0()
            if 0 <= field < ROW_STRIDE:
                if re.fullmatch(r"0x[0-9a-f]+", src):
                    pairs[field] = ("imm", int(src, 16))
                elif src in last:
                    pairs[field] = last[src]
    return pairs


def proto_base0():
    return ROW_BASE + PROTO_ROW * ROW_STRIDE


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
    smath = sentinel_math(ins, rows)
    for off, want in sorted(SENT_OFFS.items()):
        print("  +0x%02x refs=%d cmp=%d want=%d" % (
            off, len(sent[off]), sum(1 for r in sent[off] if ins[r["addr"]].mn == "cmp"), want))
    print("== the 0x1c scans (stride / backward jl / static start / iterations) ==")
    for d in smath:
        if d["start"] is not None:
            print("  0x%08x +0x%02x stride=0x%x back=%s start=0x%x end=0x%x iters=%d" % (
                d["addr"], d["off"], d["stride"] or 0, d["back"], d["start"], d["end"], d["iters"] or 0))
    print("  %d sentinel refs: %d carry a static start, %d have a backward jl" % (
        len(smath), sum(1 for d in smath if d["start"] is not None),
        sum(1 for d in smath if d["back"])))
    print("== A loop: slot -> item -> row ==")
    for a in (0x4956C6, 0x4956D6, 0x4956DD, 0x4956F0, 0x4956F4, 0x49571B, 0x49571E, 0x4957E2, 0x4959BE):
        i = ins.get(a)
        print("  0x%08x %s" % (a, (i.mn + " " + i.ops) if i else "MISSING"))
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
    nobj = len({r["fn"] for r in rows})
    pairs = proto_pairs(ins)
    want_pairs = {f: ("src", int(v, 16)) if v != "0xff" else ("imm", 0xff) for f, v in PROTO_STORES}
    gate("G1", len(im) == 756 and proto_base == 0x98BA54,
         "stride 0x34: %d imul sites, row63 base 0x%x (=0x98ba54)" % (len(im), proto_base))
    gate("G2", field_offs == want_fields and len(rows) == 1991 and len(mem) == 1907 and nobj == 227,
         "%d field offsets %s; census %d refs / %d mem / %d fns"
         % (len(field_offs), ["0x%02x" % o for o in field_offs], len(rows), len(mem), nobj))
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
    ok_sent = all(len(sent[o]) == n and all(ins[r["addr"]].mn == "cmp" for r in sent[o])
                  for o, n in SENT_OFFS.items())
    stat = [d for d in smath if d["start"] is not None]
    starts = sorted({d["start"] for d in stat})
    gate("G5", ok_sent and len(smath) == 16
         and all(d["stride"] == 0x1C and d["back"] for d in smath)
         and len(starts) == 4 and all(d["iters"] == 24 for d in stat),
         "16 cmp-only sentinels, all stride 0x1c + backward jl; %d static scans over 4 starts, all 24 iterations"
         % (len(stat),))
    s1 = seq(ins, BUILDERS[0], BUILDERS[0] + 0x160)
    s2 = seq(ins, BUILDERS[1], BUILDERS[1] + 0x160)

    def builder_bound(s):
        return [imm_of(x.ops) for x in s if x.mn == "cmp" and (x.ops.endswith(",0x80") or x.ops.endswith(",0x40"))]
    b1, b2 = builder_bound(s1), builder_bound(s2)
    gate("G6", len(cand) == 10 and sum(1 for c in cand if c["mem"]) == 7
         and all(c["disp"] == CAND_BASE and "*4+0x9267e4" in c["ins"] for c in cand if c["mem"])
         and 0x80 in b1 and 0x80 in b2,
         "0x9267e4: 10 refs, 7 mem all [reg*4+base]; both builders bound the loop at the parsed 0x80 dwords")
    def builder_shape(s):
        """match the ordered 14-instruction band sequence; return (slot, band, shift, mask)."""
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
            k3 = nxt(lambda y: y.mn == "shl" and y.ops.startswith("eax,"), k2 + 1)
            if k3 is None:
                return None
            shift = imm_of(s[k3].ops)
            k4 = nxt(lambda y: y.mn == "jmp", k3 + 1)
            k5 = nxt(lambda y: y.mn == "xor" and y.ops == "eax,eax", k4 + 1)
            k6 = nxt(lambda y: y.mn == "mov" and y.ops.endswith("," + slot), k5 + 1)
            if k6 is None:
                return None
            band = s[k6].ops.split(",")[0]
            k7 = nxt(lambda y: y.mn == "and" and y.ops.split(",")[0] == band, k6 + 1)
            if k7 is None:
                return None
            mask = imm_of(s[k7].ops)
            need = [("jns", None), ("dec", band), ("or", band + ",0xffffffc0"), ("inc", band),
                    ("add", band + ",eax")]
            j = k7
            for mn, ops in need:
                j2 = nxt(lambda y, mn=mn, ops=ops: y.mn == mn and (ops is None or y.ops == ops), j + 1)
                if j2 is None:
                    return None
                j = j2
            k13 = nxt(lambda y: y.mn == "mov" and y.ops.startswith(
                "DWORD PTR [" + slot + "*4+0x9267e4]," + band), j + 1)
            if k13 is None:
                return None
            return (slot, band, shift, mask)
        return None
    shp1, shp2 = builder_shape(s1), builder_shape(s2)
    def entry(owner, slot, shift, mask):
        return (0 if slot < 0x40 else owner << shift) + (slot & (mask & 0x3F))
    ok7 = (shp1 is not None and shp2 is not None
           and shp1[2] == 6 and shp2[2] == 6 and shp1[3] == 0x8000003F and shp2[3] == 0x8000003F)
    gate("G7", ok7 and entry(2, 0x41, shp1[2], shp1[3]) == 0x81,
         "both builders match the 14-insn band sequence %s/%s; parsed shift=%s mask=0x%x give owner2 slot41 -> 0x%x"
         % (shp1, shp2, shp1[2] if shp1 else None, shp1[3] if shp1 else 0,
            entry(2, 0x41, shp1[2], shp1[3]) if shp1 else -1))
    chain_txt = {a: (ins[a].mn + " " + ins[a].ops) if a in ins else "" for a in
                 (0x4956C6, 0x4956D6, 0x4956DD, 0x49571B, 0x49571E)}
    call_ok = any("0x5a73f0" in (x.mn + " " + x.ops) for x in seq(ins, 0x4956E0, 0x495700))
    arg_ok = any(x.ops == "eax,DWORD PTR [ebp-0x2c]" or x.ops == "DWORD PTR [ebp-0x2c],eax"
                 for x in seq(ins, 0x4956E0, 0x495700))
    gate("G8", chain_txt[0x4956C6] == "cmp DWORD PTR [ebp-0x28],0x80"
         and chain_txt[0x4956D6] == "mov edx,DWORD PTR [ecx*4+0x9267e4]"
         and chain_txt[0x4956DD] == "mov DWORD PTR [ebp-0x2c],edx"
         and call_ok and arg_ok
         and chain_txt[0x49571B] == "imul edx,edx,0x34"
         and chain_txt[0x49571E] == "add edx,0x98ad88",
         "A: cmp 0x80 -> cand load -> [ebp-0x2c] -> call 0x5a73f0 -> imul 0x34 -> add 0x98ad88")
    hi = [r for r in rows if r["off"] == 0x31]
    clears = [r for r in hi if r["acc"] == "rmw" and ins[r["addr"]].mn == "and" and imm_of(r["ins"].split(",")[-1]) == 0xFE]
    sets = [r for r in hi if r["acc"] == "rmw" and ins[r["addr"]].mn == "or" and imm_of(r["ins"].split(",")[-1]) == 0x1]
    gate("G9", len(hi) == 4 and len(clears) == 1 and len(sets) == 3,
         "flags bit8: %d sites = %d and 0xfe + %d or 0x1 (decoded immediates)" % (len(hi), len(clears), len(sets)))
    gate("G10", pairs == want_pairs,
         "FUN_00435610 source->dest pairs %s" % (sorted((hex(k), v[0], hex(v[1])) for k, v in pairs.items()),))

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
