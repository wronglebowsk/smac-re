#!/usr/bin/env python3
"""M178-M180: what ds:0x99aa38 IS, who else writes it, and who consumes the aggregator's two globals.

  M178  FUN_0041a8f0's 0x41a9xx block is a 19-bit PACK/UNPACK round-trip of the selected object's
        flag dword [ds:0x8f0d60+0x38] through ds:0x99aa38; the unpack restores EXACTLY the inverse
        permutation, 9 source bits are destroyed by the mask, and the rebuilt dword is published
        into the faction block at +0x94d600 (stride folded from the byte [ctx+4]).
  M179  ds:0x99aa38 is the SAVE BAND's staging dword: 33 stores in 14 functions, every store outside
        FUN_0041a8f0 sits directly before a writer call, 9 of them before `call 0x6267a5` with the
        tag-name / 0x41 push triple whose names read out of terran.exe are GOVOPTIONS, ASSEMBLEGROUP,
        AIEDITOR, AIEDITOR2, FACOBJ, RULES, FACTION; FUN_00518c50 is a set/clear-scratch-BIT helper;
        the leg-sequence writers agree on one scratch bit band (0..17, 0..18 for the UI writer) and
        read it back in one ascending order.
  M180  consumers of ds:0x920720 (the aggregator's second accumulator) and ds:0x9204b0 (the
        [block+0x94d4a8] stamp export): writer sets, read sets, and the tests they are used in.

    python3 scripts/m178_m180_scratchband.py            # all three
    python3 scripts/m178_m180_scratchband.py m179       # one

All derived from the static .text dump (scratch/m574/text.txt), ghidra_out/index.csv containment and
terran.exe's own section table. No box time, no gdb, no Wine.
"""
import importlib.util
import os
import re
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
_spec = importlib.util.spec_from_file_location("field_census", os.path.join(HERE, "field_census.py"))
FC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(FC)
INS, LOW, fnof, IDX = FC.INS, FC.LOW, FC.fnof, FC.IDX
INDEX = {n: (a, z) for a, n, z in IDX}
POS_OF_PC = {pc: i for i, (pc, _) in enumerate(INS)}
R = {}

SCRATCH = "0x99aa38"
SUB8 = {"al": ("eax", 0), "ah": ("eax", 8), "cl": ("ecx", 0), "ch": ("ecx", 8),
        "dl": ("edx", 0), "dh": ("edx", 8), "bl": ("ebx", 0), "bh": ("ebx", 8)}
DREGS = ("eax", "ecx", "edx", "ebx", "esi", "edi")
MEM = r"(?:dword\s+ptr\s+|byte\s+ptr\s+|word\s+ptr\s+|fword\s+ptr\s+)?"
# objdump prints `DWORD PTR DS:0x985ac4`: a class of [0-9a-f]+ stops at the 'x', so write 0x[0-9a-f]+
DSOP = r"(?:dword|byte|word)\s+ptr\s+ds:0x[0-9a-f]+"
MEMOP = r"(?:" + DSOP + r"|dword\s+ptr\s+\[[^\]]+\]|\[[^\]]+\]|[a-z0-9]+)"


def ok(mid, cond, text):
    R[mid] = cond
    print("{mid}  {verdict} - {text}".format(mid=mid, verdict="PASS" if cond else "FAIL", text=text))


def pc1(x):
    return int(x, 16) if x.startswith("0x") else int(x)


def one_bit(imm, width):
    return [b for b in range(width) if (imm >> b) & 1] \
        if bin(imm & ((1 << width) - 1)).count("1") == 1 else None


def window(lo, hi):
    return [(pc, s) for pc, s in INS if lo <= pc <= hi]


def idx_of(pc, win):
    for i, (p, _) in enumerate(win):
        if p == pc:
            return i
    return 0


def norm(s):
    return " ".join(s.lower().split())


def resolve_mask(reg, i, win):
    """Nearest preceding `mov <reg>,0ximm` - these legs park their bit mask in edi/esi."""
    for j in range(i - 1, -1, -1):
        sl = norm(win[j][1])
        m = re.match(r"^mov\s+%s\s*,\s*(0x[0-9a-f]+)$" % re.escape(reg), sl)
        if m:
            return pc1(m.group(1)), win[j][0]
        if re.match(r"^mov\s+%s\s*," % re.escape(reg), sl):
            return None, win[j][0]
    return None, None


