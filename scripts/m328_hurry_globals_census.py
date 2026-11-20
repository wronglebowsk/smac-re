#!/usr/bin/env python3
# M328: name the two HURRY-story globals M326 left OPEN (STATIC, zero box).
#   A = ds:0x91c64c = the TURN-START ENERGY SNAPSHOT ("reserve baseline") of the
#       faction in upkeep: FUN_00520540 (upkeep energy settlement) writes
#       A := ENERGY[faction] at 52065d AFTER inter-faction debt payment, BEFORE
#       interest/refund; the HURRY dialog's immediate-pay leg mirrors the cost
#       into A (41a551 read / 41a563 store, M326 T6b); the INFRASTRUCTURE
#       warning FUN_0051fe90 reads it (11*E < 10*A && E < 100, formula DERIVED
#       by forward symbolic evaluation) - no subtraction exists in the
#       measured post-snapshot window (linear, clobber-aware, scoped; deeper
#       callees untraced), so the warning branch is INFERRED-dead, not proved
#       unreachable (review #336 F3 downgrade).
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
# depth<=4, affine over opaque leaves, no CFG proof) + seed scan covers
# exact/lane/lea-brk seeds (computed pointers beyond that DECLARED out of
# scope) + fread dests in registers
#       are opaque unless the resolver pins them (review F6: the 17 reg-dest
#       freads are resolved and printed; const dests gated against covering
#       A/B; runtime/stack dests DECLARED opaque).
# Review #336 round (7 findings, all accepted): F1 debt/interest ordering
# pinned in G2 (520603 sub + 520605 store < 52065d < 520743, loop bounds);
# F2 warning formula DERIVED (warn_formula forward evaluator) not hardcoded;
# F3 'unreachable' downgraded to INFERRED-dead (scoped window measurement);
# F4 add_proven clobber-aware (call in window -> not proven) + def printed;
# F5 G6 first-STORE pin + exact prologue; F6 reg-dest freads resolved/gated;
# F7 seed scan broadened (lane immediates addr+/-1..3 + lea-brk pointer
# seeds), computed-pointer limits DECLARED. The F2 gate immediately caught
# an evaluator bug: shl k is x2^k, not xk (first derivation printed 11E-5A).
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
# L2b round (s305): exact-address pins at the 5 walk-only review-mutant sites
# (57ecf3 prologue, 52076e add-def, 596af2 fread dest-push, 51f267 lifecycle,
# 5981e2 opener gap) so every cited code mutant touches a LITERAL-read byte.
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
    """Sole-definition fallback: scan the containing function from its start
    to the write; if exactly one instruction defines reg (or a partial of it)
    and it is xor reg,reg / mov reg,imm, the value is pinned. Returns
    (value, (def_addr, def_mn, def_ops)) so the PROVENANCE is gateable
    (review #336 run2 F5)."""
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
        return (("const", 0), (da, dmn, dops))
    if dmn == "mov" and len(parts) == 2 and m326.reg_of(parts[0]) == reg:
        mm = re.fullmatch(r"0x([0-9a-f]+)", parts[1].strip())
        if mm: return (("const", int(mm.group(1), 16)), (da, dmn, dops))
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
                if sd is not None: return sd[0]
            return v
        if ALGO != "4":
            sd = sole_def(a, reg)
            if sd is not None: return sd[0]
        return ("opaque", src)
    return ("opaque", src)

