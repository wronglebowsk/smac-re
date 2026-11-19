#!/usr/bin/env python3
# M324: the SAVE-CARRY question (M323's biggest OPEN). Does the .SAV loader re-derive
# ROUND (ds:0x985afc) from YEAR via FUN_004e0350, or carry it raw? STATIC, zero box.
# Footing: NAMED ## M323 (4-writer map, no loader writer), ## M272 (load window:
# opener FUN_00597ee0 round=-39 -> faction fread round=50), ## M242 (FUN_00596850 =
# ONE codec for both directions; header leg dst=0x985ab8 sz=0x31c), ## M106 (read()
# lands STRAIGHT INTO THE REGION: kernel copy_to_user, no ring-3 store -> a census of
# instruction writers CANNOT see a load restore), ## M107/M108 (block A 0x105e0 leg,
# counts 67/18, live version 9), decode_save.py (mission year u16 @file 0x54).
# Law: table FIRST then ASSERT; >=1 RIVAL that FAILS on the printed numbers; digest
# hashes the MEASURED detail; declared sets MEASURED not authored.
# Mutants: M324_PATCH addr|mn ops (disassembly rewrite), M324_ALGO 1=push-order swap
# 2=direction swap, M324_SAVE=<file> (data mutant), M324_EVIDENCE_ROOT=<dir>.
# Resolver limit (DECLARED): push-arg walk is a LINEAR backward scan within the owning
# function (<=24 instrs), not a CFG dataflow proof; legs whose dest/size are not push
# immediates are reported as reg/heap and EXCLUDED from static coverage (counted).
import bisect, csv, hashlib, os, re, struct, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
IDX = os.path.join(ROOT, "ghidra_out/index.csv")
EV = os.environ.get("M324_EVIDENCE_ROOT", ROOT)
ALGO = os.environ.get("M324_ALGO", "0")
SAVE = os.environ.get("M324_SAVE", os.path.join(ROOT, "programs/saves/m54b_clean.SAV"))

CODEC = 0x596850          # FUN_00596850, the bidirectional codec (M242)
OPENER = 0x597ee0         # FUN_00597ee0, the .SAV opener (M272)
RD, WR = 0x64cc00, 0x64c9a0   # fread / fwrite wrappers (M242/M109)
ROUND, YEAR, G999 = 0x985afc, 0x985b00, 0x999fa4
HDRBASE = 0x985ab8        # header blob base (M242 header leg)
BLKBASE, STRIDE, NBLK = 0x94d430, 0x20bc, 8   # M320/M316 faction blocks
FAC1436 = 0x927590        # 8x1436 save-side faction array (M272)
RWRITERS = {0x5a0fa0, 0x51f320, 0x4e0350, 0x59ce10}  # M323's 4 round-writer fns

def load_ins():
    ins = {}
    lin = re.compile(r"^\s*([0-9a-f]{6,8}):\s[0-9a-f ]+\t(\w+)\s*(.*)$")
    for ln in open(TEXT):
        m = lin.match(ln)
        if m:
            ins[int(m.group(1), 16)] = (m.group(2), m.group(3).strip())
    p = os.environ.get("M324_PATCH")
    n = 0
    if p:
        for chunk in p.split(";"):
            chunk = chunk.strip()
            if not chunk: continue
            addr, rest = chunk.split("|", 1)
            mn, _, ops = rest.partition(" ")
            a = int(addr, 16)
            if a not in ins:
                raise SystemExit("M324_PATCH address not in .text cache: %s" % addr)
            if ins[a] == (mn, ops.strip()):
                raise SystemExit("M324_PATCH applied to nothing (already equal)")
            ins[a] = (mn, ops.strip()); n += 1
        if n == 0: raise SystemExit("M324_PATCH applied to nothing")
    return ins

INS = load_ins()
ADDRS = sorted(INS)
funcs = []
with open(IDX) as f:
    for r in csv.DictReader(f):
        funcs.append((int(r["addr"], 16), r["name"], int(r["size_bytes"] or 0)))
funcs.sort()
FSTARTS = [a for a, _, _ in funcs]
FNAME = {a: n for a, n, _ in funcs}
FSIZE = {a: s for a, _, s in funcs}

def owner(a):
    i = bisect.bisect_right(FSTARTS, a) - 1
    if i >= 0 and a < funcs[i][0] + max(funcs[i][2], 1):
        return funcs[i][1]
    return "?"

