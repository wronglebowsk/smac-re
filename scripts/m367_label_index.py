#!/usr/bin/env python3
"""M367 - the 13 faction-relations LABEL SLOTS: where they are indexed, which bit each anchors.

PICK (run context 2026-11-24 ~04:20 EST): the last OPEN of `## M362` / `## M365` - the 13 label
strings behind `FUN_0061482f(0x997b28,[0x997b20+off])` in the builder `FUN_004db480`. STATIC only.

WHAT THE BYTES SAY (one line): the labels are NOT in the image - `0x997b20` is a heap array of
`count` line-pointers built at startup from `labels.txt` (count = atoi of the line after the
`#LABELS` header), and each dialog row hard-codes ONE element index (a byte offset / 4 into that
array); the element index maps to labels.txt line `index+10`, so every checkbox row resolves to a
fixed text, and the bit it toggles is the id it passes to `set_checked` (0x6050d4).

GATES (tables printed FIRST, then asserted; every VERIFIED row names a mutant in
scripts/m367_mutate.py):
  G0  the loader: exactly 2 stores to 0x997b20 (one zero, one alloc of count*4), one element
      store form [edx+ecx*4] fed by the 0x5ea457 line reader -> the array is a LINE-POINTER table.
  G1  labels.txt contract: header at line 8, count line 9 = 1089, and exactly 1089 label lines
      follow before the trailing sentinel -> element0 = 'Mission Year', element i = line 10+i.
  G2  FUN_004db480's rows: 13 add_item(text,id,0) rows, ids identical AND in the same order as the
      sync's 13 set_checked(id,mask) rows; every label operand is one dword of the 0x997b20 array.
  G3  the clamp 0x61482f is a VALIDATOR (no arithmetic on the argument) -> the element index is a
      build-time constant, not a computed position; the 13 elements form 3 maximal runs.
  G4  independent anchor: 0x4120c4 tests bit 0x1 of the same 0x82f-indexed record and selects
      element 0xa14 ('Pact') when set, 0xa10 ('Treaty') when clear -> a set bit names its label.
  G5  per-id base from the sync blocks: 11 plain (0x94d448) / 2 high (0x94d468), mask==id&0x7fffffff.
  G6  RIVALS, each measured and each FAILING on the printed numbers.

    python3 -u scripts/m367_label_index.py
"""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M367_TEXT") or os.path.join(ROOT, "scratch/m574/text.txt")
LABELS = os.environ.get("M367_LABELS") or os.path.join(ROOT, "programs/labels.txt")

TEXTOBJ = 0x997B20          # heap array of char* to one labels.txt line each
ARENA = 0x997B28            # string arena descriptor (base@+4, size@+0xc)
BUILDER = (0x4DB480, 0x4DB480 + 2024)      # FUN_004db480: the dialog builder
SYNC = (0x4DB1B0, 0x4DB474)                # FUN_004db1b0: the 13 set_checked blocks
CLAMP = 0x61482F
LOADER = 0x614681
ADD_ITEM = 0x604FD2
SET_CHECKED = 0x6050D4
DAM = 0x4120B0                              # the status-text function that names bit 0x1
PLAIN, HIGH = 0x94D448, 0x94D468

out = []
gates = []


def say(s=""):
    out.append(s)


def gate(gid, ok, msg):
    gates.append((gid, bool(ok)))
    say("  %-5s %s  %s" % (gid, "PASS" if ok else "FAIL", msg))


# ---------------------------------------------------------------- text cache
ADDR = re.compile(r"\s*([0-9a-f]{6,8}):\s+((?:[0-9a-f]{2} )+)\s*\t(.*)$")


def load_text(path):
    ins = []
    with open(path, "r", errors="replace") as f:
        for line in f:
            m = ADDR.match(line)
            if m:
                ins.append((int(m.group(1), 16), re.sub(r"\s+", " ", m.group(3)).strip()))
    return ins


def window(ins, lo, hi):
    return [(a, t) for a, t in ins if lo <= a <= hi]


def imm(t):
    m = re.search(r"push +(0x[0-9a-f]+)", t)
    return int(m.group(1), 16) if m else None


def parse_labels(path):
    raw = open(path, "rb").read()
    lines = [x.rstrip(b"\r") for x in raw.split(b"\n")]
    return lines


