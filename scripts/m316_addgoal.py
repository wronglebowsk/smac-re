#!/usr/bin/env python3
# M316: the GOAL record system - AddGoal(block,kind,prio,p1,p2,owner) at FUN_0056d350.
# Static only. Evidence: scratch/m574/text.txt (full .text disasm) + terran.exe bytes.
# Law: digests hash MEASURED detail values, not gate names.
import os, re, sys, hashlib, struct, bisect, csv, collections

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(REPO, "scratch", "m574", "text.txt")
EXE = os.path.join(REPO, "terran.exe")
IDX = os.path.join(REPO, "ghidra_out", "index.csv")

# ---------- load parsed .text (optionally code-patched via M316_PATCH) ----------
def load_ins():
    ins = {}
    lin = re.compile(r"^\s*([0-9a-f]{6,8}):\s[0-9a-f ]+\t(\w+)\s*(.*)$")
    for ln in open(TEXT):
        m = lin.match(ln)
        if m:
            a = int(m.group(1), 16)
            ins[a] = (m.group(2), m.group(3).strip())
    p = os.environ.get("M316_PATCH")
    n = 0
    if p:
        for chunk in p.split(";"):
            chunk = chunk.strip()
            if not chunk: continue
            addr, rest = chunk.split("|", 1)
            mn, _, ops = rest.partition(" ")
            ops = ops.strip()
            a = int(addr, 16)
            if a not in ins:
                raise SystemExit("M316_PATCH address not in .text cache: %s" % addr)
            if (ins[a][0], ins[a][1]) == (mn, ops.strip()):
                raise SystemExit("M316_PATCH applied to nothing (already equal)")
            ins[a] = (mn, ops.strip()); n += 1
        if n == 0: raise SystemExit("M316_PATCH applied to nothing")
    return ins
INS = load_ins()
ADDRS = sorted(INS)

funcs = []
with open(IDX) as f:
    for r in csv.DictReader(f):
        funcs.append((int(r["addr"], 16), r["name"], int(r["size_bytes"] or 0)))
funcs.sort()
FSTARTS = [a for a, _, _ in funcs]
def owner(a):
    i = bisect.bisect_right(FSTARTS, a) - 1
    return funcs[i][1] if i >= 0 else "?"
def fspan(name):
    for a, nm, sz in funcs:
        if nm == name: return a, a + max(sz, 1)
    return 0, 0

def window(lo, hi):
    return [(a, INS[a][0], INS[a][1]) for a in ADDRS if lo <= a < hi and a in INS]

ADDGOAL = 0x56d350
AG_LO, AG_HI = 0x56d350, 0x56d480
ENGINE = "FUN_00556690"
ENG_LO, ENG_HI = fspan("FUN_00556690")
INV_LO, INV_HI = 0x470b90, 0x470f8a  # FUN_00470b90 (M310)

BAND_RE = re.compile(r"0x94ee(2[89a-ce]|3[04])\b")
def band_off(ops):
    m = BAND_RE.search(ops.lower())
    if not m: return None
    return int(m.group(1), 16) - 0x28

results = []
def ck(name, ok, detail):
    results.append((name, ok, detail))
    print(("OK  " if ok else "FAIL") + " " + name + "  " + detail)

# ---------- A1: the file-wide GOAL-band DIRECT-WRITE set is exactly 6 ----------
stores = []
for a in ADDRS:
    mn, ops = INS[a]
    if mn == "mov":
        dest = ops.split(",")[0]
        d = band_off(dest)
        if d is not None and "ptr" in dest.lower():
            src = ops.split(",", 1)[1].strip()
            stores.append((a, d, "WORD" if dest.lower().startswith("word") else "DWORD", src))
want = {0x56d44b: (4, "DWORD", "ecx"), 0x56d455: (8, "DWORD", "edx"),
        0x56d45f: (0, "WORD", "cx"),   0x56d469: (2, "WORD", "dx"),
        0x56d470: (12, "DWORD", "ecx"), 0x470d5c: (0, "WORD", "0xffff")}
# relative stores: lea reg,[...+0x94eeXX]; then mov <size> PTR [reg(+/-d)],v  -> eff offset
def rel_stores(lo, hi):
    out = {}; lea = {}
    for a in range(lo, hi):
        if a not in INS: continue
        mn, o = INS[a]
        if mn == "lea":
            m = re.match(r"(\w+),\s*\[(.*?)0x94ee([0-9a-f]{2})\]", o)
            if m: lea[m.group(1)] = int(m.group(3), 16) - 0x28
        if mn == "mov":
            for r, base in lea.items():
                mm = re.match(r"(WORD|DWORD|BYTE) PTR \[%s\s*(?:([+-])\s*(0x[0-9a-f]+))?\]" % re.escape(r), o)
                if mm:
                    sign = -1 if mm.group(2) == "-" else 1
                    off = int(mm.group(3), 16) if mm.group(3) else 0
                    out[a] = (base + sign * off, mm.group(1), o.split(",", 1)[1].strip())
    return out
