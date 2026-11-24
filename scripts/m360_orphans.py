#!/usr/bin/env python3
"""M360 (chain-3, STATIC) — the four dialog ids with no row (0x37/0x38/0x39/0x50).

PICK (run context 2026-11-24 ~02:40 EST): M357 left ids 0x37/0x38/0x39/0x50 with no
dialog row. Do they belong to a seventh page nobody builds, or a non-preferences dialog?

WHAT THE BYTES SAY (one line): neither. The Preferences dialog owns SEVEN row widgets
(+0x5974/0x649c/0x6fc4/0x7aec/0x8614/0x913c/0x9c64); the builder fills 66 rows into them
(8/12/14/8/13/4/7) while REBUILD 0x492940 queries 70 ids (8/12/14/11/14/4/7) - the extra
ids are three AUDIO/VISUAL radio rows (0x37/0x38/0x39, which paint as radio handlers that
relabel controls 0x4e/0x4c/0x4d) and one id (0x50) in the seventh widget whose BUILT row
carries a different id (0x30). A query for an absent id resolves to bit<rowcount>, not 0;
for the A/V widget that bit is written by nothing, so those three ORs never fire.

GATES (tables printed FIRST, then asserted; every VERIFIED row names a mutant in
scripts/m360_mutate.py):
  G1  widget inventory: the same 7 member offsets are the targets of add_item (builder),
      of 0x6051fa (rebuild) and of 0x6050d4 (paint).
  G2  rows vs queries vs paints per widget, and the set differences (the four orphans).
  G3  miss semantics: the row-scan in 0x6051fa/0x6050d4 sets index<count> on a miss;
      traced over every widget's row list (algorithm tracer).
  G4  paint handler classes decoded from the jump tables: 0x37/0x38/0x39 are RADIO
      handlers (no 0x6050d4 call); 0x50 sits in a block whose test operand is STALE.
  G5  bit-write census: the three producers of a checked bit, and which absent-id
      (widget,id) pairs are ever written.
  G6  the seventh widget's built row 0x30 is never queried and never painted.
  G7  RIVALS, each measured and each FAILING on the printed numbers.
"""
import hashlib
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M360_TEXT") or os.path.join(ROOT, "scratch/m574/text.txt")
EXE = os.environ.get("M360_EXE") or os.path.join(ROOT, "programs/terran.exe")
SCRIPT = os.environ.get("M360_SCRIPT") or os.path.join(ROOT, "programs/Script.txt")

BUILD = (0x48FED0, 0x491C00)     # page/row builder (one member widget per block)
ADD_ITEM = 0x604FD2              # widget::add_item(id, text, flag)  (this=ecx)
QUERY = 0x6051FA                 # widget::is_checked(id)            (this=ecx)
SET_ID = 0x6050D4                # widget::set_checked(id, on)       (this=ecx)
SET_BIT = 0x6052BD               # widget::set_bit(index, on)        (this=ecx)
TOGGLE_ID = 0x60505E
REBUILD = (0x492940, 0x4930D0)   # rebuild accumulators from the widgets
PAINT = (0x4930E0, 0x4937C7)     # paint the widgets from the accumulators
RELABEL = 0x493EC0               # relabel radio control 0x4b..0x4e from a dialog flag
CELL_A, CELL_B, CELL_C = 0x92BEFC, 0x92BF00, 0x92BF04
ORPHANS = (0x37, 0x38, 0x39, 0x50)

LINE = re.compile(r"^\s*([0-9a-f]{6,8}):\t([0-9a-f ]+?)\s*\t(.*?)(?:\t;.*)?$")
OPS = re.compile(r"^([a-z][a-z0-9]*)\s+(.*)$")
IMM = re.compile(r"^0x[0-9a-f]+$")
WIDGET_LEA = re.compile(r"^(edi|ecx|eax|edx|ebx),\[esi\+0x([0-9a-f]+)\]$")
WIDGET_ADD = re.compile(r"^ecx,0x([0-9a-f]+)$")
WIDGET_LEAB = re.compile(r"^(ecx|ebx|eax|edx),\[ebx\+0x([0-9a-f]+)\]$")

# ---------------------------------------------------------------- disassembly
def insns():
    out = []
    with open(TEXT, "r", errors="replace") as f:
        for line in f:
            m = LINE.match(line)
            if not m:
                continue
            t = m.group(3).strip()
            mo = OPS.match(t)
            out.append({"a": int(m.group(1), 16), "op": mo.group(1) if mo else t.split()[0],
                        "arg": mo.group(2) if mo else "", "t": t})
    return out

INS = insns()
POS = {i["a"]: n for n, i in enumerate(INS)}


def at(a):
    return INS[POS[a]] if a in POS else None


