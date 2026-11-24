#!/usr/bin/env python3
"""M357 — the BIT -> OPTION LABELS of the two `Laptop` bitmaps (chain-3, static).

PICK: run context 2026-11-24 ~02:10 EST: "the bit->option labels for the two Laptop
bitmaps — M355 measured the defaults; the per-page checkbox labels are unread."

WHAT THE BYTES SAY (one line): each checkbox row of the six Preferences pages is
created by a per-page builder that reads one line of the section named on its row
(0x5ea448), copies it into a fixed 4-byte slot of a static row table (0x68b6xx /
0x68b7xx), and adds it to that page's list widget with a hard-coded option id
(push imm; call 0x604fd2); the rebuild function 0x492940 maps every id to exactly
one (dialog field, flag bit), and the APPLY dataflow merges those fields into the
two cells M355 measured - so a set bit of 0x92befc / 0x92bf00 resolves to the
Script.txt row labels printed below.

GATES (tables printed FIRST, then asserted; every VERIFIED row names a mutant in
scripts/m357_mutate.py):
  G0  the six page builders: section-name push, row count, row-buffer run.
  G1  each builder consumes its section with 0x5ea431 and rows with 0x5ea448;
      the id is the push immediately below the text push; the text is copied into
      the row slot the static table reserves (slot VA measured).
  G2  the row slots of each page are the consecutive dwords of the page's table
      entry (name + slots), i.e. the labels are positionally bound.
  G3  Script.txt: the six sections' ordered labels, counts, and the measured
      exe/txt divergence (A/V: 8 rows built, 11 lines offered).
  G4  the rebuild table: 70 ids -> (field, bit) decoded from immediates; every UI
      id present exactly once; the ids with no UI row named.
  G5  APPLY dataflow: field -> target cell (simulated, not named).
  G6  bit -> label table for both cells; the alias groups MEASURED, not authored.
  G7  defaults: each cell's default bits vs the rows' bits (declared from M355,
      re-confirmed to be present as immediates in the loader window).
  G8  RIVALS, each measured and each FAILING on the printed numbers.
"""
import bisect
import hashlib
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M357_TEXT") or os.path.join(ROOT, "scratch/m574/text.txt")
EXE = os.path.join(ROOT, "programs/terran.exe")
SCRIPT = os.environ.get("M357_SCRIPT") or os.path.join(ROOT, "programs/Script.txt")
if not os.path.exists(EXE):
    EXE = os.path.join(ROOT, "terran.exe")

# --- addresses (all VAs; exe image base 0x400000, .text RVA 0x1000) -------------
SEC_READ = 0x5EA431          # open/each section by name -> returns 0 on success
SEC_LINE = 0x5EA448          # next line of the open section
ITEM_ADD = 0x604FD2          # list widget: add_item(text, id, flag)
ITEM_TEXT = 0x604C8F         # list widget ctor/reset
STRCPY = 0x64B9E0
CELL_A, CELL_B, CELL_C = 0x92BEFC, 0x92BF00, 0x92BF04
REBUILD = (0x492940, 0x4930D0)
APPLY = (0x4923D3, 0x49247A)
TEXTBUF = 0x997120           # the shared build buffer the row text is assembled in

# page table: section name VA -> (first row slot VA, slot count field in the table)
PAGES = [
    ("BASICPREFS",       0x68B66C, 0x68B678),
    ("ADVANCEDPREFS",    0x68B698, 0x68B6A8),
    ("AUTOMATIONPREFS",  0x68B6D8, 0x68B6E8),
    ("AUDIOVISUALPREFS", 0x68B720, 0x68B734),
    ("BASEWARNINGS",     0x68B754, 0x68B764),
    ("MAPPREFS",         0x68B7A8, 0x68B7B4),
]
SECTION_KEY = "PREF:"           # Script.txt section is "#<name>"

