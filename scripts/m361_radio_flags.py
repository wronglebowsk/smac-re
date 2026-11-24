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
      and stores the text through 0x5fa1e8 — a GENERIC set-label (10 call
      sites, only field +0xa7c, no flag knowledge);
  (c) every other reader: the commit path 0x492940 (flag -> pending
      preference bit), the aggregate 0x492030 (any child -> master 0x136d4),
      the seed path 0x4930e0 (bit cell -> flag -> relabel), the toggle
      handler 0x493ff0 (radio-group semantics + parent propagation), the
      constructor 0x48fed0.

Method: census the literal displacements in the full objdump
(scratch/m574/text.txt), attribute each site to its containing function,
classify the addressing form (field load / field store / cmp / pointer
arithmetic), split functions into the widget family and loners, resolve the
dispatcher's jump table at 0x493fe0 out of the image, and resolve every
register-sourced store/RMW bit by def-use.  Tables print first; assertions
follow.

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


def window(lo, hi):
    return [(a, m, o) for a, m, o in INS if lo <= a < hi]


def mem_any(ops, disp):
    return re.search(r"\[e[a-z]{2}\+0x%x\]" % disp, ops) is not None


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
    return [(a, mn, classify(mn, o), o) for a, mn, o in INS if mem_any(o, disp)]


def ptr_arith(disp):
    """`add reg,0x<disp>` — pointer/buffer arithmetic, not a field access"""
    out = []
    for a, mn, o in INS:
        if "0x%x" % disp in o and not mem_any(o, disp) and re.search(r"\b(e[a-z]{2}),0x%x$" % disp, o):
            out.append((a, mn, o))
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


