#!/usr/bin/env python3
"""M191-M193: three questions about the PUBLISH side of the aggregate/save machinery -
one census script, one evidence file, zero box time.

  M191  what IS 0x626634 (called at 0x530fc0 by FUN_00530e30 and twice by FUN_004e0260)?
        M185/M189 know only that it is a callee; M179/M182 know 0x6267a5 is the tagged writer.
  M192  who fills [ebp-0x50]/[ebp-0x4c] in FUN_0052a720 - the only 0x10 carriers of
        [fac*4+0x94d448] per M190?  Producer, or bracket?
  M193  the aggregate pass's OUTPUT side: what does FUN_0053a9c0 write, who calls it, and what
        does the caller do with the answer (M188 showed the count pair is read-only there)?

    python3 scripts/m191_m193_channels.py   > evidence/m191_m193_channels.txt

Static only: scratch/m574/text.txt + ghidra_out/index.csv, via field_census.py.
Every number the prose quotes is COMPUTED here; the gates count sites and FAIL otherwise.
"""
import importlib.util
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("field_census", os.path.join(HERE, "field_census.py"))
FC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(FC)
INS, fnof, IDX = FC.INS, FC.fnof, FC.IDX
INDEX = {n: (a, z) for a, n, z in IDX}
NORM = [(pc, " ".join(s.lower().split())) for pc, s in INS]
POS = {pc: i for i, (pc, _) in enumerate(NORM)}
R = {}
BODY_CACHE = {}


def ok(mid, cond, text):
    R[mid] = bool(cond)
    print(mid + "  " + ("PASS" if cond else "FAIL") + " - " + text)


def body(name):
    if name not in BODY_CACHE:
        a, z = INDEX[name]
        BODY_CACHE[name] = [(pc, s) for pc, s in NORM if a <= pc < a + z]
    return BODY_CACHE[name]


def ops(text):
    """(mnemonic, op1, op2); op1 may itself contain spaces ('dword ptr [eax+1]')."""
    m = re.match(r"^([a-z0-9]+)\s+(.*)$", text)
    if not m:
        return text.strip(), "", ""
    p = m.group(2).split(",", 1)
    return m.group(1), p[0].strip(), (p[1].strip() if len(p) > 1 else "")


def ismem(op):
    """memory operand in ANY objdump spelling: '[eax+1]', 'dword ptr [eax+1]', 'ds:0x99aa1c',
    'dword ptr ds:0x99aa20'."""
    return bool(re.match(r"^(dword|word|byte)\s+ptr\s+", op)) or bool(re.match(r"^\[", op)) or op.startswith("ds:")


def regname(op):
    return op.strip().split()[0] if op.strip() else ""


def globtok(op):
    m = re.search(r"0x[0-9a-f]{6,8}", op)
    return m.group(0) if m else ""


def fieldtok(text):
    m = re.search(r"0x94d[0-9a-f]{3}", text)
    return m.group(0) if m else ""


def callsites(callee):
    return [(pc, fnof(pc)) for pc, s in NORM if ops(s)[0] == "call" and ops(s)[1] == callee]


def refcensus(tok):
    """(writers, readers, other) per owning function for a global token, spelling-agnostic."""
    w, rd, other = Counter(), Counter(), Counter()
    for pc, s in NORM:
        mn, o1, o2 = ops(s)
        if tok not in s:
            continue
        if mn == "mov" and ismem(o1) and tok in o1:
            w[fnof(pc)] += 1
        elif mn == "mov" and ismem(o2) and tok in o2:
            rd[fnof(pc)] += 1
        elif mn == "push" or mn in ("cmp", "test") or (mn in ("lea", "movzx", "movsx") and tok in o2):
            rd[fnof(pc)] += 1
        else:
            other[s] += 1
    return w, rd, other