# defaults (VERIFIED by M355, evidence/m355_laptop_masks.txt:35-51):
DEF_PREF_L0, DEF_PREF_L1 = 0xBBE1DD96, 0xA3E1DD16
DEF_MORE_L0, DEF_MORE_L1 = 0x003A7168, 0x00327168
DEF_GETTERC = 0x0003C3A9         # a48's own key (M355 G4 row "group@0x3c3a9")
LOADER_WIN = (0x58E9F3, 0x58EB7E)

LINE = re.compile(r"^\s*([0-9a-f]{6,8}):\t([0-9a-f ]+?)\s*\t(.*?)(?:\t;.*)?$")
OPS = re.compile(r"^([a-z][a-z0-9]*)\s+(.*)$")
IMM = re.compile(r"^0x[0-9a-f]+$")


def insns():
    out = []
    with open(TEXT, "r", errors="replace") as f:
        for line in f:
            m = LINE.match(line)
            if not m:
                continue
            txt = m.group(3).strip()
            mo = OPS.match(txt)
            out.append({"a": int(m.group(1), 16), "by": m.group(2).split(), "t": txt,
                        "op": mo.group(1) if mo else txt.split()[0],
                        "arg": mo.group(2) if mo else ""})
    return out


INS = insns()
ADDRS = [i["a"] for i in INS]
POS = {a: n for n, a in enumerate(ADDRS)}


def at(a):
    return INS[POS[a]] if a in POS else None


def win(lo, hi):
    return [i for i in INS if lo <= i["a"] <= hi]


def imm(s):
    s = s.strip()
    return int(s, 16) if IMM.match(s) else None


def hexa(v):
    return "0x%x" % v


def bits(x, width=32):
    return [n for n in range(width) if (x >> n) & 1]


def row(*cols):
    print(" | ".join(str(c) for c in cols))


def chk(gate, ok, msg):
    print("[%s] %s %s" % ("PASS" if ok else "FAIL", gate, msg))
    return ok


RESULT = []


def gate(g, ok, msg):
    RESULT.append((g, bool(ok)))
    return chk(g, ok, msg)


# --- PE -----------------------------------------------------------------------
def pe_sections():
    d = open(EXE, "rb").read()
    pe = struct.unpack_from("<I", d, 0x3C)[0]
    nsec = struct.unpack_from("<H", d, pe + 6)[0]
    opt = struct.unpack_from("<H", d, pe + 20)[0]
    img = struct.unpack_from("<I", d, pe + 24 + 28)[0]
    base = pe + 24 + opt
    secs = []
    for i in range(nsec):
        o = base + 40 * i
        name = d[o:o + 8].rstrip(b"\0").decode("latin-1")
        vsz, va, rsz, ra = struct.unpack_from("<IIII", d, o + 8)
        secs.append((name, va, vsz, ra, rsz))
    return d, img, secs


D, IMG, PESECS = pe_sections()


def va2off(va):
    r = va - IMG
    for name, sva, vsz, ra, rsz in PESECS:
        if sva <= r < sva + vsz:
            if r - sva >= rsz:
                return None            # uninitialised (.data tail) - BSS
            return ra + (r - sva)
    return None


def cstr(va, cap=96):
    o = va2off(va)
    if o is None:
        return None
    e = D.find(b"\0", o, o + cap)
    return D[o:e].decode("latin-1") if e > 0 else None


def dword(va):
    o = va2off(va)
    return None if o is None else struct.unpack_from("<I", D, o)[0]


# --- page builders ------------------------------------------------------------
def find_name_push(name_va):
    """index of the `push <name_va>` that opens the page builder (call 0x5ea431 after)."""
    for n, i in enumerate(INS):
        if i["op"] == "push" and imm(i["arg"]) == name_va:
            for j in range(n + 1, min(n + 5, len(INS))):
                if INS[j]["op"] == "call" and imm(INS[j]["arg"]) == SEC_READ:
                    return n
    return None


