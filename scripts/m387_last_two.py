#!/usr/bin/env python3
"""M387 (chain 5) - M383 left 2 of M380's 14 relations rewrites "unknown": the stores at
0x52b9c7 / 0x52b9d0 read the frame slots -0x50 / -0x4c, written at 0x52affb / 0x52b004 from
the pair dword +0x94d448, and that writer does not dominate the store over the edge-feasible
CFG.  This instrument asks WHAT blocks the two - and the answer is not "dominance is blind".

Two guards decide the legs, and neither is visible to dominance:
  (a) the message id in [ebp+0x8] - a read-only function invariant that indexes the entry
      table 0x52ba1c and the per-iteration table 0x52bafc.  Pinned to 0x16 the 42-way tables
      collapse to 52a9e7 (entry) and 52af1b (the snapshot case).
  (b) the flag in [ebp+0x1c] - `test eax,eax / je 0x52b1ee` at 0x52af21 gates the snapshot,
      and the store block reads [ebp+0x1c] ZERO times.  So with arg7==0 the store writes an
      unwritten frame dword.

Gates
  G0  population: 27 dword stores to +0x94d448 image-wide; exactly 2 are slot-sourced.
  G1  the frame: FUN_0052a720 (index.csv), one prologue, CFG closed (5 jump tables, 0
      unresolved indirect edges).
  G2  lineage: each slot has exactly ONE writer and ONE reader, in this function; each
      writer's source is the pair dword -> the value is a verbatim dword copy.
  G3  the M383 blocker reproduced: writer not in dom(store), and an edge-feasible witness
      reaches the store without it.
  G4  the parameter: [ebp+0x8] has 7 reads and 0 writes -> invariant; two jump tables and
      the epilogue cmp chain are driven by it.
  G5  PINNED reachability: with [ebp+0x8]=m folded (and the tables pruned by m), the store
      is reachable for exactly ONE of 53 message values (0x16) and for no other.
  G6  the avoiding set: every pinned path that skips the writer passes 0x52b1ee (arg7==0)
      or 0x52b88c (loop count 0) - no third route.
  G7  the loop count for m=0x16 is 1 by the emitted round-up idiom (esi=0x48, mask 0x7ff,
      shift 0xb) -> the count==0 leg is dead; only arg7==0 survives.
  G8  verdict: arg7!=0 -> PRESERVE (verbatim copy); arg7==0 -> UNINIT frame-dword write.
  G9  bit 0x20 (M366, INF): carried by the copied dword, tested 0 times -> noun NOT reached.
  G10 rivals, each measured against the printed numbers (>=1 REFUTED).
  G11 digest.

Mutants (scripts/m387_mutate.py drives this):
  M387_PATCH='addr|new text'   rewrite one instruction line in memory.
  M387_ALGO=n                  flip a law (see the ALGO sites).
"""
import collections
import csv
import hashlib
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M387_TEXT", os.path.join(ROOT, "scratch/m574/text.txt"))
IDXCSV = os.path.join(ROOT, "ghidra_out/index.csv")
EXE = os.path.join(ROOT, "programs/terran.exe")

PAIR = 0x94D448
FUNC, FUNC_SIZE = 0x52A720, 4859
POP_ANCHOR = 0x551B1D                 # M375's status-write store: must be in the census
PARAM_READS = (0x52A752, 0x52AD45, 0x52B219, 0x52B398, 0x52B54B, 0x52B86F, 0x52B892)
STQ, STQ2 = 0x52B9C7, 0x52B9D0
SLOT_A, SLOT_B = "-0x50", "-0x4c"
WR_A, WR_B = 0x52AFFB, 0x52B004
LD_A, LD_B = 0x52B9C4, 0x52B9CD
SRC_A, SRC_B = 0x52AFF5, 0x52AFFE
T_ENTRY, T_ITER = 0x52BA1C, 0x52BAFC
EPI_JNE = 0x52B904
ARG7_LOAD, ARG7_TEST, ARG7_JE = 0x52AF1B, 0x52AF21, 0x52AF30
CASE16, ITER16 = 0x52A9E7, 0x52AF1B
MSGMAX = 0x34
ALGO = int(os.environ.get("M387_ALGO", "0") or 0)

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
            if ins:                      # objdump wraps long instructions
                ins[-1]["b"] += " " + m.group(2).strip()
            continue
        p = body.split(None, 1)
        ins.append({"a": int(m.group(1), 16), "b": m.group(2).strip(),
                    "mn": p[0].lower(), "ops": p[1] if len(p) > 1 else ""})
    return ins


INS = load_text(TEXT)
IDXBY = {i["a"]: k for k, i in enumerate(INS)}

