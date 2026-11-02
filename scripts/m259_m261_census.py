#!/usr/bin/env python3
"""M259-M261: three static census questions on terran.exe through ONE instrument (the whole-image
instruction corpus + the image-derived vtable map + containment via ghidra_out/index.csv).

  M259  the 7 dwords at terrain record +16..+43: who writes them, who reads them, what they are
  M260  who allocates the ~140 KB map-view objects (live slots spaced 0x224b8, slot 0 at 0x8f79e0)
  M261  what the 15 unique slots of vtable 0x679f98 are and which screen calls its constructors

    python3 scripts/m259_m261_census.py      # all gates -> SUMMARY M259/M260/M261: n/14 gates PASS
Static only: no box, no /proc, no gdb. Instrument imported from scripts/m235_m237_records.py.
"""
import os, re, sys, bisect, struct, collections, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
_spec = importlib.util.spec_from_file_location("m235", os.path.join(HERE, "m235_m237_records.py"))
M = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(M)
NM, fnof, IDXMAP, IMG = M.NM, M.fnof, M.IDXMAP, M.IMG
dw, body, VT = M.dw, M.body, M.VT
PC2T = dict(NM)
def at(pc): return PC2T.get(pc, "<missing>")
def texts(fn): return [s for _, s in body(fn)]
def has(fn, *pats):
    b = body(fn); return all(any(re.match(p, s) for _, s in b) for p in pats)
def seq(fn, pat): return [hex(pc) for pc, s in body(fn) if re.match(pat, s)]
def window(fn, want):
    """True if the literal instruction sequence `want` occurs in fn's body."""
    t = texts(fn); n = len(want)
    return any(t[i:i + n] == want for i in range(len(t) - n + 1))
def strs(fn, cap=10):
    out = []
    for pc, s in body(fn):
        for m in re.finditer(r"0x6[0-9a-f]{5}", s):
            v = int(m.group(), 16)
            if 0x660000 <= v < 0x6a0000:
                t2 = M.readstr(v)
                if t2 and len(t2) > 3 and t2 not in out: out.append(t2)
        if len(out) >= cap: break
    return out
GATES = []
def G(desc, cond, numbers): GATES.append((desc, bool(cond), numbers))

# band access = record dword 3+idx: [base + idx*4 + 0xc] with base holding the terrain array
FORM = re.compile(r"\[(e?[a-z]{2,3})\+(e?[a-z]{2,3})\*4\+0xc\]")
LOADB = re.compile(r"^mov (e?[a-z]{2,3}),(?:dword ptr )?ds:0x92ae14$")
LEA = re.compile(r"^lea (e?[a-z]{2,3}),\[(e?[a-z]{2,3})\+(e?[a-z]{2,3})\*4\]$")
_ld = {}
def terrain_regs(fn):
    """registers holding the terrain-array base, or a record pointer lea'd from it"""
    if fn not in _ld:
        t = texts(fn)
        s = set(m.group(1) for m in (LOADB.match(x) for x in t) if m)
        for _ in range(2):
            for m in (LEA.match(x) for x in t):
                if m and m.group(2) in s: s.add(m.group(1))
        _ld[fn] = s
    return _ld[fn]
def band_accesses():
    w = collections.Counter(); r = collections.Counter(); sites = collections.defaultdict(list)
    for pc, s in NM:
        m = FORM.search(s)
        if not m: continue
        fn = fnof(pc)
        if fn not in IDXMAP or m.group(1) not in terrain_regs(fn): continue
        (w if M.is_store(s) else r)[fn] += 1
        sites[(fn, "W" if M.is_store(s) else "R")].append((hex(pc), s, m.group(2)))
    return w, r, sites