def seed_scan(addr):
    """Indirect-write census (review F7 broadened): registers seeded with
    (a) the EXACT immediate addr, (b) LANE immediates addr+/-1..3, or
    (c) lea reg,[base+addr] pointer forms; forward-scanned for stores through
    that register. Breaks on (partial) redefinition of the seed register
    (M326 review fix). Calls clobber eax/ecx/edx only. DECLARED limit:
    computed pointers (addr-k arithmetic beyond lanes, multi-instruction
    address math, pointer params) are OUT OF SCOPE; the disp/brk census
    catches any [reg+addr] access regardless of how reg was formed."""
    seeds, indirect = [], []
    lanes = {addr + k for k in (-3, -2, -1, 1, 2, 3)}
    for a in m326.ADDRS:
        mn, ops = m326.INS[a]
        parts = m326.split_ops(ops)
        if len(parts) != 2: continue
        dst = m326.reg_of(parts[0])
        if dst is None: continue
        kind = None
        if mn == "mov":
            mm = re.fullmatch(r"0x([0-9a-f]+)", parts[1].strip())
            if mm:
                v = int(mm.group(1), 16)
                if v == addr: kind = "exact"
                elif v in lanes: kind = "lane"
        if mn == "lea":
            mi = m326.memref(parts[1])
            if mi and mi[0] == "abs" and mi[1] == addr: kind = "exact"
            elif mi and mi[0] == "brk" and mi[2] == addr: kind = "lea"
        if kind is None: continue
        seeds.append((a, dst, kind))
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
    (add/adc/inc/lea) - scanned back <=4 instrs (DECLARED window). A CALL
    before the def clobbers caller-saved regs -> NOT proven (review F4).
    Returns (ok, def_addr, def_mn, def_ops)."""
    i = m326.AIDX[a]
    for b in reversed(m326.ADDRS[max(0, i - 4):i]):
        bmn, bops = m326.INS[b]
        if bmn == "call" and reg in m326.CALLER_SAVED:
            return (False, b, bmn, bops)
        bp = m326.split_ops(bops)
        if bp and m326.reg_of(bp[0]) == reg and bmn not in ("cmp", "test", "push"):
            return (bmn in ("add", "adc", "inc", "lea"), b, bmn, bops)
    return (False, None, None, None)

def warn_formula():
    """Forward symbolic evaluation of the INFRASTRUCTURE warning window
    (review F2): E := ecx loaded at 51fee9 from [eax+0x94d650]; A := ecx
    loaded at 51ff00 from ds:A. Expressions are affine tuples (e, a, c) =
    e*E + a*A + c. Window-local, DECLARED; unknown forms fail the gate."""
    if m326.INS.get(0x51fee9) != ("mov", "ecx,DWORD PTR [eax+0x94d650]"): return None
    if m326.INS.get(0x51ff00) != ("mov", "ecx,DWORD PTR ds:0x91c64c"): return None
    regs = {"ecx": (1, 0, 0), "edx": (0, 0, 0)}
    def scale(v, k): return (v[0] * k, v[1] * k, v[2] * k)
    def add(v, w): return (v[0] + w[0], v[1] + w[1], v[2] + w[2])
    def sub(v, w): return (v[0] - w[0], v[1] - w[1], v[2] - w[2])
    def ev(op):
        op = op.strip()
        if op in regs: return regs[op]
        m = re.fullmatch(r"\[(\w+)\+(\w+)\*(\d+)\]", op)
        if m and m.group(1) in regs and m.group(2) in regs:
            return add(regs[m.group(1)], scale(regs[m.group(2)], int(m.group(3))))
        return None
    for a in (0x51fef8, 0x51fefb, 0x51fefe, 0x51ff00, 0x51ff06, 0x51ff09, 0x51ff0b):
        mn, ops = m326.INS[a]
        parts = m326.split_ops(ops)
        if a == 0x51ff00:
            regs["ecx"] = (0, 1, 0); continue
        if mn in ("mov", "lea"):
            v = ev(parts[1])
            if v is None or parts[0] not in regs: return None
            regs[parts[0]] = v
        elif mn == "shl" and parts[0] in regs:
            regs[parts[0]] = scale(regs[parts[0]], 2 ** int(parts[1], 0))
        elif mn == "sub" and parts[0] in regs:
            v = ev(parts[1])
            if v is None: return None
            regs[parts[0]] = sub(regs[parts[0]], v)
        else:
            return None
    return regs["edx"], regs["ecx"]

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
            ok, da, dmn, dops = add_proven(a, m326.reg_of(src))
            post.append((a, mn, ok, da, "%s %s" % (dmn, dops)))
    callee_store = None
    for a in m326.ADDRS:
        if 0x4f5a70 <= a < 0x4f5a70 + m326.FSIZE[0x4f5a70]:
            mn, ops = m326.INS[a]
            if "0x94d650" in ops and mn in m326.STORE_MN and "[" in ops.split(",")[0]:
                src = m326.split_ops(ops)[1]
                ok, da, dmn, dops = add_proven(a, m326.reg_of(src))
                callee_store = (a, mn, ok, da, "%s %s" % (dmn, dops))
    p("post-snapshot ENERGY stores (add-proven, clobber-aware): %s" %
      [("%06x" % a, mn, ok, "%06x" % da if da else None, di) for a, mn, ok, da, di in post])
    p("4f5a70 store: %s" % str(("%06x" % callee_store[0], callee_store[1], callee_store[2],
                               "%06x" % callee_store[3], callee_store[4]) if callee_store else None))
    d("post|%s|callee|%s" % ([("%06x" % a, mn, ok, "%06x" % da if da else None, di)
                              for a, mn, ok, da, di in post], callee_store))
    # warning formula, DERIVED by forward symbolic evaluation (review F2)
    wf = warn_formula()
    p("warning formula derived (edx,ecx)@51ff0b: %s" % (wf,))
    d("warnformula|%s" % (wf,))
    # debt-pay / interest ordering around the snapshot (review F1)
    order = {"debt_sub": m326.INS.get(0x520603), "debt_store": m326.INS.get(0x520605),
             "loop_add": m326.INS.get(0x520628), "loop_cmp": m326.INS.get(0x52062f)}
    order_ok = (order["debt_sub"] == ("sub", "edx,ecx") and
                order["debt_store"] == ("mov", "DWORD PTR [esi+0x94d650],edx") and
                order["loop_add"] == ("add", "ebx,0x20bc") and
                order["loop_cmp"] == ("cmp", "ebx,0x95dc30") and
                0x520605 < 0x52065d < 0x520743)
    p("snapshot ordering (linear code order): %s ok=%s" % (order, order_ok))
    d("order|%s|%s" % (order, order_ok))
    # 57ecf0 prologue + first-store pin (review F5)
    pro = [(a,) + m326.INS[a] for a in m326.ADDRS if 0x57ecf0 <= a < 0x57ed04]
    stores57 = [a for a in m326.ADDRS
                if 0x57ecf0 <= a < 0x57ecf0 + m326.FSIZE[0x57ecf0]
                and m326.classify(a)[0]]
    first_store_ok = bool(stores57) and min(stores57) == 0x57ed04
    p("57ecf0 prologue: %s ; first store %s (==57ed04: %s)" %
      (pro, "%06x" % min(stores57) if stores57 else None, first_store_ok))
    d("pro|%s|firststore|%s|%s" % (pro, "%06x" % min(stores57) if stores57 else None, first_store_ok))
    # sole-def PROVENANCE for the 512b40 pair (review run2 F5)
    prov = {}
    for wa in (0x515ad8, 0x515fb1):
        sd = sole_def(wa, "ebx")
        prov["%06x" % wa] = sd[1] if sd else None
    p("512b40 sole-def provenance: %s" % prov)
    d("prov|%s" % prov)
    # lifecycle clear mapping: every B write owned by a lifecycle fn must be
    # const 0, and the RESET fn's site is pinned (review run2 F1/F6)
    life = {"FUN_0050fea0": "Retire*****************************",
            "FUN_00516b80": "REALLYQUIT",
            "FUN_0051e700": "YOULOSE2", "FUN_00522240": "MULTIDEBUG",
            "FUN_00522850": "opening", "FUN_005985e0": "SAVEFAILED"}
    life_fns = set(life) | {"FUN_0059ec90"}
    life_writes = [(a, r["fn"], str(gb["wvals"].get(a))) for a, r in b_w.items()
                   if r["fn"] in life_fns]
    life_zero_ok = all(v == "('const', 0)" for a, f, v in life_writes) and \
        any(f == "FUN_0059ec90" for a, f, v in life_writes)
    reset_site = [a for a, r in b_w.items() if r["fn"] == "FUN_0059ec90"]
    p("lifecycle writes (site,fn,value): %s ; all-zero+RESET=%s" % (life_writes, life_zero_ok))
    d("lifewrites|%s|%s" % (life_writes, life_zero_ok))
    # opener gap: exact fallthrough sequence jne@5981da -> or@5981ec, no
    # intervening branch (review run2 F8)
    gap = [(a,) + m326.INS[a] for a in m326.ADDRS if 0x5981da < a <= 0x5981ec]
    gap_ok = gap == [(0x5981dc, "mov", "edx,DWORD PTR ds:0x985ae8"),
                     (0x5981e2, "mov", "DWORD PTR ds:0x91b5b8,0x0"),
                     (0x5981ec, "or", "edx,0x10c0")] and \
        not any(m326.INS[a][0].startswith("j") for a in m326.ADDRS
                if 0x5981da < a < 0x5981ec)
    p("opener fallthrough gap: %s ok=%s" % (gap, gap_ok))
    d("gap|%s|%s" % (gap, gap_ok))
    # no stores between the upkeep's 520540 call and 51fe90 call (run2 F4)
    between = [a for a in m326.ADDRS if 0x52091a < a < 0x520939
               and m326.classify(a)[0]]
    p("stores between upkeep calls (52091a,520939): %s" % ["%06x" % a for a in between])
    d("between|%s" % ["%06x" % a for a in between])
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
    # register-dest freads: resolve the dest (review F6) - const dests are
    # gated against covering B; runtime/stack dests are DECLARED opaque.
    regdest_res = []
    for a, pp in regdests:
        dop = pp[-1].strip()
        reg = m326.reg_of(dop)
        if reg:
            v = m326.value_of(a, reg)
            regdest_res.append((a, dop, str(v)))
        elif re.fullmatch(r"0x[0-9a-f]+", dop):
            regdest_res.append((a, dop, "imm-dest/runtime-size"))
        else:
            regdest_res.append((a, dop, "stack/local"))
    for a, dop, v in regdest_res:
        p("  reg-dest fread %06x: %s -> %s" % (a, dop, v))
    d("regdests|%s" % regdest_res)
    const_cover = []
    for a, dop, v in regdest_res:
        mm = re.fullmatch(r"\('const', (\d+)\)", v)
        if mm:
            dst = int(mm.group(1))
            szm = re.fullmatch(r"0x([0-9a-f]+)", regdests[[x[0] for x in regdests].index(a)][1][0].strip())
            sz = int(szm.group(1), 16) if szm else 0
            if dst <= B < dst + sz or dst <= A < dst + sz:
                const_cover.append((a, dst, sz))
        elif v == "imm-dest/runtime-size":
            # size is runtime, but a dest ABOVE both globals cannot cover
            # either (fread writes [dest, dest+size))
            dst = int(dop, 16)
            if dst <= max(A, B):
                const_cover.append((a, dst, "runtime-size"))
    p("loader register-dest freads: %d (const-cover=%s)" % (len(regdests), const_cover))
    fread_pair_ok = (m326.INS.get(0x596aed) == ("push", "0xe5e0") and
                     m326.INS.get(0x596af2) == ("push", "edi") and
                     m326.INS.get(0x596af3) == ("je", "0x596afc") and
                     m326.INS.get(0x596af5) == ("call", "0x64c9a0") and
                     m326.INS.get(0x596afc) == ("call", "0x64cc00"))
    p("fread branch pair 596af5/596afc (size/dest pushes + je + targets): ok=%s" % fread_pair_ok)
    d("freadpair|%s" % fread_pair_ok)
    d("freads|%s|regdests=%d|constcover=%s" %
      ([("0x%x" % dst, "0x%x" % sz) for dst, sz, a in pairs], len(regdests), const_cover))
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
         a_sites[0x41a563]["fn"] == "FUN_00419c30" and order_ok,
         "A snapshot := ENERGY[faction] (esi=8380*arg fold); writers 520540/419c30; debt-pay(520605) < snapshot < interest(520743) pinned (linear code order)")
    gate("G3", m326.INS.get(0x51feef) == ("cmp", "ecx,0x64") and
         m326.INS.get(0x51fef2) == ("jge", "0x520532") and
         m326.INS.get(0x51fef8) == ("lea", "edx,[ecx+ecx*4]") and
         m326.INS.get(0x51fefb) == ("lea", "ecx,[ecx+edx*2]") and
         m326.INS.get(0x51ff06) == ("lea", "ecx,[ecx+ecx*4]") and
         m326.INS.get(0x51ff09) == ("shl", "ecx,1") and
         m326.INS.get(0x51ff0b) == ("sub", "edx,ecx") and
         m326.INS.get(0x51ff0d) == ("jns", "0x520532") and
         wf == ((11, -10, 0), (0, 10, 0)) and
         has_string(0x51fe90, "INFRASTRUCTURE") is not None and
         has_string(0x51fe90, "INFRASTRUCTURE2") is not None,
         "A reader = INFRASTRUCTURE warning; E<100 gate pinned (cmp 0x64/jge); formula DERIVED edx=11E-10A ecx=10A @51ff0b; strings pinned")
    adds_ok = all(ok for a, mn, ok, da, di in post) and \
              callee_store is not None and callee_store[2]
    defs_ok = [da for a, mn, ok, da, di in post] == \
        [0x520741, 0x52076e, 0x5207d7, 0x5207fe] and \
        callee_store is not None and callee_store[3] == 0x4f5c85
    gate("G4", len(post) == 4 and adds_ok and defs_ok and not between and
         [a for a, t in upk_calls] == [0x52091a, 0x520939] and
         all(t == "0x520540" for a, (mn, t) in upk_calls[:1]) and
         all(t == "0x51fe90" for a, (mn, t) in upk_calls[1:]),
         "no subtraction in measured post-snapshot window (4 stores + 4f5a70, add-proven clobber-aware, def sites 520741/52076e/5207d7/5207fe+4f5c85 pinned; linear, scoped); upkeep 520540->51fe90; warning deadness INFERRED")
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
         first_store_ok and
         pro == [(0x57ecf0, "push", "ebp"), (0x57ecf1, "mov", "ebp,esp"),
                 (0x57ecf3, "sub", "esp,0x2c4"), (0x57ecf9, "push", "ebx"),
                 (0x57ecfa, "push", "esi"), (0x57ecfb, "xor", "esi,esi"),
                 (0x57ecfd, "push", "edi"), (0x57ecfe, "mov", "ebx,0x1"),
                 (0x57ed03, "push", "esi")] and
         gb["wvals"].get(0x515ad8) == ("const", 0) and
         gb["wvals"].get(0x515fb1) == ("const", 0) and
         prov == {"515ad8": (0x512b63, "xor", "ebx,ebx"),
                  "515fb1": (0x512b63, "xor", "ebx,ebx")},
         "B values {0x14,1x1}; sole 1 = 57ed04 = FIRST STORE of 57ecf0 (prologue pinned); 512b40 pair 0 via sole-def xor@512b63 (provenance pinned)")
    life_sites_ok = sorted(a for a, f, v in life_writes) == \
        [0x50fff5, 0x516f30, 0x516fd4, 0x51f267, 0x52280c, 0x52289d,
         0x522993, 0x598db9, 0x5a09ad]
    gate("G7", all(v is not None for v in life_sites.values()) and
         set(m326.owner(a) for a in b_w) >= set(life) | {"FUN_0057ecf0", "FUN_0059ec90", "FUN_00512b40"} and
         life_zero_ok and life_sites_ok and reset_site == [0x5a09ad],
         "lifecycle strings pinned in writer fns; every lifecycle B-write measures 0 at the 9 pinned sites; RESET site 5a09ad (59ec90) pinned")
    gate("G8", tab[4] == 0x57fcf9 and tab[0] == 0x57fa19 and tab[1] == 0x57fa19 and
         tab[2] == 0x57fa99 and tab[3] == 0x57fa39 and tab[5] == 0x57fd04 and
         sorted(callers57) == [0x5229b7, 0x57fcfa] and
         m326.INS.get(0x57fcfa) == ("call", "0x57ecf0") and
         m326.INS.get(0x57fa22) == ("call", "0x57e890") and
         m326.callers_of(0x57c550) and not sp_writers,
         "B entry: menu switch case4 -> 57ecf0 (callers {5229b7,57fcfa}); SP path 57c550 writes no B")
    gate("G9", blob == [(0x91f750, 0xce0)] and 0x91f750 + 0xce0 == B - 4 and
         not cover and not cover_a and not const_cover and
         len(regdests) == 17 and
         (0x92046c, 4) in [(dst, sz) for dst, sz, a in pairs] and
         multi_push == 0x5981c1 and sorted(opener_reads) == [0x59800a, 0x5981d3] and
         m326.INS.get(0x5981d8) == ("test", "eax,eax") and
         m326.INS.get(0x5981da) == ("jne", "0x598221") and
         m326.INS.get(0x5981ec) == ("or", "edx,0x10c0") and gap_ok and
         fread_pair_ok,
         "B uncarried: blob ends B-4; 17 reg-dest freads resolved (runtime/stack, none const-cover); opener 'multi' gate B==0 fallthrough pinned -> option-init 0x10c0")
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