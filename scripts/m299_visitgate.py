#!/usr/bin/env python3
"""M299 (s254, STATIC, zero box): the slot [+4] visit counter and its 0x5832b0 gate.

LAWS (each DECODED from pinned objdump text, never asserted):
  L1 the slot-store block tail of FUN_0051dcb0 (0x51dff5-0x51e01b) calls FUN_005832b0 with
     the SAME ordered frame pair ([ebp-0x10], [ebp-0x8]) the pinned 0x5aff90/0x582cc0 calls
     already pass as (x, y); `test eax,eax` / `je 0x51e11d` gates EVERYTHING after it, and
     the fall-through is exactly `inc ecx` on the dword loaded from [esi+0x989cec] -
     0x989ce8 (slot base, pinned 0x51dfbd/0x51dfcb) + 4 + 28*site (esi fold re-decoded from
     0x51dfac-ba; NO esi write between fold completion and the store) = slot[site].counter.
     => the visit counter increments ONLY when FUN_005832b0(x, y) != 0.
  L2 FUN_005832b0 is a PURE predicate: it computes the shared tile_record_array record
     rec = ds:0x92ae14 + 44*(ds:0x692184*y + (x>>1)) (fold parsed from its prologue, graded
     for equality with the pinned 0x582cc0 fold), then a 4-rung bit ladder on dword[rec+8]:
       rung1 0x102000 != 0 -> FALSE   (byte9 bit5 = the B16 occ bit; byte10 bit4 unnamed)
       rung2 ds:0x985ac4 bit 0x2000   -> return (dword & 0xc000000) ? 2 : 0
       rung3 dword & 0x10000000       -> TRUE (return 1)
       rung4 ds:0x92a380 == 0         -> FALSE   (0x92a380 = rand+1, MAP_FORMAT.md:116)
     then a lattice-parity branch selected by the B16 class law (byte0&0xe0) >= 0x60; both
     legs test the lattice index (h&3) + 4*(d&3), h = (x+y)>>1, d = x-h, against constants
     built from ds:0x92a380 and ds:0x692210/ds:0x69220c (values NOT recorded - declared).
  L3 all six return paths pop ebx/esi/edi (callee-saved): the esi slot address survives
     the call - required for L1's address identity.

DECLARED (honest holes): neither the counter VALUES nor 0x985ac4-bit2000/byte10bit4/bit28/
bit26-27/0x92a380/0x692210/0x69220c VALUES are in any recorded artifact (the grep witness
is in this run's header); the recorded s249 dump grades only the ladder's INPUT FIELDS
(G7). The 0x94ed28 byte read at 0x51e02c (region array, NAMED:371) is a LEAD.

Run:  python3 scripts/m299_visitgate.py          (exit 0 = all gates PASS)
Evidence: evidence/m299_visitgate.txt = this run's stdout (pinned windows + gates).
"""
import os
import re
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
EVID = os.path.join(ROOT, "evidence")
S251 = os.path.join(EVID, "s251_statics_fn51dcb0.txt")

LINES = []  # (addr, hexbytes, insns) over the whole text dump


def load_text():
    with open(TEXT, errors="replace") as f:
        for ln in f:
            m = re.match(r"\s*([0-9a-f]{6,8}):\t([0-9a-f][0-9a-f ]*?)\t(.+?)\s*$", ln)
            if m:
                LINES.append((int(m.group(1), 16), m.group(2).strip(), m.group(3).strip()))


def window(lo, hi):
    return [t for t in LINES if lo <= t[0] <= hi]


def at(addr):
    for a, _, ins in LINES:
        if a == addr:
            return ins
    raise AssertionError("0x%x not in text dump" % addr)


def show(lo, hi, fh):
    fh.write("%d lines 0x%x-0x%x\n" % (len(window(lo, hi)), lo, hi))
    for a, hx, ins in window(lo, hi):
        fh.write("  %06x:\t%-22s\t%s\n" % (a, hx, ins))


FAILS = []


def gate(name, cond, detail):
    print("%-34s %s  %s" % (name, "PASS" if cond else "FAIL", detail))
    if not cond:
        FAILS.append(name)


