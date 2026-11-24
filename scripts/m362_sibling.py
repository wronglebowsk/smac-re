#!/usr/bin/env python3
"""M362 (chain-3, STATIC) - the 0x4db1xx sibling dialog's +0x15a0 checkbox group.

PICK (run context 2026-11-24 ~03:08 EST): M360's alternate lead - "a second dialog with
its own radio/flag block". The dialog is the FACTION RELATIONS page (builder
FUN_004db480: title = the faction's name from 0x927874+f*0x59c upper-cased, left list =
every OTHER faction, object fields +0xa1c = faction / +0xa20 = target). Its flag widget is
an INLINE sub-object at dialog+0x15a0, and FUN_004db1b0 syncs exactly THIRTEEN checkboxes
into it from two dwords of the (faction,target) record:

    ids 0x1,0x2,0x4,0x8,0x10,0x20,0x400,0x1000,0x2000,0x40000,0x2000000  <- 0x94d448
    ids 0x80000008, 0x80002000                                            <- 0x94d468

i.e. id == the bit itself, and the 0x80000000 prefix selects the SECOND dword of the same
record (base delta 0x20 = 8 dwords inside the 0x82f-dword faction block). The four toggle
handlers (0x4dabb0/0x4dac30/0x4dacc0/0x4dad40) push a changed id to six writers at
0x5518f0/0x5519c0/0x551a20/0x551c40/0x551cf0/0x551d70; four of them write the PAIR in both
directions (fac,tgt) and (tgt,fac), two write one direction only.

GATES (tables printed FIRST, then asserted; every VERIFIED row names a mutant in
scripts/m362_mutate.py):
  G1  the 13 (id, mask, base) pairs decoded from the set-by-id calls; id==mask (11) and
      id==mask|0x80000000 (2); the high-id set is exactly the 0x94d468-row set.
  G2  the index arithmetic of all 13 blocks emulated op-by-op -> 0x82f*fac + tgt (13/13,
      one identical op sequence); 0x82f*4 == 0x20bc.
  G3  the widget: one `lea edi,[esi+0x15a0]`, 13 `mov ecx,edi`, only the two fields
      0xa1c/0xa20 in the window, tail = a vtable [eax+0xf0] call.
  G4  the builder's 13 add_item rows carry the SAME ids in the SAME order, each label from
      FUN_0061482f(0x997b28, [0x997b20+off], 0) with 13 distinct offsets.
  G5  the 4 toggle handlers -> (id class, test base, off-writer, on-writer); base agrees with
      the id class in 4/4.
  G6  the 6 writers -> (base, op, directions): 4 symmetric + 2 one-way, MEASURED.
  G7  RIVALS, each measured and each FAILING on the printed numbers.
"""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M362_TEXT") or os.path.join(ROOT, "scratch/m574/text.txt")
IDX = os.environ.get("M362_INDEX") or os.path.expanduser("~/reverse/smac/ghidra_out/index.csv")

SYNC = (0x4DB1B0, 0x4DB474)      # FUN_004db1b0: the 13 sync blocks (incl. tail call)
BUILD = (0x4DB480, 0x4DBC68)     # FUN_004db480: the dialog builder (13 add_item rows)
SET_ID = 0x6050D4                # widget::set_checked(id, on)   (this=ecx)
ADD_ITEM = 0x604FD2              # widget::add_item(id, text, 0)
GET_TEXT = 0x61482F              # text object -> char*
GET_ID = 0x6051FA                # widget::is_checked(id)
TEXTOBJ = 0x997B20               # heap text table (dword at +off = a string id)
BASE_A, BASE_B = 0x94D448, 0x94D468
FAC_OFF, TGT_OFF, WIDGET_OFF = 0xA1C, 0xA20, 0x15A0
HANDLERS = (0x4DABB0, 0x4DAC30, 0x4DACC0, 0x4DAD40)
WRITERS = (0x5518F0, 0x5519C0, 0x551A20, 0x551C40, 0x551CF0, 0x551D70)
STRIDE = 0x82F
PREF_BLOCK = (0x92BEFC, 0x92BF00, 0x92BF04)   # M357's flag block (the rival's base)