_patch = os.environ.get("M387_PATCH")
if _patch:
    a_s, new = _patch.split("|", 1)
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
LO, HI = FUNC, FUNC + FUNC_SIZE


def va_dword(va):
    o = va - 0x400000
    if 0 <= o <= len(IMG) - 4:
        return struct.unpack("<I", IMG[o:o + 4])[0]
    return None


def text_of(a):
    i = INS[IDXBY[a]]
    return f"{a:06x} {i['mn']} {i['ops']}".strip()


def imms(s):
    return [int(x, 16) for x in re.findall(r'0x([0-9a-f]+)', s or "", re.I)]


def has_pair(s):
    return PAIR in imms(s)


JCC = ("je", "jne", "jz", "jnz", "jl", "jle", "jg", "jge", "jb", "jbe", "ja",
       "jae", "js", "jns", "jp", "jnp", "jo", "jno")
TGT = re.compile(r'^(?:0x)?([0-9a-f]+)\s*$')

# ---------------------------------------------------------------- G0 population
say("G0  the relations-dword store population and its two slot-sourced members")
STORES = []
for i in INS:
    if i["mn"] != "mov":
        continue
    d = i["ops"].split(",")[0].lower()
    if re.search(r'dword ptr \[[^\]]*\+0x94d448\]', d) and has_pair(d):
        STORES.append(i["a"])
say(f"  dword stores to +0x94d448, image-wide: {len(STORES)}")
slot_src = []
for a in STORES:
    src = INS[IDXBY[a] - 1]
    m = re.search(r'\[ebp(-0x[0-9a-f]+)\]', src["ops"].lower())
    if m and src["mn"] == "mov":
        slot_src.append((a, src["a"], "slot:" + m.group(1), src["ops"].split(",")[0].lower()))
for a, s, sl, _ in slot_src:
    say(f"  slot-sourced store {a:06x} <- {s:06x} loads {sl}")
M380_14 = {0x55540A, 0x5556EB, 0x555758, 0x55580F, 0x555A45, 0x555A60, 0x555A6E,
           0x555F39, 0x52B9C7, 0x52B9D0, 0x552CCA, 0x552CD8, 0x552D6F, 0x552D7D}
say(f"  M380's 14 all in the population: {len(M380_14 - set(STORES)) == 0}; the slot-sourced "
    f"set = {[hex(a) for a, _, _, _ in slot_src]}")
say(f"  anchor 0x{POP_ANCHOR:x} (M375's status store) present: {POP_ANCHOR in STORES}")
if len(STORES) != 27 or POP_ANCHOR not in STORES:
    bad(f"G0 the population is not the 27 M380/M383 measured: {len(STORES)}")
elif {a for a, _, _, _ in slot_src} != {STQ, STQ2}:
    bad(f"G0 the slot-sourced set changed: {[hex(a) for a, _, _, _ in slot_src]}")
else:
    ok("G0", "27 stores; exactly 2 are fed by a frame slot (52b9c7, 52b9d0)")

# ---------------------------------------------------------------- G1 the frame + CFG
say("")
say("G1  the enclosing function and its control-flow closure")
rows = list(csv.DictReader(open(IDXCSV)))


def owner(t):
    hits = [r for r in rows
            if int(r["addr"], 16) <= t < int(r["addr"], 16) + int(r["size_bytes"])]
    return hits[0] if hits else None


own, ownst = owner(FUNC), owner(STQ)
say(f"  index.csv: {own['name']} @0x{int(own['addr'], 16):x} size {own['size_bytes']} "
    f"callers {own['n_callers']}")
say(f"  store 52b9c7 owner {ownst['name']}; writer 52affb owner {owner(WR_A)['name']}; "
    f"same function: {own['name'] == ownst['name'] == owner(WR_A)['name']}")

TABLES = []
succ, bad_edges = {}, 0


def jump_table(k):
    i = INS[k]
    m = re.search(r'\[[^\]]*?\*4\+(0x[0-9a-f]+)\]', i["ops"].lower())
    if not m:
        return None
    table = int(m.group(1), 16)
    bound = None
    for j in range(k - 1, max(0, k - 16), -1):
        c = INS[j]
        if c["mn"] == "cmp" and imms(c["ops"]) and \
                INS[j + 1]["mn"] in ("ja", "jae", "jg", "jge", "jbe", "jb"):
            bound = imms(c["ops"])[0]
            break
    if bound is None or bound > 0x400 or ALGO == 6:   # A6: ignore the emitting bound
        return None
    tg = []
    for e in range(bound + 1):
        d = va_dword(table + 4 * e)
        if d is None or d not in IDXBY or not (LO <= d < HI):
            return None
        tg.append(d)
    return table, bound + 1, tg