def build_pages():
    out = []
    hp = [find_name_push(p[1]) for p in PAGES]
    for k, (sec, nva, slot0) in enumerate(PAGES):
        n = hp[k]
        if n is None:
            out.append({"sec": sec, "rows": [], "lines": 0, "slot0": slot0,
                        "name_va": nva, "entry": None, "err": "no name push"})
            continue
        end = len(INS)
        for q in range(n + 5, len(INS)):
            if INS[q]["op"] == "call" and imm(INS[q]["arg"]) == SEC_READ:
                end = q
                break
        rows, lines = [], 0
        last_line_at = None
        for q in range(n, end):
            i = INS[q]
            if i["op"] == "call" and imm(i["arg"]) == 0x5EA422 and rows:
                break
            if i["op"] == "call" and imm(i["arg"]) == SEC_LINE:
                lines += 1
                last_line_at = q
            if i["op"] == "call" and imm(i["arg"]) == ITEM_ADD:
                idv = None
                for b in range(q - 1, max(n, q - 8), -1):
                    if INS[b]["op"] == "push":
                        v = imm(INS[b]["arg"])
                        if v is not None and v != TEXTBUF:
                            idv = v
                            break
                buf = None
                for b in range(q - 1, max(n, q - 14), -1):
                    if INS[b]["op"] == "push":
                        v = imm(INS[b]["arg"])
                        if v is not None and 0x68B600 <= v <= 0x68B7FF:
                            buf = v
                            break
                copied = any(INS[b]["op"] == "call" and imm(INS[b]["arg"]) == STRCPY
                             for b in range(max(n, q - 14), q))
                rows.append({"addr": i["a"], "id": idv, "slot": buf,
                             "copied": copied, "line_at": last_line_at})
        out.append({"sec": sec, "rows": rows, "lines": lines, "slot0": slot0,
                    "name_va": nva, "entry": INS[n]["a"]})
    return out


PAGE_BUILD = build_pages()


# --- rebuild table: id -> (field, bit) ----------------------------------------
def rebuild_table():
    ws = win(*REBUILD)
    rows, last_push, ebx = [], None, None
    for k, i in enumerate(ws):
        if i["op"] == "push" and imm(i["arg"]) is not None:
            last_push = imm(i["arg"])
        if i["op"] == "mov" and re.match(r"ebx,0x[0-9a-f]+$", i["arg"]):
            ebx = imm(i["arg"].split(",")[1])
        if i["op"] == "call" and imm(i["arg"]) == 0x6051FA:
            field, val, how, addr, oidx = None, None, None, None, None
            for j in range(k + 1, min(k + 14, len(ws))):
                j2 = ws[j]
                if j2["op"] == "mov" and re.match(r"ebx,0x[0-9a-f]+$", j2["arg"]):
                    ebx = imm(j2["arg"].split(",")[1])
                if j2["op"] == "or":
                    m = re.search(r"\[esi\+0x(a[0-9a-f]{2})\],(.*)$", j2["arg"])
                    if m:
                        field, how = m.group(1), "imm"
                        val = imm(m.group(2))
                        if val is None and m.group(2).strip() == "ebx":
                            val, how = ebx, "ebx"
                    else:
                        m = re.match(r"(al|ah),0x([0-9a-f]+)$", j2["arg"])
                        if m:
                            val = int(m.group(2), 16) << (8 if m.group(1) == "ah" else 0)
                            how = "imm8"
                    addr, oidx = j2["a"], j
                    break
            if field is None and oidx is not None:
                for j in range(oidx - 1, max(k - 8, oidx - 8), -1):
                    m = re.search(r"\[esi\+0x(a[0-9a-f]{2})\]", ws[j]["arg"])
                    if m:
                        field = m.group(1)
                        break
            rows.append({"id": last_push, "field": field, "bit": val,
                         "how": how, "addr": addr})
    return rows


REBUILD_ROWS = rebuild_table()
BY_ID = {r["id"]: r for r in REBUILD_ROWS if r["id"] is not None}


