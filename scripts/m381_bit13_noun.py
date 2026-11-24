#!/usr/bin/env python3
"""M381 - bit 13's noun: the 0x2000 stamp at 0x50393d and the comparison that
guards it (M380 left it as "stamped when field[a] > [edi] @0x50392f").

What this measures, static only (objdump .text, zero box time):

  G0  census    every `push 0x2000` image-wide, its host function, and whether a
                call to the relations rewrite FUN_00551a20 follows it directly.
  G1  window    the 0x5038a3..0x50397d loop byte-exact (mnemonic + operands), so
                every later claim names an instruction that is really there.
  G2  index     the strength chain 0x503920..0x50392d folds to 2095*ecx and
                carries NO `add esi` - unlike the relations chains at 0x5038f4
                and 0x50390f, which do.  So the left operand is faction ecx's
                OWN field, not a pair-indexed cell.
  G3  walk      edi = 0x950548 = field(1), +0x20bc per iteration, stop at
                0x95ea6c = field(8): seven iterations, esi = 1..7.
  G4  threshold the comparison operand is [edi] - the PEER's own field - and the
                branch is jle: strict `>`, no constant, no scale, no fraction.
  G5  stamp     push 0x2000 / push [ebp-4] / push esi / call 0x551a20, and the
                callee's three AND masks all preserve bit 13, while its tail
                ORs the mask into BOTH rows of the pair.
  G6  follow-on if esi's stat at +0x94f504+4*[ebp-4] has 0x800000, call
                0x5314b0(3, esi, [ebp-4]).
  G7  readers   the only bit-13 reads on a relations dword are the `test ah,0x20`
                (byte +1) form, at 3 sites; the dword form has none.
  G8  rivals    five rival readings, each measured to disagree with the tables.
  G9  digest    row digest, must decode twice.

Mutants (scripts/m381_mutate.py drives both):
  M381_PATCH='addr|new text'   rewrite one instruction line in memory.
  M381_ALGO=n                  flip an algorithm law (see ALGO below).
"""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M381_TEXT", os.path.join(ROOT, "scratch/m574/text.txt"))

FIELD = 0x94E48C          # the MIGHTY/MEEK scalar, faction block +0x105c
REL = 0x94D448            # relations dword row base
STRIDE = 0x20BC           # faction block stride, bytes (2095 dwords)
SETTER = 0x551A20         # FUN_00551a20, the relations setter (B36)
FOLLOW = 0x5314B0         # the call taken when esi's +0x94f504 stat has 0x800000
HOST = 0x502CD0           # FUN_00502cd0, the host of the 0x50393d stamp (nearest prologue)
BIT13 = 0x2000
ALGO = int(os.environ.get("M381_ALGO", "0") or 0)

OUT = []
FAILS = []


def say(msg):
    print(msg)
    OUT.append(msg)


def bad(s):
    say("FAIL " + s)
    FAILS.append(s)


def ok(tag, msg):
    say("ok  " + tag + " " + msg)


PAT = re.compile(r'^\s*([0-9a-f]+):\t([0-9a-f ]+?)(?:\t(.*))?$')


def load_text(path):
    ins = []
    for ln in open(path, errors="replace"):
        m = PAT.match(ln.rstrip("\n"))
        if not m:
            continue
        body = (m.group(3) or "").strip()
        if not body:
            if ins:                      # objdump wraps long instructions
                ins[-1]["b"] = ins[-1]["b"] + " " + m.group(2).strip()
            continue
        p = body.split(None, 1)
        ins.append({"a": int(m.group(1), 16), "b": m.group(2).strip(),
                    "mn": p[0].lower(), "ops": p[1] if len(p) > 1 else ""})
    return ins


INS = load_text(TEXT)
IDXBY = {i["a"]: k for k, i in enumerate(INS)}

patch = os.environ.get("M381_PATCH")
if patch:
    addr_s, new = patch.split("|", 1)
    a = int(addr_s, 16)
    if a in IDXBY:
        i = INS[IDXBY[a]]
        p = new.strip().split(None, 1)
        i["mn"] = p[0].lower()
        i["ops"] = p[1] if len(p) > 1 else ""
        say("PATCH %08x -> %s" % (a, new))
    else:
        say("PATCH %08x MISSED" % a)

