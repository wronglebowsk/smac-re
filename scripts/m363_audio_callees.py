#!/usr/bin/env python3
"""M363 (ANALYSE, static): the four audio callees of the A/V rows — do they touch
the global preference cells 0x985ab8 / 0x985abc, or only the mixer?

M361 left `0x4b87f0 / 0x4b8820 / 0x4b8a60 / 0x4b8af0 = audio on/off (INFERRED)`
open.  This script measures, print-first:

  (a) every memory reference inside the four bodies and inside their transitive
      direct-call closure — absolute data operands, this-relative members,
      vtable-dispatched calls, import-form calls;
  (b) the two preference cells' whole .text census, split into "inside the
      closure" and "everywhere else", so the answer is a count, not a reading;
  (c) the call sites: who calls the four, with what `this`, and with what
      argument (def-use), from the A/V handler FUN_00493ff0's four switch
      cases (jump table 0x4941ec read out of the image);
  (d) the shapes the bodies do implement: a 16-slot voice table
      (index*0x18, bound 0xf, play flag at +0x24, buffer ptr at +0x2c) and a
      two-method enable/disable pair forwarding into the +0x14 inner object.

Every function window is the parsed EXTENT from ghidra_out/index.csv.
Tables print first; assertions follow.  Every VERIFIED row names a mutant in
scripts/m363_mutate.py.
"""
import bisect
import hashlib
import io
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("SMAC_M363_TEXT") or os.path.join(ROOT, "scratch/m574/text.txt")
IMAGE = os.environ.get("SMAC_M363_IMAGE") or os.path.join(ROOT, "programs/terran.exe")
IMAGE_BASE = 0x400000

F1, F2, F3, F4 = 0x4B87F0, 0x4B8820, 0x4B8A60, 0x4B8AF0
TARGETS = [F1, F2, F3, F4]
PREF = (0x985AB8, 0x985ABC)
SINGLETON = 0x8A7920
HANDLER = 0x493FF0
JT_HANDLER = 0x4941EC
ROW_FLAGS = (0x136D4, 0x14220, 0x14D6C, 0x158B8)
CMD_FLAG = {0x4B: 0x136D4, 0x4C: 0x14220, 0x4D: 0x14D6C, 0x4E: 0x158B8}
DATA_LO, DATA_HI = 0x800000, 0xB00000

LINE = re.compile(r"^\s*([0-9a-f]{6,8}):\s+([0-9a-f ]*?)\s{2,}([a-z][a-z0-9]*)\s*(.*)$")
HEX = re.compile(r"0x([0-9a-f]+)")

rows = []
with open(os.path.join(ROOT, "ghidra_out/index.csv")) as f:
    head = f.readline().strip().split(",")
    for line in f:
        if not line.strip() or line.startswith("#"):
            continue
        d = dict(zip(head, line.rstrip("\n").split(",")))
        rows.append((int(d["addr"], 16), d["name"], int(d["size_bytes"]),
                     int(d["n_insns"]), int(d["n_callers"]), int(d["n_callees"])))
rows.sort()
STARTS = [r[0] for r in rows]
BYADDR = {r[0]: r for r in rows}

INS = []
for line in open(TEXT, errors="replace"):
    m = LINE.match(line)
    if m:
        INS.append((int(m.group(1), 16), m.group(3), re.sub(r"\s+", " ", m.group(4).strip())))
INS.sort()
IADDR = [a for a, _, _ in INS]


def fnof(pc):
    i = bisect.bisect_right(STARTS, pc) - 1
    if i >= 0 and pc < rows[i][0] + rows[i][2]:
        return rows[i]
    return (0, "?", 0, 0, 0, 0)


def win(addr):
    """the parsed function EXTENT containing addr — never a hand-picked range"""
    f = fnof(addr)
    lo, hi = f[0], f[0] + f[2]
    i, j = bisect.bisect_left(IADDR, lo), bisect.bisect_left(IADDR, hi)
    return [(a, m, o) for a, m, o in INS[i:j]]