def win(lo, hi):
    return [i for i in INS if lo <= i["a"] <= hi]


def imm(s):
    s = s.strip()
    return int(s, 16) if IMM.match(s) else None


def hexa(v):
    return "0x%x" % v if v is not None else "?"


def bits(x, width=32):
    return [n for n in range(width) if (x >> n) & 1]


def row(*cols):
    print(" | ".join(str(c) for c in cols))


RESULT = []
BODY = []


def gate(g, ok, msg):
    RESULT.append((g, bool(ok)))
    line = "[%s] %s %s" % ("PASS" if ok else "FAIL", g, msg)
    print(line)
    BODY.append(line)
    return ok


def say(*cols):
    line = " | ".join(str(c) for c in cols)
    print(line)
    BODY.append(line)


# ---------------------------------------------------------------- PE helpers
def pe():
    d = open(EXE, "rb").read()
    p = struct.unpack_from("<I", d, 0x3C)[0]
    nsec = struct.unpack_from("<H", d, p + 6)[0]
    opt = struct.unpack_from("<H", d, p + 20)[0]
    img = struct.unpack_from("<I", d, p + 24 + 28)[0]
    base = p + 24 + opt
    secs = []
    for i in range(nsec):
        o = base + 40 * i
        vsz, va, rsz, ra = struct.unpack_from("<IIII", d, o + 8)
        secs.append((va, vsz, ra, rsz))
    return d, img, secs


D, IMG, SECS = pe()


def v2o(va):
    r = va - IMG
    for va0, vsz, ra, rsz in SECS:
        if va0 <= r < va0 + vsz:
            return ra + (r - va0) if r - va0 < rsz else None
    return None


def dword(va):
    o = v2o(va)
    return None if o is None else struct.unpack_from("<I", D, o)[0]


def byte(va):
    o = v2o(va)
    return None if o is None else D[o]


# ================================================================ G1 widgets
print("-- G1  the row widgets of the Preferences dialog (member offsets of one object) --")
builder_targets, rebuild_targets, paint_targets = {}, {}, {}
cur = [0]


def note(store, off):
    store.setdefault(off, 0)
    store[off] += 1


for i in win(*BUILD):
    if i["op"] == "lea":
        m = WIDGET_LEA.match(i["arg"])
        if m:
            cur[0] = int(m.group(2), 16)
    if i["op"] == "call" and imm(i["arg"]) == ADD_ITEM:
        note(builder_targets, cur[0])

for i in win(*REBUILD):
    if i["op"] == "lea":
        m = WIDGET_LEA.match(i["arg"])
        if m:
            note(rebuild_targets, int(m.group(2), 16))
for i in win(*PAINT):
    if i["op"] == "lea":
        m = WIDGET_LEAB.match(i["arg"])
        if m:
            note(paint_targets, int(m.group(2), 16))
    if i["op"] == "add" and i["arg"].startswith("ecx,0x"):
        v = imm(i["arg"].split(",", 1)[1])
        if v and v in rebuild_targets:
            note(paint_targets, v)

WIDGETS = sorted(set(builder_targets) | set(rebuild_targets))
say("widget offsets (builder/rebuild/paint refs):")
for w in WIDGETS:
    say("  +0x%04x  builder=%d refresh=%d paint=%d" %
        (w, builder_targets.get(w, 0), rebuild_targets.get(w, 0), paint_targets.get(w, 0)))
say("  builder targets not in rebuild:", [hexa(w) for w in sorted(set(builder_targets) - set(rebuild_targets))])
say("  rebuild targets not in builder:", [hexa(w) for w in sorted(set(rebuild_targets) - set(builder_targets))])
gate("G1a", len(WIDGETS) == 7 and set(builder_targets) == set(rebuild_targets) == set(paint_targets),
     "the same %d widget offsets are built, refreshed and painted (%s)" %
     (len(WIDGETS), ", ".join("+0x%04x" % w for w in WIDGETS)))
global_refs = [i["a"] for i in INS for w in WIDGETS
               if re.search(r"ds:0x%04x\b" % w, i["arg"])]
gate("G1b", not global_refs,
     "no widget offset is ever addressed absolutely (ds:0x...): all %d are members of the "
     "dialog object, so the id space cannot be shared with another dialog" % len(WIDGETS))

# ================================================================ G2 sets
print("\n-- G2  rows built / ids queried / ids painted, per widget --")


def builder_rows():
    """(widget, id) for every add_item call: id = the push just below the text push."""
    out = []
    w = None
    for n, i in enumerate(INS):
        if not (BUILD[0] <= i["a"] <= BUILD[1]):
            continue
        if i["op"] == "lea":
            m = WIDGET_LEA.match(i["arg"])
            if m:
                w = int(m.group(2), 16)
        if i["op"] == "call" and imm(i["arg"]) == ADD_ITEM:
            pid = None
            for j in range(n - 1, max(n - 5, 0), -1):
                v = imm(INS[j]["arg"]) if INS[j]["op"] == "push" else None
                if v is not None and v != 0x997120:
                    pid = v
                    break
            out.append((w, pid))
    return out


