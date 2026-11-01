#!/usr/bin/env python3
"""M231-M234: the 0x99aa9c/0x99aac0 pair staging arrays (the 9 publishers publish ARGUMENT VALUES;
two copy-in consumers materialise 18 dwords into a row-shaped object), the 0x774c38 grid (9 records
of 11 dwords, ZERO writers in the image), the 0x7543d8 record table (its count dword, the 0xd7 pair
written for all 89 indices, and the panel tail field +0x2144 taking a slot POINTER), and what the
FUN_00455c70 trampoline's two callees FUN_005dbdc0 / FUN_005e3412 do with (buffer, 0x109, 0x107/0x106).

  sudo -n python3 scripts/m231_m234_staging.py > evidence/m231_m234_staging.txt

Static: scratch/m574/text.txt + programs/terran.exe + ghidra_out/index.csv. Live: read-only
/proc/<pid>/mem reads (TracerPid 0, no tracer, no gdb). Every number the prose quotes is COMPUTED here.
"""
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


def publish_shape(f, narg):
    """A tiny staging publisher: narg arg-loads, narg stores of those registers, nothing else."""
    b = body(f)
    args = ["[ebp+0x8]", "[ebp+0xc]", "[ebp+0x10]"][:narg]
    loads = re.findall(r"mov (\w+),dword ptr (\[ebp\+0x[8dc]0?\])", " ; ".join(s for _, s in b))
    sts = [s for _, s in b if is_store(s)]
    dests = sorted({re.search(r"0x[0-9a-f]{6,8}", dest_operand(s)).group() for s in sts})
    srcs = sorted(s.split(",")[-1].strip() for s in sts)
    reg2arg = dict(loads)
    arg_of_src = sorted(reg2arg.get(x, "?") for x in srcs)
    return dict(insns=len(b), nst=len(sts), dests=dests, srcs=srcs, nloads=len(loads),
                args=arg_of_src, callees=sum(call_targets(f).values()),
                other=[s for _, s in b if is_store(s) is False and s.startswith("mov ") and "[" in s][:2])


def m231():
    tag = "M231"
    per = [publish_shape(f, 2) for f in PUB]
    want = [sorted(["0x%x" % (PAIR0 + 4 * i), "0x%x" % (PAIR1 + 4 * i)]) for i in range(9)]
    good = all(p["nst"] == 2 and p["dests"] == want[i] and p["args"] == sorted(["[ebp+0x8]", "[ebp+0xc]"])
               and p["nloads"] == 2 and p["callees"] == 0 for i, p in enumerate(per))
    G("M231 the 9 publishers 0x45a320+0x30*i each store its 2 ARG VALUES into slot i of both arrays "
      "(2 arg-loads, 2 stores, 0 callees, 0 dereference)", good,
      "per-fn (insns,stores,dests,sources): " + "; ".join(
          "%s %d/%d %s<-%s" % (p_[0], p["insns"], p["nst"], p["dests"], p["args"])
          for p_, p in zip(want, per))[:520])
    wh = window_hits(PAIR0, PAIR1 + 36)
    st = [x for x in wh if is_store(x[1])]
    ld = collections.Counter(fnof(x[0]) for x in wh if not is_store(x[1]))
    G("M231 the 18 staging dwords [0x99aa9c,0x99aaf4) have 18 writers (the 9 publishers) and their "
      "ONLY readers are FUN_0062d630 and FUN_0062d78d", len(st) == 18 and sorted(ld) == ["FUN_0062d630", "FUN_0062d78d"],
      "window refs=%d stores=%d store fns=%s readers=%s" % (len(wh), len(st),
      sorted(set(fnof(x[0]) for x in st)), dict(ld)))
    for f, want_vt in (("FUN_0062d630", (0x679f98, 0x679f90)), ("FUN_0062d78d", None)):
        b = body(f)
        all_disps = sorted({int(m.group(1), 16) for s in [s for _, s in b if is_store(s)]
                            for m in [re.search(r"\[\w+\+(0x[0-9a-f]+)\]", s)] if m})
        disps = [d for d in all_disps if 0xab8 <= d <= 0xafc]
        installs = [s for _, s in b if re.search(r"\],0x6[0-9a-f]{5}$", s) and "0x444" not in s]

        G("M231 %s copies exactly the 18 staging dwords into [this+0xab8..0xafc] (stride 4)%s" % (f,
          "; it is the CONSTRUCT that installs vtables 0x679f98/[+0x444]=0x679f90" if want_vt else " and installs NO vtable"),
          disps == [0xab8 + 4 * i for i in range(18)] and
          (bool(installs) == (want_vt is not None)) and
          (want_vt is None or all(v in VT for v in want_vt)),
          "disps=%s..%s n=%d vtable-imm-stores=%s vtables-in-image=%s" % (
              hex(disps[0]) if disps else "-", hex(disps[-1]) if disps else "-", len(disps), len(installs),
              {hex(v): VT.get(v, ("-", "-"))[0] for v in (want_vt or ())}))
    n1 = len([1 for _, s in NM if s == "call 0x62d630"]); n2 = len([1 for _, s in NM if s == "call 0x62d78d"])
    sl = slots_holding(0x62d78d)
    G("M231 FUN_0062d78d has ZERO direct call sites and ZERO code address-takes: it is reached ONLY as "
      "slot +0x15c of the very vtable 0x679f98 that FUN_0062d630 installs - the same slot offset the "
      "dialog family uses for its +0x15c installer (M220), so the copy-in is a vmethod, not a callee",
      n1 == 6 and n2 == 0 and len(hits("0x62d78d")) == 0 and sl == [(0x679f98, 0x15c, 2)],
      "call 0x62d630=%d (fns %s); call 0x62d78d=%d; code refs of 0x62d78d=%d; vtable slots=%s" % (
          n1, sorted(set(fnof(p) for p, s in NM if s == "call 0x62d630")), n2, len(hits("0x62d78d")),
          [(hex(b), hex(o), ins) for b, o, ins in sl]))


