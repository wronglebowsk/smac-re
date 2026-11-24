#!/usr/bin/env python3
"""M356 - the +0x30 bit-2 stamp and what the component bytes +0x24..+0x28 feed.

M354's row atlas left two things open: the game nouns of +0x25..+0x28 and
whether the +0x30 bit-2 stamp is a prototype/design mark.  This milestone
answers both from the objdump listing alone (static; no box, no Wine, no gdb):

  census   every write to the row flags word (row+0x30 == absolute 0x98adb8)
           is classified SET / ASSIGN / CLEAR-BIT2 from the INSTRUCTION SHAPE,
           not from a name table.  The printed table is the answer: bit 2 has
           N setters and 0 AND-clears -- a one-way latch.
  latch    the queue decoder (0x4efe50) saves the OLD bit into a bool, ORs it
           in, STORES, and only on a 0->1 transition calls 0x572800.
  guard    two setters are guarded `cmp idx,0x40 / jl` -- owner-band rows only.
  feeds    +0x24 indexes 0x92ae80 (stride from the lea chain 9*16 = 0x90),
           +0x25 indexes 0x92b950 (0x10 stride, extent 0x92baa0 -> 21 records),
           +0x26 indexes 0x92fd18 (0x10 stride, extent 0x92fdb8 -> 10 records).
           The row finalizer 0x595e80 COMPARES the +0x25 byte with the +0x26
           byte and assigns the +0x2b mode from the ordering: that is the
           code-side proof that +0x25 is the offense rating and +0x26 the armor
           rating, independent of any text file.
  corpus   programs/alpha.txt has 21 #WEAPONS rows and 10 #DEFENSES rows -- a
           corroboration printed, never gated (game files stay out of git).
  rival    "all four component bytes +0x25..+0x28 are rule-table ordinals" is
           MEASURED FALSE: +0x27 and +0x28 reach no 16-byte table.

    python3 -u scripts/m356_prototype_stamp.py            # acceptance
    python3 -u scripts/m356_prototype_stamp.py --digest   # digest only
    SMAC_M356_TEXT=/other/listing ...
"""
import argparse
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("SMAC_M356_TEXT") or os.path.join(ROOT, "scratch", "m574", "text.txt")
STARTS = os.environ.get("SMAC_M356_STARTS") or os.path.join(ROOT, ".func_starts.json")
ALPHA = os.environ.get("SMAC_M356_ALPHA") or os.path.join(ROOT, "programs", "alpha.txt")
MUT = os.environ.get("SMAC_M356_MUTANT", "")

ROW = 0x98AD88
FLAGS = ROW + 0x30                       # +0x30 word
FLAGS_END = FLAGS + 2                    # +0x32 is the pre-req word
WEAP, ARM, CHAS = 0x92B950, 0x92FD18, 0x92AE80
WEAP_END, ARM_END = 0x92BAA0, 0x92FDB8   # loop bounds, parsed from cmp
CHAS_STRIDE_EXPECT = 0x90                # 9 records of 16, from lea/shl chain
FINALIZER = (0x595E80, 0x596000)         # the row finalizer (mode + flags init)
DEC = (0x4EFE41, 0x4EFE80)               # queue-decoder stamp window

# declared expectations (the census is computed; these are asserted against it)
SETTERS = {
    0x4D2FF9, 0x4EED18, 0x4EFE60, 0x5729D5, 0x573FED, 0x574107,
    0x574117, 0x59D273, 0x59D375, 0x59D432, 0x59DB65,
}
ASSIGN_INIT = {0x595F82: 0x1, 0x595F91: 0x105, 0x595F9C: 0x115}

INS = re.compile(r"^\s*([0-9a-f]{6,8}):\t([0-9a-f ]+)\t(.*)$")
LIT = re.compile(r"0x([0-9a-f]+)")
MEMFLAGS = re.compile(r"(BYTE|WORD) PTR \[([^\]]*)(0x98adb8)\]")
IMM = re.compile(r"^(or|and|mov|test)\s+(BYTE|WORD) PTR \[[^\]]+\],\s*0x([0-9a-f]+)$")
REGS = {"eax": 0, "ecx": 1, "edx": 2, "ebx": 3, "esp": 4, "ebp": 5, "esi": 6, "edi": 7}
R8 = {"al": "eax", "ah": "eax", "cl": "ecx", "ch": "ecx", "dl": "edx", "dh": "edx",
      "bl": "ebx", "bh": "ebx", "sil": "esi", "dil": "edi",
      "ax": "eax", "bx": "ebx", "cx": "ecx", "dx": "edx", "si": "esi", "di": "edi"}


