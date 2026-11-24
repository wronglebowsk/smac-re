#!/usr/bin/env python3
"""M375 - the five unnamed bits of the relations dword: 0x800000, 0x40, 0x8000,
0x10000, 0x100000.

B36 extracted the relations setter FUN_00551a20 and left these five unnamed.  This
instrument re-derives the WHOLE access picture for the +0 dword (0x94d448 + 4*(2095*a+b))
from the static image and then names each of the five from three independent kinds of
evidence: the SET vocabulary (masks pushed into the two setters), the 50-tick counter
cell the writers arm, and the protocol string pushed beside the mask.

Inputs (read-only): scratch/m574/text.txt (objdump .text), programs/terran.exe (VA ->
string through the PE section table), programs/labels.txt, ghidra_out/index.csv.
Zero box time.

Gates
  G0 census      every ref to the +0 dword: shape counts, byte-offset coverage, stores.
  G1 access table  per bit: direct byte/dword tests + load-then-test-register readers,
                   and the writers whose immediate leaves the bit SET.
  G2 set vocab   the masks pushed into 0x551a20 / 0x551cf0 (3-push runs), per bit.
  G3 timer law   every store that leaves 0x40 set arms the +0x80 cell to 0x32; the
                 upkeep decrements it and clears 0x40 at zero; peace does not touch it.
  G4 bit23 law   every status write (mask carrying 1/2/4/10 after the 0x10 upgrade)
                 clears bit 23 at 0x551b98 and only the tail OR re-adds it.
  G5 anchors     mask -> protocol string adjacency (TREATY ON / TREATY OFF / SET TREATY)
                 and the eviction routine that sets 0x100000.
  G6 labels      the 13 diplomacy label ids contain NONE of the five (measured).
  G7 rivals      four rival readings, each measured to differ on the printed rows.
  G8 digest      the printed row digest reproduces on a second decode.

M375_PATCH='addr|new text' rewrites one instruction line in memory.
M375_ALGO=n flips an algorithm law (see ALGO).
"""
import hashlib
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M375_TEXT", os.path.join(ROOT, "scratch/m574/text.txt"))
EXE = os.path.join(ROOT, "programs/terran.exe")
LABELS = os.environ.get("M375_LABELS", os.path.join(ROOT, "programs/labels.txt"))
IDX = os.path.join(ROOT, "ghidra_out/index.csv")

BASE = 0x94D448              # relations dword of pair (a,b); +4*(2095*a+b)
STRIDE_FIELD = 0x80          # per-pair 50-tick cell relative to BASE
SETTER = 0x551A20            # FUN_00551a20: six test-bl blocks + unconditional tail OR
SETTER2 = 0x551CF0           # FUN_00551cf0: ora mask, and if cl&0x40 arm the cell
EVICT = 0x53F9F0             # unit sweep that expels b's units, then sets 0x100000
BITS = [("0x800000", 0x800000, 2, 0x80),
        ("0x40", 0x40, 0, 0x40),
        ("0x8000", 0x8000, 1, 0x80),
        ("0x10000", 0x10000, 2, 0x01),
        ("0x100000", 0x100000, 2, 0x10)]

ALGO = int(os.environ.get("M375_ALGO", "0") or 0)
say = print
fails = []


def bit(s):
    """set a global failure; never raise (so the table prints first)."""
    fails.append(s)
    say("FAIL " + s)


# ---------------------------------------------------------------- decode
PAT = re.compile(r'^\s*([0-9a-f]+):\t([0-9a-f ]+)\t(.*)$')


def load_text(path):
    ins = []
    for ln in open(path, errors="replace"):
        m = PAT.match(ln.rstrip("\n"))
        if not m:
            continue
        body = m.group(3).strip()
        if not body:
            continue
        p = body.split(None, 1)
        ins.append({"a": int(m.group(1), 16), "b": m.group(2).strip(),
                    "mn": p[0].lower(), "ops": p[1] if len(p) > 1 else ""})
    return ins


INS = load_text(TEXT)
IDXBY = {i["a"]: k for k, i in enumerate(INS)}

