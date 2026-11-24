#!/usr/bin/env python3
"""M359 - the game nouns of the design record's +0x27 / +0x28 bytes.

M356 left "+0x27/+0x28 index no rule table" as an OPEN end.  This milestone
reads the ONE function that writes the row (0x595b10, the design-record
builder) and its only in-tree caller on the text side (0x579f40, the #UNITS
loader), and derives the field atlas from the instruction stream:

  0x595cc3  mov BYTE PTR [esi+0x98adaf],bl   -> +0x27 <- builder arg 0x1c
  0x595cc9  mov BYTE PTR [esi+0x98adac],dl   -> +0x24 <- arg 0x0c (chassis)
  0x595ccf  mov BYTE PTR [esi+0x98adad],cl   -> +0x25 <- arg 0x10 (weapon)
  0x595cd5  mov BYTE PTR [esi+0x98adae],al   -> +0x26 <- arg 0x14 (armor)
  0x595cdc  mov DWORD PTR [esi+0x98ada8],edi -> +0x20 <- arg 0x18 (abilities)
  0x595ce7  +0x29 <- ret(0x595820)           cost, auto when the column is 0
  0x595d1c  +0x28 <- ret(0x570860) or 0      carry, auto when weapon Mode==7

The #UNITS loader passes SIX stack args; parsed, they are
  (row band, chassis, weapon, armor, ability bits, 1)
-- the 5th design field is the CONSTANT 1 for every basic unit -- and then
writes the alpha.txt columns Plan/Cost/Carry/Icon at +0x2a/+0x29/+0x28/+0x2e.

That gives the nouns:
  +0x28 = carrying capacity  VERIFIED (weapon Mode 7 == Transport per
          alpha.txt #WEAPONS binds the auto-value; the loader's Carry column
          lands in the same byte; 0x570860 = chassis base * reactor).
  +0x27 = reactor level      INFERRED (strong): the only design field not
          bound by an alpha column, constant 1 for all basic units, and it
          enters the HP-thirds scale 10*v/3 (v clamped 1..3), the carry
          multiplier, and the cost call -- the three things a reactor scales.

Two rivals are measured, not asserted from prose:
  R1 "+0x27 is the alpha.txt Plan column" -- FALSE: the loader stores the
     Plan token at +0x2a (and the Planet-Buster branch hard-sets +0x2a=5,
     alpha Plan 5 = Planet Buster) while +0x27 receives a constant.
  R2 "+0x28 has a single writer" (M356 G14) -- FALSE: two writers, one of
     them register-relative (0x57a041 [esi-0xa]) and invisible to the
     literal-form census M356 ran.  M356's row is retracted here.

Static only: objdump listing scratch/m574/text.txt.  No box, Wine or gdb.

    python3 -u scripts/m359_design_record.py            # acceptance
    python3 -u scripts/m359_design_record.py --digest
    SMAC_M359_TEXT=/other/listing ...
"""
import argparse
import hashlib
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("SMAC_M359_TEXT") or os.path.join(ROOT, "scratch", "m574", "text.txt")
ALPHA = os.environ.get("SMAC_M359_ALPHA") or os.path.join(ROOT, "programs", "alpha.txt")
MUT = os.environ.get("SMAC_M359_MUTANT", "")

ROW = 0x98AD88
BUILDER = (0x595B10, 0x595D25)      # design-record builder head (stores)
LOADER = (0x579F40, 0x57A060)       # #UNITS text loader
CARRY_FN = (0x570860, 0x5708A6)     # 0x570860 carrier-capacity formula
COST_FN = (0x595820, 0x595AD0)
HP3 = (0x40F41E, 0x40F460)          # 10*clamp(v,1,3)/3 in the UI health check
PB = (0x595D25, 0x595D60)           # Planet-Buster plan override

INS = re.compile(r"^\s*([0-9a-f]{6,8}):\t([0-9a-f ]+)\t(.*)$")
REGS32 = ("eax", "ecx", "edx", "ebx", "esp", "ebp", "esi", "edi")
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
        a = int(ad, 16)
        t = self.at.get(a)
        if t is None or t.count(old) != 1:
            raise SystemExit("PATCH REJECTED: 0x%x %r not unique in %r" % (a, old, t))
        self.at[a] = t.replace(old, new, 1)

    def window(self, lo, hi):
        return [(a, self.at[a]) for a in self.order if lo <= a < hi]

    def prev(self, a, n=1):
        i = self.order.index(a)
        return [(self.order[j], self.at[self.order[j]]) for j in range(max(0, i - n), i)]

    def after(self, a, n=6):
        i = self.order.index(a)
        return [(self.order[j], self.at[self.order[j]])
                for j in range(i + 1, min(len(self.order), i + 1 + n))]


