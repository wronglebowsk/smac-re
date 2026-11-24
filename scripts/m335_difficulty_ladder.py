#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M335 — the difficulty ladder: INDEX -> LABEL order, measured.

PICK: NEXT_PROMPT.md (x6), first clause: `## M332`'s OPEN row "which difficulty INDEX means
which label (the cmps top out at 4 while `## M330`'s k-table needs k=2 at >=5)".

Question answered: the game keeps the six difficulty NAMES parsed out of alpha.txt `#DIFF` in a
6-dword table at `0x94d2ac`; the runtime difficulty dword `ds:0x985aec` (M332) is that table's
index, so index 0..5 = file order = Citizen, Specialist, Talent, Librarian, Thinker, Transcend.
The cmps on 0x985aec top out at 4 because five boundaries separate six rows; the >=5 arm
(M330's k=2 refund) is exactly the TRANSCEND row, not a hypothetical.

Every number is COMPUTED from the static image and the shipped data file:
  scratch/m574/text.txt   objdump of .text (address -> insn)
  programs/terran.exe     the PE (VA-mapped strings)
  programs/alpha.txt      the shipped `#DIFF` block
Zero box time.

GATES (printed first, asserted after; each has a named mutant in scripts/m335_mutate.py):
  G1  alpha.txt: exactly one `#DIFF` section, exactly 6 non-empty rows, in file order.
  G2  the loader: the `DIFF` name string, its single push site, the fill loop's base/step/bound
      => the hard-coded iteration count equals the file's row count.
  G3  reference census (all addressing forms, scaled included): exact site set, 0 stores
      outside the loader.
  G4  ORDER PROOF: the chooser builds its items by walking the array FORWARD with the loop
      counter as the item index, and seeds the dialog with ds:0x985aec.
  G5  INDEX PROOF: a reader indexes the array with ds:0x985aec, and two loops bound their
      walk by the immediate 6 (an independent reading of the array length).
  G6  the domain: the only clamp on the index is FUN_00423af0(lo=0, hi=6) with hi INCLUSIVE --
      hi equals the array's END ADDRESS (off-by-one by construction); the refund's cmps on
      0x985aec are {3 (jle) , 4 (jne)} => k=1 at exactly 4, k=2 at >=5; with 6 rows, 5 is
      TRANSCEND.
  G7  RIVAL killed: "0x94d2ac is an array of something else (world sizes / faction adjectives)".
"""
import hashlib
import io
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
EXE = os.path.join(ROOT, "programs/terran.exe")
ALPHA = os.path.join(ROOT, "programs/alpha.txt")

BASE = 0x94D2AC          # the difficulty-name table
END = 0x94D2C4           # the loader's hard-coded stop
STEP = 4
ARRAY_END_ADDR = END
NAMES_VA = 0x691D20      # "DIFF" in .data
SECTION_OPENER = "0x5ea431"
ROW_READER = "0x5ea475"
LABELS = ["Citizen", "Specialist", "Talent", "Librarian", "Thinker", "Transcend"]
SITES = {  # measured; the census must reproduce this EXACTLY (both directions)
    0x57AC74: "loader: mov esi,0x94d2ac (fill start)",
    0x57AC88: "loader: cmp esi,0x94d2c4 (fill bound)",
    0x4DDAFA: "chooser FUN_004ddaa0: mov esi,0x94d2ac",
    0x4DDB36: "chooser FUN_004ddaa0: cmp esi,0x94d2c4",
    0x44A1C8: "reader: [edx*4+base], edx = BYTE[rec+0x20]",
    0x484CC9: "reader: [edx*4+base] inside a cmp-bound 6 loop",
    0x485426: "reader: [edx*4+base] inside a cmp-bound 6 loop",
    0x48678F: "reader: [edx*4+base], edx = movsx BYTE[0x176*i+0x8eff1a]",
    0x486F40: "reader: [eax*4+base], eax = FUN_00423af0(hy=6, lo=0, movsx BYTE[0x8f0c11])",
    0x57C606: "chooser FUN_0057c550: [esi*4+base] (annotated extremes)",
    0x599405: "reader: [ecx*4+base], ecx = ds:0x985aec",
}
REFUND = (0x520714, 0x520719, 0x52071C, 0x520728, 0x52072B, 0x520758)
CLAMP = "0x423af0"


def parse_text(lines):
    out = []
    for ln in lines:
        m = re.match(r"^\s*([0-9a-f]{5,8}):\t(?:[0-9a-f ]+)?\t(\w+)\s*(.*)$", ln)
        if not m:
            continue
        out.append((int(m.group(1), 16), m.group(2), m.group(3).strip()))
    return out


def at(ins, addr):
    for i, (a, op, o) in enumerate(ins):
        if a == addr:
            return i, op, o
    raise KeyError(hex(addr))


def window(ins, lo, hi):
    return [(a, op, o) for a, op, o in ins if lo <= a <= hi]


def pe_strs(data):
    pe = struct.unpack_from("<I", data, 0x3c)[0]
    n = struct.unpack_from("<H", data, pe + 6)[0]
    opt = struct.unpack_from("<H", data, pe + 20)[0]
    base = struct.unpack_from("<I", data, pe + 52)[0]
    secs, so = [], pe + 24 + opt
    for i in range(n):
        vs, va, rs, rp = struct.unpack_from("<IIII", data, so + i * 40 + 8)
        secs.append((base + va, rs, rp))
    d = {}
    for va, rs, rp in secs:
        blob = data[rp:rp + rs]
        for m in re.finditer(rb"[ -~]{3,60}", blob):
            d[va + m.start()] = m.group().decode()
    return d


def alpha_rows(txt):
    rows, inside, n_sec = [], False, 0
    for raw in txt.split("\n"):
        line = raw.rstrip("\r")
        if line.strip().upper() == "#DIFF":
            n_sec += 1
            inside = True
            continue
        if inside:
            if not line.strip() or line.lstrip().startswith("#"):
                break
            rows.append(line.strip().rstrip(",").strip())
    return n_sec, rows


def _g1(ins, strs, nsec, rows):
    return (nsec == 1 and rows == LABELS,
            "alpha.txt #DIFF sections=%d rows=%d %s" % (nsec, len(rows), rows))


def _g2(ins, strs, nsec, rows):
    pushes = [(a, o) for a, op, o in ins if op == "push" and "0x691d20" in o]
    ok = len(pushes) == 1 and pushes[0][0] == 0x57AC56
    i0 = at(ins, 0x57AC56)[0]
    call_ok = any(op == "call" and SECTION_OPENER in o for op, o in [ins[i0 + k][1:] for k in range(4)])
    i_l = at(ins, 0x57AC74)[0]
    fill = [ins[i_l + k][1:] for k in range(0, 7)]
    init_ok = fill[0] == ("mov", "esi,0x94d2ac")
    step_ok = any(op == "add" and o.replace(" ", "") == "esi,0x4" for op, o in fill)
    bound_ok = any(op == "cmp" and "0x94d2c4" in o for op, o in fill)
    back_ok = any(op == "jl" and "0x57ac79" in o for op, o in fill)
    iters = (END - BASE) // STEP
    nm = strs.get(NAMES_VA, "")
    return (ok and call_ok and nm == "DIFF" and init_ok and step_ok and bound_ok and back_ok
            and iters == len(rows),
            "loader push@0x%x -> call %s, name=%r, fill init=%s base=0x%x step=%d bound=0x%x "
            "backedge=%s => %d iterations == %d file rows"
            % (pushes[0][0] if pushes else 0, SECTION_OPENER, nm, init_ok, BASE, STEP, END,
               back_ok, iters, len(rows)))


def _g3(ins, strs, nsec, rows):
    addrs = [BASE + k * 4 for k in range((END - BASE) // 4)]
    seen = {}
    for a, op, o in ins:
        if any(hex(x) in o for x in addrs) or "0x94d2c4" in o:
            seen[a] = (op, o)
    exact = set(seen) == set(SITES)
    stores = [a for a, (op, o) in seen.items() if op == "mov" and o.split(",")[0].startswith("DWORD PTR [")]
    return (exact and not stores,
            "sites=%d expected=%d extra=%s missing=%s stores=%d"
            % (len(seen), len(SITES), sorted(hex(x) for x in set(seen) - set(SITES)),
               sorted(hex(x) for x in set(SITES) - set(seen)), len(stores)))


def _g4(ins, strs, nsec, rows):
    w = window(ins, 0x4DDAF8, 0x4DDB60)
    txt_w = ["%s %s" % (op, o) for _, op, o in w]
    has = lambda frag: any(frag in t for t in txt_w)
    order_ok = (has("mov esi,0x94d2ac") and has("mov eax,DWORD PTR [esi]")
                and has("push edi") and has("add esi,0x4") and has("inc edi")
                and has("cmp esi,0x94d2c4") and has("jl") and has("call 0x60c555"))
    seed_ok = has("mov eax,ds:0x985aec") and has("call 0x5f1394")
    return (order_ok and seed_ok,
            "append loop walks 0x94d2ac..0x94d2c4 forward with push edi as the item index=%s; "
            "current value ds:0x985aec seeded into the dialog before %s"
            % (order_ok, "call 0x5f1394" if seed_ok else "MISSING"))


def _g5(ins, strs, nsec, rows):
    i5 = at(ins, 0x599405)[0]
    o5 = ins[i5][2]
    prev = ["%s %s" % (op, o) for _, op, o in ins[max(0, i5 - 4):i5]]
    idx_ok = "mov ecx,DWORD PTR ds:0x985aec" in prev and "[ecx*4+0x94d2ac]" in o5
    bounds6 = [a for a, op, o in ins if op == "cmp" and o.replace(" ", "").endswith(",0x6")
               and a in (0x484CB3, 0x485410)]
    return (idx_ok and len(bounds6) == 2,
            "0x599405 indexes with ds:0x985aec (prev=%s); independent 6-bounds at %s"
            % (prev[-1] if prev else "-", [hex(a) for a in bounds6]))


def _g6(ins, strs, nsec, rows):
    wc = window(ins, 0x486F2C, 0x486F47)
    args = ["%s %s" % (op, o) for _, op, o in wc]
    clamp_ok = any("push 0x6" in s for s in args) and any("push 0x0" in s for s in args) \
        and any("0x8f0c11" in s for s in args) and any(CLAMP in s for s in args) \
        and any("[eax*4+0x94d2ac]" in s for s in args)
    ci = at(ins, 0x423AF0)[0]
    cb = ["%s %s" % (ins[ci + k][1], ins[ci + k][2]) for k in range(0, 20)]
    clamp_law = ("cmp eax,DWORD PTR [ebp+0xc]" in cb and "jl 0x423b09" in cb
                 and "cmp ecx,DWORD PTR [ebp+0xc]" in cb
                 and "cmp edx,DWORD PTR [ebp+0x10]" in cb and "jle 0x423b1b" in cb)
    off_by_one = (END - BASE) // STEP == 6 and "push 0x6" in args
    rf = ["%s %s" % (op, o) for a, op, o in window(ins, min(REFUND), max(REFUND))]
    ref_ok = any("cmp eax,0x3" in s for s in rf) and any("jle 0x520795" in s for s in rf) \
        and any("cmp eax,0x4" in s for s in rf) and any("jne 0x520758" in s for s in rf)
    return (clamp_ok and clamp_law and off_by_one and ref_ok,
            "clamp FUN_00423af0(lo=0,hi=6) INCLUSIVE with hi == the array END address "
            "(0x%x, 6 rows => last index 5): off-by-one by construction=%s; refund: "
            "cmp 3/jle (none <=3), cmp 4/jne => k=1 at 4, k=2 at >=5 (=Transcend) =%s"
            % (END, off_by_one, ref_ok))


def _g7(ins, strs, nsec, rows):
    nm = strs.get(NAMES_VA, "")
    iters = (END - BASE) // STEP
    return (nm == "DIFF" and rows == LABELS and iters == 6,
            "rival 'not the difficulty labels' killed: push-site string %r + alpha rows %d "
            "+ loader iterations %d all agree" % (nm, len(rows), iters))


GATE_FNS = [("G1", _g1), ("G2", _g2), ("G3", _g3), ("G4", _g4), ("G5", _g5),
            ("G6", _g6), ("G7", _g7)]


def gates(txt_lines, alpha_txt, exe_bytes):
    ins = parse_text(txt_lines)
    strs = pe_strs(exe_bytes)
    nsec, rows = alpha_rows(alpha_txt)
    g = {}
    for name, fn in GATE_FNS:
        try:
            g[name] = fn(ins, strs, nsec, rows)
        except Exception as e:            # a vanished site FAILs its own gate only
            g[name] = (False, "EXC %s: %s" % (type(e).__name__, e))
    return g


def main():
    txt = io.open(TEXT, encoding="utf-8", errors="replace").read().split("\n")
    alpha = io.open(ALPHA, encoding="utf-8", errors="replace").read()
    exe = open(EXE, "rb").read()
    g = gates(txt, alpha, exe)
    print("M335 difficulty-ladder census (static; text=%s)" % os.path.basename(TEXT))
    for k in sorted(g):
        ok, msg = g[k]
        print("%-3s %-4s %s" % (k, "PASS" if ok else "FAIL", msg))
    h = hashlib.sha1("\n".join("%s=%s" % (k, g[k][0]) for k in sorted(g)).encode()).hexdigest()
    print("digest=%s gates=%d pass=%d" % (h[:16], len(g), sum(1 for k in g if g[k][0])))
    if len(g) != 7 or not all(g[k][0] for k in g):
        print("FAIL M335: %d/%d gates" % (sum(1 for k in g if g[k][0]), len(g)))
        return 1
    print("PASS M335: %d/%d gates" % (len(g), len(g)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