def rng(lo, hi):
    i, j = bisect.bisect_left(IADDR, lo), bisect.bisect_left(IADDR, hi)
    return [(a, m, o) for a, m, o in INS[i:j]]


def absdata(items):
    """absolute data-window operands, branch/call targets excluded"""
    out = {}
    for a, m, o in items:
        if m in ("call", "jmp") or m.startswith("j"):
            if not o.startswith("DWORD PTR [") and not o.startswith("BYTE PTR ["):
                continue
        for h in HEX.findall(o):
            v = int(h, 16)
            if DATA_LO <= v <= DATA_HI:
                out.setdefault(v, []).append(a)
    return out


def direct_calls(addr):
    return [(a, int(o, 16)) for a, m, o in win(addr) if m == "call" and re.fullmatch(r"0x[0-9a-f]+", o)]


def indirect_calls(addr):
    return [(a, o) for a, m, o in win(addr) if m == "call" and (o.startswith("DWORD PTR [") or o.startswith("DWORD PTR ds:"))]


MEMBR = re.compile(r"\[([a-z]{3})(?:\+([a-z]{3})\*1)?(?:\+0x([0-9a-f]+))?\]")


def members(items):
    out = []
    for a, m, o in items:
        for mm in MEMBR.finditer(o):
            out.append((a, m, mm.group(1), mm.group(2) or "", int(mm.group(3), 16) if mm.group(3) else 0))
    return out


def closure_of(addrs):
    seen, stack, edges = set(), list(addrs), {}
    while stack:
        a = stack.pop()
        f = fnof(a)
        if not f[0] or f[0] in seen:
            continue
        seen.add(f[0])
        c = direct_calls(f[0])
        edges[f[0]] = c
        for _site, tgt in c:
            stack.append(tgt)
    return seen, edges


NCHECK = 0
FAILS = []


def check(name, cond, detail=""):
    global NCHECK
    NCHECK += 1
    print("[%s] %s%s" % ("PASS" if cond else "FAIL", name, ("  " + str(detail)) if detail else ""))
    if not cond:
        FAILS.append(name)


def defuse(items, site, reg):
    """nearest preceding write to reg inside the same case block -> ('xor',0)/('mov',imm)/('mem',None)"""
    for a, m, o in reversed([x for x in items if x[0] < site]):
        dst = o.split(",")[0].strip()
        if dst != reg:
            continue
        if m == "xor" and o.split(",")[1].strip() == reg:
            return "xor", 0, a
        if m == "mov":
            src = o.split(",", 1)[1].strip()
            if re.fullmatch(r"0x[0-9a-f]+", src):
                return "mov", int(src, 16), a
            return "mem", None, a
    return None, None, None