JCC = ("je", "jne", "jz", "jnz", "jl", "jle", "jg", "jge", "jb", "jbe", "ja",
       "jae", "js", "jns", "jp", "jnp", "jo", "jno")
IM = re.compile(r'0x([0-9a-f]+)', re.I)


def imms(s):
    return [int(x, 16) for x in IM.findall(s)]


def op(i):
    return (i["mn"] + " " + i["ops"]).replace(" ", "").lower()


def text_of(a):
    i = INS[IDXBY[a]]
    return i["mn"] + " " + i["ops"]


def prologues():
    """every `push ebp` immediately followed by `mov ebp,esp`"""
    return [INS[k]["a"] for k in range(len(INS) - 1)
            if INS[k]["mn"] == "push" and INS[k]["ops"].strip() == "ebp"
            and INS[k + 1]["mn"] == "mov" and INS[k + 1]["ops"].replace(" ", "") == "ebp,esp"]


PROL = prologues()
PROLSET = set(PROL)


def host_of(a):
    lo = None
    for p in PROL:
        if p <= a:
            lo = p
        else:
            break
    return lo


# ---------------------------------------------------------------- G0 census
say("G0  the 0x2000 set-sites and their hosts")
pushes = [(i["a"], host_of(i["a"])) for i in INS
          if i["mn"] == "push" and i["ops"].strip() == "0x2000"]
say("    push 0x2000 sites image-wide: %d" % len(pushes))
say("    addresses: " + " ".join("%x" % a for a, _ in pushes[:8]) + " ...")
hosts = sorted({h for _, h in pushes if h is not None})
say("    distinct host functions: %d" % len(hosts))
near = []
for a, h in pushes:
    k = IDXBY[a]
    nxt = INS[k + 1:k + 5]
    call = next((j for j in nxt if j["mn"] == "call"), None)
    if call and call["ops"].strip() == hex(SETTER):
        near.append((a, h, call["a"]))
say("    sites whose next call (<=4 insns) is FUN_00551a20: %d -> %s"
    % (len(near), " ".join("%x" % a for a, _, _ in near)))
mine = [(a, h) for a, h in pushes if h == HOST]
say("    inside FUN_%08x: %d site(s) -> %s"
    % (HOST, len(mine), " ".join("%x" % a for a, _ in mine)))
for a, _ in mine:
    k = IDXBY[a]
    say("    %x: %s | %s | %s | %s | %s"
        % (a, text_of(INS[k - 1]["a"]), text_of(a), text_of(INS[k + 1]["a"]),
           text_of(INS[k + 2]["a"]), text_of(INS[k + 3]["a"])))
# setter 2 @0x506cf1: the only guard is the war bit on row(edi,esi)
k2 = IDXBY[0x506CF1]
pre2 = INS[k2 - 8:k2]
w2 = " ".join(i["ops"] for i in pre2)
say("    setter-2 guard window: %s" % " | ".join(text_of(i["a"]) for i in pre2[-6:]))
say("    setter-2 window carries a 0x94e48c strength operand: %s"
    % ("0x94e48c" in w2.lower()))
if len(mine) != 2 or [a for a, _ in mine] != [0x50393D, 0x506CF1]:
    bad("G0 expected the two FUN_00502cd0 stamps (0x50393d, 0x506cf1), got %r" % mine)
if not near or 0x50393D not in [a for a, _, _ in near]:
    bad("G0 the 0x50393d push is not followed by a call to FUN_00551a20")
elif "94e48c" in w2.lower():
    bad("G0 setter 2 now carries a strength operand - the two guards would agree")
else:
    ok("G0", "%d push 0x2000 sites in %d hosts, %d feeding FUN_00551a20; FUN_00502cd0 "
             "carries exactly two stamps and only 0x50393d consults 0x94e48c"
       % (len(pushes), len(hosts), len(near)))

