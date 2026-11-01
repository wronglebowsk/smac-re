#!/usr/bin/env python3
"""M235-M237: three record/vtable questions, one instrument, static + read-only /proc.

M235  what class is vtable 0x679f98 (extent, its 2 installs, its shared slots with 0x6717cc /
      0x671d94, the strings its slot functions reference, and who dispatches its slots)
M236  who ALLOCATES and fills the 11-dword records' +4 buffer and the 0x7543d8 table entries'
      -0x40*i blocks (the +8=9 record signature census, the allocator call sites, the filler)
M237  the last route to FUN_005f5a11: are the three fields 0x2210/0x2224/0x2234 read at all
      (both addressing forms), is there a call [reg+0x22XX] site, a register-held adjustor,
      or a bulk copy over the window (the block-copy falsifier M223 pre-registered)

  sudo -n python3 scripts/m235_m237_records.py > evidence/m235_m237_records.txt

Skeleton commit first (artifact before measurement); logic filled in after.
"""
import os
import bisect, collections, importlib.util, os, re, struct, subprocess, sys

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
GR = 0x774c38; GRS = 0x2c; NGRID = 9; GRID_HI = GR + GRS * NGRID   # the 9-entry grid
TAB = 0x7543d8; TABHDR = 0x7543d4                                   # record table + its count dword
PAIR0, PAIR1 = 0x99aa9c, 0x99aac0
RX_TOK = re.compile(r"0x[0-9a-f]{6,8}")


def dw(va):
    o = va - 0x400000
    return struct.unpack("<I", IMG[o:o + 4])[0] if 0 <= o < len(IMG) - 3 else 0


def in_text(v):
    return TEXT_LO <= v < TEXT_HI


def body(fn):
    a, z = IDXMAP[fn]
    return NM[bisect.bisect_left(PCS, a):bisect.bisect_left(PCS, a + z)]


def bstart(fn):
    return IDXMAP[fn][0]


def win(pc, n=12):
    i = bisect.bisect_left(PCS, pc); return NM[i:i + n]


def hits(tok):
    return [(pc, s) for pc, s in NM if tok in s]


def window_hits(lo, hi):
    """Every instruction whose text names an address in [lo, hi) - the §8 window census."""
    out = []
    for pc, s in NM:
        for m in RX_TOK.finditer(s):
            v = int(m.group(), 16)
            if lo <= v < hi:
                out.append((pc, s, v)); break
    return out


def is_store(t):
    m = re.match(r"^([a-z][\w.]*)\s+(.*)$", t)
    if not m:
        return False
    mn, rest = m.group(1), m.group(2)
    if mn.split(".")[0] not in ("mov", "movzx", "movsx", "movbe", "xchg"):
        return False
    dest = rest.split(",")[0].strip()
    if "[" in dest:
        return True
    if re.match(r"^(d|e)?word ptr ds:", dest):
        return True
    if re.match(r"^[a-z]{1,2}:?0x[0-9a-f]{5,8}$", dest):
        return True
    return False


def dest_operand(t):
    m = re.match(r"^[a-z][\w.]*\s+(.*?),", t)
    return m.group(1).strip() if m else ""


def call_targets(fn):
    out = collections.Counter()
    for _, s in body(fn):
        m = re.match(r"^call\s+(\S+)$", s)
        if m and "[" not in m.group(1):
            out[m.group(1)] += 1
    return out


# ---- vtables from the image (m217 machinery): a base is an imm32 stored into [reg+disp] whose own
# first dword is a code address; extent capped at the next candidate base.
bases = collections.Counter(); INSTALLS = collections.defaultdict(list)
RX_INS = re.compile(r"^mov dword ptr \[([^\]]*)\],(0x[0-9a-f]{6,8})$")
for pc, s in NM:
    m = RX_INS.match(s)
    if not m:
        continue
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


def slots_holding(addr):
    out = []
    for b, (n, ins) in VT.items():
        for k in range(n):
            if dw(b + 4 * k) == addr:
                out.append((b, 4 * k, ins))
    return out


# ---- live reads: /proc/<pid>/mem, seek+read (os.pread returns EIO on this host)
def game_pid():
    for p in os.listdir("/proc"):
        if not p.isdigit():
            continue
        try:
            if open("/proc/%s/comm" % p).read().strip() == "terran.exe":
                return int(p)
        except OSError:
            pass
    return None


