#!/usr/bin/env python3
"""M377 - the two companion/latch bits of the relations dword: 0x8000 (bit 15)
and 0x10000 (bit 16), plus the single reader of 0x8000 at 0x53bbed.

M375 measured that 0x8000 and 0x10000 are carried by exactly one setter call each
(0x8010 @0x507d21, 0x10004 @0x5526b3) and left their role OPEN.  This instrument
names the cARRYING EVENT of each: WHICH host stamps the pair, WHICH branch of that
host can reach the stamp (essential-edge analysis, counterfactual), WHAT the only
reader does with it, and whether the stamp is sticky or erasable.

Inputs (read-only): scratch/m574/text.txt (objdump .text), programs/terran.exe
(VA -> string through the PE section table), ghidra_out/index.csv (function table).
Zero box time.

Gates
  G0 carriers   every push of an immediate that leaves 0x8000 / 0x10000 SET, and
                every direct store to the relations dword, classified set/clear.
  G1 hosts      the enclosing function of each carrier; the exact push run.
  G2 reach      essential edges: block one edge at a time, re-run reachability to
                the stamp.  The surviving set is MEASURED, not authored.
  G3 readers    per bit: direct tests and load-then-test-register readers.
  G4 reader act what the reader does with the bit (skip target, skipped string).
  G5 callers    every call site of the two hosts, its enclosing function, and the
                nearest preceding pushed string (the deal event's own words).
  G6 erasure    for every direct store: can it CLEAR bit 15/16?  shape algebra.
  G7 rivals     five rival readings, each measured to disagree with the tables.
  G8 digest     printed row digest, decodes twice.

M377_PATCH='addr|new text' rewrites one instruction line in memory (mutants).
M377_ALGO=n flips an algorithm law (see ALGO).
"""
import hashlib
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M377_TEXT", os.path.join(ROOT, "scratch/m574/text.txt"))
EXE = os.path.join(ROOT, "programs/terran.exe")
IDX = os.path.join(ROOT, "ghidra_out/index.csv")

BASE = 0x94D448                     # relations dword of pair (a,b)
SETTER = 0x551A20                   # FUN_00551a20 (a, b, mask): six test-bl + tail OR
CONTACT = 0x530640                  # FUN_00530640 (a, b, mask, ...): dialog 0x2441
WAR_HOST = 0x507CE0                 # FUN_00507ce0: clear status &7, then stamp
CONTACT_HOST = 0x5525D0             # FUN_005525d0: first-contact stamp
WAR_STAMP = (0x8000, 0x507D21, 0x507D1A)
TRUCE_STAMP = (0x10000, 0x5526B3, 0x552680)
BITS = [("0x8000", 0x8000, 1), ("0x10000", 0x10000, 2)]
ALGO = int(os.environ.get("M377_ALGO", "0") or 0)

OUT = []


def say(msg):
    print(msg)
    OUT.append(msg)


fails = []


def bad(s):
    fails.append(s)
    say("FAIL " + s)


# ---------------------------------------------------------------- decode
PAT = re.compile(r'^\s*([0-9a-f]+):\t([0-9a-f ]+?)(?:\t(.*))?$')


def load_text(path):
    ins = []
    for ln in open(path, errors="replace"):
        m = PAT.match(ln.rstrip("\n"))
        if not m:
            continue
        body = (m.group(3) or "").strip()
        if not body:
            # objdump wraps long instructions: the continuation line has NO third
            # column at all.  Folding its bytes keeps the byte count truthful - without
            # it every >7-byte instruction invents a phantom fall-through address.
            if ins:
                ins[-1]["b"] = ins[-1]["b"] + " " + m.group(2).strip()
            continue
        p = body.split(None, 1)
        ins.append({"a": int(m.group(1), 16), "b": m.group(2).strip(),
                    "mn": p[0].lower(), "ops": p[1] if len(p) > 1 else ""})
    return ins


INS = load_text(TEXT)
IDXBY = {i["a"]: k for k, i in enumerate(INS)}

patch = os.environ.get("M377_PATCH")
if patch:
    addr_s, new = patch.split("|", 1)
    a = int(addr_s, 16)
    if a in IDXBY:
        i = INS[IDXBY[a]]
        p = new.strip().split(None, 1)
        i["mn"] = p[0].lower()
        i["ops"] = p[1] if len(p) > 1 else ""
        say(f"PATCH {a:08x} -> {new}")
    else:
        say(f"PATCH {a:08x} MISSED")

IM = re.compile(r'0x([0-9a-f]+)', re.I)
TARGET = re.compile(r'0x([0-9a-f]+)\s*$')