def norm(s):
    return re.sub(r"\s+", " ", s.strip())


class Listing:
    def __init__(self, path, patch=None):
        self.at, self.order = {}, []
        with open(path, "r", errors="replace") as f:
            for line in f:
                m = INS.match(line)
                if not m:
                    continue
                a = int(m.group(1), 16)
                self.at[a] = norm(m.group(3))
                self.order.append(a)
        self.order.sort()
        if patch:
            self.apply_patch(patch)

    def apply_patch(self, spec):
        ad, old, new = spec.split("|")
        ad = int(ad, 16)
        t = self.at.get(ad)
        if t is None or old not in t or t.count(old) != 1:
            raise SystemExit("PATCH REJECTED: 0x%x %r not unique in %r" % (ad, old, t))
        self.at[ad] = t.replace(old, new, 1)

    def window(self, lo, hi):
        return [(a, self.at[a]) for a in self.order if lo <= a < hi]

    def prev(self, a, n=1):
        i = self.order.index(a)
        return [(self.order[j], self.at[self.order[j]]) for j in range(max(0, i - n), i)]

    def after(self, a, n=6):
        i = self.order.index(a)
        return [(self.order[j], self.at[self.order[j]])
                for j in range(i + 1, min(len(self.order), i + 1 + n))]


def fn_of(a, starts):
    import bisect
    i = bisect.bisect_right(starts, a) - 1
    return starts[i] if i >= 0 else 0


def census(L, starts):
    """Every write that touches the +0x30 flags word, classified by shape."""
    rows = []
    for a, t in L.window(0, 0x800000):
        m = MEMFLAGS.search(t)
        if not m:
            continue
        addr = int(m.group(3), 16)
        width = m.group(1)
        if addr >= FLAGS_END:
            continue
        op = t.split()[0]
        # direct RMW / assign on the memory operand
        im = IMM.match(t)
        if im and op in ("or", "and", "mov"):
            k, imm = im.group(1), int(im.group(3), 16)
            if k == "or":
                cls = "SET" if imm & 4 else "set-other"
            elif k == "and":
                cls = "CLEAR-BIT2" if (imm & 4) == 0 else "clear-other"
            else:
                cls = "ASSIGN"
            rows.append((a, fn_of(a, starts), width, k, imm, cls, t))
            continue
        # store of a register previously OR'd in the same block (0x4efe59 form)
        if op == "mov" and width == "WORD" and re.match(r"mov WORD PTR \[[^\]]+\],\w+$", t):
            reg = t.rsplit(",", 1)[1].strip()
            reg = R8.get(reg, reg)
            for pa, pt in L.prev(a, 10):
                pm = re.match(r"(or|and|mov) (\w+),(0x[0-9a-f]+|\w+)$", pt)
                if pm and R8.get(pm.group(2), pm.group(2)) == reg:
                    imm = pm.group(3)
                    po = pm.group(1)
                    if imm.startswith("0x"):
                        imm = int(imm, 16)
                        cls = "SET" if (po == "or" and imm & 4) else (
                            "CLEAR-BIT2" if (po == "and" and (imm & 4) == 0) else "rmw-other")
                    else:
                        cls = "rmw-other"
                    rows.append((a, fn_of(a, starts), width, "store<-" + po, imm, cls, t + "  // " + pt))
                    break
    return rows


TABLES = (WEAP, ARM, CHAS)


def _tbl(v):
    if WEAP <= v < WEAP + 0x200:
        return WEAP
    if ARM <= v < ARM + 0x200:
        return ARM
    if CHAS <= v < CHAS + 0x900:
        return CHAS
    return None


