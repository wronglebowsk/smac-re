#!/usr/bin/env python3
"""M227-M230: the hotspot list's address-takes (and the stack-mirror that hides them), what
gets installed in the panel's tail field +0x2144, the [obj+0xb24] page field and the 0x774c38
grid, and FUN_00455c70's registrar trampoline.

  python3 scripts/m227_m230_mirrors.py > evidence/m227_m230_mirrors.txt

Static only: scratch/m574/text.txt + programs/terran.exe + ghidra_out/index.csv. No box time.
Every number the prose quotes is COMPUTED here.
"""
import bisect, collections, importlib.util, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
_spec = importlib.util.spec_from_file_location("fc", os.path.join(HERE, "field_census.py"))
FC = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(FC)
INS, fnof, IDX = FC.INS, FC.fnof, FC.IDX
IMG = open(os.path.join(ROOT, "programs/terran.exe"), "rb").read()
NM = [(pc, " ".join(s.lower().split())) for pc, s in INS]
PCS = [pc for pc, _ in NM]; POS = {pc: i for i, pc in enumerate(PCS)}
IDXMAP = {n: (a, z) for a, n, z in IDX}
TEXT_LO, TEXT_HI = 0x401000, 0x660000
DATA_LO, DATA_HI = 0x660000, 0x9a0000
FILEMAP_END = 0x6ec8c0
ADDERS = (0x5e774d, 0x403b00)          # the only item writer and the only wrapper (M217/M222)


def dw(va):
    o = va - 0x400000
    return struct.unpack("<I", IMG[o:o + 4])[0] if 0 <= o < len(IMG) - 3 else 0


def in_text(v):
    return TEXT_LO <= v < TEXT_HI


def body(fn):
    a, z = IDXMAP[fn]
    return NM[bisect.bisect_left(PCS, a):bisect.bisect_left(PCS, a + z)]


def nxt(pc, n=12):
    i = POS[pc]; return NM[i + 1:i + 1 + n]


# ---- vtables (the m217 machinery, needed only for the +0x2144 callers' slots)
bases = collections.Counter(); INSTALLS = collections.defaultdict(list)
RX_INS = re.compile(r"^mov dword ptr \[([^\]]*)\],(0x[0-9a-f]{6,8})$")
for pc, s in NM:
    m = RX_INS.match(s)
    if not m: continue
    v = int(m.group(2), 16)
    if DATA_LO <= v < DATA_HI and in_text(dw(v)):
        bases[v] += 1; INSTALLS[v].append((pc, fnof(pc), m.group(1)))
B = sorted(bases); VT = {}
for i, b in enumerate(B):
    nx = B[i + 1] if i + 1 < len(B) else b + 0x4000
    n = 0
    while 4 * (n + 1) <= (nx - b) and in_text(dw(b + 4 * (n + 1))):
        n += 1
    VT[b] = (n + 1, bases[b])


def vt_of(addr):
    k = bisect.bisect_right(B, addr) - 1
    if k < 0: return None
    b = B[k]
    return (b, addr - b) if addr < b + 4 * VT[b][0] else None


def slots_of(fnaddr):
    pat = struct.pack("<I", fnaddr); i, out = 0, []
    while True:
        j = IMG.find(pat, i)
        if j < 0: break
        i = j + 1; ad = j + 0x400000
        if DATA_LO <= ad < DATA_HI:
            v = vt_of(ad)
            if v: out.append(v)
    return out


RESULTS = collections.OrderedDict()
def G(ok, desc, cond, numbers): ok.append((desc, bool(cond), numbers))
def report(tag):
    ok = RESULTS[tag]
    for desc, cond, numbers in ok:
        print("  [%s] %s" % ("PASS" if cond else "FAIL", desc))
        for line in numbers: print("        %s" % line)
    print("  -> %s %s (%d/%d gates)" % (tag, "PASS" if all(c for _, c, _ in ok) else "FAIL",
                                        sum(1 for _, c, _ in ok if c), len(ok)))