def m259():
    W, R, SITES = band_accesses()
    det = []
    for ld, st in ((0x4f0dec, 0x4f0def), (0x5a86a7, 0x5a86aa)):
        b = body(fnof(st)); i = [k for k, (p, _) in enumerate(b) if p == st][0]
        win = " ; ".join(s for _, s in b[max(0, i - 30):i + 14])
        det.append("%s: %s ; %s | guard %s/%s | count=%s step=%s" % (hex(st), at(ld), at(st),
            at(ld - 4), at(ld - 2), "ds:0x92a38c" in win, "add eax,0x2c" in win))
    ok = all(re.match(r"^mov (e?[a-z]{2,3}),dword ptr \[eax\+0x8\]$", at(ld)) and
             re.match(r"^mov dword ptr \[eax\+ebx\*4\+0xc\],(e?[a-z]{2,3})$", at(st)) and
             at(ld - 4) == "test ebx,ebx" and at(ld - 2).startswith("je ") and
             "ds:0x92a38c" in " ".join(texts(fnof(st))) and "add eax,0x2c" in " ".join(texts(fnof(st)))
             for ld, st in ((0x4f0dec, 0x4f0def), (0x5a86a7, 0x5a86aa)))
    G("M259 G1 two whole-array refresh loops copy each record's own +8 dword into record dword 3+fac, over ds:0x92a38c records with a 0x2c cursor",
      ok, " ; ".join(det))
    fold = has("FUN_004ef6d0", r"^shl eax,0x6$", r"^add eax,ebx$", r"^lea ecx,\[ebx\+eax\*2\]$",
               r"^shl ecx,0x4$", r"^sub ecx,ebx$", r"^lea eax,\[ecx\*4\+0x94dbac\]$")
    G("M259 G2 the band index IS the faction index: the same ebx folds to the 0x20bc per-faction stride (2095*4 = 8380) and fac 0 is skipped by the guard before every store",
      fold and at(0x5a8694) == "mov ebx,dword ptr [ebp+0x8]" and 2095 * 4 == 8380,
      "fold seq in FUN_004ef6d0=%s; FUN_005a7970 index = '%s' at 0x5a8694; guards at 0x4f0de8/0x5a86a3" % (fold, at(0x5a8694)))
    w5 = has("FUN_0051c750", r"^mov eax,0x94f4ec$", r"^add ecx,0x10$", r"^cmp eax,0x95da10$",
             r"^and ecx,0xffffffdf$", r"^mov dword ptr \[eax\],ecx$", r"^mov dword ptr \[ebp-0x18\],ecx$")
    ar = (0x94f4ec - 0x94d430 == 0x20bc) and (0x95da10 - 0x94f4ec == 7 * 0x20bc)
    G("M259 G3 FUN_0051c750 (the terrain-growth pass: kelp/forest/mindworm) walks the band: cursor = record+0x10 stepped by 4, paired with the per-faction block cursor [0x94f4ec,0x95da10) = factions 1..7, and its store is slot & ~0x20 | mask",
      w5 and ar, "texts=%s; 0x94f4ec-0x94d430=%s; span/0x20bc=%d; walk store at %s" % (w5, hex(0x94f4ec - 0x94d430), (0x95da10 - 0x94f4ec) // 0x20bc, seq("FUN_0051c750", r"^mov dword ptr \[eax\],ecx$")))
    mA = window("FUN_005a7970", ["mov edx,dword ptr [eax+edx*4+0xc]", "mov edi,dword ptr [eax+0x8]", "and edx,edi",
                                 "mov edi,dword ptr [eax+ecx*4+0xc]", "or edi,edx", "mov dword ptr [eax+ecx*4+0xc],edi"])
    mB = window("FUN_0053a820", ["mov ecx,dword ptr [eax+esi*4+0xc]", "mov ebx,dword ptr [eax+0x8]", "and ecx,ebx",
                                 "mov ebx,dword ptr [eax+edi*4+0xc]", "or ebx,ecx", "mov dword ptr [eax+edi*4+0xc],ebx"])
    mC = window("FUN_0053a820", ["mov ecx,dword ptr [eax+edi*4+0xc]", "mov ebx,dword ptr [eax+0x8]", "and ecx,ebx",
                                 "mov ebx,dword ptr [eax+esi*4+0xc]", "or ebx,ecx", "mov dword ptr [eax+esi*4+0xc],ebx"])
    G("M259 G4 the band is merged slot-to-slot through the master mask: read slot(A), AND it with record+8, OR the result into slot(B) - one such sequence in FUN_005a7970 and BOTH mirror directions in FUN_0053a820",
      mA and mB and mC, "FUN_005a7970=%s; FUN_0053a820 esi->edi=%s; FUN_0053a820 edi->esi=%s" % (mA, mB, mC))
    WANT = {"0x4e153b": "mov dword ptr [eax+edx*4+0xc],ebx", "0x4f0def": "mov dword ptr [eax+ebx*4+0xc],esi",
            "0x53a8d9": "mov dword ptr [eax+edi*4+0xc],ebx", "0x53a90c": "mov dword ptr [eax+esi*4+0xc],ebx",
            "0x582fec": "mov dword ptr [eax+ecx*4+0xc],edx", "0x583e1d": "mov dword ptr [ebx+ecx*4+0xc],eax",
            "0x5a3b95": "mov dword ptr [eax+esi*4+0xc],ecx", "0x5a3d3f": "mov dword ptr [ecx+eax*4+0xc],edx",
            "0x5a7afd": "mov dword ptr [eax+ecx*4+0xc],edi", "0x5a86aa": "mov dword ptr [eax+ebx*4+0xc],edx"}
    got = {}
    for (fn, kind), v in SITES.items():
        if kind == "W":
            for pc, t2, idx in v: got[pc] = t2
    G("M259 G5 the band's WRITER set is closed: the census finds exactly the 10 verified indexed stores (7 functions, each base register loaded from or lea'd from the terrain-array pointer) and nothing else, plus FUN_0051c750's pointer-walk store",
      got == WANT and len(seq("FUN_0051c750", r"^mov dword ptr \[eax\],ecx$")) == 1,
      "census writers: %s ; per-fn: %s" % (sorted(got.items()), dict(W)))
    G("M259 G6 the slot index is a VIEW field: FUN_004e14d0 loads it from [obj+0x23bd4] - inside the field block the view ctor FUN_00518820 initialises (0x23bcc..0x23bec) - after clearing bit 5 of the master mask",
      window("FUN_004e14d0", ["mov edx,dword ptr [esi+0x23bd4]", "mov ebx,dword ptr [eax+0x8]", "mov dword ptr [eax+edx*4+0xc],ebx"]) and
      has("FUN_004e14d0", r"^and edx,0xffffffdf$", r"^mov dword ptr \[eax\+0x8\],edx$") and
      has("FUN_00518820", r"^mov dword ptr \[esi\+0x23bcc\],(e?[a-z]{2,3})$", r"^mov dword ptr \[esi\+0x23bd0\],(e?[a-z]{2,3})$", r"^mov dword ptr \[esi\+0x23bec\],(e?[a-z]{2,3})$"),
      "FUN_004e14d0 index/store sequence + mask clear found; ctor fields 0x23bcc/0x23bd0/0x23bec found -> the viewed faction selects the band slot refreshed")
    G("M259 G7 the band's indexed READERS include the new-game natural-placement pass FUN_004e15c0 (3 sites), the display pass FUN_00519b00 (7) and FUN_0053a820 (4) - 20+ functions in all - and the shipped fresh map carries one value in all 7 slots of every record",
      R["FUN_004e15c0"] == 3 and R["FUN_00519b00"] == 7 and R["FUN_0053a820"] == 4 and len(R) >= 20 and
      re.search(r"planetx\.MP: slots=7 distinct=\[[^\]]*\] all7equal=8192/8192", open(os.path.join(ROOT, "evidence/m240_terrain_repack.txt")).read()),
      "readers: %s ; %d sites in %d functions ; fresh-map all-7-equal 8192/8192 (evidence/m240_terrain_repack.txt:17)" % (dict(R), sum(R.values()), len(R)))

def m260():
    tok = sum(1 for _, s in NM if "0x224b8" in s)
    byt = IMG.find(struct.pack("<I", 0x224b8))
    G("M260 G8 the live view stride 0x224b8 is not a constant in the image at all - no allocation of that size exists",
      tok == 0 and byt < 0, "immediates naming 0x224b8: %d; 4-byte LE pattern in the %d-B image: offset %d" % (tok, len(IMG), byt))
    t = [at(p) for p in (0x580392, 0x5803bb, 0x5803c0, 0x5803e1, 0x580401, 0x580406)]
    cal = collections.Counter(fnof(pc) for pc, s in NM if s == "call 0x518820")
    ini = collections.Counter(fnof(pc) for pc, s in NM if s == "call 0x580260")
    G("M260 G9 the startup init FUN_00580260 stores the STATIC address 0x8f79e0 into view slot 0, zeroes slots 1..7, then runs the view ctor FUN_00518820 exactly once on that static object",
      t == ["mov esi,0x7cded0", "mov dword ptr [esi],eax", "cmp esi,0x7cdeec", "mov dword ptr ds:0x7cdecc,0x8f79e0", "mov ecx,0x8f79e0", "call 0x518820"] and dict(cal) == {"FUN_00580260": 1},
      "texts: %s | ctor call sites: %s | init callers: %s" % (t, dict(cal), dict(ini)))
    sto = [(hex(pc), s) for pc, s in NM if M.is_store(s) and re.search(r"0x7cde(c[89a-f]|d[0-9a-f]|e[0-8])", s)]
    disp = [int(mm.group(1), 16) for s in texts("FUN_00518820") for mm in [re.search(r"\+0x([0-9a-f]{4,5})\]", s)] if mm]
    ctor_max = max(disp or [0])
    G("M260 G10 nothing else in the image stores into the table band 0x7cdec8..0x7cdee8, and the ctor's own field writes reach this+0x23bec - LARGER than the live 0x224b8 stride, so that stride is not an object size",
      [p for p, _ in sto] == ["0x5803e1"] and ctor_max > 0x224b8,
      "stores naming the band: %s; max ctor field offset %s (%d B) vs the live stride 0x224b8 (%d B)" % (sto, hex(ctor_max), ctor_max, 0x224b8))
    sh = open(os.path.join(ROOT, "ghidra_out/shard_015.c")).read().split("\n")
    leg = any("puVar18 = &DAT_007cdecc" in l for l in sh[10815:10830]) and any("*piVar12 + 0x1dd74" in l for l in sh[10840:10850])
    G("M260 G11 the save codec treats the 8 entries as POINTERS to per-view state rows and clears +0x1dd74 for slots 1..7 (never slot 0) when the resolution pair DAT_0091c18c/0091c188 changes",
      leg, "shard_015.c:10822 walks &DAT_007cdecc..<0x7cdeec calling FUN_00596620(*puVar18); :10842-10845 clears *(piVar12 + 0x1dd74) over 0x7cded0..0x7cdeec")

def m261():
    n, ins = VT[0x679f98]
    sl = [dw(0x679f98 + 4 * k) for k in range(n)]
    oth = {v: [dw(v + 4 * k) for k in range(VT[v][0])] for v in (0x6717cc, 0x671d94, 0x67164c) if v in VT}
    uniq = [k for k in range(n) if all(k >= len(v) or sl[k] != v[k] for v in oth.values())]
    G("M261 G12 vtable 0x679f98 is 88 slots with 2 installs, and EXACTLY 15 slots differ from all three dialog-family siblings",
      (n, ins) == (88, 2) and len(uniq) == 15, "slots=%d installs=%d; unique: %s" % (n, ins, [hex(4 * k) for k in uniq]))
    f = {}
    for k in uniq:
        fn = "FUN_%08x" % sl[k]; a, z = IDXMAP[fn]; b = body(fn)
        f[4 * k] = (fn, z, len(b), sum(1 for _, s in b if s.startswith("call ")), [s for _, s in b if s.startswith("ret")][:1])
    disp40 = any(re.match(r"^call (dword ptr )?\[e?[a-z]{2,3}\+0x4c\]$", s) for _, s in body("FUN_005fa7f5"))
    stubs = all(f[o][1] == 15 and f[o][3] == 0 for o in (0x60, 0x64, 0x68))
    ret8 = all(f[o][4] and f[o][4][0] == "ret 0x8" for o in (0x40, 0x44, 0x48, 0x4c, 0x50, 0x54))
    G("M261 G13 the 15 unique slots are: a 46-B dtor (+0x0, calls the 41-B dtor body FUN_0062d764), a 52-B +0x8, the 5143-B / 27-callee / 1139-insn +0x30 method with ZERO direct callers (dispatch-only), six control methods +0x40..+0x54 that all return 0x8 (+0x40 dispatches slot +0x4c), three 15-B zero-callee stubs at +0x60/+0x64/+0x68, a 21-B +0xa8, a 27-B +0xc4 and the 283-B +0x15c installer",
      f[0x0][1] == 46 and f[0x30][1] == 5143 and f[0x30][3] == 27 and f[0x30][2] == 1139 and disp40 and stubs and ret8 and f[0x15c][1] == 283,
      " ".join("+0x%x:%s %dB/%dcalls %s" % (o, f[o][0], f[o][1], f[o][3], f[o][4][0]) for o in sorted(f)))
    c1 = collections.Counter(fnof(pc) for pc, s in NM if s == "call 0x62d630")
    c2 = collections.Counter(fnof(pc) for pc, s in NM if s == "call 0x62d764" and not fnof(pc).startswith("Unwind@"))
    s1 = any("Start a new session or..." in x for x in strs("FUN_00636b1e", 40))
    s2 = any("Gamma Correction" in x for x in strs("FUN_00493a10", 40))
    G("M261 G14 the screens that construct the class: FUN_0062d630 is called only by FUN_0045a8b0(1)/FUN_005b3000(2)/FUN_00641f3c(3); FUN_0062d764 by FUN_00636b1e(15)/FUN_0063a770(3)/FUN_00456670(2)/FUN_00493a10(2)/FUN_0045a840(1)/FUN_0062ecc0(1); FUN_00636b1e is the session-chooser dialog and FUN_00493a10 the graphics-options screen",
      dict(c1) == {"FUN_0045a8b0": 1, "FUN_005b3000": 2, "FUN_00641f3c": 3} and
      dict(c2) == {"FUN_00456670": 2, "FUN_0045a840": 1, "FUN_00493a10": 2, "FUN_0062ecc0": 1, "FUN_00636b1e": 15, "FUN_0063a770": 3} and s1 and s2,
      "ctor1 callers %s ; ctor2 callers %s ; session-chooser=%s gamma=%s" % (dict(c1), dict(c2), s1, s2))

def main():
    print("# SMAC M259-M261 | terran.exe static image %d B, corpus %d insns, %d indexed functions" % (len(IMG), len(NM), len(IDXMAP)))
    m259(); m260(); m261()
    npass = sum(1 for d, ok, n in GATES if ok)
    for d, ok, n in GATES:
        print(("PASS " if ok else "FAIL ") + d)
        print("    " + str(n))
    print("SUMMARY M259/M260/M261: %d/%d gates PASS" % (npass, len(GATES)))
    return 0 if npass == len(GATES) else 1

if __name__ == "__main__":
    sys.exit(main())