def provenance(reg, i, win):
    """Where the tested register's value came from - ONE hop, never a guess."""
    for j in range(i - 1, -1, -1):
        m = re.match(r"^mov[a-z]*\s+" + MEM + re.escape(reg) + r"\s*,\s*(.+)$", norm(win[j][1]))
        if m:
            return m.group(1).strip()
    return "<unprovenanced %s>" % reg


def branch_between(tpc, opc, win):
    for pc, s in win:
        if tpc < pc < opc:
            m = re.match(r"^(j[a-z]+)\s", norm(s))
            if m:
                return m.group(1)
    return ""


def parse_test(sl, i, win):
    """A leg-source dict for a `test <a>,<b>` line, else None."""
    m = re.match(r"^test\s+([a-z0-9]+),\s*(.+)$", sl)
    if m:
        reg, val = m.group(1), m.group(2).strip()
        if reg == val:
            return {"kind": "truth", "value_reg": reg, "src_bit": None, "src_operand": "", "truth": True}
        if val in DREGS or val in SUB8:
            mask, _ = resolve_mask(val, i, win)
            if mask is not None and one_bit(mask, 32):
                return {"kind": "bit", "value_reg": reg, "src_bit": one_bit(mask, 32)[0],
                        "src_operand": "", "truth": False}
            mask, _ = resolve_mask(reg, i, win)
            if mask is not None and one_bit(mask, 32):
                return {"kind": "bit", "value_reg": val, "src_bit": one_bit(mask, 32)[0],
                        "src_operand": "", "truth": False}
            return None
        if re.fullmatch(r"0x[0-9a-f]+|\d+", val):
            imm = pc1(val)
            base, width = (SUB8[reg][1], 8) if reg in SUB8 else (0, 32)
            bits = one_bit(imm, width)
            if bits:
                return {"kind": "bit", "value_reg": SUB8[reg][0] if reg in SUB8 else reg,
                        "src_bit": base + bits[0], "src_operand": "", "truth": False}
        return None
    m = re.match(r"^test\s+(" + MEMOP + r"),\s*(0x[0-9a-f]+|\d+)$", sl)
    if m:                                                    # `test BYTE PTR [esi+0x94f4b0],0x20`
        opnd, imm = m.group(1), pc1(m.group(2))
        width = 8 if opnd.startswith("byte") else 32
        bits = one_bit(imm, width)
        if bits:
            return {"kind": "bit", "value_reg": "", "src_bit": bits[0], "src_operand": opnd, "truth": False}
    return None


def pack_legs(win, store_pc):
    """test -> or/and on the scratch register (eax, al, ah): one leg per scratch bit."""
    out, free = [], None
    for i, (pc, s) in enumerate(win):
        sl = norm(s)
        src = parse_test(sl, i, win)
        if src is not None:
            src["pc"] = pc
            free = src
            continue
        m = re.match(r"^(or|and)\s+(al|ah|eax)\s*,\s*(0x[0-9a-f]+|\d+)$", sl)
        bits = None
        if m:
            op, reg, imm = m.group(1), m.group(2), pc1(m.group(3))
            base, width = (SUB8[reg][1], 8) if reg in SUB8 else (0, 32)
            bits = one_bit(imm, width) if op == "or" else [b for b in range(width) if not (imm >> b) & 1]
        if m and bits and len(bits) == 1:
            if free is None or pc - free["pc"] > 20:
                continue
            leg = dict(free)
            leg["scratch"] = base + bits[0]
            leg["op_pc"] = pc
            leg["branch"] = branch_between(free["pc"], pc, win)
            leg["src_operand"] = leg["src_operand"] or provenance(leg["value_reg"], idx_of(free["pc"], win), win)
            out.append(leg)
            free = None
            continue
        m = re.match(r"^shr\s+(%s)\s*,\s*(0x[0-9a-f]+|\d+)$" % "|".join(DREGS), sl)
        if m and i + 1 < len(win) and re.match(r"^and\s+%s\s*,\s*0x1$" % re.escape(m.group(1)),
                                                norm(win[i + 1][1])):      # `shr reg,N; and reg,1`
            out.append({"kind": "norm", "scratch": 0, "src_bit": pc1(m.group(2)), "value_reg": m.group(1),
                        "truth": False, "pc": win[i][0], "op_pc": win[i + 1][0], "branch": "",
                        "src_operand": provenance(m.group(1), i, win)})
            continue
        m = re.match(r"^and\s+(%s)\s*,\s*(0x[0-9a-f]+)$" % "|".join(DREGS), sl)
        if m and one_bit(pc1(m.group(2)), 32) == [31] \
                and "neg" in " ".join(norm(s2) for pc2, s2 in win[i:i + 5]) \
                and "sbb" in " ".join(norm(s2) for pc2, s2 in win[i:i + 5]):   # `and reg,0x80000000; neg; sbb`
            out.append({"kind": "norm", "scratch": 0, "src_bit": 31, "value_reg": m.group(1), "truth": False,
                        "pc": win[i][0], "op_pc": win[i][0], "branch": "",
                        "src_operand": provenance(m.group(1), i, win)})
    return out