# ================================================== M227  the hotspot list at this+0x3098
def m227():
    ok = RESULTS["M227"] = []
    refs = [(pc, s, fnof(pc)) for pc, s in NM if re.search(r"\b0x3098\b", s)]
    mem = [x for x in refs if "ebp-0x3098" not in x[1]]
    stk = [x for x in refs if "ebp-0x3098" in x[1]]
    G(ok, "the token 0x3098 appears in %d instructions image-wide: %d MEMBER forms "
          "(`[reg+0x3098]` / `lea reg,[X+0x3098]` / `add reg,0x3098`) and %d FRAME-SLOT forms "
          "`[ebp-0x3098]`; a displacement-only census conflates the two" % (len(refs), len(mem), len(stk)),
      len(refs) == 18 and len(mem) == 8 and len(stk) == 10,
      ["member=%s" % [(hex(p), f, s) for p, s, f in mem],
       "frame=%s" % [(hex(p), f) for p, _, f in stk]])
    mir = []
    for fn in ("FUN_0058dfd0", "FUN_0058e2b0"):
        b = body(fn)
        mir.append((fn, sum(1 for _, s in b if s == "mov dword ptr [ebp-0x3098],0x671d94"),
                    sum(1 for _, s in b if s == "mov dword ptr [ebp-0x62c8],0x6717cc"),
                    sum(1 for _, s in b if s == "lea ecx,[ebp-0x3230]"),
                    sum(1 for _, s in b if s == "call 0x5e7665"),
                    sum(1 for _, s in b if s == "call 0x405ef0")))
    ar = (-0x62c8 + 0x3230 == -0x3098) and (-0x62c8 + 0x3098 == -0x3230)
    G(ok, "the frame slots ARE the same two members seen through a stack base: %s each store the "
          "PANEL vtable 0x671d94 at [ebp-0x3098] and the DIALOG vtable 0x6717cc at [ebp-0x62c8] and "
          "call the dialog ctor FUN_00405ef0 - so dialog_base = ebp-0x62c8, dialog_base+0x3230 = "
          "ebp-0x3098 (the panel, M221) and dialog_base+0x3098 = ebp-0x3230 (THE LIST, arithmetic "
          "%s), where each frame takes its address once and clears it" % ([m[0] for m in mir], ar),
      ar and all(m[1] == 1 and m[2] == 1 and m[3] == 1 and m[4] == 1 and m[5] == 1 for m in mir),
      ["per-frame (panelvt, dialogvt, list-take, clear, dialog-ctor)=%s" % mir])
    calls = []
    for pc, s, f in mem:
        t = [(x, hex(p)) for p, x in nxt(pc, 12) if re.match(r"^(call|jmp) 0x[0-9a-f]+$", x)]
        calls.append((hex(pc), f, t[0][0] if t else None))
    tgt = [c[2] for c in calls]
    cnt = collections.Counter(tgt)
    G(ok, "all %d member-form takes hand the list to a callee inside the container block "
          "0x5e7600-0x5e7a00 (%s) and NONE reaches an appender (%s are the only item writers "
          "image-wide, M217/M222): the dialog's 10-item list is allocated, cleared, reset and "
          "scanned and NEVER appended, so the +0x4c dispatcher M214 installs 466x scans an empty "
          "list unless something outside the image appends" % (len(mem), dict(cnt), [hex(a) for a in ADDERS]),
      len(tgt) == 8 and all(t and 0x5e7600 <= int(t.split(" ")[1], 16) < 0x5e7a00 for t in tgt)
      and not any(t and int(t.split(" ")[1], 16) in ADDERS for t in tgt),
      ["take->target=%s" % calls])
    report("M227")