def widen(r):
    return R8.get(r, r)


def writes_reg(reg, t):
    """True if the instruction writes the 32-bit register (a def, not a read)."""
    m = re.match(r"([a-z]+)\s", t)
    if not m:
        return False
    op, rest = m.group(1), t[m.end():]
    if op in ("call", "jmp", "push", "cmp", "test"):
        return False
    if op.startswith("j"):
        return False
    # one-operand ops whose operand is the destination
    if op in ("inc", "dec", "not", "neg", "pop", "mul", "imul") and "," not in rest:
        return widen(rest.strip()) == reg
    if op in ("imul", "mul") and "," not in rest:
        return reg in ("eax", "edx")
    dst = widen(rest.split(",")[0].strip())
    return dst == reg and "," in rest or (dst == reg and op in ("pop", "inc", "dec", "not", "neg"))


def resolve_arg(L, a, reg8):
    """Where the stored register's value came from: builder arg, call result, or const.

    Def-use, not pattern-scan: the FIRST write to the register seen when walking
    back from the store decides.  A call only counts when the register is eax
    and no other write to eax lies between the call and the store (the review's
    `call; mov al,0; store` counter-example).
    """
    reg = widen(reg8)
    for _pa, pt in reversed(L.prev(a, 16)):
        if writes_reg(reg, pt):
            m = re.match(r"mov %s,DWORD PTR \[ebp\+0x([0-9a-f]+)\]$" % reg, pt)
            if m:
                return "arg 0x" + m.group(1)
            m = re.match(r"mov %s,0x([0-9a-f]+)$" % reg, pt)
            if m:
                return "const 0x" + m.group(1)
            if re.match(r"xor %s,%s$" % (reg, reg), pt):
                return "const 0x0"
            return "other: " + pt
        if pt.startswith("call ") and reg == "eax":
            return "call " + pt.split()[-1]
    return None


def store_reg(t):
    m = re.match(r"mov BYTE PTR \[[^\]]+\],(\w+)$", t)
    return m.group(1) if m else None


def field_users(L):
    """Literal-form reference census for every row byte 0x00..0x33 (one pass)."""
    out = {off: [] for off in range(0x34)}
    for a, t in L.window(0, 0x800000):
        for h in re.findall(r"0x98ad([0-9a-f]{2})", t):
            v = int(h, 16) - 0x88          # row 0x98ad88: absolute low byte - 0x88
            if 0 <= v < 0x34:
                out[v].append(a)
    return out


def anchored_row_stores(L):
    """Byte stores to a row field through a PROVEN row-anchored base register.

    Two anchoring forms are recognised, and only these:
      A  [reg+0x98adXX]  -- reg is a row OFFSET (builder 0x595b10: esi = 13i<<2)
      B  reg <- literal 0x98adXX, advanced only by `add reg,0x34` (loader 0x579f40)
    Returns {field_off: [(addr, text, form)]}.  A store through any other base is
    NOT row-anchored and is not counted (the census is exact for these forms).
    """
    out = {}
    for a, t in L.window(0, 0x800000):
        m = re.match(r"mov BYTE PTR \[(\w+)\+(0x98ad[0-9a-f]{2})\],", t)
        if m:
            off = int(m.group(2), 16) - ROW
            out.setdefault(off, []).append((a, t, "A"))
    for a, t in L.window(0, 0x800000):
        m = re.match(r"mov (\w+),0x(98ad[0-9a-f]{2})$", t)
        if not m:
            continue
        reg, base = m.group(1), int(m.group(2), 16)
        for b, bt in L.after(a, 80):
            if bt.startswith(("ret", "jmp ")):
                break
            if re.match(r"add %s,0x34$" % reg, bt):
                continue
            m2 = re.match(r"mov BYTE PTR \[%s([-+]0x[0-9a-f]+)\]," % reg, bt)
            if m2:
                d = int(m2.group(1).replace("+", ""), 16) if m2.group(1).startswith("+") \
                    else -int(m2.group(1)[3:], 16)
                out.setdefault(base - ROW + d, []).append((b, bt, "B:" + reg))
            elif re.match(r"(mov|lea|add|sub|pop|xor|and|or) %s," % reg, bt) \
                    or re.match(r"(inc|dec) %s$" % reg, bt):
                break
    return out