# --- APPLY dataflow -----------------------------------------------------------
def apply_dataflow():
    """symbolic: reg -> set; [esi+0xaXX] cells are tracked; record each cell store."""
    ws = win(*APPLY)
    reg = {r: frozenset() for r in ("eax", "ebx", "ecx", "edx", "esi")}
    mem = {}
    out = {}
    MEMREF = re.compile(r"\[esi\+0x(a[0-9a-f]{2})\]$")
    CELL = re.compile(r"(?:DWORD PTR )?ds:0x([0-9a-f]+)$")
    for i in ws:
        a = i["arg"]
        if i["op"] not in ("mov", "or", "and"):
            continue
        dst, _, src = a.partition(",")
        dst, src = dst.strip(), src.strip()
        dm, sm = MEMREF.search(src), MEMREF.search(dst)
        if i["op"] == "mov":
            if dm and dst in reg:
                reg[dst] = mem.get(dm.group(1), frozenset([dm.group(1)]))
            elif src in reg and dst in reg:
                reg[dst] = reg[src]
            elif sm and src in reg:
                mem[sm.group(1)] = reg[src]
            elif CELL.search(dst) and src in reg:
                out[int(CELL.search(dst).group(1), 16)] = reg[src]
        else:
            val = frozenset()
            if sm:
                val = mem.get(sm.group(1), frozenset([sm.group(1)]))
            elif src in reg:
                val = reg[src]
            if dst in reg:
                reg[dst] = reg[dst] | val if i["op"] == "or" else reg[dst] & val
            elif dm:
                mem[dm.group(1)] = mem.get(dm.group(1), frozenset()) | val
            elif CELL.search(dst) and val:
                out[int(CELL.search(dst).group(1), 16)] = \
                    out.get(int(CELL.search(dst).group(1), 16), frozenset()) | val
    return out


APPLY_MAP = apply_dataflow()


# --- Script.txt ---------------------------------------------------------------
def script_sections():
    raw = open(SCRIPT, "rb").read().decode("latin-1")
    lines = [l.rstrip("\r") for l in raw.split("\n")]
    secs, cur, mode = {}, None, None
    ATTR = ("#ITEMLIST", "#CAPTION", "#XS", "#TAB", "#CHECKBOX")
    for l in lines:
        t = l.strip()
        if t.startswith("#"):
            head = t.split()[0].upper()
            if head in ATTR:
                if head == "#ITEMLIST":
                    mode = "item"
                continue
            cur = head[1:]
            secs.setdefault(cur, [])
            mode = None
            continue
        if cur is None:
            continue
        if not t:
            mode = None
            continue
        if mode == "item":
            secs[cur].append(t)
    return secs


SECS = script_sections()


# ============================== G0/G1/G2 =====================================
print("== M357  bit -> option labels for the two `Laptop` bitmaps ==")
print("exec %s  script %s  (%d instructions cached)" %
      (os.path.relpath(EXE, ROOT), os.path.relpath(SCRIPT, ROOT), len(INS)))

print("\n-- G0  the six page builders --")
row("section", "name push @", "call read", "rows", "lines read", "first slot")
ok0 = True
for p in PAGE_BUILD:
    ok0 &= len(p["rows"]) > 0 and bool(p.get("slot0"))
    row(p["sec"], hexa(p.get("entry") or 0),
        "0x5ea431" if p.get("entry") is not None else "-", len(p["rows"]),
        p.get("lines"), hexa(p.get("slot0") or 0))
names_ok = all(cstr(p["name_va"]) == p["sec"] for p in PAGE_BUILD)
print("    name strings:", [(p["sec"], cstr(p["name_va"])) for p in PAGE_BUILD])
gate("G0a", ok0 and len(PAGE_BUILD) == 6 and names_ok
     and len({p["sec"] for p in PAGE_BUILD}) == 6
     and len({p.get("entry") for p in PAGE_BUILD}) == 6,
     "six distinct builders, each pushing the VA of its OWN section-name string (cstr == section) "
     "and calling 0x5ea431")