# ========================================================= M228  the panel tail field +0x2144
def m228():
    ok = RESULTS["M228"] = []
    refs = [(pc, s, fnof(pc)) for pc, s in NM if "+0x2144]" in s]
    st = [x for x in refs if re.match(r"^mov dword ptr \[[a-z]+\+0x2144\],", x[1])]
    z = [x for x in st if x[1].endswith(",0x0")]
    sn = [x for x in st if x[1].endswith(",0xffffffff")]
    rg = [x for x in st if x not in z and x not in sn]
    tx = [(hex(p), s) for p, s, _ in st
          for m in [re.match(r"^mov dword ptr \[[a-z]+\+0x2144\],(0x[0-9a-f]+)$", s)] if m and TEXT_LO <= int(m.group(1), 16) < TEXT_HI]
    G(ok, "+0x2144 has %d references and %d stores: %d store 0 (the ctors), %d store the sentinel "
          "0xffffffff, %d store a register - and %d stores carry a TEXT-range immediate, so NOTHING "
          "in the image installs a function address in this field" % (len(refs), len(st), len(z), len(sn), len(rg), len(tx)),
      len(refs) == 54 and len(st) == 24 and len(z) == 10 and len(sn) == 3 and len(rg) == 11 and not tx,
      ["zero=%s" % [hex(p) for p, _, _ in z], "sentinel=%s" % [hex(p) for p, _, _ in sn],
       "register=%s" % [hex(p) for p, _, _ in rg], "text-immediates=%s" % tx])
    cls = collections.Counter(); det = []
    for pc, s, f in rg:
        src = re.match(r"^mov dword ptr \[[a-z]+\+0x2144\],(e?[a-z]{2})$", s).group(1)
        pre = [x for p, x in body(f) if p < pc][-60:]
        lw = [x for x in pre if re.match(r"^(mov|lea|xor) %s," % src, x)]
        last = lw[-1] if lw else "UNRESOLVED"
        if "ebp" in last: k = "frame-slot"
        elif re.match(r"^mov %s,dword ptr \[e[a-z]{2}\*4\+0x6[0-9a-f]{5}\]$" % src, last): k = ".rdata table load"
        elif re.match(r"^lea %s,\[e?[a-z]{2}\*4\+0x7[0-9a-f]{5}\]$" % src, last): k = "BSS table-slot lea"
        else: k = "UNRESOLVED"
        cls[k] += 1; det.append((hex(pc), f, last))
    G(ok, "the %d register stores' provenance (last write to the source register within 60 insns): "
          "%s - a caller's frame slot, one load out of the .rdata table at 0x689f88 and two `lea` of "
          "a slot in the runtime table at 0x7543d8; %d unresolved and 0 function addresses, so the "
          "field holds a POINTER TO a block its installer owns, not the callback itself"
          % (len(rg), dict(cls), cls["UNRESOLVED"]),
      cls["frame-slot"] == 8 and cls[".rdata table load"] == 1 and cls["BSS table-slot lea"] == 2
      and not cls["UNRESOLVED"], ["provenance=%s" % det])
    cal = collections.defaultdict(list); gua = collections.defaultdict(list)
    for pc, s, f in refs:
        if s.startswith("call dword ptr [") and s.endswith("+0x2144]"): cal[f].append(hex(pc))
        if s.startswith("cmp dword ptr [") and s.endswith("+0x2144],0x0"): gua[f].append(hex(pc))
    sl = {f: [(hex(a), hex(o)) for a, o in slots_of(int("0x" + f[4:], 16))] for f in sorted(cal)}
    inv = [(f, sum(1 for p, x in body(f) if re.match(r"^mov e[a-z]{2},dword ptr \[[a-z]+\+0x2144\]$", x)))
           for _, _, f in sn]
    G(ok, "exactly %d functions call through it (%d calls, %d `cmp [reg+0x2144],0x0` guards in those "
          "same functions): %s (slots %s). The %d sentinel stores are read-and-invalidate: each of "
          "those functions also LOADS the field (%s)" % (len(cal), sum(len(v) for v in cal.values()),
          sum(len(gua[f]) for f in cal), sorted(cal), sl, len(sn), inv),
      len(cal) == 3 and sum(len(v) for v in cal.values()) == 6 and all(gua[f] for f in cal)
      and all(n >= 1 for _, n in inv),
      ["callers=%s" % dict(cal), "guards=%s" % {k: len(v) for k, v in gua.items()}, "slots=%s" % sl])
    report("M228")