def decode_legs(win, ctx=None):
    """test ON the scratch -> or into a destination: one leg per scratch bit."""
    ctx = ctx or win
    out, pend = [], None
    for i, (pc, s) in enumerate(win):
        sl = norm(s)
        m = re.match(r"^test\s+(byte ptr ds:%s|dword ptr ds:%s|al|ah|eax),\s*(.+)$" % (SCRATCH, SCRATCH), sl)
        if m:
            form, val = m.group(1), m.group(2).strip()
            if re.fullmatch(r"0x[0-9a-f]+|\d+", val):
                imm = pc1(val)
                base, width = (SUB8[form][1], 8) if form in SUB8 else (0, 32)
                bits = one_bit(imm, width)
                sb = base + bits[0] if bits else None
            else:
                mask, _ = resolve_mask(val, idx_of(pc, ctx), ctx)
                bits = one_bit(mask, 32) if mask is not None else None
                sb = bits[0] if bits else None
            if sb is not None:
                pend = (pc, sb)
            continue
        if pend is not None:
            m = re.match(r"^or\s+(" + DSOP + r"|dword\s+ptr\s+\[[^\]]+\]|[a-z0-9]+),\s*(.+)$", sl)
            if not m:
                continue
            dest, val = m.group(1), m.group(2).strip()
            if re.fullmatch(r"0x[0-9a-f]+", val):
                imm = pc1(val)
            elif val in DREGS or val in SUB8:
                imm, _ = resolve_mask(val, idx_of(pc, ctx), ctx)
            else:
                imm = None
            if imm is None:
                bit = "?"
            else:
                base = SUB8[dest][1] if dest in SUB8 else 0
                bits = one_bit(imm, 8 if dest in SUB8 else 32)
                bit = base + bits[0] if bits else "?"
            out.append({"scratch": pend[1], "dest_operand": dest, "dest_bit": bit, "test_pc": pend[0],
                        "or_pc": pc, "mask": val})
            pend = None
            continue
        m = re.match(r"^test\s+(al|ah|eax)\s*,\s*(0x[0-9a-f]+|\d+)$", sl)
        if m:
            form, imm = m.group(1), pc1(m.group(2))
            base, width = (SUB8[form][1], 8) if form in SUB8 else (0, 32)
            bits = one_bit(imm, width)
            if bits:
                pend = (pc, base + bits[0])
    return out


def stores(tok=SCRATCH):
    return [(pc, fnof(pc)) for pc, s in LOW if re.search(r"mov\s+(dword\s+ptr\s+)?ds:%s," % tok, s)]


