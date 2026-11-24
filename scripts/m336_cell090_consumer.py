#!/usr/bin/env python3
"""M336 — ds:0x8f0090: the difficulty BYTE's sibling cell — who consumes it, and is
difficulty index 6 reachable?

PICK: NEXT_PROMPT.md (x6) remaining clauses, first one (`0x8f0090`'s consumer).
Prior footing: `NAMED ## M332` (`evidence/m332_difficulty_census.txt:104`) ends its
clean-copy map at 0x8f0090 (0x8f0c11 -> 0x8f0090 at 0x488847/0x48884d) and leaves
"the consumer of the byte cell 0x8f0090" OPEN; `NAMED ## M335` — the six `#DIFF`
names live at 0x94d2ac (end 0x94d2c4) and the only clamp FUN_00423af0(0,6) is
INCLUSIVE at the array end.

Every number below is COMPUTED from the static image `scratch/m574/text.txt`
(objdump .text, Intel syntax) plus `ghidra_out/index.csv` (function extents).
Zero box time.

The census is ADDRESS-based, not displacement-based: a small linear-expression
evaluator replays each straight-line block and resolves a memory operand's base
register to `const + sum(coeff*symbol)`. A site is a RECORD-INDEXED alias only when
its constant term lands on the target FIELD modulo the stride and every coefficient
is a multiple of the stride (so the site can hit the target record); a site whose
base register the evaluator cannot resolve is counted as RESIDUE and is printed —
the "only reader" claim is only green when the residue at the target field is empty.

GATES (printed first, then asserted; every V row names a mutant in
scripts/m336_mutate.py):
  G1  three-form alias census of 0x8f0090: direct displacement, record-indexed
      (base register = stride multiple), and pointer walk. Asserts the resolvable
      LOADS are exactly {0x486788}, the stores are the six measured sites, and the
      residue at field +2 is EMPTY. Also asserts no instruction materialises
      0x8f0090 as an immediate (so no pointer form of the target itself exists).
  G2  frame/stride/record count from the operands: field+0 disp 0x8eff18, imul imm
      0x176, walk count 8, FRAME + 8*STRIDE == 0x8f0ac8 (the reset cell), record-1
      pointer 0x8f008e == FRAME + STRIDE.
  G3  the CONSUMER as a decoded def-use chain: k (init 0 at 0x4865dc, incremented
      0x4865e8, bounded by movsx BYTE ds:0x8f0c10) -> add ecx,1 -> imul ecx,ecx,0x176
      -> movsx edx,BYTE [ecx+0x8eff1a] -> [edx*4+0x94d2ac]; all four registers are
      the same ecx, and ZERO instructions sit between the load and the table use
      (so no clamp or mask can intervene).
  G4  the WRITE set: the pointer walk's stride is read from `add eax,0x176`, its
      count from `mov edx,0x8`, and iteration 1 lands exactly on 0x8f0090; each
      stride-indexed field+2 store's value comes from the SAME register the
      preceding load into that register filled, and that load reads 0x8f0c11.
  G5  the table the consumer indexes: base read from `mov esi,0x94d2ac`, end read
      from `cmp esi,0x94d2c4` in the loader => 6 rows; b=6 -> the end pointer.
  G6  the clamp census on the difficulty byte ds:0x8f0c11: all refs classified;
      exactly ONE read is clamp-guarded, its argument register is the register the
      site loaded, the pushed bounds decode to (0,6), and FUN_00423af0's own
      branch chain makes the upper bound INCLUSIVE => clamp(6,0,6)=6.
  G7  RIVALS, measured and killed: (a) "0x8f0090 is dead storage" — the address
      census finds a reachable reader; (b) "TARGET is record 1 offset 0" — the
      record frame is 0x8eff18 (field+0) and record 1's pointer is 0x8f008e.
"""
import bisect
import csv
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
IDX = os.path.join(ROOT, "ghidra_out/index.csv")

TARGET = 0x8F0090
DIFF = 0x8F0C11          # the difficulty byte (M332/M335)
FRAME = 0x8EFF18         # record base, field +0
FIELD2 = 0x8EFF1A        # record base + 2
STRIDE = 0x176
ARRAY_END = 0x8F0AC8
TABLE = 0x94D2AC
TABLE_END = 0x94D2C4