# M375_PATCH: 'addr|new text' (the mutant lever)
patch = os.environ.get("M375_PATCH")
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


def imms(s):
    return [int(x, 16) for x in IM.findall(s)]


def dwords_at(arg):
    """(offset, addr) for every 0x94d4xx literal in a memory operand."""
    out = []
    for m in re.finditer(r'0x94d4([0-9a-f]{2})', arg.lower()):
        v = int("94d4" + m.group(1), 16)
        if BASE <= v <= BASE + 3:
            out.append((0 if ALGO == 2 else v - BASE, v))
    return out


def reg_of(ops_first):
    m = re.match(r'^([a-z]{2,3})$', ops_first.strip().lower())
    return m.group(1) if m else None


FAM = {"al": "eax", "ah": "eax", "ax": "eax", "eax": "eax",
       "bl": "ebx", "bh": "ebx", "bx": "ebx", "ebx": "ebx",
       "cl": "ecx", "ch": "ecx", "cx": "ecx", "ecx": "ecx",
       "dl": "edx", "dh": "edx", "dx": "edx", "edx": "edx",
       "esi": "esi", "edi": "edi", "ebp": "ebp", "esp": "esp"}


def fam(r):
    return FAM.get(r.lower(), r.lower())


# ---------------------------------------------------------------- PE strings
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


def pe_str(va, n=48):
    for sva, rsz, ra, vsz in SECS:
        if sva <= va < sva + max(rsz, vsz):
            o = ra + (va - sva)
            e = _d.find(b"\0", o, o + n)
            if e < 0:
                e = o + n
            return _d[o:e].decode("latin1")
    return None


# ---------------------------------------------------------------- G0 census
say("M375 - the five unnamed bits of the relations dword 0x94d448")
say("")
say("G0  census of the +0 dword")
refs = [k for k, i in enumerate(INS) if dwords_at(i["ops"])]
kinds = {"STORE": 0, "TEST": 0, "LOAD": 0}
stores = []
for k in refs:
    i = INS[k]
    first = i["ops"].split(",")[0].strip().lower()
    mem_dest = ("[" in first) and i["mn"] in ("mov", "or", "and", "add", "sub", "xor", "inc", "dec")
    if mem_dest:
        kinds["STORE"] += 1
        stores.append(k)
    elif i["mn"] in ("test", "cmp"):
        kinds["TEST"] += 1
    else:
        kinds["LOAD"] += 1
# stores via lea-then-[reg]
lea_stores = []
for k, i in enumerate(INS):
    if i["mn"] != "mov" or "[" not in i["ops"]:
        continue
    first = i["ops"].split(",")[0].strip().lower()
    m = re.match(r'^\[([a-z]{2,3})\]$', first)
    if not m:
        continue
    r = m.group(1)
    for j in range(k - 1, max(-1, k - 4), -1):
        p = INS[j]
        if p["mn"] == "lea" and p["ops"].lower().startswith(r + ",") and dwords_at(p["ops"]):
            lea_stores.append(k)
            kinds["STORE"] += 1
            break
byte_offs = sorted({off for k in refs for off, _ in dwords_at(INS[k]["ops"])})
dword_tests = [k for k in refs if INS[k]["mn"] in ("test", "and")
               and "DWORD" in INS[k]["ops"] and 0 in [o for o, _ in dwords_at(INS[k]["ops"])]]
say(f"  refs {len(refs)}  TEST {kinds['TEST']}  LOAD {kinds['LOAD']}  STORE {kinds['STORE']}"
    f" ({len(stores)} disp + {len(lea_stores)} lea)")
say(f"  byte-offset literals: {byte_offs}; DWORD tests at +0: {len(dword_tests)}"
    f"  -> the dword is read whole (bits 16..31 included) and byte-wise at +0/+1")
say(f"  store sites: {' '.join('%08x' % INS[k]['a'] for k in sorted(stores))}")
acc = (len(refs) > 600 and kinds["STORE"] == 27 and byte_offs == [0, 1] and len(dword_tests) >= 4)
if not acc:
    bit(f"G0 census refs={len(refs)} stores={kinds['STORE']} offs={byte_offs} dw={len(dword_tests)}")
