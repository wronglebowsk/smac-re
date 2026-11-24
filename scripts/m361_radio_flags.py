#!/usr/bin/env python3
"""M361 (chain2, STATIC): the A/V radio flag dwords — every reader, and where
the relabel path ends.

M360 left the two-state dwords at dialog-object offsets
0x136d4 / 0x14220 / 0x14d6c / 0x158b8 with only the relabel dispatcher
0x493ec0 known.  This script answers:

  (a) the four flags are the pending state of four radio rows, one per widget
      object at base 0x12cbc + k*0xb4c; the flag is widget+0xa18, the label
      char* is widget+0xa7c;
  (b) the relabel dispatcher maps cmd 0x4b..0x4e -> flag, picks one of two
      label ids from [0x997b20+0x10e0..0x10fc], resolves it through 0x61482f
      and stores the text through 0x5fa1e8 — a GENERIC set-label;
  (c) every other reader: the commit path 0x492940 (flag -> pending
      preference bit, scanned GLOBALLY), the aggregate 0x492030 (any child ->
      master 0x136d4), the seed path 0x4930e0, the toggle handler 0x493ff0
      (radio-group semantics in BOTH directions), the constructor 0x48fed0.

Method: census the literal displacements in the full objdump
(scratch/m574/text.txt) over EVERY addressing form (member, frame-relative,
indexed, bare arithmetic), attribute each site to its containing function,
classify the addressing form, split functions into the widget family and
loners, resolve the dispatcher's jump table at 0x493fe0 out of the image, and
resolve every register-sourced value by def-use.  Every function window is the
parsed function EXTENT from ghidra_out/index.csv (no hand-picked byte ranges).
Tables print first; assertions follow.

Every VERIFIED row has a mutant in scripts/m361_mutate.py.
"""
import bisect
import hashlib
import io
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("SMAC_M361_TEXT") or os.path.join(ROOT, "scratch/m574/text.txt")
IMAGE = os.environ.get("SMAC_M361_IMAGE") or os.path.join(ROOT, "programs/terran.exe")
IMAGE_BASE = 0x400000

FLAGS = [0x136D4, 0x14220, 0x14D6C, 0x158B8]
CHILDREN = [0x14220, 0x14D6C, 0x158B8]
MASTER = 0x136D4
WIDGET0 = 0x12CBC
STRIDE = 0xB4C
FLAG_OFF = 0xA18
TEXT_OFF = 0xA7C
JT = 0x493FE0
DISPATCH = 0x493EC0
SETTER = 0x5FA1E8
COMMIT = 0x492940
AGG = 0x492030
SEED = 0x4930E0
TOGGLE = 0x493FF0
CTOR = 0x48FED0
LABEL_IDS = [0x10E0, 0x10E4, 0x10E8, 0x10EC, 0x10F0, 0x10F4, 0x10F8, 0x10FC]
CMD_FLAG = {0x4B: 0x136D4, 0x4C: 0x14220, 0x4D: 0x14D6C, 0x4E: 0x158B8}
FIELD_REGS = ("eax", "ecx", "edx", "ebx", "esi", "edi")
READ_MN = ("mov", "cmp", "test", "or", "and", "xor", "add", "sub", "inc", "dec", "push")

LINE = re.compile(r"^\s*([0-9a-f]{6,8}):\s+([0-9a-f ]*?)\s{2,}([a-z][a-z0-9]*)\s*(.*)$")

rows = []
with open(os.path.join(ROOT, "ghidra_out/index.csv")) as f:
    head = f.readline().strip().split(",")
    for line in f:
        if not line.strip() or line.startswith("#"):
            continue
        d = dict(zip(head, line.rstrip("\n").split(",")))
        rows.append((int(d["addr"], 16), d["name"], int(d["size_bytes"])))
rows.sort()
STARTS = [r[0] for r in rows]

INS = []
for line in open(TEXT, errors="replace"):
    m = LINE.match(line)
    if m:
        INS.append((int(m.group(1), 16), m.group(3), m.group(4).strip()))


def fnof(pc):
    i = bisect.bisect_right(STARTS, pc) - 1
    if i >= 0 and pc < rows[i][0] + rows[i][2]:
        return rows[i]
    return (0, "?", 0)


def fnwin(addr):
    """the parsed function EXTENT containing addr — never a hand-picked range"""
    f = fnof(addr)
    return f[0], f[0] + f[2], f[2]


def window(lo, hi):
    return [(a, m, o) for a, m, o in INS if lo <= a < hi]