def exe_strings():
    """terran.exe's own section table -> a VA-to-string reader (image base 0x400000)."""
    b = open(os.path.join(ROOT, "terran.exe"), "rb").read()
    pe = struct.unpack_from("<I", b, 0x3c)[0]
    nsec = struct.unpack_from("<H", b, pe + 6)[0]
    optsz = struct.unpack_from("<H", b, pe + 20)[0]
    base, img = pe + 24 + optsz, 0x400000
    secs = []
    for i in range(nsec):
        o = base + i * 40
        vsize, va, rawsz, rawptr = struct.unpack_from("<IIII", b, o + 8)
        secs.append((img + va, vsize, rawptr, rawsz))

    def at(va, n=24):
        for v, vz, rp, rz in secs:
            if v <= va < v + max(vz, rz) and (va - v) < rz:
                raw = b[rp + (va - v): rp + (va - v) + n]
                cut = raw.find(b"\0")
                return raw[:cut if cut >= 0 else n].decode(errors="replace")
        return None
    return at


def next_call(pc, span=14):
    for pc2, s2 in INS[POS_OF_PC[pc] + 1:POS_OF_PC[pc] + 1 + span]:
        m = re.match(r"^call\s+(0x[0-9a-f]+)$", norm(s2))
        if m:
            return m.group(1)
    return None


# ---------------------------------------------------------------- M178
def m178():
    fn = "FUN_0041a8f0"
    a, z = INDEX[fn]
    full = window(a, a + z)
    st = sorted(pc for pc, f in stores() if f == fn)
    zero = [pc for pc, s in LOW if norm(s) == "mov dword ptr ds:%s,0x0" % SCRATCH]
    pk = pack_legs(window(a, max(st)), max(st))
    dc = decode_legs(window(max(st), a + z), full)
    pbits = sorted(l["scratch"] for l in pk)
    dbits = sorted(l["scratch"] for l in dc)
    print("M178 %s @%s: %d stores to %s (%d of them the whole-image zero-init `mov dword ptr ds:%s,0x0` at %s)"
          % (fn, hex(a), len(st), SCRATCH, len(zero), SCRATCH, [hex(x) for x in zero]))
    for l in pk:
        print("   PACK   scratch bit %-3s <- %s%s [%s %s]  %s"
              % (l["scratch"], l["src_operand"], "" if l["truth"] else " bit %s" % l["src_bit"],
                 "truth/sign" if l["truth"] else "bit", l["branch"] or l["kind"], hex(l["pc"])))
    for l in dc:
        print("   UNPACK scratch bit %-3s -> %s %s  (%s)" % (l["scratch"], l["dest_operand"], l["dest_bit"],
                                                            hex(l["or_pc"])))
    pmap, dmap = {l["scratch"]: l for l in pk}, {l["scratch"]: l for l in dc}
    inv = [(sb, pmap.get(sb, {}).get("src_bit"), dmap.get(sb, {}).get("dest_bit")) for sb in range(19)]
    bad = [(sb, s, d) for sb, s, d in inv if s != d or s is None]
    for sb, s, d in inv:
        print("   INVERSE bit %-3s pack<-src %-4s unpack->dst %-4s %s" % (sb, s, d, "OK" if s == d else "X"))
    via_field = 0
    for l in dc:
        d = l["dest_operand"]
        if d == "dword ptr [eax+0x38]":
            via_field += 1
            continue
        if d in SUB8:
            k = idx_of(l["or_pc"], full)
            for pc2, s2 in reversed(full[max(0, k - 6):k]):
                if re.match(r"^mov\s+%s,\s*dword ptr \[eax\+0x38\]" % SUB8[d][0], norm(s2)):
                    via_field += 1
                    break
    print("M178 unpack destinations that ARE the same field [eax+0x38] (eax = ds:0x8f0d60; the byte legs load "
          "the dword into ecx, or cl/ch, and write it back): %d/%d" % (via_field, len(dc)))
    seq = [norm(s) for pc, s in window(0x41abd4, 0x41abe5)]
    mask = [hex(pc) for pc, s in full if norm(s) == "and ecx,0xf000000"]
    pub = [hex(pc) for pc, s in LOW if norm(s).startswith("mov dword ptr [edx*4+0x94d600],ecx")]
    fold = [norm(s) for pc, s in window(0x41ad7a, 0x41ad94)
            if norm(s) in ("shl edx,0x6", "add edx,ecx", "lea edx,[ecx+edx*2]", "shl edx,0x4", "sub edx,ecx")]
    read_bits = sorted(set(l["src_bit"] for l in pk if l["src_bit"] is not None))
    destroyed = sorted(set(range(32)) - set(read_bits) - {24, 25, 26, 27})
    print("M178 mask sequence 0x41abd4-0x41abe5: %s" % " | ".join(seq))
    print("M178 mask sites %s ; publication sites %s ; fold chain %s" % (mask, pub, fold))
    print("M178 source bits read %s (%d); kept by the mask [24, 25, 26, 27]; cleared and never restored %s (%d)"
          % (read_bits, len(read_bits), destroyed, len(destroyed)))
    ok("M178",
       len(st) == 20 and len(zero) == 1 and pbits == list(range(19)) and dbits == list(range(19))
       and not bad and via_field == 19 and len(mask) == 1 and len(pub) == 1 and len(fold) == 5
       and "and ecx,0xf000000" in seq and "mov dword ptr [eax+0x38],ecx" in seq
       and destroyed == [1, 2, 3, 4, 8, 14, 28, 29, 30],
       ("the 0x41a9xx block is a 19-bit LOSSY FILTER on the UI record, not a copy: {n} stores to {sc} (the "
        "zero-init at {zero} plus one after each of 19 legs). The pack legs feed scratch bits 0..18, each "
        "from exactly one bit of the selected object's flag dword [ds:0x8f0d60+0x38] (source bits {rb}), and "
        "the unpack legs restore EXACTLY the inverse permutation ({inv}/19 legs agree, {vf}/19 destinations "
        "are that same field) after `mov ecx,[eax+0x38]; and ecx,0xf000000; mov [eax+0x38],ecx` ({mask}) "
        "keeps only bits 24-27 - so 9 source bits ({dstr}) are cleared and never restored. The rebuilt dword "
        "is then published to the FACTION BLOCK FIELD +0x94d600 (`mov DWORD PTR [edx*4+0x94d600],ecx` at "
        "{pub}) with edx = the 5-instruction fold of the byte [ctx+4] into fac*2095 dwords = fac*8380 bytes "
        "({fold}).").format(n=len(st), sc=SCRATCH, zero=[hex(x) for x in zero], rb=read_bits,
                            inv=19 - len(bad), vf=via_field, mask=mask, dstr=destroyed, pub=pub, fold=fold))


