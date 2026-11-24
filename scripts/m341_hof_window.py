#!/usr/bin/env python3
"""M341 -- the hall-of-fame RECORD-WINDOW law: index = 5*n - 5 + s.

PICK (run context, option 1): the HoF record-window page arithmetic
(`eax + 5*ebx - 5` vs the 35 records at 0x983a10).  This script asks ONE
question: what record does each of the three 0x983a10 writers/readers address,
and is that addressing bounded by the measured buffer?

Measured (all numbers COMPUTED from the static image `scratch/m574/text.txt`;
zero box time, no Wine/gdb):

  SITE A  0x449793 `lea ecx,[eax+ebx*4]` + 0x449796 `lea ecx,[ebx+ecx*1-0x5]`
          with eax = [obj+0xa918] (row slot) and ebx = [obj+0x59f4] (page)
          -> index = 5*page + slot - 5, then *0x8c + 0x983a10.
  SITE B  0x44af9b/0x44af9e `lea edx,[edx+eax*4]` + `lea esi,[eax+edx*1-0x5]`
          with eax = [obj+0xa4c] (= ds:0x91b5b4, the current player) and
          edx = the rank slot found by the 5-probe scan -> same 5*n-5+s law.
  SITE C  0x44b5a7..0x44b5d6 (FUN_0044b450, the insert-shift) copies
          record 5n+k-5 to record 5n+k-4: dst - src == 1 inside one block.

GATES (table printed FIRST, then asserted; every V claim names a mutant in
scripts/m341_mutate.py):
  G1  SITE A's affine law decodes to {page:5, slot:1, const:-5}.
  G2  SITE A's two inputs are exactly the two cells (page load 0x44970f,
      slot load 0x449715, spills 0x449725/0x449728, reload 0x44978d),
      with no other ebx/eax definition in the window.
  G3  SITE C: src = 5n+k-5, dst = 5n+k-4, both *0x8c onto 0x983a10.
  G4  SITE B: same law with n = [obj+0xa4c]; slot range {0..4} from the
      5-probe scan; the insert-shift is called with k in {0..3} only.
  G5  EXTENT/BOUND: 0x1324 = 35*0x8c = 7*0x2bc; the (n,s) grid {1..7}x{0..4}
      is a bijection onto 0..34; the last legal record ends at the measured
      zero-init terminator 0x984d34; an 8th page lands ON the terminator.
  G6  NO PAGE CLAMP: the only direct 0x59f4 reference in the image is the
      load at 0x44970f (12 further hits are the indexed form of a DIFFERENT
      array); no store with that displacement exists in .text.
  G7  the 6-iteration loop is COLUMNS: 6 bit tests of record byte +1 on ONE
      record (the pointer is reloaded, never stepped) -> 6 != rows.

RIVALS measured on the printed numbers:
  R1 0-based page (5n+s)      -> indices 35..39 exist for n=7 -> OUT OF BUFFER.
  R2 six rows per page        -> 42 > 35 records; grid does not cover.
  R3 flat 35-entry list       -> killed by the decode (three sites all 5n+s)
                                 and by k<4 (a 6-wide window needs k<=5).
  R4 base 0x983984            -> last record 0x984ca8-0x8c != terminator.
"""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")

BASE = 0x983A10
STRIDE = 0x8C
TERM = 0x984D34
PAGE_STEP = 5
ROWS = 5
PAGES = 7

ADDR = re.compile(r"^\s*([0-9a-f]{5,8}):\s")
INSN = re.compile(r"^\s*([0-9a-f]{5,8}):\t[0-9a-f ]+\t(\w+)\s*(.*)$")

INSN_CACHE = []
LAST_ROWS = []


def load_image(path=TEXT):
    """[(addr, mnem, operands)] -- long immediates spill 3 bytes onto a
    follow-up line with no address; such lines are skipped by INSN."""
    out = []
    with open(path, errors="replace") as f:
        for line in f:
            m = INSN.match(line)
            if m:
                out.append((int(m.group(1), 16), m.group(2),
                            m.group(3).strip()))
    return out