ROWS = builder_rows()


def block_ids(lo, hi, call, widget_re):
    """ids pushed immediately before `call`, grouped by the current member widget."""
    out = {}
    w = None
    for n, i in enumerate(INS):
        if not (lo <= i["a"] <= hi):
            continue
        if i["op"] == "lea":
            m = widget_re.match(i["arg"])
            if m:
                w = int(m.group(2), 16)
        if i["op"] == "add" and i["arg"].startswith("ecx,0x"):
            v = imm(i["arg"].split(",", 1)[1])
            if v:
                w = v
        if i["op"] == "call" and imm(i["arg"]) == call:
            pid = None
            for j in range(n - 1, max(n - 14, 0), -1):
                if INS[j]["op"] == "call":
                    break
                v = imm(INS[j]["arg"]) if INS[j]["op"] == "push" else None
                if v is not None and v != 0x997120:
                    pid = v
                    break
            out.setdefault(w, []).append(pid)
    return out


QUERIED = block_ids(*REBUILD, QUERY, WIDGET_LEA)
PAINTED = {}                                    # from the jump tables, below
say("widget | rows | queried")
for w in WIDGETS:
    r = [i for (ww, i) in ROWS if ww == w]
    q = QUERIED.get(w, [])
    say("+0x%04x | %d %s | %d %s" % (w, len(r), [hexa(x) for x in r], len(q), [hexa(x) for x in q]))
say("totals: rows=%d queried=%d" % (len(ROWS), sum(len(v) for v in QUERIED.values())))

# jump tables of the paint function, one per widget (order = iteration order)
PAINT_TABLES = [(0x4937C8, 8), (0x4937E8, 12), (0x493818, 14), (0x493898, 11),
                (0x493928, 13), (0x49395C, 4), (0x49396C, 7)]
HANDLER_TABLES = {"a4c": (0x4938C4, 7), "a40": (0x493850, 7)}
CLASS_BYTES = {"a4c": 0x4938E0, "a40": 0x49385C}


def entry_id_mask(va):
    """unused: kept out (see decode_block)."""
    return None, None


def decode_block(tab_va, n):
    """(id, mask) per jump-table entry, in table order (stop at the entry's jmp)."""
    out = []
    for k in range(n):
        va = dword(tab_va + 4 * k)
        n0 = POS[va]
        eid = emask = None
        for i in INS[n0:n0 + 5]:
            if i["op"] == "mov" and i["arg"].startswith("esi,") and eid is None:
                eid = imm(i["arg"].split(",", 1)[1])
            if i["op"] == "mov" and i["arg"].startswith("edi,") and emask is None:
                emask = imm(i["arg"].split(",", 1)[1])
            if i["op"] == "jmp" and imm(i["arg"]) and imm(i["arg"]) > va:
                t = at(imm(i["arg"]))
                if t is not None and t["op"] == "mov" and t["arg"].startswith("edi,") and emask is None:
                    emask = imm(t["arg"].split(",", 1)[1])
                break
            if i["op"] in ("ret", "call"):
                break
        out.append((eid, emask))
    return out


PAINT_BLOCKS = []
for (tab, n), w in zip(PAINT_TABLES, WIDGETS):
    dec = decode_block(tab, n)
    PAINT_BLOCKS.append((w, dec))
    PAINTED[w] = [x for x, _ in dec]

say("\nwidget | painted ids (paint order) | count")
for w, dec in PAINT_BLOCKS:
    say("+0x%04x | %s | %d" % (w, [hexa(x) for x, _ in dec], len(dec)))

diff = {}
for w in WIDGETS:
    r, q = set(i for (ww, i) in ROWS if ww == w), set(QUERIED.get(w, []))
    diff[w] = (sorted(q - r), sorted(r - q))
say("\nwidget | queried-but-not-built | built-but-not-queried")
for w in WIDGETS:
    say("+0x%04x | %s | %s" % (w, [hexa(x) for x in diff[w][0]], [hexa(x) for x in diff[w][1]]))

all_orphan = sorted({x for w in WIDGETS for x in diff[w][0]})
gate("G2a", len(ROWS) == 66 and len({i for (_, i) in ROWS}) == 66,
     "the builder fills 66 rows, all ids distinct")
gate("G2b", sum(len(v) for v in QUERIED.values()) == 70,
     "REBUILD queries 70 ids over the 7 widgets")