# ---------------------------------------------------------------- M179
def m179():
    st = stores()
    by_fn = {}
    for pc, f in st:
        by_fn.setdefault(f, []).append(pc)
    print("M179 %d stores to %s in %d functions: %s"
          % (len(st), SCRATCH, len(by_fn), {k: [hex(x) for x in sorted(v)] for k, v in sorted(by_fn.items())}))
    tables = {}
    for fn in sorted(by_fn):
        a, z = INDEX[fn]
        sp = max(by_fn[fn])
        pk, dc = pack_legs(window(a, sp), sp), decode_legs(window(sp, a + z), window(a, a + z))
        tables[fn] = (pk, dc)
        print("   %-14s pack %2d legs bits %-22s | unpack %2d legs order %s"
              % (fn, len(pk), str(sorted(set(l["scratch"] for l in pk))), len(dc), [l["scratch"] for l in dc]))
    bands = {f: sorted(set(l["scratch"] for l in tables[f][0])) for f in tables if tables[f][0]}
    band_ok = {f: (max(b) <= 17 or (f == "FUN_0041a8f0" and max(b) == 18)) for f, b in bands.items()}
    print("M179 band ceiling per writer (<=17, FUN_0041a8f0 may reach 18): %s" % band_ok)
    seq_writers = sorted(f for f in tables if len(tables[f][1]) >= 12)
    asc = {f: [l["scratch"] for l in tables[f][1]] == sorted(l["scratch"] for l in tables[f][1])
           for f in seq_writers}
    print("M179 unpack order ascending for the %d writers with >=12 unpack legs: %s" % (len(seq_writers), asc))
    key = lambda l: (l["dest_operand"], str(l["dest_bit"]))
    d5 = [key(l) for l in tables["FUN_004dc5f0"][1]]
    d7 = [key(l) for l in tables["FUN_0057c550"][1]]
    same = sum(1 for x, y in zip(d5, d7) if x == y)
    print("M179 FUN_004dc5f0 vs FUN_0057c550 unpack legs: %d vs %d, %d identical in order"
          % (len(d5), len(d7), same))
    srcs = {f: sorted(set("%s%s" % (l["src_operand"], "" if l["truth"] else ":bit" + str(l["src_bit"]))
                          for l in tables[f][0])) for f in tables if tables[f][0]}
    for f in sorted(srcs):
        print("   %-14s pack sources: %s" % (f, srcs[f]))
    calls = {}
    for pc, f in st:
        calls.setdefault(next_call(pc), []).append((f, hex(pc)))
    print("M179 nearest following call after each store: %s"
          % {str(k): [f for f, _ in v] for k, v in sorted(calls.items(), key=lambda kv: str(kv[0]))})
    at = exe_strings()
    tags = {}
    for pc, f in st:
        i = POS_OF_PC[pc]
        found = set()
        for pc2, s2 in INS[max(0, i - 8):i]:                       # pushes that precede the store
            m = re.match(r"^push\s+(0x[0-9a-f]+)$", norm(s2))
            if m:
                sv = at(pc1(m.group(1)))
                if sv and re.fullmatch(r"[A-Z0-9_]{4,16}", sv):
                    found.add("%s@%s" % (sv, m.group(1)))
        for pc2, s2 in INS[i + 1:i + 41]:                          # ... or feed the writer call after it
            sl = norm(s2)
            if sl.startswith("call 0x6267a5"):
                break
            m = re.match(r"^push\s+(0x[0-9a-f]+)$", sl)
            if m:
                sv = at(pc1(m.group(1)))
                if sv and re.fullmatch(r"[A-Z0-9_]{4,16}", sv):
                    found.add("%s@%s" % (sv, m.group(1)))
        if found:
            tags.setdefault(f, set()).update(found)
    for f in sorted(tags):
        print("   %-14s tag names pushed before its store: %s" % (f, sorted(tags[f])))
    sizes = sorted(set(norm(s) for pc, f in st for _q, s in INS[POS_OF_PC[pc] - 8:POS_OF_PC[pc]]
                       if norm(s).startswith("push 0x")))
    print("M179 push immediates preceding the stores: %s" % sizes)
    triples = []
    for pc, f in st:
        if next_call(pc) != "0x6267a5":
            continue
        j = None
        for k in range(POS_OF_PC[pc] + 1, POS_OF_PC[pc] + 40):
            if norm(INS[k][1]).startswith("call 0x6267a5"):
                j = k
                break
        if j is None:
            continue
        pushes = [m.group(1) for m in (re.match(r"^push\s+(0x[0-9a-f]+)$", norm(x))
                                       for _p, x in INS[j - 14:j]) if m]
        if len(pushes) >= 3:
            extra, size, name = pushes[-3:]
            triples.append((f, at(pc1(name)), size, extra))
    print("M179 the writer call is (name, size, extra) - stores that feed 0x6267a5:")
    for f, nm, size, extra in triples:
        print("   %-14s name=%-14s size=%-5s extra=%s" % (f, nm, size, extra))
    n41 = sum(1 for x in triples if x[2] == "0x41")
    n1 = sum(1 for x in triples if x[2] == "0x1")
    print("M179 sizes at those 9 calls: 0x41 x%d, 0x1 x%d" % (n41, n1))
    sav = subprocess.run(["bash", "-lc",
                          "cd %s && for t in GOVOPTIONS ASSEMBLEGROUP AIEDITOR AIEDITOR2 FACOBJ; do "
                          "for f in *.SAV programs/*.SAV programs/*.SC maps/*.MP; do [ -f \"$f\" ] || continue; "
                          "if grep -qa \"$t\" \"$f\"; then echo \"$t in $f\"; fi; done; done | sort | head -30"
                          % ROOT], capture_output=True, text=True).stdout.strip()
    print("M179 tag names present as ASCII in the save/scenario/map files on disk: %s"
          % (sav.replace("\n", "; ") or "NONE (the file stores numeric tags; these are the exe's "
                                          "record-type NAME table)"))
    ha, hz = INDEX["FUN_00518c50"]
    helper = [norm(s) for pc, s in window(ha, ha + hz)]
    helper_ok = all(x in helper for x in ("mov eax,0x1", "shl eax,cl", "or dword ptr ds:%s,eax" % SCRATCH,
                                          "mov edx,0x1", "shl edx,cl", "not edx", "and eax,edx",
                                          "mov ds:%s,eax" % SCRATCH))
    print("M179 FUN_00518c50 (%d insns, %d bytes) is a set/clear scratch-BIT helper: %s" % (len(helper), hz, helper_ok))
    c1c = [l for l in tables["FUN_004dc100"][0] if "0x94d8" in l["src_operand"]]
    sign = [(l["scratch"], l["src_operand"], l["branch"]) for l in tables["FUN_004dc100"][0]
            if l["truth"] and "0x94d80c" in l["src_operand"]]
    fold100 = [norm(s) for pc, s in window(0x4dc1a4, 0x4dc1b6)
               if norm(s) in ("shl edx,0x6", "add edx,edi", "lea esi,[edi+edx*2]", "shl esi,0x4",
                              "sub esi,edi", "shl esi,0x2")]
    staging = {tok: len(stores(tok)) for tok in ("0x99aa1c", "0x99aa20")}
    ok("M179",
       len(st) == 33 and len(by_fn) == 14 and all(band_ok.values()) and max(bands["FUN_0041a8f0"]) == 18
       and all(asc.values()) and len(d5) == 18 and same == 18 and len(c1c) >= 5 and len(sign) == 2
       and helper_ok and tags.get("FUN_0041a8f0") == {"GOVOPTIONS@0x6899ec"} and len(tags) == 12
       and len(calls.get("0x6267a5", [])) == 9 and len(triples) == 9 and n41 == 7 and n1 == 2
       and all(v > 500 for v in staging.values()),
       ("{sc} is the SAVE BAND'S STAGING DWORD, not one record's flag: {n} stores in {nf} functions. Its "
        "neighbours ds:0x99aa1c / ds:0x99aa20 carry {s1} / {s2} stores game-wide (the 0x626634 write-bytes "
        "arguments), and this slot is that staging record's third field: {nrec} of the {nout} stores outside "
        "FUN_0041a8f0 sit directly before `call 0x6267a5` (the tagged record writer) with the push triple "
        "(name, size, extra), and the sizes are NOT uniform: 7 pass 0x41 and the TECHRANDOM pair passes "
        "0x1 (0x510289 / 0x5170ae); the name pointers read out of terran.exe as {tags} - "
        "one record type per writer, all of them packing the SAME staging slot (the names are the exe's "
        "record-type NAME table: none appears as ASCII in the save file on disk, which stores numeric tags). "
        "FUN_00518c50 is a set/clear-scratch-BIT helper indexed by arg1 (`mov eax,1; shl eax,cl; or "
        "ds:{sc},eax` / `not edx; and eax,edx; mov ds:{sc},eax`), called with (bit, value). The leg-sequence "
        "writers agree on one bit band - every pack leg touches bits 0..17, only FUN_0041a8f0 reaches 18 "
        "({band41}) - and all {nseq} writers with a full leg sequence read them back in ONE ascending order ({asc}); "
        "FUN_004dc5f0 and FUN_0057c550 share their unpack sequence LEG FOR LEG ({same}/18 identical "
        "destination operand+bit pairs) while FUN_004dc8d0 / FUN_004dcc10 feed the same positions from the "
        "HIGH band of ds:0x985ac4 plus ds:0x985ae8 / ds:0x985dc8, and FUN_004dc100 is the only writer whose "
        "sources are per-faction RECORD fields ({nstruct} of its legs read [esi+0x94d80c..0x94d81c], the M164 "
        "20-byte struct, esi = fac*8380 folded at 0x4dc1a9-0x4dc1b6: {fold100}), serializing the 0x94d80c "
        "dword as a SIGN PAIR ({sign}).").format(sc=SCRATCH, n=len(st), nf=len(by_fn), s1=staging["0x99aa1c"],
                                                 s2=staging["0x99aa20"], nrec=len(calls.get("0x6267a5", [])),
                                                 nout=len([1 for pc, f in st if f != "FUN_0041a8f0"]),
                                                 tags=sorted(set(t.split("@")[0] for v in tags.values() for t in v)),
                                                 band41=bands["FUN_0041a8f0"], asc=asc, nseq=len(seq_writers), same=same,
                                                 nstruct=len(c1c), fold100=fold100, sign=sign))