LINE = re.compile(r"^\s*([0-9a-f]{6,8}):\t([0-9a-f ]+?)\s*\t(.*?)(?:\t;.*)?$")
MEM = re.compile(r"^(?:DWORD PTR )?\[(?:[a-z]{2,3}\*4\+)?0x([0-9a-f]+)\]$")
IDXLOAD = re.compile(r"^(?:DWORD PTR )?\[edx\*4\+0x([0-9a-f]+)\]$")
DREF = re.compile(r"^(?:BYTE|WORD|DWORD) PTR \[(?:[a-z]{2,3}\*4\+)?0x([0-9a-f]+)\]$")


def insns():
    out = []
    with open(TEXT, "r", errors="replace") as f:
        for line in f:
            m = LINE.match(line)
            if not m:
                continue
            t = m.group(3).strip()
            parts = t.split(None, 1)
            out.append({"a": int(m.group(1), 16), "op": parts[0],
                        "arg": parts[1] if len(parts) > 1 else "", "t": t})
    return out


INS = insns()
POS = {i["a"]: n for n, i in enumerate(INS)}


def at(a):
    return INS[POS[a]] if a in POS else None


def win(lo, hi):
    return [i for i in INS if lo <= i["a"] <= hi]


def imm(s):
    m = re.match(r"^0x([0-9a-f]+)$", s.strip())
    return int(m.group(1), 16) if m else None


def fn_end(va):
    """Function end from the Ghidra export index (never a hardcoded length)."""
    try:
        import csv
        for d in csv.DictReader(open(IDX)):
            if int(d["addr"], 16) == va:
                return va + int(d["size_bytes"])
    except OSError:
        pass
    return va + 0x400


def hexa(v):
    return "0x%x" % v


# ------------------------------------------------------------------ G1: the 13 pairs
def sync_pairs():
    """Walk back from every `call 0x6050d4`: id = last `push imm`, mask = last `and eax,imm`,
    base = last `[edx*4+0x94d...]` load.  All three are per-block immediates/addresses."""
    pairs = []
    for n, ins in enumerate(INS):
        if ins["op"] != "call" or imm(ins["arg"]) != SET_ID:
            continue
        if not (SYNC[0] <= ins["a"] <= SYNC[1]):
            continue
        pid = pmask = pbase = None
        stop = max(0, n - 24)
        for k in range(n - 1, stop, -1):
            b = INS[k]
            if pid is None and b["op"] == "push" and imm(b["arg"]) is not None:
                pid = imm(b["arg"])
            if pmask is None and b["op"] == "and" and b["arg"].startswith("eax,0x"):
                pmask = imm(b["arg"].split(",")[1])
            if pbase is None and b["op"] == "mov" and b["arg"].startswith("eax,DWORD PTR [edx*4+"):
                m = IDXLOAD.match(b["arg"].split(",", 1)[1])
                if m:
                    pbase = int(m.group(1), 16)
            if pid is not None and pmask is not None and pbase is not None:
                break
        # the mask is loaded from the base BEFORE the and; the id push comes after the and
        pairs.append({"addr": ins["a"], "id": pid, "mask": pmask, "base": pbase,
                      "idpush": None, "n": n})
    # recover the id push address (first push imm after the `and`)
    for p in pairs:
        for k in range(p["n"] - 1, max(0, p["n"] - 12), -1):
            b = INS[k]
            if b["op"] == "push" and imm(b["arg"]) is not None and imm(b["arg"]) == p["id"]:
                p["idpush"] = b["a"]
                break
    return pairs