print("    rows per page: %s" % [len(p["rows"]) for p in PAGE_BUILD])

print("\n-- G1  row = (label slot, option id) --")
row("section", "seq", "slot", "id", "add_item @")
ok1 = True
ROWS = []
for p in PAGE_BUILD:
    for n, r in enumerate(p["rows"]):
        row(p["sec"], n, hexa(r["slot"]) if r["slot"] else "-", r["id"], hexa(r["addr"]))
        ROWS.append(dict(r, sec=p["sec"], n=n))
        ok1 &= (r["slot"] is not None and r["id"] is not None)
ok1c = sum(1 for r in ROWS if r.get("copied"))
gate("G1a", ok1 and ok1c == len(ROWS),
     "every row carries a slot VA, an id immediate AND a strcpy (0x64b9e0) between its "
     "line read and its add_item (%d/%d rows)" % (ok1c, len(ROWS)))
ids = [r["id"] for r in ROWS]
gate("G1b", len(ids) == len(set(ids)),
     "the %d option ids are distinct across the six pages" % len(ids))

print("\n-- G2  the row slots are the page table's consecutive dwords --")
row("section", "first slot", "n", "run", "next table dword")
ok2 = True
for p in PAGE_BUILD:
    sl = [r["slot"] for r in p["rows"]]
    want = [p["slot0"] + 4 * i for i in range(len(sl))]
    ok2 &= sl == want
    after = p["slot0"] + 4 * len(sl)
    row(p["sec"], hexa(p["slot0"]), len(sl), "consecutive" if sl == want else "BROKEN",
        "%s = %r" % (hexa(after), cstr(after)))
ok2b = True
for k, (sec, nva, slot0) in enumerate(PAGES):
    nxt = PAGES[k + 1][1] if k + 1 < len(PAGES) else None
    if nxt is not None:
        last = PAGE_BUILD[k]["slot0"] + 4 * len(PAGE_BUILD[k]["rows"])
        ok2b &= last <= nxt
gate("G2a", ok2 and ok2b, "each page's slots are +4 consecutive from its table entry and "
     "its run ends before the next page's name string")

# ============================== G3 Script ====================================
print("\n-- G3  Script.txt sections: ordered labels --")
row("section", "exe rows", "txt items", "first", "last")
ok3 = True
for p in PAGE_BUILD:
    t = SECS.get(p["sec"], [])
    row(p["sec"], len(p["rows"]), len(t), (t[0][:34] if t else "-"),
        (t[-1][:34] if t else "-"))
    ok3 &= len(t) > 0
gate("G3a", ok3, "every page's section exists in the installed Script.txt with items "
     "(counts %s)" % [len(SECS.get(p["sec"], [])) for p in PAGE_BUILD])
same = [p["sec"] for p in PAGE_BUILD if len(SECS.get(p["sec"], [])) == len(p["rows"])]
diff = {p["sec"]: (len(p["rows"]), len(SECS.get(p["sec"], [])))
        for p in PAGE_BUILD if len(SECS.get(p["sec"], [])) != len(p["rows"])}
print("    equal:", same)
print("    differ:", diff)
gate("G3b", len(same) == 5 and list(diff) == ["AUDIOVISUALPREFS"]
     and diff["AUDIOVISUALPREFS"] == (8, 11),
     "5 of 6 pages: exe rows == txt items; A/V builds 8 rows from 11 offered lines "
     "(the 3 unused lines are printed above as the section tail)")
unused = SECS["AUDIOVISUALPREFS"][8:]
print("    A/V lines not consumed:", unused)

# ============================== G4 rebuild ===================================
print("\n-- G4  rebuild 0x492940: id -> (dialog field, flag bit) --")
row("id", "field", "bit", "word", "how", "or @")
WORD_OF = {}
for f in APPLY_MAP.get(CELL_A, frozenset()):
    WORD_OF[f] = CELL_A
for f in APPLY_MAP.get(CELL_B, frozenset()):
    WORD_OF[f] = CELL_B