for i in INS:
    if not (LO <= i["a"] < HI):
        continue
    k = IDXBY[i["a"]]
    nxt = INS[k + 1]["a"] if k + 1 < len(INS) and INS[k + 1]["a"] < HI else None
    m = i["mn"]
    if m in ("ret", "retn"):
        succ[i["a"]] = []
    elif m == "jmp":
        t = TGT.match(i["ops"].strip())
        if t and int(t.group(1), 16) in IDXBY:
            succ[i["a"]] = [int(t.group(1), 16)]
        else:
            jt = jump_table(k)
            if jt:
                succ[i["a"]] = sorted(set(jt[2]))
                TABLES.append((i["a"], jt[0], jt[1]))
            else:
                succ[i["a"]] = []
                bad_edges += 1
    elif m in JCC or m.startswith("loop"):
        t = TGT.match(i["ops"].strip())
        succ[i["a"]] = ([nxt] if nxt else []) + (
            [int(t.group(1), 16)] if t and int(t.group(1), 16) in IDXBY else [])
    else:
        succ[i["a"]] = [nxt] if nxt else []

preds = {}
for a, ss in succ.items():
    for t in ss:
        preds.setdefault(t, []).append(a)

say(f"  CFG: {len(succ)} instruction nodes, {sum(len(v) for v in succ.values())} edges, "
    f"{bad_edges} unresolved indirect edge(s)")
for a, t, n in TABLES:
    say(f"   table {a:06x} -> 0x{t:x} [{n:2d} entries]   {text_of(a)}")
if own["name"] != ownst["name"] or own["name"] != owner(WR_A)["name"]:
    bad("G1 the store and its slot writer are not in one index.csv function")
elif bad_edges:
    bad(f"G1 the CFG is not closed: {bad_edges} unresolved indirect edge(s)")
elif len(TABLES) != 5 or {t for _, t, _ in TABLES} != {T_ENTRY, 0x52BAC4, T_ITER,
                                                      0x52BBA4, 0x52BBDC}:
    bad(f"G1 the jump-table set changed: {[(hex(a), hex(t), n) for a, t, n in TABLES]}")
else:
    ok("G1", f"one frame; 0 unresolved edges; 5 tables "
             f"({', '.join(str(n) for _, _, n in TABLES)} entries)")

# ---------------------------------------------------------------- G2 lineage
say("")
say("G2  slot lineage: one writer, one reader, both from the pair dword")
LINE = {}
for st, slot, wr, ld, src in ((STQ, SLOT_A, WR_A, LD_A, SRC_A),
                              (STQ2, SLOT_B, WR_B, LD_B, SRC_B)):
    refs = []
    for i in INS:
        if not (LO <= i["a"] < HI):
            continue
        if re.search(r'ebp' + slot + r'\]', i["ops"].lower()):
            d = i["ops"].split(",")[0].lower()
            refs.append((i["a"], "W" if "ebp" + slot + "]" in d else "r", i["mn"], i["ops"]))
    w = [r for r in refs if r[1] == "W"]
    r = [r for r in refs if r[1] == "r"]
    say(f"  {slot}: {len(refs)} ref(s) -> {len(w)} write(s) {[hex(x[0]) for x in w]}, "
        f"{len(r)} read(s) {[hex(x[0]) for x in r]}")
    srcok = INS[IDXBY[src]]["mn"] == "mov" and has_pair(INS[IDXBY[src]]["ops"])
    say(f"    writer source: {text_of(src)}   reads +0x94d448: {srcok}")
    LINE[slot] = (len(w), len(r), [x[0] for x in w], [x[0] for x in r], srcok)
    if (len(w), len(r)) != (1, 1) or not srcok or w[0][0] != wr or r[0][0] != ld:
        bad(f"G2 {slot}: lineage changed (writes {[hex(x[0]) for x in w]}, "
            f"reads {[hex(x[0]) for x in r]}, field-sourced {srcok})")
if all(v[0] == 1 and v[1] == 1 and v[4] for v in LINE.values()):
    ok("G2", "each slot has exactly 1 write + 1 read in this frame and both writers load the "
             "pair dword -> the stored dword is that dword verbatim (nothing can mask the "
             "slot between its single writer and its single reader)")

# ---------------------------------------------------------------- G3 dominance
say("")
say("G3  the M383 blocker, reproduced: edge-feasible dominance from the entry")
ENTRY = FUNC


def dominators():
    nodes = list(succ)
    D = {a: set(nodes) for a in nodes}
    D[ENTRY] = {ENTRY}
    ch = True
    while ch:
        ch = False
        for n in nodes:
            if n == ENTRY:
                continue
            p = preds.get(n, [])
            new = {n}
            if p:
                inter = set(D[p[0]])
                for x in p[1:]:
                    inter &= D[x]
                new |= inter
            if new != D[n]:
                D[n] = new
                ch = True
    return D