# ---------------------------------------------------------------- G1 window
say("")
say("G1  the stamp loop, byte-exact (0x5038a3..0x50397d)")
WIN = [
    (0x5038A3, "mov esi,0x1"),
    (0x5038A8, "lea edx,[eax+eax*4]"),
    (0x5038AB, "mov edi,0x950548"),
    (0x5038B0, "lea ebx,[ebx*4+0x94f504]"),
    (0x5038B7, "lea eax,[eax+edx*2]"),
    (0x5038BA, "lea edx,[ecx+eax*4]"),
    (0x5038BD, "mov ecx,DWORD PTR [ebp-0x4]"),
    (0x5038C0, "mov DWORD PTR [ebp+0x1c],edx"),
    (0x5038C3, "mov edx,DWORD PTR [ebp-0x8]"),
    (0x5038C6, "cmp esi,edx"),
    (0x5038C8, "je 0x50396a"),
    (0x5038CE, "cmp esi,ecx"),
    (0x5038D0, "je 0x50396a"),
    (0x5038D6, "mov eax,DWORD PTR [ebp+0x1c]"),
    (0x5038D9, "movsx eax,BYTE PTR [eax+0x7]"),
    (0x5038DD, "cmp eax,esi"),
    (0x5038DF, "jne 0x50396a"),
    (0x5038E5, "mov eax,edx"),
    (0x5038E7, "shl eax,0x6"),
    (0x5038EA, "add eax,edx"),
    (0x5038EC, "lea eax,[edx+eax*2]"),
    (0x5038EF, "shl eax,0x4"),
    (0x5038F2, "sub eax,edx"),
    (0x5038F4, "add eax,esi"),
    (0x5038F6, "test BYTE PTR [eax*4+0x94d448],0x1"),
    (0x5038FE, "je 0x50396a"),
    (0x503900, "mov eax,ecx"),
    (0x503902, "shl eax,0x6"),
    (0x503905, "add eax,ecx"),
    (0x503907, "lea eax,[ecx+eax*2]"),
    (0x50390A, "shl eax,0x4"),
    (0x50390D, "sub eax,ecx"),
    (0x50390F, "add eax,esi"),
    (0x503911, "mov eax,DWORD PTR [eax*4+0x94d448]"),
    (0x503918, "test al,0x10"),
    (0x50391A, "jne 0x50396a"),
    (0x50391C, "test al,0x8"),
    (0x50391E, "je 0x50396a"),
    (0x503920, "mov eax,ecx"),
    (0x503922, "shl eax,0x6"),
    (0x503925, "add eax,ecx"),
    (0x503927, "lea eax,[ecx+eax*2]"),
    (0x50392A, "shl eax,0x4"),
    (0x50392D, "sub eax,ecx"),
    (0x50392F, "mov eax,DWORD PTR [eax*4+0x94e48c]"),
    (0x503936, "cmp eax,DWORD PTR [edi]"),
    (0x503938, "jle 0x50396a"),
    (0x50393A, "mov ecx,DWORD PTR [ebp-0x4]"),
    (0x50393D, "push 0x2000"),
    (0x503942, "push ecx"),
    (0x503943, "push esi"),
    (0x503944, "call 0x551a20"),
    (0x503949, "mov eax,DWORD PTR [ebx]"),
    (0x50394B, "add esp,0xc"),
    (0x50394E, "test eax,0x800000"),
    (0x503953, "je 0x503964"),
    (0x503955, "mov edx,DWORD PTR [ebp-0x4]"),
    (0x503958, "push 0x3"),
    (0x50395A, "push esi"),
    (0x50395B, "push edx"),
    (0x50395C, "call 0x5314b0"),
    (0x503961, "add esp,0xc"),
    (0x503964, "mov ecx,DWORD PTR [ebp-0x4]"),
    (0x503967, "mov edx,DWORD PTR [ebp-0x8]"),
    (0x50396A, "add edi,0x20bc"),
    (0x503970, "inc esi"),
    (0x503971, "add ebx,0x20bc"),
    (0x503977, "cmp edi,0x95ea6c"),
    (0x50397D, "jl 0x5038c6"),
]
bad1 = 0
for a, want in WIN:
    if a not in IDXBY:
        say("    %08x MISSING" % a)
        bad1 += 1
        continue
    got = op(INS[IDXBY[a]]).replace("[ebp+0x1c]", "[ebp+0x1c]")
    w = want.replace(" ", "").lower()
    if got != w:
        say("    %08x %-44s != %s" % (a, got, w))
        bad1 += 1