def faddr(name):
    for a, n, _ in funcs:
        if n == name: return a
    return None

def push_args(call_addr, limit=32):
    """The 4 cdecl pushes of the leg's push-run, innermost first: [dest,size,count,FILE*].
    The codec leg is a diamond: pushes; je READ; call WR; jmp NEXT; READ: call RD.
    A backward walk from either call must skip the diamond glue (jcc/jmp/twin-wrapper
    call) and the interleaved mov/cmp stores; it stops at the previous leg's stack
    cleanup (add esp), a NON-twin call, or the function edge. LINEAR, not CFG proof."""
    o = owner(call_addr)
    i = ADDRS.index(call_addr)
    args, seen = [], 0
    while i > 0 and seen < limit and len(args) < 4:
        i -= 1
        b = ADDRS[i]
        if owner(b) != o: break
        mn, ops = INS[b]
        if mn == "push":
            m = re.fullmatch(r"0x([0-9a-f]+)", ops.strip())
            args.append(int(m.group(1), 16) if m else None)
            seen += 1
        elif mn == "call":
            m = re.fullmatch(r"0x([0-9a-f]+)", ops.strip())
            t = int(m.group(1), 16) if m else -1
            if t not in (RD, WR, 0x596470, 0x596540): break  # foreign call ends the run
            seen += 1
        elif mn == "add" and ops.startswith("esp,"):
            break  # previous leg's cdecl cleanup
        elif mn in ("lea", "ret", "leave"):
            break
        # mov/cmp/and/test/jcc/jmp = diamond glue or interleaved stores: skip
    if ALGO == "1" and len(args) == 4:
        args = args[::-1]  # mutant: reversed push order
    while len(args) < 4: args.append(None)
    return args  # [dest, size, count, file]

def legs_in(lo, hi):
    """Every wrapper call site in [lo,hi) with its push args + direction."""
    out = []
    for a in ADDRS:
        if a < lo: continue
        if a >= hi: break
        mn, ops = INS[a]
        if mn != "call": continue
        m = re.fullmatch(r"0x([0-9a-f]+)", ops.strip())
        if not m: continue
        t = int(m.group(1), 16)
        if t not in (RD, WR): continue
        d = "R" if t == RD else "W"
        if ALGO == "2": d = "W" if d == "R" else "R"
        dest, size, cnt, fp = push_args(a)
        out.append((a, d, dest, size, cnt, fp))
    return out

CODEC_END = CODEC + max(FSIZE.get(CODEC, 0), 1)
LEGS = legs_in(CODEC, CODEC_END)

# ---- T1/T2/T3: coverage of the target globals by static-direct legs ------------
def covers(leg, addr, width=4):
    a, d, dest, size, cnt, fp = leg
    if d != "R" or dest is None or size is None: return False
    n = cnt if cnt is not None else 1
    return dest <= addr and addr + width <= dest + size * n

TARGETS = [("ROUND", ROUND), ("YEAR", YEAR), ("G999", G999)]
TARGETS += [("BLK%d+220" % k, BLKBASE + k * STRIDE + 0x220) for k in range(NBLK)]
COV = {name: [l[0] for l in LEGS if covers(l, addr)] for name, addr in TARGETS}
FAC_COV = [l[0] for l in LEGS if covers(l, FAC1436, 8 * 1436)]

# ---- T4: file-byte cross-check (12-byte prefix model, MEASURED) -----------------
SB = open(SAVE, "rb").read()
PREFIX = 12  # magic 7 + marker 1 + version 4; pinned below, not assumed
def u32(off): return struct.unpack_from("<I", SB, off)[0]
FILE_FACTS = {
    "size": len(SB), "magic": SB[:7], "marker": SB[7], "version": u32(8),
    "round@50": u32(0x50), "year@54": u32(0x54),
    "units@44": u32(0x44), "bases@48": u32(0x48), "verfield@310": u32(0x310),
}

# ---- T4b: sibling (converting) legs inside the codec ---------------------------
SIBS = []
for a in ADDRS:
    if a < CODEC: continue
    if a >= CODEC_END: break
    mn, ops = INS[a]
    if mn != "call": continue
    m = re.fullmatch(r"0x([0-9a-f]+)", ops.strip())
    if m and int(m.group(1), 16) in (0x596470, 0x596540):
        SIBS.append((a, int(m.group(1), 16)) + tuple(push_args(a)))