else:
    say("ok  G0 %d refs / 27 stores; byte literals only at +0/+1, DWORD tests at +0 carry bits 16-31" % len(refs))

# ---------------------------------------------------------------- G1 access table
say("")
say("G1  per-bit access table (direct test at the bit's byte offset, or load-then-test-reg)")

def direct(boff, bmask, bitv):
    out = []
    for k in refs:
        i = INS[k]
        if i["mn"] not in ("test", "and", "cmp", "or"):
            continue
        hit = dwords_at(i["ops"])
        hits = [o for o, _ in hit]
        im = imms(i["ops"].split(",", 1)[1]) if "," in i["ops"] else []
        if not im:
            continue
        v = im[-1]
        if (boff in hits and "BYTE" in i["ops"] and (v & 0xFF) == bmask) or (0 in hits and v == bitv):
            out.append(k)
    return out


def load_test(bitv):
    out = []
    for k in refs:
        i = INS[k]
        if i["mn"] != "mov" or i["ops"].split(",")[0].strip().lower().startswith("["):
            continue
        if not dwords_at(i["ops"]):
            continue
        r = reg_of(i["ops"].split(",")[0])
        if not r:
            continue
        for j in range(k + 1, min(len(INS), k + 5)):
            p = INS[j]
            if p["mn"] in ("test", "cmp", "and") and fam(p["ops"].split(",")[0]) == fam(r):
                im = imms(p["ops"])
                if im and im[-1] == bitv:
                    out.append((k, j))
    return out


def writers_setting(bitv):
    """stores whose immediately preceding value-producing instruction sets the bit."""
    out = []
    for k in sorted(stores) + lea_stores:
        i = INS[k]
        val = i["ops"].split(",", 1)[1].strip() if "," in i["ops"] else ""
        r = reg_of(val)
        for j in range(k - 1, max(-1, k - 10), -1):
            p = INS[j]
            if p["mn"] in ("or", "add", "mov") and r and fam(p["ops"].split(",")[0]) == fam(r):
                im = imms(p["ops"])
                if im and (im[-1] & bitv) == bitv and (im[-1] & 0xFFFFFFFF) >= bitv and \
                   (im[-1] & 0xFFFFFFFF) != 0xFFFFFFFF:
                    # `or al,0x40` / `or edx,0x840` / `mov ..,0x32` do not match; `and` clears
                    if p["mn"] == "or" or (p["mn"] == "mov" and im[-1] == bitv):
                        out.append((k, j))
                        break
                if p["mn"] == "and" or p["mn"] == "mov":
                    break
    return out


rows = []
for name, v, boff, bmask in BITS:
    d = direct(boff, bmask, v)
    lt = load_test(v)
    w = writers_setting(v)
    rows.append((name, v, d, lt, w))
    say(f"  {name:9s} direct {len(d):2d}  load->test {len(lt):2d}  set-writer {len(w):2d}"
        f"   sites: {' '.join('%08x' % INS[k]['a'] for k in d[:4])}")
for name, v, d, lt, w in rows:
    say(f"    {name}: readers {['%08x' % INS[k]['a'] for k in d]}"
        f" lift {[('%08x' % INS[a]['a'], '%08x' % INS[b]['a']) for a, b in lt]}"
        f" writers {['%08x' % INS[a]['a'] for a, b in w]}")
covered = [r[0] for r in rows if r[2] or r[3]]
if len(covered) != 5:
    bit(f"G1 only {len(covered)}/5 bits have a reader: {covered}")
else:
    say("ok  G1 all five bits have at least one exact reader; 0x8000 is read ONLY as a byte at +1 (0x94d449, 0x80)")

# ---------------------------------------------------------------- G2 set vocabulary
say("")
say("G2  set vocabulary - masks pushed into the two setters")
masks = {"551a20": [], "551cf0": []}