class Live:
    def __init__(self, pid):
        self.pid = pid
        self.f = open("/proc/%d/mem" % pid, "rb", 0)
        self.tracer = open("/proc/%d/status" % pid).read().split("TracerPid:")[1].split()[0]
        self.segs = []
        for ln in open("/proc/%d/maps" % pid):
            try:
                a, b = ln.split()[0].split("-")
            except ValueError:
                continue
            self.segs.append((int(a, 16), int(b, 16), ln.split()[-1]))

    def dw(self, va, n):
        self.f.seek(va); return struct.unpack("<%dI" % n, self.f.read(4 * n))

    def region(self, va):
        for a, b, nm in self.segs:
            if a <= va < b:
                return nm
        return None

    def loaded(self, va):
        """A value that is a live address: mapped in the process and not the exe image itself."""
        nm = self.region(va)
        return nm is not None and not nm.lower().endswith(".exe")


PID = game_pid(); LIVE = Live(PID) if PID else None
GATES = []


def G(desc, cond, numbers):
    GATES.append((desc, bool(cond), numbers))


def grid_entry(v):
    """Which 0x774c38 grid slot a value points at, or None."""
    if GR <= v < GRID_HI and (v - GR) % GRS == 0:
        return (v - GR) // GRS
    return None


# ================= M231: the 0x99aa9c/0x99aac0 pair staging arrays =================
PUB = ["FUN_0045a%03x" % (0x320 + 0x30 * i) for i in range(9)]
SET9 = ["FUN_0045a%03x" % (0x4d0 + 0x30 * i) for i in range(9)]           # 0x9978ac.. triples
TRIO = ["FUN_0045a680", "FUN_0045a6b0", "FUN_0045a6e0"]                  # 0x99779c.. triples



V6 = 0x679f98
ADDR2FN = {a: n for a, n, z in IDX}


def vslots(b):
    n = VT.get(b, (0, 0))[0]
    return [(4 * k, dw(b + 4 * k)) for k in range(n)]


def readstr(va):
    o = va - 0x400000
    if not (0 <= o < len(IMG) - 4):
        return None
    raw = IMG[o:o + 64]; i = raw.find(b"\0")
    s = raw[:i if i >= 0 else 64].decode("latin1")
    return s if len(s) >= 4 and all(32 <= ord(c) < 127 for c in s) else None


def strings_of(fnaddrs, cap=14):
    out = collections.Counter()
    for a in sorted(set(fnaddrs)):
        nm = ADDR2FN.get(a)
        if not nm:
            continue
        for pc, s in body(nm):
            for m in RX_TOK.finditer(s):
                v = int(m.group(), 16)
                if DATA_LO <= v < FILEMAP_END:
                    t = readstr(v)
                    if t:
                        out[t] += 1
    return out.most_common(cap)


def shared_slots(a, b):
    sa = dict((o, f) for o, f in vslots(a) if in_text(f))
    sb = dict((o, f) for o, f in vslots(b) if in_text(f))
    return sorted(int(o) for o in sa if o in sb and sa[o] == sb[o])