gate("G2c", set(all_orphan) == set(ORPHANS) | {0x30},
     "the queried-but-unbuilt ids are exactly %s" % [hexa(x) for x in all_orphan])
gate("G2d", diff[0x913C] == ([0x50], [0x30]),
     "the seventh widget has a SWAPPED id: it queries 0x50 and built 0x30")
gate("G2e", diff[0x7AEC] == ([0x37, 0x38, 0x39], []),
     "the Audio/Visual widget queries 3 ids it never builds")
gate("G2f", [w for w in WIDGETS if diff[w][0] or diff[w][1]] == [0x7AEC, 0x8614, 0x913C],
     "no other widget has a set difference (0x8614 queries the extra 0x30)")
rows_per = [len([1 for (ww, _) in ROWS if ww == w]) for w in WIDGETS]
q_per = [len(QUERIED.get(w, [])) for w in WIDGETS]
say("per-widget rows:", rows_per, " queries:", q_per)
gate("G2g", rows_per == [8, 12, 14, 8, 13, 4, 7] and q_per == [8, 12, 14, 11, 14, 4, 7],
     "the per-widget counts are exactly rows 8/12/14/8/13/4/7 and queries 8/12/14/11/14/4/7")

# ================================================================ G3 miss tracer
print("\n-- G3  miss semantics: 0x6051fa / 0x6050d4 scan the row list, index:=count on a miss --")
sc = win(0x6051FA, 0x6052BA)
say("loop head 0x605239 `mov [ebp-0x4],0x0`; body 0x605242 `add ecx,1`; exit 0x605251 "
    "`cmp eax,[edx+0x10] / jge`; hit test 0x60525f `cmp eax,[ebp+0x8]`")
say("tail 0x605291 `mov eax,[edx+ecx+0xd0]` (= node+0x14, the scanned index); test 0x6052b0 "
    "`and eax,[edx+ecx+0xec]` (node+0x30, the checked bitmap)")
init_zero = any(i["a"] == 0x605239 and i["op"] == "mov" and i["arg"].endswith(",0x0") for i in sc)
inc_one = any(i["a"] == 0x605245 and i["op"] == "add" and i["arg"].endswith(",0x1") for i in sc)
exit_cmp = any(i["a"] == 0x605251 and i["op"] == "cmp" and i["arg"].startswith("eax,DWORD PTR [edx+0x10]") for i in sc)
hit_cmp = any(i["a"] == 0x60525F and i["op"] == "cmp" and i["arg"] == "eax,DWORD PTR [ebp+0x8]" for i in sc)
bit_load = any(i["a"] == 0x605291 and i["op"] == "mov" and "+0xd0]" in i["arg"] for i in sc)
gate("G3a", init_zero and inc_one and exit_cmp and hit_cmp and bit_load,
     "the scan is start-0 / increment-on-miss / exit-at-count / test-id / bit<index>")

setid = win(0x6050D4, 0x6051F9)
zero_idx = [i["a"] for i in setid if i["op"] == "mov" and i["arg"] == "DWORD PTR [eax+0x14],0x0"]
exitc = [i["a"] for i in setid if i["op"] == "cmp" and i["arg"] == "eax,DWORD PTR [edx+0x10]"]
hit = [i["a"] for i in setid if i["op"] == "cmp" and i["arg"] == "eax,DWORD PTR [ebp+0x8]"]
shift = [i["a"] for i in setid if i["op"] == "mov" and i["arg"] == "eax,DWORD PTR [edx+ecx*1+0xd0]"]
orw = [i["a"] for i in setid if i["op"] == "or" and i["arg"] == "eax,edx"]
andw = [i["a"] for i in setid if i["op"] == "and" and i["arg"] == "edx,eax"]
say("set-by-id 0x6050d4: zero %s, exit-at-count %s, hit %s, shift<+0xd0> %s, OR %s, AND %s" %
    ([hexa(x) for x in zero_idx], [hexa(x) for x in exitc], [hexa(x) for x in hit],
     [hexa(x) for x in shift], [hexa(x) for x in orw], [hexa(x) for x in andw]))
gate("G3b", bool(zero_idx) and bool(exitc) and bool(hit) and bool(shift) and bool(orw) and bool(andw),
     "set-by-id 0x6050d4 runs the same start-0 / exit-at-count scan and shifts by the scanned "
     "index (+0xd0), so a miss writes bit<count> (not bit 0)")


LOOP_START = imm(at(0x605239)["arg"].split(",")[-1])
LOOP_STEP = imm(at(0x605245)["arg"].split(",")[-1])
JCC = at(0x605254)
EXIT_INCL = (JCC["op"] == "jge")          # jge -> loop ends when index >= count