def trace_base(L, addr, reg):
    """Follow the register that holds a component byte to the rule-table base
    it dereferences.  Register copies/shl/lea are followed; any other write to
    the register or a control transfer aborts.  Returns None if no table."""
    for ba, bt in L.after(addr, 8):
        if re.match(r"(j\w+|call|ret|push|pop)\b", bt):
            return None
        # a dereference through our register is the deciding event
        if re.search(r"\[[^\]]*\b%s\b" % reg, bt):
            for h in LIT.findall(bt):
                tb = _tbl(int(h, 16))
                if tb:
                    return tb
            return None               # used as an index/base elsewhere
        m = re.match(r"mov(?:sx|zx)? (\w+),(.*)$", bt)
        if m and R8.get(m.group(1), m.group(1)) == reg:
            s2 = R8.get(m.group(2).strip(), m.group(2).strip())
            if s2 in REGS:
                reg = s2 if s2 != reg else reg
                continue
            return None               # overwritten with an immediate
        if re.match(r"xor %s,%s$" % (reg, reg), bt):
            continue
        if re.match(r"(shl|sar|shr|and|add|imul|lea) %s\b" % reg, bt):
            continue
        if re.match(r"mov %s," % reg, bt):
            return None
    return None


def table_reads(L, field_abs):
    """Sites reading a row byte, attributed to a rule table by following the
    loaded register (a mini tracer, not a fixed window)."""
    out = []
    want = "0x%x" % field_abs
    for a, t in L.window(0, 0x800000):
        if want not in t or "PTR" not in t:
            continue
        m = re.match(r"mov(?:sx|zx)? (\w+),(?:BYTE|WORD) PTR", t)
        if not m:
            continue
        reg = R8.get(m.group(1), m.group(1))
        out.append((a, trace_base(L, a, reg), t))
    return out


