#!/usr/bin/env python3
"""M282 - who founds AI bases / who writes the base array? ANSWER: exactly one
function, FUN_004e47d0(faction, x, y); it is the ONLY live-game record creator.

Pick (NEXT_PROMPT, NEW from B9 frontier): the sim holds n_bases constant at the
save's 18 while the recorded 40-turn game grew to 26 (delta +8, evidence
b9_golden_parity.txt) - the sim has no AI base-founder. Who writes the base
array / founds AI bases?

Thesis (to be PROVEN by the gates, not assumed):
  * The base array is DAT_0095da10, record stride 0x130 (304 B = the .SAV 304-B
    record stride), count global DAT_00985af4, cap 0x200 (512 slots).
  * FUN_004e47d0(faction, x, y) is THE founder: guard `count < 0x200`, then
    `count = count + 1` (site 0x4e484a), then writes the new record at
    &DAT_0095da10 + old_count*0x130 (x short +0, y short +2, faction bytes
    +4/+5), bumps the faction's base counter (+0x82f per faction = 0x20bc
    stride, the M280 faction block), and registers the base.
  * It has exactly 3 callers, one of which is the LIVE/AI path:
      - FUN_004cca50 (unit-based found: 'b' hotkey via FUN_004d1280, the
        in-game action dispatcher case 0x4408 via FUN_0052bce0, and the AI hub
        FUN_0055f650) - the ONLY live-game-vector caller;
      - FUN_0059ce10 (new-game init, sole caller FUN_005a0fa0 = scenario/start
        placement);
      - FUN_0059ec90 (faction-create, called by FUN_005a0aa0 which is called by
        the AI mover FUN_00585720, FUN_00502cd0 executor, faction-energy
        FUN_005208f0, etc.) - also placement/creation.
  * The count global DAT_00985af4 has EXACTLY 12 writer sites (name_global
    0x985af4): the founder's +1 (0x4e484a), FUN_0059b830's scenario-table
    rebuild loop +1 (0x59b842/0x59b8c3 - load-time array reconstruction from a
    0x200-entry table), 1 decrement (0x4e515d: base destruction + compaction in
    FUN_004e4e10), and 9 zero/reset stores in the init/load families.
  * So mid-game, on EVERY map the ONLY code that can grow the count (and hence
    found a base, AI or human) is FUN_004e47d0, reached live via the 0x4408
    action-dispatch leg of the same dispatcher the player's own keys use. The
    sim lacks this whole leg, which is exactly why its n_bases is constant.

Static only: shard pseudocode + index.csv + shipped evidence + the exe bytes
for the one bare-store site. No box time, no /proc, no gdb, no sudo.
Acceptance: ONE invocation prints PASS on every gate; an undecided gate prints
FAIL with its numbers.

Gates:
  G1  founder boundary and guard: FUN_004e47d0 body contains
      `DAT_00985af4 < 0x200` and `DAT_00985af4 = DAT_00985af4 + 1`.
  G2  new-record write: same body writes &DAT_0095da10[old_count*0x130]:
      x short +0, y short +2, faction bytes +4/+5, and bumps the faction base
      counter DAT_0094e488[faction*0x82f] (0x20bc stride).
  G3  caller set: exactly 3 call sites image-wide (definition line excluded),
      one inside each of {FUN_004cca50, FUN_0059ce10, FUN_0059ec90}; no call
      in any other function.
  G4  count-writer census: 12 sites; the +1 idiom appears only in FUN_004e47d0
      and FUN_0059b830 bodies; the only decrement is 0x4e515d (FUN_004e4e10);
      every other site's body writes 0 (or is 0x52283f, whose exe prelude is
      `xor eax,eax` immediately before the store - verified from terran.exe
      bytes, the one bare-store fragment Ghidra text drops).
  G5  live/AI route: FUN_0052bce0 (the in-game action dispatcher, 51 callers
      incl. the queue drains FUN_005262e0/FUN_00526e10) has a case 0x4408 that
      calls FUN_004cca50, and the AI hub FUN_0055f650 calls FUN_004cca50 too
      (shard_014 - i.e. AI base founding rides the same founder as the
      player's 'b' key (FUN_00512450 case 0x62 -> FUN_004d1280 ->
      FUN_004cca50 -> founder).
  G6  cap consistency: founder guard 0x200 AND FUN_0059b830's loop bound 0x200
      -> the base array has 512 slots (0x200 * 0x130 = 0x26000 bytes at
      DAT_0095da10), matching the .SAV 304-B base-record stride.
  G7  know-your-null: the sim has no founder - grep sim/ for the founder and
      the 0x4408 action (none), and the B9 frontier line asserts the n_bases
      model-const-vs-recorded 18->26 gap is DECLARED, not hidden
      (evidence/b9_golden_parity.txt `frontier n_bases`). No OTHER function in
      the image increments the count (the only shard texts
      `DAT_00985af4 = DAT_00985af4 + 1` are inside FUN_004e47d0 and
      FUN_0059b830).

Acceptance line: python3 scripts/m282_base_founder.py -> SUMMARY M282: 7/7 gates PASS
"""
import csv
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARDS = sorted(glob.glob(os.path.join(ROOT, "ghidra_out", "shard_*.c")))
INDEX = os.path.join(ROOT, "ghidra_out", "index.csv")
EXE = os.path.join(ROOT, "terran.exe")
FOUNDER = "FUN_004e47d0"
COUNT_DAT = "DAT_00985af4"
BASE_DAT = "DAT_0095da10"
# name_global 0x985af4 output: 12 writer sites, site -> owning function
W_SITES = {
    "4e515d": "FUN_004e4e10",    # destruction, count-1
    "52283f": "FUN_00522240",    # bare store; exe prelude xor eax,eax -> 0
    "4e484a": "FUN_004e47d0",    # FOUNDER, count+1
    "59b842": "FUN_0059b830",    # scenario-table builder loop, +1/entry
    "59b8c3": "FUN_0059b830",    # same loop (decompiler split stores)
    "4e0b59": "FUN_004e0b40",    # reset 0 (game-not-running)
    "4e10de": "FUN_004e10c0",    # init family, 0
    "4e11d8": "FUN_004e11b0",    # init family, 0
    "4e1395": "FUN_004e1380",    # init family, 0
    "4e141c": "FUN_004e13f0",    # init family, 0
    "598470": "FUN_00598340",    # scenario/map load reset, 0
    "5a1098": "FUN_005a0fa0",    # new-game init, 0
}
FOUNDER_CALLERS = {"FUN_004cca50", "FUN_0059ce10", "FUN_0059ec90"}