def scan(rows_list, want, start=None, step=None, incl=None):
    """the measured loop: index<-start; exit at the count bound; advance only on a non-match."""
    start = LOOP_START if start is None else start
    step = LOOP_STEP if step is None else step
    incl = EXIT_INCL if incl is None else incl
    i, guard = start, 0
    while True:
        guard += 1
        if guard > 4096:
            return i
        if (incl and i >= len(rows_list)) or ((not incl) and i > len(rows_list)):
            return i
        if i < len(rows_list) and rows_list[i] == want:
            return i
        i += step


say("\nmeasured loop: start=%s step=%s exit=`%s` (inclusive bound=%s)" %
    (LOOP_START, LOOP_STEP, JCC["t"], EXIT_INCL))
say("\nwidget | count | id | resolved bit")
abs_pairs, scan_bad = [], []
for w in WIDGETS:
    r = [i for (ww, i) in ROWS if ww == w]
    for x in QUERIED.get(w, []):
        idx = scan(r, x)
        if x in r:
            if idx != r.index(x):
                scan_bad.append((w, x))
        else:
            abs_pairs.append((w, x, idx))
            if idx != len(r):
                scan_bad.append((w, x))
            say("+0x%04x | %d | %s | %d  (miss)" % (w, len(r), hexa(x), idx))
rival_zero = [(w, x, 0) for w, x, _ in abs_pairs]
rival_last = [(w, x, len([1 for (ww, _) in ROWS if ww == w]) - 1) for w, x, _ in abs_pairs]
say("rival 'miss leaves index 0'   :", [(hexa(x), v) for _, x, v in rival_zero])
say("rival 'miss leaves index n-1' :", [(hexa(x), v) for _, x, v in rival_last])
say("measured                     :", [(hexa(x), v) for _, x, v in abs_pairs])
gate("G3c", LOOP_START == 0 and LOOP_STEP == 1 and EXIT_INCL and not scan_bad
     and all(v == len([1 for (ww, _) in ROWS if ww == w]) for w, _, v in abs_pairs),
     "every present id resolves to its own row; all %d absent ids resolve to bit<count>, and "
     "both rival tracers give a different number on every one" % len(abs_pairs))
gate("G3d", all((w, x, v) != (w, x, v2) for (w, x, v), (_, _, v2) in zip(abs_pairs, rival_zero))
     and all((w, x, v) != (w, x, v2) for (w, x, v), (_, _, v2) in zip(abs_pairs, rival_last)),
     "the two rival miss conventions are refuted on every absent id")

# ================================================================ G4 handlers
print("\n-- G4  paint handler classes (jump tables 0x4938c4 / byte table 0x4938e0) --")
htab = [dword(0x4938C4 + 4 * k) for k in range(7)]
say("handler table 0x4938c4:", [hexa(x) for x in htab])
DISP = at(0x4934D4)
m = re.match(r"eax,\[esi-0x([0-9a-f]+)\]$", DISP["arg"])
DISP_KEY = int(m.group(1), 16) if m else None
say("dispatch 0x4934d4 `%s` -> class byte = *(0x4938e0 + id - %s)" % (DISP["t"],
     hexa(DISP_KEY) if DISP_KEY else "?"))


def class_of(x):
    return byte(0x4938E0 + x - DISP_KEY) if DISP_KEY is not None and 0 <= x - DISP_KEY < 0x60 else None


def handler_kind(va):
    body = []
    for i in INS[POS[va]:]:
        body.append(i)
        if i["op"] in ("ret", "jmp"):
            break
    calls = [imm(i["arg"]) for i in body if i["op"] == "call"]
    if SET_ID in calls:
        src = classify_src(body)
        return "checkbox", src, None
    if RELABEL in calls:
        ctrl = [imm(i["arg"]) for i in body if i["op"] == "push" and imm(i["arg"]) and imm(i["arg"]) in (0x4B, 0x4C, 0x4D, 0x4E)]
        return "radio", classify_src(body), (ctrl[0] if ctrl else None)
    return "?", "?", None


def classify_src(body):
    """the operator an entry tests: `and ecx,edi` (ecx=[ebx+0xa4c]) or `test eax,edi` (eax=[ebx+0xa50])."""
    for i in body:
        if i["op"] == "and" and i["arg"].startswith("ecx,edi"):
            return "a4c"
        if i["op"] == "mov" and i["arg"] == "eax,DWORD PTR [ebx+0xa50]":
            return "a50"
        if i["op"] == "mov" and i["arg"] == "ecx,DWORD PTR [ebx+0xa4c]":
            return "a4c"
    return "?"


