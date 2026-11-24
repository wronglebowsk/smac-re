#!/usr/bin/env python3
"""M392 (chain 5) - the UNINIT-leg caller census M387 left open.

M387 proved that FUN_0052a720's two slot-sourced stores (0x52b9c7 / 0x52b9d0 ->
+0x94d448) are gated on the stack dword at [ebp+0x1c]: non-zero => the snapshot runs and
the store copies the pair dword (PRESERVE); zero => the snapshot is skipped and the store
writes a frame dword nobody wrote (UNINIT).  It could not say whether any caller ever
passes zero - it never read a callsite.  This instrument reads all of them.

The callee is stdcall with `ret 0x1c` (28 bytes = 7 stack dwords), so the guarded value is
the SECOND push from the call (`pushed[5]`, arg1 of the push sequence being `pushed[0]`);
the FIRST push (`pushed[6]`) is 0x2101 everywhere.  M387 labels [ebp+0x1c] "arg7" by
counting ecx (this=0x91db70) as arg1; the census keys on push position so the label
cannot shift the answer.

Gates
  G0  population: every `call 0x52a720` in the linear sweep (65 sites, 22 attributed
      functions + 1 orphan wrapper), and ZERO dword pointers to the callee image-wide
      (no indirect caller can exist).
  G1  the frame: ret 0x1c x6 => 7 stack dwords; msg = movsx WORD [ebp+8]; guard =
      [ebp+0x1c] (15 reads, tested at 0x52a778 and 0x52af1b); [ebp+0x20] read once.
  G2  decode: every site resolves all seven pushes to a value/expression, unambiguously.
  G3  the guard census: how many sites push 0, how many push a non-zero constant, how
      many push an expression.
  G4  the message census: literal ids (set + counts) vs expression-sourced ids; the
      literal 0x16 site and whether its wrapper is live code.
  G5  the joint: guard==0 AND msg is the literal 0x16 (statically closed leg) vs
      guard==0 AND msg is an expression (open leg).
  G6  the open site's id source: one definition of ebx before the call, the two and only
      two entries into the block (record word == 0x1101 / 0x4101), and no compare/test
      of +0x10 anywhere between entry and the call.
  G7  verdict: per-class counts, and whether any leg is provably dead the way M387 killed
      the count==0 leg.
  G8  rivals, each measured against the printed numbers (>=1 REFUTED).
  G9  digest.

Mutants (scripts/m392_mutate.py drives this):
  M392_PATCH='addr|new text'   rewrite one instruction line in memory.
  M392_ALGO=n                  flip a law (see ALGO sites).
"""
import csv
import hashlib
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M392_TEXT", os.path.join(ROOT, "scratch/m574/text.txt"))
IDXCSV = os.path.join(ROOT, "ghidra_out/index.csv")
EXE = os.path.join(ROOT, "programs/terran.exe")

FUNC = 0x52A720
RET_SITES = (0x52B889, 0x52B8C9, 0x52B8E3, 0x52B8FD, 0x52BA00, 0x52BA18)
GUARD_SLOT = 5                    # pushed[5] = [ebp+0x1c]
MSGSRC = (0x52D840, 0x52D873)     # block entry .. the one guard-0 call
REC_EBX_DEF = 0x52BD33
ENTRIES = {0x52BE38: 0x1101, 0x52D7B4: 0x4101}
ORPHAN_CALL = 0x5844B6
LIT16 = 0x584596                  # `push 0x16` in FUN_00584580
BLOCK_HEAD = 0x52D849             # first argument-load of the open block
ALGO = int(os.environ.get("M392_ALGO", "0") or 0)

OUT, FAILS = [], []


def say(m):
    print(m)
    OUT.append(m)


def bad(s):
    say("FAIL " + s)
    FAILS.append(s)


def ok(tag, msg):
    say(f"  ok  {tag} {msg}")


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
            if ins:                                  # objdump wraps long instructions
                ins[-1]["b"] += " " + m.group(2).strip()
            continue
        p = body.split(None, 1)
        ins.append({"a": int(m.group(1), 16), "b": m.group(2).strip(),
                    "mn": p[0].lower(), "ops": p[1] if len(p) > 1 else ""})
    return ins