def imms(s):
    return [int(x, 16) for x in IM.findall(s)]


def last_imm(s):
    v = imms(s)
    return v[-1] if v else None


def dwords_at(arg):
    """(offset, va) for every 0x94d4xx literal inside the relations dword (token-exact)."""
    out = []
    for m in re.finditer(r'0x94d4([0-9a-f]{2})(?![0-9a-f])', arg.lower()):
        v = int("94d4" + m.group(1), 16)
        if BASE <= v <= BASE + 3:
            out.append((0 if ALGO == 4 else v - BASE, v))
    return out


def mem_dest(i):
    first = i["ops"].split(",")[0].strip().lower()
    return ("[" in first) and i["mn"] in ("mov", "or", "and", "add", "sub", "xor", "inc", "dec")


def src_of(i):
    p = i["ops"].split(",", 1)
    return p[1].strip() if len(p) > 1 else ""


FAMR = {"al": "eax", "ah": "eax", "ax": "eax", "eax": "eax", "bl": "ebx", "bh": "ebx",
        "bx": "ebx", "ebx": "ebx", "cl": "ecx", "ch": "ecx", "cx": "ecx", "ecx": "ecx",
        "dl": "edx", "dh": "edx", "dx": "edx", "edx": "edx", "esi": "esi", "edi": "edi"}


def fam(r):
    return FAMR.get(r.lower(), r.lower())


# ---------------------------------------------------------------- PE
_d = open(EXE, "rb").read()
_pe = struct.unpack_from("<I", _d, 0x3C)[0]
_nsec = struct.unpack_from("<H", _d, _pe + 6)[0]
_opt = _pe + 24
_ibase = struct.unpack_from("<I", _d, _opt + 28)[0]
_so = _opt + struct.unpack_from("<H", _d, _pe + 20)[0]
SECS = []
for _k in range(_nsec):
    _o = _so + _k * 40
    _vsz, _va, _rsz, _ra = struct.unpack_from("<IIII", _d, _o + 8)
    SECS.append((_va + _ibase, _rsz, _ra, _vsz))


def pe_str(va, n=64):
    for sva, rsz, ra, vsz in SECS:
        if sva <= va < sva + max(rsz, vsz):
            o = ra + (va - sva)
            e = _d.find(b"\0", o, o + n)
            if e < 0:
                e = o + n
            return _d[o:e].decode("latin1")
    return None


def is_str(va):
    s = pe_str(va, 48)
    if not s or len(s) < 4:
        return None
    if not all(32 <= ord(c) < 127 for c in s):
        return None
    return s


# ---------------------------------------------------------------- functions
FUNS = []
for ln in open(IDX).read().splitlines()[1:]:
    p = ln.split(",")
    if len(p) < 3 or not p[0].startswith("0x"):
        continue
    FUNS.append((int(p[0], 16), int(p[2]), p[1]))
FUNS.sort()
BYNAME = {n: (s, sz) for s, sz, n in FUNS}


def fn_of(a):
    best = None
    for s, sz, n in FUNS:
        if s <= a < s + sz:
            best = (n, s, sz)
        elif s > a:
            break
    return best


# ---------------------------------------------------------------- CFG
JCC = ("je", "jne", "jz", "jnz", "jl", "jle", "jg", "jge", "jb", "jbe", "ja",
       "jae", "js", "jns", "jp", "jnp", "jo", "jno", "jecxz")


def edges_from(i):
    """[(dest, kind)] kind in {'fall','jump'}"""
    nxt = i["a"] + len(i["b"].split())      # one 2-hex-digit token == one byte
    m = TARGET.search(i["ops"])
    if i["mn"].startswith("ret"):
        return []
    if i["mn"] == "jmp" and m:
        return [(int(m.group(1), 16), "jump")]
    if i["mn"] in JCC and m:
        if ALGO == 1:                       # mutant: jcc is not a gate at all
            return [(nxt, "fall")]
        return [(int(m.group(1), 16), "jump"), (nxt, "fall")]
    return [(nxt, "fall")]


def reach(start, stop, block=None, cap=20000):
    seen = set()
    stack = [start]
    n = 0
    while stack and n < cap:
        a = stack.pop()
        if a == stop:
            return True
        if a in seen:
            continue
        seen.add(a)
        n += 1
        # stop at a ret / outside the function
        if a not in IDXBY:
            continue
        i = INS[IDXBY[a]]
        if i["mn"].startswith("ret"):
            continue
        for d, kind in edges_from(i):
            if block and (a, d) == block:
                continue
            stack.append(d)
    return False