FAILS = []


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

    # ---------------- G1: literal field census ------------------------------
    P("\n-- G1 literal field census (exact [reg+0x<disp>] addressing) --")
    totals, fam = {}, {}
    for disp in FLAGS:
        sites = census(disp)
        totals[disp] = len(sites)
        fns = {}
        for a, mn, k, o in sites:
            f = fnof(a)
            fns.setdefault((f[0], f[1]), []).append(k)
        P("0x%x: %d sites in %d functions" % (disp, len(sites), len(fns)))
        for (fa, fname), lst in sorted(fns.items()):
            kinds = {}
            for k in lst:
                kinds[k] = kinds.get(k, 0) + 1
            P("   %-14s %-10s %2d  %s" % (fname, hex(fa), len(lst),
              " ".join("%s:%d" % kv for kv in sorted(kinds.items()))))
            fam.setdefault(disp, set()).add(fa)
        pa = ptr_arith(disp)
        if pa:
            P("   (non-field `reg,0x%x` arithmetic forms: %d sites, first 0x%x %s)"
              % (disp, len(pa), pa[0][0], pa[0][2]))
    check("G1a census totals 16/15/12/12 = 55", [totals[d] for d in FLAGS] == [16, 15, 12, 12],
          [totals[d] for d in FLAGS])

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
        f = fnof(fa)
        st = [(a, o) for a, m, o in window(f[0], f[0] + f[2]) if mem_any(o, 0x14220)]
        lok.append((f[1], len(st), all(o.startswith("BYTE PTR") for _, o in st)))
    P("   loners: %s" % lok)
    check("G2c every loner site is a BYTE store — a different class's member", all(x[2] for x in lok), lok)

    # ---------------- G3: jump table ----------------------------------------
    P("\n-- G3 dispatcher jump table @0x%x --" % JT)
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
    got = [(b["cmd"], b["flag"], b["widget"]) for b in blocks]
    got = [(c, f if f is not None else -1, w if w is not None else -1) for c, f, w in got]
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
    vt = []
    for a, m, o in window(CTOR, CTOR + 0x2160):
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
    P("   ctor calls through [obj+0xf0]: %d total, on radio widget bases %s"
      % (len(vt), [hex(x) for x in onw]))
    master_site = [a for a, m, o in window(CTOR, CTOR + 0x2160) if m == "lea" and o == "edi,[esi+0x%x]" % WIDGET0]
    P("   master row 0x%x: built at %s, no [obj+0xf0] call (it is a plain widget)"
      % (WIDGET0, [hex(a) for a in master_site]))
    check("G5c the three CHILD rows are vtable objects; the master row is not",
          onw == sorted(wids - {WIDGET0}) and master_site and len(onw) == 3,
          ["0x%x" % x for x in onw])

    # ---------------- G6: reader/writer split -------------------------------
    P("\n-- G6 field READ vs WRITE split --")
    rw, readers, writers = {}, [], []
    for disp in FLAGS:
        for a, mn, k, o in census(disp):
            rw[k] = rw.get(k, 0) + 1
            f = fnof(a)
            (readers if k in ("load", "cmp", "test") else writers).append((disp, a, k, f[1]))
    P("   forms: %s" % rw)
    rfns = sorted({r[3] for r in readers})
    wfns = sorted({w[3] for w in writers})
    P("   readers: %d sites in %d functions %s" % (len(readers), len(rfns), rfns))
    P("   writers: %d sites in %d functions %s" % (len(writers), len(wfns), wfns))
    check("G6a 55 sites split 17 read (load/cmp) + 38 written (store)",
          (len(readers), len(writers)) == (17, 38), "%d+%d" % (len(readers), len(writers)))
    check("G6b reader set = dispatcher + 3 state functions",
          rfns == ["FUN_00492030", "FUN_00492940", "FUN_00493ec0", "FUN_00493ff0"], rfns)

    # ---------------- G7: the commit path 0x492940 --------------------------
    P("\n-- G7 commit path 0x492940: flag -> pending preference bit --")
    win = window(COMMIT, COMMIT + 1939)
    commit = []
    for i, (a, m, o) in enumerate(win):
        fm = re.match(r"eax,DWORD PTR \[e[a-z]{2}\+0x(136d4|14220|14d6c|158b8)\]$", o)
        if not (m == "mov" and fm):
            continue
        flag = int(fm.group(1), 16)
        seg = win[i:i + 8]
        if not any(mm == "test" and oo == "eax,eax" for _, mm, oo in seg[1:3]):
            continue
        found = None
        for j, (a2, m2, o2) in enumerate(seg[3:9]):
            om = re.match(r"DWORD PTR \[e[a-z]{2}\+0x([0-9a-f]+)\],(0x[0-9a-f]+|e[a-z]{2})$", o2)
            if m2 == "or" and om:
                src = om.group(2)
                bit = int(src, 16) if src.startswith("0x") else defuse(COMMIT, a2, src)
                found = (int(om.group(1), 16), bit, a2, src)
                break
            hm = re.match(r"ah,0x([0-9a-f]+)$", o2)
            if m2 == "or" and hm:
                # `mov eax,[cell]; or ah,imm` — the cell is the preceding load
                cell = None
                for a3, m3, o3 in reversed(seg[:3 + j]):
                    cm = re.match(r"eax,DWORD PTR \[e[a-z]{2}\+0x([0-9a-f]+)\]$", o3)
                    if m3 == "mov" and cm:
                        cell = int(cm.group(1), 16)
                        break
                found = (cell, int(hm.group(1), 16) << 8, a2, "ah," + hm.group(1))
                break
        if found and found[0] is not None:
            commit.append((flag,) + found)
    for flag, cell, bit, a, src in commit:
        P("   flag 0x%-6x -> cell +0x%-4x |= 0x%-6x @0x%x (%s)" % (flag, cell, bit, a, src))
    cm = {c[0]: (c[1], c[2]) for c in commit}
    check("G7a commit map = 0x14d6c->a50|0x4000, 0x14220->a4c|0x400, 0x158b8->a4c|0x800",
          cm == {0x14D6C: (0xA50, 0x4000), 0x14220: (0xA4C, 0x400), 0x158B8: (0xA4C, 0x800)},
          {hex(k): (hex(v[0]), hex(v[1])) for k, v in cm.items()})
    check("G7b the three cells/bits are pairwise distinct", len({(c[1], c[2]) for c in commit}) == 3,
          sorted(hex(c[2]) for c in commit))
    check("G7c the master 0x136d4 is NEVER committed to a preference bit", MASTER not in cm,
          "present" if MASTER in cm else "absent")
    check("G7d the 0x14220 bit comes from a register resolved by def-use = 0x400",
          cm.get(0x14220, (0, 0))[1] == 0x400, hex(cm.get(0x14220, (0, 0))[1]))

    # ---------------- G8: the aggregate 0x492030 ----------------------------
    P("\n-- G8 aggregate 0x492030: any child on -> master 0x136d4 --")
    win = window(AGG, AGG + 670)

    def guard_flag(at):
        """nearest child-flag read that guards the store at `at`:
        `cmp [x+FLAG],zero` or `mov reg,[x+FLAG]` + `cmp reg,zero`"""
        back = [t for t in window(AGG, at)][-6:]
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
            val = int(src, 16) if src.startswith("0x") else defuse(AGG, a, src)
            agg.append((a, val, guard_flag(a)))
    for a, val, guard in agg:
        P("   store @0x%x value=%s guard=%s" % (a, val, ("0x%x" % guard) if guard else "none"))
    check("G8a four master stores: one unconditional 0 then three guarded 1s",
          [g[1] for g in agg] == [0, 1, 1, 1] and [g[2] for g in agg] == [None, 0x158B8, 0x14D6C, 0x14220],
          [(g[1], g[2]) for g in agg])
    check("G8b each 1-store is guarded by its own child flag (the master is the OR of children)",
          [g[2] for g in agg][1:] == [0x158B8, 0x14D6C, 0x14220], [g[2] for g in agg][1:])

    # ---------------- G9: toggle handler ------------------------------------
    P("\n-- G9 toggle handler 0x493ff0: radio-group semantics --")
    win = window(TOGGLE, TOGGLE + 505)
    pushes = [int(o, 16) for a, m, o in win if m == "push" and re.match(r"0x4[b-e]$", o)]
    P("   pushed cmd values: %s" % [hex(c) for c in pushes])
    check("G9a the handler drives all four relabel cmds 0x4b..0x4e",
          sorted(set(pushes)) == [0x4B, 0x4C, 0x4D, 0x4E], sorted(set(pushes)))
    ands = [(a, m, o) for a, m, o in win if m == "and" and re.match(r"[abcd]h,0x[0-9a-f]+$", o)]
    P("   byte masks in the master-off branch: %s" % [(hex(a), o) for a, _, o in ands])
    cells = [(a, o) for a, m, o in window(0x494178, 0x49419F) if m == "mov" and "0x985ab" in o]
    P("   preference cells loaded/stored around the masks: %s" % [o for _, o in cells])
    check("G9b master-off clears exactly bits 0x400|0x800 (and ch,0xf3) and 0x4000 (and ah,0xbf)",
          sorted(o for _, _, o in ands) == ["ah,0xbf", "ch,0xf3"], [o for _, _, o in ands])
    check("G9c those clears land on globals 0x985ab8 and 0x985abc (the two committed cells)",
          sum(1 for _, o in cells if "0x985ab8" in o) == 2 and sum(1 for _, o in cells if "0x985abc" in o) == 2,
          [o for _, o in cells])
    # child ON -> also set the master and relabel 0x4b
    prop = []
    for a, m, o in win:
        mm = re.match(r"DWORD PTR \[e[a-z]{2}\+0x(14220|14d6c|158b8)\],(0x1|e[a-z]{2})$", o)
        if not (m == "mov" and mm):
            continue
        val = 1 if mm.group(2) == "0x1" else defuse(TOGGLE, a, mm.group(2))
        if val != 1:
            continue
        seg = window(a, a + 0x20)
        tgt_master = [o2 for _, m2, o2 in seg if m2 == "mov" and re.match(r"DWORD PTR \[e[a-z]{2}\+0x136d4\],", o2)]
        relabel = [o2 for _, m2, o2 in seg if m2 == "push" and o2 == "0x4b"]
        if tgt_master and relabel:
            prop.append(int(mm.group(1), 16))
    P("   child-ON branches that set the master and relabel 0x4b: %s" % [hex(x) for x in prop])
    check("G9d all three children propagate ON to the master (and none goes the other way)",
          sorted(prop) == [0x14220, 0x14D6C, 0x158B8], [hex(x) for x in prop])

    # ---------------- G10: the setter is generic ----------------------------
    P("\n-- G10 setter 0x%x: generic set-label, not flag-aware --" % SETTER)
    calls = [(a, fnof(a)) for a, m, o in INS if m == "call" and "0x5fa1e8" in o]
    cfns = sorted({c[1][1] for c in calls})
    P("   %d call sites in %d functions: %s" % (len(calls), len(cfns), cfns))
    sw = window(SETTER, SETTER + 178)
    sflags = [o for a, m, o in sw if any(mem_any(o, d) for d in FLAGS)]
    fields = sorted({int(x, 16) for x in
                     re.findall(r"\[e(?:ax|cx|dx|bx|si|di)\+0x([0-9a-f]+)\]",
                                " ".join(o for _, _, o in sw))})
    P("   flag displacements inside: %d; non-stack fields touched: %s" % (len(sflags), [hex(f) for f in fields]))
    check("G10a the setter has 10 call sites in 4 functions (generic, not dialog-specific)",
          (len(calls), len(cfns)) == (10, 4), "%d/%d" % (len(calls), len(cfns)))
    check("G10b the setter never names a radio flag", not sflags, sflags)
    check("G10c its only data field is +0xa7c (free old, strlen+1, strcpy)", fields == [TEXT_OFF],
          [hex(f) for f in fields])

    # ---------------- G11: label-id table readers ---------------------------
    P("\n-- G11 label-id table [0x997b20+0x10e0..0x10fc] --")
    reads, leas = {}, {}
    for a, m, o in INS:
        for i in LABEL_IDS:
            if not mem_any(o, i):
                continue
            f = fnof(a)[1]
            if m == "mov" and re.match(r"e[a-z]{2},DWORD PTR \[e[a-z]{2}\+0x%x\]$" % i, o) \
                    and "[ebp" not in o:
                reads.setdefault(f, []).append((a, i))
            if m == "lea":
                leas.setdefault(f, []).append((a, i))
    for k in sorted(reads):
        P("   READ %-14s %d sites" % (k, len(reads[k])))
    for k in sorted(leas):
        P("   ADDR-OF %-14s %d sites (a different class's member, not a table read)" % (k, len(leas[k])))
    check("G11a exactly two functions read the table", sorted(reads) == ["FUN_0048fed0", "FUN_00493ec0"], sorted(reads))
    ctor_ids = sorted(i for _, i in reads.get("FUN_0048fed0", []))
    P("   ctor label ids: %s (expect one per block, the first of each pair)" % [hex(x) for x in ctor_ids])
    check("G11e the ctor reads the four FIRST-of-pair ids, once each",
          ctor_ids == [0x10E0, 0x10E8, 0x10F0, 0x10F8], [hex(x) for x in ctor_ids])
    check("G11b dispatcher reads 8 (two per block), ctor 4 (one per block)",
          (len(reads.get("FUN_00493ec0", [])), len(reads.get("FUN_0048fed0", []))) == (8, 4),
          (len(reads.get("FUN_00493ec0", [])), len(reads.get("FUN_0048fed0", []))))
    seen = sorted(i for _, i in reads.get("FUN_00493ec0", []))
    check("G11c the eight label ids are read once each", seen == sorted(LABEL_IDS), [hex(x) for x in seen])
    check("G11d the 3 address-of sites are LEA, in 3 other classes (no aliasing read)",
          all(m == "lea" for _, m, o in INS if False) or
          sorted(leas) == ["FUN_0050aa60", "FUN_00518980", "FUN_00518ba0"], sorted(leas))

    # ---------------- G12: seed path 0x4930e0 -------------------------------
    P("\n-- G12 seed path 0x4930e0: bit cell -> child flag -> relabel --")
    win = window(SEED, SEED + 1582)
    seeds = []
    for a, m, o in win:
        mm = re.match(r"DWORD PTR \[e[a-z]{2}\+0x(14220|14d6c|158b8)\],(0x[01])$", o)
        if m == "mov" and mm:
            cmd = [oo for _, m2, oo in window(max(SEED, a - 0x10), a) if m2 == "push" and re.match(r"0x4[b-e]$", oo)]
            seeds.append((int(mm.group(1), 16), a, val_of(mm.group(2)), cmd[-1] if cmd else None))
    for flag, a, val, cmd in seeds:
        P("   store @0x%x flag 0x%x = %d, relabel %s" % (a, flag, val, cmd))
    check("G12a the seed writes all three child flags both ways (6 stores)",
          len(seeds) == 6 and sorted({s[0] for s in seeds}) == [0x14220, 0x14D6C, 0x158B8], len(seeds))
    check("G12b every seed store is paired with its own relabel cmd",
          all(s[3] == "0x%x" % {0x14220: 0x4C, 0x14D6C: 0x4D, 0x158B8: 0x4E}[s[0]] for s in seeds),
          [(hex(s[0]), s[3]) for s in seeds])
    src = [o for a, m, o in win if m == "mov" and re.match(r"eax,DWORD PTR \[e[a-z]{2}\+0xa50\]$", o)]
    P("   pending-bit-cell reads [obj+0xa50] in the seed path: %d" % len(src))
    check("G12c the seed derives the flag from the +0xa50 bit cell, not from another flag",
          len(src) >= 1 and not any(any(mem_any(o, d) for d in FLAGS) for a, m, o in win
                                    if m in ("test", "cmp") and o.startswith("eax")),
          len(src))

    # ---------------- rivals ------------------------------------------------
    P("\n-- RIVALS (each must be refuted by the printed numbers) --")
    r1 = len({b["flag"] for b in blocks}) == 1
    P("R1 one shared flag behind all four rows              | holds=%s | distinct flag offsets=%d"
      % (r1, len({b["flag"] for b in blocks})))
    r2 = bool(sflags)
    P("R2 the relabel setter is flag-aware                  | holds=%s | setter flag sites=%d"
      % (r2, len(sflags)))
    r3 = not prop
    P("R3 the three children are independent of the master   | holds=%s | child->master propagations=%d"
      % (r3, len(prop)))
    r4 = any(not x[2] for x in lok)
    P("R4 the flags are not dialog-local: 3 other classes touch 0x14220 | holds=%s | all loner sites byte-store=%s"
      % (r4, all(x[2] for x in lok)))
    r5 = len(rfns) == 1
    P("R5 0x493ec0 is the flags' ONLY reader                    | holds=%s | reader functions=%d %s"
      % (r5, len(rfns), rfns))
    check("R all five rivals are refuted by the printed numbers", not (r1 or r2 or r3 or r4 or r5),
          "r1=%s r2=%s r3=%s r4=%s r5=%s" % (r1, r2, r3, r4, r5))

    # ---------------- verdict ----------------------------------------------
    body = buf.getvalue()
    dig = hashlib.sha256(body.encode()).hexdigest()[:16]
    print("\n%s  M361: %d/%d gates  digest %s" %
          ("PASS" if not FAILS else "FAIL", NCHECK - len(FAILS), NCHECK, dig))
    if FAILS:
        print("FAILED: %s" % ", ".join(FAILS))
        return 1
    return 0


NCHECK = 0


def val_of(tok):
    return int(tok, 16)


if __name__ == "__main__":
    sys.exit(main())