def main():
    buf = io.StringIO()

    def P(*a):
        s = " ".join(str(x) for x in a)
        print(s)
        buf.write(s + "\n")

    P("# M363 — the four A/V audio callees vs the preference cells 0x985ab8/0x985abc")
    P("corpus: %d instructions (%s), %d functions (ghidra_out/index.csv)"
      % (len(INS), os.path.relpath(TEXT, ROOT), len(rows)))

    # ---------------- G1 extents -------------------------------------------
    P("\n-- G1 function extents (index.csv), parsed insn counts, entry/exit shape --")
    ext = {}
    for t in TARGETS:
        f = fnof(t)
        w = win(t)
        ext[t] = (f[0], f[0] + f[2])
        P("0x%06x %-12s extent=0x%06x..0x%06x size=%dB idx_insns=%d parsed=%d first=%s last=%s idx_callers=%d idx_callees=%d"
          % (t, f[1], f[0], f[0] + f[2], f[2], f[3], len(w), w[0][1] if w else "-", w[-1][1] if w else "-", f[4], f[5]))
    g1 = all(len(win(t)) == fnof(t)[3] and win(t)[0][1] == "push" and win(t)[-1][1] == "ret" for t in TARGETS)
    check("G1 every target extent parses to its index insn count, opens with push, closes with ret", g1,
          "insns=%s" % [len(win(t)) for t in TARGETS])

    # ---------------- G2 absolute data operands in the four bodies ----------
    P("\n-- G2 absolute data-window operands (0x800000..0xbfffff) per body --")
    per_abs = {}
    for t in TARGETS:
        d = absdata(win(t))
        per_abs[t] = d
        P("0x%06x abs_data=%d %s  indirect_calls=%s"
          % (t, len(d), sorted(hex(x) for x in d), [o for _a, o in indirect_calls(t)]))
    check("G2 the four bodies hold ZERO absolute data operands", all(not per_abs[t] for t in TARGETS),
          "total=%d" % sum(len(per_abs[t]) for t in TARGETS))

    # ---------------- G3/G4 the closure ------------------------------------
    clo, edges = closure_of(TARGETS)
    P("\n-- G3 transitive direct-call closure (edges printed) --")
    for f in sorted(clo):
        r = fnof(f)
        P("0x%06x %-12s size=%-4d callees=%s"
          % (f, r[1], r[2], ["0x%06x" % x[1] for x in edges.get(f, [])]))
    P("closure size=%d: %s" % (len(clo), " ".join("0x%06x" % x for x in sorted(clo))))
    want = set(TARGETS + [0x4B9330, 0x4B9370, 0x4B9460, 0x4B94A0])
    check("G3 the closure is exactly the four plus the four voice-table accessors",
          clo == want, "extra=%s missing=%s" % (sorted(clo - want), sorted(want - clo)))

    P("\n-- G4 absolute data operands summed over the WHOLE closure --")
    tot = {}
    for f in sorted(clo):
        d = absdata(win(f))
        tot[f] = d
        P("0x%06x %-12s abs_data=%d %s" % (f, fnof(f)[1], len(d), sorted(hex(x) for x in d)))
    n_abs = sum(len(v) for v in tot.values())
    check("G4 no function in the closure holds one absolute data operand", n_abs == 0, "total=%d" % n_abs)

    # ---------------- G5 the pref census -----------------------------------
    P("\n-- G5 .text census of the preference cells, split by the closure --")
    site = {}
    for cell in PREF:
        hits = []
        for a, m, o in INS:
            for h in HEX.findall(o):
                if int(h, 16) == cell:
                    hits.append((a, m, o))
        fns = sorted(set(fnof(a)[0] for a, _m, _o in hits))
        inside = [(a, m, o) for a, m, o in hits if fnof(a)[0] in clo]
        site[cell] = hits
        P("0x%06x sites=%d functions=%d inside_closure=%d"
          % (cell, len(hits), len(fns), len(inside)))
        P("         functions: %s" % " ".join("0x%06x" % x for x in fns))
        if inside:
            P("         INSIDE: %s" % inside)
    n_in = sum(len([1 for a, _m, _o in site[c] if fnof(a)[0] in clo]) for c in PREF)
    pins = {0x985AB8: (121, 62), 0x985ABC: (99, 34)}
    got = {c: (len(site[c]), len(set(fnof(a)[0] for a, _m, _o in site[c]))) for c in PREF}
    check("G5 both cells are read/written across .text but NOT ONE site lies in the closure "
          "(counts pinned)", n_in == 0 and got == pins,
          "inside=%d got=%s pins=%s" % (n_in, {hex(k): v for k, v in got.items()}, {hex(k): v for k, v in pins.items()}))

    # ---------------- G6 the handler's own pref sites ----------------------
    P("\n-- G6 FUN_00493ff0, the four's only game caller, does touch both cells --")
    hw = win(HANDLER)
    hcells = [(a, m, o) for a, m, o in hw if any(int(h, 16) in PREF for h in HEX.findall(o))]
    for a, m, o in hcells:
        P("0x%06x %-4s %s" % (a, m, o))
    g6a = [a for a, _m, _o in hcells] == [0x494117, 0x494129, 0x494182, 0x494188, 0x494193, 0x494199]
    check("G6a the handler holds exactly 6 cell-referencing sites, 3 loads + 3 stores",
          g6a and [("load" if o.split(",")[0].startswith(("esi", "ecx", "eax")) else "store") for _a, _m, o in hcells]
          == ["load", "store", "load", "load", "store", "store"],
          "addrs=%s" % ["0x%06x" % a for a, _m, _o in hcells])
    mw = rng(0x494182, 0x49419A)
    for a, m, o in mw:
        P("0x%06x %-4s %s" % (a, m, o))
    g6b = [(a, m, o) for a, m, o in mw] == [(0x494182, "mov", "ecx,DWORD PTR ds:0x985ab8"),
                                            (0x494188, "mov", "eax,ds:0x985abc"),
                                            (0x49418D, "and", "ch,0xf3"),
                                            (0x494190, "and", "ah,0xbf"),
                                            (0x494193, "mov", "DWORD PTR ds:0x985ab8,ecx"),
                                            (0x494199, "mov", "ds:0x985abc,eax")]
    check("G6b the master-off arm loads both cells, masks ch&0xf3 / ah&0xbf, stores both back",
          g6b, "window 0x494182..0x494199")

    # ---------------- G7 call census ---------------------------------------
    P("\n-- G7 who calls the four: every direct call site in .text --")
    calls_by = {}
    for t in TARGETS:
        sites = [(a, fnof(a)) for a, m, o in INS if m == "call" and o == "0x%x" % t]
        calls_by[t] = sites
        P("0x%06x sites=%d idx_callers=%d -> %s"
          % (t, len(sites), fnof(t)[4], ["0x%06x@0x%06x" % (a, f[0]) for a, f in sites]))
    n_calls = sum(len(v) for v in calls_by.values())
    in_handler = sum(1 for v in calls_by.values() for _a, f in v if f[0] == HANDLER)
    outside = sorted(set(f[0] for v in calls_by.values() for _a, f in v if f[0] != HANDLER))
    P("total=%d in_handler=%d outside=%s" % (n_calls, in_handler, ["0x%06x" % x for x in outside]))
    check("G7 12 call sites: 6 in the A/V handler, 6 in five mixer internals, none in the closure",
          n_calls == 12 and in_handler == 6
          and outside == [0x4BCC70, 0x4BCD10, 0x4C6530, 0x5EDAF3, 0x5EDC95]
          and not (set(outside) & {f for f in clo}),
          "n=%d in_handler=%d outside=%s" % (n_calls, in_handler, outside))

    # ---------------- G8 `this` at the handler sites -----------------------
    P("\n-- G8 the `this` argument at each handler call site (nearest preceding ecx write) --")
    g8 = True
    for t in TARGETS:
        for a, f in calls_by[t]:
            if f[0] != HANDLER:
                continue
            pre = [x for x in hw if x[0] < a][-6:]
            src = None
            for _aa, m, o in pre:
                if m == "mov" and o.split(",")[0].strip() == "ecx":
                    src = o.split(",", 1)[1].strip()
            ok = src == "0x%x" % SINGLETON
            g8 &= ok
            P("0x%06x call 0x%06x  this<-%s  %s" % (a, t, src, "OK" if ok else "NOT the singleton"))
    check("G8 all six handler call sites pass the static sound object 0x8a7920 in ecx", g8)

    # ---------------- G9 voice-table shape ---------------------------------
    P("\n-- G9 the per-slot voice table in 0x4b8a60 (start) / 0x4b8af0 (stop) --")
    shape = {}
    for t in (F3, F4):
        w = win(t)
        imuls = [(a, o) for a, m, o in w if m == "imul"]
        bound = [(a, o) for a, m, o in w if m == "cmp" and o == "DWORD PTR [ebp+0x8],0xf"]
        flag_rd = [(a, o) for a, m, o in w if m == "mov" and re.fullmatch(r"dl,BYTE PTR \[[a-z]{3}\+[a-z]{3}\*1\+0x24\]", o)]
        flag_wr = [(a, o) for a, m, o in w if m == "mov" and re.fullmatch(r"BYTE PTR \[[a-z]{3}\+[a-z]{3}\*1\+0x24\],0x[01]", o)]
        lea = [(a, o) for a, m, o in w if m == "lea" and o.endswith("+0x2c]")]
        shape[t] = (imuls, bound, flag_rd, flag_wr, lea)
        P("0x%06x imul=%s bound=%s flag_read=%s flag_write=%s table_lea=%s"
          % (t, [o for _a, o in imuls], [a for a, _o in bound], [a for a, _o in flag_rd],
             [(a, o.split(",")[-1]) for a, o in flag_wr], [o for _a, o in lea]))
    (i3, b3, r3, w3, l3), (i4, b4, r4, w4, l4) = shape[F3], shape[F4]
    check("G9 both take index*0x18 (every imul by 0x18), bound the index at 0xf, read the byte flag "
          "at slot+0x24 and lea the slot+0x2c entry", len(i3) >= 2 and len(i4) >= 2
          and all(o.endswith(",0x18") for _a, o in i3 + i4)
          and len(b3) == len(b4) == 1 and len(r3) == len(r4) == 1
          and len(w3) == len(w4) == 1 and len(l3) == len(l4) == 2,
          "imul=%d/%d lea=%d/%d" % (len(i3), len(i4), len(l3), len(l4)))
    check("G9c the two arms are byte-symmetric: the same imul/lea displacement multiset",
          sorted(o for _a, o in i3) == sorted(o for _a, o in i4)
          and sorted(o for _a, o in l3) == sorted(o for _a, o in l4),
          "lea=%s vs %s" % ([o for _a, o in l3], [o for _a, o in l4]))
    check("G9b the flag STORE distinguishes start from stop: 1 in 0x4b8a60, 0 in 0x4b8af0",
          len(w3) == 1 and len(w4) == 1 and w3[0][1].endswith(",0x1") and w4[0][1].endswith(",0x0"),
          "%s vs %s" % ([o for _a, o in w3], [o for _a, o in w4]))

    # ---------------- G10 the 47-byte enable/disable pair -------------------
    P("\n-- G10 the 47-byte pair: one vtable slot each on the +0x14 inner object --")
    g10 = True
    for t, slot in ((F1, "0x60"), (F2, "0x64")):
        w = win(t)
        ic = indirect_calls(t)
        dc = direct_calls(t)
        guard = [(a, o) for a, m, o in w if m == "cmp" and o.startswith("DWORD PTR [eax+0x14],")]
        jcc = [(a, m, o) for a, m, o in w if m.startswith("j")]
        ok = len(ic) == 1 and ic[0][1] == "DWORD PTR [edx+%s]" % slot and not dc and len(guard) == 1
        g10 &= ok
        P("0x%06x indirect=%s direct=%d guard=%s branch=%s"
          % (t, ic, len(dc), guard, jcc[:1]))
    check("G10 each pair member makes exactly ONE call, into slot 0x60 / 0x64 of [this+0x14], "
          "guarded by cmp [this+0x14],0", g10)

    # ---------------- G11 no import-form call anywhere in the closure ------
    P("\n-- G11 call forms over the closure: vtable only, no import thunk --")
    forms = {}
    for f in sorted(clo):
        ic = indirect_calls(f)
        imp = [(a, o) for a, o in ic if o.startswith("DWORD PTR ds:")]
        forms[f] = (ic, imp)
        if ic:
            P("0x%06x %-12s indirect=%s import_form=%d" % (f, fnof(f)[1], [o for _a, o in ic], len(imp)))
    n_imp = sum(len(v[1]) for v in forms.values())
    slots = sorted(o for v in forms.values() for _a, o in v[0])
    check("G11 zero import-form calls: the closure reaches the outside only through 4 vtable "
          "slots (0x60, 0x64, 0x8c, 0x14)", n_imp == 0 and slots ==
          ["DWORD PTR [eax+0x14]", "DWORD PTR [eax+0x8c]", "DWORD PTR [edx+0x60]", "DWORD PTR [edx+0x64]"],
          "slots=%s" % slots)

    # ---------------- G12 handler switch cases ----------------------------
    P("\n-- G12 the handler's switch: jump table 0x4941ec (read out of the image) --")
    with open(IMAGE, "rb") as fh:
        fh.seek(JT_HANDLER - IMAGE_BASE)
        tbl = list(struct.unpack("<4I", fh.read(16)))
    P("cmd -> target: %s" % ", ".join("0x%x->0x%06x" % (0x4B + k, v) for k, v in enumerate(tbl)))
    lo_b = fnof(HANDLER)[0]
    hi_b = fnof(HANDLER)[0] + fnof(HANDLER)[2]
    tgt = sorted(tbl) + [hi_b]
    cases = {}
    for k, v in enumerate(tbl):
        j = tgt.index(v)
        cases[0x4B + k] = (v, tgt[j + 1])
        P("case 0x%x rows 0x%x: 0x%06x..0x%06x audio_calls=%s"
          % (0x4B + k, CMD_FLAG[0x4B + k], v, tgt[j + 1],
             ["0x%06x->0x%06x" % (a, int(o, 16)) for a, m, o in rng(v, tgt[j + 1])
              if m == "call" and o in ("0x%x" % F1, "0x%x" % F2, "0x%x" % F3, "0x%x" % F4)]))
    check("G12 the jump table maps 0x4b..0x4e to four distinct case blocks",
          len(set(tbl)) == 4 and tbl[0] == 0x494154 and tbl[3] == 0x4940C3, "tbl=%s" % [hex(x) for x in tbl])

    # ---------------- G13 which cases reach the audio object --------------
    P("\n-- G13 which rows reach the audio object, and the row-flag value they pair with --")
    pairs = []
    g13 = True
    for cmd, (v, e) in cases.items():
        w = rng(v, e)
        ac = [(a, o) for a, m, o in w if m == "call" and o in ("0x%x" % F1, "0x%x" % F2, "0x%x" % F3, "0x%x" % F4)]
        flag = CMD_FLAG[cmd]
        st = [(a, o) for a, m, o in w if m == "mov" and o.startswith("DWORD PTR [esi+0x%x]," % flag)]
        gd = [(a, o) for a, m, o in w if m == "mov" and o == "eax,DWORD PTR [esi+0x%x]" % flag]
        P("case 0x%x row 0x%x: audio=%s row_flag_stores=%s row_flag_loads=%s"
          % (cmd, flag, ["0x%06x->0x%06x" % (a, int(o, 16)) for a, o in ac],
             [(a, o.split(",")[-1]) for a, o in st], [a for a, _o in gd]))
        g13 &= (len(st) == 2 and len(gd) == 1)
        for a, o in ac:
            t = int(o, 16)
            if t not in (F3, F4):
                continue
            near = min(st, key=lambda x: abs(x[0] - a)) if st else None
            if near is None:
                g13 = False
                continue
            reg = near[1].split(",")[-1]
            kind, val, at = defuse(w, near[0], reg)
            pairs.append((cmd, a, t, reg, kind, val, near[0], at))
    P("call/flag pairs: %s" % [(hex(c), "0x%06x" % a, "0x%06x" % t, r, k, v)
                               for c, a, t, r, k, v, _p, _q in pairs])
    start_sites = [p for p in pairs if p[2] == F3]
    stop_sites = [p for p in pairs if p[2] == F4]
    g13 = (all(p[5] == 1 for p in start_sites) and all(p[5] == 0 for p in stop_sites)
           and len(start_sites) == 2 and len(stop_sites) == 2)
    check("G13 the start call (0x4b8a60) is only reached from the turn-ON branch (row flag <- 1) "
          "and stop (0x4b8af0) only from turn-OFF (row flag <- 0)", g13,
          "start=%s stop=%s" % ([(hex(p[0]), p[5]) for p in start_sites], [(hex(p[0]), p[5]) for p in stop_sites]))

    case_4e = rng(*cases[0x4E])
    c4e = [(a, o) for a, m, o in case_4e if m == "call"]
    P("case 0x4e (row 0x158b8) calls: %s" % ["0x%06x:%s" % (a, o) for a, o in c4e])
    check("G13b the fourth row (0x4e, flag 0x158b8) is NOT wired to the audio object",
          not any(o in ("0x%x" % F1, "0x%x" % F2, "0x%x" % F3, "0x%x" % F4) for _a, o in c4e)
          and any(o == "0x446490" for _a, o in c4e),
          "calls=%s" % ["0x%06x" % a for a, _o in c4e])

    # ---------------- G14 rivals ------------------------------------------
    P("\n-- G14 rivals that must FAIL on the printed numbers --")
    # a rival "holds" when the printed numbers leave it alive; every holds must be False
    r1 = (n_abs > 0) or (n_in > 0)
    P("R1 \"the four reach the pref cells indirectly, through a callee\" | holds=%s | closure abs_data=%d, "
      "closure pref sites=%d" % (r1, n_abs, n_in))
    r2 = abs(SINGLETON - PREF[0]) <= 0x200
    P("R2 \"the object passed in ecx IS the pref block\"      | holds=%s | this=0x%06x, cell=0x%06x, delta=0x%x"
      % (r2, SINGLETON, PREF[0], abs(SINGLETON - PREF[0])))
    push_args = []
    for t in TARGETS:
        for a, f in calls_by[t]:
            if f[0] != HANDLER:
                continue
            pre = [x for x in hw if x[0] < a][-3:]
            pa = [o for _aa, m, o in pre if m == "push"]
            push_args.append((a, pa[-1] if pa else "-"))
    r3 = any("[" in x for _a, x in push_args)
    P("R3 \"the callee's argument is a pref-derived value\"   | holds=%s | args=%s"
      % (r3, ["0x%06x:%s" % (a, x) for a, x in push_args]))
    r4 = n_in > 0
    P("R4 \"the four ARE the preference toggles (M361 INFERRED)\" | holds=%s | their only state is the "
      "slot+0x24 byte; the row-flag they pair with is the caller's" % r4)
    check("R all four rivals are refuted by the printed numbers", not (r1 or r2 or r3 or r4),
          "r1=%s r2=%s r3=%s r4=%s" % (r1, r2, r3, r4))

    # ---------------- verdict ---------------------------------------------
    P("\n-- VERDICT --")
    P("0x4b8a60 = voice-slot START (flag<-1, play via buffer-vtable+0x8c), 0x4b8af0 = voice-slot STOP")
    P("(flag<-0, buffer-vtable+0x14); 0x4b87f0/0x4b8820 = mixer enable/disable, one vtable slot each")
    P("(0x60/0x64) on the +0x14 inner object.  Reached with this=0x8a7920 (static sound object) and")
    P("a constant slot index.  The preference cells 0x985ab8/0x985abc are touched ONLY in the A/V")
    P("handler 0x493ff0 (6 sites, master-off mask), never by the four or their closure.")

    dig = hashlib.sha256(buf.getvalue().encode()).hexdigest()[:16]
    print("\n%s  M363: %d/%d gates  digest %s" %
          ("PASS" if not FAILS else "FAIL", NCHECK - len(FAILS), NCHECK, dig))
    if FAILS:
        print("FAILED: %s" % ", ".join(FAILS))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