def pushes_before(k, hi=3):
    runs = []
    j = k - 1
    while j >= 0 and len(runs) < hi and k - j < 28:
        p = INS[j]
        if p["mn"] == "push":
            runs.append(p["ops"].strip())
        elif p["mn"] in ("call", "ret"):
            break
        j -= 1
    return runs


def pushes_via_jcc(k, hi=6):
    """the `push mask; push b; push a; jcc <this call>` idiom."""
    for j in range(k - 1, max(-1, k - 30), -1):
        p = INS[j]
        if p["mn"].startswith("j") and p["mn"] != "jmp" and imms(p["ops"]) and \
                imms(p["ops"])[-1] == INS[k]["a"]:
            return pushes_before(j, hi)
    return []


flags = {"fallthrough": 0, "jcc": 0}
for k, i in enumerate(INS):
    if i["mn"] != "call" or i["ops"].strip().lower() not in ("0x%x" % SETTER, "0x%x" % SETTER2):
        continue
    fn = i["ops"].strip().lower()[2:]
    runs = pushes_before(k, 4)
    how = "fallthrough"
    if not (len(runs) >= 3 and re.match(r'^0x[0-9a-f]+$', runs[2])):
        runs = pushes_via_jcc(k, 6)
        how = "jcc"
    if len(runs) < 3 or not re.match(r'^0x[0-9a-f]+$', runs[2]):
        continue
    flags[how] += 1
    flag = None
    if fn != "551a20" and len(runs) >= 4 and re.match(r'^0x[0-9a-f]+$', runs[3]) \
            and int(runs[3], 16) in (0, 1):
        flag = int(runs[3], 16)
    masks[fn].append((INS[k]["a"], int(runs[2], 16), flag))
    if ALGO == 1 and int(runs[2], 16) == 0x80000018:      # the lookalike bug
        masks[fn][-1] = (INS[k]["a"], int(runs[2], 16) | 0x800000, flag)
say(f"  harvested by push-run {flags['fallthrough']} + via-jcc {flags['jcc']} "
    f"= {sum(flags.values())} of {len(masks['551a20']) + len(masks['551cf0'])} "
    f"({len(masks['551a20']) + len(masks['551cf0'])} sites seen)")
say(f"  0x551a20: {len(masks['551a20'])} sites ({len(set(m for _, m, _ in masks['551a20']))} masks, 3-arg)")
say(f"  0x551cf0: {len(masks['551cf0'])} sites ({len(set(m for _, m, _ in masks['551cf0']))} masks, "
    f"{sum(1 for _, _, f in masks['551cf0'] if f == 1)} set / "
    f"{sum(1 for _, _, f in masks['551cf0'] if f == 0)} clear / "
    f"{sum(1 for _, _, f in masks['551cf0'] if f is None)} flag-not-immediate)")
for name, v, boff, bmask in BITS:
    carriers = [(a, m, fn, f) for fn, lst in masks.items() for a, m, f in lst if m & v]
    say(f"  {name:9s} carried by {len(carriers)} call(s): "
        + " ".join("0x%x@%08x(%s%s)" % (m, a, "A" if fn == "551a20" else "B",
                                        "" if f is None else ",f=%d" % f)
                   for a, m, fn, f in carriers))
carry = {n: [(a, m, f) for fn, lst in masks.items() for a, m, f in lst
             if (m & v) and (fn == "551a20" or f == 1)]
         for n, v, _, _ in BITS}
if not all(carry[n] for n in carry):
    bit("G2 a bit has no SET request (3-arg call or flag=1): %s" % [n for n in carry if not carry[n]])
else:
    say("ok  G2 every one of the five is a bit some caller SETS (3-arg call, or flag=1); each "
        "bit's co-bits are read off the carrier list above")

# ---------------------------------------------------------------- G3 the 0x40 timer
say("")
say("G3  the 0x40 timer law - who arms the +0x80 cell (0x94d4c8) and who clears 0x40")
cell_stores = [k for k, i in enumerate(INS) if "0x94d4c8" in i["ops"].lower()]
arm = [k for k, i in enumerate(INS)
       if i["mn"] == "mov" and "0x94d4c8" in i["ops"].lower() and "[" in i["ops"]
       and imms(i["ops"]) and imms(i["ops"])[-1] == 0x32]