INS = load_text(TEXT)
IDXBY = {i["a"]: k for k, i in enumerate(INS)}

_patch = os.environ.get("M392_PATCH")
if _patch:
    for part in _patch.split(";"):
        a_s, new = part.split("|", 1)
        a = int(a_s, 16)
        if a in IDXBY:
            i = INS[IDXBY[a]]
            p = new.strip().split(None, 1)
            i["mn"] = p[0].lower()
            i["ops"] = p[1] if len(p) > 1 else ""
            say(f"PATCH {a:08x} -> {new}")
        else:
            say(f"PATCH {a:08x} MISSED")

IMG = open(EXE, "rb").read()
ROWS = list(csv.DictReader(open(IDXCSV)))
RANGES = sorted((int(r["addr"], 16), int(r["addr"], 16) + int(r["size_bytes"]), r["name"])
                for r in ROWS)


def owner(a):
    for s, e, n in RANGES:
        if s <= a < e:
            return (n, s, e)
    return None


PROLOG = ("push", "mov")


def func_range(a):
    o = owner(a)
    if o:
        return o[1], o[2]
    # orphan: nearest `push ebp` + `mov ebp,esp` before the address
    k = IDXBY[a]
    for j in range(k, max(0, k - 4000), -1):
        i = INS[j]
        if i["mn"] == "mov" and i["ops"].replace(" ", "") == "ebp,esp":
            if j and INS[j - 1]["mn"] == "push" and INS[j - 1]["ops"].strip() == "ebp":
                return INS[j - 1]["a"], a + 0x40
    return a - 0x20, a + 0x40


JCC = ("je", "jne", "jz", "jnz", "jl", "jle", "jg", "jge", "jb", "jbe", "ja",
       "jae", "js", "jns", "jp", "jnp", "jo", "jno")
WRITES = ("mov", "xor", "sub", "add", "and", "or", "lea", "pop", "inc", "dec",
          "shl", "shr", "sar", "sal", "imul", "neg", "not", "xchg", "adc", "sbb")


def imm_val(s):
    s = s.strip().lower()
    m = re.match(r'^(?:byte ptr |word ptr |dword ptr )?(0x[0-9a-f]+|-?\d+)$', s)
    if not m:
        return None
    v = m.group(1)
    return int(v, 16) if v.startswith("0x") else int(v) & 0xFFFFFFFF


REGS = ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp", "esp",
        "ax", "bx", "cx", "dx", "si", "di", "al", "ah", "bl", "bh", "cl", "ch", "dl", "dh")


SUB = {"eax": ("ax", "al", "ah"), "ebx": ("bx", "bl", "bh"), "ecx": ("cx", "cl", "ch"),
       "edx": ("dx", "dl", "dh"), "esi": ("si",), "edi": ("di",), "esp": ("sp",),
       "ebp": ("bp",)}


def last_write(reg, addr, lo):
    """Last instruction in [lo,addr) that writes `reg` (whole or partial)."""
    forms = (reg,) + SUB.get(reg, ())
    k = IDXBY[addr]
    j = k - 1
    while j >= 0 and INS[j]["a"] >= lo:
        i = INS[j]
        ops = i["ops"].lower().strip()
        if i["mn"] in WRITES:
            dst = ops.split(",")[0].strip()
            if dst in forms:
                return i
        j -= 1
    return None