# ---- T4c: image-wide immediate-dest READ legs covering ROUND (exclusivity) -----
IMG_ROUND = []
for a in ADDRS:
    mn, ops = INS[a]
    if mn != "call" or ops.strip() != "0x64cc00": continue
    dest, size, cnt, fp = push_args(a)
    if dest is None or size is None: continue
    n = cnt if cnt is not None else 1
    if dest <= ROUND and ROUND + 4 <= dest + size * n:
        IMG_ROUND.append(a)

# ---- T5: g999fa4 census + feed fold pins ----------------------------------------
G999RE = re.compile(r"ds:0x999fa4(?![0-9a-f])")
G999_HITS = [(a, INS[a][0], INS[a][1]) for a in ADDRS if G999RE.search(INS[a][1])]
G999_W = [a for a, mn, ops in G999_HITS
          if mn == "mov" and G999RE.search(ops.split(",")[0])]
FEEDFN = 0x442320
FEED_CALLERS = [a for a in ADDRS if INS[a][0] == "call"
                and INS[a][1].strip() == "0x442320"]
FEED_AT = [a for a in ADDRS if INS[a][0] != "call"
           and re.search(r"(?<![0-9a-f])0x442320(?![0-9a-f])", INS[a][1])]
# the fold: [ebp-0x10] -> +0xa24 -> *0x20bc -> [ecx+0x94d650] -> g999fa4, MAX-gated
FOLD = {
    0x442619: ("imul", "ecx,ecx,0x20bc"),
    0x44261f: ("mov", "edx,DWORD PTR ds:0x999fa4"),
    0x442625: ("cmp", "edx,DWORD PTR [ecx+0x94d650]"),
    0x44262b: ("jle", "0x442648"),
    0x442630: ("mov", "ecx,DWORD PTR [eax+0xa24]"),
    0x442636: ("imul", "ecx,ecx,0x20bc"),
    0x44263c: ("mov", "edx,DWORD PTR [ecx+0x94d650]"),
    0x442642: ("mov", "DWORD PTR ds:0x999fa4,edx"),
}
W2 = {  # second writer: g999fa4 = thunk(0x99a01c)
    0x626fca: ("push", "0x99a01c"),
    0x626fcf: ("call", "0x64c460"),
    0x626fd7: ("mov", "ds:0x999fa4,eax"),
    0x64c467: ("call", "0x64c360"),
}

# ---- T6: loader call closure (direct imm32 calls only; DECLARED limit) ----------
def call_targets(a):
    mn, ops = INS[a]
    if mn != "call": return None
    m = re.fullmatch(r"0x([0-9a-f]+)", ops.strip())
    if not m: return None
    t = int(m.group(1), 16)
    o = owner(t)
    return faddr(o) if o != "?" else None

GRAPH = {}
for a in ADDRS:
    t = call_targets(a)
    if t is not None:
        GRAPH.setdefault(faddr(owner(a)), set()).add(t)
SEEDS = {CODEC} if ALGO == "3" else {OPENER, CODEC}
CLOSURE = set()
stack = list(SEEDS)
while stack:
    f = stack.pop()
    if f is None or f in CLOSURE: continue
    CLOSURE.add(f)
    stack.extend(GRAPH.get(f, ()))
WR_IN_CLOSURE = sorted(CLOSURE & RWRITERS)
YR_CALLERS = sorted(a for a in ADDRS if INS[a][0] == "call"
                    and INS[a][1].strip() == "0x4e0350")

# ---- T7: ordering + mode pins ----------------------------------------------------
FIRST_WRAP = min(l[0] for l in LEGS)
OPINS = {
    0x597efb: ("xor", "ebx,ebx"),
    0x597f05: ("jne", "0x597f12"),
    0x597f49: ("push", "0x4"),
    0x597f53: ("call", "0x64cc00"),
    0x597f63: ("cmp", "DWORD PTR [ebp-0x10],0x56"),
    0x597fad: ("call", "0x596850"),
}
CPINS = {
    0x596881: ("je", "0x59688a"),
    0x59689a: ("cmp", "DWORD PTR ds:0x985dbc,0x4"),
}
# no ebx definition on the path body [0x597f12, 0x597f98) -> mode stays 0
EBX_DEFS_BODY = [a for a in ADDRS if 0x597f12 <= a < 0x597f98
                 and INS[a][1].split(",")[0].strip() in ("ebx", "bx", "bl")
                 and INS[a][0] not in ("cmp", "test", "push")]