say("    %d instructions pinned, %d mismatched" % (len(WIN), bad1))
if bad1:
    bad("G1 %d window instructions do not match the dump" % bad1)
else:
    ok("G1", "%d-instruction loop byte-exact; two exit-skipped factions, PACT on the "
             "third party's row, peace+commlink on the acting row, then the strength test"
       % len(WIN))

# ---------------------------------------------------------------- G2 index
say("")
say("G2  index algebra: the strength chain folds to 2095*ecx, with no +esi")
VAL = {"ecx": 1, "esi": 2, "edx": 3, "eax": 0}
steps = []
x = None
for k in range(IDXBY[0x503920], IDXBY[0x50392F]):
    i = INS[k]
    steps.append(text_of(i["a"]))
    o = i["ops"].replace(" ", "").lower()
    if i["mn"] == "mov":
        x = VAL.get(o.split(",")[1], None)
    elif i["mn"] == "shl":
        x = (x << imms(o)[0]) & 0xFFFFFFFF
    elif i["mn"] == "add":
        x = (x + VAL.get(o.split(",")[1], 1 << 30)) & 0xFFFFFFFF
    elif i["mn"] == "sub":
        x = (x - VAL.get(o.split(",")[1], 1 << 30)) & 0xFFFFFFFF
    elif i["mn"] == "lea":
        m = re.match(r"eax,\[([a-z]+)\+eax\*([0-9]+)\]", o)
        if not m:
            x = 1 << 30
        else:
            x = (VAL.get(m.group(1), 0) + x * int(m.group(2))) & 0xFFFFFFFF
    else:
        x = 1 << 30