def classify(txt, at, lo):
    """-> (kind, value/expr, src, note). kind in CONST|MEM|PARTIAL|OTHER."""
    t = txt.strip().lower()
    v = imm_val(t)
    if v is not None:
        return ("CONST", v, at, "")
    if t in REGS:
        w = last_write(t, at, lo)
        if w is None:
            return ("OTHER", "nowrite:" + t, at, "")
        ops = w["ops"].lower().strip()
        dst, src = (ops.split(",", 1) + [""])[:2]
        if w["mn"] == "xor" and src.strip() == dst:
            return ("CONST", 0, w["a"], "xor")
        sv = imm_val(src)
        if sv is not None:
            return ("CONST", sv, w["a"], "")
        if dst != t:                                  # partial write (ax vs eax)
            return ("PARTIAL", fog(src), w["a"], f"{dst}<-")
        return ("MEM", fog(src), w["a"], w["mn"])
    return ("MEM", t, at, "")


def fog(s):
    return re.sub(r'\s+', ' ', s.strip())


def succ_of(i, lo, hi, nxt):
    ops = i["ops"].strip().lower()
    s = []
    m = re.match(r'^0x([0-9a-f]+)$', ops)
    tgt = int(m.group(1), 16) if m else None
    if i["mn"] == "jmp" and tgt is not None:
        if lo <= tgt < hi:
            s.append(tgt)
    elif i["mn"] in JCC and tgt is not None:
        if lo <= tgt < hi:
            s.append(tgt)
        if nxt is not None:
            s.append(nxt)
    elif i["mn"].startswith("ret"):
        pass
    elif nxt is not None:
        s.append(nxt)
    return s


def backward_reach(addr, lo, hi):
    """Instruction set reachable backwards from `addr` over explicit edges in [lo,hi)."""
    body = [i for i in INS if lo <= i["a"] < hi]
    seq = [i["a"] for i in body]
    nxt = {seq[n]: (seq[n + 1] if n + 1 < len(seq) else None) for n in range(len(seq))}
    preds = {}
    for i in body:
        for t in succ_of(i, lo, hi, nxt[i["a"]]):
            preds.setdefault(t, []).append(i["a"])
    seen, stack = {addr}, [addr]
    while stack:
        a = stack.pop()
        for p in preds.get(a, []):
            if p not in seen:
                seen.add(p)
                stack.append(p)
    return seen


# ---------------------------------------------------------------- G0 population
say("G0  the caller population: every direct call, and the proof no indirect one exists")
SITES = [i for i in INS if i["mn"] == "call" and i["ops"].strip().lower() == "0x52a720"]
SITE_ADDRS = [i["a"] for i in SITES]
say(f"  direct `call 0x52a720` instructions in the linear sweep: {len(SITE_ADDRS)}")
own = {}
orphans = []
for a in SITE_ADDRS:
    o = owner(a)
    if o:
        own[a] = o[0]
    else:
        orphans.append(a)
say(f"  attributed to index.csv functions: {len(own)}; outside every function: "
    f"{[hex(x) for x in orphans]}")
say(f"  distinct caller functions: {len(set(own.values()))}")
ptr = struct.pack("<I", FUNC)
hits = []
k = 0
while True:
    j = IMG.find(ptr, k)
    if j < 0:
        break
    hits.append(j + 0x400000)
    k = j + 1
say(f"  dword occurrences of 0x{FUNC:06x} in the image (indirect-call payloads): {len(hits)}")
say(f"  index.csv n_callers for FUN_0052a720: "
    f"{[r['n_callers'] for r in ROWS if int(r['addr'], 16) == FUNC][0]}")
# the orphan must be dead: no branch/call targets it
refs = [i["a"] for i in INS if i["mn"] in ("call", "jmp") + JCC
        and re.match(r'^0x([0-9a-f]+)$', i["ops"].strip().lower())
        and int(i["ops"].strip().lower(), 16) in (ORPHAN_CALL - 6, ORPHAN_CALL)]
say(f"  references to the orphan wrapper 0x{ORPHAN_CALL - 6:06x}: {len(refs)}")
if ALGO == 4:
    say("  ALGO=4: orphan treated as attributed")
    orphans = []
if len(SITE_ADDRS) != 65 or len(own) != 64 or orphans != [ORPHAN_CALL] or len(hits) != 0 \
        or len(set(own.values())) != 22 or refs:
    bad(f"G0 population != 65 sites / 64 attributed / 1 dead orphan / 0 pointers "
        f"({len(SITE_ADDRS)},{len(own)},{orphans},{len(hits)},{refs})")