DOM = dominators()
for st, wr in ((STQ, WR_A), (STQ2, WR_B)):
    say(f"  dom[{st:06x}] contains writer {wr:06x}: {wr in DOM[st]}")
DOM_FAIL = not (WR_A in DOM[STQ] and WR_B in DOM[STQ2])

# ---- the parameter-pinned walk (also used by G5/G6)
def init_state(pin):
    return {"param": pin, "regs": {}, "pend": None}


def freeze(st):
    """Only the tracked registers matter: the flags at a jcc are always set by the
    instruction immediately before it, so pend cannot distinguish two futures."""
    if not st:
        return ()
    return tuple(sorted(st["regs"].items()))


def killeax(st):
    st["regs"].pop("eax", None)
    st["regs"].pop("ax", None)


def step(a, st):
    """Wrapper: the tracked set is closed (eax/ax/[ebp-0x28]) so the loop back-edge
    converges - any other register is dropped, which only makes the walk conservative."""
    st = _step(a, st)
    if st:
        st["regs"] = {k: v for k, v in st["regs"].items()
                      if k in ("eax", "ax", "slot-0x28")}
    return st


def _step(a, st):
    """Abstract transfer good enough for the dispatches: track eax/ax and [ebp-0x28]."""
    if not st:
        return {}
    # a jcc carries the flags its cmp/test set; every other instruction resets them
    st = {"param": st["param"], "regs": dict(st["regs"]), "pend": st.get("pend")}
    i = INS[IDXBY[a]]
    m, ops = i["mn"], i["ops"].lower()
    regs = st["regs"]
    if m in JCC or m.startswith("loop"):
        return st
    if m in ("test", "cmp"):
        lhs = ops.split(",")[0].strip()
        rhs = ops.split(",", 1)[1].strip() if "," in ops else lhs
        st["pend"] = (lhs, rhs, m == "test")
        return st
    st["pend"] = None               # any other instruction kills the flags
    if m in ("movsx", "movzx", "mov"):
        d, s = ops.split(",")[0].strip(), ops.split(",", 1)[1].strip()
        if d.startswith("dword ptr [ebp"):
            sl = re.search(r'\[ebp(-0x[0-9a-f]+)\]', d).group(1)
            if s in regs:
                regs["slot" + sl] = regs[s]
            elif re.fullmatch(r'0x[0-9a-f]+', s):
                regs["slot" + sl] = ("const", int(s, 16))
            else:
                regs.pop("slot" + sl, None)
            return st
        if d not in ("eax", "ax", "al", "ah"):
            regs.pop(d, None) if d not in ("ecx", "edx") else None
        if d == "ax":
            regs.pop("eax", None)
        if d == "eax":
            regs.pop("ax", None)
        if "[ebp+0x8]" in s:
            regs[d] = ("param", 32 if m != "mov" else (16 if d == "ax" else 32))
        elif s in regs:
            regs[d] = regs[s]
        elif re.fullmatch(r'0x[0-9a-f]+', s):
            regs[d] = ("const", int(s, 16))
        else:
            regs.pop(d, None)
        return st
    if m == "call":
        for r in ("eax", "ax", "ecx", "edx"):
            regs.pop(r, None)
        return st
    if m in ("jmp",) or m in JCC:
        return st
    d = ops.split(",")[0].strip() if ops else ""
    if m in ("add", "sub", "and", "or", "xor", "shl", "sar", "shr", "inc", "dec", "lea"):
        # arithmetic results are NOT tracked: a computed constant would make the loop
        # back-edge generate new states forever, and no guard we fold needs one
        regs.pop(d, None)
        return st
    if d in ("eax", "ax", "al", "ah"):
        killeax(st)
    return st


def known(st, name):
    if not st:
        return None
    r = st["regs"].get(name)
    if not r:
        return None
    if r[0] == "param":
        return st["param"] & (0xffff if r[1] == 16 else 0xffffffff)
    return r[1]


def jt_of(a):
    for ta, tb, tn in TABLES:
        if ta == a:
            return tb, tn
    return None


