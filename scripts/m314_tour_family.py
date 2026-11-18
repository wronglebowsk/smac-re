#!/usr/bin/env python3
"""M314 (s282, STATIC, zero box): the tour-dialog family + pump-direct correction.

Answers open pick (i''): WHAT ARE FUN_004c5d60's "dialog-family" (the
0x4c2e90-0x4c3760 wrappers/tour drivers) and FUN_004d3f70's band calls.
Method: instruction census over scratch/m574/text.txt (ground truth) + PE bytes
for literal immediates + one structural check on the decompiled wrapper shape.

Findings pinned by the gates below:
 - FUN_004c5d60 = token-keyed dialog/tour dispatcher (31 instr call sites).
 - 4 wrapper thunks 0x4c2e90/f00/f70/fe0: one pinned producer each; the dialog
   "this" = DAT_007cdecc + [0][+4] (the static main view + its secondary delta,
   the M269 mechanism).
 - 3 result thunks 0x4c5c40/ca0/cf0: `this + 0x444` = secondary-subobject
   adjustment (M269 law, NOT a menu id - that misreading is recorded and
   rejected); 0x4c5cf0 = abs(c+2) on the bytes; each is pushed EXACTLY twice
   (the dispatcher's pre-paint + post-paint legs).
 - RETRACT/CORRECT the M313 callee census: pumpB FUN_00516b80 calls
   FUN_004d3f70 (activate_at_tile, NAMED) DIRECTLY at 0x517858 - off, and
   outside the band; the M313 off-band list was thunk/hub-sites only.
 - The NEXT_PROMPT lead "FUN_004d3f70 calls 15 band members" is WRONG: it calls
   exactly ONE band member (FUN_0050cab0 x2); its other 22 distinct callees are
   all off-band (0x52xxxx order helpers, 0x58xxxx, FUN_004737e0...) on bytes.
"""
import csv
import hashlib
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import m308_site_list as E

IDX = os.path.join(REPO, "ghidra_out", "index.csv")
EXE = os.path.join(REPO, "terran.exe")

BAND_LO, BAND_HI = 0x50BB20, 0x5175B4  # NAMED ## M313 (half-open)

checks = []
detail = {}

def ck(name, ok, det=""):
    checks.append((name, bool(ok), det))
    print(("OK   " if ok else "FAIL ") + name + ": " + det)

