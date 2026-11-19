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

def push_args(call_addr, limit=24):
    """The 4 cdecl pushes before a wrapper call, innermost first: [dest,size,count,FILE*].
    LINEAR backward walk within the owner; non-immediate pushes -> None slot."""
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
        elif mn in ("call",) or mn.startswith("j"):
            break  # a preceding call/branch ends the straight-line push run
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

# ---- T5: g999fa4 census + feed pin (filled after window probe) ------------------
# ---- T6: loader call closure vs round writers (filled after probe) -------------
# ---- gates + rivals + digest: filled in below ----------------------------------

def main():
    print("M324 SAVE-CARRY - static census (codec FUN_00596850, opener FUN_00597ee0)")
    print("T1 codec legs (site dir dest size count):")
    for a, d, dest, size, cnt, fp in LEGS:
        print("  %#x %s dest=%s size=%s cnt=%s" % (
            a, d,
            "%#x" % dest if dest is not None else "reg/heap",
            "%#x" % size if size is not None else "?",
            "%#x" % cnt if cnt is not None else "?"))
    print("T2 coverage:", {k: ["%#x" % x for x in v] for k, v in COV.items()})
    print("T3 file:", FILE_FACTS)
    print("== M324: skeleton (gates pending) ==")

if __name__ == "__main__":
    main()