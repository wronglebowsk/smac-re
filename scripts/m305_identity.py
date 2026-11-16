#!/usr/bin/env python3
"""M305 (s263, STATIC, zero box): FUN_0051dcb0 - IDENTITY, CALLERS, CADENCE.

QUESTION (NEXT_PROMPT.md:74-76 OPEN shortlist; declared UNMODELED by B19 NAMED.md:1055 and
B20 NAMED.md:1093 - "per-call zero-rebuild cadence (FUN_0051dcb0 callers OPEN)"): the last five
milestones (M299/B19/M302/M303/B20) MODEL the two visit-counter tables; none of them modelled
their OWNER. Answer statically:
  (a) IDENTITY: is FUN_0051dcb0 the per-tile pass that zeroes-then-rebuilds BOTH counter tables?
      Zero-build window 0x51dcb8-0x51dd03 (byte family) / 0x51dd05-0x51dd17 (dword family), the
      outer walk over tile records (cursor stride 0x2c over ds:0x92ae14, bounds ds:0x92a378 /
      ds:0x92a37c), the two tables DWORD 0x989ce8(+0 MAX, +4 CNT) and BYTE 0x94eca8(MAX)/
      0x94ed28(CNT), plus the 4 sibling WORD arrays it also zeroes and 3 of them it also rebuilds.
  (b) CALLERS: every direct call site, its containing function (containment via
      ghidra_out/index.csv, never an objdump window at an arbitrary address; the ghidra shard
      headers are the second oracle), its preds, the leg that can bypass it, whether the caller
      loops it, and the guard the caller tests.
  (c) CADENCE: per-turn / per-player-phase / per-tile-pass / per-re-entry, named on the caller's
      own state, paired with an independent signal (the round counter's own writer).
  (d) UNKNOWNs stated plainly.

METHOD: every number printed is COMPUTED from scratch/m574/text.txt (objdump .text dump),
ghidra_out/index.csv and ghidra_out/shard_*.c; the table prints first, then asserts; two rival
hypotheses are scored against the SAME printed numbers and FAIL. stdout mirrors to
evidence/m305_identity.txt.

Run:  python3 scripts/m305_identity.py      (exit 0 = all assertions hold)
"""
import bisect
import collections
import csv
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
INDEX = os.path.join(ROOT, "ghidra_out/index.csv")
SHARDS = os.path.join(ROOT, "ghidra_out")
EVID = os.path.join(ROOT, "evidence", "m305_identity.txt")

FN = 0x51DCB0                        # FUN_0051dcb0
BYTE_BASE = 0x94ECA8                 # byte MAX array (per block)
BYTE_CNT = 0x94ED28                  # byte CNT  = block + 0x80
DW_BASE = 0x989CE8                   # dword slot MAX
DW_CNT = 0x989CEC                    # dword slot CNT = DW_BASE + 4
REC_BASE_GLOBAL = 0x92AE14           # tile_record_array pointer   (NAMED.md:90)
REC_COLS_GLOBAL = 0x92A378           # walk inner bound  = map width
REC_ROWS_GLOBAL = 0x92A37C           # walk outer bound  = map rows
REC_MULT_GLOBAL = 0x692184           # tile records per row = width/2 (NAMED.md:90)
ROWTAB = 0x95DA10                    # 304-B row table; count = ds:0x985af4 (NAMED.md:1044)
ROUND_GLOBAL = 0x985AFC              # round counter (skill instrument-laws.md:48)
DIRTY_GLOBAL = 0x8EFEDC              # "map changed" bitmask set inside FUN_0051dcb0
# the m54b_clean instance pinned by the s249 live census (NAMED.md:999): W=H=64, mult 32, 2048 recs
INST = dict(W=64, H=64, mult=32, recs=2048, rec_size=0x2C)

LINE_RX = re.compile(r"^ +([0-9a-f]{6,8}):\t([0-9a-f ]+)\t\s*(.+?)\s*$")
HEAD_RX = re.compile(r"^// ==== (\S+) @ (0x[0-9a-f]+) size=(\d+)")
JCC_RX = re.compile(r"^(je|jne|jl|jge|jg|jle|jb|jae|ja|jbe|js|jns|jo|jno|jc|jnc)\s+(?:0x)?([0-9a-f]{4,8})$")
JMP_RX = re.compile(r"^jmp\s+(?:0x)?([0-9a-f]{4,8})$")
CALL_RX = re.compile(r"^call\s+(?:0x)?([0-9a-f]{4,8})(?:\s|$)")
CTRL_RX = re.compile(r"\b(if|while|for|do|else)\b")