def reaches_ret_without(fstart, fsize, avoid, cap=20000):
    """True if some path from the entry reaches a `ret` without executing `avoid`."""
    seen = set()
    stack = [fstart]
    n = 0
    while stack and n < cap:
        a = stack.pop()
        if a == avoid or a in seen:
            continue
        seen.add(a)
        n += 1
        if a not in IDXBY:
            continue
        i = INS[IDXBY[a]]
        if i["mn"].startswith("ret"):
            return True
        for d, _k in edges_from(i):
            stack.append(d)
    return False


def essential_edges(fstart, fsize, stop):
    """block every (jump, dest) edge one at a time; the ones whose blocking kills
    reachability of `stop` are the gates on EVERY path to it."""
    out = []
    end = fstart + fsize
    for i in INS:
        if not (fstart <= i["a"] < end) or i["mn"] not in JCC:
            continue
        for d, kind in edges_from(i):
            if not reach(fstart, stop, block=(i["a"], d)):
                out.append((i["a"], kind, d))
    return out


def def_use(jaddr):
    """nearest earlier write to the register the jcc's flags came from (imm writes only)."""
    k = IDXBY.get(jaddr)
    if k is None:
        return ""
    for j in range(k - 1, max(-1, k - 6), -1):
        t = INS[j]
        if t["mn"] not in ("test", "cmp"):
            continue
        a, b = (t["ops"].split(",") + [""])[:2]
        if a.strip().lower() != b.strip().lower():
            return ""
        r = fam(a)
        for m in range(j - 1, max(-1, j - 80), -1):
            u = INS[m]
            dst = u["ops"].split(",")[0].strip().lower()
            if fam(dst) == r and u["mn"] in ("and", "mov", "or", "xor") and "[" not in dst:
                src = src_of(u)
                if "[" not in src:
                    return (u["mn"] + " " + u["ops"]) if ALGO != 7 else ""
        return ""
    return ""


def flag_text(jaddr):
    """the instruction that sets the flags a jcc reads: nearest prior test/cmp/and."""
    k = IDXBY.get(jaddr)
    if k is None:
        return "?"
    for j in range(k - 1, max(-1, k - 5), -1):
        if INS[j]["mn"] in ("test", "cmp", "and", "or", "sub", "add"):
            return INS[j]["mn"] + " " + INS[j]["ops"]
    return "?"


def push_run(call_a, want):
    """the `want` push instructions immediately before a call (last-first)."""
    k = IDXBY[call_a]
    out = []
    for j in range(k - 1, max(-1, k - 12), -1):
        if INS[j]["mn"] == "push":
            out.append(INS[j])
            if len(out) == want:
                break
    return list(reversed(out))


# ---------------------------------------------------------------- G0 carriers
say("M377 - the two companion bits of the relations dword 0x94d448: 0x8000, 0x10000")
say("")

say("G0  immediate carriers of bit 15/16 - setter calls, other calls, direct stores")
calls = [i for i in INS if i["mn"] == "call"]
carriers = []          # (callee, pushaddr, mask, nargs)
for c in calls:
    tgt = last_imm(c["ops"])
    if tgt not in (SETTER, CONTACT):
        continue
    nargs = 3 if tgt == SETTER else 4
    run = push_run(c["a"], nargs)
    if len(run) != nargs:
        continue
    if ALGO == 3:                      # mutant: read the mask slot one push too far
        mslot = run[-2] if len(run) > 2 else run[0]
    else:
        mslot = run[-3]                # (a, b, mask) -> mask is the third from the call
    mask = last_imm(mslot["ops"]) if "[" not in mslot["ops"] else None
    if mask is None:
        continue
    carriers.append((tgt, mslot["a"], mask, nargs))
say(f"  setter calls 0x551a20 harvested: {sum(1 for c in carriers if c[0]==SETTER)}")
say(f"  4-push calls 0x530640 harvested: {sum(1 for c in carriers if c[0]==CONTACT)}")
hits = []
for name, bit, _hi in BITS:
    h = [(t, a, m, n) for t, a, m, n in carriers if m & bit]
    hits.append((name, bit, h))
    for t, a, m, n in h:
        say(f"  {name:7s}  mask 0x{m:x} @0x{a:06x} -> call 0x{t:x} ({n} pushes)")
# lookalikes: a push of exactly 0x8000/0x10000 into ANY OTHER callee.  The value alone
# is not a carrier - the discriminator is the callee plus the pair arguments.
look = []
for k, i in enumerate(INS):
    if i["mn"] != "push" or i["ops"].strip().lower() not in ("0x8000", "0x10000"):
        continue
    callee = None
    for j in range(k + 1, min(len(INS), k + 8)):
        if INS[j]["mn"] == "call":
            callee = INS[j]["ops"].strip()
            break
    look.append((i["a"], last_imm(i["ops"]), callee))