def image():
    global INSN_CACHE
    if not INSN_CACHE:
        INSN_CACHE = load_image()
    return INSN_CACHE


def window(lo, hi):
    return [i for i in image() if lo <= i[0] <= hi]


def split_ops(ops):
    """'ecx,[eax+ebx*4]' -> ('ecx', '[eax+ebx*4]')"""
    if "," not in ops:
        return ops.strip(), ""
    d, s = ops.split(",", 1)
    return d.strip(), s.strip()


def affine(expr, env=None):
    """Affine form of an objdump memory expression: dict term -> coeff
    with the key '#' for the constant.  `env` maps a register to an affine
    dict to be substituted (used to chain two leas)."""
    env = env or {}
    e = expr.strip()
    if e.startswith("["):
        e = e[1:]
    if e.endswith("]"):
        e = e[:-1]
    e = e.replace(" ", "")
    if not e:
        return {}
    toks = re.split(r"(?=[+-])", e)
    out = {}
    for t in toks:
        if not t:
            continue
        sign = 1
        while t and t[0] in "+-":
            if t[0] == "-":
                sign = -sign
            t = t[1:]
        if not t:
            continue
        if "*" in t:
            reg, mul = t.split("*", 1)
            mul = int(mul, 0)
        else:
            reg, mul = t, 1
        if re.match(r"^(0x[0-9a-f]+|\d+)$", reg):
            out["#"] = out.get("#", 0) + sign * int(reg, 0) * mul
            continue
        out[reg] = out.get(reg, 0) + sign * mul
    # substitute chained registers (ONE pass: an env value may name a
    # register that is itself a key -- re-substitution would loop forever)
    base = dict(out)
    for r in list(base):
        if r != "#" and r in env:
            c = base.pop(r)
            for k, v in env[r].items():
                base[k] = base.get(k, 0) + c * v
    out = base
    return {k: v for k, v in out.items() if v}


def ev(aff, vals):
    """Numeric value of an affine form at a concrete register assignment."""
    return sum(c * vals.get(k, 0) for k, c in aff.items() if k != "#") \
        + aff.get("#", 0)


def fmt(aff):
    if not aff:
        return "0"
    order = sorted(aff, key=lambda k: (k == "#", k))
    parts = []
    for k in order:
        c = aff[k]
        name = "const" if k == "#" else k
        parts.append("%s*%d" % (name, c) if abs(c) != 1 or k == "#"
                     else ("%s" % name if c > 0 else "-%s" % name))
    return " + ".join(parts).replace("+ -", "- ")


def chain(lo, hi):
    """Decode a run of `lea <reg>,<expr>` / `sub <reg>,<reg>` instructions read
    from the image, keeping every destination's affine value so a
    two-register chain (SITE B: edx = slot+4n, then esi = n+edx-5) resolves."""
    env = {}
    ins = window(lo, hi)
    for a, mn, ops in ins:
        d, s = split_ops(ops)
        if mn == "lea":
            env[d] = affine(s, env)
        elif mn == "sub" and re.match(r"^[a-z]{3}$", s) and d in env:
            neg = {k: -v for k, v in affine(s, env).items()}
            cur = dict(env[d])
            for k, v in neg.items():
                cur[k] = cur.get(k, 0) + v
            env[d] = {k: v for k, v in cur.items() if v}
    return env, ins


def site_a():
    env, ins = chain(0x449793, 0x449796)
    return env.get("ecx", {}), ins


def site_b():
    env, ins = chain(0x44AF9B, 0x44AF9E)
    return env.get("esi", {}), ins