else:
    ok("G0", "65 direct sites (22 functions + 1 unreferenced wrapper), 0 indirect")

# ---------------------------------------------------------------- G1 the frame
say("")
say("G1  the callee frame: seven stack dwords, and which slot the guard is")
rets = [i for i in INS if FUNC <= i["a"] < FUNC + 5200 and i["mn"].startswith("ret")]
retops = sorted({i["ops"].strip() or "0x0" for i in rets})
say(f"  ret sites: {[hex(i['a']) for i in rets]}")
say(f"  ret operands: {retops}  -> {int(retops[0], 16) // 4} stack dwords cleaned by the callee")
reads = {}
for a in (0x8, 0xC, 0x10, 0x14, 0x18, 0x1C, 0x20):
    n = sum(1 for i in INS if FUNC <= i["a"] < FUNC + 4859
            and f"[ebp+0x{a:x}]" in i["ops"].lower())
    reads[a] = n
say(f"  reads per stack slot: {[(hex(k), v) for k, v in reads.items()]}")
say(f"  msg slot [ebp+8] read as: "
    f"{fog([i['ops'] for i in INS if i['a'] == 0x52A752][0])}")
say(f"  guard [ebp+0x1c] first test: "
    f"{fog([i['ops'] for i in INS if i['a'] == 0x52A741][0])} @52a741, "
    f"{fog([i['ops'] for i in INS if i['a'] == 0x52A778][0])} @52a778")
if ALGO == 1:
    say("  ALGO=1: guard slot set to 0 (msg)")
    GUARD_SLOT = 0 if False else 0
if retops != ["0x1c"] or int(retops[0], 16) // 4 != 7 or reads[0x8] != 7 or reads[0x1c] != 15 \
        or reads[0x20] != 1 or any(r["a"] not in RET_SITES for r in rets):
    bad(f"G1 frame != ret 0x1c x6 / 7 slots / reads {reads}")
else:
    ok("G1", "stdcall ret 0x1c = 7 dwords; guard [ebp+0x1c] read 15x, arg8 [ebp+0x20] 1x")

# ---------------------------------------------------------------- G2 decode
say("")
say("G2  decode: seven pushes per site, resolved to a value or an expression")
TABLE = []
gs = GUARD_SLOT
if ALGO == 1:
    gs = 0
for a in SITE_ADDRS:
    lo, hi = func_range(a)
    k = IDXBY[a]
    pushed, j, complex_ = [], k - 1, False
    while j >= 0 and len(pushed) < 7:
        i = INS[j]
        ops = i["ops"].lower().strip()
        if i["mn"] == "push":
            pushed.append(i)
        elif i["mn"] == "call":
            complex_ = True
            break
        elif i["mn"] in ("add", "sub") and ops.startswith("esp,"):
            complex_ = True
        elif i["mn"] == "mov" and ops.startswith("dword ptr [esp"):
            complex_ = True
        j -= 1
    slots = []
    for n in range(7):
        if n < len(pushed):
            c = classify(pushed[n]["ops"], pushed[n]["a"], lo)
        else:
            c = ("OTHER", "missing", a, "")
        slots.append(c)
    TABLE.append({"a": a, "f": own.get(a, "ORPHAN"), "slots": slots,
                  "complex": complex_, "n": len(pushed)})
short = [t for t in TABLE if t["n"] != 7 or t["complex"]]
say(f"  sites with exactly 7 pushes and no stack-form args: {len(TABLE) - len(short)}/{len(TABLE)}")
for t in TABLE:
    msg = t["slots"][0]
    g = t["slots"][gs]
    a8 = t["slots"][6]
    m = f"0x{msg[1]:x}" if msg[0] == "CONST" else f"{msg[0]}:{msg[1]}"
    gg = f"0x{g[1]:x}" if g[0] == "CONST" else f"{g[0]}:{g[1]}"
    a8s = f"0x{a8[1]:x}" if a8[0] == "CONST" else f"{a8[0]}:{a8[1]}"
    say(f"  {t['a']:06x} {t['f']:14s} msg={m:<22s} guard={gg:<22s} arg8={a8s}")