LINE = re.compile(r"^\s*([0-9a-f]{6,8}):\s+((?:[0-9a-f]{2} )+)\s*\t(.*)$")
HX = re.compile(r"0x[0-9a-f]+")
COND = re.compile(r"^(j[a-z]+|call|ret|retn)$")
REGS = re.compile(r"^(e?[abcd]x|e?[sd]i|e?[sb]p|e[bs]i|"
                  r"[abcd][lh]|[sd]il|[sb]pl|[abcd]x|[sd]i|[sb]p)$")
MUT = os.environ.get("M336_MUT", "")


def canon(r):
    r = r.strip().lower()
    if r in ("al", "ah", "ax", "eax"):
        return "eax"
    if r in ("bl", "bh", "bx", "ebx"):
        return "ebx"
    if r in ("cl", "ch", "cx", "ecx"):
        return "ecx"
    if r in ("dl", "dh", "dx", "edx"):
        return "edx"
    if r in ("si", "sil", "esi"):
        return "esi"
    if r in ("di", "dil", "edi"):
        return "edi"
    if r in ("bp", "bpl", "ebp"):
        return "ebp"
    if r in ("sp", "spl", "esp"):
        return "esp"
    return r


def load():
    ins = []
    with open(TEXT, errors="replace") as f:
        for line in f:
            m = LINE.match(line.rstrip("\n"))
            if not m:
                continue
            a = int(m.group(1), 16)
            bs = bytes.fromhex(m.group(2).replace(" ", ""))
            txt = m.group(3).strip()
            parts = txt.split(None, 1)
            ins.append({"a": a, "bs": bs, "mn": parts[0],
                        "ops": parts[1] if len(parts) > 1 else ""})
    ins.sort(key=lambda x: x["a"])
    return ins


def patch(i, old, new):
    """Rewrite an operand value in BOTH the bytes and the disassembled text."""
    ob, nb = old.to_bytes(4, "little"), new.to_bytes(4, "little")
    k = i["bs"].find(ob)
    if k >= 0:
        i["bs"] = i["bs"][:k] + nb + i["bs"][k + 4:]
    o, n = f"0x{old:x}", f"0x{new:x}"
    if o in i["ops"]:
        i["ops"] = i["ops"].replace(o, n, 1)
    else:
        o1, n1 = f"0x{old & 0xff:x}", f"0x{new & 0xff:x}"
        i["ops"] = i["ops"].replace(o1, n1, 1)
        k = i["bs"].find(bytes([old & 0xff]))
        if k >= 0:
            i["bs"] = i["bs"][:k] + bytes([new & 0xff]) + i["bs"][k + 1:]


def apply_mut(ins):
    """Mutants perturb the measured INPUT (the instruction stream), never a threshold."""
    if not MUT:
        return ins, []
    by = {i["a"]: i for i in ins}
    done = []
    if MUT == "drop_reader":
        ins = [i for i in ins if i["a"] != 0x486788]
        done.append(0x486788)
    elif MUT == "stride_175":
        patch(by[0x4866D2], STRIDE, 0x175); done.append(0x4866D2)
    elif MUT == "stride_175b":
        patch(site(by, 0x486782), STRIDE, 0x175); done.append(0x486782)
    elif MUT == "direct_moved":
        patch(by[0x48884D], TARGET, 0x8F0091); done.append(0x48884D)
    elif MUT == "count7":
        patch(site(by, 0x4E2495), 8, 7); done.append(0x4E2495)
    elif MUT == "clamp_hi5":
        patch(site(by, 0x486F2C), 6, 5); done.append(0x486F2C)
    elif MUT == "clamp_exclusive":
        i = site(by, 0x423B14)
        if i["mn"] != "jle":
            raise SystemExit("mutant: 0x423b14 is not jle")
        i["mn"] = "jl"; done.append(0x423B14)
    elif MUT == "value_src":
        patch(by[0x487E81], DIFF, 0x8F0C12); done.append(0x487E81)
    elif MUT == "table_end_moved":
        patch(site(by, 0x57AC88), TABLE_END, 0x94D2C0); done.append(0x57AC88)
    elif MUT == "table_base_moved":
        patch(site(by, 0x57AC74), TABLE, 0x94D2A8); done.append(0x57AC74)
    elif MUT == "walk_stride":
        patch(site(by, 0x4E24AB), STRIDE, 0x170); done.append(0x4E24AB)
    elif MUT == "chain_src":
        patch(site(by, 0x48677C), 0x8, 0xC); done.append(0x48677C)  # ecx <- [ebp-0xc], not the counter
    elif MUT == "clamp_arg_reg":
        i = by[0x486F37]
        if i["ops"] != "eax":
            raise SystemExit("mutant: 0x486f37 is not push eax")
        i["ops"] = "edx"; done.append(0x486F37)      # clamp gets an unrelated register
    elif MUT == "walk_stride":
        patch(site(by, 0x4E24AB), STRIDE, 0x170); done.append(0x4E24AB)
    elif MUT == "chain_src":
        i = site(by, 0x48677C)
        i["ops"] = i["ops"].replace("[ebp-0x8]", "[ebp-0xc]"); done.append(0x48677C)
    elif MUT == "alias_inserted":
        ins = list(ins) + [{"a": 0x4867AE, "bs": b"", "mn": "movsx",
                            "ops": "ebx,BYTE PTR [ecx+0x8eff1a]"}]
        ins.sort(key=lambda x: x["a"]); done.append("0x4867ae inserted")
    elif MUT == "clamp_arg_reg":
        i = by[0x486F37]
        if i["ops"] != "eax":
            raise SystemExit("mutant: 0x486f37 is not push eax")
        i["ops"] = "edx"; done.append(0x486F37)
    elif MUT == "naive_alias":
        done.append("algorithm")
    else:
        raise SystemExit(f"unknown mutant {MUT}")
    return ins, done


