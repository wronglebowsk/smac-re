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
ALGO = os.environ.get("M330_ALGO", "0")   # 1 = provenance filter OFF (algorithm mutant)

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

# ---------------- G1: census shape + provenance ----------------
def g1_census():
    hits = m326.census()
    seeds, accesses = m326.seed_scan()
    field, nonfield = [], []
    for h in hits:
        a, w, r, width, tag, mi, src = h
        if mi[0] == "abs":
            prov = ("ABS", None)
        elif ALGO == "1":
            prov = ("STRIDE", None)     # mutant: trust every disp hit
        else:
            prov = m326.base_tag(a, mi)
        if prov[0] in ("BLKCONST", "STRIDE", "ABS"):
            field.append((h, prov))
        else:
            nonfield.append((h, prov))
    W = [h for h, p in field if h[1]]
    R = [h for h, p in field if h[2] and not h[1]]
    T = [h for h, p in field if h[1] and h[2]]
    provs = {}
    for h, p in field:
        provs[p[0]] = provs.get(p[0], 0) + 1
    row("G1 census: rawhits=%d FIELD=%d (W=%d R=%d T=%d) nonfield=%d seeds=%d "
        "seedacc=%d prov=%s" % (len(hits), len(field), len(W), len(R), len(T),
                                len(nonfield), len(seeds), len(accesses),
                                sorted(provs.items())))
    for (a, w, r, width, tag, mi, src), p in field:
        row("  hit %06x %s%s w=%d tag=%s prov=%s src=%s owner=%s"
            % (a, "W" if w else "-", "R" if r else "-", width, tag, p[0], src,
               m326.owner(a)))
    for (a, w, r, width, tag, mi, src), p in nonfield:
        row("  NONFIELD %06x %s%s tag=%s prov=%s owner=%s"
            % (a, "W" if w else "-", "R" if r else "-", tag, p, m326.owner(a)))
    for a, dest, tgt in seeds:
        if tgt[0] == OFF:
            row("  seed300 %06x ->%s tgt=%s" % (a, dest, tgt))
    for a, dest, b, w, width, d, ea, hit_off, src, stag in accesses:
        if hit_off == OFF:
            row("  seedacc300 %06x %s[%+d]=%06x w=%d" % (a, dest, d, ea, w))
    fW = sorted(h[0][0] for h in field if h[0][1])
    fR = sorted(h[0][0] for h in field if h[0][2] and not h[0][1])
    ok = (len(hits) == 25 and len(field) == 11 and len(nonfield) == 14
          and fW == [0x4f4962, 0x52056d, 0x52078f, 0x59f26a]
          and fR == [0x4f4958, 0x52071e, 0x520749, 0x520776, 0x52082c, 0x5233f3, 0x5362db]
          and provs == {"STRIDE": 11}
          and [(a, t[2]) for a, d, t in seeds if t[0] == OFF]
              == [(0x5233d0, "BLKCONST")]
          and [(a, b, w) for a, d, b, w, wd, dd, ea, ho, s, st in accesses if ho == OFF]
              == [(0x5233d0, 0x5233fe, 0)])
    for a, d, b, w, wd, dd, ea, ho, s, st in accesses:
        if ho == OFF:
            row("  seedacc300 insn %06x: %s" % (b, ins(b)))
    gate("G1", ok, "rawhits=25 FIELD=11 (4W/7R, 11/11 STRIDE) nonfield=14; "
         "1 seed300 (5233d0 BLKCONST block1) + 1 seedacc read @5233fe; exact sets pinned")
    return field, seeds, accesses