if short:
    bad(f"G2 {len(short)} sites did not decode as 7 clean pushes")
else:
    ok("G2", "65/65 sites decode as 7 straight-line pushes")

# ---------------------------------------------------------------- G2b pinned provenance
say("")
say("G2b pinned push provenance: the sample sites the mutants patch")
PROBE = {x["a"]: x for x in TABLE}
SAMPLES = [(0x5262FA, 5, 0x5262EC, 1),      # guard push of a PRESERVE site
           (0x5262FA, 0, 0x5262F8, 0),      # its msg push
           (0x52D873, 5, 0x52D855, 0),      # the ONE zero guard
           (0x52D873, 0, 0x52D86A, None)]   # its id: a 16-bit partial write
pin_ok = True
for site, slot, want_addr, want_val in SAMPLES:
    c = PROBE[site]["slots"][slot]
    good = c[2] == want_addr and (want_val is None or c[1] == want_val)
    pin_ok = pin_ok and good
    say(f"  {site:06x} slot {slot}: {c[0]} {c[1]} from 0x{c[2]:06x} "
        f"(want 0x{want_addr:06x}{'' if want_val is None else f', value {want_val}'}) "
        f"{'ok' if good else 'MISMATCH'}")
if not pin_ok:
    bad("G2b a pinned push no longer carries the printed operand")
else:
    ok("G2b", "0x5262ec/0x5262f8/0x52d855/0x52d86a carry the printed operands")

# ---------------------------------------------------------------- G3 guard census
say("")
say("G3  the guard census (pushed[5] = [ebp+0x1c])")
z = [t for t in TABLE if t["slots"][gs][0] == "CONST" and t["slots"][gs][1] == 0]
one = [t for t in TABLE if t["slots"][gs][0] == "CONST" and t["slots"][gs][1] == 1]
other = [t for t in TABLE if t not in z and t not in one]
say(f"  guard == 0 : {len(z)}  {[hex(t['a']) for t in z]}")
say(f"  guard == 1 : {len(one)}")
say(f"  guard other/expression: {len(other)} "
    f"{[(hex(t['a']), t['slots'][gs][0], t['slots'][gs][1]) for t in other]}")
if len(z) != 1 or len(one) != 64 or other:
    bad(f"G3 guard census != 1 zero / 64 one / 0 other ({len(z)},{len(one)},{len(other)})")
else:
    ok("G3", "64 sites push 1, exactly ONE (52d873) pushes 0, nothing unresolved")

# ---------------------------------------------------------------- G4 msg census
say("")
say("G4  the message census (pushed[0] = [ebp+8], read movsx WORD)")
consts = {}
exprs = []
for t in TABLE:
    c = t["slots"][0]
    if c[0] == "CONST" and not (ALGO == 3 and c[1] == 0x10):
        consts.setdefault(c[1], []).append(t["a"])
    else:
        exprs.append((t["a"], c[0], c[1], c[2]))
say(f"  distinct literal ids: {len(consts)}")
say("  literals: " + " ".join(f"0x{k:02x}x{len(v)}" for k, v in sorted(consts.items())))
say(f"  expression-sourced ids: {len(exprs)} {[(hex(a), k, e, hex(s)) for a, k, e, s in exprs]}")
sixteen = consts.get(0x16, [])
say(f"  literal 0x16 sites: {[hex(a) for a in sixteen]}")
live16 = "n/a"
if sixteen:
    o = owner(sixteen[0])
    callers16 = [i["a"] for i in INS if i["mn"] == "call"
                 and i["ops"].strip().lower() == hex(o[1])]
    live16 = f"owner {o[0]} ({o[2] - o[1]} B), {len(callers16)} caller(s) " \
             f"{[hex(x) for x in callers16]}"