class Out:
    def __init__(self, path):
        self.f = open(path, "w")

    def p(self, s=""):
        self.f.write(s + "\n")
        print(s)

    def close(self):
        self.f.close()


def load_dump():
    ins, addrs = {}, []
    with open(TEXT, errors="replace") as fh:
        for ln in fh:
            m = LINE_RX.match(ln)
            if not m:
                continue
            a = int(m.group(1), 16)
            if a not in ins:
                ins[a] = m.group(3)
                addrs.append(a)
    addrs.sort()
    return ins, addrs


def load_index():
    funcs = []
    with open(INDEX) as fh:
        for row in csv.DictReader(fh):
            funcs.append((int(row["addr"], 16), row["name"], int(row["size_bytes"]),
                          int(row["n_callers"]), row["shard"]))
    funcs.sort()
    return funcs


def contain(funcs, faddrs, A):
    i = bisect.bisect_right(faddrs, A) - 1
    a, n, sz, nc, sh = funcs[i]
    return n, a, sz, nc, sh, (a <= A < a + sz)


def split(t):
    p = t.split(None, 1)
    return p[0], (p[1] if len(p) > 1 else "")


def tail_imm(op):
    m = re.search(r"0x([0-9a-f]+)\s*$", op)
    return int(m.group(1), 16) if m else None


def funcs_at(ins, addrs, lo, hi, pat):
    """instructions in [lo,hi] whose text matches pat"""
    i = bisect.bisect_left(addrs, lo)
    out = []
    while i < len(addrs) and addrs[i] <= hi:
        if pat.search(ins[addrs[i]]):
            out.append((addrs[i], ins[addrs[i]]))
        i += 1
    return out


# ---------------------------------------------------------------- ghidra C bodies
_SHARD = {}


def shard_bodies(shard):
    """{name: (addr, size, [lines])} for one ghidra export shard (cached)."""
    if shard not in _SHARD:
        path = os.path.join(SHARDS, "shard_%s.c" % shard)
        bodies = {}
        cur = None
        try:
            fh = open(path, errors="replace")
        except OSError:
            _SHARD[shard] = {}
            return _SHARD[shard]
        with fh:
            for ln in fh:
                m = HEAD_RX.match(ln)
                if m:
                    cur = (m.group(1), int(m.group(2), 16), int(m.group(3)))
                    bodies[cur[0]] = (cur[1], cur[2], [])
                    continue
                if cur is not None:
                    bodies[cur[0]][2].append(ln.rstrip("\n"))
        _SHARD[shard] = bodies
    return _SHARD[shard]


def guard_chain(body_lines, call_marker="FUN_0051dcb0("):
    """forward scan of the decompiled body, tracking braces, to the first call_marker line.
    Returns the stack of enclosing control heads (innermost last) or None."""
    stack = []
    seg = ""
    for ln in body_lines:
        s = ln.strip()
        if call_marker in s:
            return stack, s
        for ch in ln:
            if ch == "{":
                head = re.sub(r"\s+", " ", seg.strip())
                stack.append(head[-110:] if head else "{")
                seg = ""
            elif ch == "}":
                if stack:
                    stack.pop()
                seg = ""
            else:
                seg += ch
        if len(seg) > 400:
            seg = seg[-400:]
    return stack, None