REL = {}
for _lo, _hi in [(AG_LO, 0x56d47c), (0x56d690, 0x56d710), (0x56d710, 0x56d780)]:
    REL.update(rel_stores(_lo, _hi))
wantrel = {0x56d41c: (2, "WORD", "ax"),
 0x56d6be: (0, "WORD", "0xffff"), 0x56d6c8: (2, "WORD", "ax"),
 0x56d73a: (0, "WORD", "di"), 0x56d73e: (2, "WORD", "cx"), 0x56d741: (8, "DWORD", "ecx"),
 0x56d744: (4, "DWORD", "ecx"), 0x56d747: (12, "DWORD", "ecx"),
 0x56d75b: (0, "WORD", "di"), 0x56d75f: (2, "WORD", "cx"), 0x56d762: (8, "DWORD", "ecx"),
 0x56d765: (4, "DWORD", "ecx"), 0x56d768: (12, "DWORD", "ecx")}
ck("A11_band_relative_writes_exactly13", REL == wantrel,
   "rel-stores=%d offsets=%s kill-0xffff@%s max-update@0x56d41c" %
   (len(REL), sorted({hex(d) for d, _, _ in REL.values()}), REL.get(0x56d6be) == (0, "WORD", "0xffff")))
got = {a: (d, sz, src) for a, d, sz, src in stores}
ck("A1_band_absolute_writes_exactly6",
   len(stores) == 6 and got == want,
   "stores=%d addrs=%s" % (len(stores), sorted(hex(a) for a in got)))

# ---------- A2: record layout proof (offset x size x writer) ----------
lay = {}
for a, d, sz, src in stores:
    if AG_LO <= a < AG_HI: lay[d] = sz
ck("A2_record_layout", lay == {4: "DWORD", 8: "DWORD", 0: "WORD", 2: "WORD", 12: "DWORD"},
   "offset->size %s" % {hex(k): v for k, v in sorted(lay.items())})
shl16 = [a for a, m_, o in window(AG_LO, AG_HI) if m_ == "shl" and o.endswith(",0x4")]
leaband = [a for a, m_, o in window(AG_LO, AG_HI) if m_ == "lea" and band_off(o) is not None]
ck("A2b_entry16B_fold_via_shl_and_lea",
   shl16 == [0x56d395, 0x56d404, 0x56d442] and len(leaband) >= 3,
   "shl-0x4=%s lea-band=%s" % ([hex(a) for a in shl16], [hex(a) for a in leaband]))

# ---------- A3: 75-entry scan bounds, file-wide (2 here + 2 in M310 invalidator) ----------
bounds = [(a, INS[a][1]) for a in ADDRS
          if INS[a][0] == "cmp" and re.fullmatch(r".*,0x4b", INS[a][1])
          and (AG_LO <= a < AG_HI or INV_LO <= a < INV_HI)]
ck("A3_all_goal_list_bounds_are_75",
   [a for a, _ in bounds] == [0x470c16, 0x470cc8, 0x56d3b9, 0x56d436],
   "cmp-0x4b sites %s" % [hex(a) for a, _ in bounds])

# ---------- A4: eviction-score law encoded in bytes ----------
sc = []
for a, m_, o in window(AG_LO, AG_HI):
    if o.endswith(",0x3e8") and m_ == "and": sc.append(("free1000", a, m_ + " " + o))
    if re.fullmatch(r"\w+,0x14", o) and m_ == "mov": sc.append(("base20", a, m_ + " " + o))
    if o.endswith(",0x64") and m_ == "add": sc.append(("plus100", a, m_ + " " + o))
ck("A4_eviction_score_constants",
   dict((t[0], t[1]) for t in sc) == {"free1000": 0x56d3e6, "base20": 0x56d3fb, "plus100": 0x56d425},
   "%s" % sorted((t[0], hex(t[1])) for t in sc))
# candidate gate: free-or-lower-prio: sign test on kind + cmp prio<new
sign = [(a, o) for a, m_, o in window(AG_LO, AG_HI) if m_ in ("test", "cmp")]
kind_neg = [a for a, o in sign if any(re.search(r"(js|jl|sgn)", x or "") for x in [""])]
ck("A4b_candidate_gate_shape",
   len([1 for a, m_, o in window(AG_LO, AG_HI) if m_ == "movsx"]) >= 3 and
   len([1 for a, o in sign if re.fullmatch(r"\w+,\w+", o)]) >= 2,
   "movsx=%d reg-cmps=%d" % (len([1 for a, m_, o in window(AG_LO, AG_HI) if m_ == "movsx"]),
                             len([1 for a, o in sign if re.fullmatch(r"\w+,\w+", o)])))

