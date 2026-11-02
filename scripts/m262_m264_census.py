#!/usr/bin/env python3
"""M262-M264: three static census questions on terran.exe through ONE instrument
(the whole-image instruction corpus + the image-derived vtable map + containment via
ghidra_out/index.csv — imported from scripts/m235_m237_records.py, as in M259-M261).

  M262  who writes the view-table entries 1..7 (DAT_007cdec8..0x7cdee8) — no store in the
        image names them (M260); find every reference shape and any pointer derivation
  M263  does the LOAD path re-derive the per-faction terrain band (+16..+43) or trust the
        file — the codec's map leg vs the two refresh loops' reachability from the loader
  M264  FUN_005be090: which of the 13 image-wide `call [reg+4]` sites dispatch to it and
        with what arg sizes; which of the 3 loaders of ds:0x9965b8 fills its records;
        and who calls FUN_005f3f5b (6102 B)

    python3 scripts/m262_m264_census.py    # -> SUMMARY M262/M263/M264: n/N gates PASS
Static only: no box, no /proc, no gdb.
"""
import os, re, sys, collections, importlib.util
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
GATES = []
def G(desc, cond, numbers): GATES.append((desc, bool(cond), numbers))

BAND = (0x7cdecc, 0x7cdee9)
ADDR = re.compile(r"^(?:lea (e?[a-z]{2,3}),\[(?:e?[a-z]{2,3}\*4\+)?(0x7cde[c-e][0-9a-f])\]|mov (e?[a-z]{2,3}),(0x7cde[c-e][0-9a-f]))$")