foreign = [x for x in look if x[2] not in ("0x551a20", "0x530640")]
say(f"  lookalikes: {len(look)} bare pushes of exactly 0x8000/0x10000 image-wide,"
    f" {len(foreign)} into a callee that is not a relations setter")
if not (len(look) == 24 and len(foreign) == 24):
    bad(f"G0 lookalike census is not 24 bare pushes, all foreign: {len(look)}/{len(foreign)}")
ok0 = ([(c[1], c[2]) for c in hits[0][2]] == [(0x507D1A, 0x8010)]
       and sorted((c[1], c[2]) for c in hits[1][2]) ==
       [(0x54D2E5, 0x10004), (0x552680, 0x10004), (0x5526B3, 0x10004)])
if ALGO == 3 or not ok0:
    bad(f"G0 carrier table is not the measured one:"
        f" {[(n, [(hex(a), hex(m)) for _, a, m, _ in h]) for n, _, h in hits]}")
else:
    say("ok  G0 0x8000 <- mask 0x8010 @0x507d1a (1 carrier); 0x10000 <- mask 0x10004 at"
        " 0x54d2e5/0x552680 (call 0x530640) and 0x5526b3 (setter) - 3 carriers, 2 hosts")
say("")

# ---------------------------------------------------------------- G1 hosts
say("G1  the hosts of the two stamps")
hosts = {}
for name, bit, h in hits:
    for t, a, m, n in h:
        f = fn_of(a)
        hosts.setdefault(name, set()).add(f[0])
        say(f"  {name:7s} 0x{a:06x} in {f[0]} (0x{f[1]:06x}, {f[2]} B)  push run:")
        k = IDXBY[a]
        for j in range(k, min(len(INS), k + 4)):
            say(f"      {INS[j]['a']:06x}: {INS[j]['mn']:6s} {INS[j]['ops']}")
argok = []
for name, bit, h in hits:
    for t, a, m, n in h:               # `a` = the mask push itself
        k = IDXBY[a]
        after = []
        for j in range(k + 1, min(len(INS), k + 6)):
            if INS[j]["mn"] == "push":
                after.append(INS[j]["ops"].strip().lower())
            if INS[j]["mn"] == "call":
                break
        argok.append(len(after) == 2 and all(re.fullmatch(r'e[a-z]{2}', x) for x in after))
say(f"  mask slot is an immediate and both arg pushes are registers: {argok}")
f_war = fn_of(WAR_STAMP[1])
f_truce = fn_of(TRUCE_STAMP[1])
if hosts.get("0x8000") != {"FUN_00507ce0"} or hosts.get("0x10000") != {"FUN_005525d0",
                                                                       "FUN_00546800"}:
    bad(f"G1 carrier hosts are not the measured two sets: {hosts}")
elif not all(argok):
    bad(f"G1 a carrier's mask is not an immediate behind two register pushes: {argok}")
elif f_war[0] == "FUN_00507ce0" and f_truce[0] == "FUN_005525d0":
    say("ok  G1 0x8000 lives in ONE 80-byte host (FUN_00507ce0); 0x10000 in TWO"
        " (FUN_005525d0 twice + FUN_00546800 once) - every carrier accounted for")
else:
    bad("G1 carrier hosts do not match the enclosing functions")
say("")

# ---------------------------------------------------------------- G2 reach
say("G2  essential edges - every condition that MUST hold on the way to a stamp")
ess = {}
for name, (bit, site, _pad) in (("0x8000", WAR_STAMP), ("0x10000", TRUCE_STAMP)):
    f = fn_of(site)
    e = essential_edges(f[1], f[2], official := site) if ALGO != 2 else []
    ess[name] = e
    say(f"  {name:7s} store @0x{site:06x} in {f[0]}: {len(e)} essential edge(s)")
    for j, kind, d in e:
        du = def_use(j)
        say(f"      jcc @0x{j:06x} {kind:4s}->0x{d:06x}   gate: {flag_text(j)}"
            + (f"   [{du}]" if du else ""))
    if not e and ALGO != 2:
        say("      (none - no single edge gates the stamp)")
war_ess = ess["0x8000"]
want_war = []
war_bypass = reaches_ret_without(f_war[1], f_war[2], WAR_STAMP[1])
tru_bypass = reaches_ret_without(0x5525D0, 642, 0x5526B3)
say(f"  bypass: a path from entry to a ret that SKIPS the stamp - 0x8000 {war_bypass},"
    f" 0x10000 {tru_bypass}")