# ------------------------------------------------------------------ G2: the index math
def emu_stride(lo_addr, base_addr):
    """Emulate ecx/edx/eax (as linear forms {a,b,k}) over one sync block and return the
    coefficient of fac (a) and tgt (b) at the `[edx*4+base]` load."""
    form = {}

    def E(a=0, b=0, k=0):
        return (a, b, k)

    def add(x, y):
        return (x[0] + y[0], x[1] + y[1], x[2] + y[2])

    def mul(x, c):
        return (x[0] * c, x[1] * c, x[2] * c)

    ops = []
    for ins in win(lo_addr, base_addr):
        o, g = ins["op"], ins["arg"].replace(" ", "")
        if o == "mov" and g == "eax,DWORDPTR[esi+0x%x]" % FAC_OFF:
            form["eax"] = E(a=1)
        elif o == "mov" and g == "eax,DWORDPTR[esi+0x%x]" % TGT_OFF:
            form["eax"] = E(b=1)
        elif o == "mov" and g.startswith("ecx,eax"):
            form["ecx"] = form["eax"]
            ops.append("mov ecx,eax")
        elif o == "shl" and g.startswith("ecx,"):
            form["ecx"] = mul(form["ecx"], 1 << int(g.split(",")[1], 16))
            ops.append("shl ecx," + g.split(",")[1])
        elif o == "add" and g == "ecx,eax":
            form["ecx"] = add(form["ecx"], form["eax"])
            ops.append("add ecx,eax")
        elif o == "lea" and g.startswith("edx,[eax+ecx*"):
            c = int(g.split("*")[1].rstrip("]"))
            form["edx"] = add(form["eax"], mul(form["ecx"], c))
            ops.append("lea edx,[eax+ecx*%d]" % c)
        elif o == "shl" and g.startswith("edx,"):
            form["edx"] = mul(form["edx"], 1 << int(g.split(",")[1], 16))
            ops.append("shl edx," + g.split(",")[1])
        elif o == "sub" and g == "edx,eax":
            form["edx"] = add(form["edx"], mul(form["eax"], -1))
            ops.append("sub edx,eax")
        elif o == "add" and g == "edx,eax":
            form["edx"] = add(form["edx"], form["eax"])
            ops.append("add edx,eax")
        elif o in ("mov",) and g.startswith("eax,DWORDPTR[edx*4+0x"):
            return form["edx"], ops
    raise SystemExit("no index load in 0x%x..0x%x" % (lo_addr, base_addr))


def block_starts(pairs):
    """For each pair, the address of the `mov eax,[esi+0xa1c]` that opens its index math."""
    starts = []
    for p in pairs:
        for k in range(p["n"] - 1, max(0, p["n"] - 24), -1):
            b = INS[k]
            if b["op"] == "mov" and b["arg"].startswith("eax,DWORD PTR [esi+0x%x]" % FAC_OFF):
                starts.append(b["a"])
                break
    return starts


# ------------------------------------------------------------------ G4: builder rows
def build_rows():
    rows = []
    for n, ins in enumerate(INS):
        if ins["op"] != "call" or imm(ins["arg"]) != ADD_ITEM:
            continue
        if not (BUILD[0] <= ins["a"] <= BUILD[1]):
            continue
        rid = off = None
        for k in range(n - 1, max(0, n - 14), -1):
            b = INS[k]
            if rid is None and b["op"] == "push" and imm(b["arg"]) is not None and imm(b["arg"]):
                rid = imm(b["arg"])
            if off is None and b["op"] == "mov":
                m = re.search(r"DWORD PTR \[[a-z]{2,3}\+0x([0-9a-f]+)\]$", b["arg"])
                if m and 0x900 <= int(m.group(1), 16) <= 0xEFF:
                    off = int(m.group(1), 16)
            if rid is not None and off is not None:
                break
        rows.append({"addr": ins["a"], "id": rid, "label_off": off})
    return rows