say("\nA/V block (widget +0x7aec): id | mask | class | source | relabel ctrl")
AV = dict(PAINT_BLOCKS)[0x7AEC]
av_rows = []
for x, mask in AV:
    cls = class_of(x) if 0x13 <= x <= 0x58 else None
    hva = dword(0x4938C4 + 4 * cls) if cls is not None and cls < 7 else None
    kind, src, ctrl = handler_kind(hva) if hva else ("?", "?", None)
    av_rows.append((x, mask, cls, kind, src, ctrl, hva))
    say("+0x7aec | %s | %s | class %s | %s | %s | %s" %
        (hexa(x), hexa(mask), cls, kind, src, hexa(ctrl) if ctrl else "-"))
A = {r[0]: r for r in av_rows}
gate("G4a", A[0x37][3] == "radio" and A[0x38][3] == "radio" and A[0x39][3] == "radio"
     and (A[0x37][5], A[0x38][5], A[0x39][5]) == (0x4E, 0x4C, 0x4D),
     "the three unbuilt A/V ids paint as RADIO handlers relabelling controls 0x4e/0x4c/0x4d")
gate("G4b", (A[0x37][4], A[0x38][4], A[0x39][4]) == ("a4c", "a4c", "a50")
     and (A[0x37][1], A[0x38][1], A[0x39][1]) == (0x800, 0x400, 0x4000),
     "their masks are a4c 0x800 / a4c 0x400 / a50 0x4000 (M357's bits 11/10/14)")
radio_hva = [r[6] for r in av_rows if r[3] == "radio"]
say("radio handler VAs (from the class bytes):", [hexa(h) for h in radio_hva])


def body_calls(va):
    out = []
    for i in INS[POS[va]:]:
        if i["op"] == "call":
            out.append(imm(i["arg"]))
        if i["op"] in ("ret", "jmp") and out:
            break
        if i["op"] == "ret":
            break
    return out


gate("G4c", len(radio_hva) == 3 and all(SET_ID not in body_calls(h) for h in radio_hva),
     "the three radio handlers decoded for 0x37/0x38/0x39 never call set-by-id "
     "0x6050d4 (bodies scanned to their own jmp/ret)")
gate("G4f", DISP_KEY == 0x13 and (A[0x37][2], A[0x38][2], A[0x39][2]) == (1, 2, 3),
     "the dispatch key is the MEASURED (id-0x13) and the three ids read class bytes 1/2/3")

print("\nseventh widget (+0x913c) block 0x4936b8:")
b7 = win(0x4936B8, 0x493718)
src7 = [i["a"] for i in b7 if "0xa48" in i["arg"]]
b7_dec = dict(PAINT_BLOCKS)[0x913C]
say("  ids/masks:", [(hexa(x), hexa(m)) for x, m in b7_dec])
say("  a48 reloads in this block:", [hexa(x) for x in src7])
say("  test operand:", "0x%x `and eax,edi` with eax=[ebp-0x8]" % 0x4936F5)
b6_last_mask = dict(PAINT_BLOCKS)[0x8614][-1]
# every write to [ebp-0x8] between the a48 load and the seventh block's first test
w8 = [i for i in win(0x4935D4, 0x4936F0) if i["op"] == "mov"
      and i["arg"].startswith("DWORD PTR [ebp-0x8],")]
a48_load = [i["a"] for i in win(0x4935D4, 0x4936B1) if i["op"] == "mov"
            and i["arg"] == "ecx,DWORD PTR [ebx+0xa48]"]
b6_mask_mov = [i["a"] for i in win(0x4935D4, 0x4936B1) if i["op"] == "and"
               and i["arg"] == "ecx,edi"]
operand = at(0x4936F2)["arg"]
say("  writes to [ebp-0x8]:", [(hexa(i["a"]), i["arg"]) for i in w8])
say("  a48 -> ecx loads:", [hexa(x) for x in a48_load], " `and ecx,edi`:", [hexa(x) for x in b6_mask_mov])
say("  seventh-block operand load:", "0x4936f2 `%s`, tested at 0x4936f5 `%s`" %
    (operand, at(0x4936F5)["arg"]))
gate("G4d", not src7 and b6_last_mask[1] == 0x1000 and len(w8) == 1
     and w8[0]["a"] == 0x49368C and w8[0]["arg"].endswith(",ecx")
     and len(a48_load) == 1 and a48_load[0] == 0x4935D4 and len(b6_mask_mov) == 1
     and b6_mask_mov[0] == 0x49368A and operand == "eax,DWORD PTR [ebp-0x8]",
     "the seventh block never reloads a48: its operand [ebp-0x8] is THE single write at "
     "0x49368c = ecx & edi, ecx from [ebx+0xa48] (0x4935d4), edi = the block's last mask "
     "0x%x -> all four states are 0 for every a48" % b6_last_mask[1])