def parse_m272():
    ev = {}
    pat = re.compile(r"pc=0x([0-9a-f]+) ret=0x([0-9a-f]+) round=(-?\d+) cp=(\d+)")
    for ln in open(os.path.join(EV, "evidence/m272w9.gdblog")):
        m = pat.search(ln)
        if m:
            ev.setdefault(int(m.group(1), 16), []).append(
                (int(m.group(2), 16), int(m.group(3)), int(m.group(4))))
    return ev
M272 = parse_m272()
M272_OPENER = M272.get(OPENER, [])
M272_FAC = [e for e in M272.get(RD, []) if e[0] == 0x596edb]
M272_WFAM = [pc for pc in M272 if pc in
             (0x57ecf0, 0x5a0fa0, 0x59ce10, 0x51f320, 0x4e0350, 0x5b2970)]

def parse_m302():
    p = os.path.join(EV, "evidence/m302_livepins.txt")
    txt = open(p).read()
    sha = re.search(r"sha256 ([0-9a-f]{16})", txt)
    sz = re.search(r"\((\d+) B, sha256", txt)
    yr = re.search(r"year (\d+) \(0x[0-9a-f]+\)\s+round (\d+)", txt)
    return (sha.group(1) if sha else None, int(sz.group(1)) if sz else None,
            (int(yr.group(1)), int(yr.group(2))) if yr else None)
M302_SHA, M302_SIZE, M302_YR = parse_m302()
SB_SHA = hashlib.sha256(SB).hexdigest()[:16]

# ---- gates ---------------------------------------------------------------------
def leg(site):
    for l in LEGS:
        if l[0] == site: return l
    return None

def pin_ok(pins):
    return all(INS.get(a) == v for a, v in pins.items())

GATES = []
def gate(name, ok, detail):
    GATES.append((name, bool(ok), detail))

# G1: codec leg census - the three carry legs + blockA converting siblings
# PUSH_PINS: the push-run POSITIONS are pinned too, not just the resolved values
# (a value-only check would accept the same immediates pushed from anywhere).
PUSH_PINS = {
    0x596866: ("push", "0x31c"),
    0x59687c: ("push", "0x985ab8"),
    0x596a7e: ("push", "0x105e0"),
    0x596a83: ("push", "0x94d430"),
    0x596ec3: ("push", "0x2ce0"),
    0x596ec8: ("push", "0x927590"),
}
hl, ha, hf = leg(0x59688a), leg(0x596a91), leg(0x596ed6)
sibA = [s for s in SIBS if s[0] in (0x596a6b, 0x596a72)]
g1 = (hl == (0x59688a, "R", HDRBASE, 0x31c, 1, None)
      and leg(0x596883) == (0x596883, "W", HDRBASE, 0x31c, 1, None)
      and ha == (0x596a91, "R", BLKBASE, 0x105e0, 1, None)
      and leg(0x596a8a) == (0x596a8a, "W", BLKBASE, 0x105e0, 1, None)
      and hf == (0x596ed6, "R", FAC1436, 0x2ce0, 1, None)
      and leg(0x596ecf) == (0x596ecf, "W", FAC1436, 0x2ce0, 1, None)
      and len(sibA) == 2
      and all(s[2] == BLKBASE and s[3] == 0x105e0 for s in sibA)
      and {s[1] for s in sibA} == {0x596470, 0x596540}
      and pin_ok(PUSH_PINS))
gate("G1", g1, "header R/W=59688a/596883 dst=985ab8 sz=31c; blockA R/W=596a91/596a8a "
     "dst=94d430 sz=105e0 +siblings 596a6b/596a72 same args; faction R/W=596ed6/596ecf "
     "dst=927590 sz=2ce0; pushpins=%s; legs R=%d W=%d sib=%d" % (
         pin_ok(PUSH_PINS),
         sum(1 for l in LEGS if l[1] == "R"), sum(1 for l in LEGS if l[1] == "W"), len(SIBS)))
# G2: ROUND+YEAR carried by the header leg, and by NO OTHER immediate-dest read leg
g2 = (COV["ROUND"] == [0x59688a] and COV["YEAR"] == [0x59688a]
      and IMG_ROUND == [0x59688a]
      and ROUND - HDRBASE == 0x44 and YEAR - HDRBASE == 0x48)
