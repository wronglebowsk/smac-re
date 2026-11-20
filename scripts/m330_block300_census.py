#!/usr/bin/env python3
"""M330 (chain2 s9): block+0x300 census — the upkeep SPEND-ACCUMULATOR lead (M325 OPEN).

STATIC, zero box. Reuses M326's reviewed resolver (import m326_block224_census,
subreg-aware affine backward evaluator + lea-seed scan), retargeted to OFF=0x300
(family addrs 0x94d730 + k*0x20bc). M328's import-patch pattern: M330_PATCH env
applies instruction patches to m326.INS AFTER import; every patched site is
LITERAL-read by an exact-address pin below (review_lint L2b, M328 lesson).

Footing: NAMED ## M325/M326/M324/M320/M308; the refund window 520714-52078f:
  gate: bit (1<<[ebp-4]) in BYTE ds:0x985b10; ds:0x985aec > 3; field != 0
  diff==4: ENERGY += trunc(field/3);  diff>=5: ENERGY += trunc(2*field/3)
  both:    field -= refund  (magic 0x55555556 signed-div-3, sign-fix shr 0x1f)
  entry:   52056d zeroes field (with +2fc/+308/+3f8) at upkeep start.

Acceptance: python3 -u scripts/m330_block300_census.py  -> table FIRST, then
gates, digest; re-run must be byte-identical. Mutants: scripts/m330_mutate.py.
"""
import hashlib, os, re, struct, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import m326_block224_census as m326

OFF = 0x300
BLKBASE, STRIDE, NBLK = 0x94d430, 0x20bc, 8
FADDRS = [BLKBASE + OFF + k * STRIDE for k in range(NBLK)]
ENERGY_OFF = 0x220
EADDRS = [BLKBASE + ENERGY_OFF + k * STRIDE for k in range(NBLK)]

# retarget the shared resolver/census/seed machinery at the +300 family
m326.OFF = OFF
m326.FADDRS = FADDRS
m326.ENERGY_OFF = ENERGY_OFF
m326.EADDRS = EADDRS

# ---- M330_PATCH: apply to m326.INS after import (M328 pattern) ----
def apply_patch():
    p = os.environ.get("M330_PATCH")
    n = 0
    if p:
        for chunk in p.split(";"):
            chunk = chunk.strip()
            if not chunk: continue
            addr, rest = chunk.split("|", 1)
            mn, _, ops = rest.partition(" ")
            a = int(addr, 16)
            if a not in m326.INS:
                raise SystemExit("M330_PATCH address not in .text cache: %s" % addr)
            if m326.INS[a] == (mn, ops.strip()):
                raise SystemExit("M330_PATCH applied to nothing (already equal)")
            m326.INS[a] = (mn, ops.strip()); n += 1
        if n == 0: raise SystemExit("M330_PATCH applied to nothing")
    return n

NPATCH = apply_patch()

def ins(a):
    return m326.INS[a]

def ops(a):
    return m326.split_ops(ins(a)[1])

def imm(a):
    """immediate of mov reg,imm at a (None if not that shape)."""
    mn, o = ins(a)
    if mn != "mov": return None
    parts = m326.split_ops(o)
    if len(parts) != 2 or not m326.reg_of(parts[0]): return None
    m = re.fullmatch(r"0x([0-9a-f]+)", parts[1].strip())
    return int(m.group(1), 16) if m else None

ROWS = []   # printed table rows (digest input)
GATES = []

def row(s):
    ROWS.append(s)
    print(s)