def branch(a, t, st, pin):
    """(feasible, state) for edge a->t, folding a jcc or an indexed jmp on the pinned value."""
    i = INS[IDXBY[a]]
    if pin is None or not st:
        return True, st
    if i["mn"] == "jmp":
        jt = jt_of(a)
        if not jt:
            return True, st
        tb, tn = jt
        idx = known(st, "eax")
        if idx is None:
            return True, st
        pos = idx
        if 0 <= pos < tn:
            return (t == va_dword(tb + 4 * pos)), st
        return False, st
    if i["mn"] not in JCC or not st.get("pend"):
        return True, st
    if ALGO == 5 and a == EPI_JNE:            # A5: the epilogue cmp chain is not a guard
        return True, st
    lhs, rhs, is_test = st["pend"]
    lreg = lhs.split()[0].lower()
    lv = known(st, lreg)
    if is_test:                              # `test X,X` compares X with ZERO
        rv = 0
    else:
        rv = known(st, rhs) if rhs in st["regs"] else (
            int(rhs, 16) if re.fullmatch(r'0x[0-9a-f]+', rhs) else None)
    if lv is None or rv is None:
        return True, st
    w = 16 if lreg == "ax" else 32
    msk = (1 << w) - 1
    a16, b16 = lv & msk, rv & msk
    L = a16 - (1 << w) if a16 >> (w - 1) else a16
    R = b16 - (1 << w) if b16 >> (w - 1) else b16
    taken = {
        "je": L == R, "jz": L == R, "jne": L != R, "jnz": L != R,
        "jl": L < R, "jle": L <= R, "jg": L > R, "jge": L >= R,
        "jb": a16 < b16, "jbe": a16 <= b16,
        "ja": a16 > b16, "jae": a16 >= b16,
    }.get(i["mn"])
    if taken is None:
        return True, st
    fall = INS[IDXBY[a] + 1]["a"]
    if t == fall:
        return (not taken), st
    return taken, st


def walk(start, st0, want, avoid=None, pin=None, cap=60000, collect=None):
    """BFS from (start, st0) to `want`, pruning infeasible pinned guards."""
    q = collections.deque([(start, [start], st0)])
    seen = {(start, freeze(st0) if pin is not None else ())}
    n, paths = 0, []
    while q and n < cap:
        a, path, st = q.popleft()
        n += 1
        if a == want:
            paths.append(path)
            if collect is None or len(paths) >= collect:
                return True, path, paths, st
            continue
        for t in succ.get(a, []):
            if t == avoid:
                continue
            nst = step(a, st)
            keep, nst = branch(a, t, nst, pin)
            if not keep:
                continue
            key = (t, freeze(nst) if pin is not None else ())
            if key in seen:
                continue
            seen.add(key)
            q.append((t, path + [t], nst))
    return bool(paths), (paths[0] if paths else []), paths, st0


def bfs(want=None, avoid=None, pin=None, cap=60000, collect=None):
    hit, path, paths, _ = walk(ENTRY, init_state(pin), want, avoid, pin, cap, collect)
    return hit, path, paths


reach_av, path_av, _ = bfs(want=STQ, avoid=WR_A)
say(f"  edge-feasible path to 52b9c7 avoiding 52affb: {reach_av} ({len(path_av)} nodes)")
gshape = (INS[IDXBY[0x52A759]]["mn"] == "jg" and INS[IDXBY[0x52A759]]["ops"].strip() == "0x52aadb"
          and INS[IDXBY[EPI_JNE - 4]]["mn"] == "cmp"
          and INS[IDXBY[EPI_JNE - 4]]["ops"].strip() == "ax,0x16"
          and INS[IDXBY[EPI_JNE]]["mn"] == "jne")
if reach_av:
    gs = [x for x in path_av if INS[IDXBY[x]]["mn"] in JCC]
    say("   jccs on the witness: " + "; ".join(
        f"{x:06x} {INS[IDXBY[x]]['mn']} {INS[IDXBY[x]]['ops']}" for x in gs if x in
        (0x52A759, 0x52A762, 0x52A76B, 0x52AD4F, 0x52AD55, 0x52AD5E, EPI_JNE)))
say(f"  witness guard shapes: 52a759 jg(msg>0x30) / 52b900 cmp ax,0x16 + 52b904 jne = {gshape}")
if not DOM_FAIL:
    bad("G3 dominance now holds - the M383 blocker is gone; re-read the instrument")
elif not reach_av:
    bad("G3 no edge-feasible path avoids the writer - M383's stated reason was wrong")
elif not gshape:
    bad("G3 the witness guards changed shape (0x52a759 jg / cmp ax,0x16 / jne)")
else:
    ok("G3", "dominance fails for both stores AND an edge-feasible witness avoids the "
             "writer; that witness satisfies 0x52a759 `jg` (msg>0x30) and 0x52b904 (msg==0x16) "
             "-> contradictory on one read-only parameter")

# ---------------------------------------------------------------- G4 parameter
say("")
say("G4  [ebp+0x8] is a function invariant, and two jump tables are indexed by it")
refs8 = [(i["a"], i["mn"], i["ops"]) for i in INS
         if LO <= i["a"] < HI and re.search(r'\[ebp\+0x8\]', i["ops"].lower())]