gate("G2", g2, "COV ROUND=%s YEAR=%s img-wide=%s blob+44/+48" % (
    ["%#x" % x for x in COV["ROUND"]], ["%#x" % x for x in COV["YEAR"]],
    ["%#x" % x for x in IMG_ROUND]))
# G3: all 8 block+0x220 fields + the 1436-array carried; size algebra
g3 = (all(COV["BLK%d+220" % k] == [0x596a91] for k in range(NBLK))
      and FAC_COV == [0x596ed6] and 0x105e0 == NBLK * STRIDE and 0x2ce0 == 8 * 1436)
gate("G3", g3, "8/8 block+220 legs=%s fac1436=%s 105e0=8*20bc 2ce0=8*1436" % (
    sorted({tuple(COV["BLK%d+220" % k]) for k in range(NBLK)}),
    ["%#x" % x for x in FAC_COV]))
# G4: g999fa4 writer set + feed fold + NOT carried by any static leg
g4 = (sorted(G999_W) == [0x442642, 0x626fd7] and len(G999_HITS) == 11
      and pin_ok(FOLD) and pin_ok(W2) and 0x94d650 - BLKBASE == 0x220
      and COV["G999"] == [] and FEED_CALLERS == [] and FEED_AT == [])
gate("G4", g4, "writers=%s refs=%d fold8pins=%s w2pins=%s 94d650-94d430=220 "
     "COV=[] feedcallers=%d feedAT=%d" % (
         ["%#x" % x for x in sorted(G999_W)], len(G999_HITS), pin_ok(FOLD),
         pin_ok(W2), len(FEED_CALLERS), len(FEED_AT)))
# G5: file bytes == the live pins of the SAME save (sha-identified)
g5 = (FILE_FACTS["magic"] == b"TERRAN\x00" and FILE_FACTS["marker"] == 0x1a
      and FILE_FACTS["version"] == 86 and FILE_FACTS["size"] == 242539
      and SB_SHA == M302_SHA == "74d0f44ab9b9290b" and M302_SIZE == 242539
      and FILE_FACTS["round@50"] == 50 and FILE_FACTS["year@54"] == 2150
      and M302_YR == (2150, 50)
      and FILE_FACTS["units@44"] == 67 and FILE_FACTS["bases@48"] == 18
      and FILE_FACTS["verfield@310"] == 9
      and PREFIX + 0x44 == 0x50 and PREFIX + 0x48 == 0x54 and PREFIX + 0x304 == 0x310)
gate("G5", g5, "sha=%s size=%d round@50=%d year@54=%d units@44=%d bases@48=%d "
     "ver@310=%d m302=(%s,%s,%s)" % (SB_SHA, FILE_FACTS["size"],
         FILE_FACTS["round@50"], FILE_FACTS["year@54"], FILE_FACTS["units@44"],
         FILE_FACTS["bases@48"], FILE_FACTS["verfield@310"], M302_SHA, M302_SIZE, M302_YR))
# G6: loader closure contains NO round writer; year-sync callers = the 2 tour pumps
g6 = (WR_IN_CLOSURE == [] and YR_CALLERS == [0x514ecf, 0x517e3a]
      and FEEDFN not in CLOSURE and CODEC in CLOSURE and OPENER in CLOSURE
      and 0x512b40 not in CLOSURE and 0x516b80 not in CLOSURE)
gate("G6", g6, "closure=%d fns writers-in=%s 4e0350callers=%s feed/pumps absent" % (
    len(CLOSURE), ["%#x" % x for x in WR_IN_CLOSURE], ["%#x" % x for x in YR_CALLERS]))
# G7: header leg FIRST, mode=0 pinned, version read by opener, M272 live order
g7 = (FIRST_WRAP == 0x596883 and pin_ok(OPINS) and pin_ok(CPINS)
      and EBX_DEFS_BODY == []
      and M272_OPENER == [(0x5992f2, -39, 0)] and M272_FAC == [(0x596edb, 50, 3)]
      and M272_WFAM == [])
gate("G7", g7, "firstwrap=%#x mode:xor@597efb+jne@597f05+noebxdef=%s verleg@597f53 "
     "m272 opener=%s fac=%s writerfam=%s" % (
         FIRST_WRAP, EBX_DEFS_BODY == [], M272_OPENER, M272_FAC, M272_WFAM))