if [(j, k) for j, k, d in war_ess] != want_war or war_bypass:
    bad(f"G2 0x8000 must be unconditional: essential={[(hex(j),k) for j,k,_ in war_ess]}"
        f" bypass={war_bypass}")
elif not tru_bypass:
    bad("G2 0x10000 bypass must exist (the stamp is conditional)")
else:
    say("ok  G2 0x8000 is UNCONDITIONAL: 0 essential edges AND no entry->ret path skips"
        " 0x507d21 (0x10000: such a path exists, so its stamp is conditional)")
# (3) the clear-then-stamp arc inside FUN_00507ce0, read from bytes
arc = []
for k in range(IDXBY[0x507CE0], IDXBY.get(0x507D30, len(INS))):
    i = INS[k]
    if i["a"] >= 0x507D30:
        break
    arc.append(i)
pre = [i for i in arc if i["mn"] in ("test", "call") and i["a"] < 0x507D1A]
clear = [i for i in pre if i["mn"] == "call" and last_imm(i["ops"]) == 0x5076D0]
tst7 = [i for i in pre if i["mn"] == "test" and dwords_at(i["ops"]) and last_imm(src_of(i)) == 7]
neg1 = [i for i in arc if i["a"] < 0x507D1A and i["mn"] == "push"
        and last_imm(i["ops"]) == 0xFFFFFFFF]
say(f"  arc before the stamp: test7 {[hex(i['a']) for i in tst7]}, call0x5076d0"
    f" {[hex(i['a']) for i in clear]}, push -1 x{len(neg1)}")
if not (len(tst7) == 1 and len(clear) == 1 and len(neg1) == 1 and clear[0]["a"] < 0x507D1A):
    bad("G2 the clear-then-stamp arc is not read from FUN_00507ce0's bytes")
else:
    say("ok  G2 FUN_00507ce0 clears status&7 first: `test BYTE [pair],0x7` @0x507cff ->"
        " FUN_005076d0(a,b,-1) @0x507d0d (mask -1 = clear-all) -> stamp 0x8010 @0x507d1a")
want_truce = [(0x5525F2, "fall"), (0x552646, "fall"), (0x5526AD, "fall"), (0x5526B1, "fall")]
got_truce = [(j, k) for j, k, d in ess["0x10000"]]
du_truce = {j: def_use(j) for j, k, d in ess["0x10000"] if def_use(j)}
say(f"  def-use of the gated registers: {[(hex(j), t) for j, t in du_truce.items()]}")
if du_truce != {0x552646: "mov eax,ds:0x920434", 0x5526B1: "and edx,0x8"}:
    bad(f"G2 the rel&0x8 provenance is not measured: {du_truce}")
if got_truce != want_truce:
    bad(f"G2 0x10000 gates are not the measured set: {[(hex(j),k,hex(d)) for j,k,d in ess['0x10000']]}")
else:
    say("ok  G2 0x10000 needs exactly 4 edges: player-bit(a), 0x920434 != 0, player-bit(b),"
        " and rel&0x8 == 0 (edx = [pair]&0x8 @0x55261a); the human branch reaches the same"
        " join, so a != human is NOT a gate")
say("")

# ---------------------------------------------------------------- G3 readers
say("G3  readers of bit 15/16 - direct byte/dword test + load-then-test-register")
readers = {}
for name, bit, shift in BITS:
    direct, lift = [], []
    for k, i in enumerate(INS):
        if i["mn"] not in ("test", "cmp"):
            continue
        offs = [o for o, _ in dwords_at(i["ops"])]
        if not offs:
            continue
        v = last_imm(src_of(i))        # the MASK must be an immediate, not a register
        if v is None or "[" in src_of(i):
            continue
        hit = False
        for o in offs:
            lo, hi = (bit >> 8) & 0xff, (bit >> 16) & 0xff
            if o == 1 and lo and (v & lo):
                hit = True
            if o == 2 and hi and (v & hi):
                hit = True
            if o == 0 and (v & bit):
                hit = True
        if (ALGO == 5) and offs and 0 not in offs:      # mutant: only DWORD tests count
            hit = False
        if hit:
            direct.append((i["a"], v))
    for k, i in enumerate(INS):
        if i["mn"] != "mov" or "[" not in i["ops"]:
            continue
        reg = i["ops"].split(",")[0].strip().lower()
        if reg not in FAMR or not dwords_at(i["ops"]):
            continue
        r = fam(reg)
        for j in range(k + 1, min(len(INS), k + 6)):
            t = INS[j]
            if t["mn"] not in ("test", "cmp"):
                continue
            ops = t["ops"]
            if fam(ops.split(",")[0].strip()) != r:
                break
            v = last_imm(src_of(t))
            dirty = False
            for m in range(k + 1, j):
                u = INS[m]
                dst = u["ops"].split(",")[0].strip().lower()
                if fam(dst) == r and u["mn"] in ("mov", "and", "or", "xor", "add", "sub", "lea"):
                    dirty = True
                    break
            if dirty:
                break
            if v is not None and (v & bit):
                lift.append((i["a"], t["a"]))
                break
            continue
    readers[name] = (direct, lift)
    say(f"  {name:7s} direct {len(direct)}: {[(hex(a), hex(v)) for a, v in direct]}")
    say(f"          lift   {len(lift)}: {[(hex(a), hex(b)) for a, b in lift]}")