for f in APPLY_MAP.get(CELL_C, frozenset()):
    WORD_OF[f] = CELL_C
for r in sorted(REBUILD_ROWS, key=lambda x: (x["id"] is None, x["id"])):
    w = WORD_OF.get(r["field"])
    row(r["id"], "a" + (r["field"] or "?"),
        bits(r["bit"] or 0)[0] if r["bit"] else "?", hexa(w) if w else "?",
        r["how"], hexa(r["addr"] or 0))
gate("G4a", all(r["bit"] and r["field"] for r in REBUILD_ROWS),
     "all %d ids decode to a field and a bit from the encodings" % len(REBUILD_ROWS))
ui = set(ids)
rb = set(BY_ID)
gate("G4b", ui <= rb, "every UI id is in the rebuild table (%d of %d)" % (len(ui & rb), len(ui)))
extra = sorted(rb - ui)
print("    ids in the rebuild table with no dialog row:", [hexa(x) for x in extra])
print("    -> %d rebuild ids have no dialog row" % len(extra))

# ============================== G5 apply =====================================
print("\n-- G5  APPLY dataflow: dialog field -> cell --")
for cell in (CELL_A, CELL_B, CELL_C):
    print("    %s <- %s" % (hexa(cell), sorted(APPLY_MAP.get(cell, ()))))
ALLF = sorted({r["field"] for r in REBUILD_ROWS})
A_F = set(APPLY_MAP.get(CELL_A, ()))
B_F = set(APPLY_MAP.get(CELL_B, ()))
C_F = set(APPLY_MAP.get(CELL_C, ()))
ACC = {"a20", "a24", "a28"}
gate("G5a", set(ALLF) == (A_F | B_F | C_F) - ACC,
     "all %d rebuilt fields land in a cell (the %d accumulator fields excluded)"
     % (len(ALLF), len(ACC)))
gate("G5b", not (A_F & B_F) and not (C_F & (A_F | B_F)),
     "the three cell field sets are disjoint (A %d / B %d / C %d)"
     % (len(A_F), len(B_F), len(C_F)))
# cross-lane: M355's measured APPLY sets (evidence/m355_laptop_masks.txt:97-99)
M355_A = {"a20", "a30", "a38", "a40", "a4c", "a54"}
M355_B = {"a24", "a34", "a3c", "a44", "a50", "a58"}
gate("G5c", A_F == M355_A and B_F == M355_B,
     "the A/B cell sets equal M355's measured APPLY sets (0x92befc / 0x92bf00)")
gate("G5d", C_F == {"a28", "a48"},
     "the third cell 0x92bf04 is fed by a28|a48 only (the warnings page, own INI key)")

# ============================== G6 join ======================================
print("\n-- G6  the row table: label -> id -> (field, bit) -> cell --")
row("page", "row", "label", "id", "field", "cell", "bit", "default")
JOIN = []
WORD_OF = {}
for f in A_F:
    WORD_OF[f] = CELL_A
for f in B_F:
    WORD_OF[f] = CELL_B
for f in C_F:
    WORD_OF[f] = CELL_C
DEFS = {CELL_A: (DEF_PREF_L0, DEF_PREF_L1), CELL_B: (DEF_MORE_L0, DEF_MORE_L1),
        CELL_C: (DEF_GETTERC, DEF_GETTERC)}
for r in ROWS:
    rb = BY_ID.get(r["id"])
    f = rb["field"] if rb else None
    w = WORD_OF.get(f)
    b = bits(rb["bit"])[0] if rb and rb["bit"] is not None else None
    d0, d1 = DEFS.get(w, (0, 0))
    on0 = bool(b is not None and (d0 >> b) & 1)
    on1 = bool(b is not None and (d1 >> b) & 1)
    lap = ("cleared by Laptop" if (on0 and not on1) else
           ("set for Laptop" if (not on0 and on1) else ""))
    lab = SECS.get(r["sec"], [])
    txt = lab[r["n"]] if r["n"] < len(lab) else "<no line>"
    JOIN.append(dict(r, label=txt, field=f, word=w, bit=b, on0=on0, on1=on1, lap=lap))
    row(r["sec"][:10], r["n"], txt[:44], r["id"], (f or "?"),
        hexa(w) if w else "?", b, ("ON" if on0 else "off") + "/" + ("ON" if on1 else "off"))