def alpha_rows(path):
    if not os.path.exists(path):
        return None
    want = {"#WEAPONS": None, "#DEFENSES": None, "#CHASSIS": None}
    cur = None
    counts = {}
    for line in open(path, "r", errors="replace"):
        s = line.strip()
        if s.startswith("#") and not s.startswith(";") and not s.startswith("#;"):
            hdr = s.split(";")[0].strip()
            cur = hdr if hdr in want else None
            if cur:
                counts[cur] = 0
            continue
        if cur and s and not s.startswith(";"):
            counts[cur] += 1
    return counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--digest", action="store_true")
    args = ap.parse_args()

    starts = sorted(json.load(open(STARTS)))
    L = Listing(TEXT, MUT or None)
    fails = []

    def gate(name, cond, detail):
        print("%-4s %-34s %s" % ("PASS" if cond else "FAIL", name, detail))
        if not cond:
            fails.append(name)

    print("== M356 row+0x30 flags-word write census (computed from instruction shapes)")
    rows = census(L, starts)
    print(" %-8s %-9s %-5s %-11s %-6s %s" % ("addr", "function", "width", "op", "imm", "class / text"))
    for a, fn, w, op, imm, cls, t in rows:
        print(" 0x%06x 0x%06x %-5s %-11s %-6s %s" % (a, fn, w, op, hex(imm) if isinstance(imm, int) else imm, cls + "  " + t[:58]))

    setters = {r[0] for r in rows if r[5] == "SET"}
    clears = [r for r in rows if r[5] == "CLEAR-BIT2"]
    assigns = {r[0]: r[4] for r in rows if r[5] == "ASSIGN"}
    bit2_assign = {a: v for a, v in assigns.items() if isinstance(v, int) and v & 4}
    print("\n measured: %d flag-word writes, %d bit-2 setters, %d bit-2 AND-clears, "
          "%d ASSIGNs (%d with bit 2)" % (len(rows), len(setters), len(clears), len(assigns), len(bit2_assign)))

    gate("G1 setter census", setters == SETTERS,
         "measured %d == declared %d%s" % (len(setters), len(SETTERS),
                                           "" if setters == SETTERS else "  diff " + str(sorted(map(hex, setters ^ SETTERS)))))
    gate("G2 no bit-2 clearer (latch)", len(clears) == 0,
         "%d AND instructions clear bit 2" % len(clears))
    gate("G3 init constants carry bit 2", bit2_assign == {a: v for a, v in ASSIGN_INIT.items() if v & 4},
         "bit-2 ASSIGNs " + str(sorted(map(hex, bit2_assign))))

    # --- guard: the two owner-band guards -------------------------------
    def guard_of(addr):
        for pa, pt in L.prev(addr, 12):
            m = re.match(r"cmp (\w+),0x([0-9a-f]+)$", pt)
            if m:
                return (pa, int(m.group(2), 16))
        return (None, None)

    g_ee = guard_of(0x4EED18)
    g_fe = guard_of(0x4EFE60)
    print("\n guards: 0x4eed18 <- cmp at 0x%x,0x%x ; 0x4efe60 <- cmp at 0x%x,0x%x"
          % (g_ee[0] or 0, g_ee[1] or 0, g_fe[0] or 0, g_fe[1] or 0))
    gate("G4 owner-band guard == 0x40", g_ee[1] == 0x40 and g_fe[1] == 0x40,
         "cmp imm %s / %s" % (hex(g_ee[1] or 0), hex(g_fe[1] or 0)))

    # --- second latch 0x4d2ff9: test-BEFORE-store, follow-up call --------
    one = dict(L.window(0x4D2FEC, 0x4D3008))
    one_seq = " | ".join("%s" % one[a] for a in sorted(one))
    print("\n latch2: " + one_seq)
    call2 = next((one[a] for a in sorted(one) if one[a].startswith("call")), "")
    ok_one = (one.get(0x4D2FF3, "") == "test al,0x4" and one.get(0x4D2FF5, "") == "jne 0x4d3016"
              and one.get(0x4D2FF7, "") == "or al,0x4" and call2 == "call 0x584520")
    gate("G15 second one-way latch", ok_one,
         "test-before-store + on-0->1 %r" % call2)

    # --- decoder latch: store precedes the was-set test, call on 0->1 ----
    dec = L.window(*DEC)
    txt = [(a, t) for a, t in dec]
    store_i = next((i for i, (a, t) in enumerate(txt) if a == 0x4EFE60), None)
    test_i = next((i for i, (a, t) in enumerate(txt) if a == 0x4EFE6A), None)
    call = next((t for a, t in dec if a > 0x4EFE6A and t.startswith("call")), "")
    seq = " | ".join(t for a, t in txt if a <= 0x4EFE6F)
    print("\n decoder: " + seq)
    ok_latch = (store_i is not None and test_i is not None and store_i < test_i
                and call == "call 0x572800")
    gate("G5 decoder latch + 0->1 call", ok_latch,
         "store@%s < test@%s, on-fall-through %r" % (hex(txt[store_i][0]) if store_i is not None else "-",
                                                    hex(txt[test_i][0]) if test_i is not None else "-", call))

    # --- component feeds -------------------------------------------------
    print("\n== component byte -> rule table (row0-anchored literal + base within 6 insns)")
    feeds = {}
    for off, absaddr, name in ((0x24, ROW + 0x24, "chassis"), (0x25, ROW + 0x25, "offense"),
                                (0x26, ROW + 0x26, "armor"), (0x27, ROW + 0x27, "?"),
                                (0x28, ROW + 0x28, "?")):
        rs = table_reads(L, absaddr)
        bases = {}
        for a, b, t in rs:
            if b is not None:
                key = CHAS if CHAS <= b < CHAS + 0x900 else (WEAP if WEAP <= b < WEAP + 0x200 else ARM)
                bases[key] = bases.get(key, 0) + 1
        feeds[off] = (len(rs), bases)
        print(" +0x%02x %-8s %3d read sites; table hits %s" %
              (off, name, len(rs), {hex(k): v for k, v in sorted(bases.items())}))

    gate("G6 +0x25 -> 0x92b950", feeds[0x25][1] == {WEAP: 181},
         "measured %s" % {hex(k): v for k, v in sorted(feeds[0x25][1].items())})
    gate("G7 +0x26 -> 0x92fd18", feeds[0x26][1] == {ARM: 47},
         "measured %s" % {hex(k): v for k, v in sorted(feeds[0x26][1].items())})
    gate("G8 +0x24 -> 0x92ae80", feeds[0x24][1] == {CHAS: 68},
         "measured %s" % {hex(k): v for k, v in sorted(feeds[0x24][1].items())})

    # table extents, parsed from the scan loops
    def cmp_imm(addr):
        t = L.at.get(addr, "")
        m = re.search(r"cmp \w+,0x([0-9a-f]+)$", t)
        return int(m.group(1), 16) if m else None

    we = cmp_imm(0x5745CC)
    ae = cmp_imm(0x5746B3)
    nw = (we - WEAP) // 0x10 if we else 0
    na = (ae - ARM) // 0x10 if ae else 0
    print("\n extents: offense 0x%x..0x%x = %d records; armor 0x%x..0x%x = %d records"
          % (WEAP, we or 0, nw, ARM, ae or 0, na))
    gate("G9 offense table = 21 recs", we == WEAP_END and nw == 21, "bound %s -> %d" % (hex(we or 0), nw))
    gate("G10 armor table = 10 recs", ae == ARM_END and na == 10, "bound %s -> %d" % (hex(ae or 0), na))

    # chassis stride from the lea/shl chain (9*16), not authored
    chain = [L.at.get(0x595EED, ""), L.at.get(0x595EF0, "")]
    m1 = re.match(r"lea \w+,\[\w+\+\w+\*8\]$", chain[0])
    m2 = re.match(r"shl \w+,0x([0-9a-f]+)$", chain[1])
    stride = (8 + 1) * (1 << int(m2.group(1), 16)) if (m1 and m2) else 0
    print(" chassis stride chain: %r ; %r -> 0x%x" % (chain[0], chain[1], stride))
    gate("G11 chassis stride 0x90", stride == CHAS_STRIDE_EXPECT, "computed 0x%x" % stride)

    # --- finalizer: offense vs armor -> mode byte +0x2b ------------------
    fin = dict(L.window(*FINALIZER))
    off_load = fin.get(0x595E9E, "")
    arm_load = fin.get(0x595EA4, "")
    cmpw = fin.get(0x595EAA, "")
    mode = fin.get(0x595EAE, "")
    print("\n finalizer: %r / %r / %r -> %r" % (off_load, arm_load, cmpw, mode))
    ok_fin = ("0x92b950" in off_load and "0x92fd18" in arm_load
              and cmpw.startswith("cmp al,bl") and "0x98adb3" in mode)
    gate("G12 finalizer compares W vs A", ok_fin, "offense byte vs armor byte -> +0x2b")

    # --- rival: are all four component bytes 0x10-stride table ordinals? -
    ten = lambda o: sum(v for k, v in feeds[o][1].items() if k in (WEAP, ARM))
    rare = {o: ten(o) for o in (0x27, 0x28) if ten(o)}
    print("\n RIVAL 'every component byte is an ordinal into a 0x10-stride rule table': "
          "+0x25=%d +0x26=%d hits, +0x27=%d +0x28=%d -> rival %s"
          % (ten(0x25), ten(0x26), ten(0x27), ten(0x28),
             "FAILS" if (ten(0x25) > 40 and ten(0x26) > 20 and not rare) else "survives"))
    gate("G13 rival fails on measurement", ten(0x25) > 40 and ten(0x26) > 20 and not rare,
         "0x10-table hits on +0x27/+0x28: %s" % ({hex(k): v for k, v in rare.items()} or "none"))

    # --- +0x28 writer census --------------------------------------------
    writes_28 = [a for a, t in L.window(0, 0x800000)
                 if re.search(r"mov BYTE PTR \[[^\]]*\+0x98adb0\],", t)]
    reads_28 = feeds[0x28][0]
    print("\n +0x28: %d writer(s) %s, %d reader(s)" % (len(writes_28), [hex(x) for x in writes_28], reads_28))
    gate("G14 +0x28 single writer", writes_28 == [0x595D1C] and reads_28 == 10,
         "writers %s / readers %d" % ([hex(x) for x in writes_28], reads_28))

    # --- corpus corroboration (printed, never gated) --------------------
    ac = alpha_rows(ALPHA)
    if ac:
        print("\n CORROBORATE programs/alpha.txt rows: " +
              ", ".join("%s=%d" % (k, v) for k, v in sorted(ac.items())) +
              " (offense %d, armor %d)" % (nw, na))
    else:
        print("\n CORROBORATE programs/alpha.txt not present (game file, not in git) - skipped")

    # --- digest ---------------------------------------------------------
    blob = "\n".join("%06x %s" % (r[0], r[6]) for r in rows) + "\n" + \
           "\n".join("%02x %d %s" % (o, feeds[o][0], sorted(hex(k) for k in feeds[o][1])) for o in feeds)
    digest = hashlib.sha256(blob.encode()).hexdigest()[:16]
    print("\n DIGEST %s" % digest)
    if args.digest:
        return 0
    print("\n%s M356: %d/%d gates" % ("PASS" if not fails else "FAIL", 15 - len(fails), 15))
    if fails:
        print(" failing: " + ", ".join(fails))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