if [(a, v) for a, v in readers["0x8000"][0]] != [(0x5380F2, 0x8020), (0x53BBED, 0x80),
                                                  (0x541C5C, 0x8020)] or readers["0x8000"][1]:
    bad(f"G3 0x8000 readers are not 2x0x8020 dword + 1 byte test: {readers['0x8000']}")
elif [(a, v) for a, v in readers["0x10000"][0]] != [(0x547367, 0x10000)] or \
        [(a, b) for a, b in readers["0x10000"][1]] != [(0x532FA7, 0x532FB1), (0x5468C1, 0x5468CB)]:
    bad(f"G3 0x10000 readers are not 1 direct + 2 lift: {readers['0x10000']}")
else:
    say("ok  G3 0x8000: 3 readers - test DWORD 0x8020 at 0x5380f2/0x541c5c and the BYTE"
        " test 0x80 at +1 @0x53bbed (M375 counted 1: RETRACTED); 0x10000: 1 direct"
        " (0x547367) + 2 load-then-test-register (0x532fa7, 0x5468c1)")
say("")

# ---------------------------------------------------------------- G4 reader act
say("G4  what each reader does with the bit")
# 0x53bbed: the jcc right after the test, and the block it leaves
k = IDXBY[0x53BBED]
jt = INS[k + 1]
tgt = last_imm(jt["ops"])
say(f"  0x53bbed test -> {jt['mn']} 0x{tgt:x}")
blk = [i for i in INS if tgt <= i["a"] < tgt + 8]
say(f"    taken-block: " + " | ".join(f"{i['a']:06x}:{i['mn']} {i['ops']}" for i in blk))
war_skip00 = any(i["mn"] == "mov" and "0x0" == i["ops"].split(",")[-1].strip()
                 and "[ebp-0x1c]" in i["ops"] for i in blk)
if not war_skip00:
    bad("G4 0x53bbed's skip block must zero the flag [ebp-0x1c]")
# (6) the compare lives on the FALL-THROUGH (bit-set) path: window derived from the jump
fall0 = 0x53BBED + len(INS[IDXBY[0x53BBED]]["b"].split())
cmp_arc = [i for i in INS if fall0 <= i["a"] < tgt and i["mn"] == "cmp"
           and "0x94e48c" in i["ops"]]
say(f"    bit-set path 0x{fall0:06x}..0x{tgt:06x} compare:"
    f" {[(hex(i['a']), i['mn'] + ' ' + i['ops']) for i in cmp_arc]}")
if len(cmp_arc) != 1:
    bad(f"G4 0x53bbed's bit-set path must hold exactly one 0x94e48c compare: {cmp_arc}")
# (4) the reader's host and its only caller, read from bytes
f53 = fn_of(0x53BBED)
c53 = [i["a"] for i in INS if i["mn"] == "call" and last_imm(i["ops"]) == f53[1]]
say(f"    0x53bbed host {f53[0]} (0x{f53[1]:06x}, {f53[2]} B); its callers"
    f" {[hex(a) for a in c53]} in {[fn_of(a)[0] for a in c53]}")
if f53[0] != "FUN_0053bb90" or c53 != [0x545D4A] or fn_of(0x545D4A)[0] != "FUN_00545c50":
    bad(f"G4 the reader's provenance is not FUN_0053bb90 <- FUN_00545c50@0x545d4a")
# 0x547367: the jcc and the string the skipped block logs
k = IDXBY[0x547367]
jt = INS[k + 1]
tgt = last_imm(jt["ops"])
say(f"  0x547367 test -> {jt['mn']} 0x{tgt:x}")
strs = []
for i in INS:
    if not (0x547367 <= i["a"] < tgt):
        continue
    if i["mn"] == "push":
        v = last_imm(i["ops"])
        s = is_str(v) if v else None
        if s:
            strs.append((i["a"], hex(v), s))