def m235():
    n, ins = VT.get(V6, (0, 0))
    sl = vslots(V6)
    nb = bisect.bisect_right(B, V6)
    nxt = B[nb] if nb < len(B) else 0
    G("M235 0x679f98 is a %d-slot vtable (+0..+0x15c) whose last slot IS FUN_0062d78d, whose next dword is NOT code (0x%x) and whose next candidate base is %d dwords past its end"
      % (n, dw(V6 + 4 * n), (nxt - V6) // 4 if nxt else -1),
      n == 88 and dw(V6 + 0x15c) == 0x62d78d and not in_text(dw(V6 + 4 * n)),
      "slots=%d installs_in_image=%d last_slot=%08x after_last=%08x next_base=%08x gap_dwords=%s"
      % (n, ins, dw(V6 + 4 * (n - 1)), dw(V6 + 4 * n), nxt, (nxt - V6) // 4 if nxt else None))
    its = INSTALLS.get(V6, [])
    fns = sorted(set(fnof(pc) for pc, f, d in its))
    G("M235 0x679f98 has EXACTLY %d immediate installs, both at [reg+0], in the class's TWO constructors %s - nothing else in the image installs it"
      % (len(its), " and ".join(fns)),
      len(its) == 2 and fns == ["FUN_0062d630", "FUN_0062d764"] and all(d == "eax" for pc, f, d in its),
      "installs=%s second_ctor=%s" % ([(hex(pc), fn, d) for pc, fn, d in its], IDXMAP.get("FUN_0062d764", ("?", "?"))))
    sh17 = shared_slots(0x6717cc, V6); sh1d = shared_slots(0x671d94, V6)
    core = sorted(set(sh17) & set(sh1d))
    uniq = sorted(o for o, f in sl if o not in set(sh17) and o not in set(sh1d))
    names = strings_of([f for o, f in sl if in_text(f)])
    G("M235 the class is named STRUCTURALLY, not by strings: its %d slot functions reference %d string literals, but %d of its %d slots are IMPLEMENTATION-IDENTICAL to 0x6717cc and %d to 0x671d94 (%d identical in all three), leaving %d slots unique to it (%s)"
      % (n, len(names), len(sh17), n, len(sh1d), len(core), len(uniq), [hex(x) for x in uniq[:10]]),
      len(names) == 0 and len(core) >= 60 and 0 < len(uniq) < 20,
      "shared_6717cc=%s shared_671d94=%s core=%d unique=%s extents=%d/%d/%d" %
      ([hex(x) for x in sh17[:10]], [hex(x) for x in sh1d[:8]], len(core), [hex(x) for x in uniq[:12]],
       VT.get(0x6717cc, (0,))[0], VT.get(0x671d94, (0,))[0], n))
    CALLD = collections.Counter(); CALLALL = collections.Counter()
    for pc, s in NM:
        m = re.match(r"^call +dword ptr \[([a-z]+)(?:\*(\d+))?\+0x([0-9a-f]+)\]", s)
        if m:
            d = int(m.group(3), 16)
            CALLALL[d] += 1
            if d < 0x2000:
                CALLD[d] += 1
    hitsl = sorted(((o, CALLD.get(o, 0)) for o, f in sl), key=lambda x: -x[1])
    tot = sum(c for o, c in hitsl)
    zero = [o for o, c in hitsl if c == 0]
    G("M235 %d of the 88 slots have at least one member-scale (disp < 0x2000) `call [reg+slot]` site image-wide (%d sites, busiest +%s x%d); EXACTLY %d slot has zero dispatchers (+%s); +0x15c itself carries %d sites, so the class's LAST slot is an ordinary self-dispatch point - the largest call displacement of any form in the image is +%s, which is where the panel's stored FIELD callback sits (M225)"
      % (sum(1 for o, c in hitsl if c), tot, hex(hitsl[0][0]), hitsl[0][1], len(zero), hex(zero[0]) if zero else "-",
         CALLD.get(0x15c, 0), hex(max(CALLALL))),
      tot > 0 and CALLD.get(0x15c, 0) >= 1 and len(zero) == 1,
      ([(hex(o), c) for o, c in hitsl[:6]], "zero_dispatch_slots=%s of_%d max_member_disp=%s all_form_max=%s sites_at_0x15c=%d" %
       ([hex(x) for x in zero], n, hex(max(CALLD)), hex(max(CALLALL)), CALLD.get(0x15c, 0))))

RX_BR = re.compile(r"\[([a-z]+)(?:\*(\d+))?\+0x([0-9a-f]{1,8})\]")
RX_ABS = re.compile(r"^(?:[a-z]+ ptr )?d?s?:0x([0-9a-f]{1,8})$")
RX_MN = re.compile(r"^([a-z][\w.]*)\s+(.*)$")
RMW = ("and", "or", "xor", "add", "sub", "shl", "shr", "inc", "dec", "neg", "not", "xchg")
READERS = ("cmp", "test")


def parts(s):
    m = RX_MN.match(s)
    return (m.group(1), m.group(2)) if m else ("?", s)


def brk_of(op):
    """The memory operand of an instruction, from EITHER print form: a bracket
    ([reg*4+disp]) or an absolute (DWORD PTR ds:0x9977f0 / ds:0x9977f0, no brackets)."""
    op = (op or "").strip()
    m = RX_BR.search(op)
    if m:
        return (m.group(1), int(m.group(2) or 1), int(m.group(3), 16))
    m = RX_ABS.match(op)
    return ("ds", 1, int(m.group(1), 16)) if m else None


def classify(s):
    """-> (kind, mem_or_dest_brk, other_brk); kind in store/load/rmw/read/lea/call/other."""
    mn, rest = parts(s)
    ops = rest.split(",")
    first = ops[0] if ops else ""
    second = ",".join(ops[1:]) if len(ops) > 1 else ""
    fb, sb = brk_of(first), brk_of(second)
    if mn == "mov":
        return ("store", fb, sb) if fb else ("load", sb, fb)
    if mn in ("movzx", "movsx", "lds"):
        return ("load", fb or sb, sb if fb else None)
    if mn == "lea":
        return ("lea", sb if not fb else fb, fb if not sb else sb)
    if mn in READERS:
        return ("read", fb or sb, sb if fb else None)
    if mn in RMW:
        return ("rmw", fb, sb)
    if mn == "call":
        return ("call", fb, sb)
    return ("other", fb, sb)


WIN_LO, WIN_HI = 0x21c0, 0x2260
FIELDS = (0x2210, 0x2224, 0x2234)

def ctor_facts(f, back=12):
    bl = body(f)
    stores, calls, rets = [], [], []
    for i, (pc, s) in enumerate(bl):
        mn, rest = parts(s)
        k, db, sb = classify(s)
        if k in ("store", "rmw") and db:
            stores.append((db[2], db[1], rest.split(",")[-1].strip(), pc))
        if mn == "call" and re.match(r"^0x[0-9a-f]{6,8}$", rest.strip()):
            imms = []
            for j in range(max(0, i - back), i):
                m2 = re.match(r"^push +0x([0-9a-f]+)$", bl[j][1])
                if m2:
                    imms.append("0x" + m2.group(1))
            calls.append((rest.strip()[2:], pc, imms))
        if mn == "ret":
            rets.append(rest.strip() or "0")
    return stores, calls, rets


def m236():
    nine = [(pc, s, fnof(pc)) for pc, s in NM
            if classify(s)[0] == "store" and classify(s)[1] and classify(s)[1][2] == 8
            and classify(s)[1][1] not in ("ebp", "esp")
            and parts(s)[1].split(",")[-1].strip() in ("0x9", "9")]
    cf = ctor_facts("FUN_005dbb5f") if nine else ([], [], [])
    cst = collections.Counter(hex(d) for d, r, v, pc in cf[0])
    G("M236 the record signature `mov [reg+8],9` has EXACTLY %d immediate store in the whole %d-instruction image - at %s inside %s - so the 9 that every grid record, table entry and trampoline buffer carries at +8 has ONE emitter, not a packer family; that function is %d insns, %d calls, and stores at disps %s"
      % (len(nine), len(NM), hex(nine[0][0]) if nine else "-", nine[0][2] if nine else "-",
         len(body("FUN_005dbb5f")) if nine else 0, len(cf[1]), sorted(cst)),
      len(nine) == 1 and nine[0][2] == "FUN_005dbb5f" and len(cf[1]) == 0,
      "site=%s ctor stores=%s" % ([(hex(pc), s) for pc, s, f in nine],
        sorted(set((hex(d), r, v) for d, r, v, pc in cf[0]))[:16]))
    zero_disps = sorted(set(hex(d) for d, r, v, pc in cf[0] if v in ("0x0", "0") and d < 0x100))
    pubs = [(hex(d), r, v) for d, r, v, pc in cf[0] if d >= 0x400000]
    a4 = [x for x in cf[0] if x[0] == 4]
    G("M236 the constructor does NOT allocate: it has %d calls, writes %d immediates of 0x0 into the record (disps %s, including +4 = %d store(s)), writes the 9 as a BYTE (`%s`) and publishes the record POINTER itself into the global %s - so the +4 buffer pointer is installed by a DIFFERENT writer than the one that stamps +8"
      % (len(cf[1]), len(zero_disps), zero_disps, len(a4), nine[0][1] if nine else "-", pubs[0][0] if pubs else "-"),
      len(cf[1]) == 0 and bool(pubs) and len(a4) == 1 and nine and nine[0][1].startswith("mov byte ptr"),
      "zeroed=%s stores_at_4=%s global_publish=%s" % (zero_disps, [(hex(d), r, v, hex(pc)) for d, r, v, pc in a4], pubs))
    ld4 = collections.defaultdict(list)
    for pc, s in NM:
        k, db, sb = classify(s)
        if k == "store" and db and db[2] == 4 and db[1] not in ("ebp", "esp") and parts(s)[1].split(",")[-1].strip() == "eax":
            c, i = None, POS[pc]
            for back in range(1, 9):
                if i - back < 0:
                    break
                pc2, s2 = NM[i - back]
                if fnof(pc2) != fnof(pc):
                    break
                m = re.match(r"^call +0x([0-9a-f]+)", s2)
                if m:
                    c = m.group(1); break
            if c:
                ld4[c].append((hex(pc), fnof(pc)))
    top = sorted(ld4.items(), key=lambda kv: -len(kv[1]))[:5]
    g9 = [(pc, s, fnof(pc)) for pc, s in NM if "0x9965b8" in s]
    g9st = collections.Counter(f for pc, s, f in g9 if classify(s)[0] in ("store", "rmw"))
    g9ld = collections.Counter(f for pc, s, f in g9 if classify(s)[0] in ("load", "read"))
    G("M236 the +4 pointer IS allocated, but not here: image-wide %d sites store a call result into [reg+4] within 8 insns of that call over %d callees, the top being FUN_00%s with %d sites in %d functions; and the record-under-construction global 0x9965b8 has %d stores in %d functions and %d loads in %d functions - the writer that fills these records consumes THAT global"
      % (sum(len(v) for _, v in ld4.items()), len(ld4), top[0][0] if top else "?", len(top[0][1]) if top else 0,
         len(set(f for _, f in top[0][1])) if top else 0, sum(g9st.values()), len(g9st), sum(g9ld.values()), len(g9ld)),
      len(ld4) >= 3 and bool(top) and len(top[0][1]) >= 10 and len(g9ld) >= 1,
      "ranked=%s 9965b8_stores=%s 9965b8_loads=%s" % ([(c, len(v), sorted(set(f for _, f in v))[:5]) for c, v in top], dict(g9st), dict(g9ld)))
    if LIVE:
        ptrs = sorted(LIVE.dw(GR + GRS * i + 4, 1)[0] for i in range(NGRID))
        cl, i = [], 0
        while i < len(ptrs):
            j = i
            step = ptrs[i + 1] - ptrs[i] if i + 1 < len(ptrs) else 0
            while j + 1 < len(ptrs) and (ptrs[j + 1] - ptrs[j]) == step:
                j += 1
            cl.append((ptrs[i:j + 1], step if j > i else 0)); i = j + 1
        tp = [LIVE.dw(TAB + 0x2c * k, 1)[0] for k in range(4)]
        tsteps = sorted(set(tp[k + 1] - tp[k] for k in range(3)))
        G("M236 live: the 9 grid +4 buffers fall in %d block-strided clusters (%s) and every pointer is MAPPED heap memory; the 0x7543d8 entries' +0 pointers step by exactly %s (count dword %d) - NEITHER region is per-record allocated, each is one allocation handed out at a fixed block size"
          % (len(cl), ["%d blocks x step %s" % (len(c), hex(s)) for c, s in cl], [hex(x) for x in tsteps], LIVE.dw(TABHDR, 1)[0]),
          all(LIVE.loaded(p) for p in ptrs) and len(cl) == 2 and sorted(set(s for c, s in cl if s)) == [0x70, 0x568] and tsteps == [-0x40],
          "pid=%d tracer=%s grid=%s clusters=%s table0..3=%s" % (PID, LIVE.tracer, [hex(p) for p in ptrs], [(len(c), hex(s)) for c, s in cl], [hex(x) for x in tp]))
    else:
        G("M236 live: no terran.exe pid - the block-stride claim is UNVERIFIED", False, "pid=None")

def m237():
    win = []
    for pc, s in NM:
        k, db, sb = classify(s)
        for b in (db, sb):
            if b and WIN_LO <= b[2] < WIN_HI:
                win.append((pc, s, k, b[2], b[1], b[0])); break
    byk = collections.Counter((k, d) for pc, s, k, d, sc, br in win)
    fld = {f: {k: c for (k, d), c in byk.items() if d == f} for f in FIELDS}
    fstores = sum(e.get("store", 0) + e.get("rmw", 0) for e in fld.values())
    freads = sum(e.get("load", 0) + e.get("read", 0) + e.get("call", 0) + e.get("lea", 0) for e in fld.values())
    totloads = sum(c for (k, d), c in byk.items() if k in ("load", "read"))
    busy = sorted(((sum(c for (k2, d2), c in byk.items() if d2 == d), hex(d)) for d in set(d for pc, s, k, d, sc, br in win)), reverse=True)
    G("M237 the three callback fields 0x2210/0x2224/0x2234 have %d stores and %d loads/call-through/lea/add - ZERO readers in EITHER addressing form - while the member block they sit in is BUSY (%d bracket sites, %d loads/reads, busiest displacements %s): the fields are write-only, the block around them is not"
      % (fstores, freads, len(win), totloads, ["+%s x%d" % (d, c) for c, d in busy[:4]]),
      fstores == 3 and freads == 0 and totloads >= 20,
      "per-field=%s per-disp=%s" % ({hex(f): fld[f] for f in FIELDS}, busy[:8]))
    ins = [(pc, s, fnof(pc)) for pc, s in NM if "0x5f5a11" in s]
    dsts = sorted(set(hex(classify(s)[1][2]) for pc, s, f in ins if classify(s)[1]))
    ifns = sorted(set(f for pc, s, f in ins))
    G("M237 &FUN_005f5a11 appears at %d sites in the image, ALL stores, ALL inside %s, at disps %s - ONE installer writes the SAME callback into all three fields; the function is never called, never appears in a vtable, never copied"
      % (len(ins), ifns, dsts),
      len(ins) == 3 and all(classify(s)[0] == "store" for pc, s, f in ins) and len(ifns) == 1 and tuple(dsts) == ("0x2210", "0x2224", "0x2234"),
      "sites=%s installer=%s installer_size=%s" % ([(hex(pc), s[:44]) for pc, s, f in ins], ifns, IDXMAP.get(ifns[0], ("?", "?"))[1] if ifns else "?"))
    rm = [(pc, s, fnof(pc)) for pc, s in NM if s.startswith("rep movs")]
    wfns = collections.defaultdict(set)
    for pc, s, k, d, sc, br in win:
        wfns[fnof(pc)].add(hex(d))
    inw = [(hex(pc), f, sorted(wfns[f])) for pc, s, f in rm if f in wfns]
    reach = [x for x in inw if any(hex(fld) in x[2] for fld in FIELDS)]
    ctx = [(p, [t for _, t in NM[max(0, POS[int(p, 16)] - 6):POS[int(p, 16)] + 1]]) for p, f, ds in inw]
    G("M237 the pre-registered block-copy falsifier: %d `rep movs` sites image-wide, %d of them in %d functions that also name a displacement in the member block; %d of those functions name any of the three callback displacements - no bulk copy reaches the fields, so the 3 stores in %s are the whole story"
      % (len(rm), len(inw), len(set(f for p, f, ds in inw)), len(reach), ifns[0] if ifns else "?"),
      len(rm) > 0 and len(inw) > 0 and len(reach) == 0,
      "rep-movs-in-window-fns=%s copy-prelude=%s" % ([(p, f, ds[:6]) for p, f, ds in inw], [(p, c[-2:]) for p, c in ctx]))
    hw = [(pc, s, fnof(pc)) for pc, s in NM if "0x9977f0" in s]
    st = [(hex(pc), f, s[:38]) for pc, s, f in hw if classify(s)[0] in ("store", "rmw")]
    ld = [(hex(pc), f) for pc, s, f in hw if classify(s)[0] in ("load", "read")]
    noabs = sum(1 for pc, f, s in st if not s.startswith("mov dword ptr ["))
    hv = LIVE.dw(0x9977f0, 1)[0] if LIVE else None
    G("M237 the handle FUN_005f5a11 itself gates on, ds:0x9977f0, is written at %d sites in %d functions (%d of them absolute stores a bracket-grep cannot see) and read at %d; live it reads 0x%x - NO modal object is instantiated, so the installed callbacks cannot be read back from the running game without opening a dialog (box)"
      % (len(st), len(set(f for pc, f, s in st)), noabs, len(ld), hv if hv is not None else -1),
      len(st) >= 2 and len(ld) >= 5 and hv == 0,
      "stores=%s loads=%d handle=%s pid=%s tracer=%s" % (st, len(ld), hex(hv) if hv is not None else None, PID, LIVE.tracer if LIVE else "-"))


def main():
    print("# SMAC M235-M237 record/vtable census | terran.exe pid %s TracerPid %s | corpus %d insns, image %d B, FILEMAP_END %s"
          % (PID, LIVE.tracer if LIVE else "-", len(NM), len(IMG), hex(FILEMAP_END)))
    m235(); m236(); m237()
    npass = sum(1 for d, ok, n in GATES if ok)
    for d, ok, n in GATES:
        print(("PASS " if ok else "FAIL ") + d)
        print("    " + str(n))
    print("SUMMARY M235/M236/M237: %d/%d gates PASS" % (npass, len(GATES)))
    return 0 if npass == len(GATES) else 1

if __name__ == "__main__":
    sys.exit(main())