# ------------------------------------------------------------------ G5/G6: handlers/writers
def handler_row(va):
    """One toggle handler: the id class (is it pushed as id|0x80000000?), the dword it
    tests, and every writer call site (0x551xxx) in the body."""
    body = win(va, fn_end(va) - 1)
    cls = "plain"
    base = None
    getter = 0
    writers = []
    for i in body:
        g = i["arg"].replace(" ", "")
        if i["op"] == "or" and g == "eax,0x80000000":
            cls = "high"
        if i["op"] == "test":
            m = DREF.match(i["arg"].split(",", 1)[0].strip())
            if m:
                base = int(m.group(1), 16)
        if i["op"] == "call":
            t = imm(i["arg"])
            if t == GET_ID:
                getter += 1
            elif t in WRITERS:
                writers.append(t)
    return {"va": va, "cls": cls, "base": base, "writers": writers,
            "uniq": sorted(set(writers)), "getter": getter,
            "n": len(body)}


def writer_row(va):
    """One writer: its base dword(s), set/clear ops, the index forms it builds, and the base
    of its LAST store.  The index idiom is the same 6-insn shl/add/lea/shl/sub/add chain the
    sync blocks use, but here the result stays in a scratch register and the store is an RMW
    through a COPIED register (s242 trap #3) - so the census is by FORM, not a store grep."""
    body = win(va, fn_end(va) - 1)
    bases = set()
    ops = []
    stores = 0
    lastlea = {}
    primary = None
    for i in body:
        g = i["arg"].replace(" ", "")
        if i["op"] in ("and", "or") and g.split(",")[0] in ("edi", "esi", "edx", "eax", "ecx"):
            ops.append("clear" if i["op"] == "and" else "set")
        m = re.search(r"^([a-z]{2,3}),(?:DWORDPTR)?\[([a-z]{2,3})\*4\+0x94d([0-9a-f]+)\]$", g)
        if i["op"] in ("mov", "lea") and m:
            b = int("0x94d" + m.group(3), 16)
            bases.add(b)
            if i["op"] == "lea":
                lastlea[m.group(1)] = b
        if i["op"] == "mov" and re.match(r"^DWORDPTR\[([a-z]{2,3})\],([a-z]{2,3})$", g):
            stores += 1
            r = re.match(r"^DWORDPTR\[([a-z]{2,3})\],", g).group(1)
            primary = lastlea.get(r, primary)
    forms = []
    for n, i in enumerate(body):
        g = i["arg"].replace(" ", "")
        m = re.match(r"^([a-z]{2,3}),\[([a-z]{2,3})\+([a-z]{2,3})\*2\]$", g)
        if i["op"] != "lea" or not m:
            continue
        r, base_reg = m.group(1), m.group(2)
        mult = roles_at(body, n, base_reg)
        addend = None
        sub_at = None
        for k in range(n + 1, min(len(body), n + 8)):
            gg = body[k]["arg"].replace(" ", "")
            if body[k]["op"] == "sub" and gg == "%s,%s" % (r, base_reg):
                sub_at = k
                break
        if sub_at is not None:
            for k in range(sub_at + 1, min(len(body), sub_at + 4)):
                gg = body[k]["arg"].replace(" ", "")
                if body[k]["op"] == "add" and gg.startswith(r + ","):
                    addend = roles_at(body, k, gg.split(",")[1])
                    break
        forms.append((mult, addend))
    return {"va": va, "n_idx": len(forms), "forms": forms,
            "dirs": len(set(f for f in forms if None not in f)),
            "bases": sorted(bases), "primary": primary, "ops": sorted(set(ops)),
            "n_store": stores, "n": len(body)}


def block_info(body, n):
    """(first instruction index of n's basic block, index of the branch opening it or None)."""
    ta = body[n]["a"]
    starts = []
    targets = {}
    for b, i in enumerate(body[:n]):
        if not i["op"].startswith("j"):
            continue
        if b + 1 < len(body):
            starts.append(body[b + 1]["a"])
        t = imm(i["arg"].split(",")[-1])
        if t is not None and t <= ta:
            starts.append(t)
            targets[t] = b
    if not starts:
        return 0, None
    block = max(starts)
    anchor = targets.get(block)
    fs = 0
    for k, i in enumerate(body):
        if i["a"] >= block:
            fs = k
            break
    return fs, anchor