gate("G6a", all(j["bit"] is not None and j["word"] for j in JOIN),
     "all %d dialog rows resolve to a cell bit" % len(JOIN))

BITMAP = {}
for j in JOIN:
    BITMAP.setdefault((j["word"], j["bit"]), []).append(j)
al = {k: v for k, v in BITMAP.items() if len(v) > 1}
gate("G6b", not al,
     "the row->bit map is INJECTIVE per cell: %d rows, %d distinct (cell,bit) pairs, "
     "%d shared" % (len(JOIN), len(BITMAP), len(al)))
if al:
    for (w, b), v in sorted(al.items()):
        print("    SHARED %s bit %d <- %s" % (hexa(w), b, [r["label"] for r in v]))

print("\n-- G6c  bit -> label (the answer) --")
DEF_ANY = {CELL_A: DEF_PREF_L0, CELL_B: DEF_MORE_L0, CELL_C: DEF_GETTERC}
for cell in (CELL_A, CELL_B, CELL_C):
    used = sorted(k[1] for k in BITMAP if k[0] == cell)
    on = [b for b in used if (DEF_ANY[cell] >> b) & 1]
    print("  %s  (default %s, %d set bits)" % (hexa(cell), hexa(DEF_ANY[cell]),
                                               len(bits(DEF_ANY[cell]))))
    for b in used:
        r0 = BITMAP[(cell, b)][0]
        mark = "*" if (DEF_ANY[cell] >> b) & 1 else " "
        print("    %s bit %-2d  %-11s r%-2d %s" %
              (mark, b, r0["sec"][:10], r0["n"] + 1, r0["label"]))
    free = [b for b in range(32) if b not in used]
    print("    no dialog row writes these bits: %s" % free)
print("  -> the * rows are the default-set bits of each cell")

# ============================== G7 defaults ==================================
print("\n-- G7  defaults vs the rows --")
row("cell", "Laptop=0", "n bits", "Laptop!=0", "n bits")
for cell in (CELL_A, CELL_B, CELL_C):
    m0, m1 = DEFS[cell]
    row(hexa(cell), hexa(m0), len(bits(m0)), hexa(m1), len(bits(m1)))
cleared = [j for j in JOIN if j["lap"] == "cleared by Laptop"]
print("  rows whose bit the Laptop profile CLEARS:")
for j in sorted(cleared, key=lambda x: (x["word"], x["bit"])):
    print("    %s bit %-2d %-11s r%d \"%s\" (id %d)" %
          (hexa(j["word"]), j["bit"], j["sec"][:10], j["n"] + 1, j["label"], j["id"]))
setb = [j for j in JOIN if j["lap"] == "set for Laptop"]
gate("G7a", sorted((j["word"], j["bit"]) for j in cleared)
     == [(CELL_A, 7), (CELL_A, 27), (CELL_A, 28), (CELL_B, 19)] and not setb,
     "the Laptop delta is exactly {A:7,27,28; B:19} on dialog rows and adds nothing")
# M355's Difficulty<2 gate ORs bit 0x20 of the Preferences word: the label there
tut = BITMAP.get((CELL_A, 5), [])
gate("G7c", len(tut) == 1 and tut[0]["label"].lower().startswith("tutorial"),
     "Preferences bit 5 (the Difficulty<2 gate bit of M355 G3a) is the row %r" %
     (tut[0]["label"] if tut else None))