# ---------------------------------------------------------------- M180
def m180():
    res = {}
    for tok in ("0x920720", "0x9204b0"):
        hits = [(pc, s) for pc, s in LOW if ("ds:%s" % tok) in s]
        w, r = [], []
        for pc, s in hits:
            sl = norm(s)
            if re.search(r"mov\s+(dword ptr )?ds:%s," % tok, sl) or ("inc dword ptr ds:%s" % tok) in sl:
                w.append((pc, fnof(pc), s.strip()))
            else:
                r.append((pc, fnof(pc), s.strip()))
        res[tok] = (hits, w, r)
        print("== ds:%s : %d refs = %d writes + %d reads ==" % (tok, len(hits), len(w), len(r)))
        for tag, rows in (("W", w), ("R", r)):
            for pc, f, s in rows:
                print("   %s %s %-14s %s" % (tag, hex(pc), f, s))
        print("   writer functions %s ; reader functions %s"
              % (sorted(set(f for pc, f, s in w)), sorted(set(f for pc, f, s in r))))
    gates720 = [hex(pc) for pc, s in LOW if norm(s) == "cmp dword ptr ds:0x920720,0x2"]
    increl = [norm(s) for pc, s in window(0x532104, 0x53210c)]
    age = [norm(s) for pc, s in window(0x5406af, 0x5406ba)]
    zero720 = [hex(pc) for pc, s in LOW if norm(s) == "mov dword ptr ds:0x920720,edx"]
    ok("M180",
       len(res["0x920720"][0]) == 13 and len(res["0x920720"][1]) == 2
       and len(set(f for pc, f, s in res["0x920720"][1])) == 1 and len(gates720) == 2
       and increl == ["test dword ptr [ecx],0x2000000", "jne 0x532112", "inc dword ptr ds:0x920720"]
       and len(res["0x9204b0"][1]) == 2 and len(res["0x9204b0"][2]) == 3
       and "sub eax,edx" in age and "mov eax,ds:0x985afc" in age and "mov edx,dword ptr ds:0x9204b0" in age,
       ("ds:0x920720 is a COUNT WITH ONE WRITER FUNCTION: FUN_00531df0 zeroes it ({zero}) and increments it "
        "at 0x53210c on the leg {inc} - so it counts the records whose flag bit 25 is CLEAR - and 11 reads "
        "sit in 4 consumers: FUN_0053a9c0 (4: entry read paired with ds:0x9204ac, a switch case that ADDS it "
        "to an accumulator, and `cmp ,0x1; jg`), FUN_0053bb90 (`cmp ds:0x920720,eax` under the M163 rank<5 "
        "test), FUN_0053cb20 (zero test gated `cmp ds:0x985afc,0x32; jl` = round >= 50) and FUN_00546800 (5: "
        "two zero tests that fall back to ds:0x9204c8, a loop bound, and TWO `cmp ds:0x920720,0x2; jl` gates "
        "at {g2}). ds:0x9204b0 is the stamp EXPORT, bidirectional: 2 writers (the aggregator's export of "
        "[block+0x94d4a8] at 0x5321a4, and FUN_00546800 re-priming it with the round counter ds:0x985afc at "
        "0x54d121) and 3 readers, one computing the AGE as `mov eax,ds:0x985afc; mov edx,ds:0x9204b0; sub "
        "eax,edx` at 0x5406af-0x5406ba, the other two testing its sign (`jl` at 0x546d44) and non-positivity "
        "(`jle` at 0x54bf5f).").format(zero=zero720, inc=increl, g2=gates720))


only = (sys.argv[1] if len(sys.argv) > 1 else "").lower()
for name, fn in (("m178", m178), ("m179", m179), ("m180", m180)):
    if not only or only == name:
        fn()
print("SUMMARY " + " ".join("%s=%s" % (k, "PASS" if v else "FAIL") for k, v in sorted(R.items())))
sys.exit(0 if all(R.values()) else 1)