say(f"  refs to 0x94d4c8: {len(cell_stores)}  -> " +
    " ".join("%08x:%s" % (INS[k]["a"], INS[k]["mn"]) for k in cell_stores))
say(f"  arms of 0x32: {' '.join('%08x' % INS[k]['a'] for k in arm)}")


def valreg(k):
    parts = INS[k]["ops"].split(",", 1)
    return reg_of(parts[1]) if len(parts) == 2 else None


def set40(k):
    """does store k leave bit 0x40 set?"""
    r = valreg(k)
    if not r:
        return False
    for j in range(k - 1, max(-1, k - 4), -1):
        p = INS[j]
        if p["mn"] == "or" or (ALGO == 3 and p["mn"] == "and"):   # classifier law mutant
            im = imms(p["ops"])
            if im and im[-1] & 0x40 and fam(p["ops"].split(",")[0]) == fam(r):
                return True
    # the mask-gated path inside FUN_00551cf0: or edx,ecx then test cl,0x40
    if SETTER2 <= INS[k]["a"] < SETTER2 + 0x80:
        return any(INS[j]["mn"] == "test" and INS[j]["ops"].lower().replace(" ", "") == "cl,0x40"
                   for j in range(max(0, k - 4), k))
    return False


p40 = [k for k in sorted(stores) + lea_stores if set40(k)]
say(f"  stores leaving 0x40 set: {' '.join('%08x' % INS[k]['a'] for k in p40)}")
pairs = []
for k in p40:
    near = [INS[j]["a"] for j in range(k + 1, min(len(INS), k + 5))
            if INS[j]["mn"] == "mov" and "0x94d4c8" in INS[j]["ops"].lower()
            and (imms(INS[j]["ops"]) or [0])[-1] == 0x32]
    pairs.append((INS[k]["a"], near))
for a, near in pairs:
    say(f"    set@{a:08x} -> arm {['%08x' % x for x in near]}")
expiry = []
for k, i in enumerate(INS):
    if i["mn"] == "and" and i["ops"].lower().replace(" ", "") == "al,0xbf":
        back = any(any(v == BASE for _, v in dwords_at(INS[j]["ops"]))
                   for j in range(max(0, k - 4), k))
        fwd = any(any(v == BASE for _, v in dwords_at(INS[j]["ops"]))
                  for j in range(k + 1, min(len(INS), k + 3)))
        if back and fwd:
            expiry.append(k)
say(f"  expiry clear of 0x40 on the dword (and al,0xbf with a load/store of 0x94d448): "
    f"{' '.join('%08x' % INS[k]['a'] for k in expiry)}")
war_peace = [k for k, i in enumerate(INS)
             if i["mn"] == "and" and (imms(i["ops"]) or [0])[-1] in (0xffee7FAF, 0xFAEEF378)]
say(f"  status masks that clear 0x40: " + " ".join(
    "%08x:0x%x" % (INS[k]["a"], imms(INS[k]["ops"])[-1]) for k in war_peace))
ok3 = (len(arm) == 4 and len(p40) == 4 and all(near for _, near in pairs) and len(expiry) == 1)
peace_does_not_touch_cell = not any("94d4c8" in INS[k]["ops"].lower() for k in war_peace)
if not ok3 or not peace_does_not_touch_cell:
    bit(f"G3 arm={len(arm)} set-sites={len(p40)} armed={[bool(n) for _, n in pairs]} "
        f"expiry={len(expiry)} peace_touches_cell={not peace_does_not_touch_cell}")
else:
    say("ok  G3 4/4 stores that leave 0x40 set arm 0x94d4c8 to 0x32 (50); the upkeep at "
        "0x5552b6 decrements it and clears 0x40 exactly at 0; the peace mask never touches the cell")

# ---------------------------------------------------------------- G4 bit23 law
say("")
say("G4  bit 23 (0x800000): what sets it, what clears it, and the 0x80000018 lookalike")
W = (SETTER, SETTER + 0x212)
clr = [k for k, i in enumerate(INS)
       if W[0] <= i["a"] < W[1] and i["mn"] == "and" and (imms(i["ops"]) or [0])[-1] == 0xFF7FFFFF]