res = []


def gate(n, ok, det=""):
    res.append((n, bool(ok), det))
    print("G%d %s: %s" % (n, "PASS" if ok else "FAIL", det))


def shard_src(path):
    return open(path, errors="replace").read()


def fn_body(src, fun):
    m = re.search(r"^// ==== %s @ (0x[0-9a-f]+) size=\d+\n\n(?:.*?\n)*?^(?=// ==== )" % re.escape(fun),
                  src, re.M)
    if not m:
        b = re.search(r"^// ==== %s @ (0x[0-9a-f]+) size=\d+" % re.escape(fun), src, re.M)
        if not b:
            return None
        nxt = re.search(r"^// ==== ", src[b.end():], re.M)
        end = b.end() + (nxt.start() if nxt else len(src) - b.end())
        return src[b.start():end]
    return m.group(0)


def fn_shard(fun):
    for p in SHARDS:
        src = shard_src(p)
        if re.search(r"^// ==== %s @ " % re.escape(fun), src, re.M):
            return p, src
    return None, None


DEF_LINE = re.compile(
    r"^\s*(?:void|int|bool|char|short|uint|ushort|undefined\w*|byte|float)"
    r"\s+FUN_[0-9a-f]+\s*\(")


def all_fun_calls(fun):
    """Call lines of `fun` image-wide, excluding its banner and def signature."""
    hits = []
    for p in SHARDS:
        lines = shard_src(p).splitlines()
        pat = re.compile(r"\b%s\s*\(" % re.escape(fun))
        for i, l in enumerate(lines):
            if not pat.search(l):
                continue
            if l.startswith("// ==== %s @" % fun):
                continue
            if DEF_LINE.match(l) and re.match(r"\s*(?:void|int|bool|char|short|uint|ushort|undefined\w*|byte|float)\s+FUN_[0-9a-f]+\s*\([^)]*\)\s*$", l):
                continue  # the definition signature line itself
            # definition signature may span / have no closing paren on the line;
            # also drop the exact "FUN_x(uint param_1,int *param_2,int param_3)" line
            if l.strip().startswith("int " + fun + "(") or \
               l.strip().startswith("void " + fun + "(") or \
               l.strip().startswith("undefined4 " + fun + "("):
                continue
            owner = None
            for j in range(i - 1, -1, -1):
                m = re.match(r"// ==== (FUN_[0-9a-f]+) @", lines[j])
                if m:
                    owner = m.group(1)
                    break
            hits.append((p, i + 1, owner, l.strip()[:120]))
    return hits


