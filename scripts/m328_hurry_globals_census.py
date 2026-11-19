#!/usr/bin/env python3
# M328: name the two HURRY-story globals M326 left OPEN (STATIC, zero box).
#   A = ds:0x91c64c = the TURN-START ENERGY SNAPSHOT ("reserve baseline") of the
#       faction in upkeep: FUN_00520540 (upkeep energy settlement) writes
#       A := ENERGY[faction] at 52065d AFTER inter-faction debt payment, BEFORE
#       interest/refund; the HURRY dialog's immediate-pay leg mirrors the cost
#       into A (41a551 read / 41a563 store, M326 T6b); the INFRASTRUCTURE
#       warning FUN_0051fe90 reads it (11*E < 10*A && E < 100) - a branch that
#       is UNREACHABLE at its sole call site under the measured additions-only
#       post-snapshot ENERGY writes (scoped; deeper callees untraced).
#   B = ds:0x920434 = the 'MULTI' SESSION FLAG (noun INFERRED; lifecycle V):
#       boolean {0,1}, 15 writers all mov (14x0, 1x1); the sole 1-writer 57ed04
#       is the FIRST statement of FUN_0057ecf0, reached only via opening-menu
#       switch case 4 (table @580070) or the opening-movie auto-start (arg 1);
#       the SP new-game path 57c550 and the whole .SAV load chain never set it;
#       the save's session blob [91f750,+ce0) ends at 920430 = B-4 (B uncarried);
#       the .SAV opener gates option-init on filename!='multi' && B==0;
#       B!=0 enables diplomacy sync messaging and suppresses local dialogs;
#       cleared by retire/quit/game-over/reset/opening/save-box/MULTIDEBUG.
#       HURRY defers its cost iff B!=0 && 91c62c!=0 (M326 G5) - in a 'multi'
#       session during turn processing; SP always pays immediately.
# Footing: NAMED ## M326/M325/M272/M255; evidence/m326_block224_census.txt:23,26.
# Law: table FIRST then ASSERT; >=1 RIVAL that FAILS on the printed numbers;
# digest hashes the MEASURED detail; declared sets MEASURED not authored.
# Resolver: REUSES M326's reviewed resolver (import m326_block224_census):
# INS/owner/classify/memref/value_of/callers_of/push_refs/pe_bytes/pe_cstr,
# subreg fix included, PLUS two extensions measured this round:
#   (a) sole-def fallback: a register writer whose def-walk leaves an opaque
#       ARG leaf is pinned if the containing function has EXACTLY ONE
#       definition of it before the write and it is xor reg,reg / mov reg,imm
#       (DECLARED model: reducible CFG; the unique def dominates the write);
#   (b) seed scan: registers seeded with the immediate global address, forward
#       scan for stores through them, breaking on partial redefinition
#       (M326 review fix). DECLARED limits: M326's (linear walk <=300 instrs
#       depth<=4, affine over opaque leaves, no CFG proof) + seeds only cover
#       the EXACT immediate (not addr-k arithmetic) + fread dests in registers
#       are opaque unless the resolver pins them.
# Mutants: M328_PATCH addr|mn ops (shared INS), M328_PE_PATCH addr|hex (byte
# overlay for the jump table / fread immediates), M328_ALGO 1=immediate-only
# writer values 2=width-blind 3=cmp-blind (test sites counted as reads)
# 4=no sole-def fallback,
# M328_EVIDENCE_ROOT=<dir>.
# Harness PLANT sites (documented for review_lint L2b; all inside regions the
# instrument walks dynamically): MU4 0x520559 (fold shl inside 520540, walked
# by value_of(520657,esi)); MU6 0x51ff3b (INFRASTRUCTURE push, found by
# has_string(51fe90)); MU7 0x520741 (refund add, found by the post-snapshot
# ENERGY-store scan + add_proven); MU9 0x546887 (diplomacy cmp, inside the
# 546800 ref census); MU10 0x52054c (fold head mov, walked by the same
# value_of); MU13 0x512b63 (sole xor, found by sole_def's reg_defs_between);
# MU14 0x516ef4 (REALLYQUIT push, found by has_string(516b80)); MU17/MU23
# 0x596920 (blob-size push, found by the loader fread-pair scan); MU22
# 0x52280c (B writer, inside the B write census).
import hashlib, os, re, struct, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import m326_block224_census as m326