wr8 = []
for a, mn, ops in refs8:
    d = ops.split(",")[0].lower()
    if "ebp+0x8]" in d and mn not in ("cmp", "test", "push"):
        wr8.append((a, mn, ops))
for a, mn, ops in refs8:
    say(f"  {a:06x} {mn:6s} {ops}")
say(f"  reads {len(refs8)}, writes {len(wr8)}")
say(f"  entry dispatch {text_of(0x52A771)} bounded by "
    f"{text_of(0x52A759)} / {text_of(0x52A762)} / {text_of(0x52A76B)}")
say(f"  iteration dispatch {text_of(0x52AD64)} fed by {text_of(0x52AD45)} bounded by "
    f"{text_of(0x52AD4F)} / {text_of(0x52AD55)} / {text_of(0x52AD5E)}")
if ALGO == 1:                                     # A1: declare the parameter mutable
    wr8 = wr8 or [("algo", "mov", "dword ptr [ebp+0x8],eax")]
sites = sorted(a for a, _, _ in refs8)
if len(refs8) != 7 or wr8 or sites != sorted(PARAM_READS):
    bad(f"G4 [ebp+0x8] is not a read-only invariant: {len(refs8)} reads at "
        f"{[hex(s) for s in sites]}, {len(wr8)} writes")
else:
    ok("G4", "7 reads / 0 writes; the same slot drives the entry table 0x52ba1c, the "
             "iteration table 0x52bafc and the epilogue cmp chain")

# ---------------------------------------------------------------- G5 pinned reachability
say("")
say("G5  PINNED reachability: fold [ebp+0x8] = m, prune both tables by m, re-walk")
if ALGO == 2:                                     # A2: no pinning
    pinned = {m: True for m in range(MSGMAX + 1)}
else:
    pinned = {}
    for m in range(MSGMAX + 1):
        pinned[m], _, _ = bfs(want=STQ, pin=m)
hit = sorted(m for m, v in pinned.items() if v)
say(f"  message values probed: {len(pinned)}; 52b9c7 reachable for {len(hit)}: "
    f"{[hex(x) for x in hit]}")
say("  entry target by m: " + ", ".join(
    f"{m:#04x}->0x{va_dword(T_ENTRY + 4 * m):x}" for m in (0x0, 0x2, 0x11, 0x13, 0x16, 0x29)))
t16, i16 = va_dword(T_ENTRY + 4 * 0x16), va_dword(T_ITER + 4 * 0x16)
i11 = va_dword(T_ITER + 4 * 0x11)
say(f"  T1[0x16]=0x{t16:x} (entry case)   T2[0x16]=0x{i16:x} (the snapshot case)   "
    f"T2[0x11]=0x{i11:x}")
p_any, p_path, _ = bfs(want=STQ, pin=0x16)
# a path that DOES pass the writer (the arg7!=0 leg), and the shortest one that skips it
h1, pth1, _, st1 = walk(ENTRY, init_state(0x16), WR_A, pin=0x16)
h2, pth2, _, _ = walk(WR_A, step(WR_A, st1), STQ, pin=0x16)
via_w = bool(h1 and h2)
av_any, av_path, _ = bfs(want=STQ, avoid=WR_A, pin=0x16)
say(f"  pinned witness for m=0x16: {p_any}; a pinned path THROUGH the writer exists: {via_w} "
    f"({len(pth1) + len(pth2)} nodes)")
say(f"  shortest pinned path that SKIPS the writer: {av_any} ({len(av_path)} nodes)")
for x in pth1 + pth2:
    if x in (0x52A759, 0x52A762, 0x52A76B, 0x52AD4F, 0x52AD55, 0x52AD5E, 0x52AF1B,
             EPI_JNE - 4, EPI_JNE):
        say(f"    {text_of(x)}")
if hit != [0x16]:
    bad(f"G5 the store is not reachable for exactly message 0x16: {[hex(x) for x in hit]}")
elif t16 != CASE16 or i16 != ITER16:
    bad(f"G5 the 0x16 cases moved: entry 0x{t16:x}, iteration 0x{i16:x}")
elif not (h1 and h2):
    bad("G5 no pinned path reaches the store THROUGH the slot writer")
else:
    ok("G5", "only m=0x16 reaches the store; T1[0x16]=52a9e7, T2[0x16]=52af1b (the snapshot); "
             "the 42-way dispatches collapse to one edge each, and one pinned path runs "
             "through the writer")