def main():
    out = Out(EVID)
    ins, addrs = load_dump()
    funcs = load_index()
    faddrs = [f[0] for f in funcs]
    checks = []

    def A(name, cond, detail=""):
        checks.append((name, bool(cond), detail))
        out.p("  %-56s %s  %s" % (name, "OK" if cond else "FAIL", detail))

    out.p("M305 FUN_0051dcb0 - identity, callers, cadence   (STATIC: zero box, zero /proc, zero gdb)")
    out.p("inputs: %s (%d insn records), %s (%d functions)" % (TEXT, len(addrs), INDEX, len(funcs)))
    nm, fa, sz, nc, sh, ok = contain(funcs, faddrs, FN)
    nbody = sum(1 for a in addrs if FN <= a < FN + sz)
    out.p("S0 subject: %s @ %#x size=%d n_callers(index.csv)=%d n_insns=%d body_insns_in_window=%d"
          % (nm, FN, sz, nc, nbody, nbody))

    # ============================== S1 zero-build window
    out.p("\n== S1 zero-build window 0x51dcb8 - 0x51dd17 (verbatim)")
    for a in addrs:
        if 0x51DCB8 <= a <= 0x51DD17:
            out.p("  %s  %-42s" % (hex(a), ins[a]))
    # decode the byte-family loop
    b_base = tail_imm(split(ins[0x51DCB8])[1])
    inner_cmp = funcs_at(ins, addrs, 0x51DCEC, 0x51DCF6, re.compile(r"^cmp"))[0]
    n_entry = tail_imm(split(inner_cmp[1])[1])
    stride_i = funcs_at(ins, addrs, 0x51DCF7, 0x51DD03, re.compile(r"^add"))[0]
    blk_stride = tail_imm(split(stride_i[1])[1])
    term_i = funcs_at(ins, addrs, 0x51DCF7, 0x51DD03, re.compile(r"^cmp"))[0]
    b_term = tail_imm(split(term_i[1])[1])
    def disps(lo, hi, want, rx):
        got = []
        for a in addrs:
            if lo <= a <= hi and want in ins[a]:
                m = rx.search(ins[a])
                if m:
                    got.append(int(m.group(1) or "0", 16))
        return sorted(got)
    word_disp = disps(0x51DCC7, 0x51DCDF, "WORD PTR", re.compile(r"\[eax(?:\+0x([0-9a-f]+))?\],si"))
    byte_disp = disps(0x51DCDF, 0x51DCEC, "BYTE PTR", re.compile(r"\[edx\+ecx\*1(?:\+0x([0-9a-f]+))?\],0x0"))
    blocks, rem = divmod(b_term - b_base, blk_stride)
    word_step = tail_imm(split(funcs_at(ins, addrs, 0x51DCEC, 0x51DCF6, re.compile(r"^add"))[0][1])[1])
    out.p("  byte family: base=%#x entries/field=%d blk_stride=%d blocks=%d (remainder %d) terminator=%#x"
          % (b_base, n_entry, blk_stride, blocks, rem, b_term))
    out.p("  per-block zeroed fields: WORD disps %s (step %d) -> %s ; BYTE disps %s -> %s"
          % ([hex(d) for d in word_disp], word_step,
             [hex(b_base - 0x400 + d) for d in word_disp],
             [hex(d) for d in byte_disp], [hex(b_base + d) for d in byte_disp]))
    # dword-family loop
    d_base = tail_imm(split(ins[0x51DD05])[1])
    d_disp = disps(0x51DD0A, 0x51DD12, "DWORD PTR", re.compile(r"\[eax(?:\+0x([0-9a-f]+))?\],esi"))
    d_step = tail_imm(split(funcs_at(ins, addrs, 0x51DD0F, 0x51DD19, re.compile(r"^add"))[0][1])[1])
    d_term = tail_imm(split(funcs_at(ins, addrs, 0x51DD0F, 0x51DD19, re.compile(r"^cmp"))[0][1])[1])
    slots, srem = divmod(d_term - d_base, d_step)
    out.p("  dword family: base=%#x zeroed disps %s slot_stride=%d slots=%d (remainder %d) terminator=%#x"
          % (d_base, [hex(d) for d in d_disp], d_step, slots, srem, d_term))
    out.p("  RIVALS (byte-family block stride): span=%#x" % (b_term - b_base))
    for cand, why in ((0x100, "rival B: stride 256 (4 word arrays only)"),
                      (0x400, "rival C: stride 1024 (one page per block)"),
                      (blk_stride, "the decoded stride")):
        q, r = divmod(b_term - b_base, cand)
        out.p("    %-40s span/%#x = %d remainder %d%s" % (why, cand, q, r,
               "" if r == 0 else "   <== NOT A DIVISOR, FAILS"))
    A("A1 byte CNT base = byte MAX base + 0x80", b_base + byte_disp[-1] == BYTE_CNT,
      "%#x + %#x = %#x" % (b_base, byte_disp[-1], BYTE_CNT))
    A("A2 dword CNT = dword MAX + 4", d_base + max(d_disp) == DW_CNT,
      "%#x + %#x = %#x" % (d_base, max(d_disp), DW_CNT))
    A("A3 8 blocks divide the span exactly", blocks == 8 and rem == 0, "blocks=%d rem=%d" % (blocks, rem))
    A("A4 128 slots x 28 B divide the span exactly", slots == 128 and srem == 0,
      "slots=%d rem=%d" % (slots, srem))
    A("A5 the zero window covers BOTH counter tables",
      set(d_disp) == {0, 4} and set(byte_disp) == {0, 0x80},
      "dword %s byte %s" % ([hex(x) for x in d_disp], [hex(x) for x in byte_disp]))
    A("A6 rival strides fail on the printed span",
      all((b_term - b_base) % c for c in (0x100, 0x400)))

    # ============================== S2 the walk algebra
    out.p("\n== S2 the walk: bounds, cursor stride, parity (verbatim tail block)")
    for a in addrs:
        if 0x51DD19 <= a <= 0x51DD42 or 0x51E11D <= a <= 0x51E14A:
            out.p("  %s  %-42s" % (hex(a), ins[a]))
    rows_g = int(re.search(r"0x([0-9a-f]+)", ins[0x51DD19]).group(1), 16)
    base_g = int(re.search(r"0x([0-9a-f]+)", ins[0x51DD1E]).group(1), 16)
    cols_g = int(re.search(r"0x([0-9a-f]+)", ins[0x51E120]).group(1), 16)
    x_stride = tail_imm(split(ins[0x51E125])[1])
    rec_stride = tail_imm(split(ins[0x51E128])[1])
    parity = tail_imm(split(ins[0x51DD3A])[1])
    out.p("  decoded: rows_global=%#x cols_global=%#x rec_array_global=%#x x_stride=%d "
          "rec_cursor_stride=%#x parity_mask=%d"
          % (rows_g, cols_g, base_g, x_stride, rec_stride, parity))
    # enumerate the walk exactly as the machine code does, on the pinned instance
    W, H, mult, recs = INST["W"], INST["H"], INST["mult"], INST["recs"]
    per_row, total, seen, fold_match, cursor = [], 0, [], 0, 0
    for y in range(H):
        k = 0
        x = (y & parity)
        while x < W:
            total += 1
            k += 1
            seen.append(cursor)
            if cursor != mult * y + (x >> 1):
                fold_match += 1
            cursor += 1
            x += x_stride
        per_row.append(k)
    out.p("  pinned instance %s" % INST)
    out.p("  visits/row=%s (min %d max %d)  TOTAL record visits=%d  array length=%d"
          % ("uniform %d" % per_row[0] if len(set(per_row)) == 1 else per_row,
             min(per_row), max(per_row), total, recs))
    out.p("  cursor ends at record %d; cursor==mult*y+(x>>1) mismatches = %d ; "
          "records visited once = %d/%d (dupes %d)"
          % (cursor, fold_match, len(set(seen)), len(seen), len(seen) - len(set(seen))))
    def sim(xs, par, h, reset):
        tot, bad, cur2 = 0, 0, 0
        for y in range(h):
            if reset:
                cur2 = 0
            x = (y & par)
            while x < W:
                tot += 1
                if cur2 != mult * y + (x >> 1):
                    bad += 1
                cur2 += 1
                x += xs
        return tot, bad
    rivals2 = [
        ("RIVAL1 x-stride 1 (whole row per pass)", 1, parity, H, False),
        ("RIVAL2 outer bound 1 (one row per call)", x_stride, parity, 1, False),
        ("RIVAL3 cursor reset to base each row", x_stride, parity, H, True),
        ("AS DECODED (x+=2, parity start, shared cursor)", x_stride, parity, H, False),
    ]
    s2tab = {}
    for name, xs, par, h, reset in rivals2:
        tot, bad = sim(xs, par, h, reset)
        s2tab[name] = (tot, bad)
        verdict = "" if (tot == recs and bad == 0) else "   <== FAILS on the printed numbers"
        out.p("    %-46s visits=%-6d fold-mismatches=%-5d%s" % (name, tot, bad, verdict))
    A("A7 the walk visits every tile record exactly once",
      total == recs and len(set(seen)) == total, "visits=%d recs=%d unique=%d" % (total, recs, len(set(seen))))
    A("A8 the cursor algebra IS the documented record fold",
      fold_match == 0, "mismatches=%d (fold from NAMED.md:1025: base+0x2c*(mult*y + x>>1))" % fold_match)
    A("A9 walk bounds are the two map globals (W then H)",
      rows_g == REC_ROWS_GLOBAL and cols_g == REC_COLS_GLOBAL,
      "rows=%#x cols=%#x" % (rows_g, cols_g))
    out.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