def gate(name, ok, detail):
    GATES.append((name, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", name, detail))

def digest():
    h = hashlib.sha256("\n".join(ROWS).encode()).hexdigest()[:16]
    return h

# ---------------- G1: census shape ----------------
def g1_census():
    hits = m326.census()
    seeds, accesses = m326.seed_scan()
    W = [h for h in hits if h[1]]
    R = [h for h in hits if h[2] and not h[1]]
    T = [h for h in hits if h[1] and h[2]]
    tags = {}
    for h in hits:
        t = h[4].split("0")[0] if h[4][:3] == "ABS" else h[4]
        tags[t] = tags.get(t, 0) + 1
    row("G1 census: hits=%d W=%d R=%d T=%d seeds=%d seed-accesses=%d tags=%s"
        % (len(hits), len(W), len(R), len(T), len(seeds), len(accesses),
           sorted(tags.items())))
    for a, w, r, width, tag, mi, src in hits:
        row("  hit %06x %s%s w=%d tag=%s src=%s owner=%s"
            % (a, "W" if w else "-", "R" if r else "-", width, tag, src,
               m326.owner(a)))
    for a, dest, tgt in seeds:
        row("  seed %06x ->%s tgt=%s" % (a, dest, tgt))
    for a, dest, b, w, width, d, ea, hit_off, src, stag in accesses:
        row("  seedacc %06x %s[%s%+d]=%06x w=%d off=%s" % (a, dest, "", d, ea, w, hit_off))
    return hits, seeds, accesses

# ---------------- G2/G3: writer / reader roles (exact pins) ----------------
# Every census hit address is literal-read here via ins(a) — L2b-safe.
def g23_roles(hits):
    waddrs = sorted(h[0] for h in hits if h[1])
    raddrs = sorted(h[0] for h in hits if h[2] and not h[1])
    wroles = []
    for a in waddrs:
        mn, o = ins(a)
        wroles.append((a, mn, o))
        row("G2 writer %06x: %s %s" % (a, mn, o))
    for a in raddrs:
        mn, o = ins(a)
        row("G3 reader %06x: %s %s" % (a, mn, o))
    return wroles, raddrs

# ---------------- G4: refund-fraction law from bytes ----------------
MAGIC = 0x55555556
# exact-address pins (all literal-read; mutants patch these)
P_MAGIC = [0x52072d, 0x52074f, 0x52075a, 0x52077c]      # mov eax,0x55555556
P_IMUL = {0x520732: "ecx", 0x520754: "ecx", 0x52075f: "ecx", 0x520784: "edx"}
P_SIGNFIX = [(0x520734, 0x520736, 0x520739),            # mov eax,edx/shr 1f/add edx,eax
             (0x520767, 0x520769, 0x52076c),            # mov ecx,edx/shr 1f/add edx,ecx
             (0x520786, 0x520788, 0x52078b)]
P_K5 = [0x520758, 0x520781]                             # add ecx,ecx / lea edx,[ecx+ecx*1]
P_ELOAD = [0x52073b, 0x520761]                          # mov eax,[esi+0x94d650]
P_EADD = [0x520741, 0x52076e]                           # add eax,edx
P_ESTORE = [0x520743, 0x520770]                         # mov [esi+0x94d650],eax
P_RESID = [0x52078d, 0x52078f]                          # sub ecx,edx / mov [esi+0x94d730],ecx
P_FLOAD = [0x52071e, 0x520749, 0x520776]                # mov ecx,[esi+0x94d730]

def magic_div3(x):
    """model of imul-magic + sign-fix: trunc(x/3) toward zero."""
    prod = x * MAGIC
    hi = prod >> 32                      # arithmetic shift = floor(prod / 2^32)
    return hi + (1 if hi < 0 else 0)     # shr eax,0x1f + add edx,eax

def g4_law():
    magics = [imm(a) for a in P_MAGIC]
    imul_ok = all(ins(a) == ("imul", r) for a, r in P_IMUL.items())
    sf_ok = True
    for m1, s1, a1 in P_SIGNFIX:
        mn1, o1 = ins(m1); mn2, o2 = ins(s1); mn3, o3 = ins(a1)
        ok = (mn1 == "mov" and mn2 == "shr" and o2.endswith("0x1f") and mn3 == "add")
        sf_ok = sf_ok and ok
    k5 = [ins(a) for a in P_K5]
    k5_ok = (k5[0] == ("add", "ecx,ecx")
             and k5[1][0] == "lea" and "ecx+ecx" in k5[1][1])
    eload_ok = all(ins(a)[0] == "mov" and "0x94d650" in ins(a)[1]
                   and ins(a)[1].startswith("eax,") for a in P_ELOAD)
    estore_ok = all(ins(a)[0] == "mov" and "0x94d650" in ins(a)[1]
                    and ins(a)[1].endswith(",eax") for a in P_ESTORE)
    eadd_ok = all(ins(a) == ("add", "eax,edx") for a in P_EADD)
    resid_ok = (ins(P_RESID[0]) == ("sub", "ecx,edx")
                and ins(P_RESID[1])[0] == "mov"
                and "0x94d730" in ins(P_RESID[1])[1]
                and ins(P_RESID[1])[1].endswith(",ecx"))
    fload_ok = all(ins(a)[0] == "mov" and "0x94d730" in ins(a)[1]
                   and ins(a)[1].startswith("ecx,") for a in P_FLOAD)
    # numeric model vs trunc division, incl. negatives
    xs = [-100, -7, -4, -3, -1, 0, 1, 2, 3, 4, 5, 7, 10, 100, 999999]
    model_ok = all(magic_div3(x) == int(x / 3) for x in xs)
    r4 = {x: magic_div3(x) for x in xs}
    r5 = {x: magic_div3(2 * x) for x in xs}
    row("G4 law: magics=%s imul=%s signfix=%s k5=%s E-load/add/store=%s/%s/%s "
        "resid=%s fload=%s model=%s" % (["%x" % m if m is not None else None for m in magics],
        imul_ok, sf_ok, k5_ok, eload_ok, eadd_ok, estore_ok, resid_ok, fload_ok, model_ok))
    row("G4 samples x: r4=trunc(x/3) r5=trunc(2x/3) residue=x-r: %s"
        % [(x, r4[x], r5[x], x - r4[x], x - r5[x]) for x in (1, 2, 3, 4, 5, 7, 10)])
    ok = (all(m == MAGIC for m in magics) and imul_ok and sf_ok and k5_ok
          and eload_ok and eadd_ok and estore_ok and resid_ok and fload_ok and model_ok)
    gate("G4", ok, "refund=trunc(k*x/3) k=1(diff4)/2(diff5+); ENERGY+=r; field-=r; "
         "magic %x, sign-fix, residue SUB (not zero)" % MAGIC)
    return ok

# ---------------- G5: difficulty switch ----------------
def g5_switch():
    src = ins(0x520714)                    # mov eax,ds:0x985aec
    cmp3 = ins(0x520719)                   # cmp eax,0x3
    jle = ins(0x52071c)                    # jle 0x520795
    cmp4 = ins(0x520728)                   # cmp eax,0x4
    jne = ins(0x52072b)                    # jne 0x520758
    je0 = ins(0x520726)                    # je 0x520795 (field==0 skip)
    cmp0 = ins(0x520724)                   # cmp ecx,ebx
    ok = (src == ("mov", "eax,ds:0x985aec") and cmp3 == ("cmp", "eax,0x3")
          and jle[0] == "jle" and "0x520795" in jle[1]
          and cmp4 == ("cmp", "eax,0x4") and jne[0] == "jne" and "0x520758" in jne[1]
          and cmp0 == ("cmp", "ecx,ebx") and je0[0] == "je" and "0x520795" in je0[1])
    row("G5 switch: %s | %s | %s | %s | %s | %s | %s"
        % (src, cmp3, jle, cmp4, jne, cmp0, je0))
    gate("G5", ok, "ds:0x985aec>3 gate; ==4 -> 1/3 path else (>=5) -> 2/3 path; "
         "field==0 skip; noun 'difficulty' INFERRED (M308 enum)")
    return ok

# ---------------- G6: faction-mask gate is VACUOUS (cl ends at NBLK=8) ----------------
# [ebp-4] def chain: 1 @520586, loop tail inc @52062e + store @520635;
# loop ebx: 0x94f70c @520589, +0x20bc @520628, bound cmp 0x95dc30 @52062f.
P_LOOP = {0x52057e: ("mov", "ecx,0x1"), 0x520586: ("mov", "DWORD PTR [ebp-0x4],ecx"),
          0x520589: ("mov", "ebx,0x94f70c"), 0x520628: ("add", "ebx,0x20bc"),
          0x52062e: ("inc", "ecx"), 0x52062f: ("cmp", "ebx,0x95dc30"),
          0x520635: ("mov", "DWORD PTR [ebp-0x4],ecx")}
def g6_mask():
    ld = ins(0x520700)                     # mov al,ds:0x985b10
    one = ins(0x520705)                    # mov edx,0x1
    shl = ins(0x52070a)                    # shl edx,cl
    test = ins(0x52070c)                   # test dl,al
    jne = ins(0x52070e)                    # jne 0x520795
    clsrc = ins(0x5206fd)                  # mov ecx,[ebp-0x4]
    shape_ok = (ld == ("mov", "al,ds:0x985b10") and one == ("mov", "edx,0x1")
                and shl == ("shl", "edx,cl") and test == ("test", "dl,al")
                and jne[0] == "jne" and "0x520795" in jne[1]
                and clsrc == ("mov", "ecx,DWORD PTR [ebp-0x4]"))
    loop_ok = all(ins(a) == t for a, t in P_LOOP.items())
    iters = (0x95dc30 - 0x94f70c) // STRIDE      # 7 (blocks 1..7)
    cl_final = 1 + iters                          # 8 = NBLK
    bitbyte = (1 << cl_final) & 0xff              # 0 -> test dl,al always 0
    row("G6 mask: %s | %s | %s | %s | %s | %s | loop=%s iters=%d cl_final=%d (1<<cl)&0xff=%d"
        % (ld, one, shl, test, jne, clsrc, loop_ok, iters, cl_final, bitbyte))
    ok = shape_ok and loop_ok and iters == NBLK - 1 and cl_final == NBLK and bitbyte == 0
    gate("G6", ok, "mask gate VACUOUS: [ebp-4]=1+7=8 at refund (loop bound pinned); "
         "1<<8 has dl=0 -> test dl,al always 0 -> jne never taken; refund NOT faction-masked")
    return ok

# ---------------- G7: entry zeroing ----------------
P_ZERO = {0x520561: 0x94d828, 0x520567: 0x94d72c, 0x52056d: 0x94d730, 0x520573: 0x94d738}
def g7_zero():
    x = ins(0x520557)                      # xor eax,eax
    ok = x == ("xor", "eax,eax")
    det = []
    for a, disp in sorted(P_ZERO.items()):
        mn, o = ins(a)
        good = mn == "mov" and o == "DWORD PTR [esi+0x%x],eax" % disp
        ok = ok and good
        det.append("%06x:+%x=%s" % (a, disp - BLKBASE, "0" if good else "?"))
    row("G7 entry-zero: %s | %s" % (x, " ".join(det)))
    gate("G7", ok, "upkeep entry 520540 zeroes +3f8/+2fc/+300/+308 (eax=0 xor@520557); "
         "+300 accumulates WITHIN the upkeep pass before the refund")
    return ok

# ---------------- G8: save carry ----------------
def g8_carry():
    sv = m326.save_values()
    if sv is None:
        gate("G8", False, "save parse failed")
        return False
    # raw block carry pinned by M324 G3: fread 596a91 <- 94d430 sz 105e0
    rd = ins(0x596a91) if 0x596a91 in m326.INS else None
    vals = sv["vals"]
    foffs = [sv["off"] + k * STRIDE + OFF for k in range(NBLK)]
    row("G8 carry: blockA@%x vals=%s foffs=%s energy=%s sha=%s round=%d fread@596a91=%s"
        % (sv["off"], vals, foffs, sv["energy"], sv["sha"], sv["round"], rd))
    ok = (len(vals) == NBLK and rd is not None)
    gate("G8", ok, "+300 inside raw block carry (M324: 596a91 105e0/94d430); "
         "values measured from m54b_clean")
    return ok

# ---------------- G9: turnfn ----------------
def g9_turnfn():
    ts = m326.turnfn_stores()
    blk = m326.turnfn_blkstores(ts)
    row("G9 turnfn: stores=%d blkstores=%d" % (len(ts), len(blk)))
    gate("G9", len(blk) == 0, "turnfn 51f320 writes no block field (as +220/+224)")
    return len(blk) == 0

# ---------------- R: rivals (must FAIL on the printed numbers) ----------------
def rivals():
    # R1: refund fraction is 1/2 (would need shr-by-1 or magic 0x66666667-ish /2)
    r1 = all(imm(a) == MAGIC for a in P_MAGIC) and all(
        ins(a)[0] == "imul" for a in P_IMUL)
    # R2: fraction independent of difficulty (k5 doubling absent)
    r2 = ins(0x520758) == ("add", "ecx,ecx")
    # R3: field zeroed after refund (the +224 law) instead of residue kept
    r3 = ins(0x52078d)[0] == "xor" or ins(0x52078f)[1].endswith(",eax") and imm(0x520557) is None
    # R4: the 985b10 mask gate restricts the refund to a faction subset
    r4 = ((1 << (1 + (0x95dc30 - 0x94f70c) // STRIDE)) & 0xff) != 0
    row("R rivals: R1(half)=%s R2(diff-independent)=%s R3(zeroed)=%s R4(mask-gated)=%s"
        % (r1, r2, r3, r4))
    ok = (not r1) and (not r2) and (not r3) and (not r4)
    gate("R", ok, "R1 half-refund DEAD (magic div3+imul); R2 diff-independent DEAD "
         "(k5 doubling pinned); R3 zero-after DEAD (sub ecx,edx residue); "
         "R4 mask-gated DEAD (cl=8, dl=0)")
    return ok

def main():
    print("== M330 block+300 census (resolver: M326 import, OFF=0x300) patches=%d ==" % NPATCH)
    hits, seeds, accesses = g1_census()
    g23_roles(hits)
    g4_law()
    g5_switch()
    g6_mask()
    g7_zero()
    g8_carry()
    g9_turnfn()
    rivals()
    d = digest()
    npass = sum(1 for _, ok in GATES if ok)
    print("digest %s" % d)
    print("== M330: %d/%d ==" % (npass, len(GATES)))
    return 0 if npass == len(GATES) else 1

if __name__ == "__main__":
    sys.exit(main())