# ---------------- G2/G3: writer / reader roles (exact pins) ----------------
# Every census hit address is literal-read here via ins(a) — L2b-safe.
def g23_roles(field):
    waddrs = sorted(h[0][0] for h in field if h[0][1])
    raddrs = sorted(h[0][0] for h in field if h[0][2] and not h[0][1])
    wroles = []
    for a in waddrs:
        mn, o = ins(a)
        wroles.append((a, mn, o))
        row("G2 writer %06x: %s %s" % (a, mn, o))
    for a in raddrs:
        mn, o = ins(a)
        row("G3 reader %06x: %s %s" % (a, mn, o))
    okW = (waddrs == [0x4f4962, 0x52056d, 0x52078f, 0x59f26a]
           and ins(0x4f4962) == ("mov", "DWORD PTR [edi+0x94d730],edx")
           and ins(0x52056d) == ("mov", "DWORD PTR [esi+0x94d730],eax")
           and ins(0x52078f) == ("mov", "DWORD PTR [esi+0x94d730],ecx")
           and ins(0x59f26a) == ("mov", "DWORD PTR [ebx+0x94d730],edx"))
    gate("G2", okW, "4 writers: feeder 4f4962 (edx), entry-zero 52056d (eax=0), "
         "residue 52078f (ecx), reset 59f26a (edx, FUN_0059ec90=M320 RESET)")
    okR = (raddrs == [0x4f4958, 0x52071e, 0x520749, 0x520776, 0x52082c, 0x5233f3, 0x5362db]
           and all(ins(a)[0] in ("mov", "sub") for a in raddrs))
    gate("G3", okR, "7 STRIDE readers: feeder-load 4f4958, refund loads 52071e/749/776, "
         "ledger 52082c, 5233f3 (522b70), 5362db (535c60); +2 arg-fed in G12")
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
    # bound DERIVED from the pinned cmp bytes (tracks mutants), not authored
    bound = int(ins(0x52062f)[1].split(",")[1], 16)
    iters = (bound - 0x94f70c) // STRIDE
    cl_final = 1 + iters
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
    ok = (len(vals) == NBLK and rd == ("call", "0x64cc00")
          and vals == [0, 1, 1, 0, 1, 0, 1, 1]
          and sv["energy"] == [10, 28, 112, 69, 229, 60, 102, 37]   # M325 blkA
          and sv["off"] == 0x32c and sv["round"] == 50
          and foffs == [0x32c + OFF + k * STRIDE for k in range(NBLK)]
          and 0 <= OFF < STRIDE)
    gate("G8", ok, "+300 inside raw block carry (M324: 596a91 105e0/94d430); "
         "m54b_clean vals=[0,1,1,0,1,0,1,1] (residues), energy==M325 blkA, foffs pinned")
    return ok

# ---------------- G9: turnfn ----------------
def g9_turnfn():
    ts = m326.turnfn_stores()
    blk = m326.turnfn_blkstores(ts)
    pin = ins(0x51f53c)                    # ROUND store inside turnfn (M325 G4)
    row("G9 turnfn: stores=%d blkstores=%d pin@51f53c=%s" % (len(ts), len(blk), pin))
    ok = len(blk) == 0 and len(ts) == 16 and pin == ("mov", "ds:0x985afc,eax")
    gate("G9", ok, "turnfn 51f320: 16 stores, 0 block stores (as +220/+224); "
         "ROUND store 51f53c pinned")
    return ok

# ---------------- G10: feeder law (FUN_004f47f0, called ROUND>1) ----------------
# Per slot esi=1..34 whose bit is set in base[68cbb0]'s 5-byte flags 0x95da9c
# (query 507410 = div-8 decomposition, M307): v = DWORD[0x984d48 + 48*esi];
# exemption scan vs profile+0x530 list (count at +0x50c) can zero v;
# if 985ba0>=0 AND base[985ba0].owner==faction: v += flagword bit5, bit5 :=
# parity(v), v = trunc(v/2) (cdq/sub/sar); ELSE v stays FULL (skip branches
# 4f48dc/4f48f8 -> 4f4938). Then ENERGY -= v; +300 += v; ENERGY<0 floor-0
# branch when block+8 <= 1. Call gate: cmp ds:0x985afc,1; jle skip @4f5cc6-cf.
P_FEED = {0x4f48ce: ("mov", "eax,DWORD PTR [eax+0x984d48]"),
          0x4f48d4: ("mov", "ecx,DWORD PTR ds:0x985ba0"),
          0x4f48e9: ("mov", "dl,BYTE PTR [ecx+0x95da14]"),
          0x4f48f1: ("cmp", "edx,ebx"), 0x4f48f3: ("sete", "cl"),
          0x4f4909: ("mov", "ecx,DWORD PTR [edx*4+0x94d430]"),
          0x4f4917: ("mov", "edi,ecx"), 0x4f4919: ("shr", "edi,0x5"),
          0x4f491c: ("and", "edi,0x1"), 0x4f491f: ("add", "eax,edi"),
          0x4f4921: ("test", "al,0x1"), 0x4f4925: ("or", "ecx,0x20"),
          0x4f492e: ("and", "ecx,0xffffffdf"),
          0x4f4931: ("mov", "DWORD PTR [edx],ecx"),
          0x4f4933: ("cdq", ""), 0x4f4934: ("sub", "eax,edx"), 0x4f4936: ("sar", "eax,1"),
          0x4f494a: ("mov", "ecx,DWORD PTR [edi+0x94d650]"),
          0x4f4950: ("sub", "ecx,eax"),
          0x4f4952: ("mov", "DWORD PTR [edi+0x94d650],ecx"),
          0x4f4958: ("mov", "edx,DWORD PTR [edi+0x94d730]"),
          0x4f495e: ("add", "edx,eax"), 0x4f4960: ("xor", "eax,eax"),
          0x4f4962: ("mov", "DWORD PTR [edi+0x94d730],edx"),
          0x4f4968: ("mov", "ecx,DWORD PTR [edi+0x94d650]"),
          0x4f496e: ("cmp", "ecx,eax"),
          0x4f4976: ("cmp", "DWORD PTR [edi+0x94d438],0x1"),
          0x4f497f: ("mov", "DWORD PTR [edi+0x94d650],eax"),
          0x4f5cc6: ("cmp", "DWORD PTR ds:0x985afc,0x1"),
          0x4f5ccf: ("call", "0x4f47f0")}