def mem_any(ops, disp):
    return re.search(r"\[e[a-z]{2}\+0x%x\]" % disp, ops) is not None


def mem_field(ops, disp):
    """exact object-member form: [field-reg + disp]"""
    return re.search(r"\[\b(%s)\+0x%x\]" % ("|".join(FIELD_REGS), disp), ops) is not None


def mem_first(ops):
    return ops.split(",")[0].strip().startswith(("DWORD PTR", "BYTE PTR", "WORD PTR"))


def classify(mn, ops):
    if mn == "cmp":
        return "cmp"
    if mn == "test":
        return "test"
    if mn in ("or", "and", "xor", "add", "sub"):
        return "rmw" if mem_first(ops) else "alu"
    if mn == "mov":
        return "store" if mem_first(ops) else "load"
    if mn == "lea":
        return "lea"
    return mn


def census(disp):
    return [(a, mn, classify(mn, o), o) for a, mn, o in INS if mem_field(o, disp)]


def forms(disp):
    """every instruction naming the literal, split by addressing form"""
    out = {"field": [], "frame": [], "indexed": [], "arith": []}
    for a, mn, o in INS:
        if "0x%x" % disp not in o:
            continue
        if re.search(r"\[ebp\+0x%x\]" % disp, o):
            out["frame"].append((a, o))
        elif re.search(r"\[e[a-z]{2}\*", o) and mem_any(o, disp):
            out["indexed"].append((a, o))
        elif mem_field(o, disp):
            out["field"].append((a, o))
        elif re.search(r"\b(e[a-z]{2}),0x%x$" % disp, o):
            out["arith"].append((a, o))
    return out


def defuse(lo, pc, reg):
    """value of `reg` at pc: last mov reg,imm / xor reg,reg in [lo,pc]"""
    last = None
    for a, m, o in window(lo, pc + 1):
        if m == "mov":
            mm = re.match(re.escape(reg) + r",(0x[0-9a-f]+|[0-9]+)$", o)
            if mm:
                last = int(mm.group(1), 16) if mm.group(1).startswith("0x") else int(mm.group(1))
        elif m == "xor" and o == "%s,%s" % (reg, reg):
            last = 0
        elif m == "lea" and re.match(re.escape(reg) + r",", o):
            last = None
    return last


def image_dwords(va, n):
    out = []
    with open(IMAGE, "rb") as fh:
        for k in range(n):
            fh.seek(va - IMAGE_BASE + k * 4)
            b = fh.read(4)
            if len(b) < 4:
                raise SystemExit("image read past EOF at 0x%x" % (va + k * 4))
            out.append(struct.unpack("<I", b)[0])
    return out


def or_bit(seg, fn_lo):
    """the `or` that commits a bit into a preference cell inside `seg`:
    `or [x+cell],imm|reg`, or `mov eax,[x+cell]; or ah,imm`.  (cell, bit, addr, src)"""
    for j, (a2, m2, o2) in enumerate(seg):
        om = re.match(r"DWORD PTR \[e[a-z]{2}\+0x([0-9a-f]+)\],(0x[0-9a-f]+|e[a-z]{2})$", o2)
        if m2 == "or" and om:
            src = om.group(2)
            bit = int(src, 16) if src.startswith("0x") else defuse(fn_lo, a2, src)
            return int(om.group(1), 16), bit, a2, src
        hm = re.match(r"ah,0x([0-9a-f]+)$", o2)
        if m2 == "or" and hm:
            cell = None
            for a3, m3, o3 in reversed(seg[:j]):
                cm = re.match(r"eax,DWORD PTR \[e[a-z]{2}\+0x([0-9a-f]+)\]$", o3)
                if m3 == "mov" and cm:
                    cell = int(cm.group(1), 16)
                    break
            return cell, int(hm.group(1), 16) << 8, a2, "ah," + hm.group(1)
    return None


def commit_scan():
    """GLOBAL over the whole image: every site where a radio flag gates an `or`
    into a preference cell (load -> test -> or shape)"""
    out = []
    for i, (a, m, o) in enumerate(INS):
        fm = re.match(r"eax,DWORD PTR \[e[a-z]{2}\+0x(136d4|14220|14d6c|158b8)\]$", o)
        if not (m == "mov" and fm):
            continue
        flag = int(fm.group(1), 16)
        seg = INS[i + 1:i + 9]
        if not any(mm == "test" and oo == "eax,eax" for _, mm, oo in seg[:2]):
            continue
        f = fnof(a)
        got = or_bit(seg[2:9], f[0])
        if got and got[0] is not None:
            out.append((a, flag, got[0], got[1], got[2], got[3], f[1]))
    return out