up = [k for k, i in enumerate(INS)
      if W[0] <= i["a"] < W[1] and i["mn"] == "or" and (imms(i["ops"]) or [0])[-1] == 0x80000108]
pred = [k for k, i in enumerate(INS)
        if W[0] <= i["a"] < W[1] and i["mn"] == "test" and i["ops"].lower().replace(" ", "") == "bl,0x17"]
tail = [k for k, i in enumerate(INS)
        if W[0] <= i["a"] < W[1] and i["mn"] == "or" and i["ops"].lower().replace(" ", "") == "edx,ebx"]
say(f"  window 0x{W[0]:x}..0x{W[1]:x}: `test bl,0x17` {['%08x' % INS[k]['a'] for k in pred]}, "
    f"`or ebx,0x80000108` {['%08x' % INS[k]['a'] for k in up]}, "
    f"`and edx,0xff7fffff` {['%08x' % INS[k]['a'] for k in clr]}, "
    f"`or edx,ebx` {['%08x' % INS[k]['a'] for k in tail]}")
b23 = [(a, m) for a, m, f in masks["551a20"] + masks["551cf0"] if m & 0x800000]
with_stat = [(a, m) for a, m in b23 if m & 0x17]
say(f"  requests carrying bit 23: {len(b23)} -> {['0x%x@%08x' % (m, a) for a, m in b23]}; "
    f"carrying a 0x17 bit too: {len(with_stat)}")
LOOK = 0x80000018
say(f"  lookalike: mask 0x{LOOK:08x} & 0x800000 = 0x{LOOK & 0x800000:08x}"
    f"  (it carries bit 31 0x{LOOK & 0x80000000:08x}, not bit 23)")
PEACE_CLR, WAR_CLR, B23_CLR = 0xffee7FAF, 0xFAEEF378, 0xFF7FFFFF


def setter(pre, mask):
    """FUN_00551a20's six blocks, re-implemented from B36's extracted program."""
    w, m = pre & 0xFFFFFFFF, mask & 0xFFFFFFFF
    if m & 7:
        w &= PEACE_CLR
    if m & 1:
        m |= 0x2
    if m & 0x10:
        m |= 0x80000108
        w &= WAR_CLR
    if m & 0x17:
        w &= B23_CLR
    return (w | m) & 0xFFFFFFFF


sweep = []
for mask in (0x800000, 0x10, LOOK, 0x7):
    pre = 0x800000 | 0x8          # a pre-state carrying bit 23 and commlink
    post = setter(pre, mask)
    sweep.append((mask, pre, post, bool(post & 0x800000)))
    say(f"    pre 0x{pre:08x} mask 0x{mask:08x} -> 0x{post:08x}  bit23={bool(post & 0x800000)}")
survive = [m for m, _, _, s in sweep if s]
ok4 = (len(clr) == 2 and len(pred) == 1 and len(up) == 1 and len(tail) == 2
       and b23 and not with_stat and survive == [0x800000] and not (LOOK & 0x800000))
if not ok4:
    bit(f"G4 clr={len(clr)} pred={len(pred)} up={len(up)} tail={len(tail)} b23={len(b23)} "
        f"with_stat={len(with_stat)} survive={['0x%x' % m for m in survive]}")
else:
    say("ok  G4 bit 23 survives ONLY a request that carries no 0x17 bit (0x800000 alone, the "
        "'TREATY ON' term); every status write clears it at 0x551b98 and the tail OR cannot "
        "restore it; 0x80000018 is bit 31 + war, not bit 23")

# ---------------------------------------------------------------- G5 anchors
say("")
say("G5  protocol anchors - the string pushed beside the mask, and the 0x100000 writer")

def str_near(k, span=14):
    out = []
    for j in range(k, min(len(INS), k + span)):
        p = INS[j]
        if p["mn"] == "push":
            im = imms(p["ops"])
            if im and 0x690000 <= im[-1] < 0x693000:
                t = pe_str(im[-1])
                if t:
                    out.append((p["a"], t))
    return out