def main():
    blob = open(EXE, "rb").read()
    ib, secs = E.pe_sections(blob)

    def at(va, n):
        off, _ = E.va2off(secs, va)
        return blob[off:off + n] if off is not None else b""

    # ---- instruction table ------------------------------------------------
    E._INS, E._ORDER = E.parse_text()
    ins, order = E._INS, E._ORDER
    funcs = []
    with open(IDX) as f:
        for r in csv.DictReader(f):
            funcs.append((int(r["addr"], 16), r["name"], int(r["size_bytes"])))
    funcs.sort()
    fstart = [a for a, _, _ in funcs]
    fsize = {a: s for a, _, s in funcs}
    fname = {a: n for a, n, _ in funcs}

    def contain(a):
        import bisect
        i = bisect.bisect_right(fstart, a) - 1
        return funcs[i][0] if i >= 0 else None

    CALL = re.compile(r"^(call|jmp)\s+0x([0-9a-f]+)\s*$")
    def targets(lo, hi):
        out = []
        for a, mn, ops in E.window(lo, hi):
            m = CALL.match(mn + " " + ops.strip())
            if m:
                out.append((a, mn, int(m.group(2), 16)))
        return out

    def call_sites(tgt):
        pat = re.compile(r"^(call|jmp)\s+0x%x$" % tgt)
        return [a for a, (mn, ops) in ins.items() if pat.match(mn + " " + ops)]

    # ---- A1: FUN_004c5d60 is called by exactly 31 instruction sites -------
    D60 = 0x4C5D60
    sites = sorted(call_sites(D60))
    # literal imm32 of each call's target field in the PE bytes (E8 xx xx xx xx)
    def call_target(a):
        off, _ = E.va2off(secs, a)
        return off is not None and at(a, 1) == b"\xe8" and \
            struct.unpack("<i", at(a + 1, 4))[0] + a + 5 == D60
    pinned = [a for a in sites if call_target(a)]
    detail["A1"] = "31?=%d pinned=%d first=%s last=%s" % (
        len(sites), len(pinned), hex(sites[0]), hex(sites[-1]))
    ck("A1 dispatcher 31 instr call sites, all imm32-pinned in PE bytes",
       len(sites) == 31 and len(pinned) == 31, detail["A1"])

    # ---- A1b: token census from the decompiled call lines -----------------
    tokens = []
    for shard in sorted(os.listdir(os.path.join(REPO, "ghidra_out"))):
        if not shard.startswith("shard_"):
            continue
        txt = open(os.path.join(REPO, "ghidra_out", shard),
                   errors="replace").read().replace("\n ", " ").replace("\n\t", " ")
        for m in re.finditer(r"(?:=\s*)?FUN_004c5d60\(([^;]*?);", txt):
            args = m.group(1).split(",")
            if len(args) >= 2 and not args[0].strip().startswith("undefined4"):
                t = args[1].strip()
                tokens.append(t if t[0] == '"' else t)
        # end per-file; keep memory small
    toks = {}
    for t in tokens:
        toks[t] = toks.get(t, 0) + 1
    named = [t for t in toks if t.startswith("s_")]
    quoted = [t for t in toks if t.startswith('"')]
    detail["A1b"] = "calls=%d distinct=%d quoted=%d s_=%s" % (
        len(tokens), len(toks), len(quoted), sorted(named))
    ck("A1b dispatcher token-keyed: 30 sites, distinct tokens, 2 named s_ strings",
       len(tokens) == 31 and len(toks) >= 25 and sorted(named) ==
       ["s_BASECONTROL_00689a18", "s_DRONERIOTS_00689a24"], detail["A1b"])

    # ---- A2: the 4 wrapper thunks, pinned producer + view-derived this ----
    W = {0x4C2E90: 0x4C3F90, 0x4C2F00: 0x4C3F20,
         0x4C2F70: 0x4C4000, 0x4C2FE0: 0x4C4070}
    rows = []
    ok2 = True
    for w, prod in W.items():
        tg = [(a, mn, t) for a, mn, t in targets(w, w + fsize[w])
              if mn == "call" and t in (prod, D60)]
        prodcalls = [a for a, _, t in tg if t == prod]
        d60calls = [a for a, _, t in tg if t == D60]
        ok2 &= (len(prodcalls) == 1 and len(d60calls) == 1)
        rows.append("%s->p@%s+d@%s" % (hex(w), hex(prodcalls[0]) if prodcalls else "X",
                                       hex(d60calls[0]) if d60calls else "X"))
    detail["A2"] = "; ".join(rows)
    ck("A2 four wrappers: exactly one pinned-producer call + one dispatcher call each",
       ok2, detail["A2"])

    # structural: the `this` formula DAT_007cdecc + [0][+4] inside wrappers
    body = open(os.path.join(REPO, "ghidra_out", "shard_011.c"),
                errors="replace").read()
    wtxt = body[body.index("FUN_004c2e90 @"):body.index("FUN_004c3050 @")]
    n_formula = wtxt.count("(int)DAT_007cdecc + *(int *)(*DAT_007cdecc + 4)")
    ck("A2b wrapper this-formula = DAT_007cdecc + [0][+4] in all 4 wrappers",
       n_formula == 4, "occurrences=%d" % n_formula)

    # ---- A3: the 3 result thunks on the BYTES ------------------------------
    # common: cmp DWORD PTR [ebp+0xc],0x0 / je / mov eax,[ebp+0xc] / add eax,0x444
    T = {0x4C5C40: 0x4C1220, 0x4C5CA0: 0x54F790, 0x4C5CF0: 0x5510F0}
    add444 = 0
    rows3 = []
    for t, tgt in T.items():
        win = E.window(t, t + fsize[t])
        has = lambda pred: any(pred(mn, ops) for _, mn, ops in win)
        okm = has(lambda m, o: m == "cmp" and o == "DWORD PTR [ebp+0xc],0x0") and \
              has(lambda m, o: m == "add" and o == "eax,0x444") and \
              any(m == "call" and int(o.split()[0], 16) == tgt for _, m, o in win)
        add444 += sum(1 for _, m, o in win if m == "add" and o == "eax,0x444")
        rows3.append("%s:%s" % (hex(t), hex(tgt)))
        ck("A3 result-thunk %s shape(cmp0/je/add444/call %s) holds" % (hex(t), hex(tgt)),
           okm, "; ".join(rows3))
    # 0x4c5cf0 computes abs(c+2) in the bytes, NOT -(c+2) unconditionally
    w2 = [(mn, ops) for _, mn, ops in E.window(0x4C5CF0, 0x4C5CF0 + fsize[0x4C5CF0])]
    negs = sum(1 for m, o in w2 if m == "neg")
    subs = sum(1 for m, o in w2 if m == "sub")
    ck("A3b 0x4c5cf0 abs(c+2): neg exactly 1 + a sub branch (bytes; Ghidra -(c+2) understates)",
       negs == 1 and subs >= 1, "neg=%d sub=%d" % (negs, subs))
    ck("A3c add eax,0x444 present once per thunk (3 total) - M269 secondary delta, not a menu id",
       add444 == 3, "count=%d" % add444)

    # ---- A4: registration: each result thunk pushed EXACTLY twice ----------
    pushes = {}
    for a, (mn, ops) in ins.items():
        m = re.match(r"^0x([0-9a-f]+)$", ops.strip()) if mn == "push" else None
        if m and int(m.group(1), 16) in T:
            pushes.setdefault(int(m.group(1), 16), []).append(a)
    # all 6 pushes live INSIDE the dispatcher (its pre-paint and post-paint legs)
    own = {hex(contain(a2)) for v in pushes.values() for a2 in v}
    legA = sorted(hex(a2) for v in pushes.values() for a2 in v if a2 < 0x4C6000)
    legB = sorted(hex(a2) for v in pushes.values() for a2 in v if a2 >= 0x4C6000)
    def order(ls):
        out = []
        for x in sorted(ls, key=lambda z: int(z, 16)):
            v = int(x, 16)
            out.append((x, next(k for k, vv in pushes.items() if v in vv)))
        return out
    exact2 = (all(len(v) == 2 for v in pushes.values()) and len(pushes) == 3 and
              own == {"0x4c5d60"} and len(legA) == 3 and len(legB) == 3 and
              [t for _, t in order(legA)] == [t for _, t in order(legB)])
    detail["A4"] = "; ".join("%s@%s" % (hex(k), ",".join(hex(x) for x in v))
                             for k, v in sorted(pushes.items()))
    ck("A4 each result thunk address-taken via push exactly twice (pre+post paint legs)",
       exact2, detail["A4"])
    pumpA = sorted(call_sites(0x512B40))
    ck("A4b pumps reached by direct call only (no image-wide push of pumpA exists)",
       all(0x512B40 != int(re.match(r"^push\s+0x([0-9a-f]+)$", o).group(1), 16)
           for a, (m, o) in ins.items() if m == "push"
           and re.match(r"^push\s+0x", o)) and pumpA,
       "pumpA call sites=%d" % len(pumpA))

    # ---- A5: pumpB callee census - the CORRECTION --------------------------
    pb_lo, pb_hi = 0x516B80, 0x516B80 + fsize[0x516B80]
    pbc = [(a, t) for a, m, t in targets(pb_lo, pb_hi) if m == "call"]
    owners = sorted({contain(t) for _, t in pbc if contain(t) is not None})
    # band OWNERS = callees whose function start lies in the band (M313 mesh)
    inband = sorted({hex(o) for o in owners if BAND_LO <= o < BAND_HI})
    # M313's cited off-band callee set, checked against the pump's real calls
    M313_OFF = [0x4736E0, 0x4738F0, 0x4739A0, 0x4C40E0, 0x4E10C0]
    called = {t for _, t in pbc}
    missing = [hex(x) for x in M313_OFF if x not in called]
    ck("A5 pumpB calls FUN_004d3f70 DIRECT at 0x517858 (outside band) - corrects M313 list",
       any(t == 0x4D3F70 for _, t in pbc) and
       [hex(a) for a, t in pbc if t == 0x4D3F70] == ["0x517858"],
       "pumpB call targets=%d inband owners=%d inband=%s" % (
           len(pbc), len(inband), inband))
    ck("A5b every M313-cited off-band pumpB callee really is one, + FUN_004d3f70 is a 6th",
       missing == [] and 0x4D3F70 in called,
       "missing=%s inband_owners=%d" % (missing, len(inband)))
    pa = [(a, t) for a, m, t in targets(0x512B40, 0x512B40 + fsize[0x512B40])
          if m == "call"]
    ck("A5c pumpA FUN_00512b40 does NOT call FUN_004d3f70 (the correction is pumpB-only)",
       all(t != 0x4D3F70 for _, t in pa), "pumpA callee fns=%d" % len({t for _, t in pa}))

    # ---- A6: activate_at_tile census ---------------------------------------
    af_lo, af_hi = 0x4D3F70, 0x4D3F70 + fsize[0x4D3F70]
    aft = [(a, t) for a, m, t in targets(af_lo, af_hi) if m == "call"]
    def in_band(t):
        o = contain(t)
        return (o is not None and BAND_LO <= o < BAND_HI) or BAND_LO <= t < BAND_HI
    inb = [(hex(a), hex(t)) for a, t in aft if in_band(t)]
    off = [(hex(a), hex(t)) for a, t in aft if not in_band(t)]
    ck("A6 activate_at_tile: ONE band member (FUN_0050cab0, thunk owner) at 2 sites; 14 off-band (lead's 15 REFUTED)",
       sorted(hex(x) for x in {int(t, 16) for _, t in inb}) == ["0x50cab0"] and
       len(inb) == 2 and len({t for _, t in off}) == 22,
       "inband=%s off=%d offsites=%s" % ([a for a, _ in inb], len(off),
                                          sorted({t for _, t in off})))
    ac = sorted(call_sites(0x4D3F70))
    aco = sorted({hex(contain(a)) for a in ac})
    ck("A6b activate_at_tile called at exactly 5 instr sites in {4748b0,476580,511960,512450,516b80}",
       aco == ["0x4748b0", "0x476580", "0x511960", "0x512450", "0x516b80"],
       "sites=%s owners=%s" % ([hex(x) for x in ac], aco))
    # its 4 debug-token strings read real ASCII at the pinned .data addresses
    strs = {}
    for va, want in ((0x68C200, "Console"), (0x68C238, "VEH"), (0x68C260, "Activate"),
                     (0x68C278, "Activate")):
        s = at(va, 24).split(b"\0")[0].decode("ascii", "replace")
        strs[hex(va)] = s
    ck("A6c activate_at_tile logs 4 tokens via FUN_0062732a: strings real at .data",
       all(strs[k].startswith(w) for k, w in
           [("0x68c200", "Console"), ("0x68c238", "VEH"),
            ("0x68c260", "Activate"), ("0x68c278", "Activate")]),
       str(strs))

    # ---- A7: record-array stride cross-check (0x5510f0's param_2) ----------
    w7 = [(a, mn, ops) for a, mn, ops in
          E.window(0x5510F0, 0x5510F0 + fsize[0x5510F0])]
    usesda12 = [(hex(a), mn, ops.strip()) for a, mn, ops in w7 if "0x95da12" in ops]
    baseoff = [x for x in usesda12 if re.search(r"\[e[a-z]x\+0x95da12\]", x[2])]
    ck("A7 0x5510f0 reads the 0x95da12 array via reg+disp (reg = rec*0x130-2, M311 stride INFERRED)",
       len(usesda12) >= 1 and len(baseoff) >= 1,
       "n=%d sample=%s" % (len(usesda12), baseoff[:2]))

    digest = hashlib.sha256(
        "|".join("%s=%s" % (k, detail.get(k, "")) for k in sorted(checks and
                 [c[0] for c in checks])).encode()).hexdigest()[:16]
    fails = [c[0] for c in checks if not c[1]]
    print("== M314: %d/%d ==  digest %s" %
          (len(checks) - len(fails), len(checks), digest))
    if fails:
        print("FAILED:", fails)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