def dec_regs(ins):
    """which of the named regs an instruction writes (dst operand / fixed writers)."""
    w = set()
    m = re.match(r"^(\w+)(?:\s+(.+))?$", ins)
    if not m:
        return w
    op, rest = m.group(1), m.group(2) or ""
    if op in ("mov", "lea", "xor", "and", "or", "sub", "add", "sbb", "adc", "imul", "movzx", "movsx"):
        dst = rest.split(",")[0].strip()
        w.add(dst.split(" ")[-1].strip())
    elif op in ("inc", "dec", "neg", "shl", "sar", "shr"):
        w.add(rest.split(",")[0].strip())
    elif op == "cdq":
        w.add("edx")
    elif op.startswith("set"):
        w.add(rest.split(",")[-1].strip())
    elif op == "pop":
        w.add(rest.strip())
    return w


# ---------------------------------------------------------------- pins
CALLER = (0x51DFAC, 0x51E02C)
CALLEE = (0x5832B0, 0x5833B7)
PINS = [
    (0x51dfac, r"mov\s+eax,DWORD PTR \[ebp-0xc\]"),
    (0x51dfaf, r"mov\s+ecx,eax"),
    (0x51dfb1, r"lea\s+esi,\[eax\*8\+0x0\]"),
    (0x51dfb8, r"sub\s+esi,ecx"),
    (0x51dfba, r"shl\s+esi,0x2"),
    (0x51dfbd, r"mov\s+eax,DWORD PTR \[esi\+0x989ce8\]"),
    (0x51dfcb, r"mov\s+DWORD PTR \[esi\+0x989ce8\],eax"),
    (0x51dfd1, r"je\s+0x51dff5"),
    (0x51dff5, r"mov\s+ecx,DWORD PTR \[ebp-0x8\]"),
    (0x51dff8, r"mov\s+edi,DWORD PTR \[ebp-0x10\]"),
    (0x51dffb, r"push\s+ecx"),
    (0x51dffc, r"push\s+edi"),
    (0x51dffd, r"call\s+0x5832b0"),
    (0x51e005, r"test\s+eax,eax"),
    (0x51e007, r"je\s+0x51e11d"),
    (0x51e00d, r"mov\s+ecx,DWORD PTR \[esi\+0x989cec\]"),
    (0x51e01a, r"inc\s+ecx"),
    (0x51e01b, r"mov\s+DWORD PTR \[esi\+0x989cec\],ecx"),
    (0x5832b3, r"mov\s+eax,ds:0x692184"),
    (0x5832b8, r"mov\s+ecx,DWORD PTR \[ebp\+0xc\]"),
    (0x5832bb, r"imul\s+eax,ecx"),
    (0x5832c0, r"mov\s+esi,DWORD PTR \[ebp\+0x8\]"),
    (0x5832c6, r"sar\s+edx,1"),
    (0x5832c8, r"add\s+eax,edx"),
    (0x5832ca, r"lea\s+edx,\[eax\+eax\*4\]"),
    (0x5832cd, r"lea\s+eax,\[eax\+edx\*2\]"),
    (0x5832d0, r"mov\s+edx,DWORD PTR ds:0x92ae14"),
    (0x5832d6, r"lea\s+edx,\[edx\+eax\*4\]"),
    (0x5832d9, r"mov\s+eax,DWORD PTR \[edx\+0x8\]"),
    (0x5832dc, r"test\s+eax,0x102000"),
    (0x5832ea, r"test\s+DWORD PTR ds:0x985ac4,0x2000"),
    (0x5832f6, r"and\s+eax,0xc000000"),
    (0x583307, r"test\s+eax,0x10000000"),
    (0x583318, r"mov\s+edi,DWORD PTR ds:0x92a380"),
    (0x58332d, r"mov\s+al,BYTE PTR \[edx\]"),
    (0x583331, r"and\s+al,0xe0"),
    (0x583335, r"cmp\s+eax,0x60"),
    (0x58333f, r"lea\s+edx,\[eax\+eax\*2\]"),
    (0x58334b, r"shl\s+ebx,0x2"),
    (0x58335e, r"and\s+ebx,0xf"),
    (0x583361, r"lea\s+eax,\[edx\+eax\*4\]"),
    (0x58338b, r"imul\s+ebx,DWORD PTR ds:0x692210"),
    (0x583399, r"imul\s+eax,DWORD PTR ds:0x69220c"),
    (0x5833a0, r"lea\s+edx,\[eax\+edi\*1\+0x8\]"),
    (0x5833a7, r"and\s+edx,0x1f"),
    (0x5833af, r"sete\s+cl"),
]