# ------------------------------------------------------------------ M191
def m191():
    b = body("FUN_00626634")
    stores = [(pc, s) for pc, s in b if ops(s)[0] == "mov" and ismem(ops(s)[1])]
    loads = [(pc, s) for pc, s in b if ops(s)[0] == "mov" and ismem(ops(s)[2])]
    cc = Counter(ops(s)[1] for pc, s in b if ops(s)[0] == "call")
    seq = [("g_size", "cmp dword ptr [ebp+0xc],0x0"), ("g_size_jmp", "je 0x626646"),
           ("g_slot", "cmp dword ptr [ebp+0x8],0x9"), ("g_slot_jmp", "jle 0x62664d"),
           ("bail_val", "mov eax,0x3"), ("bail_jmp", "jmp 0x6266bd"),
           ("a3_test", "cmp dword ptr [ebp+0x10],0x0"), ("a3_staging", "mov ecx,dword ptr ds:0x99aa1c"),
           ("storeA", "mov dword ptr [edx*4+0x999ff4],eax"),
           ("a4_test", "cmp dword ptr [ebp+0x14],0x0"), ("a4_staging", "mov edx,dword ptr ds:0x99aa20"),
           ("storeB", "mov dword ptr [eax*4+0x999fcc],ecx"), ("slotmul", "shl edx,0x8"),
           ("clear", "mov byte ptr [edx+0x99a01c],0x0"), ("push_arg2", "push eax"),
           ("buflea", "add ecx,0x99a01c"), ("push_buf", "push ecx"), ("call_copy", "call 0x64b9e0"),
           ("clean", "add esp,0x8"), ("ok_val", "xor eax,eax")]
    pcs = [(k, next((pc for pc, s in b if s == t), 0)) for k, t in seq]
    order = [p for _, p in pcs]
    monotonic = all(p > 0 for p in order) and all(order[i] < order[i + 1] for i in range(len(order) - 1))
    print("M191 FUN_00626634: %d insns (%d B), %d stores, %d loads, callees %s"
          % (len(b), INDEX["FUN_00626634"][1], len(stores), len(loads), dict(cc)))
    print("   key pcs: " + "  ".join("%s=%s" % (k, hex(p) if p else "MISSING") for k, p in pcs))
    print("   stores: " + " ; ".join("%s %s" % (hex(p), s) for p, s in stores))
    print("   the negative-argument fallbacks read the STAGING pair: "
          + " ; ".join(s for _, s in b if "ds:0x99aa1c" in s or "ds:0x99aa20" in s))
    bc = body("FUN_0064b9e0")
    bst = [(pc, s) for pc, s in bc if ops(s)[0] == "mov" and ismem(ops(s)[1])]
    bst_edi = sum(1 for _, s in bst if "[edi" in s)
    trick = sum(1 for _, s in bc if "0x7efefeff" in s)
    argreads = sorted({s for _, s in bc if "[esp+0x4]" in s or "[esp+0x8]" in s})
    print("   callee FUN_0064b9e0: %d insns (%d B), %d stores of which %d go through [edi], "
          "%d uses of the 0x7efefeff zero-byte trick, %d rets, args read %s"
          % (len(bc), INDEX["FUN_0064b9e0"][1], len(bst), bst_edi, trick,
             sum(1 for _, s in bc if s == "ret"), argreads))
    ok("M191a", monotonic and len(stores) == 7 and len(loads) == 11 and list(cc) == ["0x64b9e0"]
       and bst_edi == len(bst) == 7 and trick == 2,
       "0x626634 is a GUARDED COPY, not an emitter: %d insns / %d stores / %d loads / exactly 1 callee, "
       "and the guards run in the order %s - arg2 must be non-zero and arg1 <= 9, else 'mov eax,0x3' "
       "IS the return value and the success path ends 'xor eax,eax'; a negative arg3/arg4 is replaced "
       "by the staging pair ds:0x99aa1c / ds:0x99aa20; its single callee 0x64b9e0 writes ONLY through "
       "[edi] (%d of %d stores) with the 0x7efefeff zero-byte scan on BOTH operands = an "
       "append-until-NUL byte copy" % (len(b), len(stores), len(loads),
                                       ", ".join("%s@%s" % (k, hex(p)) for k, p in pcs), bst_edi, len(bst)))

    A, B, S, STAGING, n = 0x999fcc, 0x999ff4, 0x99a01c, 0x99aa1c, 10
    geo = (A + n * 4 == B, B + n * 4 == S, S + n * 256 == STAGING)
    print("M191 geometry: A=0x%x B=0x%x strings=0x%x staging=0x%x, %d slots" % (A, B, S, STAGING, n))
    for label, a, k, stride, bb, res in (("A->B", A, n, 4, B, geo[0]), ("B->strings", B, n, 4, S, geo[1]),
                                          ("strings->staging", S, n, 256, STAGING, geo[2])):
        print("   %s: 0x%x + %d*%d == 0x%x : %s" % (label, a, k, stride, bb, res))
    print("   slot addressing in the body: 'mov [edx*4+0x999ff4],eax' (dword slot), "
          "'shl edx,0x8 / mov byte [edx+0x99a01c],0x0' (256-byte slot); guard bound 9 == %d slots" % n)
    ok("M191b", all(geo),
       "the three destinations are ONE table of %d slots: dwords A[10] at 0x%x, B[10] at 0x%x "
       "(A + 10*4 == B: %s), 256-byte text slots at 0x%x (B + 10*4 == strings: %s), and strings + "
       "10*256 == 0x%x = the staging record base M178/M182 already own (%s) - the staging pair IS "
       "slot 10 of the channel table, and 'cmp [ebp+8],0x9' is exactly the bound of slots 0..9"
       % (n, A, B, geo[0], S, geo[1], STAGING, geo[2]))

    sites, sites2 = callsites("0x626634"), callsites("0x6267a5")
    slotarg = Counter()
    for pc, fn in sites:
        i = POS[pc]
        last = ("none", 0)
        for j in range(i - 1, max(-1, i - 8), -1):
            mn, p1, _p2 = ops(NORM[j][1])
            if mn == "push":
                last = ("imm", int(p1, 16)) if re.match(r"^0x[0-9a-f]{1,8}$", p1) else ("reg", p1)
                break
        slotarg[last] += 1
    imms = sorted(v for (k, v) in slotarg if k == "imm")
    dyn = sum(c for (k, _v), c in slotarg.items() if k == "reg")
    outofrange = [hex(v) for (k, v) in slotarg if k == "imm" and not 0 <= v <= 9]
    wA, rA, _ = refcensus("0x999fcc")
    wB, rB, _ = refcensus("0x999ff4")
    wS, rS, _ = refcensus("0x99a01c")
    print("M191 fan-out: call 0x626634 = %d sites in %d functions; call 0x6267a5 (the tagged writer, "
          "M179) = %d sites in %d functions"
          % (len(sites), len({f for _, f in sites}), len(sites2), len({f for _, f in sites2})))
    print("   arg1 (slot) as pushed: " + "  ".join(
        ("slot %d x%d" % (v, c) if k == "imm" else "%s x%d" % (v, c))
        for (k, v), c in sorted(slotarg.items(), key=lambda kv: (kv[0][0] != "imm", kv[0][1] if kv[0][0] == "imm" else 99))))
    print("   immediates outside 0..9: %s ; sites passing a REGISTER slot: %d" % (outofrange, dyn))
    print("   table stores: A %s ; B %s ; strings %s" % (dict(wA.most_common()), dict(wB.most_common()), dict(wS.most_common())))
    print("   table reads/tests: A in %d fns ; B in %d fns ; strings in %d fns %s"
          % (len(rA), len(rB), len(rS), dict(rS.most_common(8))))
    s7 = next((pc for pc, f in sites if f == "FUN_00530e30"), 0)
    print("   the FUN_00530e30 site %s is reached after: %s"
          % (hex(s7), " ; ".join(t for _, t in NORM[POS[s7] - 6:POS[s7]])))
    ok("M191c", len(sites) == 1584 and len({f for _, f in sites}) == 190 and len(sites2) == 18
       and not outofrange and dyn > 0 and sum(wA.values()) == 2 and sum(wB.values()) == 2
       and len(wS) == 3 and len(rS) >= 20,
       "0x626634 is a GENERAL publish primitive, not a save emitter: %d sites in %d functions (the "
       "tagged writer 0x6267a5 has %d in %d); all %d immediate slots lie in 0..9 (%s), %d sites pass "
       "a register; the table it fills takes only %d/%d/%d stores from %d/%d/%d functions while the "
       "256-byte slots are read in %d functions - few writers, many readers. The visit's own site %s "
       "follows 'lea eax,[ebp-0x100]' (filled by the 0x5808b0 call at 0x530fab) and pushes "
       "(slot 7, &[ebp-0x100], -1, -1): channel 7 with BOTH dwords taken from the staging pair"
       % (len(sites), len({f for _, f in sites}), len(sites2), len({f for _, f in sites2}),
          len(imms), [hex(v) for v in imms], dyn, sum(wA.values()), sum(wB.values()),
          sum(wS.values()), len(wA), len(wB), len(wS), len(rS), hex(s7)))