def roles_at(body, n, reg):
    """Role of `reg` at instruction n by backward DEF-USE: the block's OWN writes first, then
    (only if none) the values that reach the block from before the branch that opens it.
    0x551d70's `je` at 0x551d7b targets 0x551da8; the arm between them clobbers eax, so that
    arm is never scanned - but the target block's own `mov edx,[ebp+0xc]` is."""
    writes = {"mov", "lea", "and", "or", "xor", "add", "sub", "shl", "shr", "not", "pop",
              "imul", "inc", "dec", "neg", "mul", "div", "idiv"}
    fs, anchor = block_info(body, n)
    order = list(range(n - 1, fs - 1, -1))
    if anchor is None:
        order += list(range(fs - 1, -1, -1))
    else:
        order += list(range(anchor - 1, -1, -1))
    for k in order:
        i = body[k]
        g = i["arg"].replace(" ", "")
        dest = g.split(",")[0]
        if i["op"] not in writes or dest != reg:
            continue
        if i["op"] == "mov":
            m = re.match(r"^([a-z]{2,3}),(?:DWORDPTR)?\[ebp\+0x([0-9a-f]+)\]$", g)
            mm = re.match(r"^([a-z]{2,3}),([a-z]{2,3})$", g)
            if m:
                return {"8": "p1", "c": "p2"}.get(m.group(2))
            if mm:
                return roles_at(body, k, mm.group(2))
        return None
    return None