# ================================================= M229  the [obj+0xb24] page field / grid
def m229():
    ok = RESULTS["M229"] = []
    refs = [(pc, s, fnof(pc)) for pc, s in NM if "+0xb24]" in s]
    st = [x for x in refs if x[1].startswith("mov dword ptr [")]
    ld = [x for x in refs if re.match(r"^mov e[a-z]{2},dword ptr \[", x[1])]
    ts = [x for x in refs if x[1].startswith("cmp ")]
    wf, lf = sorted(set(x[2] for x in st)), sorted(set(x[2] for x in ld))
    G(ok, "[obj+0xb24] has %d references: %d stores in %d functions, %d loads in %d functions, %d "
          "test. RETRACTS M224's \"9 other functions load [obj+0xb24]\": the loaders are %s"
          % (len(refs), len(st), len(wf), len(ld), len(lf), len(ts), lf),
      len(refs) == 25 and len(st) == 12 and len(wf) == 6 and len(ld) == 12 and len(lf) == 5 and len(ts) == 1,
      ["writers=%s" % sorted(collections.Counter(x[2] for x in st).items()),
       "loaders=%s" % sorted(collections.Counter(x[2] for x in ld).items()),
       "test=%s" % [(hex(p), s) for p, s, _ in ts]])
    reg = {f: len([1 for _, s in body(f) if re.search(r"\b0x77[0-9a-f]{3}\b", s)]) for f in lf}
    disp = []
    for pc, s, f in ld:
        r = re.match(r"^mov (e[a-z]{2}),dword ptr \[", s).group(1)
        w = nxt(pc, 12)
        idx = any(re.search(r"\*4\+0x7543d8", x) for _, x in w)
        pus = any(x == "push %s" % r for _, x in w)
        cmp_ = any(re.match(r"^cmp %s,0x" % r, x) for _, x in w)
        disp.append((hex(pc), f, "index-into-0x7543d8" if idx else ("pushed-as-arg" if pus else
                     ("compared" if cmp_ else "other"))))
    c2 = collections.Counter(k for _, _, k in disp)
    G(ok, "no loader walks the grid: the %d loader functions reference the 0x774xxx region %d times "
          "in total (%s), and of the %d loads %d are indexed into the 0x2c-stride table at 0x7543d8 "
          "(`lea X,[X+X*4]; lea X,[X+Y*2]; lea X,[X*4+0x7543d8]` = index*44), %d are pushed to a "
          "callee, %d compared, %d other - so the field carries a SLOT INDEX for these owners while "
          "FUN_0041f450 stores a PAGE ADDRESS in the same displacement: a displacement collision, not "
          "one field" % (len(lf), sum(reg.values()), reg, len(ld), c2["index-into-0x7543d8"],
                         c2["pushed-as-arg"], c2["compared"], c2["other"]),
      sum(reg.values()) == 0 and c2["index-into-0x7543d8"] == 1,
      ["dispositions=%s" % disp])
    b = body("FUN_0041f450")
    ins = [(hex(p), s) for p, s in b if re.match(r"^mov dword ptr \[[a-z]+\+0xb24\],", s)]
    cnt = collections.Counter(m.group(1) for _, s in ins for m in [re.search(r",(0x[0-9a-f]+)$", s)] if m)
    grid = 0x774c38; goff = grid - 0x400000
    zero = all(dw(grid + 4 * i) == 0 for i in range(99))
    G(ok, "FUN_0041f450's %d stores to the field are %s: 0x774c0c = grid base - 0x2c (one entry "
          "BELOW the first entry any setter receives) and 0x774a80 = grid base - 9*0x2c; the grid "
          "0x774c38..0x774dcc (9 x 0x2c = 99 dwords) sits at file offset 0x%x > len(terran.exe) "
          "0x%x, i.e. it has NO file contents (BSS) and reads 0 (%s) - runtime-filled state, reached "
          "through this field" % (len(ins), dict(cnt), goff, len(IMG), zero),
      len(ins) == 5 and dict(cnt) == {"0x774c0c": 4, "0x774a80": 1} and grid - 0x774c0c == 0x2c
      and 0x774c0c - 0x774a80 == 9 * 0x2c and goff > len(IMG) and zero,
      ["stores=%s" % ins, "grid-base-offset=0x%x file-len=0x%x all-99-dwords-zero=%s" % (goff, len(IMG), zero)])
    report("M229")