gate("G4e", all((row_mask & 0x1000) == 0 for _, row_mask in b7_dec if row_mask),
     "every mask in the seventh block is disjoint from 0x1000 -> the AND is identically 0")

# ================================================================ G5 bit writes
print("\n-- G5  who can write a checked bit --")
setbit_callers = [i["a"] for i in INS if i["op"] == "call" and imm(i["arg"]) == SET_BIT]
say("callers of set_bit 0x6052bd:", [hexa(x) for x in setbit_callers])
say("  - add_item 0x604fd2 (0x605008) with index=[this+0xcc] = the row count BEFORE append")
say("  - toggle-by-bit 0x605099 (0x6050b9 / 0x6050c9) with the caller's bit index")
say("  - set-by-id 0x6050d4 writes inline (OR 0x605197 / AND 0x6051e0) at the scanned index")
setid_callers = [i["a"] for i in INS if i["op"] == "call" and imm(i["arg"]) == SET_ID]
say("callers of set-by-id 0x6050d4: %d (%d in paint 0x4930e0, %d elsewhere)" %
    (len(setid_callers), len([x for x in setid_callers if PAINT[0] <= x <= PAINT[1]]),
     len([x for x in setid_callers if not (PAINT[0] <= x <= PAINT[1])])))
def first_call(va):
    """the first call control reaches from an entry VA, following one short forward jmp."""
    n = POS[va]
    for i in INS[n:n + 80]:
        if i["op"] == "jmp" and imm(i["arg"]) and imm(i["arg"]) > va and imm(i["arg"]) in POS:
            t = at(imm(i["arg"]))
            if t is not None and t["op"] == "mov" and t["arg"].startswith("edi,"):
                continue
            n2 = POS[imm(i["arg"])]
            for j in INS[n2:n2 + 40]:
                if j["op"] == "call":
                    return imm(j["arg"])
            return None
        if i["op"] == "call":
            return imm(i["arg"])
        if i["op"] in ("ret",):
            return None
    return None


bad_pairs = []
for (tab, n), (w, dec) in zip(PAINT_TABLES, PAINT_BLOCKS):
    r = [i for (ww, i) in ROWS if ww == w]
    merge = {0x5974: 0x49319D, 0x649C: 0x49341A, 0x6FC4: 0x4935BA, 0x7AEC: None,
             0x8614: 0x49369E, 0x913C: 0x493709, 0x9C64: 0x4937AC}[w]
    for k, (x, _) in enumerate(dec):
        if x in r:
            continue
        if merge is None:
            cls = class_of(x)
            tgt = dword(0x4938C4 + 4 * cls)
        else:
            tgt = merge
        if first_call(tgt) == SET_ID:
            bad_pairs.append((w, x))
say("absent-id (widget,id) pairs decoded from the PAINT blocks:", [(hexa(w), hexa(x)) for w, x in bad_pairs])
# census: every set-by-id call site in .text, with the widget it targets (member offset)
WID7 = set(WIDGETS)
def widget_at(n):
    """the member offset ecx holds at instruction n, traced over the preceding block."""
    j = n - 1
    while j > 0 and INS[j]["op"] != "call":
        j -= 1
    edi_off = w = None
    for i in INS[j:n]:
        if i["op"] == "lea":
            m = re.search(r"^(ecx|edi),\[(?:esi|ebx)\+0x([0-9a-f]+)\]$", i["arg"])
            if m:
                off = int(m.group(2), 16)
                if m.group(1) == "edi":
                    edi_off = off
                else:
                    w = off
        if i["op"] == "mov" and i["arg"] == "ecx,edi" and edi_off is not None:
            w = edi_off
        if i["op"] == "add" and i["arg"].startswith("ecx,0x"):
            v = imm(i["arg"].split(",", 1)[1])
            if v:
                w = v
    return w


sites = []
for n, i in enumerate(INS):
    if i["op"] == "call" and imm(i["arg"]) == SET_ID:
        sites.append((i["a"], widget_at(n)))
say("set-by-id call sites: %d total, %d target one of the seven widgets (%d in paint)" %
    (len(sites), len([1 for a, w in sites if w in WID7]),
     len([1 for a, w in sites if w in WID7 and PAINT[0] <= a <= PAINT[1]])))
foreign = [w for a, w in sites if w not in WID7]
say("  targets outside the seven widgets (other dialog objects):", sorted({hexa(w) for w in foreign}))
gate("G5c", len([1 for a, w in sites if w in WID7]) ==
     len([1 for a, w in sites if w in WID7 and PAINT[0] <= a <= PAINT[1]]),
     "every set-by-id call aimed at one of the seven widgets is inside PAINT 0x4930e0")