def atoi(b):
    m = re.match(rb"\s*(-?\d+)", b)
    return int(m.group(1)) if m else 0


def main():
    ins = load_text(TEXT)
    L = parse_labels(LABELS)
    say("M367 - the 13 faction-relations label slots (0x997b20 = a labels.txt line table)")

    # ---------------------------------------------------------------- G0 loader
    say("")
    say("G0  the loader: who owns 0x997b20")
    st = [(a, t) for a, t in ins if re.match(r"mov +(DWORD PTR )?ds:0x997b20,", t)]
    say("    stores to ds:0x997b20: %d" % len(st))
    for a, t in st:
        say("      %08x  %s" % (a, t))
    w = window(ins, 0x614681, 0x614717)
    alloc = [t for a, t in w if "shl eax,0x2" in t or "call 0x5be090" in t]
    count_load = [t for a, t in w if "ds:0x997b24" in t]
    elem_store = [(a, t) for a, t in w if re.search(r"mov DWORD PTR \[e?d?x?\+?e?c?x?\*4\]", t)
                  or re.search(r"mov DWORD PTR \[[a-z]{2,3}\+[a-z]{2,3}\*4\]", t)]
    say("    alloc chain: %s" % " | ".join(alloc))
    say("    count load : %s" % " | ".join(count_load[:3]))
    say("    element store: %s" % " | ".join("%08x %s" % x for x in elem_store))
    zero = [a for a, t in st if t.endswith(",0x0") or t.endswith(",0")]
    gate("G0a", len(st) == 2 and len(zero) == 1,
         "0x997b20 has exactly 2 stores (%d): the free-path zero at %08x and the alloc result"
         % (len(st), zero[0] if zero else -1))
    gate("G0b", sum(1 for t in alloc if "shl eax,0x2" in t) == 1
         and sum(1 for t in alloc if "call 0x5be090" in t) == 1,
         "the window holds one `shl eax,2` and one alloc call %s" % [t for t in alloc])
    # the DATA FLOW, by address order: count -> shl 2 -> push -> alloc -> store 0x997b20
    chain = []
    for a, t in w:
        if re.match(r"mov +eax,ds:0x997b24$", t):
            chain = [("count", a)]
        elif chain and chain[-1][0] == "count" and t == "shl eax,0x2":
            chain.append(("shl", a))
        elif chain and chain[-1][0] == "shl" and t == "push eax":
            chain.append(("push", a))
        elif chain and chain[-1][0] == "push" and t == "call 0x5be090":
            chain.append(("alloc", a))
        elif chain and chain[-1][0] == "alloc" and re.match(r"mov +ds:0x997b20,eax$", t):
            chain.append(("store", a))
            break
    say("    data flow: %s" % " -> ".join("%s@%08x" % c for c in chain))
    prolog = [a for a, t in w if t == "push ebp"]
    rets = [a for a, t in w if t.startswith("ret")]
    gate("G0d", [c[0] for c in chain] == ["count", "shl", "push", "alloc", "store"]
         and len(prolog) == 1 and rets,
         "count(0x997b24) -> shl 2 -> alloc -> stored to 0x997b20 in ONE body (1 prologue, rets): "
         "the owner is the function at 0x614681")
    # the count itself: the loader stores the return of 0x5ea484 (0x5eaa53 = atoi of the line it reads)
    srcs = []
    for i, (a, t) in enumerate(w):
        if t == "call 0x5ea484" and i + 1 < len(w) and re.match(r"mov +ds:0x997b24,eax$", w[i + 1][1]):
            srcs.append((a, w[i + 1][0]))
    gate("G0e", len(srcs) == 1 and len([1 for a, t in w if "ds:0x997b24," in t]) == 1,
         "0x997b24 has ONE store, fed by the 0x5ea484 return (0x5eaa53 = atoi of the line just read)")

    es = elem_store[0][1] if elem_store else "none"
    gate("G0c", len(elem_store) == 1 and "ecx*4" in es.replace(" ", ""),
         "one element store form %s = the reader's return -> an array of LINE POINTERS"
         % (es.split("PTR ")[1].rsplit(",", 1)[0] if "PTR " in es else es))

    # ---------------------------------------------------------------- G1 file contract
    say("")
    say("G1  labels.txt is the file the loader opens (`labels` + '.txt', fopen mode 'rt' at 0x5ea673)")
    say("    line  8: %r" % L[8][:40])
    say("    line  9: %r   atoi -> %d" % (L[9][:40], atoi(L[9])))
    sent = [i for i in range(10, len(L)) if L[i].startswith(b"# ;")]
    count = atoi(L[9])
    body_end = sent[0] if sent else len(L)
    while body_end > 10 and not L[body_end - 1].strip():
        body_end -= 1
    body = body_end - 10
    say("    label lines after the count line (10..%d, trailing blanks excluded; sentinel at %s): %d"
        % (body_end - 1, sent[0] if sent else "-", body))
    say("    element 0 -> line 10 %r ; element %d -> line %d %r"
        % (L[10][:30], count - 1, 10 + count - 1, L[10 + count - 1][:30]))
    gate("G1a", L[8].strip().lower() == b"#labels",
         "the section header line 8 is %r (the loader opens section 'labels')" % L[8][:12])
    gate("G1b", count == body,
         "the declared count %d equals the %d label lines that follow it (element i = line 10+i)"
         % (count, body))
    tail = len(L) - (10 + count)
    gate("G1c", L[10].strip() == b"Mission Year" and body_end == 10 + count,
         "the array is exactly lines 10..%d; the %d lines after the %dth element are beyond the "
         "loader's only bound (count) and are never read"
         % (10 + count - 1, tail, count))

    # ---------------------------------------------------------------- G2 builder rows
    say("")
    say("G2  FUN_004db480's add_item rows (text, id, 0) and the sync's set_checked rows (id, mask)")
    # every clamp site in the window: 13 add_item rows + 3 non-row label slots
    allslots = []
    for a, t in window(ins, *BUILDER):
        if not re.match(r"call +0x61482f$", t):
            continue
        back = [x for x in window(ins, a - 40, a) if x[0] < a]
        pid = lab = None
        src = "other"
        sreg = None
        for ta, tb in reversed(back):
            if pid is None:
                m = re.search(r"mov ([a-z]{2,3}),DWORD PTR \[([a-z]{2,3})\+0x([0-9a-f]+)\]", tb)
                if m:
                    pid, lab, sreg = int(m.group(3), 16), ta, m.group(2)
                continue
            if re.match(r"mov +%s,(DWORD PTR )?ds:0x997b20" % sreg, tb):
                src = "obj"
                break
        fwd = window(ins, a + 1, a + 40)
        dst = next((tb for ta, tb in fwd if re.match(r"call +0x[0-9a-f]+$", tb)), "?")
        ids = [imm(x[1]) for x in back]
        ids = [x for x in ids if x is not None]
        if pid is not None:
            allslots.append({"clamp": a, "off": pid, "slot": lab if src == "obj" else None,
                             "src": src, "dst": dst,
                             "id": ids[-1] if ids else None,
                             "flag": ids[-2] if len(ids) > 1 else None})
    rows = [r for r in allslots if r["dst"] == "call 0x604fd2" and r["src"] == "obj"]
    others = [r for r in allslots if r not in rows]
    rows.sort(key=lambda r: r["clamp"])
    say("    #  call@      id          flag  label off  element  line  text")
    for n, r in enumerate(rows):
        el = r["off"] // 4
        say("    %2d %-10s %-11s %-5s 0x%-6x %5d %5d  %s"
            % (n + 1, hexa(r["clamp"]), hexa(r["id"]), hexa(r["flag"]), r["off"], el, 10 + el,
               L[10 + el].strip().decode("latin1") if 10 + el < len(L) else "?"))
    say("    the same window's NON-row label slots (different call target):")
    for r in others:
        el = r["off"] // 4
        say("      %08x +0x%-5x elem %4d line %4d  -> %-14s %s"
            % (r["clamp"], r["off"], el, 10 + el, r["dst"],
               L[10 + el].strip().decode("latin1") if 10 + el < len(L) else "?"))
    ids = [r["id"] for r in rows]
    gate("G2a", len(rows) == 13,
         "13 add_item rows carry a clamp'd operand loaded through ds:0x997b20 (%d of %d clamp sites)"
         % (len(rows), len(allslots)))
    gate("G2b", len({r["off"] for r in rows}) == 13 and all(r["off"] % 4 == 0 for r in rows),
         "13 distinct label offsets, every one a multiple of 4 (a dword element index)")
    gate("G2e", L[10 + 0xD88 // 4].strip() == b"Diplomacy for"
         and L[10 + 0xD8C // 4].strip() == b"Clear" and L[10 + 0xDB0 // 4].strip() == b"Atrocity",
         "the 3 statics inside the runs read %r / %r / %r - a dialog title, a button, a heading"
         % (L[10 + 0xD88 // 4].strip(), L[10 + 0xD8C // 4].strip(), L[10 + 0xDB0 // 4].strip()))
    gate("G2c", len(others) == 5 and {o["off"] for o in others} ==
         {0xD88, 0xD8C, 0xDB0, 0x378, 0x194},
         "the window's %d clamp sites split 13 rows + 5 non-row statics, excluded by their "
         "call target" % len(allslots))

    # sync rows
    srows = []
    for a, t in window(ins, *SYNC):
        if not re.match(r"call +0x6050d4$", t):
            continue
        back = window(ins, a - 40, a)
        gid = mask = base = None
        for ta, tb in reversed(back):
            if gid is None and imm(tb) is not None and tb.startswith("push 0x"):
                gid = imm(tb)
            elif gid is not None and mask is None and "and eax,0x" in tb:
                mask = int(tb.split("0x")[-1], 16)
            elif gid is not None and mask is not None and base is None:
                m = re.search(r"\[[a-z]{2,3}\*4\+0x([0-9a-f]+)\]", tb)
                if m:
                    base = int(m.group(1), 16)
                break
        if gid and mask and base:
            srows.append({"id": gid, "mask": mask, "base": base, "addr": a})
    srows.sort(key=lambda r: r["addr"])
    say("    sync rows: %d   ids in builder order: %s"
        % (len(srows), [r["id"] for r in srows] == ids))
    gate("G2d", [r["id"] for r in srows] == ids,
         "the 13 sync ids are identical AND in the same order as the 13 builder rows")

    # ---------------------------------------------------------------- G3 clamp / runs
    say("")
    say("G3  the clamp 0x61482f is a validator, so the element index is a build-time constant")
    cw = window(ins, CLAMP, CLAMP + 56)
    argops = [t for a, t in cw if "[ebp+0x8]" in t]
    classes = sorted(set(t.split()[0] for t in argops))
    arith = [t for t in argops if re.match(r"(add|sub|shl|sar|imul|and|or|lea)\b", t)]
    say("    clamp body (%d insns), reads of the argument [ebp+8]: %d" % (len(cw), len(argops)))
    say("      %s" % " | ".join(argops))
    gate("G3a", 20 <= len(cw) <= 26 and len(arith) == 0 and classes == ["cmp", "mov"]
         and sum(1 for t in argops if t.startswith("cmp")) == 1,
         "%d-insn body; the argument is read by mov/cmp only (classes %s, 1 compare, 0 arithmetic) "
         "-> a validator, not an index computation" % (len(cw), classes))
    elems = sorted(r["off"] // 4 for r in rows)
    runs = [[elems[0]]] if elems else []
    for e in elems[1:]:
        if e == runs[-1][-1] + 1:
            runs[-1].append(e)
        else:
            runs.append([e])
    say("    element runs: %s" % " ".join("%d..%d" % (r[0], r[-1]) if len(r) > 1 else str(r[0])
                                         for r in runs))
    say("    the 10-run 0xd88..0xdac, consumers: %s"
        % sorted("%08x->%d(%s)" % (r["clamp"], r["off"] // 4,
                                   "row" if r["dst"] == "call 0x604fd2" else "other")
                 for r in allslots if 0xD88 <= r["off"] <= 0xDAC))
    run10 = {0xD88 + 4 * k for k in range(10)}
    gate("G3b", [len(r) for r in runs] == [4, 8, 1],
         "the 13 elements form exactly 3 maximal runs of sizes %s" % [len(r) for r in runs])
    gate("G3c", {r["off"] for r in allslots if 0xD88 <= r["off"] <= 0xDAC} == run10
         and len([r for r in allslots if 0xD88 <= r["off"] <= 0xDAC]) == 10,
         "the 10-element run 0xd88..0xdac is consumed exactly once each (1 title + 1 button + 8 rows)")

    # ---------------------------------------------------------------- G4 the dam
    say("")
    say("G4  independent anchor: the status-text function at 0x4120c4 names bit 0x1")
    dw = window(ins, 0x4120A0, 0x412100)
    for a, t in dw:
        if "0x94d448" in t or "0x94d468" in t or re.search(r"\+0xa1[048]", t) or "0x61482f" in t:
            say("      %08x  %s" % (a, t))
    test = [t for a, t in dw if t.startswith("test") and "0x94d448" in t]
    set_off = [t for a, t in dw if re.search(r"\+0xa14\]", t)]
    clr_off = [t for a, t in dw if re.search(r"\+0xa10\]", t)]
    ta_ = [a for a, t in dw if t.startswith("test") and "0x94d448" in t]
    je = [x for x in dw if re.match(r"je +0x[0-9a-f]+$", x[1])]
    je_tgt = int(je[0][1].split("0x")[1], 16) if je else -1
    set_addr = [a for a, t in dw if re.search(r"\+0xa14\]", t)]
    clr_addr = [a for a, t in dw if re.search(r"\+0xa10\]", t)]
    att = dict(ins)
    say("    branch: test@%s je@%s -> 0x%x (%r) ; set load @%s ; clear load @%s"
        % (hexa(ta_[0]) if ta_ else "-", hexa(je[0][0]) if je else "-", je_tgt,
           att.get(je_tgt, "?"), hexa(set_addr[0] if set_addr else 0),
           hexa(clr_addr[0] if clr_addr else 0)))
    gate("G4a", len(test) == 1 and test[0].endswith(",0x1"),
         "the predicate is `%s` -> bit 0x1 of the plain relations dword" % (test[0] if test else "-"))
    br = bool(je and ta_ and set_addr and clr_addr
              and je[0][0] < set_addr[0] < je_tgt <= clr_addr[0]
              and "ds:0x997b20" in att.get(je_tgt, ""))
    gate("G4b", len(set_off) == 1 and len(clr_off) == 1 and br,
         "set -> element 0xa14 (fallthrough after the je), clear -> element 0xa10 (the je target): "
         "the branch, not just presence, picks the label")
    gate("G4c", L[10 + 0xA14 // 4].strip() == b"Pact" and L[10 + 0xA10 // 4].strip() == b"Treaty",
         "element 0xa14 = %r, element 0xa10 = %r -> the SET bit names its own label (M364: 0x1=PACT)"
         % (L[10 + 0xA14 // 4].strip(), L[10 + 0xA10 // 4].strip()))

    # ---------------------------------------------------------------- G5 the table
    say("")
    say("G5  THE TABLE - bit -> array element -> labels.txt line -> text")
    say("    #  id          bit      dword       elem  line  text")
    tbl = []
    for n, r in enumerate(rows):
        sm = [x for x in srows if x["id"] == r["id"]]
        s = sm[0] if sm else {"base": 0, "mask": 0}
        el = r["off"] // 4
        txt = L[10 + el].strip().decode("latin1")
        tbl.append((r["id"], s["base"], el, 10 + el, txt, s["mask"]))
        say("    %2d %-11s 0x%-6x %-10s %5d %5d  %s"
            % (n + 1, hexa(r["id"]), r["id"] & 0x7FFFFFFF,
               "plain" if s["base"] == PLAIN else "high", el, 10 + el, txt))
    PINNED = [(0x8, 875, "Commlink"), (0x10, 646, "Vendetta"), (0x4, 643, "Truce"),
              (0x2, 644, "Treaty"), (0x1, 645, "Pact"), (0x1000, 868, "I have infiltrator"),
              (0x2000, 869, "I want to talk"), (0x20, 870, "I want revenge"),
              (0x2000000, 871, "I have surrendered"), (0x400, 872, "I shall betray"),
              (0x40000, 873, "I am atrocity victim"), (0x80000008, 874, "Fight to the death"),
              (0x80002000, 894, "Fix current status as permanent")]
    got = [(x[0], x[2], x[4]) for x in tbl]
    gate("G5c", got == PINNED,
         "all 13 (id, element, text) triples match the pinned table (%d/13 rows)"
         % sum(1 for g, w in zip(got, PINNED) if g == w))
    stance = {x[0]: x[4] for x in tbl}
    gate("G5b", [stance.get(i) for i in (0x1, 0x2, 0x4, 0x10)] ==
         ["Pact", "Treaty", "Truce", "Vendetta"],
         "the 4 stance ids resolve (through the computed element) to %s"
         % [stance.get(i) for i in (0x1, 0x2, 0x4, 0x10)])
    np_ = sum(1 for x in tbl if x[1] == PLAIN)
    nmask = sum(1 for x in tbl if x[5] == (x[0] & 0x7FFFFFFF))
    gate("G5a", np_ == 11 and len(tbl) - np_ == 2 and nmask == 13,
         "11 rows anchor the plain dword 0x94d448, 2 the high dword 0x94d468; every sync mask == "
         "id&0x7fffffff (%d/13)" % nmask)

    # ---------------------------------------------------------------- G6 rivals
    say("")
    say("G6  RIVALS (each must FAIL on the numbers above)")
    raw = open(os.path.join(ROOT, "programs/terran.exe"), "rb").read() if os.path.exists(
        os.path.join(ROOT, "programs/terran.exe")) else b""
    hits = [(t, raw.find(t.encode("latin1"))) for _, _, _, _, t, _ in tbl
            if raw and t.encode("latin1") in raw]
    inline = [r for r in allslots if r["dst"] == "call 0x604fd2" and r["src"] != "obj"]
    say("    R1 'the labels are inline strings in terran.exe' -> %d/%d of the 13 texts occur in the"
        % (len(hits), len(tbl)))
    say("       image at all: %s" % ", ".join("%r@%x" % (t, o) for t, o in hits))
    say("       13 row text operands: %d are heap loads [0x997b20+off], %d are address pushes"
        % (13 - len(inline), len(inline)))
    gate("R1", raw and not inline,
         "R1 refuted: 13/13 add_item texts are loaded through ds:0x997b20 (%d inline); the "
         "%d incidental image copies are never referenced by these rows" % (len(inline), len(hits)))
    no_shift = [L[el].strip().decode("latin1") for _, _, el, _, _, _ in tbl]
    say("    R2 'the element index IS the file line (no +10 shift)' -> first row would read %r"
        % (no_shift[0][:40] if no_shift else "-",))
    say("       and the count line would be atoi(%r) = %d" % (L[8][:20], atoi(L[8])))
    gate("R2", atoi(L[8]) == 0 and bool(no_shift) and no_shift[0] != tbl[0][4],
         "R2 refuted: without the +10 shift the count parses from the '#LABELS' header -> 0 lines")
    ords = [n + 1 for n, r in enumerate(rows)]
    nhi = sum(1 for r in rows if r["id"] & 0x80000000)
    gate("R3", [r["id"] for r in rows] != ords and sum(1 for r in rows if r["id"] > 13) >= 9
         and nhi == 2,
         "R3 refuted: the ids are bit masks (%d of 13 exceed 13; %d carry 0x80000000), not ordinals"
         % (sum(1 for r in rows if r["id"] > 13), nhi))
    lo = {x[0]: x[4] for x in tbl}
    hi = {x[0] & 0x7FFFFFFF: x[4] for x in tbl if x[1] == HIGH}
    same = [b for b in hi if lo.get(b) == hi[b]]
    gate("R4", len(same) == 0,
         "R4 refuted: the 2 high ids do NOT reuse the low bit's text (%d/%d equal) - distinct flags"
         % (len(same), len(hi)))
    gaps = [runs[i + 1][0] - runs[i][-1] for i in range(len(runs) - 1)]
    gate("R5", len(runs) == 3,
         "R5 refuted: the 13 labels are not one contiguous page (%d runs %s, gaps %s)"
         % (len(runs), [len(r) for r in runs], gaps))

    # ---------------------------------------------------------------- verdict
    npass = sum(1 for _, ok in gates if ok)
    h = hashlib.sha256(("\n".join(out)).encode()).hexdigest()[:16]
    say("")
    say("%s M367: %d/%d gates" % ("PASS" if npass == len(gates) else "FAIL", npass, len(gates)))
    say("digest %s" % h)
    print("\n".join(out))
    return 0 if npass == len(gates) else 1


def hexa(v):
    return "0x%x" % (v or 0)


if __name__ == "__main__":
    sys.exit(main())