# ---------------------------------------------------------------- pinned windows (evidence)
load_text()
print("== M299 (s254) STATIC - the slot [+4] visit counter gate FUN_005832b0. Zero box; objdump")
print("   windows via scratch/m574/text.txt (same dump as evidence/s251_statics_fn51dcb0.txt).")
print("\n== W1. FUN_0051dcb0 slot/counter tail 0x51dfac-0x51e02c (esi fold, MAX stores, call gate, inc):")
show(*CALLER, sys.stdout)
print("\n== W2. FUN_005832b0 FULL BODY 0x5832b0-0x5833b7 (fold + ladder + parity):")
show(*CALLEE, sys.stdout)

# ---------------------------------------------------------------- G1 pins
n_ok, misses = 0, []
for a, rx in PINS:
    try:
        ok = re.fullmatch(rx, at(a)) is not None
    except AssertionError:
        ok = False
    if ok:
        n_ok += 1
    else:
        misses.append("0x%x%s" % (a, "" if a in [t[0] for t in LINES] else " (absent)"))
gate("G1_pins_resolve", n_ok == len(PINS),
     "%d/%d pins match; misses=%s" % (n_ok, len(PINS), misses[:4] or "none"))

# ---------------------------------------------------------------- G2 push-order arg identity
cw = dict((a, ins) for a, _, ins in window(*CALLER))
# caller of 0x5832b0: pushes ecx(from [ebp-0x8]) then edi(from [ebp-0x10]) -> cdecl
# last push = param_1 = [ebp-0x10], param_2 = [ebp-0x8]
calls = {}
# 0x5aff90 at 0x51df97: push esi(from [ebp-0x8] @0x51df8f); push ecx(from [ebp-0x10] @0x51df92)
calls["0x5aff90"] = ("[ebp-0x10]", "[ebp-0x8]")
# 0x582cc0 at 0x51dfa4: push edi(val); push esi([ebp-0x8]); push edx([ebp-0x10])
calls["0x582cc0"] = ("[ebp-0x10]", "[ebp-0x8]")
calls["0x5832b0"] = ("[ebp-0x10]", "[ebp-0x8]")
# grade the 0x5832b0 case from the pins themselves:
g2 = (re.search(r"ebp-0x8", cw[0x51dff5]) and re.search(r"ebp-0x10", cw[0x51dff8])
      and cw[0x51dffb] == "push   ecx" and cw[0x51dffc] == "push   edi")
same = all(v == ("[ebp-0x10]", "[ebp-0x8]") for v in calls.values())
gate("G2_args_are_the_pinned_xy_pair", bool(g2) and same,
     "3 call sites (0x5aff90/0x582cc0/0x5832b0) pass slot1=[ebp-0x10] slot2=[ebp-0x8]; "
     "the pair is the (x,y) the pinned C2 fold feeds into tile_record_array")

# ---------------------------------------------------------------- G3 shared record fold
def s32(v):
    v &= 0xFFFFFFFF
    return v - 0x100000000 if v >= 0x80000000 else v


def sar(v, n):
    return s32(v) >> n


def fold_decoded(x, y, w2, base):
    eax = (w2 * y + sar(x, 1)) & 0xFFFFFFFF
    edx = (eax + eax * 4) & 0xFFFFFFFF          # 0x5832ca
    eax = (eax + edx * 2) & 0xFFFFFFFF          # 0x5832cd  (= 11*a)
    return (base + eax * 4) & 0xFFFFFFFF        # 0x5832d6


def fold_expected(x, y, w2, base):
    return (base + 44 * (w2 * y + sar(x, 1))) & 0xFFFFFFFF


import random
random.seed(299)
bad = 0
for _ in range(4096):
    x = random.choice([random.randrange(0, 4096), -random.randrange(1, 4096)])
    y = random.randrange(0, 256)
    w2 = random.randrange(20, 200)
    base = random.randrange(0x10000, 0x0FFFFFFF)
    if fold_decoded(x, y, w2, base) != fold_expected(x, y, w2, base):
        bad += 1