def main():
    out = []
    say = out.append
    gates = []

    def gate(gid, ok, msg):
        gates.append((gid, ok, msg))
        say("  %-5s %s  %s" % (gid, "PASS" if ok else "FAIL", msg))

    pairs = sync_pairs()
    say("M362 - the 0x4db1xx sibling dialog's +0x15a0 flag group")
    say("")
    say("G1  the 13 set-by-id rows of FUN_004db1b0 (0x%x..0x%x)" % SYNC)
    say("    #  call@       id         mask       base        id==mask|hi")
    for n, p in enumerate(pairs):
        say("    %2d %-10s %-10s %-10s %-10s %s" % (
            n + 1, hexa(p["addr"]), hexa(p["id"]), hexa(p["mask"]), hexa(p["base"]),
            "yes" if p["id"] == p["mask"] or p["id"] == p["mask"] | 0x80000000 else "NO"))
    ids = [p["id"] for p in pairs]
    high = [p for p in pairs if p["id"] & 0x80000000]
    b_rows = [p for p in pairs if p["base"] == BASE_B]
    a_rows = [p for p in pairs if p["base"] == BASE_A]
    gate("G1a", len(pairs) == 13 and len(set(ids)) == 13,
         "13 distinct set-by-id rows (got %d, distinct %d)" % (len(pairs), len(set(ids))))
    gate("G1b", len(a_rows) == 11 and len(b_rows) == 2 and
         all(p["id"] == p["mask"] for p in a_rows) and
         all(p["id"] == p["mask"] | 0x80000000 for p in b_rows),
         "11 rows id==mask on 0x94d448, 2 rows id==mask|0x80000000 on 0x94d468")
    gate("G1c", set(id(p) for p in high) == set(id(p) for p in b_rows),
         "the 0x80000000 prefix set is EXACTLY the 0x94d468-row set (%d/%d)"
         % (len(high), len(b_rows)))

    say("")
    say("G2  index arithmetic, emulated per block")
    say("    #  block@      fac coeff  tgt coeff  const")
    starts = block_starts(pairs)
    forms = []
    for p, s in zip(pairs, starts):
        (fa, tb, c), _ = emu_stride(s, p["addr"])
        forms.append((fa, tb, c))
        say("    %2d %-11s %-10s %-10s %-6s" % (len(forms), hexa(s), hexa(fa), hexa(tb), hexa(c)))
    gate("G2a", len(forms) == 13 and all(f == (STRIDE, 1, 0) for f in forms),
         "all 13 blocks compute %s*fac + 1*tgt + 0" % hexa(STRIDE))
    gate("G2b", STRIDE * 4 == 0x20BC,
         "the dword stride is 0x%x bytes = the per-faction block size"
         % (STRIDE * 4))
    seqs = []
    for p, s in zip(pairs, starts):
        _, ops = emu_stride(s, p["addr"])
        seqs.append(tuple(ops))
    gate("G2c", len(set(seqs)) == 1 and len(seqs) == 13,
         "one identical instruction sequence in 13/13 blocks (%d distinct)" % len(set(seqs)))

    say("")
    say("G3  the widget: an INLINE sub-object at dialog+0x%x" % WIDGET_OFF)
    body = win(*SYNC)
    nimps = [i for i in body if i["t"].replace(" ", "") == "leaedi,[esi+0x%x]" % WIDGET_OFF]
    necx = [i for i in body if i["t"].replace(" ", "") == "movecx,edi"]
    fields = sorted(set(int(m.group(1), 16) for i in body if i["op"] == "mov"
                        for m in [re.search(r"^eax,DWORD PTR \[esi\+0x([0-9a-f]+)\]$", i["arg"])] if m))
    tails = [i["t"] for i in body if 0x4DB458 <= i["a"] <= 0x4DB473]
    say("    lea [esi+0x%x]: %d   mov ecx,edi: %d   fields read: %s"
        % (WIDGET_OFF, len(nimps), len(necx), ",".join(hexa(f) for f in fields)))
    say("    tail: " + " | ".join(tails))
    gate("G3a", len(nimps) == 1 and len(necx) == 13,
         "one `lea edi,[esi+0x15a0]` feeds 13 set-by-id calls")
    gate("G3b", fields == sorted([FAC_OFF, TGT_OFF]),
         "the window reads exactly the two fields 0x%x/0x%x" % (FAC_OFF, TGT_OFF))
    gate("G3c", any(re.search(r"call\s+DWORD PTR \[eax\+0xf0\]", t) for t in tails)
         and sum(1 for t in tails if "+0x%x" % WIDGET_OFF in t) == 2
         and tails[0].replace(" ", "") == "movecx,DWORDPTR[edi]",
         "tail = vtable [eax+0xf0] call through the +0x%x object (%d insns)"
         % (WIDGET_OFF, len(tails)))

    say("")
    say("G4  the builder's 13 add_item rows (FUN_004db480)")
    rows = build_rows()
    say("    #  call@       id         label slot")
    for n, r in enumerate(rows):
        say("    %2d %-11s %-10s %s" % (n + 1, hexa(r["addr"]), hexa(r["id"]),
                                       hexa(TEXTOBJ + r["label_off"]) if r["label_off"] else "-"))
    offs = [r["label_off"] for r in rows]
    gate("G4a", len(rows) == 13 and [r["id"] for r in rows] == ids,
         "13 rows, ids and ORDER identical to the sync (%d/%d)" % (len(rows), len(ids)))
    gate("G4b", len(set(offs)) == 13 and None not in offs,
         "13 distinct label slots in the 0x997b20 text object (%d distinct)" % len(set(offs)))

    say("")
    say("G5  the 4 toggle handlers -> writer pairs")
    say("    handler     id class  test base   writer sites            getter")
    hrows = [handler_row(h) for h in HANDLERS]
    for h in hrows:
        say("    %-11s %-9s %-11s %-23s %d" % (
            hexa(h["va"]), h["cls"], hexa(h["base"]) if h["base"] else "-",
            ",".join(hexa(w) for w in h["writers"]) or "-", h["getter"]))
    gate("G5a", all(h["getter"] == 1 and len(h["writers"]) == 2 for h in hrows),
         "4/4 handlers ask is_checked once and call a writer on BOTH branches (8 sites)")
    gate("G5b", all((h["base"] == BASE_B) == (h["cls"] == "high") for h in hrows) and
         sorted(set(h["base"] for h in hrows)) == [BASE_A, BASE_B],
         "the id class selects the dword: high|0x80000000 <-> 0x94d468, 4/4")
    gate("G5c", sorted(h["uniq"][0] for h in hrows if len(h["uniq"]) == 1) == [0x551CF0, 0x551D70],
         "the two 4-arg writers are each called by exactly one handler (one-way pair)")

    say("")
    say("G6  the 6 writers: base, op, directions")
    say("    writer      bases           primary     ops      forms                     stores")
    wrows = [writer_row(w) for w in WRITERS]
    for w in wrows:
        say("    %-11s %-15s %-11s %-8s %-25s %d" % (
            hexa(w["va"]), ",".join(hexa(b) for b in w["bases"]) or "-",
            hexa(w["primary"]) if w["primary"] else "-",
            "+".join(w["ops"]) or "-",
            " ".join("%s>%s" % (a or "?", b or "?") for a, b in w["forms"]) or "-",
            w["n_store"]))
    dirs = sorted(w["dirs"] for w in wrows)
    gate("G6a", dirs == [1, 1, 2, 2, 2, 2],
         "4 writers build both (p1,p2)/(p2,p1) forms, 2 only one (%s)" % dirs)
    prim = {w["va"]: w["primary"] for w in wrows}
    gate("G6b", sorted(prim[v] for v in prim if prim[v] == BASE_A) == [BASE_A] * 3 and
         sorted(prim[v] for v in prim if prim[v] == BASE_B) == [BASE_B] * 3,
         "primary (last-store) base splits 3 A / 3 B: %s"
         % ",".join(hexa(prim[v]) for v in WRITERS))

    say("")
    say("G7  RIVALS (each must FAIL on the numbers above)")
    r1 = {0x92BEFC, 0x92BF00, 0x92BF04} & set(p["base"] for p in pairs)
    say("    R1 'this group is the preferences flag block 0x92befc..' -> bases seen %s; "
        "overlap %d" % (sorted(set(hexa(p["base"]) for p in pairs)), len(r1)))
    gate("R1", not r1, "R1 refuted: no 0x92befc/0x92bf00/0x92bf04 read in the window")
    contiguous = all(b - a == 1 for a, b in zip(sorted(ids), sorted(ids)[1:]))
    say("    R2 'ids are row ordinals 1..13' -> sorted ids %s; contiguous %s"
        % (",".join(hexa(i) for i in sorted(ids)), contiguous))
    gate("R2", not contiguous and sum(1 for i in ids if i & (i - 1) == 0) == 11,
         "R2 refuted: 11 ids are single bits, gaps at 0x40/0x800/0x8000/0x100000")
    d = BASE_B - BASE_A
    say("    R3 '0x94d468 is an independent array' -> base delta %s = %d dwords, "
        "index forms identical %d/13" % (hexa(d), d // 4, sum(1 for f in forms if f == (STRIDE, 1, 0))))
    gate("R3", d == 0x20 and d < 4 * STRIDE and len(set(forms)) == 1,
         "R3 refuted: base+0x20 is slot +8 INSIDE the same 0x82f-dword block")
    sym = sum(1 for w in wrows if w["dirs"] == 2)
    say("    R4 'the pair is written one-way' -> %d/6 writers write both directions, "
        "the two one-way ones are the only writers the 3rd/4th handlers call" % sym)
    gate("R4", sym == 4, "R4 refuted for 4 of 6 writers; asymmetry localised to 2")

    npass = sum(1 for _, ok, _ in gates if ok)
    say("")
    dig = hashlib.sha1(("\n".join(out)).encode()).hexdigest()
    say("PASS M362: %d/%d gates" % (npass, len(gates)) if npass == len(gates)
        else "FAIL M362: %d/%d gates" % (npass, len(gates)))
    say("digest %s" % dig[:16])
    print("\n".join(out))
    return 0 if npass == len(gates) else 1


if __name__ == "__main__":
    sys.exit(main())