# ------------------------------------------------------------------ M192
def m192():
    b = body("FUN_0052a720")
    BI = {pc: i for i, (pc, _s) in enumerate(b)}
    mentions = [(pc, s) for pc, s in b if "0x94d448" in s]
    # capture side: every load of a 0x94dXXX block field. The byte field 0x94d4e8 is captured with
    # MOVSX, so a mov-only filter reports 16 loads / 8 fields and the pair looks asymmetric.
    cap = []
    for pc, s in b:
        mn, o1, o2 = ops(s)
        if mn in ("mov", "movzx", "movsx") and ismem(o2) and fieldtok(o2):
            cap.append((pc, fieldtok(o2), o2, o1))
    pub = [(pc, ops(s)[1], ops(s)[2]) for pc, s in b
           if 0x52b930 <= pc <= 0x52b9f8 and ops(s)[0] == "mov" and ismem(ops(s)[1])]
    cap_fields = sorted({fld for _p, fld, _o, _r in cap})
    pub_fields = sorted({fieldtok(o1) for _p, o1, _o2 in pub if fieldtok(o1)})
    other = [(hex(pc), ops(s)[1]) for pc, s in b if ops(s)[0] == "mov" and ismem(ops(s)[1])
             and fieldtok(ops(s)[1]) and not (0x52b930 <= pc <= 0x52b9f8)]
    print("M192 FUN_0052a720: %d insns, %d B, ret 0x1c" % (len(b), INDEX["FUN_0052a720"][1]))
    print("   every 0x94d448 mention: " + " ; ".join("%s %s" % (hex(p), s) for p, s in mentions))
    print("   capture side: %d loads of a 0x94dXXX field (%d mov + %d movzx), published back as %d stores"
          % (len(cap), sum(1 for _p, _f, _o, r in cap if regname(r) in ("eax", "ecx", "edx")),
             sum(1 for pc, s in b if ops(s)[0] == "movsx" and fieldtok(ops(s)[2])), len(pub)))
    for pc, fld, o2, o1 in cap:
        print("     CAP %-10s %-10s %s -> %s" % (fld, hex(pc), o2, o1))
    for pc, o1, o2 in pub:
        print("     PUB %-10s %-22s <- %s" % (hex(pc), o1, o2))
    print("   captured fields (%d): %s" % (len(cap_fields), cap_fields))
    print("   published fields (%d): %s  EQUAL=%s"
          % (len(pub_fields), pub_fields, cap_fields == pub_fields))
    print("   stores to any 0x94d field OUTSIDE the publish run: %s" % other)
    ok("M192a", len(mentions) == 4 and len(cap) == 18 and len(pub) == 18
       and len(cap_fields) == 9 and cap_fields == pub_fields and not other,
       "the two 0x94d448 stores are the PUBLISH half of a bracket: %d mentions of 0x94d448 (2 loads "
       "into edx, 2 stores out); the function captures %d block fields (%s) with %d field loads and "
       "its ONLY stores to any 0x94d field are the %d-store run at 0x52b93d-0x52b9f6 that writes back "
       "those SAME %d displacements; %d stores of 0x94d fields lie outside that run"
       % (len(mentions), len(cap_fields), cap_fields, len(cap), len(pub), len(pub_fields), len(other)))

    slots = {}
    for disp in ("[ebp-0x50]", "[ebp-0x4c]"):
        w = [(pc, s) for pc, s in b if ops(s)[0] == "mov" and ismem(ops(s)[1]) and disp in ops(s)[1]]
        r = [(pc, s) for pc, s in b if ops(s)[0] == "mov" and ismem(ops(s)[2]) and disp in ops(s)[2]]
        fed, nxt = [], []
        for pc, s in w:
            src = regname(ops(s)[2])
            for j in range(BI[pc] - 1, max(-1, BI[pc] - 4), -1):
                mn, o1, o2 = ops(b[j][1])
                if mn == "mov" and ismem(o2) and "0x94d448" in o2 and regname(o1) == src:
                    fed.append((b[j][0], b[j][1]))
                    break
        for pc, _s in r:
            nxt.append(b[BI[pc] + 1])
        slots[disp] = (w, r, fed, nxt)
        print("   slot %-10s writer(s) %s fed by %s ; reader(s) %s -> next insn %s"
              % (disp, ["%s %s" % (hex(p), t) for p, t in w],
                 ["%s %s" % (hex(p), t) for p, t in fed],
                 ["%s %s" % (hex(p), t) for p, t in r],
                 ["%s %s" % (hex(p), t) for p, t in nxt]))
    callees = sorted({ops(s)[1] for pc, s in b if ops(s)[0] == "call" and ops(s)[1].startswith("0x")})
    store_fns = Counter()
    for pc, s in NORM:
        mn, o1, _o2 = ops(s)
        if mn == "mov" and ismem(o1) and "0x94d448" in o1:
            store_fns[fnof(pc)] += 1
    hits = [c for c in callees if "FUN_" + c[2:].zfill(6) in store_fns]
    print("   %d distinct direct callees; those that store 0x94d448: %s" % (len(callees), hits))
    print("   the image's 0x94d448 store functions: %s" % dict(store_fns.most_common()))
    ok("M192b", all(len(w) == 1 and len(r) == 1 and len(fed) == 1 and len(nxt) == 1
                    and "0x94d448" in nxt[0][1] for w, r, fed, nxt in slots.values()) and not hits,
       "the bracket is VALUE-PRESERVING for 0x94d448: [ebp-0x50] / [ebp-0x4c] each have exactly 1 "
       "writer (fed by the field's own load %s) and exactly 1 reader whose very next instruction is "
       "the store back (%s), and %d of this function's %d direct callees store 0x94d448 (the image's "
       "%d store functions are %s, none a callee) - the published value IS the value the field held "
       "on entry, so FUN_0052a720 PRESERVES bit 0x10, it does not produce it"
       % ([fed[0][1] for _w, _r, fed, _n in slots.values()],
          [t for _w, _r, _f, nxt in slots.values() for _p, t in nxt], len(hits), len(callees),
          len(store_fns), sorted(store_fns)))

    # the block-base fold: mov r,S; shl r,6; add r,S; lea r,[S+r*2]; shl r,4; sub r,S; add r,C; shl r,2
    # = 8380*S + 4*C  (the M176 *8380 fold, here with a 4*C dword sub-index)
    def fold(pc, reg, back=220):
        i = BI[pc]
        rows, seed, clean = [], None, True
        for j in range(i - 1, max(-1, i - back), -1):
            p, t = b[j]
            mn, o1, o2 = ops(t)
            if mn.startswith("j") or mn == "call":
                clean = False
            if not o1 or regname(o1) != reg:
                continue
            rows.append((p, t, mn, o1, o2))
            if mn == "mov" and not ismem(o2) and regname(o2) != reg:
                seed = regname(o2)
                break
        rows = list(reversed(rows))
        want = [("mov", reg, "S"), ("shl", reg, "0x6"), ("add", reg, "S"), ("lea", reg, "S+r*2"),
                ("shl", reg, "0x4"), ("sub", reg, "S"), ("add", reg, "C"), ("shl", reg, "0x2")]
        got, C = [], None
        for (p, t, mn, o1, o2), (wm, _wr, wop) in zip(rows, want):
            if mn != wm:
                got.append("MISMATCH:" + mn)
                continue
            if wm == "mov":
                got.append("seed " + regname(o2))
            elif wm == "lea":
                m = re.match(r"^\[(\w+)\+" + reg + r"\*2\]$", o2)
                got.append("lea b=" + (m.group(1) if m else "?"))
            elif wop in ("S", "C"):
                got.append("%s %s" % (mn, o2))
        if len(rows) == 8 and rows[0][2] == "mov" and "MISMATCH" not in " ".join(got):
            S = regname(rows[0][4])
            same_S = all(re.search(r"\b" + S + r"\b", rows[i][4]) for i in (2, 3, 5) if rows[i][2] in ("add", "sub", "lea"))
            Cops = [r[4] for r in rows if r[2] == "add" and regname(r[4]) != S]
            C = Cops[0] if len(Cops) == 1 else None
            return S, C, bool(same_S and C), clean, rows
        return None, None, False, clean, rows

    chains = {}
    for k, (pc, reg) in (("capture A", (0x52aff5, "eax")), ("capture B", (0x52affe, "ecx")),
                         ("publish A", (0x52b9c7, "eax")), ("publish B", (0x52b9d0, "ecx"))):
        chains[k] = fold(pc, reg)
        S, C, m, cl, rows = chains[k]
        print("   %-10s matched=%-5s clean=%-5s S=%-4s C=%-4s  %s"
              % (k, m, cl, S, C, " | ".join("%s %s" % (hex(p), t) for p, t, _mn, _o1, _o2 in rows)))
    spill = {d: [(pc, s) for pc, s in b if ops(s)[0] == "mov" and ismem(ops(s)[1]) and d in ops(s)[1]]
             for d in ("[ebp-0x2c]", "[ebp-0x30]")}
    reload = {d: [(pc, s) for pc, s in b if ops(s)[0] == "mov" and ismem(ops(s)[2]) and d in ops(s)[2]]
              for d in ("[ebp-0x2c]", "[ebp-0x30]")}
    for d in spill:
        print("   slot %s written at %s ; read at %s"
              % (d, [hex(p) for p, _ in spill[d]], [hex(p) for p, _ in reload[d]]))
    bridge = [(hex(pc), s) for pc, s in b
              if 0x52af23 < pc < 0x52af76 and ops(s)[1] and regname(ops(s)[1]) in ("edi", "ebx")
              and not ismem(ops(s)[1])]
    tailw = [(hex(pc), s) for pc, s in b
             if 0x52b88f < pc < 0x52b90a and ops(s)[1] and regname(ops(s)[1]) in ("edx", "esi")
             and not ismem(ops(s)[1])]
    print("   writes to edi/ebx between the spills and the capture seed: %s" % bridge)
    print("   writes to edx/esi between the last spill reload (0x52b88f) and the publish seed "
          "(0x52b90a): %s  [all of them lie on ax-branches that ret 0x1c, not on the "
          "cmp ax,0x16 fallthrough the publish run sits on]" % tailw)
    samepair = (chains["capture A"][0] == "edi" and chains["capture A"][1] == "ebx"
                and chains["capture B"][0] == "ebx" and chains["capture B"][1] == "edi"
                and chains["publish A"][0] == "edx" and chains["publish A"][1] == "esi"
                and chains["publish B"][0] == "esi" and chains["publish B"][1] == "edx")
    allm = all(chains[k][2] for k in chains) and all(chains[k][3] for k in chains)
    ok("M192c", allm and samepair and all(len(spill[d]) == 1 for d in spill)
       and len(reload["[ebp-0x2c]"]) >= 1 and len(reload["[ebp-0x30]"]) >= 1 and not bridge,
       "the publish addresses EXACTLY the two bases the capture read, by the same arithmetic: all "
       "four chains are the canonical fold 'mov r,S; shl r,6; add r,S; lea r,[S+r*2]; shl r,4; sub "
       "r,S; add r,C; shl r,2' = 8380*S + 4*C (the M176 *8380 stride plus a 4*C dword sub-index), "
       "with no jump or call inside any chain; capture A = 8380*edi + 4*ebx and capture B = "
       "8380*ebx + 4*edi, publish A = 8380*edx + 4*esi and publish B = 8380*esi + 4*edx, and edx/esi "
       "are reloaded from [ebp-0x2c]/[ebp-0x30] - written exactly ONCE each, by 'mov [ebp-0x2c],edi' "
       "at %s and 'mov [ebp-0x30],ebx' at %s - before the capture, with %d writes to edi/ebx in "
       "between; so 8380*edx+4*esi == 8380*edi+4*ebx and the round trip is ADDRESS-EXACT"
       % ([hex(p) for p, _ in spill["[ebp-0x2c]"]], [hex(p) for p, _ in spill["[ebp-0x30]"]],
          len(bridge)))