FAILS = []
NCHECK = 0


def check(name, cond, detail=""):
    global NCHECK
    NCHECK += 1
    print("[%s] %s%s" % ("PASS" if cond else "FAIL", name, ("  " + str(detail)) if detail else ""))
    if not cond:
        FAILS.append(name)


def main():
    buf = io.StringIO()

    def P(*a):
        s = " ".join(str(x) for x in a)
        print(s)
        buf.write(s + "\n")

    P("# M361 — A/V radio flag dwords: readers + relabel terminal")
    P("corpus: %d instructions (scratch/m574/text.txt), %d functions (ghidra_out/index.csv)"
      % (len(INS), len(rows)))
    exts = {n: fnwin(n) for n in (DISPATCH, COMMIT, AGG, SEED, TOGGLE, CTOR, SETTER)}
    P("function extents from index.csv: %s"
      % "  ".join("%s=0x%x..0x%x(%dB)" % (fnof(n)[1], a, b, s) for n, (a, b, s) in exts.items()))

    # ---------------- G1: literal field census ------------------------------
    P("\n-- G1 literal census over EVERY addressing form; [field-reg+disp] is the member form --")
    totals, fam = {}, {}
    for disp in FLAGS:
        sites = census(disp)
        totals[disp] = len(sites)
        fm = forms(disp)
        P("0x%x: %d member sites (%d frame-relative, %d indexed, %d bare arithmetic)"
          % (disp, len(sites), len(fm["frame"]), len(fm["indexed"]), len(fm["arith"])))
        fns = {}
        for a, mn, k, o in sites:
            f = fnof(a)
            fns.setdefault((f[0], f[1]), []).append(k)
        for (fa, fname), lst in sorted(fns.items()):
            kinds = {}
            for k in lst:
                kinds[k] = kinds.get(k, 0) + 1
            P("   %-14s %-10s %2d  %s" % (fname, hex(fa), len(lst),
              " ".join("%s:%d" % kv for kv in sorted(kinds.items()))))
            fam.setdefault(disp, set()).add(fa)
        if fm["arith"]:
            P("   (non-memory `reg,0x%x` arithmetic: %d sites, first 0x%x %s)"
              % (disp, len(fm["arith"]), fm["arith"][0][0], fm["arith"][0][1]))
        if fm["frame"] or fm["indexed"]:
            P("   (frame/indexed sites: %s)" % (fm["frame"] + fm["indexed"]))
    check("G1a census totals 16/15/12/12 = 55", [totals[d] for d in FLAGS] == [16, 15, 12, 12],
          [totals[d] for d in FLAGS])
    comp = {hex(d): len(forms(d)["frame"]) + len(forms(d)["indexed"]) for d in FLAGS}
    check("G1b no frame-relative or indexed form names any of the four literals",
          all(v == 0 for v in comp.values()), comp)

    # ---------------- G2: family partition ----------------------------------
    P("\n-- G2 family partition: functions naming >=2 of the four --")
    allfn = set().union(*fam.values())
    family = sorted({fa for fa in allfn if sum(1 for d in FLAGS if fa in fam[d]) >= 2})
    loners = sorted(allfn - set(family))
    for fa in sorted(allfn):
        P("   %-14s %-10s %s" % (fnof(fa)[1], hex(fa),
          " ".join("0x%x" % d for d in FLAGS if fa in fam[d]) or "-"))
    P("   family=%d %s" % (len(family), [hex(x) for x in family]))
    check("G2a exactly 7 family functions, 3 loners", len(family) == 7 and len(loners) == 3,
          "family=%d loners=%d" % (len(family), len(loners)))
    check("G2b the family is the A/V dialog's own function set",
          [fnof(x)[1] for x in family] == ["FUN_0048fed0", "FUN_00492030", "FUN_00492940",
                                           "FUN_004930e0", "FUN_00493a10", "FUN_00493ec0",
                                           "FUN_00493ff0"],
          [fnof(x)[1] for x in family])
    lok = []
    for fa in loners:
        a, b, _ = fnwin(fa)
        st = [(x, o) for x, m, o in window(a, b) if mem_any(o, 0x14220)]
        lok.append((fnof(fa)[1], len(st), all(o.startswith("BYTE PTR") for _, o in st)))
    P("   loners: %s" % lok)
    check("G2c every loner site is a BYTE store — a different class's member", all(x[2] for x in lok), lok)

    # ---------------- G3: jump table ----------------------------------------
    P("\n-- G3 dispatcher jump table @0x%x (image) --" % JT)
    tgt = image_dwords(JT, 4)
    for k, t in enumerate(tgt):
        P("   cmd 0x%x -> 0x%x" % (0x4B + k, t))
    check("G3a jump table = 0x493f9d,0x493f1c,0x493edc,0x493f5d",
          tgt == [0x493F9D, 0x493F1C, 0x493EDC, 0x493F5D], [hex(t) for t in tgt])
    guard = window(DISPATCH, DISPATCH + 0x20)
    okg = any(m == "add" and o == "eax,0xffffffb5" for _, m, o in guard) and \
          any(m == "cmp" and o == "eax,0x3" for _, m, o in guard)
    check("G3b guard: eax = cmd-0x4b, cmp 3, ja", okg, [x[1:] for x in guard[:6]])

    # ---------------- G4: relabel blocks ------------------------------------
    P("\n-- G4 relabel chain 0x493ec0 block -> 0x61482f -> 0x5fa1e8 --")
    blocks = []
    for k, t in enumerate(tgt):
        win = window(t, t + 0x40)
        flag = wid = None
        for a, m, o in win:
            fm = re.search(r"\[e[a-z]{2}\+0x(136d4|14220|14d6c|158b8)\]", o)
            if fm and m == "mov" and o.startswith("eax,DWORD PTR"):
                flag = int(fm.group(1), 16)
            wm = re.match(r"ecx,\[e[a-z]{2}\+0x([0-9a-f]+)\]$", o)
            if m == "lea" and wm:
                wid = int(wm.group(1), 16)
        sids = sorted({int(s, 16) for s in
                       re.findall(r"\[e[a-z]{2}\+0x(10e[0-9a-f]|10f[0-9a-f])\]", " ".join(o for _, _, o in win))})
        calls = [o for a, m, o in win if m == "call"]
        blocks.append(dict(cmd=0x4B + k, addr=t, flag=flag, widget=wid, sids=sids, calls=calls))
        P("   cmd 0x%x @0x%x flag=0x%x widget=0x%x label-ids=%s calls=%s"
          % (0x4B + k, t, flag or 0, wid or 0, [hex(s) for s in sids], calls))
    want = [(0x4B, 0x136D4, 0x12CBC), (0x4C, 0x14220, 0x13808),
            (0x4D, 0x14D6C, 0x14354), (0x4E, 0x158B8, 0x14EA0)]
    got = [(c, f if f is not None else -1, w if w is not None else -1)
           for c, f, w in [(b["cmd"], b["flag"], b["widget"]) for b in blocks]]
    check("G4a cmd -> flag -> widget map matches the four blocks", got == want, got)
    check("G4b every block calls 0x61482f (label-id resolve) then 0x5fa1e8 (set text)",
          all(any("0x61482f" in c for c in b["calls"]) and any("0x5fa1e8" in c for c in b["calls"])
              and b["calls"].index("0x61482f") < b["calls"].index("0x5fa1e8") for b in blocks),
          [b["calls"] for b in blocks])
    pair = sorted({tuple(sorted(b["sids"])) for b in blocks})
    check("G4c each block names exactly one of the four label-id PAIRS",
          pair == [(0x10E0, 0x10E4), (0x10E8, 0x10EC), (0x10F0, 0x10F4), (0x10F8, 0x10FC)],
          [[hex(x) for x in p] for p in pair])

    # ---------------- G5: geometry ------------------------------------------
    P("\n-- G5 widget geometry: base 0x%x + k*0x%x, flag=+0x%x, label=+0x%x --"
      % (WIDGET0, STRIDE, FLAG_OFF, TEXT_OFF))
    geom = []
    for b in blocks:
        wantb = WIDGET0 + (b["cmd"] - 0x4B) * STRIDE
        fl = b["flag"] if b["flag"] is not None else -1
        geom.append((b["cmd"], (b["widget"] or 0) - wantb, fl - (b["widget"] or 0)))
        P("   cmd 0x%x widget=0x%x (expect 0x%x, delta %+d)  flag-widget=0x%x"
          % (b["cmd"], b["widget"] or 0, wantb, (b["widget"] or 0) - wantb, fl - (b["widget"] or 0)))
    check("G5a widget = 0x12cbc + k*0xb4c for all four", all(g[1] == 0 for g in geom), geom)
    check("G5b flag - widget == 0xa18 for all four", all(g[2] == FLAG_OFF for g in geom), geom)
    ca, cb, _ = fnwin(CTOR)
    vt = []
    for a, m, o in window(ca, cb):
        if not (m == "call" and re.match(r"DWORD PTR \[e[a-z]{2}\+0xf0\]$", o)):
            continue
        base = None
        for a2, m2, o2 in window(a - 0x10, a):
            lm = re.match(r"ecx,\[e[a-z]{2}\+0x([0-9a-f]+)\]$", o2)
            if m2 == "lea" and lm:
                base = int(lm.group(1), 16)
        vt.append((a, base))
    wids = {b["widget"] for b in blocks}
    onw = sorted({b for _, b in vt if b in wids})
    master_site = [a for a, m, o in window(ca, cb) if m == "lea" and o == "edi,[esi+0x%x]" % WIDGET0]
    P("   ctor extent 0x%x..0x%x: [obj+0xf0] calls on radio bases %s; master row built at %s"
      % (ca, cb, [hex(x) for x in onw], [hex(a) for a in master_site]))
    check("G5c in the ctor extent the three CHILD rows get vtable calls; the master row does not",
          onw == sorted(wids - {WIDGET0}) and master_site and len(onw) == 3,
          ["0x%x" % x for x in onw])

    # ---------------- G6: reader/writer split -------------------------------
    P("\n-- G6 field READ vs WRITE split (every class printed) --")
    rw, readers, writers = {}, [], []
    for disp in FLAGS:
        for a, mn, k, o in census(disp):
            rw[k] = rw.get(k, 0) + 1
            f = fnof(a)
            (readers if k in ("load", "cmp", "test") else writers).append((disp, a, k, f[1]))
    P("   forms: %s" % sorted(rw.items()))
    rfns = sorted({r[3] for r in readers})
    wfns = sorted({w[3] for w in writers})
    P("   readers: %d sites in %d functions %s" % (len(readers), len(rfns), rfns))
    P("   writers: %d sites in %d functions %s" % (len(writers), len(wfns), wfns))
    check("G6a 55 sites = 15 loads + 2 cmps + 38 stores, no rmw/test class",
          sorted(rw.items()) == [("cmp", 2), ("load", 15), ("store", 38)], sorted(rw.items()))
    check("G6b reader set = dispatcher + 3 state functions",
          rfns == ["FUN_00492030", "FUN_00492940", "FUN_00493ec0", "FUN_00493ff0"], rfns)

    # ---------------- G7: the commit path, scanned globally -----------------
    P("\n-- G7 commit path: GLOBAL scan for a flag gating an `or` into a preference cell --")
    cs = commit_scan()
    for a, flag, cell, bit, src_a, src, fname in cs:
        P("   @0x%x %-14s flag 0x%-6x -> cell +0x%-4x |= 0x%-6x (%s)"
          % (a, fname, flag, cell, bit, src))
    cm = {c[1]: (c[2], c[3]) for c in cs}
    cm_fns = sorted({c[6] for c in cs})
    check("G7a the only commit sites in the image are the three children, in 0x492940",
          cm == {0x14D6C: (0xA50, 0x4000), 0x14220: (0xA4C, 0x400), 0x158B8: (0xA4C, 0x800)}
          and cm_fns == ["FUN_00492940"],
          {hex(k): (hex(v[0]), hex(v[1])) for k, v in cm.items()})
    check("G7b the three cells/bits are pairwise distinct", len({(c[2], c[3]) for c in cs}) == 3,
          sorted(hex(c[3]) for c in cs))
    check("G7c the master 0x136d4 is NEVER committed, anywhere in the image", MASTER not in cm,
          "present" if MASTER in cm else "absent")
    check("G7d the 0x14220 bit comes from a register resolved by def-use = 0x400",
          cm.get(0x14220, (0, 0))[1] == 0x400, hex(cm.get(0x14220, (0, 0))[1]))

    # ---------------- G8: the aggregate -------------------------------------
    P("\n-- G8 aggregate 0x492030 (function extent): any child on -> master 0x136d4 --")
    aa, ab, asz = fnwin(AGG)
    win = window(aa, ab)

    def guard_flag(at):
        back = window(aa, at)[-6:]
        for idx in range(len(back) - 1, -1, -1):
            a2, m2, o2 = back[idx]
            gm = re.match(r"DWORD PTR \[e[a-z]{2}\+0x(136d4|14220|14d6c|158b8)\],e[a-z]{2}$", o2)
            if m2 == "cmp" and gm:
                return int(gm.group(1), 16)
            lm = re.match(r"(e[a-z]{2}),DWORD PTR \[e[a-z]{2}\+0x(136d4|14220|14d6c|158b8)\]$", o2)
            if m2 == "mov" and lm:
                reg = lm.group(1)
                if any(mm == "cmp" and oo.startswith(reg + ",") for _, mm, oo in back[idx + 1:]):
                    return int(lm.group(2), 16)
        return None

    agg = []
    for a, m, o in win:
        mm = re.match(r"DWORD PTR \[e[a-z]{2}\+0x([0-9a-f]+)\],(0x[0-9a-f]+|e[a-z]{2})$", o)
        if m == "mov" and mm and int(mm.group(1), 16) == MASTER:
            src = mm.group(2)
            val = int(src, 16) if src.startswith("0x") else defuse(aa, a, src)
            agg.append((a, val, guard_flag(a)))
    for a, val, guard in agg:
        P("   store @0x%x value=%s guard=%s" % (a, val, ("0x%x" % guard) if guard else "none"))
    master_stores = [c for c in census(MASTER) if c[2] == "store"]
    in_fn = [c for c in master_stores if fnof(c[0])[1] == "FUN_00492030"]
    out_fn = [c for c in master_stores if fnof(c[0])[1] != "FUN_00492030"]
    P("   master stores in the image: %d here, %d elsewhere (%s)"
      % (len(in_fn), len(out_fn), sorted({fnof(c[0])[1] for c in out_fn})))
    check("G8a four master stores in the %dB extent (one 0 then three guarded 1s); none elsewhere in this function"
          % asz,
          [g[1] for g in agg] == [0, 1, 1, 1]
          and [g[2] for g in agg] == [None, 0x158B8, 0x14D6C, 0x14220]
          and len(in_fn) == len(agg), [(g[1], g[2]) for g in agg])
    check("G8b each 1-store is guarded by its own child, in program order — the master is the OR",
          [g[2] for g in agg][1:] == [0x158B8, 0x14D6C, 0x14220], [g[2] for g in agg][1:])

    # ---------------- G9: toggle handler ------------------------------------
    P("\n-- G9 toggle handler 0x493ff0 (function extent): radio-group, BOTH directions --")
    ta, tb, tsz = fnwin(TOGGLE)
    win = window(ta, tb)
    pushes = [int(o, 16) for a, m, o in win if m == "push" and re.match(r"0x4[b-e]$", o)]
    P("   pushed cmd values: %s" % [hex(c) for c in pushes])
    check("G9a the handler drives all four relabel cmds 0x4b..0x4e",
          sorted(set(pushes)) == [0x4B, 0x4C, 0x4D, 0x4E], sorted(set(pushes)))
    ands = [(a, m, o) for a, m, o in win if m == "and" and re.match(r"[abcd]h,0x[0-9a-f]+$", o)]
    P("   byte masks in the master-off branch: %s" % [(hex(a), o) for a, _, o in ands])
    masked = []
    for a, m, o in ands:
        reg, imm = o.split(",")
        hi = {"ch": "ecx", "ah": "eax", "dh": "edx", "bh": "ebx"}[reg]
        cell_in = cell_out = None
        for a2, m2, o2 in reversed(window(ta, a)):
            mm = re.match(r"%s,(?:DWORD PTR )?ds:0x([0-9a-f]+)$" % hi, o2)
            if m2 == "mov" and mm:
                cell_in = int(mm.group(1), 16)
                break
        for a2, m2, o2 in window(a + 1, tb):
            mm = re.match(r"(?:DWORD PTR )?ds:0x([0-9a-f]+),%s$" % hi, o2)
            if m2 == "mov" and mm:
                cell_out = int(mm.group(1), 16)
                break
        masked.append((hex(a), o, hex(cell_in or 0), hex(cell_out or 0)))
    P("   masks with their source/destination cell: %s" % masked)
    check("G9b master-off clears exactly bits 0x400|0x800 (and ch,0xf3) and 0x4000 (and ah,0xbf)",
          sorted(o for _, _, o in ands) == ["ah,0xbf", "ch,0xf3"], [o for _, _, o in ands])
    check("G9c each masked register is loaded from and stored back to the committed cells 0x985ab8/0x985abc",
          sorted((c[2], c[3]) for c in masked) == [("0x985ab8", "0x985ab8"), ("0x985abc", "0x985abc")],
          masked)
    prop_c2m, prop_m2c = [], []
    for a, m, o in win:
        mm = re.match(r"DWORD PTR \[e[a-z]{2}\+0x(14220|14d6c|158b8)\],(0x1|e[a-z]{2})$", o)
        if m == "mov" and mm:
            val = 1 if mm.group(2) == "0x1" else defuse(ta, a, mm.group(2))
            seg = window(a, a + 0x20)
            if val == 1 and [x for _, m2, x in seg if m2 == "mov"
                             and re.match(r"DWORD PTR \[e[a-z]{2}\+0x136d4\],", x)] \
                    and [x for _, m2, x in seg if m2 == "push" and x == "0x4b"]:
                prop_c2m.append(int(mm.group(1), 16))
        mm2 = re.match(r"DWORD PTR \[e[a-z]{2}\+0x136d4\],(0x[01]|e[a-z]{2})$", o)
        if m == "mov" and mm2:
            seg = window(a, a + 0x24)
            kids = set()
            for _, m3, x3 in seg:
                x = re.match(r"DWORD PTR \[e[a-z]{2}\+0x(14220|14d6c|158b8)\],", x3)
                if m3 == "mov" and x:
                    kids.add(int(x.group(1), 16))
            if len(kids) == 3:
                v = mm2.group(1)
                v = hex(int(v, 16)) if v.startswith("0x") else hex(defuse(ta, a, v) or 0)
                prop_m2c.append((a, v))
    P("   child-ON -> master: %s" % [hex(x) for x in prop_c2m])
    P("   master write -> all three children: %s" % [(hex(a), v) for a, v in prop_m2c])
    check("G9d every child ON sets the master and relabels 0x4b",
          sorted(prop_c2m) == [0x14220, 0x14D6C, 0x158B8], [hex(x) for x in prop_c2m])
    check("G9e the master write also hits all three children (propagation runs both ways)",
          sorted({v for _, v in prop_m2c}) == ["0x0", "0x1"] and len(prop_m2c) == 2,
          [(hex(a), v) for a, v in prop_m2c])

    # ---------------- G10: the setter is generic ----------------------------
    P("\n-- G10 setter 0x%x (function extent): generic set-label --" % SETTER)
    calls = [(a, fnof(a)) for a, m, o in INS if m == "call" and "0x5fa1e8" in o]
    cfns = sorted({c[1][1] for c in calls})
    P("   %d call sites in %d functions: %s" % (len(calls), len(cfns), cfns))
    sa, sb, ssz = fnwin(SETTER)
    sw = window(sa, sb)
    sflags = [o for a, m, o in sw if any(mem_any(o, d) for d in FLAGS)]
    fields = sorted({int(x, 16) for x in
                     re.findall(r"\[e(?:ax|cx|dx|bx|si|di)\+0x([0-9a-f]+)\]",
                                " ".join(o for _, _, o in sw))})
    P("   extent %dB; flag displacements inside: %d; non-stack fields: %s"
      % (ssz, len(sflags), [hex(f) for f in fields]))
    check("G10a the setter has 10 call sites in 4 functions (generic, not dialog-specific)",
          (len(calls), len(cfns)) == (10, 4), "%d/%d" % (len(calls), len(cfns)))
    check("G10b the setter never names a radio flag, over its whole function extent", not sflags, sflags)
    check("G10c its only data field over the whole extent is +0xa7c", fields == [TEXT_OFF],
          [hex(f) for f in fields])

    # ---------------- G11: label-id table readers ---------------------------
    P("\n-- G11 label-id table [0x997b20+0x10e0..0x10fc]: every read mnemonic --")
    reads, leas, frame = {}, {}, {}
    for a, m, o in INS:
        hit = [i for i in LABEL_IDS if mem_field(o, i)]
        if not hit:
            continue
        f = fnof(a)[1]
        if m == "lea":
            leas.setdefault(f, []).append((a, hit[0]))
        elif m == "mov" and mem_first(o):
            continue                                   # store into the table, not a read
        elif m in READ_MN:
            reads.setdefault(f, []).append((a, hit[0]))
    for a, m, o in INS:
        for i in LABEL_IDS:
            if re.search(r"\[ebp\+0x%x\]" % i, o):
                frame.setdefault(fnof(a)[1], []).append((a, i))
    for k in sorted(reads):
        P("   READ     %-14s %d sites" % (k, len(reads[k])))
    for k in sorted(leas):
        P("   ADDR-OF  %-14s %d sites (other classes' members)" % (k, len(leas[k])))
    P("   frame-relative reads: %s" % ({k: len(v) for k, v in frame.items()} or "none"))
    check("G11a exactly two functions read the table, across every read mnemonic",
          sorted(reads) == ["FUN_0048fed0", "FUN_00493ec0"], sorted(reads))
    check("G11b dispatcher reads 8 (two per block), ctor 4 (one per block)",
          (len(reads.get("FUN_00493ec0", [])), len(reads.get("FUN_0048fed0", []))) == (8, 4),
          (len(reads.get("FUN_00493ec0", [])), len(reads.get("FUN_0048fed0", []))))
    seen = sorted(i for _, i in reads.get("FUN_00493ec0", []))
    check("G11c the eight label ids are read once each", seen == sorted(LABEL_IDS), [hex(x) for x in seen])
    ctor_ids = sorted(i for _, i in reads.get("FUN_0048fed0", []))
    P("   ctor label ids: %s" % [hex(x) for x in ctor_ids])
    check("G11e the ctor reads the four FIRST-of-pair ids, once each",
          ctor_ids == [0x10E0, 0x10E8, 0x10F0, 0x10F8], [hex(x) for x in ctor_ids])
    check("G11d the 3 address-of sites are LEA in 3 other classes and no frame form exists",
          sorted(leas) == ["FUN_0050aa60", "FUN_00518980", "FUN_00518ba0"] and not frame,
          sorted(leas))

    # ---------------- G12: seed path ----------------------------------------
    P("\n-- G12 seed path 0x4930e0 (function extent): bit cell -> child flag -> relabel --")
    na, nb, nsz = fnwin(SEED)
    win = window(na, nb)
    seeds = []
    for a, m, o in win:
        mm = re.match(r"DWORD PTR \[e[a-z]{2}\+0x(14220|14d6c|158b8)\],(0x[01])$", o)
        if m == "mov" and mm:
            cmd = [oo for _, m2, oo in window(max(na, a - 0x10), a)
                   if m2 == "push" and re.match(r"0x4[b-e]$", oo)]
            seeds.append((int(mm.group(1), 16), a, int(mm.group(2), 16), cmd[-1] if cmd else None))
    for flag, a, val, cmd in seeds:
        P("   store @0x%x flag 0x%x = %d, relabel %s" % (a, flag, val, cmd))
    check("G12a the seed writes all three child flags both ways (6 stores)",
          len(seeds) == 6 and sorted({s[0] for s in seeds}) == [0x14220, 0x14D6C, 0x158B8], len(seeds))
    check("G12b every seed store is paired with its own relabel cmd",
          all(s[3] == "0x%x" % {0x14220: 0x4C, 0x14D6C: 0x4D, 0x158B8: 0x4E}[s[0]] for s in seeds),
          [(hex(s[0]), s[3]) for s in seeds])
    src = [o for a, m, o in win if m == "mov" and re.match(r"eax,DWORD PTR \[e[a-z]{2}\+0xa50\]$", o)]
    flagloads = [o for a, m, o in win if m in ("test", "cmp") and o.startswith("eax")
                 and any(mem_any(o, d) for d in FLAGS)]
    P("   +0xa50 bit-cell reads: %d; flag comparisons: %d" % (len(src), len(flagloads)))
    check("G12c the seed derives each flag from the +0xa50 bit cell, not from another flag",
          len(src) >= 1 and not flagloads, len(src))

    # ---------------- rivals ------------------------------------------------
    P("\n-- RIVALS (each must be refuted by the printed numbers) --")
    r1 = len({b["flag"] for b in blocks}) == 1
    P("R1 one shared flag behind all four rows              | holds=%s | distinct flag offsets=%d"
      % (r1, len({b["flag"] for b in blocks})))
    r2 = bool(sflags)
    P("R2 the relabel setter is flag-aware                  | holds=%s | setter flag sites=%d"
      % (r2, len(sflags)))
    r3 = not prop_c2m
    P("R3 the children are independent of the master          | holds=%s | child->master sites=%d"
      % (r3, len(prop_c2m)))
    r4 = any(not x[2] for x in lok)
    P("R4 the flags are not dialog-local: 3 classes touch 0x14220 | holds=%s | all loners byte-store=%s"
      % (r4, all(x[2] for x in lok)))
    r5 = len(rfns) == 1
    P("R5 0x493ec0 is the flags' ONLY reader                  | holds=%s | reader functions=%d %s"
      % (r5, len(rfns), rfns))
    check("R all five rivals are refuted by the printed numbers", not (r1 or r2 or r3 or r4 or r5),
          "r1=%s r2=%s r3=%s r4=%s r5=%s" % (r1, r2, r3, r4, r5))

    # ---------------- verdict ----------------------------------------------
    dig = hashlib.sha256(buf.getvalue().encode()).hexdigest()[:16]
    print("\n%s  M361: %d/%d gates  digest %s" %
          ("PASS" if not FAILS else "FAIL", NCHECK - len(FAILS), NCHECK, dig))
    if FAILS:
        print("FAILED: %s" % ", ".join(FAILS))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