def hexes(s):
    return [int(x, 16) for x in HX.findall(s)]


def disp(i):
    """Signed displacement of the memory operand ('[eax-0x2]' -> -2)."""
    m = re.search(r"\[([^\]]+)\]", i["ops"])
    if not m:
        m = re.search(r"ds:(0x[0-9a-f]+)", i["ops"])
        return int(m.group(1), 16) if m else None
    inside = m.group(1).replace(" ", "")
    hits = re.findall(r"([+-])0x([0-9a-f]+)", inside)
    v = 0
    for sign, h in hits:
        v += -int(h, 16) if sign == "-" else int(h, 16)
    return v


def base_reg(i):
    m = re.search(r"\[([^\]]+)\]", i["ops"])
    if not m:
        return None
    for p in re.split(r"[+\-]", m.group(1).replace(" ", "")):
        r = p.split("*")[0]
        if REGS.match(r):
            return canon(r)
    return None


def scale_of(i, reg):
    m = re.search(rf"\[([^\]]+)\]", i["ops"])
    if not m:
        return 1
    for p in re.split(r"[+\-]", m.group(1).replace(" ", "")):
        parts = p.split("*")
        if len(parts) == 2 and canon(parts[0]) == reg and parts[1] in ("2", "4", "8"):
            return int(parts[1])
    return 1


def imm(i):
    outside = re.sub(r"\[[^\]]*\]", "", i["ops"])
    outside = re.sub(r"ds:0x[0-9a-f]+", "", outside)
    h = hexes(outside)
    return h[-1] if h else None


def dst_reg(i):
    d = i["ops"].split(",", 1)[0]
    d = re.sub(r"(BYTE|WORD|DWORD) PTR", "", d).strip()
    return canon(d) if REGS.match(d) else None


def src_reg(i):
    if "," not in i["ops"]:
        return None
    s = i["ops"].split(",", 1)[1].strip()
    return canon(s) if REGS.match(s) else None


def is_write(i):
    dst = i["ops"].split(",", 1)[0]
    return ("BYTE PTR" in dst or "DWORD PTR" in dst or "WORD PTR" in dst
            or "ds:0x" in dst or dst.strip().startswith("["))


class Expr:
    """const + sum(coeff * symbol)."""

    def __init__(self, c=0, terms=None):
        self.c = c
        self.t = dict(terms or {})

    def scale(self, k):
        return Expr(self.c * k, {s: v * k for s, v in self.t.items()})

    def add(self, o, sign=1):
        t = dict(self.t)
        for s, v in o.t.items():
            t[s] = t.get(s, 0) + sign * v
            if t[s] == 0:
                del t[s]
        return Expr(self.c + sign * o.c, t)

    def __repr__(self):
        parts = [f"{v}*{s}" for s, v in sorted(self.t.items())] + ([str(self.c)] if self.c or not self.t else [])
        return "+".join(parts)


ADDRS = []


def prepare(ins):
    global ADDRS
    ADDRS = [i["a"] for i in ins]


def block_start(ins, addr):
    k = bisect.bisect_left(ADDRS, addr)
    while k > 0 and not COND.match(ins[k - 1]["mn"]):
        k -= 1
    return k