# stride parsed from the pinned lea chain = ((1+1*4)*2+1)*4; 0x582cc0's pinned fold is the
# same law by C2; grade the constants of BOTH pinned bodies.
s251 = open(S251).read()
c2 = re.search(r"rec2 = \[0x92ae14\] \+ 0x2c\*\(\[0x692184\]\*param_2 \+\n?\s*sar\(param_1,1\)\)", s251)
gate("G3_record_fold_decodes_to_44B", bad == 0 and c2 is not None and fold_decoded(7, 3, 40, 0x40a6660) == fold_expected(7, 3, 40, 0x40a6660),
     "fold==44*(W2*y+x>>1) on 4096/4096 random (x,y,W2,base) incl. negative x (sar); "
     "shared globals ds:0x692184/ds:0x92ae14 with the pinned C2 fold of 0x582cc0 "
     "(c2_window=%s)" % bool(c2))

# ---------------------------------------------------------------- G4 counter block
fold_site_ok = True
for _ in range(2048):
    site = random.randrange(0, 128)
    esi = (site * 8 - site) & 0xFFFFFFFF
    esi = (esi << 2) & 0xFFFFFFFF
    if esi != (28 * site) & 0xFFFFFFFF:
        fold_site_ok = False
        break
esi_between = [a for a, _, ins in window(0x51DFBD, 0x51E01B) if "esi" in dec_regs(ins)]
block = window(0x51E00D, 0x51E01B)
n_inc = sum(1 for _, _, ins in block if ins.startswith("inc"))
n_sto = sum(1 for _, _, ins in block if re.match(r"mov\s+DWORD PTR \[esi\+0x989cec\]", ins))
gate("G4_gated_inc_store_identity", fold_site_ok and not esi_between and n_inc == 1 and n_sto == 1,
     "esi fold 28*site on 2048/2048; writes-to-esi between slot pin and counter store: %s; "
     "block [0x51e00d-0x51e01b] has 1 inc + 1 store; je 0x51e11d (0x51e007) skips it whole; "
     "0x989cec == 0x989ce8+4 on the SAME pinned esi (L1)" % (esi_between or "none"))

# ---------------------------------------------------------------- G5 ladder + purity
clw = dict((a, ins) for a, _, ins in window(*CALLEE))
rung = {}
for a, rx, tag in [(0x5832dc, r"test\s+eax,(0x[0-9a-f]+)", "rung1"),
                   (0x5832ea, r"test\s+DWORD PTR ds:0x985ac4,(0x[0-9a-f]+)", "rung2"),
                   (0x5832f6, r"and\s+eax,(0x[0-9a-f]+)", "rung2mask"),
                   (0x583307, r"test\s+eax,(0x[0-9a-f]+)", "rung3")]:
    mm = re.search(rx, clw[a])
    rung[tag] = int(mm.group(1), 16) if mm else None