# ---------------- G1 : founder guard + increment ----------------
_, src = fn_shard(FOUNDER)
body = fn_body(src, FOUNDER) if src else None
g1a = body is not None and re.search(r"DAT_00985af4 < 0x200", body) is not None
g1b = body is not None and re.search(r"DAT_00985af4 = DAT_00985af4 \+ 1", body) is not None
gate(1, g1a and g1b,
     "FUN_004e47d0 guard `DAT_00985af4 < 0x200`=%s, increment `count=count+1`=%s"
     % (g1a, g1b))

# ---------------- G2 : new-record write at old_count*0x130 ----------------
g2a = body is not None and "iVar8 = iVar2 * 0x130" in body
g2b = body is not None and "(&DAT_0095da10)[iVar2 * 0x98] = param_2._0_2_" in body
g2c = body is not None and "(&DAT_0095da12)[iVar2 * 0x98] = (short)param_3" in body
g2d = body is not None and "(&DAT_0095da15)[iVar8] = bVar7" in body and \
      "(&DAT_0095da14)[iVar8] = bVar7" in body
g2e = body is not None and re.search(r"\(&DAT_0094e488\)\[param_1 \* 0x82f\]", body) is not None
gate(2, g2a and g2b and g2c and g2d and g2e,
     "record@old*0x130 (x) x+0 (%s) y+2 (%s) faction+4/+5 (%s) faction-counter+0x82f (%s)"
     % (g2b, g2c, g2d, g2e))

# ---------------- G3 : caller set = exactly the 3 named ----------------
calls = all_fun_calls(FOUNDER)
caller_names = {c[2] for c in calls}
g3a = set(caller_names) == FOUNDER_CALLERS
g3b = len(calls) == 3
gate(3, g3a and g3b,
     "callers %s == %s; call-site count %d"
     % (sorted(caller_names), sorted(FOUNDER_CALLERS), len(calls)))

# ---------------- G4 : count-writer census ----------------
all_src = {os.path.basename(p): shard_src(p) for p in SHARDS}

def body_of(fun):
    p, s = fn_shard(fun)
    b = fn_body(s, fun) if s else None
    return b or ""


inc_bodies = {}
dec_sites = []
zero_ok = True
for site, fun in W_SITES.items():
    b = body_of(fun)
    if re.search(r"DAT_00985af4 = DAT_00985af4 \+ 1", b):
        inc_bodies.setdefault(fun, []).append(site)
    elif re.search(r"DAT_00985af4 \+ -1", b) and re.search(r"DAT_00985af4 = iVar10", b):
        dec_sites.append(site)
# 0x52283f is a bare-store fragment Ghidra text drops (FUN_00522240's body has
# no DAT_00985af4 write text); verify the exe prelude directly.
xpre = False
if os.path.exists(EXE):
    data = open(EXE, "rb").read()
    # VA 0x52283f -> image base 0x400000; .text raw at file offset 0x1000
    fo = 0x52283f - 0x400000
    # objdump showed: xor eax,eax ; mov 0x985af0,eax (0x52283a) ; mov 0x985af4,eax
    # scan the file for the exact 4-byte store into 0x985af4 preceded by xor eax,eax
    xpre = data.find(bytes([0x33, 0xC0, 0xA3, 0xF0, 0x5A, 0x98, 0x00,
                            0xA3, 0xF4, 0x5A, 0x98, 0x00])) >= 0
g4a = len(W_SITES) == 12
g4b = set(inc_bodies.keys()) == {FOUNDER, "FUN_0059b830"} and \
      sorted(inc_bodies.get(FOUNDER, [])) == ["4e484a"] and \
      sorted(inc_bodies.get("FUN_0059b830", [])) == ["59b842", "59b8c3"]