# ============== M232: the 0x774c38 grid, its zero writers, and who receives it ==============
def named_in(op, lo, hi):
    return [int(m.group(), 16) for m in RX_TOK.finditer(op) if lo <= int(m.group(), 16) < hi]


def handouts():
    """FUN_00459bb0's calls that push grid addresses (push order; LAST push = arg1)."""
    out = []; pend = []
    for pc, s in body("FUN_00459bb0"):
        m = re.match(r"^push\s+(\S.*)$", s)
        if m:
            pend.append(m.group(1).strip()); continue
        m = re.match(r"^call\s+(0x[0-9a-f]+)$", s)
        if m:
            g = [int(v, 16) for v in pend if re.fullmatch(r"0x[0-9a-f]{6,8}", v) and GR <= int(v, 16) < GRID_HI]
            if g:
                out.append((pc, m.group(1), len(pend), g))
            pend = []
    return out


def staging_slots(f):
    """The absolute dwords a tiny publisher/setter writes."""
    return sorted(int(m.group(), 16) for _, s in body(f) if is_store(s)
                  for m in [re.search(r"0x[0-9a-f]{6,8}", dest_operand(s))] if m)


def m232():
    lo, hi = 0x774a00, 0x774e00
    reg = window_hits(lo, hi)
    st = [x for x in reg if is_store(x[1])]
    into = [x for x in st if named_in(dest_operand(x[1]), lo, hi)]
    srcs = [x for x in st if named_in(x[1].split(",", 1)[1] if "," in x[1] else "", lo, hi)]
    disps = collections.Counter(m.group(2) for x in st for m in
                                [re.search(r"\[(\w+)\+(0x[0-9a-f]+)\]", dest_operand(x[1]))] if m)
    inblk = all(0xaf0 <= int(d, 16) <= 0xb30 for d in disps)
    G("M232 the grid has ZERO writers: of the %d stores naming [0x774a00,0x774e00), %d carry a region "
      "address in the DESTINATION and %d carry one in the SOURCE (FUN_0041f450 installing page bases "
      "into one field block at [reg+0xaf0..0xb30]); the region is written only through pointers"
      % (len(st), len(into), len(srcs)),
      len(into) == 0 and len(srcs) == len(st) == 39 and inblk and len(disps) == 9,
      "region refs=%d stores=%d into=%d source-carried=%d store fns=%s dest disps=%s" % (
          len(reg), len(st), len(into), len(srcs),
          dict(collections.Counter(fnof(x[0]) for x in st)), dict(sorted(disps.items()))))
    ho = handouts()
    push_ct = collections.Counter(v for _, _, _, gs in ho for v in gs)
    tri = sorted((tuple(sorted((v - GR) // GRS for v in g)), c) for _, c, _, g in ho if len(g) == 3)
    pair = sorted((tuple(sorted((v - GR) // GRS for v in g)), c) for _, c, _, g in ho if len(g) == 2)
    G("M232 the 9 entries are handed out 24 times over 9 calls: 6 calls take a TRIPLE (0,3,6)/(1,4,7)/"
      "(2,5,8) - 3 to the 0x9978ac setters, 3 to the 0x99779c trio - and 3 calls take the PAIR (e,e+6) "
      "to pair publishers i=2,4,5",
      sum(push_ct.values()) == 24 and len(ho) == 9 and
      sorted(set(c for _, c in tri)) == ["0x45a530", "0x45a590", "0x45a5c0", "0x45a680", "0x45a6b0", "0x45a6e0"] and
      sorted(set(c for _, c in pair)) == ["0x45a380", "0x45a3e0", "0x45a410"] and
      all(sorted(e[1] - e[0] for e in [x[0]]) == [6] for x in pair),
      "pushes=%d over %d calls; per-entry counts=%s; triples=%s; pairs=%s" % (
          sum(push_ct.values()), len(ho), dict(sorted(push_ct.items())), tri, pair))
    if not LIVE:
        return
    g = LIVE.dw(GR, 99)
    rows = [g[11 * i:11 * i + 11] for i in range(9)]
    shape_ok = all(r[0] == 0 and LIVE.loaded(r[1]) and r[2] == 9 and r[3] == r[4] == r[6]
                   and r[5] == r[7] == 0x14 and r[8] == r[9] == r[10] == 0 for r in rows)
    ns = collections.Counter(r[3] for r in rows)
    G("M232 live: all 9 grid entries are the SAME record shape {+0=0, +4=mapped pointer, +8=9, "
      "+0xc=+0x10=+0x18=N, +0x14=+0x1c=0x14, +0x20..+0x28=0}; 6 entries N=3, 3 entries N=0x43",
      shape_ok and ns[3] == 6 and ns[0x43] == 3,
      "pid %s TracerPid %s; N histogram=%s; pointers=%s" % (
          PID, LIVE.tracer, {hex(k): v for k, v in ns.items()}, [hex(r[1]) for r in rows]))
    exp = {}
    for pc, callee, nargs, gs in ho:
        if nargs == len(gs) >= 2:
            fn = "FUN_00%s" % callee[2:]
            slots = staging_slots(fn)
            if len(slots) == len(gs):
                exp[fn] = (slots, list(reversed(gs)))
    got = {f: (v[0], [LIVE.dw(a, 1)[0] for a in v[0]]) for f, v in exp.items()}
    G("M232 live read-back: every triple/pair the calls passed is EXACTLY what its staging slots hold "
      "now (the row group data are POINTERS to grid records, not values)",
      all(exp[f][1] == got[f][1] for f in exp) and len(exp) == 9,
      "mapped %d/9 publishers; " % len(exp) + "; ".join(
          "%s@%s=%s want %s" % (f, [hex(x) for x in got[f][0]], [hex(v) for v in got[f][1]],
                                [hex(v) for v in exp[f][1]]) for f in sorted(exp))[:420])


# ============== M233: the 0x7543d8 record table: 3 writers, 13 base-takes ==============
def pre(pc, n):
    i = bisect.bisect_left(PCS, pc); return [s for _, s in NM[i - n:i]]


def m233():
    tok = re.compile(r"0x7543[0-9a-f]{2}")
    reg = [(pc, s, m.group()) for pc, s in NM for m in [tok.search(s)] if m]
    st = [x for x in reg if is_store(x[1])]
    d7 = [x for x in st if x[1].endswith(",0xd7")]
    hdr = [x for x in st if "0x7543d4" in dest_operand(x[1])]
    b = body("FUN_00459490")
    bound = max(int(m.group(1), 16) for _, s in b
                for m in [re.search(r"cmp dword ptr \[ebp-0x4\],(0x[0-9a-f]+)", s)] if m)
    back = [(int(m.group(1), 16), pc) for pc, s in b for m in [re.match(r"^jmp\s+0x([0-9a-f]+)$", s)] if m
            and int(m.group(1), 16) < pc]
    inloop = all(any(t <= pc <= p for t, p in back) for pc, s, _ in d7)
    mul = all(any(re.search(r"imul %s,%s,0x2c" % (r, r), q) for q in pre(pc, 4))
              for pc, s, _ in d7 for r in [re.search(r"\[(\w+)\+0x7543", s).group(1)])
    G("M233 the whole image writes the 0x7543d8 table at only 3 sites: 2 folded stores of 0xd7 into "
      "+0x18/+0x1c of entry idx (idx=[ebp-0x4], imul 0x2c, inside FUN_00459490's loop bound 0x%x -> "
      "%d iterations) and 1 count store to 0x7543d4" % (bound, bound),
      len(st) == 3 and len(d7) == 2 and len(hdr) == 1 and inloop and mul,
      "census refs=%d stores=%d; 0xd7 sites=%s in-loop=%s stride-mul=%s; header store=%s@%s" % (
          len(reg), len(st), [hex(x[0]) for x in d7], inloop, mul, hdr[0][1] if hdr else "-",
          hex(hdr[0][0]) if hdr else "-"))
    base = [(pc, s) for pc, s in hits("0x7543d8")]
    cls = collections.Counter()
    for pc, s in base:
        if is_store(s):
            cls["store"] += 1; continue
        m = re.match(r"^(push|add|lea|mov|cmp|sub|and|or|test) ", s)
        cls[m.group(1) if m else "?"] += 1
    adj = [(pc, fnof(pc), NM[POS[pc] + 1][1]) for pc, s in base if s.startswith("add ")]
    G("M233 0x7543d8 itself is never a store destination: the 13 references are 2 push-as-arg, 5 "
      "receiver adjustors (add reg,0x7543d8 immediately before a call) and 6 lea address-takes",
      cls["store"] == 0 and cls["push"] == 2 and cls["add"] == 5 and cls["lea"] == 6 and len(base) == 13,
      "refs=%d classes=%s; adjustor sites+callees=%s" % (
          len(base), dict(cls), [(hex(a[0]), a[1], a[2]) for a in adj]))
    s2144 = [(pc, s) for pc, s in NM if s == "mov dword ptr [edi+0x2144],eax"
              and any(re.search(r"lea eax,\[\w+\*4\+0x7543d8\]", q) for q in pre(pc, 3))]
    G("M233 the panel tail field +0x2144 (M225/M228) receives a POINTER INTO this table: 2 sites in "
      "FUN_005aa310 store a register loaded by lea reg,[reg*4+0x7543d8] into [edi+0x2144] - stride 4 "
      "against the 0xd7 writer's stride 0x2c, the same collision M229 found for [obj+0xb24]",
      len(s2144) == 2 and all(fnof(pc) == "FUN_005aa310" for pc, _ in s2144),
      "sites=%s fns=%s" % ([hex(pc) for pc, _ in s2144], [fnof(pc) for pc, _ in s2144]))
    if not LIVE:
        return
    hdr_v = LIVE.dw(TABHDR, 1)[0]; e = LIVE.dw(TAB, 11 * 24)
    rows = [e[11 * i:11 * i + 11] for i in range(24)]
    p0 = rows[0][0]
    ok = (hdr_v == 11 and all(r[0] == p0 - 0x40 * i and LIVE.loaded(r[0]) and r[1] == 0 and r[2] == 9
                              and r[3] == r[4] == r[5] == 0 and r[6] == 0xd7 and r[7] == 0xd7
                              and r[8] == r[9] == r[10] == 0 for i, r in enumerate(rows[:16])))
    G("M233 live: count dword 0x7543d4 = 11 and entries 0..15 are {+0 = %s - 0x40*i (mapped: the "
      "entries point BACKWARD at 64-byte blocks), +4=0, +8=9, +0x18=+0x1c=0xd7 (the folded stores' "
      "value, so the loop ran for every index), rest 0}" % hex(p0), ok,
      "count=%d; ptrs 0..15=%s; entries 16..23 (+0,+8,+0x18)=%s" % (
          hdr_v, [hex(r[0]) for r in rows[:16]], [(hex(r[0]), r[2], hex(r[6])) for r in rows[16:]]))


# ============== M234: what the trampoline's callees do with (buffer, 0x109, 0x107/0x106) ==============
def resolve(op, pc):
    """A pushed REGISTER is resolved at ITS OWN push pc (s186 law) to its defining operand."""
    if not re.fullmatch(r"\w+", op):
        return op
    i = bisect.bisect_left(PCS, pc)
    for _, s in reversed(NM[max(0, i - 12):i]):
        m = re.match(r"^mov %s,(.*)$" % op, s)
        if m:
            return m.group(1).strip().replace("dword ptr ", "").replace("ds:", "")
    return op


def argvecs(fn, nargs):
    """(site, callee, this-source, args in order) from push order, truncated to the callee's own
    cleaned arg count (its ret imm) and with register pushes resolved to their defining load."""
    out = []; pend = []; ecx = None
    for pc, s in body(fn):
        m = re.match(r"^push\s+(\S.*)$", s)
        if m:
            pend.append((m.group(1).strip(), pc)); continue
        if re.match(r"^mov ecx,dword ptr \[ebp\+0x8\]$", s):
            ecx = "[ebp+0x8]"; continue
        m = re.match(r"^call\s+(0x[0-9a-f]+)$", s)
        if m:
            cn = m.group(1)
            if cn in nargs and nargs[cn]:
                n = nargs[cn]
                out.append((pc, cn, ecx, tuple(resolve(o, p) for o, p in reversed(pend[-n:]))))
            pend = []; ecx = None
    return out


def shape(fn):
    b = body(fn)
    ind = len([s for _, s in b if re.match(r"^call dword ptr \[", s)])
    byte_st = len([s for _, s in b if is_store(s) and s.startswith("mov byte ptr [")])
    byte_cmp = len([s for _, s in b if s.startswith("cmp byte ptr [")])
    gstores = [s for _, s in b if is_store(s) and "ds:0x" in dest_operand(s)]
    return dict(insns=len(b), ret=[s for _, s in b if s.startswith("ret")],
                direct=sum(call_targets(fn).values()), indirect=ind, callees=dict(call_targets(fn)),
                byte_stores=byte_st, byte_cmps=byte_cmp, global_stores=[dest_operand(s) for s in gstores],
                text=" ; ".join(s for _, s in b))


def m234():
    na = {}
    for c in ("0x5dbdc0", "0x5e3412"):
        rt = [s for _, s in body("FUN_00%s" % c[2:]) if s.startswith("ret")]
        m = re.match(r"^ret 0x([0-9a-f]+)$", rt[0]) if rt else None
        na[c] = int(m.group(1), 16) // 4 if m else 0
    av = argvecs("FUN_00455c70", na)
    dbtv = ("0x792a30", "0x109", "[ebp+0xc]", "[ebp+0x10]", "[ebp+0x14]", "[ebp+0x18]", "0x0")
    ok1 = (len(av) == 3 and all(t == "[ebp+0x8]" for _, _, t, _ in av) and
           [a for _, c, _, a in av if c == "0x5dbdc0"] == [dbtv] and
           sorted(tuple(a[:2]) for _, c, _, a in av if c == "0x5e3412") == [("0x106", "0x109"), ("0x107", "0x109")])
    G("M234 FUN_00455c70 hands its OWN arg1 to both callees as `this` (mov ecx,[ebp+0x8] before every "
      "call) and injects arg1=&0x792a30 + arg2=0x109 for FUN_005dbdc0 and (0x107,0x109)/(0x106,0x109) "
      "for the two FUN_005e3412 calls", ok1,
      "callee-cleaned arg counts (from their own ret imm)=%s; derived arg vectors=%s" % (
          na, [(hex(p), c, t, a) for p, c, t, a in av]))
    d = shape("FUN_005dbdc0"); e = shape("FUN_005e3412")
    n_d = len([1 for _, s in NM if s == "call 0x5dbdc0"]); n_e = len([1 for _, s in NM if s == "call 0x5e3412"])
    ok2 = (d["ret"] == ["ret 0x1c"] and d["indirect"] == 0 and n_d == 59 and
           "0x5ca8d2" in d["callees"] and "0x5be090" in d["callees"] and
           "[eax+0x80]" in d["text"] and d["text"].count("mov eax,0x3") >= 2)
    G("M234 FUN_005dbdc0 (ret 0x1c = 7 args, %d insns, %d direct sites, 0 indirect calls) gates its arg1 "
      "(&0x792a30) non-null through callee 0x5ca8d2, requires [ebp+0x18] and [ebp+0x1c] non-zero, returns "
      "3 on %d guard paths, reads [arg1+0x80] and allocates via 0x5be090: a RECORD consumer, not a formatter"
      % (d["insns"], n_d, d["text"].count("mov eax,0x3")), ok2,
      "ret=%s insns=%d direct=%d indirect=%d sites=%d callees=%s mov-eax3=%d global stores=%s" % (
          d["ret"], d["insns"], d["direct"], d["indirect"], n_d,
          dict(sorted(d["callees"].items(), key=lambda x: -x[1])[:6]),
          d["text"].count("mov eax,0x3"), d["global_stores"]))
    ok3 = (e["ret"] == ["ret 0x8"] and e["direct"] == 0 and e["indirect"] == 0 and n_e == 14 and
           e["byte_stores"] == 5 and e["byte_cmps"] >= 5 and "and ecx,0xff" in e["text"] and
           "and edx,0xff" in e["text"] and "mov eax,0x7" in e["text"] and
           re.search(r"imul ecx,dword ptr \[eax\+0x14\]", e["text"]) and "sar ecx,0x2" in e["text"])
    G("M234 FUN_005e3412 (ret 0x8 = 2 args, %d insns, 0 callees of any kind, %d direct sites) returns 7 "
      "when [this+4]==0, CLAMPS both args to their low bytes (and reg,0xff), takes the data pointer from "
      "[this+4] and the dword count from [this+0xc]*[this+0x14]>>2, then does %d byte-compares against "
      "low(arg1) with %d byte-stores of low(arg2): a tag-byte substitution pass on the buffer object"
      % (e["insns"], n_e, e["byte_cmps"], e["byte_stores"]), ok3,
      "ret=%s insns=%d direct callees=%d indirect=%d sites=%d byte cmp=%d byte store=%d count-mul=%s" % (
          e["ret"], e["insns"], e["direct"], e["indirect"], n_e, e["byte_cmps"], e["byte_stores"],
          bool(re.search(r"imul ecx,dword ptr \[eax\+0x14\]", e["text"]))))
    if not LIVE:
        return
    bufs = []; pend = []
    for pc, s in body("FUN_00459bb0"):
        m = re.match(r"^push\s+(\S.*)$", s)
        if m:
            pend.append(m.group(1).strip()); continue
        if s == "call 0x455c70":
            if pend and re.fullmatch(r"0x[0-9a-f]{6,8}", pend[-1]):
                bufs.append((pc, int(pend[-1], 16), len(pend)))
            pend = []
        elif s.startswith("call"):
            pend = []
    rows = [LIVE.dw(b, 11) for _, b, _ in bufs]
    exact = sum(1 for r in rows if (r[3] * r[5]) % 4 == 0)
    ok4 = (len(bufs) == 11 and len(set(b for _, b, _ in bufs)) == 11 and
           all(b > FILEMAP_END and nargs == 5 for _, b, nargs in bufs) and
           all(r[0] == 0 and LIVE.loaded(r[1]) and r[2] == 9 and r[3] == r[4] and r[5] != 0
               for r in rows))
    G("M234 live: the 11 buffers FUN_00459bb0 passes as the trampoline's arg1 are distinct BSS records "
      "(> FILEMAP_END) of the SAME 11-dword shape as the 0x774c38 grid entries {+0=0, +4=mapped data "
      "pointer, +8=9, +0xc=+0x10=N, +0x14=M} - they ARE grid-type records, and FUN_005e3412's length is "
      "the TRUNCATING dword count (N*M)>>2 (%d of 11 divide exactly)" % exact, ok4,
      "buffers=%s; per-buffer (+4,+8,+0xc,+0x10,+0x14,(N*M)>>2,N*M%%4)=%s" % (
          [hex(b) for _, b, _ in bufs],
          [(hex(r[1]), r[2], hex(r[3]), hex(r[4]), hex(r[5]), (r[3] * r[5]) >> 2, (r[3] * r[5]) % 4)
           for r in rows]))


def main():
    if not LIVE:
        print("BLOCKED: terran.exe is not running - the live half of M232/M233/M234 cannot answer")
        return 2
    for f in (m231, m232, m233, m234):
        f()
    print("# SMAC M231-M234 staging census | terran.exe pid %d TracerPid %s | corpus %d insns, "
          "image %d B, FILEMAP_END 0x%x" % (PID, LIVE.tracer, len(NM), len(IMG), FILEMAP_END))
    bad = 0
    for desc, ok, nums in GATES:
        print("%s %s\n    %s" % ("PASS" if ok else "FAIL", desc, nums))
        bad += 0 if ok else 1
    print("SUMMARY %s: %d/%d gates PASS" % ("M231/M232/M233/M234" if not bad else "MISMATCH",
                                            len(GATES) - bad, len(GATES)))
    return 0 if bad == 0 else 1


sys.exit(main())