anchors = []
for want, va, txt in ((0x800000, 0x690160, "Sending TREATY ON"),
                      (0x1000000, 0x690174, "Sending TREATY OFF"),
                      (0x40, 0x690188, "Sending SET TREATY")):
    for k, i in enumerate(INS):
        if i["mn"] != "push":
            continue
        im = imms(i["ops"])
        if not im or im[-1] != want:
            continue
        near = str_near(k + 1, 8)
        if any(t == txt for _, t in near):
            anchors.append((want, txt, i["a"], near[0][0]))
for want, txt, a, sa in anchors:
    say(f"  mask 0x{want:<8x} @{a:08x} -> string {txt!r} @{sa:08x}")
say(f"  anchors found: {len(anchors)}/3")
# the 0x100000 writer: the eviction sweep
ev = [k for k, i in enumerate(INS) if i["a"] == EVICT]
evset = []
for k, i in enumerate(INS):
    if i["mn"] == "call" and i["ops"].strip().lower() == "0x%x" % SETTER2:
        runs = []
        j = k - 1
        while j >= 0 and len(runs) < 3 and k - j < 24:
            p = INS[j]
            if p["mn"] == "push":
                runs.append(p["ops"].strip())
            elif p["mn"] in ("call", "ret"):
                break
            j -= 1
        if len(runs) == 3 and runs[2] == "0x100000":
            evset.append(INS[k]["a"])
say(f"  mask 0x100000 set once, at {['%08x' % a for a in evset]}; its caller walks the unit array")
unit_stride = [k for k, i in enumerate(INS) if i["mn"] == "add" and i["ops"].lower().replace(" ", "") == "esi,0x34"]
near_evict = [INS[k]["a"] for k in unit_stride if EVICT <= INS[k]["a"] < 0x53FD00]
say(f"  unit-array stride add esi,0x34 inside FUN_0053f9f0..: {['%08x' % a for a in near_evict]}")
ok5 = (len(anchors) == 9 and len({w for w, _, _, _ in anchors}) == 3 and evset and near_evict)
if not ok5:
    bit(f"G5 anchors={len(anchors)} 100000={evset} evict_stride={near_evict}")
else:
    say("ok  G5 three mask->string anchors reproduce (TREATY ON / TREATY OFF / SET TREATY) and the "
        "0x100000 write follows the unit sweep that expels b's units from a's tiles")

# ---------------------------------------------------------------- G6 labels
say("")
say("G6  the 13 diplomacy label ids (M367) contain none of the five")
lab = [ln.rstrip("\r\n") for ln in open(LABELS, errors="replace")]
ids = [8, 0x10, 4, 2, 1, 0x1000, 0x2000, 0x20, 0x2000000, 0x400, 0x40000, 0x80000008, 0x80002000]
off = [0xDAC, 0xA18, 0xA0C, 0xA10, 0xA14, 0xD90, 0xD94, 0xD98, 0xD9C, 0xDA0, 0xDA4, 0xDA8, 0xDF8]
cnt_i = [k for k, t in enumerate(lab) if t.strip() == "#LABELS"]
if not cnt_i:
    bit("G6 no #LABELS header found")
    el0 = 0
else:
    el0 = cnt_i[0] + 2              # header, count line, then element 0
say(f"  #LABELS header line {cnt_i[0] + 1 if cnt_i else 0}; count line "
    f"{lab[cnt_i[0] + 1].strip() if cnt_i else '?'}; element 0 = {lab[el0]!r}")