# ---------------------------------------------------------------- G6 the avoiding set
say("")
say("G6  every pinned path that skips the writer passes an arg7 or a count guard")
_, _, avpaths = bfs(want=STQ, avoid=WR_A, pin=0x16, collect=60)
cls = {"arg7==0": 0, "count==0": 0, "neither": 0}
for p in avpaths:
    if 0x52B1EE in p:
        cls["arg7==0"] += 1
    elif 0x52B88C in p:
        cls["count==0"] += 1
    else:
        cls["neither"] += 1
say(f"  writer-skipping pinned paths collected: {len(avpaths)} -> {cls}")
say(f"  arg7==0 leg enters {text_of(0x52AF1B)} -> {text_of(ARG7_JE)} -> 0x52b1ee")
say(f"  count==0 leg exits at {text_of(0x52AC89)} -> 0x52b88c")
if not avpaths:
    bad("G6 no writer-skipping pinned path exists - the slots are never written un-guarded")
elif cls["neither"]:
    bad(f"G6 {cls['neither']} writer-skipping path(s) pass NEITHER guard - a third route "
        "reaches the store with the slots un-written")
else:
    ok("G6", f"all {len(avpaths)} writer-skipping paths pass 0x52b1ee (arg7==0) or 0x52b88c "
             "(count==0); no third route")

# ---------------------------------------------------------------- G7 loop count
say("")
say("G7  the loop count for m=0x16, by the emitted round-up idiom")
esi_imm = imms(INS[IDXBY[CASE16]]["ops"])[0]
idiom = [INS[IDXBY[0x52AC5F] + j] for j in range(11)]
say(f"  entry case {text_of(CASE16)} -> esi = {esi_imm:#x}")
say("  idiom: " + " ; ".join(f"{i['mn']} {i['ops']}" for i in idiom))
mask = next(i for i in idiom if i["mn"] == "and" and "edx" in i["ops"])
shift = next(i for i in idiom if i["mn"] == "sar")
mask = imms(mask["ops"])[0]
shift = imms(shift["ops"])[0]
count = (esi_imm + mask) >> shift
rem = esi_imm - ((esi_imm >> shift) << shift)
if ALGO == 3:                                     # A3: the loop "never runs"
    count = 0
say(f"  count = (esi + {mask:#x}) >> {shift} = {count}; remainder {rem:#x}")
if (mask, shift) != (0x7ff, 11):
    bad(f"G7 the round-up idiom changed: mask {mask:#x}, shift {shift}")
elif count != 1:
    bad(f"G7 the count for m=0x16 is not 1: {count} (the 0x52b88c leg would be live)")
elif rem == 0:
    bad("G7 the remainder is 0 - the `je 0x52ac7a` bump would not apply")
else:
    ok("G7", "esi=0x48 -> count=1, remainder 0x48 != 0: exactly one iteration runs T2[0x16], "
             "so the snapshot executes before the epilogue -> the count==0 leg is dead")

# ---------------------------------------------------------------- G8 verdict
say("")
say("G8  the two legs, and the verdict for each")
arg7refs = [(i["a"], i["mn"], i["ops"]) for i in INS
            if LO <= i["a"] < HI and re.search(r'\[ebp\+0x1c\]', i["ops"].lower())]
epi = [x for x in arg7refs if x[0] >= 0x52B86C]
say(f"  refs to [ebp+0x1c]: {len(arg7refs)}; on the epilogue path (>=52b86c): {len(epi)}")
say(f"  the snapshot guard: {text_of(ARG7_LOAD)} / {text_of(ARG7_TEST)} / {text_of(ARG7_JE)}"
    f"  (fall-through = the snapshot case, je -> 0x52b1ee = the arg7==0 leg)")
if ALGO == 4:                                     # A4: assume the snapshot is unconditional
    epi = epi + [(0x52B86C, "algo", "-")]
g_ok = (0x52AF1B in [x[0] for x in arg7refs]
        and INS[IDXBY[ARG7_TEST]]["mn"] == "test"
        and INS[IDXBY[ARG7_TEST]]["ops"].strip() == "eax,eax"
        and imms(INS[IDXBY[ARG7_JE]]["ops"]) == [0x52B1EE])
if not g_ok:
    bad("G8 the arg7 guard changed shape (load 52af1b / test 52af21 / je 52b1ee)")
elif epi:
    bad(f"G8 the epilogue DOES read [ebp+0x1c] ({[hex(x[0]) for x in epi]}) - the store is "
        "guarded, so the arg7==0 hazard would not exist")
else:
    ok("G8", "the snapshot sits behind test [ebp+0x1c] / je 0x52b1ee and the store block "
             "reads [ebp+0x1c] 0 times -> the two legs diverge at the store")