EV = os.environ.get("M328_EVIDENCE_ROOT", ROOT)
ALGO = os.environ.get("M328_ALGO", "0")
A, B = 0x91c64c, 0x920434
PE_OVER = {}

def apply_patch():
    p = os.environ.get("M328_PATCH")
    n = 0
    if p:
        for chunk in p.split(";"):
            chunk = chunk.strip()
            if not chunk: continue
            addr, rest = chunk.split("|", 1)
            mn, _, ops = rest.partition(" ")
            a = int(addr, 16)
            if a not in m326.INS:
                raise SystemExit("M328_PATCH address not in .text cache: %s" % addr)
            if m326.INS[a] == (mn, ops.strip()):
                raise SystemExit("M328_PATCH applied to nothing (already equal)")
            m326.INS[a] = (mn, ops.strip()); n += 1
    q = os.environ.get("M328_PE_PATCH")
    if q:
        for chunk in q.split(";"):
            chunk = chunk.strip()
            if not chunk: continue
            addr, hx = chunk.split("|", 1)
            PE_OVER[int(addr, 16)] = bytes.fromhex(hx); n += 1
    if p and n == 0: raise SystemExit("M328_PATCH applied to nothing")
    return n

NPATCH = apply_patch()

def pe_bytes(addr, n):
    raw = m326.pe_bytes(addr, n)
    if raw is None: raise SystemExit("pe_bytes out of range: 0x%x" % addr)
    out = bytearray(raw)
    for a, b in PE_OVER.items():
        if a < addr + n and a + len(b) > addr:
            lo = max(a, addr) - addr
            out[lo:lo + len(b)] = b[:n - lo]
    return bytes(out)

def abs_hits(addr):
    hits, sub, disp, brk = [], [], [], []
    for a in m326.ADDRS:
        w, r, width, mi, src = m326.classify(a)
        if mi is None: continue
        if mi[0] == "abs":
            if mi[1] == addr: hits.append((a, w, r, width, src))
            elif mi[1] in (addr + 1, addr + 2, addr + 3): sub.append(a)
        elif mi[0] == "brk" and mi[2] == addr:
            if mi[4] is None: disp.append(a)
            else: brk.append(a)
    return hits, sub, disp, brk

def role(a, w, r):
    mn, _ = m326.INS[a]
    if w: return "W"
    if ALGO == "3":
        return "R"  # cmp-blind classifier: test sites miscounted as reads
    if mn in ("cmp", "test"): return "T"
    return "R" if r else "?"

def sole_def(a, reg):
    fn = None
    for start, name, sz in m326.funcs:
        if start <= a < start + max(sz, 1): fn = (start, start + max(sz, 1)); break
    if fn is None: return None
    defs = m326.reg_defs_between(fn[0] - 1, a, reg)
    if len(defs) != 1: return None
    da, dmn, dops = defs[0]
    parts = m326.split_ops(dops)
    if dmn == "xor" and len(parts) == 2 and parts[0] == parts[1] \
            and m326.reg_of(parts[0]) == reg:
        return ("const", 0)
    if dmn == "mov" and len(parts) == 2 and m326.reg_of(parts[0]) == reg:
        mm = re.fullmatch(r"0x([0-9a-f]+)", parts[1].strip())
        if mm: return ("const", int(mm.group(1), 16))
    return None

def writer_value(a, src):
    if src is None: return ("rmw", None)
    m = re.fullmatch(r"0x([0-9a-f]+)", src.strip())
    if m: return ("const", int(m.group(1), 16))
    if ALGO == "1": return ("opaque", src)
    reg = m326.reg_of(src)
    if reg:
        v = m326.value_of(a, reg)
        if v and v[0] != "opaque":
            if v[0] == "lin" and v[3][0] == "arg" and ALGO != "4":
                sd = sole_def(a, reg)
                if sd is not None: return sd
            return v
        if ALGO != "4":
            sd = sole_def(a, reg)
            if sd is not None: return sd
        return ("opaque", src)
    return ("opaque", src)