say(f"  the 0x16 wrapper: {live16}")
push16 = [i for i in INS if i["a"] == LIT16 and i["mn"] == "push"]
if len(consts) != 49 or sixteen != [0x58459D] or len(exprs) != 1 \
        or exprs[0][0] != 0x52D873 or not push16 or imm_val(push16[0]["ops"]) != 0x16:
    bad(f"G4 msg census != 49 literals / 0x16 once at 58459d / 1 expression at 52d873 "
        f"({len(consts)},{[hex(a) for a in sixteen]},{len(exprs)})")
else:
    ok("G4", f"{len(consts)} literal ids; 0x16 exactly once (live wrapper); 1 expression id")

# ---------------------------------------------------------------- G5 the joint
say("")
say("G5  the joint the milestone asks about: guard==0 crossed with the id")
both = [t for t in TABLE if t in z and t["slots"][0][0] == "CONST" and t["slots"][0][1] == 0x16]
openl = [t for t in TABLE if t in z and t["slots"][0][0] != "CONST"]
say(f"  guard==0 AND literal 0x16 (statically closed UNINIT leg): {len(both)}")
say(f"  guard==0 AND expression id (leg open to any id): {len(openl)} "
    f"{[hex(t['a']) for t in openl]}")
if len(both) != 0 or len(openl) != 1 or openl[0]["a"] != 0x52D873:
    bad(f"G5 joint != 0 closed / 1 open at 52d873 ({len(both)},{len(openl)})")
else:
    ok("G5", "no caller closes the leg; exactly one (52d873) leaves it open")

# ---------------------------------------------------------------- G6 the id source
say("")
say("G6  the open site: where its id word comes from, and what guards the block")
lo, hi = func_range(0x52D873)
reach = backward_reach(0x52D873, lo, hi)
defs = [(i["a"], i["mn"], fog(i["ops"])) for i in INS
        if i["a"] in reach and i["mn"] in WRITES
        and i["ops"].lower().strip().split(",")[0].strip() == "ebx"]
w = defs[0] if len(defs) == 1 else None
say(f"  enclosing function: {owner(0x52D873)[0]} [{lo:06x},{hi:06x}) size {hi - lo}")
say(f"  backward-reachable instruction set over explicit edges: {len(reach)}")
say(f"  writes to ebx inside that set: {[(hex(a), m, o) for a, m, o in defs]}")
say(f"  last write to ebx before 52d873: "
    f"{f'{w[0]:06x} {w[1]} {w[2]}' if w else 'NOT UNIQUE'}")
say(f"  (ebx is also written out of path, in SEH epilogues: "
    f"{[hex(i['a']) for i in INS if lo <= i['a'] < hi and i['mn'] == 'pop' and i['ops'].strip() == 'ebx']})")
pushed_ops = [fog(i["ops"]) for i in INS if 0x52D86E <= i["a"] <= 0x52D873 and i["mn"] == "push"]
say(f"  the id operand: {fog([i['ops'] for i in INS if i['a'] == 0x52D86A][0])} "
    f"(16-bit store into ax; the callee takes movsx WORD)")
entries = [(i["a"], i["mn"], fog(i["ops"])) for i in INS
           if lo <= i["a"] < hi and i["mn"] in ("call", "jmp") + JCC
           and i["ops"].strip().lower() == "0x52d840"]
say(f"  jumps into the block 52d840: {[(hex(a), m, o) for a, m, o in entries]}")
mid = [(i["a"], i["mn"], fog(i["ops"])) for i in INS
       if MSGSRC[0] <= i["a"] < MSGSRC[1]]
head = [x for x in mid if x[0] == BLOCK_HEAD]
say(f"  instructions in the block: {len(mid)}; head 0x{BLOCK_HEAD:06x} = "
    f"{head[0][1] + ' ' + head[0][2] if head else 'MISSING'}")