def g10_feeder():
    ok = all(ins(a) == t for a, t in P_FEED.items())
    jge = ins(0x4f4970); jg = ins(0x4f497d)
    jl1 = ins(0x4f48dc); je1 = ins(0x4f48f8); jle = ins(0x4f5ccd)
    ok = (ok and jge[0] == "jge" and "0x4f4a34" in jge[1]
          and jg[0] == "jg" and "0x4f498a" in jg[1]
          and jl1[0] == "jl" and "0x4f4938" in jl1[1]
          and je1[0] == "je" and "0x4f4938" in je1[1]
          and jle[0] == "jle" and "0x4f5cd4" in jle[1])
    # model: h = trunc(x/2); ENERGY' = E - h; field' = F + h
    xs = [-7, -1, 0, 1, 2, 3, 5, 10, 99]
    halve = {x: x // 2 if x >= 0 else -((-x) // 2) for x in xs}
    model_ok = all(halve[x] == int(x / 2) for x in xs)
    row("G10 feeder: pins=%s skip-halve=%s/%s round-gate=%s halve-model=%s samples=%s"
        % (ok, jl1, je1, jle, model_ok, [(x, halve[x]) for x in (1, 3, 5, 10)]))
    gate("G10", ok and model_ok, "FUN_004f47f0 (ROUND>1 only): per-slot v from "
         "0x984d48+48*slot; CONDITIONAL halving (owner-match path: +bit5, parity, "
         "trunc/2; else FULL v); ENERGY-=v @4f4950-52; +300+=v @4f495e-62; "
         "ENERGY<0 floor-0 if block+8<=1; slot noun OPEN")
    return ok

# ---------------- G11: residue ledger (upkeep tail) ----------------
P_LEDGER = {0x52081a: ("mov", "eax,DWORD PTR [esi+0x94d72c]"),
            0x520820: ("mov", "DWORD PTR [esi+0x94d740],eax"),
            0x520826: ("mov", "ecx,DWORD PTR [esi+0x94d738]"),
            0x52082c: ("mov", "edi,DWORD PTR [esi+0x94d730]"),
            0x520832: ("mov", "edx,DWORD PTR [esi+0x94d72c]"),
            0x520838: ("sub", "ecx,edi"), 0x52083f: ("add", "ecx,edx"),
            0x520841: ("mov", "DWORD PTR [esi+0x94d73c],ecx")}
def g11_ledger():
    ok = all(ins(a) == t for a, t in P_LEDGER.items())
    row("G11 ledger: pins=%s" % ok)
    gate("G11", ok, "post-refund: +310 := +2fc; +30c := +308 - +300 + +2fc "
         "(residue feeds a derived balance; nouns INFERRED)")
    return ok

# ---------------- G12: arg-fed provenance + exclusions (manual pins) ----------------
# (a) 546800: [ebp+8] is overwritten 13x internally; the LAST overwrite before
#     54b35c is 54b1e5 := ecx = 8380*esi (fold 54b1ba-d9). So 54b367 reads
#     block(esi)+300. (b) 535c60: [ebp-0x14] := 2095*arg3 (fold WITHOUT the
#     final shl2, 535cb1-c3); 5362f5 = 2095*arg3 + 0x94d730; arg3=4*faction
#     INFERRED (2/3 callers feed [edx+0xa1c], 1/3 const 0 -> block0).
# (c) exclusions: 579329 is facprofile+300 (callers pass 0x927590+k*1436),
#     51dcd8 hits counter ladder +1778, 596xxx is loader struct-rearrange,
#     5bad16 is stack [esp+0x300].
P_546 = {0x54b1ba: ("mov", "edx,esi"), 0x54b1bf: ("shl", "edx,0x6"),
         0x54b1c4: ("add", "edx,esi"), 0x54b1c9: ("lea", "ecx,[esi+edx*2]"),
         0x54b1cf: ("shl", "ecx,0x4"), 0x54b1d4: ("sub", "ecx,esi"),
         0x54b1d9: ("shl", "ecx,0x2"), 0x54b1e5: ("mov", "DWORD PTR [ebp+0x8],ecx"),
         0x54b35c: ("mov", "edx,DWORD PTR [ebp+0x8]"),
         0x54b361: ("mov", "ecx,DWORD PTR [edx+0x94d72c]"),
         0x54b367: ("mov", "ebx,DWORD PTR [edx+0x94d730]")}
P_535 = {0x535c90: ("mov", "edi,DWORD PTR [ebp+0xc]"), 0x535cb1: ("mov", "eax,edi"),
         0x535cb6: ("shl", "eax,0x6"), 0x535cb9: ("add", "eax,edi"),
         0x535cbb: ("lea", "eax,[edi+eax*2]"), 0x535cbe: ("shl", "eax,0x4"),
         0x535cc1: ("sub", "eax,edi"), 0x535cc3: ("mov", "DWORD PTR [ebp-0x14],eax"),
         0x535cc6: ("add", "eax,ebx"),
         0x5362b1: ("mov", "esi,DWORD PTR [ebp-0x14]"),
         0x5362f5: ("sub", "edx,DWORD PTR [esi+0x94d730]")}
# second def of [ebp-0x14]: FULL 8380-fold of edi @535f1a-2c (other path)
P_535B = {0x535f1a: ("mov", "ecx,edi"), 0x535f1c: ("shl", "ecx,0x6"),
          0x535f1f: ("add", "ecx,edi"), 0x535f21: ("lea", "esi,[edi+ecx*2]"),
          0x535f24: ("shl", "esi,0x4"), 0x535f27: ("sub", "esi,edi"),
          0x535f29: ("shl", "esi,0x2"), 0x535f2c: ("mov", "DWORD PTR [ebp-0x14],esi")}
P_EXCL = {0x5791a6: ("lea", "ecx,[eax*4+0x927590]"), 0x5791ae: ("call", "0x5791c0"),
          0x579e9c: ("mov", "esi,0x927590"), 0x579eaa: ("call", "0x5791c0"),
          0x579329: ("mov", "DWORD PTR [esi+0x300],eax"),
          0x51dcd8: ("mov", "WORD PTR [eax+0x300],si"),
          0x596bee: ("mov", "eax,DWORD PTR [edi+0x300]"),
          0x596cb5: ("mov", "bx,WORD PTR [ecx+0x300]"),
          0x596cbc: ("mov", "WORD PTR [edx+0x300],bx"),
          0x5bad16: ("mov", "edx,DWORD PTR [esp+0x300]"),
          0x426bae: ("mov", "eax,DWORD PTR [edx+0xa1c]"), 0x426bb4: ("push", "eax"),
          0x426c8e: ("mov", "eax,DWORD PTR [edx+0xa1c]"), 0x426c94: ("push", "eax"),
          0x54654d: ("push", "0x0"), 0x546551: ("call", "0x535c60")}
def stores_to_ebp_slot(lo, hi, slot):
    out = []
    for a in m326.ADDRS:
        if a < lo: continue
        if a >= hi: break
        mn, o = ins(a)
        if mn == "mov" and o.startswith("DWORD PTR [ebp%s]" % slot):
            out.append(a)
    return out
def g12_argfed():
    ok = all(ins(a) == t for a, t in P_546.items())
    ok = ok and all(ins(a) == t for a, t in P_535.items())
    ok = ok and all(ins(a) == t for a, t in P_535B.items())
    ok = ok and all(ins(a) == t for a, t in P_EXCL.items())
    # fold multipliers computed from the pinned ops (not authored)
    m546 = (((1 << 6) + 1) * 2 + 1) * 16 - 1
    m546 = m546 * 4
    m535 = (((1 << 6) + 1) * 2 + 1) * 16 - 1     # NO final *4 (535cc6 is add)
    m535b = ((((1 << 6) + 1) * 2 + 1) * 16 - 1) * 4   # full fold @535f1a-2c
    # last-overwrite law: no [ebp+8] store in (54b1e5, 54b35c)
    ow = stores_to_ebp_slot(0x54b1e6, 0x54b35c, "+0x8")
    # two-store law: [ebp-0x14] in 535c60 written exactly at 535cc3 + 535f2c
    fn = next(f for f in m326.funcs if f[0] == 0x535c60)
    ss = stores_to_ebp_slot(fn[0], fn[0] + max(fn[2], 1), "-0x14")
    row("G12 argfed: pins546=%s pins535=%s pins535b=%s pinsexcl=%s m546=%d m535=%d "
        "m535b=%d overwrite(54b1e5,54b35c)=%s stores535=%s edi@535f1a=%s"
        % (all(ins(a) == t for a, t in P_546.items()),
           all(ins(a) == t for a, t in P_535.items()),
           all(ins(a) == t for a, t in P_535B.items()),
           all(ins(a) == t for a, t in P_EXCL.items()), m546, m535, m535b, ow, ss,
           m326.value_of(0x535f1a, "edi")))
    ok = (ok and m546 == STRIDE and m535 == STRIDE // 4 and m535b == STRIDE
          and ow == [] and ss == [0x535cc3, 0x535f2c])
    gate("G12", ok, "54b367=block(esi)+300 (8380-fold, last-overwrite law); "
         "5362f5: [ebp-0x14] has 2 defs (2095*arg3 @535cc3 / 8380*edi @535f2c), "
         "both block-offset folds; arg3=4*faction INFERRED; caller 546551 const 0; "
         "EXCLUDED: 579329 facprofile+300 (0x927590 callers), 51dcd8 ladder+1778, "
         "596bee/cb5/cbc loader rearrange, 5bad16 stack")
    return ok

# ---------------- R: rivals (each must be DEAD on the measured bytes) ----------------
def rivals():
    # R1: refund is x/2 — would need a halving shape, not magic-div3
    r1_holds = not (all(imm(a) == MAGIC for a in P_MAGIC)
                    and all(ins(a)[0] == "imul" for a in P_IMUL))
    # R2: fraction independent of difficulty — would need NO k5 doubling
    r2_holds = not (ins(0x520758) == ("add", "ecx,ecx")
                    and ins(0x520781)[0] == "lea" and "ecx+ecx" in ins(0x520781)[1])
    # R3: field zeroed after refund (the +224 law) — would need a 0-store
    r3_holds = ins(0x52078d)[0] in ("xor", "sub") and ins(0x52078d)[1] == "ecx,ecx"
    # R4: the 985b10 mask gate restricts the refund to a faction subset
    # (bound derived from the same pinned cmp bytes as G6 — mutant-trackable)
    bound = int(ins(0x52062f)[1].split(",")[1], 16)
    r4_holds = ((1 << (1 + (bound - 0x94f70c) // STRIDE)) & 0xff) != 0
    # R5: a persistent maintenance BASE (would survive upkeep entry)
    r5_holds = not (ins(0x52056d) == ("mov", "DWORD PTR [esi+0x94d730],eax")
                    and ins(0x520557) == ("xor", "eax,eax"))
    row("R rivals hold: R1(half)=%s R2(diff-independent)=%s R3(zeroed)=%s "
        "R4(mask-gated)=%s R5(persistent-base)=%s"
        % (r1_holds, r2_holds, r3_holds, r4_holds, r5_holds))
    ok = not (r1_holds or r2_holds or r3_holds or r4_holds or r5_holds)
    gate("R", ok, "R1 DEAD (magic 55555556 div3 x4 + imul x4); R2 DEAD (k5 doubling "
         "@520758/520781); R3 DEAD (sub ecx,edx residue kept); R4 DEAD (cl=8 -> dl=0); "
         "R5 DEAD (entry-zero 52056d + per-upkeep feeder)")
    return ok

def main():
    print("== M330 block+300 census (resolver: M326 import, OFF=0x300) patches=%d ==" % NPATCH)
    field, seeds, accesses = g1_census()
    g23_roles(field)
    g4_law()
    g5_switch()
    g6_mask()
    g7_zero()
    g8_carry()
    g9_turnfn()
    g10_feeder()
    g11_ledger()
    g12_argfed()
    rivals()
    d = digest()
    npass = sum(1 for _, ok in GATES if ok)
    print("digest %s" % d)
    print("== M330: %d/%d ==" % (npass, len(GATES)))
    return 0 if npass == len(GATES) else 1

if __name__ == "__main__":
    sys.exit(main())