def env_at(ins, addr):
    """Replay the straight-line block before `addr`; return {reg: Expr}."""
    end = bisect.bisect_left(ADDRS, addr)
    env = {}
    for x in ins[block_start(ins, addr):end]:
        mn, ops = x["mn"], x["ops"]
        if mn in ("mov", "movsx", "movzx"):
            d = dst_reg(x)
            if d is None:
                continue
            if "[" in ops.split(",", 1)[0] or "ds:0x" in ops.split(",", 1)[0]:
                env.pop(d, None)          # a store, not a definition of d
                continue
            s = src_reg(x)
            if s is not None:
                env[d] = env.get(s, Expr(0, {f"reg{s}": 1}))
            elif "[" in ops or "ds:0x" in ops:
                mm = re.search(r"\[([^\]]+)\]|ds:(0x[0-9a-f]+)", ops)
                env[d] = Expr(0, {("mem" + (mm.group(0) if mm else "?")): 1})
            else:
                env[d] = Expr(imm(x) or 0)
        elif mn in ("add", "sub"):
            d = dst_reg(x)
            if d is None:
                continue
            s = src_reg(x)
            iv = imm(x)
            left = env.get(d, Expr(0, {f"reg{d}": 1}))
            if s is not None and s != d:
                right = env.get(s, Expr(0, {f"reg{s}": 1}))
            elif s == d:
                right = left
            else:
                right = Expr(iv or 0)
            env[d] = left.add(right, 1 if mn == "add" else -1)
        elif mn == "shl" and imm(x) is not None:
            d = dst_reg(x)
            if d:
                env[d] = env.get(d, Expr(0, {f"reg{d}": 1})).scale(1 << imm(x))
        elif mn == "imul":
            d = dst_reg(x)
            iv = imm(x)
            if d and iv is not None:
                base = d if src_reg(x) in (None, d) else src_reg(x)
                env[d] = env.get(base, Expr(0, {f"reg{base}": 1})).scale(iv)
        elif mn == "lea":
            d = dst_reg(x)
            m = re.search(r"\[([^\]]+)\]", ops)
            if d and m:
                inside = m.group(1).replace(" ", "")
                total = Expr(0)
                for sign, part in re.findall(r"([+\-]?)([^+\-]+)", inside):
                    if not part:
                        continue
                    sg = -1 if sign == "-" else 1
                    pcs = part.split("*")
                    r = canon(pcs[0])
                    if REGS.match(pcs[0]):
                        k = int(pcs[1]) if len(pcs) == 2 else 1
                        total = total.add(env.get(r, Expr(0, {f"reg{r}": 1})).scale(k), sg)
                    else:
                        total = total.add(Expr(hexes(part)[0] if hexes(part) else 0), sg)
                env[d] = total
        elif mn in ("inc", "dec"):
            d = dst_reg(x)
            if d:
                env[d] = env.get(d, Expr(0, {f"reg{d}": 1})).add(Expr(1), 1 if mn == "inc" else -1)
        elif mn == "xor" and src_reg(x) == dst_reg(x):
            env[dst_reg(x)] = Expr(0)
        else:
            d = dst_reg(x)
            if d:
                env.pop(d, None)          # unknown writer: the register becomes opaque
    return env


def walk_evidence(ins, addr, reg):
    """Nearest `add reg,<stride multiple>` within +-0x400 B: the register is a record
    pointer stepped by the stride, so the site addresses a record FIELD with an index
    the straight-line evaluator could not pin."""
    lo = bisect.bisect_left(ADDRS, addr - 0x400)
    hi = bisect.bisect_left(ADDRS, addr + 0x400)
    cands = [x for x in ins[lo:hi] if x["mn"] == "add" and dst_reg(x) == reg
             and imm(x) is not None and imm(x) % STRIDE == 0]
    return min(cands, key=lambda x: abs(x["a"] - addr)) if cands else None


def site(by, addr):
    return by.get(addr, {"a": addr, "bs": b"", "mn": "nop", "ops": ""})


def fnof(addr, rows):
    for r in rows:
        b = int(r["addr"], 16)
        if b <= addr < b + int(r["size_bytes"]):
            return r["name"]
    return "?"