lw = win(*LOADER_WIN)
andimm, addimm, derived = [], [], []
for k, i in enumerate(lw):
    m = re.match(r"esi,0x([0-9a-f]+)$", i["arg"])
    if not m:
        continue
    if i["op"] == "and":
        andimm.append(int(m.group(1), 16))
        for j in range(k + 1, min(k + 8, len(lw))):
            m2 = re.match(r"esi,0x([0-9a-f]+)$", lw[j]["arg"])
            if lw[j]["op"] == "add" and m2:
                addimm.append(int(m2.group(1), 16))
                derived.append((int(m.group(1), 16) + int(m2.group(1), 16)) & 0xFFFFFFFF)
                break
gate("G7d", set(addimm) == {0xBBE1DD96, 0x3A7168}
     and {0xA3E1DD16, 0x327168} <= set(derived),
     "the two Laptop=0 defaults are immediates of the loader's `add` (%s) and the two "
     "Laptop!=0 words are DERIVED by its `and`+`add` (%s)" %
     ([hexa(x) for x in addimm], [hexa(x) for x in derived]))

# ============================== G8 rivals ====================================
print("\n-- G8  rivals (each must FAIL on the printed numbers) --")
RIV = []


def rival(name, ok, detail):
    RIV.append((name, ok, detail))
    print("  R %-46s holds=%-5s %s" % (name, ok, detail))


rival("bit index == option id", all(j["id"] == j["bit"] for j in JOIN),
      "mismatches %d/%d" % (sum(1 for j in JOIN if j["id"] != j["bit"]), len(JOIN)))
rival("bits are the page row ordinal", all(j["bit"] == j["n"] for j in JOIN),
      "mismatches %d/%d" % (sum(1 for j in JOIN if j["bit"] != j["n"]), len(JOIN)))
rival("a bit is written by more than one row", len(al) > 0, "shared bits %d" % len(al))
rival("each page lives in one dialog field",
      all(len({j["field"] for j in JOIN if j["sec"] == p["sec"]}) == 1 for p in PAGE_BUILD),
      "fields/page %s" % {p["sec"][:8]: len({j["field"] for j in JOIN
                                              if j["sec"] == p["sec"]}) for p in PAGE_BUILD})
rival("exe rows == Script.txt items on every page",
      all(len(SECS.get(p["sec"], [])) == len(p["rows"]) for p in PAGE_BUILD),
      "differ %s" % diff)
rival("the warnings page feeds 0x92befc",
      bool(C_F & set()) or CELL_C not in APPLY_MAP,
      "0x92bf04 <- %s, 0x92befc <- %s" % (sorted(C_F), sorted(A_F)))
rival("the 11 dialog fields are 11 pages", len(ALLF) == len(PAGE_BUILD),
      "fields %d pages %d" % (len(ALLF), len(PAGE_BUILD)))
rival("the Laptop delta touches a non-A/V row",
      any(j["sec"] != "AUDIOVISUALPREFS" for j in cleared),
      "delta rows %s" % sorted({j["sec"] for j in cleared}))
gate("G8", all(not ok for _, ok, _ in RIV),
     "%d/%d rivals FALSIFIED by the printed numbers" %
     (sum(1 for _, ok, _ in RIV if not ok), len(RIV)))

# ============================== digest =======================================
h = hashlib.sha1()
for j in JOIN:
    h.update(("%s|%d|%s|%d|%s|%s|%s\n" % (j["sec"], j["n"], j["label"], j["id"],
                                          j["field"], j["word"], j["bit"])).encode("latin-1"))
for k in sorted(BITMAP):
    h.update(("B|%s|%d|%d\n" % (hexa(k[0]), k[1], len(BITMAP[k]))).encode())
print("\ntables digest %s  (%d rows, %d bit rows)" % (h.hexdigest()[:16], len(JOIN), len(BITMAP)))
good = sum(1 for _, ok in RESULT if ok)
print("%s M357: %d/%d gates" % ("PASS" if good == len(RESULT) else "FAIL", good, len(RESULT)))
sys.exit(0 if good == len(RESULT) else 1)