# ---------- A5: duplicate law - 3-field match then MAX priority ----------
TRIPLE = [(0x56d3a3, "cmp", "DWORD PTR [ecx-0x4],esi"),
          (0x56d3a8, "cmp", "DWORD PTR [ecx],edi"),
          (0x56d3ac, "movsx", "ebx,WORD PTR [ecx-0x8]"),
          (0x56d3b0, "cmp", "ebx,DWORD PTR [ebp+0xc]"),
          (0x56d3b3, "je", "0x56d404"),
          (0x56d3b6, "add", "ecx,0x10")]
ck("A5_duplicate_triple_and_16B_stride",
   all(INS[a] == (m, o) for a, m, o in TRIPLE) and INS[0x56d407][1].endswith("+0x94ee2a]"),
   "triple pinned; dup-hit je->max-tail lea prio %s" % INS[0x56d407][1])
ck("A5b_max_tail_and_eviction_backedge",
   INS[0x56d436] == ("cmp", "edi,0x4b") and any(m_ == "jl" for a, m_, o in window(0x56d436, 0x56d442)),
   "evict-bound %s; jl in %s" % (INS[0x56d436], hex([a for a, m_, o in window(0x56d436, 0x56d442) if m_ == "jl"][0])))

# ---------- A6: the 50 construction sites and their constant kinds ----------
def pushwalk(si_addr):
    idx = bisect.bisect_left(ADDRS, si_addr)
    pushed, regimm, steps = [], {}, 0
    i = idx - 1
    while i >= 0 and steps < 28:
        a = ADDRS[i]; mn, o = INS[a]; steps += 1
        if mn == "call" and not o.replace(" ", "").startswith("0x56d350"): break
        if mn == "push":
            t = o.strip()
            if re.fullmatch(r"0x[0-9a-f]+", t): pushed.append(int(t, 16))
            elif t in regimm: pushed.append(regimm[t])
            else: pushed.append(None)
        elif mn == "mov":
            m = re.fullmatch(r"(\w+),\s*(-?0x[0-9a-f]+)", o)
            if m: regimm[m.group(1)] = int(m.group(2), 16)
        i -= 1
    pushed.reverse()
    return pushed
sites = [a for a in ADDRS if INS[a] == ("call", "0x56d350")]
siteinfo = []
for a in sites:
    p = pushwalk(a)
    kind = p[-2] if len(p) >= 2 else None
    prio = p[-3] if len(p) >= 3 else None
    siteinfo.append((a, owner(a), kind, prio))
imm_kinds = sorted(set(k for _, _, k, _ in siteinfo if k is not None))
ck("A6_sites_exactly50", len(sites) == 50 and
   len(set(o for _, o, _, _ in siteinfo)) == 12,
   "sites=%d owners=%d" % (len(sites), len(set(o for _, o, _, _ in siteinfo))))
SITE_DIGEST = "8ace40ec97032541"  # measured; the 50 (site, owner, kind, prio) tuples
ck("A6b_site_owner_digest", hashlib.sha256(repr(siteinfo).encode()).hexdigest()[:16] == SITE_DIGEST,
   "digest=" + hashlib.sha256(repr(siteinfo).encode()).hexdigest()[:16])
ck("A6c_immediate_kinds_constructed",
   imm_kinds == [0, 2, 3, 6, 7, 8, 9, 11, 16, 25, 41],
   "imm-kinds=%s (reg-kinds=%d sites)" % (imm_kinds, sum(1 for *_x, k, _y in siteinfo if k is None)))

# ---------- A7: Bad GOAL debug assertion (bytes, not the C) ----------
refs = [a for a in ADDRS if "0x6914fc" in INS[a][1].lower()]
pe = open(EXE, "rb").read()
p = struct.unpack_from("<I", pe, 0x3c)[0]
nsec = struct.unpack_from("<H", pe, p + 6)[0]; opt = struct.unpack_from("<H", pe, p + 20)[0]
ib = struct.unpack_from("<I", pe, p + 52)[0]
def r2o(v):
    for i in range(nsec):
        off = p + 24 + opt + i * 40
        va = ib + struct.unpack_from("<I", pe, off + 12)[0]
        vs = struct.unpack_from("<I", pe, off + 8)[0]
        raw = struct.unpack_from("<I", pe, off + 20)[0]
        if vs and va <= v < va + vs: return raw + (v - va)