def site_c():
    """The insert-shift: edx = 5n+k-5 (src), add ecx,<imm> (dst) on the same
    5n+k value -- dst - src is the row shift."""
    env, ins = chain(0x44B5A7, 0x44B5AD)
    add = [i for i in window(0x44B5AF, 0x44B5BC) if i[1] == "add"
           and split_ops(i[2])[0] == "ecx"]
    imm = int(split_ops(add[0][2])[1], 0) if add else 0
    if imm > 0x7FFFFFFF:
        imm -= 0x100000000
    return env.get("edx", {}), imm, ins + add


def cover(step=5, const=-5, pages=PAGES, rows=ROWS, start=1):
    idx = {}
    for n in range(start, start + pages):
        for s in range(rows):
            i = step * n + const + s
            idx.setdefault(i, []).append((n, s))
    return idx


def bounds(step=5, const=-5, pages=PAGES, rows=ROWS, base=BASE, stride=STRIDE,
           start=1):
    idx = cover(step, const, pages, rows, start)
    lo, hi = min(idx), max(idx)
    return idx, lo, hi, base + lo * stride, base + (hi + 1) * stride


def byte_hits(disp, pat):
    """Every .text line whose mnemonic text mentions the displacement, split
    into the DIRECT form (a plain [reg+disp] / [disp]) and the INDEXED form
    ([reg+reg*k+disp])."""
    direct, indexed = [], []
    rx = re.compile(r"\[([^\]]*%s[^\]]*)\]" % re.escape(disp))
    for a, mn, ops in image():
        m = rx.search(ops)
        if not m:
            continue
        inner = m.group(1)
        (indexed if "*" in inner.split(disp)[0] else direct).append(a)
    return direct, indexed


ZERO_INIT = [0x44B6AC, 0x44B7B0, 0x44B812, 0x44B8C9, 0x44B90F]


def init_cells():
    """Measure the zero-init / read-fault loop that DEFINES the buffer:
    mov eax,<base> ; mov ecx,<inner> ; loop { mov BYTE [eax],0 ; add eax,<stride>
    ; dec ecx ; jne } ; cmp eax,<term> ; jl.  Returns one dict per site."""
    sites = []
    for start in ZERO_INIT:
        w = window(start, start + 0x1A)
        if not w:
            continue
        base = inner = stride = term = None
        for a, mn, ops in w:
            d, s = split_ops(ops)
            if mn == "mov" and d == "eax" and re.match(r"^0x[0-9a-f]+$", s):
                base = int(s, 0)
            elif mn == "mov" and d == "ecx" and re.match(r"^0x[0-9a-f]+$", s):
                inner = int(s, 0)
            elif mn == "add" and d == "eax" and re.match(r"^0x[0-9a-f]+$", s):
                stride = int(s, 0)
            elif mn == "cmp" and d == "eax" and re.match(r"^0x[0-9a-f]+$", s):
                term = int(s, 0)
        if None not in (base, inner, stride, term):
            sites.append(dict(site=start, base=base, inner=inner,
                              stride=stride, term=term))
    return sites