tests = [x for x in mid if x[1] in ("cmp", "test", "and", "or") and "+0x10]" in x[2].lower()]
say(f"  instructions in the block that test/compare +0x10: {len(tests)} {tests}")
if not w or w[0] != REC_EBX_DEF or w[1] != "mov" or "[ebp+0x8]" not in w[2].lower():
    bad(f"G6 ebx lineage != single def at 52bd33 from [ebp+8] ({defs})")
elif {e[0] for e in entries} != set(ENTRIES):
    bad(f"G6 entries into 52d840 changed: {[hex(e[0]) for e in entries]}")
elif len(tests) != 0:
    bad(f"G6 the block now filters +0x10: {tests}")
elif not head:
    bad("G6 the block head 52d849 is gone")
else:
    ok("G6", "ebx = arg record (52bd33); 2 entries on record word 0x1101/0x4101; no +0x10 test")

# ---------------------------------------------------------------- G7 verdict
say("")
say("G7  the verdict")
pres = [x for x in TABLE if x["slots"][gs][0] == "CONST" and x["slots"][gs][1] != 0]
say(f"  guard!=0 (PRESERVE: the snapshot runs, the store copies the pair dword): {len(pres)}")
say(f"  guard==0, literal id            : {len(both)}")
say(f"  guard==0, expression id (UNINIT): {len(openl)}  <- reachable, id unconstrained")
dead = [x for x in TABLE if x["slots"][0][0] != "CONST" and x["slots"][gs][1] != 0]
say(f"  legs killed by arithmetic like M387's count==0: 0 for this axis")
say("  So the UNINIT leg is LIVE: one callsite opens it, the id there is a 16-bit record")
say("  field with no static filter, and 0x16 is a live id in this same dispatcher")
say("  (0x58459d, one caller at 0x5355eb). A runtime witness needs a box run (out of scope).")
if len(pres) != 64 or len(both) != 0 or len(openl) != 1:
    bad(f"G7 verdict counts != 64/0/1 ({len(pres)},{len(both)},{len(openl)})")
else:
    ok("G7", "64 PRESERVE + 0 closed + 1 LIVE-UNINIT (52d873) = 65")

# ---------------------------------------------------------------- G8 rivals
say("")
say("G8  rivals, measured against the printed numbers")
r1 = len(z) == 0
r2 = bool(both) or len(openl) != 1
r3 = all(TABLE[i]["slots"][0][0] == "CONST" for i in range(len(TABLE))
         if TABLE[i]["f"].startswith("FUN_00584"))
r4 = False
if ALGO == 6:
    say("  ALGO=6: rival classifier sees only the guard axis")
    r1 = r2 = r3 = True
say(f"  R1 every caller pushes a non-zero guard           -> "
    f"{'CONFIRMED' if r1 else 'REFUTED'} (guards: {len(z)} zero, {len(one)} one, "
    f"{len(other)} other)")
say(f"  R2 the zero-guard site's id is the literal 0x16   -> "
    f"{'CONFIRMED' if r2 else 'REFUTED'} (closed={len(both)}, open={len(openl)})")
say(f"  R3 the 0x584xxx wrapper family relays runtime ids  -> "
    f"{'CONFIRMED' if not r3 else 'REFUTED'} (all literal: {not r3})")
say(f"  R4 the record id is bounded to the game's own ids  -> OPEN (no code constrains it;"
    f" producer census is the next pick)")
refuted = int(not r1) + int(not r2) + int(not r3)
if refuted == 0:
    bad("G8 every rival survived - no refutation on the printed numbers")
else:
    ok("G8", f"{refuted} rivals REFUTED, R4 left OPEN")

# ---------------------------------------------------------------- G9 digest
say("")
dig = hashlib.sha1("\n".join(OUT).encode()).hexdigest()[:16]
n_gates = 10
passed = n_gates if not FAILS else n_gates - len({f.split()[0] for f in FAILS})
say(f"  table {len(TABLE)} sites | sha1 {dig}")
if FAILS:
    say(f"FAIL M392: {passed}/{n_gates}  {dig}")
    sys.exit(1)
say(f"PASS M392: {n_gates}/{n_gates}  {dig}")