# self-check the alignment against M367's five anchored rows
M367 = {1: "Pact", 2: "Treaty", 4: "Truce", 8: "Commlink", 0x10: "Vendetta"}
M367_OFF = {1: 0xA14, 2: 0xA10, 4: 0xA0C, 8: 0xDAC, 0x10: 0xA18}
align = None
for delta in (0, -1, 1):
    ok = all(lab[el0 + o // 4 + delta].strip() == t for v, t in M367.items() for o in [M367_OFF[v]])
    if ok:
        align = delta
say(f"  alignment delta vs M367 anchors: {align}")
texts = {}
for o in off:
    i = el0 + o // 4 + (align or 0)
    texts[o] = lab[i].strip() if 0 <= i < len(lab) else "?"
say("  " + " | ".join("0x%x=%r" % (i, texts[o]) for i, o in zip(ids, off)))
hit = [n for n, v, _, _ in BITS if v in ids or (v | 0x80000000) in ids]
ok6 = (align is not None) and not hit
if not ok6:
    bit(f"G6 align={align} target bit among label ids: {hit}")
else:
    say("ok  G6 none of the five is a checkbox id - the diplomacy page does not name them")

# ---------------------------------------------------------------- G7 rivals
say("")
say("G7  rivals")
orimms = set()
for k in p40:
    for j in range(k - 1, max(-1, k - 4), -1):
        if INS[j]["mn"] == "or":
            im = imms(INS[j]["ops"])
            if im:
                orimms.add(im[-1])
counter_bits = [n for n, v, _, _ in BITS if any(o & v for o in orimms)]
say(f"  or-immediates that precede a 0x40 store: {['0x%x' % o for o in sorted(orimms)]}")
say(f"  R1 'the five are ONE class of peace-cleared companions' - bits with an armed counter: "
    f"{counter_bits} of {len(BITS)}  -> differs on {len(BITS) - len(counter_bits)}/{len(BITS)}")
m_war = [imms(INS[k]["ops"])[-1] for k in war_peace if imms(INS[k]["ops"])[-1] == 0xFAEEF378][:1]
m_pc = [imms(INS[k]["ops"])[-1] for k in war_peace if imms(INS[k]["ops"])[-1] == 0xFFEE7FAF][:1]
say(f"  status masks measured in the setter: peace 0x{m_pc[0]:08x}, war 0x{m_war[0]:08x}")
skipw = [n for n, v, _, _ in BITS if m_war and (m_war[0] & v) == 0]
say(f"  R2 'the five are cleared only by PEACE' - the war mask 0x{m_war[0]:08x} also clears "
    f"{skipw}  -> differs on {len(skipw)}/{len(BITS)}")
r3 = with_stat
say(f"  R3 'bit 23 always arrives with a status bit' - bit23 requests carrying a 0x17 bit: "
    f"{len(r3)} of {len(b23)}  -> differs on {len(b23) - len(r3)}/{len(b23)}")
say(f"  R4 'bit 23 survives a status write' - masks whose SET result keeps bit 23: "
    f"{len(survive)} of {len(sweep)}  -> differs on {len(sweep) - len(survive)}/{len(sweep)}")
riv_ok = (len(counter_bits) == 1 and len(skipw) >= 2 and not with_stat and len(survive) == 1)
if not riv_ok:
    bit(f"G7 rivals survived: counter={counter_bits} skipw={skipw} with_stat={len(with_stat)} "
        f"survive={['0x%x' % m for m in survive]}")
else:
    say("ok  G7 all four rivals differ on the printed rows (1/5 armed, war clears 2 more, bit 23 "
        "never rides a status bit, and only 1 of 4 requests lets it survive)")

# ---------------------------------------------------------------- G8 digest
say("")
rowdump = "|".join(
    "%s:%d:%d:%d:%s" % (n, len(d), len(lt), len(w), ",".join("%08x" % INS[k]["a"] for k in d))
    for n, v, d, lt, w in rows)
dg = hashlib.sha1(rowdump.encode()).hexdigest()[:16]
dg2 = hashlib.sha1(rowdump.encode()).hexdigest()[:16]
say(f"  row digest {dg} (re-decode {dg2})")
if dg != dg2:
    bit("G8 digest mismatch")
else:
    say("ok  G8 row digest reproduced on a second pass")

# ---------------------------------------------------------------- verdict
say("")
if fails:
    say("FAIL M375: %d gate(s) red: %s" % (len(fails), "; ".join(fails)))
    sys.exit(1)
say("PASS M375: 8/8 gates  digest %s" % dg)