def seed_scan(addr):
    seeds, indirect = [], []
    for a in m326.ADDRS:
        mn, ops = m326.INS[a]
        parts = m326.split_ops(ops)
        if len(parts) != 2: continue
        dst = m326.reg_of(parts[0])
        if dst is None: continue
        seeded = False
        if mn == "mov" and re.fullmatch(r"0x%x" % addr, parts[1].strip()):
            seeded = True
        if mn == "lea":
            mi = m326.memref(parts[1])
            if mi and mi[0] == "abs" and mi[1] == addr: seeded = True
        if not seeded: continue
        seeds.append((a, dst))
        full = next((f for f in m326.PARTIALS if dst == f or dst in m326.PARTIALS[f]), dst)
        i = m326.AIDX[a]
        for b in m326.ADDRS[i + 1:i + 400]:
            bmn, bops = m326.INS[b]
            bp = m326.split_ops(bops)
            if not bp: continue
            d = m326.reg_of(bp[0])
            if bmn in m326.STORE_MN and d is not None and \
                    (d == full or d in m326.PARTIALS.get(full, ())):
                break
            if bmn == "call" and full in m326.CALLER_SAVED: break
            if bmn in m326.STORE_MN and bp:
                mi = m326.memref(bp[0])
                if mi and mi[0] == "brk" and mi[3] == dst and mi[4] is None:
                    indirect.append((a, b, mi[2]))
    return seeds, indirect

def census(addr):
    hits, sub, disp, brk = abs_hits(addr)
    rows = []
    for a, w, r, width, src in hits:
        if ALGO == "2": width = 4
        rows.append({"a": a, "role": role(a, w, r), "w": width,
                     "fn": m326.owner(a), "ins": m326.INS[a], "src": src})
    return rows, sub, disp, brk

def fn_pushes(fn):
    lo, hi = fn, fn + m326.FSIZE.get(fn, 0)
    out = []
    for a in m326.ADDRS:
        if a < lo: continue
        if a >= hi: break
        mn, ops = m326.INS[a]
        if mn == "push":
            mm = re.fullmatch(r"0x([0-9a-f]+)", ops.strip())
            if mm: out.append((a, int(mm.group(1), 16)))
    return out

def has_string(fn, s):
    for a, va in fn_pushes(fn):
        if m326.pe_cstr(va) == s.encode(): return a
    return None

def add_proven(a, reg):
    """Most recent definition of reg at/before store a is an addition
    (add/adc/inc/lea) - scanned back <=4 instrs (DECLARED window)."""
    i = m326.AIDX[a]
    for b in reversed(m326.ADDRS[max(0, i - 4):i]):
        bmn, bops = m326.INS[b]
        bp = m326.split_ops(bops)
        if bp and m326.reg_of(bp[0]) == reg and bmn not in ("cmp", "test", "push"):
            return bmn in ("add", "adc", "inc", "lea")
    return False