# G8: the RIVALS die on the printed numbers
r1_dead = (WR_IN_CLOSURE == [] and FILE_FACTS["round@50"] == 50
           and FIRST_WRAP == 0x596883 and COV["ROUND"] == [0x59688a])
r2_dead = (0x5a0fa0 not in CLOSURE
           and INS.get(0x5a108b) == ("mov", "DWORD PTR ds:0x985afc,esi")
           and M272_WFAM == [] and FILE_FACTS["round@50"] == 50)
gate("G8", r1_dead and r2_dead, "R1 RE-DERIVE dead=%s R2 REBUILD dead=%s" % (r1_dead, r2_dead))

def main():
    print("M324 SAVE-CARRY - static census (codec FUN_00596850, opener FUN_00597ee0)")
    print("T1 codec legs (site dir dest size count):")
    for a, d, dest, size, cnt, fp in LEGS:
        print("  %#x %s dest=%s size=%s cnt=%s" % (
            a, d, "%#x" % dest if dest is not None else "reg/heap",
            "%#x" % size if size is not None else "?",
            "%#x" % cnt if cnt is not None else "?"))
    print("T1b converting siblings: %s" % [
        ("%#x" % s[0], "%#x" % s[1], "%#x" % s[2] if s[2] is not None else "reg",
         "%#x" % s[3] if s[3] is not None else "?") for s in SIBS])
    print("T2 coverage:", {k: ["%#x" % x for x in v] for k, v in COV.items()})
    print("T2b img-wide immediate-dest read legs covering ROUND:",
          ["%#x" % x for x in IMG_ROUND])
    print("T3 file:", {k: (v.hex() if isinstance(v, bytes) else v)
                       for k, v in FILE_FACTS.items()}, "sha16=%s" % SB_SHA)
    print("T4 g999fa4 refs=%d writers=%s feedcallers=%s feedAT=%s" % (
        len(G999_HITS), ["%#x" % x for x in sorted(G999_W)],
        ["%#x" % x for x in FEED_CALLERS], ["%#x" % x for x in FEED_AT]))
    for a, mn, ops in G999_HITS:
        print("  %#x %s %s" % (a, mn, ops))
    print("T5 closure: %d fns from seeds %s; writers-in=%s; 4e0350 callers=%s" % (
        len(CLOSURE), sorted("%#x" % s for s in SEEDS),
        ["%#x" % x for x in WR_IN_CLOSURE], ["%#x" % x for x in YR_CALLERS]))
    print("T6 order: firstwrap=%#x ebxdefs-body=%s m272 opener=%s fac=%s wfam=%s" % (
        FIRST_WRAP, ["%#x" % x for x in EBX_DEFS_BODY], M272_OPENER, M272_FAC, M272_WFAM))
    print("T7 m302 cross: sha=%s size=%s yearround=%s" % (M302_SHA, M302_SIZE, M302_YR))
    for name, ok, detail in GATES:
        print("%s %s %s" % (name, "PASS" if ok else "FAIL", detail))
    print("R1 RE-DERIVE-FROM-YEAR (load calls FUN_004e0350): %s - 4e0350 callers are "
          "the 2 tour pumps, closure writers=%s, file round@0x50=%d, header leg first" % (
              "DEAD" if r1_dead else "ALIVE", WR_IN_CLOSURE, FILE_FACTS["round@50"]))
    print("R2 NEW-GAME-REBUILD (load calls FUN_005a0fa0/59ce10): %s - 5a0fa0 not in "
          "closure, its store is const-0 via esi (M323), m272 writer-family events=%d" % (
              "DEAD" if r2_dead else "ALIVE", len(M272_WFAM)))
    npass = sum(1 for _, ok, _ in GATES if ok)
    detail = "\n".join("%s %s %s" % (n, o, d) for n, o, d in GATES)
    detail += "\nlegs=%s\ncov=%s\nimg=%s\nfile=%s\nsha=%s\ng999w=%s\nclosure=%d\nm272=%s" % (
        LEGS, COV, IMG_ROUND, FILE_FACTS, SB_SHA, sorted(G999_W), len(CLOSURE), M272)
    dig = hashlib.sha256(detail.encode()).hexdigest()[:16]
    print("== M324: %d/%d == digest %s" % (npass, len(GATES), dig))
    return 0 if npass == len(GATES) else 1

if __name__ == "__main__":
    sys.exit(main())