gate("G5a", len(setbit_callers) == 3 and imm(at(0x605008)["arg"]) == SET_BIT,
     "three bit-write paths, all indexed: add_item (index = count-so-far), toggle-by-bit, and "
     "set-by-id's inline OR/AND (index = the scan result)")
gate("G5b", bad_pairs == [(0x913C, 0x50)],
     "over the seven widgets the absent-id writes are EXACTLY [(0x913c,0x50)]: the A/V bit 8 "
     "and the +0x8614 bit 13 are written by nothing")

# ================================================================ G6 built row 0x30
print("\n-- G6  the id the seventh widget actually built (0x30) --")
q30 = [w for w in WIDGETS if 0x30 in QUERIED.get(w, [])]
p30 = [w for w, dec in PAINT_BLOCKS if 0x30 in [x for x, _ in dec]]
r30 = [w for (w, i) in ROWS if i == 0x30]
say("id 0x30: built in %s, queried in %s, painted in %s" %
    ([hexa(x) for x in r30], [hexa(x) for x in q30], [hexa(x) for x in p30]))
gate("G6a", r30 == [0x913C] and q30 == [0x8614] and p30 == [],
     "the built row 0x30 lives in +0x913c but is queried against +0x8614 and painted nowhere: "
     "its check state is read back from the wrong widget and never shown")

# ================================================================ G7 rivals
print("\n-- G7  RIVALS (each must FAIL on the printed numbers) --")
riv = []
riv.append(("R1 seventh page nobody builds",
            len([1 for (w, i) in ROWS if w == 0x913C]) == 0,
            "builder rows into +0x913c = %d (a page nobody builds would be 0)" %
            len([1 for (w, i) in ROWS if w == 0x913C])))
riv.append(("R2 a non-preferences dialog owns the ids",
            len([1 for (w, i) in ROWS if w is None]) > 0 or len(set(WIDGETS)) > 7,
            "every add_item site targets one of the 7 members of the one dialog object "
            "(%d widgets, 0 foreign targets)" % len(WIDGETS)))
riv.append(("R3 an absent id returns 0 immediately",
            len(bad_pairs) == 0,
            "the scan runs to count and tests bit<count>: %d absent-id set calls exist" % len(bad_pairs)))
riv.append(("R4 a miss leaves the index at 0",
            any(scan([i for (ww, i) in ROWS if ww == w], x) == 0 for w in WIDGETS for x in ORPHANS
                if x not in [i for (ww, i) in ROWS if ww == w]),
            "traced index on a miss = rowcount, never 0"))
for name, holds, ev in riv:
    say("%-42s | holds=%-5s | %s" % (name, holds, ev))
gate("G7a", not any(h for _, h, _ in riv), "all %d rivals are refuted by the printed numbers" % len(riv))

# Script.txt side (INFERRED correspondence, only the counts are gated)
print("\n-- Script.txt: the Audio/Visual section offers more lines than the exe builds --")
sec = {}
cur = None
for line in open(SCRIPT, errors="replace"):
    s = line.rstrip("\r\n")
    if re.match(r"^#[A-Z][A-Z0-9_]+$", s):
        cur = s[1:]
        sec[cur] = []
    elif cur and s.strip() and not s.startswith("#"):
        sec[cur].append(s.strip())
av_lines = [x for x in sec.get("AUDIOVISUALPREFS", []) if not x.startswith("caption")]
say("AUDIOVISUALPREFS lines=%d, exe rows for +0x7aec=%d, unbuilt ids=%d" %
    (len(av_lines), len([1 for (w, i) in ROWS if w == 0x7AEC]),
     len(diff[0x7AEC][0])))
say("unconsumed tail:", av_lines[len([1 for (w, i) in ROWS if w == 0x7AEC]):])
gate("G7b", len(av_lines) - len([1 for (w, i) in ROWS if w == 0x7AEC]) == len(diff[0x7AEC][0]) == 3,
     "the A/V section offers 3 more lines than the exe builds, and 3 ids go unbuilt (count match)")

# ================================================================ verdict
npass = sum(1 for _, ok in RESULT if ok)
print("\n-- VERDICT --")
say("id 0x37/0x38/0x39 = A/V radio rows (+0x7aec) that the builder no longer emits; "
    "0x50 = the seventh widget's 4th id, whose built row is 0x30")
say("an absent id resolves to bit<count> (8 / 13 / 4); the A/V bit 8 is written by nobody, "
    "so 0x37/0x38/0x39 contribute nothing; 0x50's write is masked to 0 by the stale operand")
digest = hashlib.sha1("\n".join(BODY).encode()).hexdigest()[:16]
print("[%s] M360: %d/%d gates" % ("PASS" if npass == len(RESULT) else "FAIL", npass, len(RESULT)))
print("DIGEST %s" % digest)
sys.exit(0 if npass == len(RESULT) else 1)