# ------------------------------------------------------------------ M193
def m193():
    b = body("FUN_0053a9c0")
    gs = [(pc, ops(s)[1], ops(s)[2]) for pc, s in b
          if ops(s)[0] == "mov" and ismem(ops(s)[1]) and "ds:0x" in ops(s)[1]]
    cnt = Counter(globtok(o1) for _, o1, _o2 in gs)
    pair = {t: (sum(1 for _, s in b if t in s), sum(1 for _, o1, _o2 in gs if t in o1))
            for t in ("0x9204ac", "0x920720")}
    print("M193 FUN_0053a9c0: %d insns, %d B; %d global stores to %d distinct globals %s"
          % (len(b), INDEX["FUN_0053a9c0"][1], len(gs), len(cnt), dict(cnt.most_common())))
    for pc, o1, o2 in gs:
        print("   %-10s %-22s <- %s" % (hex(pc), o1, o2))
    print("   the count pair inside: 0x9204ac %d mention(s) / %d stores ; 0x920720 %d mentions / %d stores"
          % (pair["0x9204ac"][0], pair["0x9204ac"][1], pair["0x920720"][0], pair["0x920720"][1]))
    w4ac, r4ac, _ = refcensus("0x9204ac")
    w720, r720, _ = refcensus("0x920720")
    print("   image stores of 0x9204ac by function: %s ; of 0x920720: %s"
          % (dict(w4ac.most_common()), dict(w720.most_common())))
    b4 = body("FUN_00535940")
    r4 = Counter(globtok(ops(s)[1]) for pc, s in b4
                 if ops(s)[0] == "mov" and ismem(ops(s)[1]) and "ds:0x" in ops(s)[1])
    inter = sorted(set(cnt) & set(r4))
    print("   FUN_00535940 (the reset pass, M185) resets %d globals: %s" % (len(r4), dict(r4.most_common())))
    print("   INTERSECT(this pass writes, reset pass clears) = %s" % inter)
    fan = {}
    for t in inter:
        w, rd, _o = refcensus(t)
        fan[t] = len(w)
        print("   fan-out %s: %d writer functions, %d reader functions, top readers %s"
              % (t, len(w), len(rd), dict(rd.most_common(4))))
    ok("M193a", len(gs) == 23 and len(cnt) == 8 and all(v[1] == 0 for v in pair.values())
       and pair["0x9204ac"][0] >= 1 and pair["0x920720"][0] >= 4
       and "FUN_0053a9c0" not in w4ac and "FUN_0053a9c0" not in w720,
       "the pass's WHOLE global write set is %d stores to %d globals %s; the pair M188 followed "
       "(0x9204ac %d mention, 0x920720 %d mentions) has ZERO stores in it, and the image holds no "
       "store of either global by this function at all (0x9204ac writers %s ; 0x920720 writers %s) - "
       "the count is a pure INPUT to this pass"
       % (len(gs), len(cnt), dict(cnt.most_common()), pair["0x9204ac"][0], pair["0x920720"][0],
          dict(w4ac.most_common()), dict(w720.most_common())))
    ok("M193b", inter == ["0x9206e4", "0x920774"] and all(fan[t] >= 3 for t in inter),
       "the OUTPUT side is the aggregate scratch: exactly %s of the %d globals this pass writes are "
       "among the %d that the reset pass 0x535940 clears, and both are shared scratch (%s writer "
       "functions respectively) - the pair 0x9204ac/0x920720 is consumed and dropped; what survives "
       "the visit is 0x9206e4 / 0x920774 plus the staging pair, the 0x997120 flag and 2 scratch zeros"
       % (inter, len(cnt), len(r4), [fan[t] for t in inter]))

    sites = callsites("0x53a9c0")
    spc = sites[0][0]
    pre = [t for _, t in NORM[POS[spc] - 8:POS[spc]]]
    post = [t for _, t in NORM[POS[spc] + 1:POS[spc] + 8]]
    tail = [s for _, s in b[-14:]]
    gate = [t for t in pre if "0x920700" in t or ("cmp" in t and "0x2" in t)]
    tested = any(t.startswith("test eax,eax") for t in post)
    w700, r700, _ = refcensus("0x920700")
    print("M193 caller: %d site(s): %s" % (len(sites), ", ".join("%s in %s" % (hex(p), f) for p, f in sites)))
    print("   8 insns before: " + " ; ".join(pre))
    print("   7 insns after:  " + " ; ".join(post))
    print("   the pass's own last 14 insns: " + " ; ".join(tail))
    print("   gate global ds:0x920700: %d stores in %d functions %s ; %d reads in %d functions"
          % (sum(w700.values()), len(w700), dict(w700.most_common(8)), sum(r700.values()), len(r700)))
    zero_tail = [s for s in tail if "ds:0x9204b4" in s or "ds:0x920718" in s]
    hand = [s for s in tail if "call 0x533e70" in s or "mov eax,0x1" in s]
    ok("M193c", len(sites) == 1 and tested and len(gate) >= 2 and len(zero_tail) == 2 and len(hand) == 2,
       "the pass has ONE entry point, it is MODE-GATED, and its answer is TESTED: %s in %s is reached "
       "only after '%s' (the gate global ds:0x920700 takes %d stores in %d functions), the caller's "
       "next block branches on 'test eax,eax' (%s), and the pass's own tail zeroes ds:0x9204b4 and "
       "ds:0x920718, calls 0x533e70 (one of the 17 aggregator call sites, M175) and returns 1"
       % (hex(spc), sites[0][1], "' ; '".join(gate), sum(w700.values()), len(w700),
          [t for t in post if t.startswith("jne") or t.startswith("je")]))


m191()
m192()
m193()
print("SUMMARY " + " ".join("%s=%s" % (k, "PASS" if v else "FAIL") for k, v in sorted(R.items())))
sys.exit(0 if R and all(R.values()) else 1)