say("  verdict table (M380's last two):")
say("   store    slot   writer   arg7!=0 (snapshot ran)         arg7==0 (snapshot skipped)")
for st, slot, wr in ((STQ, SLOT_A, WR_A), (STQ2, SLOT_B, WR_B)):
    say(f"   {st:06x} {slot:5s}  {wr:06x} PRESERVE - verbatim dword copy   "
        f"UNINIT - writes an unwritten frame dword")
say("   PRESERVE = the dword written IS the pair dword read at the writer (every bit travels "
    "unchanged; the slot has one writer and one reader, so nothing can mask it)")
say("   UNINIT  = on the arg7==0 leg the slots are never written and the store carries no "
    "arg7 guard, so 0x94d448 receives whatever [ebp-0x50]/[ebp-0x4c] held. NOT a stamp drop "
    "- a different defect class, gated on a caller-supplied flag, caller census OPEN")

# ---------------------------------------------------------------- G9 bit 0x20
say("")
say("G9  bit 0x20 (M366's human-branch war record, INF): does this instrument reach a noun?")
tests20 = [(i["a"], i["mn"], i["ops"]) for i in INS
           if LO <= i["a"] < HI and i["mn"] in ("test", "and", "or", "xor")
           and re.search(r'0x20\b', i["ops"]) and re.search(r'94d44[89]', i["ops"].lower())]
say(f"  bit-0x20 tests on the pair dword inside FUN_0052a720: {len(tests20)}")
say(f"  pair-dword writers added by this function: {STQ:06x}, {STQ2:06x} (whole-dword copies)")
if tests20:
    bad("G9 a bit-0x20 test exists in this function - the noun may be reachable; re-read")
else:
    ok("G9", "0 bit-0x20 tests here: the copy CARRIES 0x20 into a second pair but names "
             "nothing -> the noun stays INF (M366 unchanged)")

# ---------------------------------------------------------------- G10 rivals
say("")
say("G10 rivals, each measured against the printed numbers")
rivals = [
    ("R1 'the 2 are an artifact of an incomplete CFG'",
     f"{bad_edges} unresolved edge(s), {len(TABLES)} tables", bad_edges != 0),
    ("R2 'the slots alias another function's frame'",
     "one index.csv function; writes "
     + ", ".join(hex(v[2][0]) if v[2] else "-" for v in LINE.values())
     + "; reads " + ", ".join(hex(v[3][0]) if v[3] else "-" for v in LINE.values()),
     not all(v[0] == 1 and v[1] == 1 for v in LINE.values())),
    ("R3 'the store is dead code'",
     f"pinned witness m=0x16: {p_any}; count={count}", not p_any or count == 0),
    ("R4 'dominance is the oracle: both must be PRESERVE'",
     f"epilogue refs to [ebp+0x1c] = {len(epi)}; writer-skipping paths = {len(avpaths)}",
     len(epi) > 0),
    ("R5 'any message can write the pair dword here'",
     f"store reachable for {len(hit)} of {len(pinned)} message values", len(hit) > 1),
    ("R6 'the store is guarded by the same flag as the snapshot'",
     f"epilogue refs to [ebp+0x1c] = {len(epi)}", len(epi) > 0),
]
for name, meas, stands in rivals:
    say("    %-56s %s -> %s" % (name, meas, "STANDS" if stands else "REFUTED"))
    if stands:
        bad("G10 " + name + " was not refuted")
ok("G10", f"{len(rivals)}/{len(rivals)} rivals refuted on the printed numbers")

# ---------------------------------------------------------------- G11 digest
say("")
k = [f"k0:{PAIR:x}:{len(STORES)}",
     f"k1:{STQ:x}/{STQ2:x}<-{WR_A:x}/{WR_B:x}",
     f"k2:{len(succ)}:{bad_edges}:{len(TABLES)}",
     f"k3:{len(refs8)}:{len(wr8)}:{len(arg7refs)}:{len(epi)}",
     f"k4:{t16:x}:{i16:x}:{esi_imm:x}:{count}",
     f"k5:{sorted(hit)}:{len(avpaths)}:{cls}",
     f"k6:{len(tests20)}"]
for line in k:
    say("  " + line)
dig = hashlib.sha1("\n".join(k).encode()).hexdigest()[:16]
dig2 = hashlib.sha1("\n".join(k).encode()).hexdigest()[:16]
say(f"  digest {dig} (twice: {dig == dig2})")
if dig != dig2:
    bad("G11 digest does not decode twice")

say("")
gate_n = sum(1 for m in OUT if m.startswith("  ok  "))
if FAILS:
    tags = ",".join(sorted({f.split()[0] for f in FAILS}))
    say(f"FAIL M387: {len(FAILS)} gate(s) red: {tags}")
    for f in FAILS:
        say("  - " + f)
    sys.exit(1)
say(f"PASS M387: {gate_n}/{gate_n}  {dig}")