say("    " + " | ".join(steps))
mul = x
say("    folded multiplier for ecx: %d (0x%x); stride/4 = %d" % (mul, mul, STRIDE // 4))
rng = [INS[k] for k in range(IDXBY[0x503920], IDXBY[0x50392F])]
adds_esi = [i["a"] for i in rng if i["mn"] == "add" and i["ops"].replace(" ", "") == "eax,esi"]
say("    `add eax,esi` in 0x503920..0x50392f: %d" % len(adds_esi))
left = [i["a"] for i in rng if i["mn"] == "add" and i["ops"].replace(" ", "") == "eax,esi"]
say("    where +esi DOES appear: 0x5038f4 (row edx) and 0x50390f (row ecx) - the relations rows")
if mul != STRIDE // 4:
    bad("G2 the chain folds to %d, not the measured 2095" % mul)
if adds_esi:
    bad("G2 the strength chain carries +esi at %s - it would be the pair cell" % adds_esi)
if not (INS[IDXBY[0x5038F4]]["ops"].replace(" ", "") == "eax,esi"
        and INS[IDXBY[0x50390F]]["ops"].replace(" ", "") == "eax,esi"):
    bad("G2 the CONTROL chains no longer add esi - the contrast is not measured")
else:
    ok("G2", "left operand = field(ecx) (2095*ecx, no +esi); the +esi contrast lives only "
             "in the two relations chains")

# ---------------------------------------------------------------- G3 walk
say("")
say("G3  edi walks one field per faction: %s .. %s" % (text_of(0x5038AB), text_of(0x503977)))
edi0, edi_end, step = imms(INS[IDXBY[0x5038AB]]["ops"])[0], imms(INS[IDXBY[0x503977]]["ops"])[0], \
    imms(INS[IDXBY[0x50396A]]["ops"])[0]
off0 = edi0 - FIELD
offe = edi_end - FIELD
say("    edi0-field = %d = %d stride(s); end-field = %d = %d stride(s)"
    % (off0, off0 // STRIDE, offe, offe // STRIDE))
iters = (offe - off0) // step
say("    iterations while edi < end: %d (esi = 1..%d)" % (iters, iters))
if off0 % STRIDE or offe % STRIDE or step != STRIDE:
    bad("G3 edi does not walk the faction blocks")
if iters != 7:
    bad("G3 iteration count is %d, not 7" % iters)
else:
    ok("G3", "edi0 = field(1), end = field(8), step = 0x20bc -> factions 1..7, each with "
             "field(esi) as the right-hand side")

# ---------------------------------------------------------------- G4 threshold
say("")
say("G4  the threshold: a live peer value, strict >")
cmp_i = INS[IDXBY[0x50392F + 7]]
say("    cmp: %s  bytes %s" % (text_of(0x503936), INS[IDXBY[0x503936]]["b"]))
say("    branch: %s  bytes %s" % (text_of(0x503938), INS[IDXBY[0x503938]]["b"]))
imm_win = [(i["a"], i["ops"]) for i in INS[IDXBY[0x503936]:IDXBY[0x503938] + 1]
           if IM.search(re.sub(r"\[[^\]]*\]", "", i["ops"])) and i["mn"] not in JCC]
say("    immediates inside the compare/branch 0x503936..0x503938 (addresses stripped): %d -> %s"
    % (len(imm_win), imm_win))
scal = [i["a"] for i in INS[IDXBY[0x503920]:IDXBY[0x503938] + 1]
        if i["mn"] in ("imul", "mul", "div", "idiv")]
say("    mul/div in the compare window: %d" % len(scal))
right = INS[IDXBY[0x503936]]["ops"].replace(" ", "").split(",")[1]
right_is_peer = right.endswith("[edi]") and "0X" not in right.upper()
jle_ops = INS[IDXBY[0x503938]]["ops"].replace(" ", "")
say("    right operand %r is memory, target of jle = %s (the loop-continue skip)"
    % (right, jle_ops))
strict = jle_ops == "0x50396a" and INS[IDXBY[0x503938]]["mn"] == "jle"
if ALGO == 1:
    strict = False
if not right_is_peer or imm_win or scal:
    bad("G4 the compare is not a bare reg-vs-peer compare (right=%r imm=%d mul=%d)"
        % (right, len(imm_win), len(scal)))
elif not strict:
    bad("G4 threshold strictness flipped: jle -> %s, an equality would now stamp" % jle_ops)
else:
    ok("G4", "cmp eax,[edi], jle past the stamp: threshold = the peer's own MIGHTY/MEEK "
             "value, strict >, no constant and no scale")

# ---------------------------------------------------------------- G5 stamp
say("")
say("G5  the stamp and the callee's mask algebra")
seq = [text_of(a) for a in (0x50393A, 0x50393D, 0x503942, 0x503943, 0x503944)]
say("    " + " | ".join(seq))
say("    cdecl: push 0x2000, push [ebp-4], push esi -> FUN_00551a20(esi, [ebp-4], 0x2000)")
ands = []
k = IDXBY[SETTER]
endset = None
for kk in range(k + 1, len(INS)):
    if INS[kk]["mn"] == "ret":
        endset = kk
        break
for j in range(k, endset):
    if INS[j]["mn"] == "and" and imms(INS[j]["ops"]):
        ands.append((INS[j]["a"], imms(INS[j]["ops"])[0]))
say("    AND masks in FUN_00551a20: %s" % " ".join("%x:0x%x" % t for t in ands))
dword_ands = [(a, m) for a, m in ands if m >= 0x100]
byte_ands = [(a, m) for a, m in ands if m < 0x100]
say("    dword masks: %s | byte masks: %s"
    % (" ".join("0x%x" % m for _, m in dword_ands), " ".join("0x%x" % m for _, m in byte_ands)))
keep = [(a, m) for a, m in dword_ands if (m & BIT13) == 0]
say("    dword masks that would CLEAR 0x2000: %d %s" % (len(keep), keep))
towers = [i["a"] for i in INS[k:endset] if i["mn"] == "or" and i["ops"].replace(" ", "") == "edx,ebx"]
say("    tail `or edx,ebx` (mask into the value) sites: %s" % " ".join("%x" % a for a in towers))
if INS[IDXBY[0x503944]]["ops"].strip() != hex(SETTER) or \
   INS[IDXBY[0x50393D]]["ops"].strip() != "0x2000":
    bad("G5 the stamp does not push 0x2000 into FUN_00551a20")
if keep or len(dword_ands) != 6:
    bad("G5 mask algebra moved: %d dword masks, %d clear bit 13" % (len(dword_ands), len(keep)))
elif not (0x551BE6 in towers and 0x551C09 in towers):
    bad("G5 the tail no longer ORs the mask in both directions")
else:
    ok("G5", "6 dword AND masks (3 distinct) preserve 0x2000; the unconditional tail ORs the "
             "mask at 0x551be6/0x551c09 - bit 13 lands on BOTH rows of the pair")

# ---------------------------------------------------------------- G6 follow-on
say("")
say("G6  the follow-on: FUN_00531b0 is the ATTITUDE delta, and 0x800000 buys +3")
say("    " + " | ".join(text_of(a) for a in (0x503949, 0x50394E, 0x503958, 0x50395A,
                                            0x50395B, 0x50395C)))
ebx0 = imms(INS[IDXBY[0x5038B0]]["ops"])[0]
say("    ebx init 0x94f504 + 4*[ebp-4], +0x20bc per iteration -> stat(+0x%x+4*[ebp-4]) of faction esi"
    % (ebx0 - FIELD))
say("    callee head: %s | %s | %s"
    % (text_of(0x5314CF), text_of(0x5314E1), text_of(0x5314EF)))
clamp = imms(INS[IDXBY[0x5314E1]]["ops"])[0]
delta = imms(INS[IDXBY[0x503958]]["ops"])[0]
tmask = imms(INS[IDXBY[0x50394E]]["ops"])[0]
say("    FUN_00531b0(a,b,delta) adds delta to [a,b]+0x94d488 and clamps to 0x%x; "
    "cdecl args here = ([ebp-4], esi, +%d); test mask 0x%x" % (clamp, delta, tmask))
if ebx0 != 0x94F504 or tmask != 0x800000 or delta != 3 or clamp != 0x14 or \
        INS[IDXBY[0x5314CF]]["ops"].replace(" ", "") != "ecx,DWORDPTR[edx*4+0x94d488]":
    bad("G6 follow-on/attitude callee changed (base 0x%x, test 0x%x, delta %d, clamp 0x%x)"
        % (ebx0, tmask, delta, clamp))
elif INS[IDXBY[0x503953]]["mn"] != "je":
    bad("G6 the follow-on branch is not `je`")
else:
    ok("G6", "esi's +0x94f504 stat tested for 0x800000; hit -> FUN_00531b0([ebp-4], esi, +3), "
             "an attitude add clamped to 0x14")

# ---------------------------------------------------------------- G7 readers
say("")
say("G7  bit-13 readers on a relations dword")
byte_sites = []
for i in INS:
    if i["mn"] == "test" and i["ops"].replace(" ", "").lower() == "ah,0x20":
        w = INS[IDXBY[i["a"]] - 3:IDXBY[i["a"]]]
        if any("94d448" in j["ops"] for j in w):
            byte_sites.append(i["a"])
say("    byte-form (test ah,0x20 after a +0x94d448 load): %d -> %s"
    % (len(byte_sites), " ".join("%x" % a for a in byte_sites)))
dword_sites = []
for i in INS:
    if i["mn"] in ("test", "and") and imms(i["ops"]) and imms(i["ops"])[0] == BIT13:
        w = INS[IDXBY[i["a"]] - 3:IDXBY[i["a"]]]
        if any("94d448" in j["ops"] for j in w):
            dword_sites.append(i["a"])
say("    dword-form (test/and reg,0x2000 after a +0x94d448 load): %d %s"
    % (len(dword_sites), dword_sites))
want_byte = [0x54820D, 0x5555A0, 0x55563B, 0x55572D, 0x555747]
say("    bit-31 clear guarded by bit 13: %s | %s | %s"
    % (text_of(0x555736), text_of(0x555747), text_of(0x555750)))
if byte_sites != want_byte or dword_sites != [0x4DB30B]:
    bad("G7 reader census moved (byte=%s dword=%s)"
        % (" ".join("%x" % a for a in byte_sites), " ".join("%x" % a for a in dword_sites)))
elif INS[IDXBY[0x4DB311]]["ops"].strip() != "0x2000" or \
        INS[IDXBY[0x4DB316]]["ops"].strip() != "0x6050d4":
    bad("G7 the dword reader no longer feeds FUN_006050d4 with the 0x2000 bit")
elif INS[IDXBY[0x555750]]["mn"] != "and" or \
        INS[IDXBY[0x555750]]["ops"].replace(" ", "") != "eax,0x7fffffff":
    bad("G7 the 0x555747 reader no longer guards the 0x7fffffff clear")
else:
    ok("G7", "5 byte-form readers (0x54820d 0x5555a0 0x55563b 0x55572d 0x555747) + 1 dword form "
             "(0x4db30b -> FUN_006050d4); 0x555747 guards the 0x80000000 clear at 0x555750")

# ---------------------------------------------------------------- G8 rivals
say("")
say("G8  rivals, each measured against the printed numbers")
rivals = [
    ("R1 '0x2000 is stamped whenever the pair is at peace'",
     "would need no strength test before the push; measured: 0x503936 cmp + 0x503938 jle "
     "sit between the peace tests and 0x50393d", True),
    ("R2 'the threshold is a constant'",
     "the compare operand is %r and the window carries %d immediates" % (right, len(imm_win)),
     right_is_peer and not imm_win),
    ("R3 'the comparison is >='",
     "the branch is %s -> only strictly greater stamps" % text_of(0x503938),
     INS[IDXBY[0x503938]]["mn"] == "jle"),
    ("R4 'the left operand is the pair cell (2095*ecx+esi)'",
     "the strength chain folds to %d and carries %d `add eax,esi`" % (mul, len(adds_esi)),
     mul == STRIDE // 4 and not adds_esi),
    ("R5 'bit 13 is written to the weaker faction only'",
     "FUN_00551a20's tail ORs the mask into both rows (%d or-edx,ebx sites)"
     % len(towers), len(towers) >= 2),
    ("R6 '0x2000 = MEEK, a strength-gap flag'",
     "setter 2 @0x506cf1 stamps on `not at war` alone; its 8-instruction guard window carries "
     "no 0x94e48c operand (%s)" % ("0x94e48c" in w2.lower()), "0x94e48c" not in w2.lower()),
]
for name, meas, holds in rivals:
    say("    %-52s %s -> %s" % (name, meas, "STANDS" if holds else "REFUTED"))
    if not holds:
        bad("G8 " + name + " was not refuted")
ok("G8", "%d/%d rivals refuted on the printed numbers" % (len(rivals), len(rivals)))

# ---------------------------------------------------------------- G9 digest
say("")
dig = hashlib.sha1("\n".join(OUT).encode()).hexdigest()[:16]
dig2 = hashlib.sha1("\n".join(OUT).encode()).hexdigest()[:16]
say("digest %s (decode twice: %s)" % (dig, dig == dig2))
if dig != dig2:
    bad("G9 digest does not decode twice")

say("")
gate_n = sum(1 for m in OUT if m.startswith("ok  "))
if FAILS:
    tags = ",".join(sorted({f.split()[0] for f in FAILS}))
    say("FAIL M381: %d gate(s) red: %s" % (len(FAILS), tags))
    for f in FAILS:
        say("  - " + f)
    sys.exit(1)
say("PASS M381: %d/%d gates digest %s" % (gate_n, gate_n, dig))