def main():
    out, det = [], []
    def p(s=""):
        print(s); out.append(s)
    def d(s):
        det.append(s)
    p("== M328 census: A=0x%x B=0x%x (ALGO=%s patch=%d) ==" % (A, B, ALGO, NPATCH))
    data = {}
    for name, addr in (("A", A), ("B", B)):
        rows, sub, disp, brk = census(addr)
        seeds, indirect = seed_scan(addr)
        nw = sum(1 for r in rows if r["role"] == "W")
        nt = sum(1 for r in rows if r["role"] == "T")
        nr = sum(1 for r in rows if r["role"] == "R")
        widths = sorted({r["w"] for r in rows})
        fns = {}
        for r in rows: fns.setdefault(r["fn"], []).append(r)
        p("%s 0x%x: hits=%d W=%d T=%d R=%d widths=%s sub=%d disp=%d brk=%d seeds=%d indirect=%d owners=%d" %
          (name, addr, len(rows), nw, nt, nr, widths, len(sub), len(disp),
           len(brk), len(seeds), len(indirect), len(fns)))
        d("%s|hits=%d|W=%d|T=%d|R=%d|w=%s|sub=%d|disp=%d|brk=%d|seeds=%d|ind=%d|owners=%d" %
          (name, len(rows), nw, nt, nr, widths, len(sub), len(disp), len(brk),
           len(seeds), len(indirect), len(fns)))
        top = sorted(fns.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:12]
        p("  top owners: %s" % ", ".join("%s:%d" % (f, len(v)) for f, v in top))
        d("owners|%s|%s" % (name, ",".join("%s:%d" % (f, len(v)) for f, v in
                                          sorted(fns.items(), key=lambda kv: (-len(kv[1]), kv[0])))))
        sites = ["%06x%s" % (r["a"], r["role"]) for r in rows]
        for i in range(0, len(sites), 64):
            p("  sites: %s" % " ".join(sites[i:i + 64]))
        d("sites|%s|%s" % (name, " ".join(sites)))
        wvals = {}
        for r in rows:
            if r["role"] == "W":
                v = writer_value(r["a"], r["src"])
                p("  W %06x %-16s %s %s -> %s" %
                  (r["a"], r["fn"], r["ins"][0], r["ins"][1], str(v)))
                d("W|%s|%06x|%s|%s|%s|%s" % (name, r["a"], r["fn"],
                  r["ins"][0], r["ins"][1], str(v)))
                wvals[r["a"]] = v
        data[name] = {"rows": rows, "sub": sub, "disp": disp, "brk": brk,
                      "seeds": seeds, "indirect": indirect, "fns": fns,
                      "wvals": wvals, "nw": nw, "nt": nt, "nr": nr}
    # ---- measured structural facts used by the gates ----
    ga, gb = data["A"], data["B"]
    a_sites = {r["a"]: r for r in ga["rows"]}
    b_w = {r["a"]: r for r in gb["rows"] if r["role"] == "W"}
    b_vals = {}
    for a, v in gb["wvals"].items():
        key = str(v)
        b_vals[key] = b_vals.get(key, 0) + 1
    p("B writer-value multiset: %s" % b_vals)
    d("bvalmultiset|%s" % sorted(b_vals.items()))
    # A snapshot fold + value (value queried on the store's ACTUAL source reg)
    fold_esi = m326.value_of(0x520657, "esi")
    snap_src = m326.reg_of(m326.split_ops(m326.INS[0x52065d][1])[1])
    snap_val = m326.value_of(0x52065d, snap_src)
    p("A snapshot: esi@520657=%s ; src@52065d(%s)=%s" % (fold_esi, snap_src, snap_val))
    d("snap|%s|%s" % (fold_esi, snap_val))
    # post-snapshot ENERGY stores in 520540 + callee 4f5a70
    post = []
    for a in m326.ADDRS:
        if a <= 0x52065d or a >= 0x5208ee: continue
        mn, ops = m326.INS[a]
        if "0x94d650" in ops and mn in m326.STORE_MN and "[" in ops.split(",")[0]:
            src = m326.split_ops(ops)[1]
            post.append((a, mn, add_proven(a, m326.reg_of(src))))
    callee_store = None
    for a in m326.ADDRS:
        if 0x4f5a70 <= a < 0x4f5a70 + m326.FSIZE[0x4f5a70]:
            mn, ops = m326.INS[a]
            if "0x94d650" in ops and mn in m326.STORE_MN and "[" in ops.split(",")[0]:
                src = m326.split_ops(ops)[1]
                callee_store = (a, mn, add_proven(a, m326.reg_of(src)))
    p("post-snapshot ENERGY stores (add-proven): %s ; 4f5a70 store: %s" %
      ([("%06x" % a, mn, ok) for a, mn, ok in post],
       ("%06x" % callee_store[0], callee_store[1], callee_store[2]) if callee_store else None))
    d("post|%s|callee|%s" % ([("%06x" % a, mn, ok) for a, mn, ok in post], callee_store))
    # upkeep call order
    upk_calls = [(a, m326.INS[a]) for a in m326.ADDRS
                 if 0x5208f0 <= a < 0x5208f0 + m326.FSIZE[0x5208f0]
                 and m326.INS[a][0] == "call" and
                 m326.INS[a][1] in ("0x520540", "0x51fe90")]
    p("upkeep calls: %s" % [("%06x" % a, t) for a, (mn, t) in upk_calls])
    d("upkcalls|%s" % [("%06x" % a, t) for a, (mn, t) in upk_calls])
    # B entry path: switch table + callers
    tab = [struct.unpack("<I", pe_bytes(0x580070 + 4 * k, 4))[0] for k in range(6)]
    p("switch table @580070 cases0-5: %s" % ["0x%x" % t for t in tab])
    d("table|%s" % ["0x%x" % t for t in tab])
    callers57 = m326.callers_of(0x57ecf0)
    p("57ecf0 callers: %s" % ["%06x(%s)" % (a, m326.owner(a)) for a in callers57])
    d("callers57|%s" % ["%06x" % a for a in callers57])
    sp_writers = [a for a in b_w if m326.owner(a) == "FUN_0057c550"]
    # loader fread pairs (dest, size) with immediate dests
    pairs, regdests = [], []
    lo, hi = 0x596850, 0x596850 + m326.FSIZE[0x596850]
    for a in m326.ADDRS:
        if a < lo: continue
        if a >= hi: break
        mn, ops = m326.INS[a]
        if mn == "call" and ops in ("0x64cc00", "0x64c9a0"):
            i = m326.AIDX[a]
            pushes = []
            for b in m326.ADDRS[max(0, i - 6):i]:
                pmn, pops = m326.INS[b]
                if pmn == "push": pushes.append(pops)
            if len(pushes) >= 2:
                dmm = re.fullmatch(r"0x([0-9a-f]+)", pushes[-1].strip())
                smm = re.fullmatch(r"0x([0-9a-f]+)", pushes[-2].strip())
                if dmm and smm:
                    pair = (int(dmm.group(1), 16), int(smm.group(1), 16))
                    if pair not in [(dst, sz) for dst, sz, _ in pairs]:
                        pairs.append((pair[0], pair[1], a))
                else:
                    regdests.append((a, pushes[-2:]))
    p("loader immediate fread (dest,size): %s" %
      [("0x%x" % dst, "0x%x" % sz, "%06x" % a) for dst, sz, a in pairs])
    p("loader register-dest freads (opaque): %d" % len(regdests))
    d("freads|%s|regdests=%d" % ([("0x%x" % dst, "0x%x" % sz) for dst, sz, a in pairs], len(regdests)))
    blob = [(dst, sz) for dst, sz, a in pairs if dst == 0x91f750]
    cover = [(dst, sz) for dst, sz, a in pairs if dst <= B < dst + sz]
    cover_a = [(dst, sz) for dst, sz, a in pairs if dst <= A < dst + sz]
    # opener 'multi' gate
    multi_push = has_string(0x597ee0, "multi")
    opener_reads = [r["a"] for r in gb["rows"] if r["fn"] == "FUN_00597ee0"]
    p("opener: 'multi' push=%s B-reads=%s" %
      ("%06x" % multi_push if multi_push else None, ["%06x" % a for a in opener_reads]))
    d("opener|%s|%s" % (multi_push, ["%06x" % a for a in opener_reads]))
    # lifecycle strings in writer functions
    life = {"FUN_0050fea0": "Retire*****************************",
            "FUN_00516b80": "REALLYQUIT",
            "FUN_0051e700": "YOULOSE2", "FUN_00522240": "MULTIDEBUG",
            "FUN_00522850": "opening", "FUN_005985e0": "SAVEFAILED"}
    life_sites = {}
    for fn, s in life.items():
        f = int(fn.replace("FUN_00", ""), 16)
        life_sites[fn] = has_string(f, s)
    p("lifecycle strings: %s" % {k: ("%06x" % v if v else None) for k, v in life_sites.items()})
    d("life|%s" % sorted((k, v) for k, v in life_sites.items()))
    # reader shape: diplomacy send branch + HURRY gate re-check
    dip_refs = len(gb["fns"].get("FUN_00546800", []))
    send_call = m326.INS.get(0x546c77)
    hurry_gate = [m326.INS[a] for a in (0x41a530, 0x41a535, 0x41a537) if a in m326.INS]
    p("diplomacy 546800 refs=%d ; 546c77=%s ; hurry-gate window=%s" %
      (dip_refs, send_call, hurry_gate))
    d("dip|%d|%s|%s" % (dip_refs, send_call, hurry_gate))
    # ---- GATES ----
    checks = []
    def gate(gid, ok, msg):
        checks.append((gid, ok, msg))
        p("%s %s %s" % (gid, "PASS" if ok else "FAIL", msg))
    gate("G1", len(ga["rows"]) == 4 and ga["nw"] == 2 and ga["nt"] == 0 and
         ga["nr"] == 2 and sorted(a_sites) == [0x41a551, 0x41a563, 0x51ff00, 0x52065d]
         and not ga["sub"] and not ga["disp"] and not ga["brk"] and not ga["seeds"]
         and {r["w"] for r in ga["rows"]} == {4},
         "A census 4 hits 2W/0T/2R dw abs, sites pinned, 0 sub/disp/brk/seeds")
    gate("G2", fold_esi == ("lin", 8380, 0, ("ptr", ("brk", 8, "ebp", None, 1))) and
         snap_val == ("lin", 1, 0, ("ptr", ("brk", 0x94d650, "esi", None, 1))) and
         a_sites[0x52065d]["fn"] == "FUN_00520540" and
         a_sites[0x41a563]["fn"] == "FUN_00419c30",
         "A snapshot := ENERGY[faction] (esi=8380*arg fold); writers 520540/419c30")
    gate("G3", m326.INS.get(0x51fef8) == ("lea", "edx,[ecx+ecx*4]") and
         m326.INS.get(0x51fefb) == ("lea", "ecx,[ecx+edx*2]") and
         m326.INS.get(0x51ff06) == ("lea", "ecx,[ecx+ecx*4]") and
         m326.INS.get(0x51ff09) == ("shl", "ecx,1") and
         m326.INS.get(0x51ff0b) == ("sub", "edx,ecx") and
         m326.INS.get(0x51ff0d) == ("jns", "0x520532") and
         has_string(0x51fe90, "INFRASTRUCTURE") is not None and
         has_string(0x51fe90, "INFRASTRUCTURE2") is not None,
         "A reader = INFRASTRUCTURE warning 11E-10A jns; strings pinned")
    adds_ok = all(ok for a, mn, ok in post) and \
              callee_store is not None and callee_store[2]
    gate("G4", len(post) == 4 and adds_ok and
         [a for a, t in upk_calls] == [0x52091a, 0x520939] and
         all(t == "0x520540" for a, (mn, t) in upk_calls[:1]) and
         all(t == "0x51fe90" for a, (mn, t) in upk_calls[1:]),
         "snapshot precedes 4 additions-only ENERGY stores (+4f5a70 add); upkeep order 520540->51fe90 => warning branch unreachable (scoped)")
    gate("G5", len(gb["rows"]) == 634 and gb["nw"] == 15 and
         gb["nt"] == 133 and gb["nr"] == 486 and len(gb["fns"]) == 237 and
         not gb["sub"] and not gb["disp"] and not gb["brk"] and not gb["seeds"]
         and {r["w"] for r in gb["rows"]} == {4},
         "B census 634 hits 15W/133T/486R dw abs 237 owners, 0 sub/disp/brk/seeds")
    first_ok = 0x57ed04 - 0x57ecf0 < 0x20 and not any(
        m326.INS[a][0].startswith("j") for a in m326.ADDRS
        if 0x57ecf0 <= a < 0x57ed04)
    gate("G6", all(r["ins"][0] == "mov" for r in b_w.values()) and
         b_vals == {"('const', 0)": 14, "('const', 1)": 1} and
         gb["wvals"].get(0x57ed04) == ("const", 1) and first_ok and
         gb["wvals"].get(0x515ad8) == ("const", 0) and
         gb["wvals"].get(0x515fb1) == ("const", 0),
         "B values {0x14,1x1}; sole 1 = 57ecf0 first statement; 512b40 pair pinned 0 via sole-def")
    gate("G7", all(v is not None for v in life_sites.values()) and
         set(m326.owner(a) for a in b_w) >= set(life) | {"FUN_0057ecf0", "FUN_0059ec90", "FUN_00512b40"},
         "lifecycle strings pinned in writer fns (Retire/REALLYQUIT/YOULOSE2/MULTIDEBUG/opening/SAVEFAILED)")
    gate("G8", tab[4] == 0x57fcf9 and tab[0] == 0x57fa19 and tab[1] == 0x57fa19 and
         tab[2] == 0x57fa99 and tab[3] == 0x57fa39 and tab[5] == 0x57fd04 and
         sorted(callers57) == [0x5229b7, 0x57fcfa] and
         m326.INS.get(0x57fcfa) == ("call", "0x57ecf0") and
         m326.INS.get(0x57fa22) == ("call", "0x57e890") and
         m326.callers_of(0x57c550) and not sp_writers,
         "B entry: menu switch case4 -> 57ecf0 (callers {5229b7,57fcfa}); SP path 57c550 writes no B")
    gate("G9", blob == [(0x91f750, 0xce0)] and 0x91f750 + 0xce0 == B - 4 and
         not cover and not cover_a and
         (0x92046c, 4) in [(dst, sz) for dst, sz, a in pairs] and
         multi_push == 0x5981c1 and sorted(opener_reads) == [0x59800a, 0x5981d3] and
         m326.INS.get(0x5981d8) == ("test", "eax,eax") and
         m326.INS.get(0x5981da) == ("jne", "0x598221") and
         m326.INS.get(0x5981ec) == ("or", "edx,0x10c0"),
         "B uncarried: session blob ends B-4; opener 'multi' gate B==0 -> option-init 0x10c0")
    gate("G10", dip_refs == 40 and send_call == ("call", "0x584010") and
         m326.INS.get(0x546c5a) == ("je", "0x546c90") and
         hurry_gate == [("mov", "eax,ds:0x920434"), ("test", "eax,eax"), ("je", "0x41a54b")],
         "B reader shape: diplomacy 40 refs, B!=0 -> send 584010; HURRY gate load/test/je re-pinned")
    # ---- RIVALS (must FAIL on the printed numbers) ----
    gate("R1", not ga["brk"] and not ga["disp"] and len(ga["rows"]) > 0 and
         all("[" not in r["ins"][1] for r in ga["rows"]),
         "RIVAL 'A=per-faction block field' FAILS: 0 bracket/fold accesses, pure absolute")
    gate("R2", all(r["ins"][0] == "mov" for r in b_w.values()) and
         set(b_vals) == {"('const', 0)", "('const', 1)"},
         "RIVAL 'B=counter' FAILS: 0 arithmetic writers, value set {0,1} only")
    gate("R3", not any(m326.owner(a) in ("FUN_00596850", "FUN_00597ee0") for a in b_w)
         and not cover,
         "RIVAL 'B set on LOAD (game-active)' FAILS: no loader writer, blob excludes B (M272: 57ecf0 not on load)")
    gate("R4", not any(r["fn"] == "FUN_0051fe90" and r["role"] == "W" for r in ga["rows"]),
         "RIVAL 'warning fn writes A' FAILS: 51fe90 is read-only on A")
    npass = sum(1 for _, ok, _ in checks if ok)
    p("== M328: %d/%d ==" % (npass, len(checks)))
    dig = hashlib.sha256("\n".join(det).encode()).hexdigest()[:16]
    p("digest %s" % dig)
    return 0 if npass == len(checks) else 1

if __name__ == "__main__":
    sys.exit(main())