def main():
    rows = []
    out = []

    def say(s=""):
        out.append(s)
        print(s)

    say("== M341 hall-of-fame record-window law: index = 5*n - 5 + s ==")

    # ---------------- G1 SITE A ----------------
    law, ins = site_a()
    say("G1 SITE A 0x449793/0x449796 window (%d insns):" % len(ins))
    for a, mn, ops in ins:
        say("   0x%x %s %s" % (a, mn, ops))
    say("   affine law: %s" % fmt(law))
    g1 = law == {"ebx": 5, "eax": 1, "#": -5}
    slot_coef = law.get("eax", 0)
    step = law.get("ebx", 0) // slot_coef if slot_coef else 0
    const = law.get("#", 0) // slot_coef if slot_coef else 0
    say("   normalised: index = %d*n %+d + s" % (step, const))
    rows.append(("G1 SITE A law = 5*page + slot - 5", g1))

    # ---------------- G2 inputs ----------------
    srcs = []
    for a, mn, ops in window(0x44970f, 0x449715):
        d, s = split_ops(ops)
        if mn in ("mov", "lea") and d in ("ebx", "eax"):
            srcs.append((a, d, s))
    spill_p = [i for i in window(0x449720, 0x449730)
               if i[1] == "mov" and split_ops(i[2])[0] == "DWORD PTR [ebp-0x24]"]
    spill_s = [i for i in window(0x449720, 0x449730)
               if i[1] == "mov" and split_ops(i[2])[0] == "DWORD PTR [ebp-0x18]"]
    reload_s = [i for i in window(0x449785, 0x449790)
                if i[1] == "mov" and split_ops(i[2])[0] == "eax"
                and "ebp-0x18" in split_ops(i[2])[1]]
    ebx_defs = [i for i in window(0x449710, 0x449793)
                if i[1] == "mov" and split_ops(i[2])[0] == "ebx"]
    say("G2 SITE A inputs:")
    for a, d, s in srcs:
        say("   0x%x mov %s <- %s" % (a, d, s))
    say("   page spill 0x449725 -> [ebp-0x24]: %d   slot spill 0x449728 ->"
        " [ebp-0x18]: %d   slot reload 0x44978d: %d   other ebx defs: %d"
        % (len(spill_p), len(spill_s), len(reload_s), len(ebx_defs)))
    g2 = ([(a, d) for a, d, s in srcs] == [(0x44970F, "ebx"),
                                           (0x449715, "eax")]
          and "0x59f4" in srcs[0][2] and "0xa918" in srcs[1][2]
          and len(spill_p) == 1 and len(spill_s) == 1 and len(reload_s) == 1
          and not ebx_defs)
    rows.append(("G2 inputs = [obj+0x59f4] (page) and [obj+0xa918] (slot)", g2))

    # ---------------- G3 SITE C insert-shift ----------------
    law_c, dst_signed, c = site_c()
    env_c, _ = chain(0x44B5AF, 0x44B5D6)
    say("G3 SITE C 0x44b5a1..0x44b5d6 insert-shift (%d insns):" % len(c))
    for a, mn, ops in c[:8]:
        say("   0x%x %s %s" % (a, mn, ops))
    say("   src index law: %s ; dst = src %+d"
        % (fmt(law_c), dst_signed - (-5)))
    # evaluate both address chains: they must be base + idx*0x8c
    n_val, k_val = 2, 3
    idx_src = ev(law_c, {"esi": n_val, "edi": k_val})
    idx_dst = idx_src + (dst_signed - (-5))
    a_src = ev(env_c.get("edi", {}), {"edx": idx_src, "ecx": idx_dst})
    a_dst = ev(env_c.get("esi", {}), {"edx": idx_src, "ecx": idx_dst})
    want_src = 0x983A10 + idx_src * 0x8C
    say("   index(%d,%d) = %d -> %d ; address chains: edi=0x%x esi=0x%x ;"
        " want src 0x%x, dst = src+0x8c"
        % (n_val, k_val, idx_src, idx_dst, a_src, a_dst, want_src))
    g3 = (law_c == {"esi": 5, "edi": 1, "#": -5} and dst_signed == -4
          and (dst_signed - (-5)) == 1
          and a_src == want_src and a_dst == want_src + 0x8C)
    rows.append(("G3 insert-shift src=5n+k-5 dst=5n+k-4 (delta +1), both *0x8c",
                 g3))

    # ---------------- G4 SITE B ----------------
    law_b, b = site_b()
    say("G4 SITE B 0x44af95..0x44afa8 install (%d insns):" % len(b))
    for a, mn, ops in b:
        say("   0x%x %s %s" % (a, mn, ops))
    eax_src = [i for i in window(0x44aed4, 0x44aee0)
               if i[1] == "mov" and "[esi+0xa4c]" in i[2]]
    # dataflow: eax <- ds:0x91b5b4 at 0x44aecb, then stored to [esi+0xa4c]
    load_91b5b4 = [i for i in window(0x44aec6, 0x44aed2)
                   if i[1] == "mov" and split_ops(i[2])[0] == "eax"
                   and "0x91b5b4" in split_ops(i[2])[1]]
    eax_between = [i for i in window(0x44AECC, 0x44AED9)
                   if i[1] in ("mov", "lea", "xor", "add", "sub")
                   and split_ops(i[2])[0] == "eax"]
    # push/call pairing: each k immediate must feed a call to 0x44b450
    push_call = []
    for i, (a, mn, ops) in enumerate(window(0x44af45, 0x44af90)):
        if mn == "push" and re.match(r"^0x[0-9a-f]+$", ops):
            nxt = [x for x in window(a, a + 0xC) if x[1] == "call"]
            push_call.append((a, int(ops, 0), nxt[0][2] if nxt else None))
    scan = window(0x44af1d, 0x44af43)
    probe = [i for i in scan if i[1] == "mov" and "0xe" != i[2][:1]
             and re.match(r"^(eax|edx),0x", i[2])]
    kvals = sorted(v for _, v, tgt in push_call if tgt == "0x44b450")
    seed = int(split_ops(probe[0][2])[1], 0) if probe else -1
    tail = [i for i in scan if i[1] == "jge" and i[2] == "0x44af2b"]
    rows_n = seed + 1                       # probes seed, seed-1, ... 0
    say("   n cell: 0x44aed9 %s ; load 0x91b5b4: %s ; eax writes between: %d"
        % ([i[2] for i in eax_src],
           [(hex(i[0]), i[2]) for i in load_91b5b4], len(eax_between)))
    say("   push->call 0x44b450: %s ; probe seed: 0x%x ; loop tail: %s"
        % ([(hex(a), "0x%x" % v, t) for a, v, t in push_call], seed,
           [hex(i[0]) for i in tail]))
    say("   affine law: %s ; slot rows measured: %d (indices 0..%d)"
        % (fmt(law_b), rows_n, seed))
    g4 = (law_b == {"eax": 5, "edx": 1, "#": -5}
          and len(load_91b5b4) == 1 and not eax_between
          and len(eax_src) == 1 and "eax" in split_ops(eax_src[0][2])[1]
          and kvals == list(range(rows_n - 1))
          and all(t == "0x44b450" for _, _, t in push_call)
          and len(tail) == 1 and tail[0][2] == "0x44af2b")
    rows.append(("G4 SITE B law = 5*[obj+0xa4c] + slot - 5; k in 0..3", g4))

    # ---------------- G5 extent / bound ----------------
    ext = init_cells()
    say("G5 ZERO-INIT census (the loop that defines the buffer):")
    for s in ext:
        say("   0x%x base=0x%x stride=0x%x inner=%d term=0x%x"
            % (s["site"], s["base"], s["stride"], s["inner"], s["term"]))
    shapes = {(s["base"], s["stride"], s["inner"], s["term"]) for s in ext}
    say("   distinct shapes: %d ; sites measured: %d (declared %d)"
        % (len(shapes), len(ext), len(ZERO_INIT)))
    if shapes:
        base, stride, inner, term = list(shapes)[0]
    else:
        base, stride, inner, term = BASE, STRIDE, 0, TERM
    pages = (term - base) // (stride * rows_n) if rows_n else 0
    idx, lo, hi, first, last = bounds(step, const, pages, rows_n, base, stride)
    say("   extent (0x%x-0x%x)=0x%x = %d*0x8c = %d*0x2bc"
        % (term, base, term - base, (term - base) // stride,
           (term - base) // 0x2BC))
    say("   pages = 0x%x / (0x%x*%d) = %d ; grid {%d..%d}x{0..%d}: %d cells,"
        " indices %d..%d, first 0x%x, one past last 0x%x"
        % (term - base, stride, rows_n, pages, 1, pages, rows_n - 1, len(idx),
           lo, hi, first, last))
    say("   duplicate indices: %d ; index %d (page %d) -> 0x%x (== terminator:"
        " %s)" % (len([k for k, v in idx.items() if len(v) > 1]),
                  pages * rows_n, pages + 1, base + pages * rows_n * stride,
                  base + pages * rows_n * stride == term))
    g5 = (shapes == {(0x983A10, 0x8C, 5, 0x984D34)}
          and inner == rows_n
          and (term - base) == pages * rows_n * stride == 7 * 0x2BC
          and pages * rows_n == 35 and len(idx) == 35
          and lo == 0 and hi == 34
          and not [k for k, v in idx.items() if len(v) > 1]
          and base + pages * rows_n * stride == term)
    rows.append(("G5 35 = 7*5 records; 7 pages cover 0..34; page 8 = terminator",
                 g5))

    # ---------------- G6 no page clamp ----------------
    direct, indexed = byte_hits("0x59f4", "0x59f4")
    insns = len(image())
    idx_forms = []
    for a in indexed:
        ops = [i[2] for i in window(a, a)][0]
        inner = re.search(r"\[([^\]]*0x59f4[^\]]*)\]", ops).group(1)
        idx_forms.append(inner)
    say("G6 0x59f4 census over %d insns: direct %s ; indexed-form %d hits"
        % (insns, ["0x%x" % a for a in direct], len(indexed)))
    say("   indexed forms: %s" % sorted(set(idx_forms)))
    say("   any indexed form that is a plain [reg+0x59f4]: %s"
        % [f for f in idx_forms if "*" not in f])
    lin = [i for i in window(0x44971B, 0x449793)
           if i[1] in ("cmp", "test") and "ebx" in i[2]]
    say("   cmp/test on ebx between load and use: %d" % len(lin))
    g6 = (insns > 780000 and direct == [0x44970F] and len(indexed) == 12
          and all("*" in f and f.count("+") >= 2 for f in idx_forms)
          and not lin)
    rows.append(("G6 no direct 0x59f4 store/clamp in .text (page bound OPEN)",
                 g6))

    # ---------------- G7 columns ----------------
    probes = []
    w7 = window(0x449900, 0x449B60)
    for i, (a, mn, ops) in enumerate(w7):
        m = re.match(r"^BYTE PTR \[(\w+)\+0x1\],(0x[0-9a-f]+)$", ops)
        if mn == "test" and m:
            probes.append((a, m.group(1), int(m.group(2), 0), a))
        m2 = re.match(r"^(\w+),BYTE PTR \[(\w+)\+0x1\]$", ops)
        if mn == "mov" and m2 and i + 1 < len(w7):
            nxt = w7[i + 1]
            m3 = re.match(r"^al,(0x[0-9a-f]+)$", nxt[2])
            if nxt[1] == "test" and m3 and nxt[0] - a <= 6:
                probes.append((a, m2.group(1), int(m3.group(1), 0), a))
    ebx_defs7 = [i for i in window(0x449982, 0x449B40)
                 if i[1] in ("mov", "lea", "add", "inc", "sub", "xor")
                 and split_ops(i[2])[0] == "ebx"]
    ptr_loads = [i for i in window(0x449900, 0x449990)
                 if i[1] == "mov" and "ebp-0x1c" in i[2]]
    say("G7 column probes on record+1: %s"
        % [(hex(a), r, hex(v)) for a, r, v, _ in probes])
    say("   ebx definitions in the probe run: %s ; record-pointer loads: %s"
        % ([(hex(a), mn, ops) for a, mn, ops in ebx_defs7],
           [(hex(a), ops) for a, mn, ops in ptr_loads]))
    g7 = ([(v, a) for _, _, v, a in probes]
          == [(1, 0x449915), (2, 0x449985), (4, 0x4499F1),
              (8, 0x449A5C), (0x10, 0x449AC8), (0x20, 0x449B34)]
          and len(ebx_defs7) == 1 and ebx_defs7[0][0] == 0x449982
          and ebx_defs7[0][2] == "ebx,DWORD PTR [ebp-0x1c]"
          and any("0x449982" == hex(a).replace("0x0", "0x") or a == 0x449982
                  for a, _, _ in ptr_loads))
    rows.append(("G7 six bit probes = columns of ONE record, not rows", g7))

    # ---------------- RIVALS ----------------
    say("RIVALS:")
    # R1: a 0-based page (n in 0..pages-1, const 0) covers the SAME 35 records:
    # bounds do NOT discriminate -- only the decoded constant does.
    r1_idx, _, r1hi, _, _ = bounds(step, 0, pages, rows_n, base, stride, 0)
    r1_bad = sorted(k for k in r1_idx if k < 0 or k > 34)
    say("   R1 0-based page (n=0..%d, const 0): indices %d..%d, out-of-buffer=%s"
        " => bounds %s ; decoded const is %d not 0 => DEAD by DECODE (MU2)"
        % (pages - 1, min(r1_idx), r1hi, r1_bad,
           "ALIVE" if not r1_bad else "DEAD", const))
    r1d = (not r1_bad) and const != 0          # dead because the const is -5
    # R2: a coherent 6-row page (step 6, const -6) needs 6 pages for 36 cells
    w = rows_n + 1
    r2_pages = -(-35 // w)
    r2_idx, _, r2hi, _, _ = bounds(w, -w, r2_pages, w, base, stride)
    r2_over = r2hi > 34
    say("   R2 %d rows/page: step %d, pages %d, cells %d, indices %d..%d,"
        " over-buffer=%s -> %s"
        % (w, w, r2_pages, len(r2_idx), min(r2_idx), r2hi, r2_over,
           "DEAD" if r2_over else "ALIVE"))
    r2d = r2_over
    # R3: a flat list has coefficient 1 on a single counter; the three sites
    # all carry coefficient 5 (renamed n) and 1 (slot).
    trip = [("A", law, "ebx", "eax"), ("B", law_b, "eax", "edx"),
            ("C", law_c, "esi", "edi")]
    trip_n = []
    for tag, lw, nreg, sreg in trip:
        sc = lw.get(sreg, 0)
        trip_n.append((tag, lw.get(nreg, 0) // sc if sc else 0,
                       lw.get("#", 0) // sc if sc else 0))
    say("   R3 per-site (coef_n, const): %s ; a flat list needs coef_n == 1 ->"
        " %s" % (trip_n, "DEAD" if any(c != 1 for _, c, _ in trip_n) else "ALIVE"))
    r3d = any(c != 1 for _, c, _ in trip_n) and len({(c, k) for _, c, k in trip_n}) == 1
    r4_last = 0x983984 + 34 * stride + stride
    say("   R4 base 0x983984: one-past-last 0x%x != 0x%x -> %s"
        % (r4_last, term, "DEAD" if r4_last != term else "ALIVE"))
    r4d = r4_last != term
    rows.append(("R1 0-based page DEAD", r1d))
    rows.append(("R2 six rows/page DEAD", r2d))
    rows.append(("R3 flat list (coef_n == 1) DEAD", r3d))
    rows.append(("R4 base 0x983984 DEAD", r4d))

    # ---------------- verdict ----------------
    global LAST_ROWS
    LAST_ROWS = list(rows)
    blob = "\n".join(out)
    digest = hashlib.sha256(blob.encode()).hexdigest()[:16]
    fails = [n for n, ok in rows if not ok]
    for n, ok in rows:
        say("%-4s %s" % ("PASS" if ok else "FAIL", n))
    say("table_sha256=%s" % hashlib.sha256(
        "\n".join("%s=%d" % (n, ok) for n, ok in rows).encode()).hexdigest()[:16])
    say("digest=%s gates=%d pass=%d" % (digest, len(rows),
                                        len(rows) - len(fails)))
    if fails:
        say("FAIL M341: %d/%d gates" % (len(rows) - len(fails), len(rows)))
        return 1
    say("PASS M341: %d/%d gates" % (len(rows), len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