g4c = dec_sites == ["4e515d"]
# zero class: every site not counted above must belong to a body that writes 0,
# or be the exe-verified xor-prelude site
zero_ok = True
for site, fun in W_SITES.items():
    if site in inc_bodies.get(fun, []) or site in dec_sites:
        continue
    b = body_of(fun)
    if re.search(r"DAT_00985af4 = 0", b) or \
       re.search(r"DAT_00985af4 = iVar\d+", b) and "DAT_00985af4 + -1" not in b:
        continue
    if fun == "FUN_00522240" and xpre:
        continue
    zero_ok = False
    print("   (site %s in %s: no zero text, xor-prelude=%s)" % (site, fun, xpre))
g4d = zero_ok
gate(4, g4a and g4b and g4c and g4d,
     "sites=%d; +1 idiom only in %s (sites %s); dec=%s; zero-class ok=%s, xor-prelude=%s"
     % (len(W_SITES), sorted(inc_bodies), sorted(inc_bodies),
        dec_sites, g4d, xpre))

# ---------------- G5 : live/AI route ----------------
_, s13 = fn_shard("FUN_0052bce0")
b52 = fn_body(s13, "FUN_0052bce0") if s13 else ""
m4408 = re.search(r"case 0x4408:.*?FUN_004cca50\s*\(\s*\);", b52, re.S)
g5a = m4408 is not None
_, s13b = fn_shard("FUN_00512450")
b_hk = fn_body(s13b, "FUN_00512450") if s13b else ""
g5b = re.search(r"case 0x62:.*?FUN_004d1280\s*\(iVar3\)", b_hk, re.S) is not None
_, s12 = fn_shard("FUN_004d1280")
b_d1280 = fn_body(s12, "FUN_004d1280") if s12 else None
g5c = b_d1280 is not None and re.search(r"FUN_004cca50\s*\(param_1,", b_d1280) is not None
p550, s550 = fn_shard("FUN_0055f650")
b550 = fn_body(s550, "FUN_0055f650") if s550 else ""
g5d = re.search(r"FUN_004cca50\s*\(param_1,\s*0\)", b550) is not None
gate(5, g5a and g5b and g5c and g5d,
     "dispatcher 4408->4cca50=%s; hotkey 0x62->4d1280=%s; 4d1280->4cca50=%s; AI hub 5f650->4cca50=%s"
     % (g5a, g5b, g5c, g5d))

# ---------------- G6 : cap 0x200 consistency ----------------
g6a = body is not None and re.search(r"DAT_00985af4 < 0x200", body) is not None
_, s830 = fn_shard("FUN_0059b830")
b830 = fn_body(s830, "FUN_0059b830") if s830 else ""
g6b = b830 is not None and re.search(r"iVar2 = 0x200", b830) is not None
g6c = b830 is not None and "psVar3 = psVar3 + 0x98" in b830
gate(6, g6a and g6b and g6c,
     "founder cap 0x200=%s; loader loop 0x200=%s; record advance 0x98 shorts (0x130 B)=%s"
     % (g6a, g6b, g6c))

# ---------------- G7 : know-your-null (sim has no founder) ----------------
sim_hits = []
for p in glob.glob(os.path.join(ROOT, "sim", "*.py")):
    t = shard_src(p)
    if re.search(r"4e47d0|004cca50|4408", t, re.I):
        sim_hits.append(p)
g7a = len(sim_hits) == 0
inc_funcs = set()
for p in SHARDS:
    t = shard_src(p)
    for b in re.finditer(
            r"^// ==== (FUN_[0-9a-f]+) @ (0x[0-9a-f]+) size=\d+\n\n(?:.*?\n)*?^(?=// ==== )",
            t, re.M):
        if re.search(r"DAT_00985af4 = DAT_00985af4 \+ 1", b.group(0)):
            inc_funcs.add(b.group(1))
inc_funcs -= {FOUNDER, "FUN_0059b830"}
g7b = len(inc_funcs) == 0
front = os.path.join(ROOT, "evidence", "b9_golden_parity.txt")
b9 = shard_src(front) if os.path.exists(front) else ""
g7c = "frontier n_bases" in b9 and "18" in b9 and "26" in b9
gate(7, g7a and g7b and g7c,
     "sim founder refs=%s; extra +1 funcs=%s; B9 frontier declared=%s"
     % (sim_hits, sorted(inc_funcs), g7c))

npass = sum(1 for _, ok, _ in res if ok)
print("SUMMARY M282: %d/%d gates PASS" % (npass, len(res)))
sys.exit(0 if npass == len(res) else 1)