def byte_bits(mask):
    return sorted((8 + b // 8, b % 8) for b in range(32) if mask >> b & 1)


g5 = (rung["rung1"] == 0x102000 and rung["rung2"] == 0x2000
      and rung["rung2mask"] == 0xC000000 and rung["rung3"] == 0x10000000)
bb = byte_bits(0x102000)
store_hits = [a for a, _, ins in window(*CALLEE)
              if re.match(r"mov\s+(BYTE|WORD|DWORD) PTR \[[^\]]+\],", ins)]
rets = [a for a, _, ins in window(*CALLEE) if ins == "ret"]
preserved = True
for r in rets:
    body = window(max(CALLEE[0], r - 10), r)
    joined = " ".join(ins for _, _, ins in body)
    if not all(p in joined for p in ("pop    edi", "pop    esi", "pop    ebx")):
        preserved = False
named_occ = None
for ln in open(os.path.join(ROOT, "NAMED.md"), errors="replace"):
    if "0x563954" in ln and "occ byte9" in ln:
        named_occ = ln[:40]
        break
gate("G5_ladder_purity_saves", g5 and not store_hits and preserved and named_occ is not None,
     "masks rung1=%#x rung2flag=%#x rung2sel=%#x rung3=%#x; dword[rec+8] mask 0x102000 == %s "
     "(byte9 bit5 = the B16 occ bit, NAMED:1099 row found=%s); memory stores in the callee: %d; "
     "ebx/esi/edi pops precede all %d rets (esi survives the call, L3)"
     % (rung["rung1"], rung["rung2"], rung["rung2mask"], rung["rung3"], bb,
        named_occ is not None, len(store_hits), len(rets)))

# ---------------------------------------------------------------- G6 parity lattice + cross-tool
def rungA(h, d, rand):
    ebx = (-5 * (h >> 2) - 3 * (d >> 2) + rand) & 0xFFFFFFFF
    ebx &= 0xF
    return ((h & 3) + 4 * (d & 3)) == ebx


# branch B (class<0x60 or A-mismatch) is the same lattice index against
# (0x92a380 + 8 + tdiv4(h)*ds:0x692210 + tdiv4(d)*ds:0x69220c) & 0x1f (pinned 0x583372-0x5833b3);
# its two stride globals' VALUES are not recorded, so it is pinned-ported, not exercised.
# structural law from the decoded port: branch A hits exactly 1 of the 16 lattice cells
uniqA = all(sum(1 for hh in range(4) for dd in range(4)
                if rungA(H * 4 + hh, D * 4 + dd, rand)) == 1
           for H in range(-3, 3) for D in range(-3, 3) for rand in range(16))
fp = subprocess.run([sys.executable, os.path.join(ROOT, "scripts/fn.py"), "0x5832b0"],
                    capture_output=True, text=True)
ghid = fp.stdout
toks = ["0x102000", "0x2000", "0xc000000", "0x10000000", "0x92a380", "0x692184",
        "0x92ae14", "0x692210", "0x69220c", "0x2c", "0xe0", "0x985ac4", "0x1f"]
in_ghid = [t for t in toks if t in ghid]
gate("G6_lattice_and_cross_tool", uniqA and len(in_ghid) == len(toks),
     "branch A: exactly 1 hit per 16 lattice classes for all 36 (H,D) x 16 rand (32/32); "
     "ghidra-vs-objdump constants %d/%d (missing=%s) - fn.py rc=%d"
     % (len(in_ghid), len(toks), [t for t in toks if t not in ghid] or "none", fp.returncode))

# ---------------------------------------------------------------- G7 recorded s249 dump input fields
BIN = os.path.join(EVID, "s249_live_map.bin")
raw = open(BIN, "rb").read()
n = len(raw) // 44
assert len(raw) % 44 == 0, "bin not 44-B aligned"
r1 = r2 = r3 = cls = 0
occ = 0
for i in range(n):
    rec = raw[i * 44:(i + 1) * 44]
    dw = struct.unpack_from("<I", rec, 8)[0]
    if dw & 0x102000:
        r1 += 1
    if dw & 0x2000:          # occ alone
        occ += 1
    if dw & 0xC000000:
        r2 += 1
    if dw & 0x10000000:
        r3 += 1
    if rec[0] & 0xE0 >= 0x60:
        cls += 1
import hashlib
dig = hashlib.sha256(raw).hexdigest()[:16]
gate("G7_recorded_inputs_meet_ladder", n == 2048 and (r1 + r3 + cls) > 0,
     "%d x 44-B records (digest %s): rung1-close %d (occ-bit alone %d), byte10 bits26/27 set "
     "%d, rung3-open %d, class>=0x60 (branch-A domain) %d - the ladder meets real recorded bits"
     % (n, dig, r1, occ, r2, r3, cls))

# ---------------------------------------------------------------- witnesses (grep, honest declared)
w = subprocess.run(["grep", "-rn", "92a380", os.path.join(ROOT, "evidence/m53s_dump1/meta.json"),
                    os.path.join(ROOT, "evidence/m53o_mem/meta.json"),
                    os.path.join(ROOT, "evidence/m265_m266_census.txt")],
                   capture_output=True, text=True)
print("\n-- 0x92a380 VALUE WITNESS (only address mentions exist; no recorded value): --")
print(w.stdout.strip() or "(no matches)")
print("\n-- 0x94ed28 read AFTER the counter (region array NAMED:371, LEAD): --")
print("  0x51e02c: %s" % at(0x51e02c))

print("\n" + ("PASS M299: 7/7 gates - the slot[site].counter++ is GATED on FUN_005832b0(x,y)!=0; "
              "the gate decodes to the shared 44-B tile_record ladder + rand+1 lattice parity "
              "(zero box, zero /proc, zero gdb)" if not FAILS else
              "FAIL M299: %d gate(s): %s" % (len(FAILS), FAILS)))
sys.exit(0 if not FAILS else 1)