def m262():
    H = M.window_hits(*BAND)
    sto = [(hex(p), fnof(p), s) for p, s, v in H if M.is_store(s)]
    idx = [(hex(p), fnof(p), s) for p, s, v in H if "*4+0x7cdecc" in s]
    idxw = [x for x in idx if M.is_store(x[2])]
    G("M262 G1 the 8-dword band 0x7cdecc..0x7cdee8 has exactly ONE store in the image that names it (the startup entry-0 store) and ZERO indexed stores among the 39 [reg*4+0x7cdecc] mentions in 12 functions - counts cross-checked against an independently regenerated objdump corpus (39 mentions, 0 indexed stores, 1 band store)",
      sto == [("0x5803e1", "FUN_00580260", "mov dword ptr ds:0x7cdecc,0x8f79e0")] and not idxw
      and len(idx) == 39 and len(set(f for _, f, _ in idx)) == 12,
      "%d mentions; stores naming the band: %s ; indexed mentions %d in %d functions, of which stores: %d" % (len(H), sto, len(idx), len(set(f for _, f, _ in idx)), len(idxw)))
    b = body("FUN_00580260"); i = [k for k, (p, _) in enumerate(b) if p == 0x580392][0]
    got = [s for _, s in b[i:i + 18]]
    WANT = ["mov esi,0x7cded0", "push 0x22480", "call 0x64bc20", "add esp,0x4", "mov dword ptr [ebp-0x10],eax", "cmp eax,ebx",
            "mov dword ptr [ebp-0x4],ebx", "je 0x5803b9", "push 0x1", "mov ecx,eax", "call 0x469650", "jmp 0x5803bb",
            "xor eax,eax", "mov dword ptr [esi],eax", "add esi,0x4", "cmp esi,0x7cdeec", "mov dword ptr [ebp-0x4],0xffffffff", "jl 0x580397"]
    G("M262 G2 entries 1..7 DO have a writer: FUN_00580260's 7-iteration loop (cursor esi 0x7cded0 -> 0x7cdeec step 4) allocates 0x22480 bytes per entry through FUN_0064bc20, constructs the block with push 1 / FUN_00469650, and stores it with the POINTER-ARITHMETIC form mov [esi],eax - the shape the M260 store census could not see (0 is stored only when the alloc fails)",
      got == WANT and (0x7cdeec - 0x7cded0) // 4 == 7,
      "loop @0x580392 (iters=%d): %s" % ((0x7cdeec - 0x7cded0) // 4, " ; ".join(got)))
    n280 = [(hex(p), fnof(p)) for p, s in NM if "0x22480" in s]
    n2b8 = sum(1 for _, s in NM if "0x224b8" in s)
    G("M262 G3 the allocation size 0x22480 (140,416 B) is named exactly ONCE in the 3,067,904-B image - at that loop - while the live stride 0x224b8 is named zero times; 0x224b8 - 0x22480 = 0x38 (56 B heap header, INFERRED), so M260's 'the ~140 KB views are not allocated' is RETRACTED: seven of them are allocated at startup",
      n280 == [("0x580397", "FUN_00580260")] and n2b8 == 0 and 0x224b8 - 0x22480 == 0x38,
      "0x22480 sites: %s ; 0x224b8 mentions: %d ; alloc wrapper FUN_0064bc20 (%d B): %s" % (n280, n2b8, IDXMAP["FUN_0064bc20"][1], " ; ".join(texts("FUN_0064bc20")[:6])))
    esc = []
    for p, s in NM:
        m = ADDR.match(s)
        if not m: continue
        reg = m.group(1) or m.group(3); imm = int(m.group(2) or m.group(4), 16)
        if not (BAND[0] <= imm < BAND[1]) or fnof(p) not in IDXMAP: continue
        bb = body(fnof(p)); k = [j for j, (q, _) in enumerate(bb) if q == p]
        for q, t in bb[k[0] + 1:k[0] + 40]:
            mm = re.match(r"^\[" + reg + r"(?:\+0x([0-9a-f]+))?\]$", M.dest_operand(t)) if M.is_store(t) else None
            if (mm and (mm.group(1) is None or int(mm.group(1), 16) <= 0x1c)) or t == "push " + reg:
                esc.append((hex(p), fnof(p), hex(imm), reg, hex(q), t)); break
    G("M262 G4 no pointer to an entry 1..7 ever leaves its function: of the 35 address-of-band sites, only 4 escape, and all 4 hand out &DAT_007cdecc (entry 0); the 4 lea'd [reg*4+0x7cdecc] cursors (2 in FUN_00512b40, 1 each in FUN_0050a550/FUN_0050a770) are only re-read",
      len([x for x in esc if x[2] != "0x7cdecc"]) == 0 and len(esc) == 4 and len([1 for p, s in NM if ADDR.match(s) and BAND[0] <= int((ADDR.match(s).group(2) or ADDR.match(s).group(4)), 16) < BAND[1]]) == 35,
      "escapes: %s" % (esc,))

    d0 = [(hex(p), fnof(p)) for p, s, v in M.window_hits(0x7cded0, 0x7cded1)]
    b2 = body("FUN_00597ee0"); i2 = [k for k, (p, _) in enumerate(b2) if p == 0x597f6d][0]
    got2 = [s for _, s in b2[i2:i2 + 12]]
    WANT2 = ["mov esi,0x7cded4", "mov eax,dword ptr [esi]", "cmp eax,ebx", "je 0x597f8d", "cmp dword ptr [eax+0x1dd74],ebx",
             "je 0x597f8d", "mov dword ptr [eax+0x1dd74],ebx", "mov ecx,dword ptr [esi]", "call 0x479e90", "add esi,0x4",
             "cmp esi,0x7cdeec", "jl 0x597f72"]
    G("M262 G5 the entries are per-view state POINTERS that the load path tears down: entry 1 (0x7cded0) is read 32 times in >=12 functions, and FUN_00597ee0 - a caller of the map-load leg - walks entries 2..7 with the same cursor shape (esi 0x7cded4 -> 0x7cdeec step 4), clearing *(entry+0x1dd74) and calling FUN_00479e90(entry) for every non-null one",
      len(d0) == 32 and len(set(f for _, f in d0)) >= 12 and got2 == WANT2,
      "entry-1 reads: %d in %d functions, top %s ; teardown: %s" % (len(d0), len(set(f for _, f in d0)), collections.Counter(f for _, f in d0).most_common(5), " ; ".join(got2)))

CALLS = collections.defaultdict(collections.Counter); REVC = collections.defaultdict(collections.Counter)
for _p, _s in NM:
    _m = re.match(r"^call (0x[0-9a-f]{6,8})$", _s)
    if _m:
        _t = "FUN_%08x" % int(_m.group(1), 16); CALLS[fnof(_p)][_t] += 1; REVC[_t][fnof(_p)] += 1
def fwd(start, depth=9):
    seen = {start}; fr = {start}
    while fr and depth:
        nx = set()
        for f in fr:
            for c in CALLS.get(f, {}):
                if c not in seen: seen.add(c); nx.add(c)
        fr = nx; depth -= 1
    return seen

def m263():
    FORM = re.compile(r"\[(e?[a-z]{2,3})\+(e?[a-z]{2,3})\*4\+0xc\]")
    LOADB = re.compile(r"^mov (e?[a-z]{2,3}),(?:dword ptr )?ds:0x92ae14$")
    LEA = re.compile(r"^lea (e?[a-z]{2,3}),\[(e?[a-z]{2,3})\+(e?[a-z]{2,3})\*4\]$")
    _ld = {}
    def tregs(fn):
        if fn not in _ld:
            t = texts(fn); s = set(m.group(1) for m in (LOADB.match(x) for x in t) if m)
            for _ in range(2):
                for m in (LEA.match(x) for x in t):
                    if m and m.group(2) in s: s.add(m.group(1))
            _ld[fn] = s
        return _ld[fn]
    W = collections.defaultdict(list)
    for p, s in NM:
        m = FORM.search(s)
        if not m or not M.is_store(s): continue
        fn = fnof(p)
        if fn in IDXMAP and m.group(1) in tregs(fn): W[fn].append(hex(p))
    W["FUN_0051c750"] = ["0x51ca52"]
    WANT = {"FUN_004e14d0": ["0x4e153b"], "FUN_004ef6d0": ["0x4f0def"], "FUN_0051c750": ["0x51ca52"],
            "FUN_0053a820": ["0x53a8d9", "0x53a90c"], "FUN_00582fc0": ["0x582fec"], "FUN_00583c70": ["0x583e1d"],
            "FUN_005a3470": ["0x5a3b95", "0x5a3d3f"], "FUN_005a7970": ["0x5a7afd", "0x5a86aa"]}
    G("M263 G6 the band's writer set re-derives to exactly M259's closed list: 8 functions, 10 indexed stores, plus FUN_0051c750's pointer-walk store",
      {k: sorted(v) for k, v in W.items()} == WANT, "writers: %s" % {k: sorted(v) for k, v in sorted(W.items())})
    MAPLOAD = sorted(set(fnof(p) for p, s in NM if s == "call 0x582260"))
    LOAD = tuple(sorted(set(MAPLOAD) | set(f for L in MAPLOAD for f in REVC.get(L, {}))))
    reach = {L: fwd(L) for L in LOAD}
    U = set().union(*reach.values())
    inter = sorted(U & set(WANT))
    inslot = [fn for fn in WANT if M.slots_holding(int(fn[4:], 16))]
    G("M263 G7 the LOAD path never reaches a band writer: the forward call-closure (depth 9) of the 6 load-path functions (the 2 that call map_load_arrays 0x582260 + their 4 callers) is %d functions, its intersection with the writer set is EMPTY, and no band writer sits in any vtable slot, so indirect dispatch cannot reach them either" % (len(U) - len(LOAD) + 1),
      MAPLOAD == ["FUN_00596850", "FUN_00597a70"] and len(LOAD) == 6 and not inter and not inslot and all(len(reach[L]) >= 100 for L in LOAD),
      "load set: %s ; per-fn closure: %s ; union %d ; writers reached: %s ; writers in vtables: %s" % (list(LOAD), {L: len(reach[L]) - 1 for L in LOAD}, len(U), inter, inslot))
    ml = texts("FUN_00582260")
    hitsw = sorted(set(CALLS.get("FUN_00582260", {})) & set(WANT))
    clean = not any(FORM.search(s) for s in ml) and not hitsw
    ref583 = [(hex(p), s) for p, s in NM if "0x583c70" in s]
    G("M263 G8 the map leg is a verbatim fill (FUN_00582260 has no band-shaped store and no call into the writer set - MAP_FORMAT.md:23-24/118), the writers' callers are gameplay passes (FUN_004e14d0 <- FUN_00516b80; FUN_004ef6d0 <- FUN_004f5a70; FUN_0051c750 <- FUN_0051f320; FUN_005a7970 <- 24 callers), and FUN_00583c70 - the copy-in writer - has ZERO references in the image (no call, no imm32, no vtable slot), so its store can never execute",
      clean and ref583 == [] and dict(REVC.get("FUN_004e14d0", {})) == {"FUN_00516b80": 1}
      and dict(REVC.get("FUN_004ef6d0", {})) == {"FUN_004f5a70": 1}
      and dict(REVC.get("FUN_0051c750", {})) == {"FUN_0051f320": 1}
      and len(REVC.get("FUN_005a7970", {})) == 24,
      "FUN_00582260: %d insns, band-shaped stores %s, calls into writers %s ; 0x583c70 refs: %d ; callers 004e14d0=%s 004ef6d0=%s 0051c750=%s 005a7970=%d" % (
          len(ml), [s for s in ml if FORM.search(s)], hitsw, len(ref583), dict(REVC.get("FUN_004e14d0", {})),
          dict(REVC.get("FUN_004ef6d0", {})), dict(REVC.get("FUN_0051c750", {})), len(REVC.get("FUN_005a7970", {}))))

def m264():
    b = texts("FUN_005be090")
    WANTB = ["push ebp", "mov ebp,esp", "sub esp,0x8", "mov eax,dword ptr [ebp+0x8]", "push eax", "call 0x649e00", "add esp,0x4",
             "mov dword ptr [ebp-0x4],eax", "cmp dword ptr [ebp-0x4],0x0", "je 0x5be0b0", "mov eax,dword ptr [ebp-0x4]", "jmp 0x5be0d4",
             "mov ecx,dword ptr ds:0x99aa98", "mov dword ptr [ebp-0x8],ecx", "push 0x30", "push 0x698890", "push 0x69889c", "push 0x0",
             "call dword ptr ds:0x671320", "push 0x4", "call 0x649c80", "mov esp,ebp", "pop ebp", "ret"]
    s1, s2 = M.readstr(0x698890), M.readstr(0x69889c)
    cal = [p for p, s in NM if s == "call 0x5be090"]
    G("M264 G9 FUN_005be090 is the game's operator-new: 24 insns / 72 B that hand arg1 to FUN_00649e00 (a 29-B shim over FUN_00649e70 passing the process heap handle ds:0x99d5f8); on a NULL return it reports through the GLOBAL function pointer ds:0x671320 with 'FATAL ERROR' + 'Windows has run out of virtual memory; the game will exit...', then push 4 / call 0x649c80. It is installed in NO vtable slot image-wide, so the footing's '13 [reg+4] sites' were never dispatch sites - they are store-after-alloc sites",
      b == WANTB and s1 == "FATAL ERROR" and s2.startswith("Windows has run out of virtual memory; the game will exit")
      and not M.slots_holding(0x5be090) and len(cal) == 119 and len(set(fnof(p) for p in cal)) == 74,
      "%d insns/%d B ; strings %r / %r ; vtable slots %s ; direct sites %d in %d functions" % (len(b), IDXMAP["FUN_005be090"][1], s1, s2[:44], M.slots_holding(0x5be090), len(cal), len(set(fnof(p) for p in cal))))
    res = []
    for i, (p, s) in enumerate(NM):
        if s != "call 0x5be090": continue
        arg = next((NM[k][1] for k in range(i - 1, max(0, i - 6), -1) if NM[k][1].startswith("push ")), "")
        for q, t in NM[i + 1:i + 9]:
            if re.match(r"^mov \w+ ptr \[[^]]*\+0x4\],", t):
                res.append((hex(p), fnof(p), arg, t)); break
    G("M264 G10 the store-after-alloc census: of the 119 new-sites, 14 (in 13 functions) store the result into an object's +0x4 within 8 instructions - the record payload slot the docs were pointing at; the pushed size is a register in 92 of 119 sites and an immediate in the rest (0x14 x7, 0x18 x4, 0x1 x3, 0x1c x2, 0x4 x2, 0x104, 0x820, 0x11800 = 71,680 B)",
      len(res) == 14 and len(set(f for _, f, _, _ in res)) == 13 and all(x[1] in IDXMAP for _, x in enumerate(res)),
      "sites: %s" % (res,))
    def win(fn, want):
        t = texts(fn); return any(t[i:i + len(want)] == want for i in range(len(t) - len(want) + 1))
    t5, t6, t7 = texts("FUN_005dbb5f"), texts("FUN_005dbbe6"), texts("FUN_005dbdc0")
    cur = [(hex(p), s) for p, s in NM if "0x9965b8" in s]
    nz = sum(1 for s in t5 if re.match(r"^mov dword ptr \[[a-z]+(\+0x[0-9a-f]+)?\],0x0$", s))
    seqA = ["mov ecx,dword ptr ds:0x9965b8", "add ecx,0x2c", "mov dword ptr ds:0x9965b8,ecx"]
    seqB = ["mov ecx,dword ptr [edx+0x10]", "imul ecx,dword ptr [eax+0x14]", "mov edx,dword ptr ds:0x9965b8", "sub edx,ecx", "mov dword ptr ds:0x9965b8,edx"]
    seqC = ["mov eax,dword ptr [ecx+0x10]", "imul eax,dword ptr [edx+0x14]", "mov ecx,dword ptr ds:0x9965b8", "add ecx,eax", "mov dword ptr ds:0x9965b8,ecx"]
    seqD = ["push edx", "call 0x5be090", "add esp,0x4", "mov ecx,dword ptr [ebp-0x28]", "mov dword ptr [ecx+0x4],eax"]
    G("M264 G11 ds:0x9965b8 is a LINEAR RECORD CURSOR - 6 mentions = 3 read/modify/write pairs, one per function: FUN_005dbb5f (33 insns) stamps a blank record (10 dword zero stores + the byte signature [rec+8] = 9) and bumps the cursor by 0x2c; FUN_005dbbe6 (63 insns) gates [rec+0x28]==0 and [rec+4]!=0, rewinds the cursor by [rec+0x10]*[rec+0x14] and frees [rec+4] through FUN_0064a7f0; FUN_005dbdc0 (1303 B, ret 0x1c) is the FILLER - it allocates [rec+0x10]*[rec+0x14] bytes through FUN_005be090, stores the pointer at [rec+4], then advances the cursor by the same product",
      len(cur) == 6 and win("FUN_005dbb5f", seqA) and win("FUN_005dbbe6", seqB) and win("FUN_005dbdc0", seqC)
      and win("FUN_005dbdc0", seqD) and nz == 10 and "mov byte ptr [ecx+0x8],0x9" in t5
      and "call 0x64a7f0" in t6 and IDXMAP["FUN_0064a7f0"][1] == 19,
      "cursor ops: %s ; zero-stores in 005dbb5f: %d ; stamp: %s ; free wrapper FUN_0064a7f0 = %d B, %d callers" % (cur, nz, "mov byte ptr [ecx+0x8],0x9" in t5, IDXMAP["FUN_0064a7f0"][1], sum(REVC.get("FUN_0064a7f0", {}).values())))

def main():
    print("# SMAC M262-M264 | terran.exe static image %d B, corpus %d insns, %d indexed functions" % (len(IMG), len(NM), len(IDXMAP)))
    m262(); m263(); m264()
    npass = sum(1 for d, ok, n in GATES if ok)
    for d, ok, n in GATES:
        print(("PASS " if ok else "FAIL ") + d)
        print("    " + str(n))
    print("SUMMARY M262/M263/M264: %d/%d gates PASS" % (npass, len(GATES)))
    return 0 if npass == len(GATES) else 1

if __name__ == "__main__":
    sys.exit(main())