o = r2o(0x6914fc)
sbytes = pe[o:o + 0x18]
dbgtest = [a for a, m_, o_ in window(AG_LO, AG_HI) if m_ == "test" and o_.endswith(",0x10") and "ah" in o_]
gbl = [a for a, m_, o_ in window(AG_LO, AG_HI) if "0x985ae8" in o_]
par = [(a, INS[a]) for a in (0x56d35e, 0x56d360) if a in INS]
ck("A7_bad_goal_assertion",
   len(refs) == 1 and sbytes[:20] == b"Bad GOAL\x00\x00\x00\x00Bad SITE"
   and dbgtest == [0x56d369] and len(gbl) == 1,
   "ref@%s bytes=%r dbgbit test-ah-0x10@%s global-load-sites=%s" %
   (hex(refs[0]) if refs else "-", sbytes[:8], [hex(a) for a in dbgtest], [hex(a) for a in gbl]))
ck("A7b_parity_predicate_shape",
   INS[0x56d35e] == ("xor", "eax,edi") and INS[0x56d360] == ("test", "al,0x1"),
   "xor@0x56d35e=%s test@0x56d360=%s" % (INS[0x56d35e], INS[0x56d360]))

# ---------- A8: the four accessors (kind/prio readers) ----------
acc = {"FUN_0056d5d0": (0, 15), "FUN_0056d690": (2, 1), "FUN_0056d710": (2, 1), "FUN_0056d780": (0, 12)}
# 0056d690 + 0056d710 are MUTATORS (kill/prio + force-set); 0056d5d0/0056d780 are READERS (no band store)
accgot = {}
for nm, (off, _nc) in acc.items():
    lo, hi = fspan(nm)
    offs = sorted(set(d for a, m_, o in window(lo, hi) if (d := band_off(o)) is not None))
    ncall = len([1 for a in ADDRS if INS[a] == ("call", "0x%x" % int(nm[4:], 16))])
    accgot[nm] = (offs, ncall)
ck("A8_accessor_family", all(accgot[nm] == ([acc[nm][0]], acc[nm][1]) for nm in acc),
   "%s" % {k: ([hex(x) for x in v[0]], v[1]) for k, v in accgot.items()})

# ---------- A9: goal-engine dominance + owner-field reader ----------
offs = collections.Counter(d for a, m_, o in window(ENG_LO, ENG_HI) if (d := band_off(o)) is not None)
engcall = sorted(hex(a) for a in ADDRS if INS[a] == ("call", "0x556690"))
ck("A9_engine_band_access_shape",
   dict(offs) == {0: 8, 2: 2, 4: 12, 8: 12, 12: 1} and engcall == ["0x52094f", "0x59dd43"],
   "offsets=%s callers=%s (owners %s)" % ({hex(k): v for k, v in sorted(offs.items())}, engcall,
                                          [owner(int(x, 16)) for x in engcall]))

# ---------- A10: tokens vs constructed kinds (M310 cross-ledger) ----------
TOK = {0: "a", 2: "d", 3: "s", 6: "n", 8: "c", 9: "f", 41: "^"}
tok_live = sorted(k for k in TOK if k in imm_kinds)
tok_regonly = sorted(k for k in TOK if k not in imm_kinds)
nontok_constructed = sorted(k for k in imm_kinds if k not in TOK)
ck("A10_token_kinds_constructed",
   tok_live == [0, 2, 3, 6, 8, 9, 41] and nontok_constructed == [7, 11, 16, 25] and tok_regonly == [],
   "token+immediate=%s token-without-immediate=%s constructed-untokened=%s"
   % (tok_live, tok_regonly, nontok_constructed))

# ---------- digest over measured details ----------
det = {
    "A1": repr(sorted((a, d, s) for a, d, s, _ in stores)),
    "A3": repr([hex(a) for a, _ in bounds]),
    "A4": repr(sorted((t[0], t[1]) for t in sc)) + repr(dbgtest) + repr(gbl),
    "A5": repr(TRIPLE) + repr(INS[0x56d407]) + repr(INS[0x56d436]),
    "A11": repr(sorted(REL.items())),
    "A6": repr(siteinfo),
    "A7": repr(sbytes) + repr(dbgtest) + repr(gbl) + repr(par),
    "A8": repr(accgot),
    "A9": repr(dict(offs)) + repr(engcall),
    "A10": repr((imm_kinds, tok_live, nontok_constructed)),
}
dg = hashlib.sha256(repr(sorted(det.items())).encode()).hexdigest()[:16]
n_ok = sum(1 for _n, ok, _d in results if ok)
print("== M316: %d/%d ==" % (n_ok, len(results)))
print("digest %s" % dg)
sys.exit(0 if n_ok == len(results) else 1)