say(f"    strings pushed on the skipped path: {[(hex(a), v, s) for a, v, s in strs]}")
tt = [s for _, _, s in strs]
if tt != ["Sending TREATY OFF", "Sending TREATY OFF", "NOPATIENCEFRIEND", "NOPATIENCE"]:
    bad(f"G4 the block 0x10000 skips is not the TREATY-OFF + no-patience block: {strs}")
# the string at the WAR host's own callee is not needed; but assert 0x690160 name-check
if is_str(0x690160) != "Sending TREATY ON":
    bad("G4 0x690160 is not 'Sending TREATY ON' (pair-label anchor moved)")
else:
    say("ok  G4 0x8000 gates an AI comparison (flag=0 on the skip path); 0x10000 skips the"
        " block that logs 'Sending TREATY OFF'")
say("")

# ---------------------------------------------------------------- G5 callers
say("G5  who calls the two hosts, and the deal event's own words")
callers = {}
for host, nm in ((WAR_HOST, "FUN_00507ce0"), (CONTACT_HOST, "FUN_005525d0")):
    sites = [i["a"] for i in INS if i["mn"] == "call" and last_imm(i["ops"]) == host]
    callers[nm] = sites
    say(f"  {nm}: {len(sites)} call site(s)")
    for s in sites:
        f = fn_of(s)
        say(f"    @0x{s:06x} in {f[0]} (0x{f[1]:06x}, {f[2]} B)")
        near = []
        kk = IDXBY[s]
        for j in range(kk - 1, max(-1, kk - 70), -1):
            p = INS[j]
            if p["mn"] != "push":
                continue
            v = last_imm(p["ops"])
            if v is None:
                continue
            t = is_str(v)
            if t:
                near.append((p["a"], t))
                break
        if near:
            say(f"        nearest pushed string: 0x{near[0][0]:06x} '{near[0][1]}'")
if sorted(hex(s) for s in callers["FUN_00507ce0"]) != ["0x4cfe22", "0x503885", "0x5893f2", "0x594c3b"]:
    bad(f"G5 FUN_00507ce0 call sites are not the measured four: {[hex(s) for s in callers['FUN_00507ce0']]}")
elif [hex(s) for s in callers["FUN_005525d0"]] != ["0x5543e6", "0x5543ed"]:
    bad(f"G5 FUN_005525d0 call sites are not 0x5543e6/0x5543ed: {[hex(s) for s in callers['FUN_005525d0']]}")
else:
    say("ok  G5 4 callers of the war host; the contact host is called TWICE, back to back,"
        " from one site (both directions)")
say("")

# ---------------------------------------------------------------- G6 erasure
say("G6  can any direct store CLEAR bit 15/16?  (shape algebra, not a guess)")
stores = []
for k, i in enumerate(INS):
    if not mem_dest(i):
        continue
    offs = [o for o, _ in dwords_at(i["ops"])]
    if not offs:
        continue
    first = i["ops"].split(",")[0].strip().lower()
    if not re.match(r'^(dword|word|byte) ptr ', first) and "[" not in first:
        continue
    if "ptr" in first and re.search(r'ptr\s+\w*word', first):
        pass
    s = src_of(i)
    v = last_imm(s) if s else None
    w = "dword" if "dword" in first else ("word" if re.search(r'\bword\b', first) else "byte")
    if w != "dword":
        shape = "BYTE/WORD (does not touch bits 15/16 of the +0 dword)"
    elif i["mn"] == "mov" and v is not None and "[" not in s:
        shape = ("SETS exactly 0x%x" % v) + (" - CLEARS" + (" 0x8000" if not v & 0x8000 else "")
                                            + (" 0x10000" if not v & 0x10000 else ""))
    elif i["mn"] in ("and",) and v is not None and "[" not in s:
        shape = ("MASK 0x%x" % v) + (" - CLEARS" + (" 0x8000" if not v & 0x8000 else "")
                                    + (" 0x10000" if not v & 0x10000 else ""))
    elif i["mn"] == "or" and v is not None:
        shape = "OR 0x%x - cannot clear" % v
    else:
        shape = "opaque (src %s) - cannot prove" % s
    stores.append((i["a"], shape))
sar = [s for s in stores if "CLEARS" in s[1]]
say(f"  direct stores to the +0 dword: {len(stores)}; shapes that could CLEAR bit 15/16: {len(sar)}")
say("  store sites: " + " ".join(f"{a:06x}" for a, _ in stores))
for a, s in stores:
    if "CLEARS" in s:
        say(f"    0x{a:06x} {s}")