# ============================================== M230  FUN_00455c70's registrar trampoline
def m230():
    ok = RESULTS["M230"] = []
    b = body("FUN_00455c70")
    cl = collections.Counter(m.group(1) for _, s in b for m in [re.match(r"^call (0x[0-9a-f]+)$", s)] if m)
    st = [x for x in b if re.match(r"^mov (?:dword ptr )?\[", x[1])]
    imm = collections.Counter(m.group(1) for _, s in b for m in [re.search(r"^push (0x[0-9a-f]+)$", s)] if m)
    fwd = [hex(p) for p, s in b if s == "mov ecx,dword ptr [ebp+0x8]"]
    args = sorted(set(m.group(1) for _, s in b for m in [re.search(r"\[ebp\+(0x[0-9a-f]+)\]", s)] if m))
    G(ok, "FUN_00455c70 (%d B, %d insns) is a pure TRAMPOLINE: %d stores; it calls %s and every call "
          "is preceded by `mov ecx,[ebp+0x8]` (%d sites - arg1 becomes the callee's this); it reads "
          "only %s and injects %s: a 5-arg (buffer, n, id, id, id) wrapper over the FUN_005dbdc0 "
          "registrar (ret 0x1c) plus two FUN_005e3412 flag calls on the same buffer"
          % (IDXMAP["FUN_00455c70"][1], len(b), len(st), dict(cl), len(fwd), args, dict(imm)),
      len(st) == 0 and dict(cl) == {"0x5dbdc0": 1, "0x5e3412": 2} and len(fwd) == 3
      and dict(imm) == {"0x109": 3, "0x107": 1, "0x106": 1, "0x792a30": 1, "0x0": 1},
      ["calls=%s imm=%s this-sites=%s args-read=%s" % (dict(cl), dict(imm), fwd, args)])
    fb = body("FUN_00459bb0")
    sites = [pc for pc, s in fb if s == "call 0x455c70"]
    a1 = []
    for t in sites:
        i = POS[t]; pre = [x for p, x in NM[i - 14:i] if x.startswith("push ")]
        a1.append(pre[-1][5:] if pre else None)
    immu = [x for x in a1 if x and x.startswith("0x")]
    regb = [x for x in a1 if x and not x.startswith("0x")]
    bss = [x for x in immu if int(x, 16) >= FILEMAP_END]
    ingrid = [x for x in immu if 0x774c38 <= int(x, 16) < 0x774c38 + 9 * 0x2c]
    G(ok, "its %d call sites in FUN_00459bb0 pass %d immediate arg1 buffers (%d register-passed); the "
          "immediates are %d distinct addresses, all %d above FILEMAP_END 0x6ec8c0 (runtime buffers), "
          "and %d fall inside the 0x774c38 grid - these sites register BUFFERS, not the grid"
          % (len(sites), len(immu), len(regb), len(set(immu)), len(bss), len(ingrid)),
      len(sites) == 15 and len(immu) == 11 and len(regb) == 4 and len(set(immu)) == 11
      and len(bss) == 11 and not ingrid,
      ["sites=%s" % [hex(x) for x in sites], "arg1=%s" % a1])
    lo, hi = 0x45a320, 0x45a6e0
    fam = sorted([(a, n) for a, n, z in IDX if lo <= a <= hi])
    pairs = []
    for a, n in fam:
        gg = sorted(set(int(m.group(1), 16) for _, s in body(n) for m in [re.search(r"ds:(0x9[0-9a-f]{5})", s)] if m))
        if len(gg) == 2 and gg[1] - gg[0] == 0x24:
            pairs.append((n, [hex(x) for x in gg]))
    G(ok, "the 0x45a320..0x45a6e0 run holds %d indexed functions; %d write EXACTLY two globals 0x24 "
          "apart - the pairs %s - i.e. parallel arrays at 0x99aa9c+4i and 0x99aac0+4i; the rest are "
          "the 3-store row-triple setters (M219/M224)" % (len(fam), len(pairs), pairs),
      len(pairs) >= 3 and [p[0] for p in pairs][:3] == ["FUN_0045a320", "FUN_0045a350", "FUN_0045a380"]
      and [p[1] for p in pairs][:3] == [["0x99aa9c", "0x99aac0"], ["0x99aaa0", "0x99aac4"],
                                        ["0x99aaa4", "0x99aac8"]],
      ["family-size=%d" % len(fam), "pair-publishers=%s" % pairs])
    report("M230")


for tag, fn in (("M227", m227), ("M228", m228), ("M229", m229), ("M230", m230)):
    fn()
print()
res, tot, got = [], 0, 0
for tag in RESULTS:
    v = RESULTS[tag]
    res.append("%s=%s" % (tag, "PASS" if all(c for _, c, _ in v) else "FAIL"))
    tot += len(v); got += sum(1 for _, c, _ in v if c)
print("SUMMARY %s (%d/%d gates)" % (" ".join(res), got, tot))
sys.exit(0 if got == tot else 1)