def alpha_lines(path):
    return open(path, "r", errors="replace").read().replace("\r", "").split("\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--digest", action="store_true")
    args = ap.parse_args()

    L = Listing(TEXT, MUT or None)
    fails = []
    total = [0]

    def gate(name, cond, detail):
        print("%-4s %-40s %s" % ("PASS" if cond else "FAIL", name, detail))
        total[0] += 1
        if not cond:
            fails.append(name)

    # ---- G1 literal-form reference census -------------------------------
    print("== M359 design-record field census (row 0x98ad88, stride 0x34)")
    users = field_users(L)
    print(" %-5s %6s  %s" % ("off", "refs", "first sites"))
    for off in range(0x00, 0x34):
        if users[off]:
            print(" +0x%02x %6d  %s" % (off, len(users[off]),
                                         " ".join("%06x" % a for a in users[off][:6])))
    gate("G1 ref census +0x27=135 +0x28=12",
         len(users[0x27]) == 135 and len(users[0x28]) == 12,
         "+0x27=%d +0x28=%d (M356's independent census: 135/12)"
         % (len(users[0x27]), len(users[0x28])))

    # ---- G2 builder: arg -> field map ----------------------------------
    print("\n== builder 0x595b10: row stores and their source (computed)")
    bmap = {}
    print(" %-8s %-6s %-10s %s" % ("addr", "field", "src", "instruction"))
    for a, t in L.window(*BUILDER):
        if not re.match(r"mov (BYTE|WORD|DWORD) PTR \[esi\+0x98ad", t) or ",esi" in t:
            continue
        m = re.search(r"\[esi\+0x98ad([0-9a-f]{2})\]", t)
        if not m:
            continue
        off = int(m.group(1), 16) - 0x88
        reg = store_reg(t) or t.rsplit(",", 1)[1].strip()
        src = resolve_arg(L, a, reg)
        bmap[off] = src
        print(" %06x +0x%02x  %-10s %s" % (a, off, src or "?", t))
    want = {0x24: "arg 0xc", 0x25: "arg 0x10", 0x26: "arg 0x14",
            0x27: "arg 0x1c", 0x20: "arg 0x18", 0x29: "call 0x595820"}
    got = {k: bmap.get(k) for k in want}
    gate("G2 five component bytes from ONE arg vector",
         got == want,
         "map %s" % {hex(k): v for k, v in sorted(got.items())})

    # ---- +0x28 value path: call 0x570860 or 0 --------------------------
    win28 = dict(L.window(0x595CF8, 0x595D1D))
    carry_call = [a for a, t in win28.items() if t == "call 0x570860"]
    zero = [a for a, t in win28.items() if t == "xor eax,eax"]
    print(" +0x28 value path: call 0x570860 at %s, zero at %s"
          % ([hex(a) for a in carry_call], [hex(a) for a in zero]))

    # ---- G3 loader: six args, the 5th is the constant 1 ----------------
    print("\n== #UNITS loader 0x579f40: stack args in call order")
    pushes = [(a, t) for a, t in L.window(0x57A011, 0x57A022) if t.startswith("push")]
    argsv = list(reversed(pushes))
    for i, (a, t) in enumerate(argsv):
        print(" arg%d (ebp+0x%x): %-22s @%06x" % (i, 8 + 4 * i, t, a))
    calltgt = next((t.split()[-1] for _a, t in L.window(0x57A021, 0x57A027)
                    if t.startswith("call ")), "")
    gate("G3 5th design field is the CONSTANT 1",
         len(argsv) == 6 and argsv[5][1] == "push 0x1"
         and calltgt == "0x595b10" and bmap.get(0x27) == "arg 0x1c",
         "args %s -> call %s ; builder +0x27 <- %s"
         % ([t for _a, t in argsv], calltgt, bmap.get(0x27)))

    # ---- G4 loader: Plan/Cost/Carry/Icon stores, base 0x98adba --------
    print("\n== loader post-call field stores (base literal + stride)")
    base = [(a, t) for a, t in L.window(*LOADER) if t.startswith("mov esi,")]
    stride = [(a, t) for a, t in L.window(*LOADER) if re.match(r"add esi,0x[0-9a-f]+$", t)]
    stores = [(a, t) for a, t in L.window(0x57A026, 0x57A04F)
              if re.match(r"mov BYTE PTR \[esi-0x[0-9a-f]+\],\w+$", t)]
    fields = {}
    for a, t in stores:
        md = re.search(r"\[esi-0x([0-9a-f]+)\]", t)
        if not md:
            continue
        d = int(md.group(1), 16)
        fields[0x32 - d] = (a, t)
    print(" base %s ; stride %s" % (base, stride))
    for off, (a, t) in sorted(fields.items()):
        print("  +0x%02x @%06x %s" % (off, a, t))
    ok_base = bool(base) and base[0][1] == "mov esi,0x98adba" and \
        bool(stride) and stride[0][1] == "add esi,0x34"
    gate("G4 loader writes Plan+0x2a Cost+0x29 Carry+0x28 Icon+0x2e",
         ok_base and sorted(fields) == [0x28, 0x29, 0x2A, 0x2E],
         "fields %s from base %r stride %r"
         % (sorted(hex(k) for k in fields), base[0][1] if base else None,
            stride[0][1] if stride else None))

    # conditional stores: Plan<0 skips, Cost==0 and Carry==0 skip
    cond = {}
    for off, jcc in ((0x2A, "jl"), (0x29, "je"), (0x28, "je")):
        a = fields[off][0] if off in fields else 0
        pre = list(L.prev(a, 2)) if a else []
        shape = [t for _pa, t in pre]
        tgt_ok = False
        if len(pre) == 2 and shape[0].startswith("test ") and shape[1].startswith(jcc + " "):
            tgt_ok = int(shape[1].split()[-1], 16) == min(
                [b for b in L.order if b > a], default=0)
        cond[off] = tgt_ok
    print(" conditional guard (plan<0 jl / cost==0 je / carry==0 je, jump lands after the store): %s"
          % {hex(k): v for k, v in cond.items()})
    gate("G12 loader stores are conditionally guarded",
         all(cond.values()),
         "plan test+jl over the store, cost/carry test+je over the store")

    # ---- G5 +0x28 writers: anchored-register census --------------------
    anch = anchored_row_stores(L)
    w28 = [a for a, _t, _f in anch.get(0x28, [])]
    lit28 = [a for a, t in L.window(0, 0x800000)
             if re.search(r"mov BYTE PTR \[[^\]]*\+0x98adb0\],", t)]
    print("\n +0x28 writers: literal-form %s ; anchored census %s"
          % ([hex(a) for a in sorted(set(lit28))], [hex(a) for a in sorted(set(w28))]))
    print(" anchored census rows: %s"
          % {hex(k): [hex(x[0]) for x in v] for k, v in sorted(anch.items())})
    gate("G5 +0x28 has TWO writers (M356 said one)",
         sorted(set(w28)) == [0x57A041, 0x595D1C],
         "anchored-register census (disp form + literal base with 0x34 stride) "
         "finds %s" % [hex(a) for a in sorted(set(w28))])

    # ---- G6 transport gate: weapon record +0x02 == 7 -------------------
    g6 = [t for a, t in L.window(0x595CEF, 0x595D00)]
    print("\n carry auto-value gate: %s" % g6)
    gate("G6 auto-carry gated on weapon Mode 7",
         any(t.startswith("cmp BYTE PTR [e") and t.endswith("+0x92b952],0x7") for t in g6)
         and "shl eax,0x4" in " ".join(t for _a, t in L.window(0x595CF0, 0x595CF6))
         and "mov edi,eax" in g6
         and L.at.get(0x595D31, "").startswith("cmp BYTE PTR [edi+0x92b950],0x63"),
         "index<<4 -> weapon row +0x02 == 7 (Transport); same base +0x00 == 99 (Planet Buster)")

    # ---- G7 carrier formula 0x570860 ----------------------------------
    print("\n== carrier formula 0x570860")
    for a, t in L.window(*CARRY_FN):
        print("  %06x %s" % (a, t))
    cf = dict(L.window(*CARRY_FN))
    gate("G7 carry = chassis base * arg (reactor), ability-scaled",
         cf.get(0x57086E, "") == "mov dl,BYTE PTR [ecx+0x92ae81]"
         and cf.get(0x570874, "") == "mov al,BYTE PTR [ecx+0x92ae83]"
         and cf.get(0x57087A, "") == "cmp dl,0x1"
         and cf.get(0x57087F, "") == "imul eax,DWORD PTR [ebp+0x10]"
         and cf.get(0x570886, "") == "test ecx,0x800000"
         and cf.get(0x570891, "") == "sar eax,1"
         and cf.get(0x570893, "") == "test ecx,0x80000"
         and cf.get(0x57089B, "") == "lea eax,[eax+eax*2+0x1]"
         and cf.get(0x5708A2, "") == "sar eax,1",
         "chassis +0x01/+0x03, x arg0x10 when +0x01==1, /2 on 0x800000, (3v+1)/2 on 0x80000")

    # ---- G8 +0x27 compare band: {1,3} ----------------------------------
    loads27 = [a for a, t in L.window(0, 0x800000)
               if re.match(r"mov\w* \w+,BYTE PTR \[[^\]]*0x98adaf\]$", t)]
    imms, sites_band = {}, []
    for a in loads27:
        ml = re.match(r"mov\w* (\w+),", L.at[a])
        if not ml:
            continue
        reg8 = ml.group(1)
        regs = {widen(reg8)}
        hit = []
        for b, t in L.after(a, 4):
            m = re.match(r"mov (\w+),(\w+)$", t)
            if m and m.group(2) in regs:
                regs.add(widen(m.group(1)))
            m = re.match(r"cmp (\w+),0x([0-9a-f]+)$", t)
            if m and widen(m.group(1)) in regs:
                hit.append(int(m.group(2), 16))
        for v in hit:
            imms[v] = imms.get(v, 0) + 1
        if 1 in hit and 3 in hit:
            sites_band.append(a)
    print("\n +0x27 loads %d; compare immediates seen on the loaded reg: %s;"
          " 1-and-3 clamp sites %d" % (len(loads27), imms, len(sites_band)))
    gate("G8 +0x27 band is exactly {1,3}",
         imms == {1: 53, 3: 54} and len(sites_band) == 52 and len(loads27) == 127,
         "loads %d, immediates %s over %d clamp sites (pinned)"
         % (len(loads27), imms, len(sites_band)))

    # ---- G9 10*v/3 chain ----------------------------------------------
    h3 = dict(L.window(*HP3))
    print("\n HP-thirds chain: %s | %s | %s | %s | %s | %s"
          % (h3.get(0x40F43E, ""), h3.get(0x40F441, ""), h3.get(0x40F443, ""),
             h3.get(0x40F448, ""), h3.get(0x40F44A, ""), h3.get(0x40F454, "")))
    chain_in = [t for a, t in L.window(0x40F432, 0x40F43E) if t.startswith("mov eax,")]
    gate("G9 clamp(v)*10/3 chain (HP thirds)",
         h3.get(0x40F43E, "") == "lea ecx,[eax+eax*4]"
         and h3.get(0x40F441, "") == "shl ecx,1"
         and h3.get(0x40F443, "") == "mov eax,0x55555556"
         and h3.get(0x40F448, "") == "imul ecx"
         and h3.get(0x40F44A, "") == "mov eax,edx"
         and h3.get(0x40F454, "") == "shr eax,0x1f"
         and h3.get(0x40F457, "") == "add edx,eax"
         and sorted(chain_in) == ["mov eax,0x1", "mov eax,0x3"],
         "input eax written only by the clamp (%s); lea *5, shl 1, magic /3, imul, sign fixup"
         % sorted(chain_in))

    # ---- G10 plan at +0x2a: Planet Buster override ---------------------
    pb = dict(L.window(*PB))
    print("\n Planet-Buster branch: %s -> %s"
          % (pb.get(0x595D31, ""), pb.get(0x595D3A, "")))
    gate("G10 weapon 99 (Planet Buster) hard-sets +0x2a=5",
         pb.get(0x595D31, "") == "cmp BYTE PTR [edi+0x92b950],0x63"
         and pb.get(0x595D3A, "") == "mov BYTE PTR [esi+0x98adb2],0x5",
         "cmp wep+0x00,99 -> +0x2a <- 5 (alpha Plan 5 = Planet Buster)")

    # ---- G11 +0x2a compared against 12 (max Plan) ----------------------
    p12 = [(a, t) for a, t in L.window(0, 0x800000)
           if re.search(r"cmp BYTE PTR \[\w+\+0x98adb2\],0xc$", t)]
    regs = {}
    for a, t in p12:
        mr = re.search(r"\[(\w+)\+", t)
        if mr:
            regs[mr.group(1)] = regs.get(mr.group(1), 0) + 1
    print(" +0x2a == 12 compares: %d sites by base %s, first %s"
          % (len(p12), regs, [hex(a) for a, _t in p12][:6]))
    gate("G11 +0x2a bounded at 12 (max Plan)", len(p12) == 49,
         "%d sites compare the plan byte with 12 across %d base registers (pinned)"
         % (len(p12), len(regs)))

    # ---- R1: +0x27 is NOT the Plan column ------------------------------
    r1 = (argsv[5][1] == "push 0x1" if len(argsv) > 5 else False) and \
         fields.get(0x2A, (0, ""))[1].endswith(",bl") and pb.get(0x595D3A, "").endswith(",0x5")
    print("\n R1 '+0x27 is the alpha.txt Plan column': loader Plan token -> +0x2a (%s),"
          " builder +0x27 <- constant (%s) -> rival %s"
          % (fields.get(0x2A, (0, "?"))[1], argsv[5][1] if len(argsv) > 5 else "?",
             "FAILS" if r1 else "survives"))
    gate("R1 rival fails on measurement", r1,
         "plan lives at +0x2a, +0x27 gets a literal 1")

    # ---- R2: +0x28 single writer (M356) --------------------------------
    r2 = len(lit28) == 1 and 0x57A041 in [a for a, _t in stores]
    print(" R2 '+0x28 has one writer' (M356 G14): literal census finds %d, the"
          " register-relative store at 0x57a041 is a SECOND -> rival %s"
          % (len(lit28), "FAILS" if r2 else "survives"))
    gate("R2 M356 single-writer retracted", r2, "2 writers, 0x595d1c + 0x57a041")

    # ---- alpha.txt corroboration (printed, never gated) ----------------
    try:
        al = alpha_lines(ALPHA)
        hdr = next((s for s in al if s.startswith("; Name, Chassis, Weapon, Armor")), "")
        mode7 = next((s for s in al if "7=Transport" in s), "")
        plan5 = next((s for s in al if "5  = Planet Buster" in s or "5 = Planet Buster" in s), "")
        reactors = 0
        inr = False
        for s in al:
            if s.startswith("#REACTORS"):
                inr = True
                continue
            if inr and s.startswith("#"):
                break
            if inr and s.strip() and not s.startswith(";"):
                reactors += 1
        print("\n CORROBORATE alpha.txt: %r" % hdr.strip())
        print("   %r ; %r ; #REACTORS rows=%d" % (mode7.strip(), plan5.strip(), reactors))
    except OSError:
        print("\n CORROBORATE alpha.txt absent (game file, not in git)")

    # ---- diagnostic: does any +0x27 reader index a global table? ------
    bases = {}
    for a in loads27:
        for b, t in L.after(a, 8):
            for h in re.findall(r"0x9[0-9a-f]{5}", t):
                v = int(h, 16)
                if not (ROW <= v < ROW + 0x34):
                    bases[hex(v)] = bases.get(hex(v), 0) + 1
    print(" table-index diagnostic (+0x27 used as an index into a global): %s"
          % (bases or "none"))

    blob = "\n".join("%02x %d %s" % (off, len(users[off]),
                                     ",".join("%06x" % a for a in users[off]))
                     for off in users if users[off])
    blob += "\n" + "\n".join("%06x %s" % (a, t) for a, t in L.window(*BUILDER))
    digest = hashlib.sha256(blob.encode()).hexdigest()[:16]
    print("\n DIGEST %s" % digest)
    if args.digest:
        return 0
    total_n = total[0]
    print("\n%s M359: %d/%d gates" % ("PASS" if not fails else "FAIL", total_n - len(fails), total_n))
    if fails:
        print(" failing: " + ", ".join(fails))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