opq = [s for s in stores if s[1].startswith("opaque")]
if ALGO == 6:
    sar = stores[:1]
wordish = [s for s in stores if s[1].startswith("BYTE/WORD")]
if len(sar) != 0 or len(opq) != 27 or len(stores) != 27 or wordish:
    bad(f"G6 store shapes are not 27 register-sourced / 0 provable clearers:"
        f" {len(stores)} stores, {len(opq)} opaque, {len(sar)} clear-capable,"
        f" {len(wordish)} byte/word")
else:
    say("ok  G6 all 27 direct stores are register-sourced (opaque): 0 stores PROVE a clear and"
        " 0 prove a preserve - both stamps survive only as long as each rewrite's register keeps"
        " them; the two stamp sites are OR-shaped and cannot clear")
say("")

# ---------------------------------------------------------------- G7 rivals
say("G7  rivals - each prediction is measured against the tables above")
riv = []
# R1: 0x8000 is a TRUCE companion (M375's own OPEN guess)
r1 = [m for _, _, m, _ in hits[0][2] if m & 0x4]
riv.append(("R1", "0x8000 rides the TRUCE bit 0x4", bool(r1), "carrier 0x8010 has 0x10, no 0x4"))
# R2: 0x10000 is a WAR companion
r2 = [m for _, _, m, _ in hits[1][2] if m & 0x10]
riv.append(("R2", "0x10000 rides the WAR bit 0x10", bool(r2), "carrier 0x10004 has 0x4, no 0x10"))
# R3: one host stamps both
r3 = f_war[0] == f_truce[0]
riv.append(("R3", "one host stamps both companions", r3, "two distinct hosts"))
# R4: 0x10000's stamp needs no commlink condition (pure mirror of 0x4)
r4 = not any(def_use(j).strip() in ("and edx,0x8", "and eax,0x8", "and ecx,0x8")
             for j, _, _ in ess["0x10000"])
riv.append(("R4", "the 0x10000 stamp is unconditional on contact", r4,
            "an essential gate tests rel&0x8"))
# R5: the war stamp sits inside the status-clear branch
r5 = any(j == 0x507D07 for j, _, _ in war_ess)
riv.append(("R5", "the 0x8000 stamp is inside FUN_00507ce0's &7 branch", r5,
            "no essential edge: it is after the join"))
for rid, claim, pred, why in riv:
    say(f"  {rid} {claim:52s} predicted={pred}  -> {'FAILS' if not pred else 'HOLDS'}"
        f"   ({why})")
    if pred:
        bad(f"G7 rival {rid} held: {claim}")
say("ok  G7 five rival readings measured and rejected" if not any(p for _, _, p, _ in riv)
    else "")
say("")

# ---------------------------------------------------------------- G8 digest
say("G8  digest of the printed rows - every digested token must appear in the table above")
rows = []
for name, bit, h in hits:
    rows.append(name + ":" + ",".join(f"{a:06x}/{m:x}/{t:x}" for t, a, m, n in h))
for name, _b, _s in BITS:
    rows.append(name + ":|E|" + ",".join(f"{j:06x}" for j, k, d in ess[name]))
    rows.append(name + ":|R|" + ",".join(f"{a:06x}" for a, _v in readers[name][0])
                + "/" + ",".join(f"{a:06x}" for a, b in readers[name][1]))
rows.append("call:" + ",".join(f"{a:06x}" for a in callers["FUN_00507ce0"])
            + "/" + ",".join(f"{a:06x}" for a in callers["FUN_005525d0"]))
rows.append("st:" + ",".join(f"{a:06x}" for a, _ in stores))
if ALGO == 8:                      # mutant: digest a subset of the printed rows
    rows = rows[:-1]
txt = "\n".join(OUT)
missing = sorted({t for row in rows for t in re.split(r'[:/,|]', row)
                  if re.fullmatch(r'[0-9a-f]{4,8}', t) and t not in txt})
dig = hashlib.sha256("|".join(rows).encode()).hexdigest()[:16]
say(f"  rows {len(rows)}  digest {dig}  unprinted tokens {missing}")
if missing:
    bad(f"G8 digested tokens that the table never printed: {missing}")
elif len(rows) != 8:
    bad(f"G8 row set is not the measured 8: {len(rows)}")
else:
    say("ok  G8 all 8 digest rows reproduce from the printed table")
say("")

say("M377 %d/%d" % (8 - len(fails), 8))
print("PASS M377: %d/8" % (8 - len(fails)) + " " + dig if not fails else "FAILURES: " + "; ".join(fails))
sys.exit(0 if not fails else 1)