def main():
    ins, mutated = apply_mut(load())
    prepare(ins)
    rows = list(csv.DictReader(l for l in open(IDX) if not l.startswith("#")))
    by = {i["a"]: i for i in ins}
    gates = []

    def gate(gid, ok, detail):
        gates.append((gid, bool(ok), detail))

    # ---------------- G1: address-based alias census of TARGET ----------------
    lo, ld, lw, lu = [], [], [], []
    for i in ins:
        d = disp(i)
        if d is None:
            continue
        reg = base_reg(i)
        field = (d - FRAME) % STRIDE
        if reg is None:
            if d == TARGET:                 # a definite address: it can only alias itself
                lo.append((i, 2))
            continue
        if not (0 <= d <= 8 or FRAME - STRIDE <= d < ARRAY_END):
            continue       # outside the array window: with 8 records, no non-negative
                           # record index can fold this displacement onto the target
        sc = scale_of(i, reg)
        e = env_at(ins, i["a"]).get(reg)
        terms = {k: v * sc for k, v in e.t.items()} if e else {}
        c = (e.c if e else 0) * sc
        if e is not None:                    # the base register resolved: the field follows the address
            field = (c + d - FRAME) % STRIDE
        if not (FRAME <= (c + d if e is not None else d) < ARRAY_END + STRIDE):
            continue                        # outside the array: a non-negative record index cannot reach it
        if terms and all(v % STRIDE == 0 for v in terms.values()) and (c + d - FRAME) % STRIDE == 2:
            ld.append((i, c + d))
        elif e is not None and not terms and (c + d) == TARGET:
            lo.append((i, 2))
        else:
            w = walk_evidence(ins, i["a"], reg)
            if w is not None:
                lw.append((i, field, w))
            else:
                lu.append((i, field))
    if MUT == "naive_alias":
        # ALGORITHM mutant: the M332-style direct-displacement-only model
        ld, lw = [], []
    print(f"== G1 address census of 0x{TARGET:x} (frame {FRAME:#x}, stride {STRIDE:#x}) ==")
    print(f"  form A definite addresses: {len(lo)}")
    for i, f in lo:
        print(f"    {i['a']:#08x} {'W' if is_write(i) else 'R'} {i['mn']:7s} {i['ops']}")
    print(f"  form B record-indexed at field +2: {len(ld)}")
    for i, c in ld:
        off = (c - TARGET) // STRIDE if (c - TARGET) % STRIDE == 0 else None
        print(f"    {i['a']:#08x} {'W' if is_write(i) else 'R'} {i['mn']:7s} {i['ops']}"
              f"   const {c:#x} = target {('%+d' % off) if off is not None else '?'} records")
    print(f"  form C pointer walks: {len(lw)} sites; at field +2: "
          f"{[hex(i['a']) for i, f, w in lw if f == 2]}")
    for i, f, w in lw:
        if f == 2:
            e = env_at(ins, i["a"]).get(base_reg(i))
            start = ""
            if e is not None and not e.t:
                start = f" starts at record {(e.c + (disp(i) or 0) - FRAME) // STRIDE}"
            print(f"    {i['a']:#08x} {'W' if is_write(i) else 'R'} {i['mn']:7s} {i['ops']}"
                  f"   step {w['a']:#x} {w['ops']}{start}")
    res2 = [(i["a"], f) for i, f in lu if f == 2]
    print(f"  RESIDUE (base register unresolved): {len(lu)} sites, at field +2: {len(res2)} "
          f"{[hex(a) for a, _ in res2]}")
    loads = sorted([i["a"] for i, c in ld if not is_write(i)]
                   + [i["a"] for i, f in lo if not is_write(i)]
                   + [i["a"] for i, f, w in lw if f == 2 and not is_write(i)])
    stores = sorted([i["a"] for i, c in ld if is_write(i)]
                    + [i["a"] for i, f in lo if is_write(i)]
                    + [i["a"] for i, f, w in lw if f == 2 and is_write(i)])
    mat = [i["a"] for i in ins if imm(i) == TARGET]
    print(f"  => resolvable loads at field +2 {[hex(x) for x in loads]}; stores "
          f"{[hex(x) for x in stores]}")
    print(f"  => immediate materialisations of the target address: {[hex(x) for x in mat]}")
    expect_w = [0x48884D, 0x487E87, 0x525B83, 0x525CB9, 0x525D28, 0x4E24A2]
    gate("G1", loads == [0x486788] and not mat and not res2 and stores == sorted(expect_w),
         f"loads={[hex(x) for x in loads]} stores={len(stores)} residue@+2={len(res2)} "
         f"mat={len(mat)}")

    # ---------------- G2: frame + stride + count from the operands ----------------
    f0_read = disp(by[0x4866D8])
    f0_write = disp(by[0x487E60])
    stride_a = imm(by[0x4866D2])
    stride_b = imm(by[0x487E57])
    count = imm(site(by, 0x4E2495))
    walk_base = imm(site(by, 0x4E2490))
    rec1 = imm(by[0x525C42])
    end_cell = disp(by[0x4E2482])
    print("\n== G2 frame / stride / record count, read from the operands ==")
    print(f"  field+0 read disp {f0_read:#x}  write disp {f0_write:#x}")
    print(f"  imul immediates {stride_a:#x} (0x4866d2)  {stride_b:#x} (0x487e57)")
    print(f"  walk base {walk_base:#x} count {count}  record-1 pointer {rec1:#x}")
    print(f"  array end cell {end_cell:#x}")
    print(f"  TARGET - field+2 base = {TARGET - walk_base:#x} = "
          f"{(TARGET - walk_base) / stride_a:.3f} * stride")
    print(f"  record 1 = FRAME + stride = {FRAME + stride_a:#x} "
          f"(TARGET - record1 = {TARGET - (FRAME + stride_a)})")
    print(f"  FRAME + {count}*stride = {FRAME + count * stride_a:#x} (reset end cell {end_cell:#x})")
    gate("G2", f0_read == FRAME and f0_write == FRAME and stride_a == STRIDE == stride_b
         and count == 8 and rec1 == FRAME + STRIDE and end_cell == FRAME + count * STRIDE
         and TARGET == FRAME + STRIDE + 2 and TARGET == walk_base + STRIDE,
         f"frame={f0_read:#x} stride={stride_a:#x} count={count} "
         f"end={end_cell:#x} rec1={rec1:#x}")

    # ---------------- G3: the consumer as a def-use chain ----------------
    chain = (0x4865DC, 0x4865E8, 0x4865EE, 0x4865F8, 0x48677C, 0x48677F, 0x486782, 0x486788, 0x48678F)
    print("\n== G3 the consumer chain (registers decoded) ==")
    for a in chain:
        i = site(by, a)
        print(f"  {a:#08x} {i['mn']:7s} {i['ops']}   dst={dst_reg(i)} src={src_reg(i)}")
    ls, add1, imul, ld_site, feeds = site(by, 0x4865EE), site(by, 0x486782), site(by, 0x486782), site(by, 0x486788), site(by, 0x48678F)
    idx = imm(imul)
    # chain: the load's base register is the imul's destination; the add feeds it
    ld_base = base_reg(ld_site)
    add_dst, add_src = dst_reg(site(by, 0x48677F)), src_reg(site(by, 0x48677F))
    mul_dst = dst_reg(imul)
    mov_src_dst = dst_reg(site(by, 0x48677C))
    feed_src = src_reg(feeds)
    feed_idx = re.search(r"\[([^\]]+)\]", feeds["ops"]).group(1).split("*")[0]
    between = [x for x in ins if 0x486788 < x["a"] < 0x48678F]
    slot = "ebp-0x8"
    slot_ok = (slot in site(by, 0x4865DC)["ops"] and slot in site(by, 0x4865F5)["ops"]
               and slot in site(by, 0x48677C)["ops"])
    chain_ok = (ld_base == mul_dst == add_dst == mov_src_dst
                and ld_base == "ecx" and canon(feed_idx) == dst_reg(ld_site)
                and slot_ok and not between)
    print(f"  the imul input is the loop's own slot [{slot}]: {slot_ok} "
          f"(init 0x4865dc, test 0x4865f5, reload 0x48677c)")
    print(f"  load base {ld_base} == imul dst {mul_dst} == add dst {add_dst} == "
          f"mov dst {mov_src_dst}; feed index reg {canon(feed_idx)} == load dst "
          f"{dst_reg(ld_site)}; instructions between load and table use: {len(between)}")
    addr_k0 = walk_base + idx
    print(f"  imul imm {idx:#x}; k=0 -> {walk_base:#x}+{idx:#x} = {addr_k0:#x} "
          f"== TARGET: {addr_k0 == TARGET}")
    reset_cnt = imm(by[0x4E2444])
    print(f"  reset row count {reset_cnt} (0x4e2444) => rows k=0..{reset_cnt - 1}, "
          f"records 1..{reset_cnt}; record 1 is row 0")
    print(f"  the byte feeds {feeds['a']:#08x} {feeds['mn']} {feeds['ops']}")
    gate("G3", chain_ok and idx == STRIDE and addr_k0 == TARGET
         and disp(feeds) == TABLE and 0 < reset_cnt <= 7
         and "0x8f0c10" in ls["ops"] and site(by, 0x4865F8)["mn"] == "jge"
         and "0x0" in site(by, 0x4865DC)["ops"],
         f"chain={'ok' if chain_ok else 'BROKEN'} idx={idx:#x} k0={addr_k0:#x} "
         f"between={len(between)} table={disp(feeds):#x}")

    # ---------------- G4: the write set, register-aware ----------------
    walk_store = site(by, 0x4E24A2)
    walk_stride = imm(site(by, 0x4E24AB))
    walk_add, walk_dec, walk_jne = site(by, 0x4E24AB), site(by, 0x4E24B0), site(by, 0x4E24B1)
    iters = [walk_base + n * (walk_stride or 0) for n in range(count)]
    hit = [n for n, a in enumerate(iters) if a == TARGET]
    print("\n== G4 the pointer walk and the field+2 value sources ==")
    for a in (0x4E249C, 0x4E249F, 0x4E24A2, 0x4E24A4, 0x4E24A7, 0x4E24AB, 0x4E24B0, 0x4E24B1):
        i = by[a]
        print(f"  {a:#08x} {i['mn']:5s} {i['ops']}")
    print(f"  stride from {walk_add['a']:#x} 'add {walk_add['ops']}' = {walk_stride:#x}; "
          f"count {count}; addresses {iters[0]:#x}..{iters[-1]:#x}")
    print(f"  TARGET is iteration {hit} (stored as [eax] with {walk_store['ops'].split(',')[-1]})")
    srcs = []
    cand = [i for i, c in ld if is_write(i)] + [i for i, f, w in lw if f == 2 and is_write(i)]
    for i in cand:
        if i["a"] not in (0x487E87, 0x525B83, 0x525CB9, 0x525D28):
            continue
        r = src_reg(i)
        prev = [x for x in ins if x["a"] < i["a"] and is_write(x) is False
                and dst_reg(x) == r and "BYTE PTR" in x["ops"]]
        cell = disp(prev[-1]) if prev else None
        srcs.append((i["a"], r, cell))
    print("  field+2 stores: (site, stored register, cell that register was loaded from)")
    for a, r, c in srcs:
        print(f"    {a:#08x} {r} <- {('literal 0' if c is None else hex(c))}")
    src_ok = (len(srcs) == 4 and sum(1 for _, _, c in srcs if c == DIFF) == 3
              and all(c in (None, DIFF) for _, _, c in srcs))
    gate("G4", hit == [1] and walk_stride == STRIDE and src_ok
         and walk_store["mn"] == "mov" and walk_dec["mn"] == "dec" and walk_jne["mn"] == "jne",
         f"walk_stride={walk_stride:#x} iter={hit} sources={[('lit0' if c is None else hex(c)) for _, _, c in srcs]}")

    # ---------------- G5: the table geometry from the loader ----------------
    lbase = imm(site(by, 0x57AC74))       # mov esi,0x94d2ac
    lend = imm(site(by, 0x57AC88))        # cmp esi,0x94d2c4
    step = imm(by[0x57AC7C]) if 0x57AC7C in by else None
    print("\n== G5 the #DIFF table, base and end read from the loader ==")
    for a in (0x57AC74, 0x57AC88):
        i = by[a]
        print(f"  {a:#08x} {i['mn']:7s} {i['ops']}")
    nrows = (lend - lbase) // 4 if (lbase is not None and lend is not None) else 0
    print(f"  base {('0x%x' % lbase) if lbase else None} end "
          f"{('0x%x' % lend) if lend else None} rows={nrows}")
    for b in (0, 5, 6):
        addr = lbase + 4 * b
        what = ("first row" if b == 0 else "last row" if b == nrows - 1
                else "interior row" if b < nrows else "END POINTER, one past"
                if b == nrows else "PAST END")
        print(f"  b={b} -> {addr:#x}  ({what})")
    gate("G5", lbase == TABLE and lend == TABLE_END and nrows == 6
         and TABLE + 24 == TABLE_END and TABLE + 20 < TABLE_END,
         f"base={lbase:#x} end={lend:#x} rows={nrows}")

    # ---------------- G6: clamp census on the difficulty byte ----------------
    drefs = [i for i in ins if disp(i) == DIFF]
    print(f"\n== G6 every reference to the difficulty byte ds:0x{DIFF:x} ==")
    clamped = []
    for i in drefs:
        kind = "W" if is_write(i) else "R"
        extra = ""
        if kind == "R":
            win = [x for x in ins if i["a"] < x["a"] <= i["a"] + 20]
            call = [x for x in win if x["mn"] == "call" and "0x423af0" in x["ops"]]
            if call:
                caddr = call[0]["a"]
                prev = max([x["a"] for x in ins if x["mn"] == "call" and x["a"] < caddr] or [0])
                pushes = [x for x in ins if prev < x["a"] < caddr and x["mn"] == "push"]
                vals = [imm(x) for x in pushes]
                regs = [x["ops"].strip() for x in pushes]
                extra = f"  <clamp pushes {list(zip(regs, [None if v is None else hex(v) for v in vals]))}>"
                if regs and regs[-1] == dst_reg(i):
                    clamped.append(i["a"])
                else:
                    extra += "  <VALUE NOT THE SITE'S REGISTER>"
        print(f"  {i['a']:#08x} {kind} {i['mn']:7s} {i['ops']}{extra}   [{fnof(i['a'], rows)}]")
    w = [i for i in drefs if is_write(i)]
    r = [i for i in drefs if not is_write(i)]
    inc = (site(by, 0x423AFF)["mn"] == "jl" and site(by, 0x423B07)["mn"] == "jge"
           and site(by, 0x423B14)["mn"] == "jle")
    call_hi = imm(site(by, 0x486F2C))
    print(f"  writes={len(w)} reads={len(r)} clamp-guarded reads={[hex(x) for x in clamped]}")
    print("  FUN_00423af0:")
    for a in (0x423AFC, 0x423AFF, 0x423B04, 0x423B07, 0x423B11, 0x423B14, 0x423B16, 0x423B1B):
        print(f"    {a:#08x} {by[a]['mn']:5s} {by[a]['ops']}")
    print(f"  inclusive chain (jl/jge/jle)={inc}  clamp hi pushed={call_hi}")
    print(f"  clamp(6,0,{call_hi}) = 6 -> [{6}*4+{TABLE:#x}] = {TABLE + 24:#x} "
          f"== the loader end: {TABLE + 24 == TABLE_END}")
    gate("G6", len(w) == 6 and len(r) == 6 and clamped == [0x486F30] and inc
         and call_hi == 6 and TABLE + 4 * call_hi == TABLE_END,
         f"writes={len(w)} reads={len(r)} clamped={[hex(x) for x in clamped]} "
         f"hi={call_hi} inclusive={inc}")

    # ---------------- G7: the two rivals ----------------
    dead = (not loads and not res2)
    rec1_ok = (rec1 == FRAME + STRIDE) and (TARGET - rec1 == 2) and f0_read == FRAME
    print("\n== G7 rivals ==")
    print(f"  R1 '0x8f0090 is dead storage': resolvable loads={[hex(x) for x in loads]} "
          f"-> {'STILL STANDING' if dead else 'KILLED'}")
    print(f"  R2 'TARGET is record 1 offset 0': rec1={rec1:#x} TARGET-rec1={TARGET - rec1} "
          f"rec1-FRAME={rec1 - FRAME:#x} field+0 at {f0_read:#x} -> "
          f"{'STILL STANDING' if not rec1_ok else 'KILLED'}")
    gate("G7", not dead and rec1_ok,
         f"R1 killed by {[hex(x) for x in loads]}; R2 killed: rec1={rec1:#x}")

    # ---------------- verdict ----------------
    print("\n== gates ==")
    for gid, ok, detail in gates:
        print(f"  {gid}: {'PASS' if ok else 'FAIL'}  {detail}")
    digest = hashlib.sha256(repr([(g, o, d) for g, o, d in gates]).encode()).hexdigest()[:16]
    npass = sum(1 for _, ok, _ in gates if ok)
    print(f"\ndigest={digest} gates={npass}/{len(gates)}"
          + (f"  MUT={MUT} ({mutated})" if MUT else ""))
    verdict = "PASS" if npass == len(gates) else "FAIL"
    print(f"{verdict} M336: {npass}/{len(gates)} gates" + (f" [mutant {MUT}]" if MUT else ""))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
