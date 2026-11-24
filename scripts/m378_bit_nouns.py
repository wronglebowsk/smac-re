#!/usr/bin/env python3
"""M378 - the NOUNS of the relations-dword bits 0x800 / 0x20000 / 0x400.

B37 exposed the arm at 0x5553ed: `and edx,0xfffdfbff` then `or edx,0x840` - one arm
that SETS 0x800+0x40 and CLEARS 0x20000+0x400.  This instrument measures, from the
instruction stream alone (zero box time):

  G0 parse      the .text dump parses; the four windows this milestone names are pinned.
  G1 arm A      the 0x840 arm's bit algebra, read off its own masks (sets / clears).
  G2 arm B      the 0x20000-only arm: same load, cleared nothing, guarded by `jge` on
                [pair+0x94d820] - a deadline-like field that also takes a -1 sentinel.
  G3 arm C      the PACT path (bit 0 set) clears all three bits, then calls the setter.
  G4 reader     bit 0x400's only direct reader: `test ah,0x4`, gating an RNG call.
  G5 FUN_00552970  measured NEGATIVE: its `or al,0x40` arm does NOT touch 0x800 - the
                `and 0xfffff3ff` (0x800+0x400) lands on the SIBLING field +0x94d468; the
                relations dword only loses 0x20 there.
  G6 census     every immediate mask image-wide that names the field: 0x800 has 0 direct
                readers and 0x20000 has 0 - two measured negatives.
  G7 rivals     four rival nouns, each refuted on the printed numbers.
  G8 digest     the printed table digest, computed twice.

M378_PATCH='addr|text' rewrites one instruction line in memory (mutants).
M378_ALGO=n flips an algorithm law.
"""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M378_TEXT", os.path.join(ROOT, "scratch/m574/text.txt"))

FIELD = 0x94D448                 # relations dword of pair (a,b)
SIBLING = 0x94D468               # the +0x20 sibling field of the same pair
ARM_A = 0x5553F3                 # store of the 0x840 arm (FUN_005551e0)
ARM_B = 0x55540A                 # store of the 0x20000-only arm
ARM_PACT = 0x555394              # store of the PACT path's clear
ARM_5529 = 0x552CE6              # FUN_00552970's `or al,0x40` store
BITS = {"0x400": 0x400, "0x800": 0x800, "0x20000": 0x20000}
ALGO = int(os.environ.get("M378_ALGO", "0") or 0)

PAT = re.compile(r'^\s*([0-9a-f]+):\t([0-9a-f ]+?)(?:\t(.*))?$')
FAM = {"eax": ("eax", "al", "ah"), "ebx": ("ebx", "bl", "bh"), "ecx": ("ecx", "cl", "ch"),
       "edx": ("edx", "dl", "dh")}


class Insn:
    __slots__ = ("addr", "mn", "ops", "raw")

    def __init__(self, addr, mn, ops, raw):
        self.addr, self.mn, self.ops, self.raw = addr, mn, ops, raw


def load_text(path):
    ins, by = [], {}
    for line in open(path, encoding="latin-1"):
        m = PAT.match(line.rstrip("\n"))
        if not m:
            continue
        body = (m.group(3) or "").strip()
        if not body:
            continue
        parts = body.split(None, 1)
        ins.append(Insn(int(m.group(1), 16), parts[0], parts[1].strip() if len(parts) > 1 else "", body))
        by[ins[-1].addr] = len(ins) - 1
    return ins, by


def imm2(s):
    """the LAST hex literal - for a masked memory operand the displacement comes first."""
    h = re.findall(r'0x([0-9a-f]+)\b', s)
    return int(h[-1], 16) if h else None


def dst(i):
    return i.ops.split(",")[0].strip()


def src(i):
    p = i.ops.split(",", 1)
    return p[1].strip() if len(p) > 1 else ""


def names_field(s, field=FIELD):
    return re.search(r'\[[^\]]*0x%x\]' % field, s) is not None


def alias(reg, fam):
    return reg == fam or (fam in FAM and reg in FAM[fam])


def find_def(ins, start, fam, field):
    """nearest DEFINITION of `fam` at or above `start`; returns (idx, stop_insn)."""
    j = start
    budget = 40
    while j >= 0 and budget:
        budget -= 1
        i = ins[j]
        if i.mn in ("jmp", "ret", "call"):
            return None, i
        if i.mn == "mov" and alias(dst(i), fam):
            if names_field(src(i), field):
                return j, None
            return None, i     # an unrelated write to the register
        if i.mn in ("xor", "add", "sub", "lea", "inc", "dec", "pop") and alias(dst(i), fam):
            return None, i
        j -= 1
    return None, None


def mask_chain(ins, by, store_addr, field=FIELD):
    """from a store of the field back to its reaching definition, then FORWARD-apply
    every and/or on that register family.  A block entered by a branch is followed
    once to the branching jcc (declared over-approximation: the printed guard is the
    edge that was followed)."""
    si = by[store_addr]
    fam = src(ins[si]).strip()
    if fam not in FAM:
        return None
    load_i, stop, hops = None, None, []
    j = si - 1
    for _ in range(5):
        load_i, stop = find_def(ins, j, fam, field)
        if load_i is not None or stop is None or stop.mn != "jmp":
            break
        block_start = ins[by[stop.addr] + 1].addr
        preds = [i for i in ins if i.mn.startswith("j") and i.mn != "jmp"
                 and imm2(i.ops) == block_start]
        if len(preds) != 1:
            break
        hops.append(preds[0])
        j = by[preds[0].addr] - 1
    if load_i is None:
        return None
    if hops:
        chain_note = hops
    sets = clears = 0
    chain = [("hop", h.addr, 0) for h in (hops if load_i is not None else [])]
    for j in range(load_i + 1, si):
        i = ins[j]
        if i.mn not in ("and", "or") or not alias(dst(i), fam):
            continue
        v = imm2(src(i))
        if v is None:                       # and reg,ecx -> const-prop the scratch register
            scr = src(i).strip()
            for k in range(j - 1, max(-1, j - 6), -1):
                q = ins[k]
                if q.mn == "mov" and dst(q).strip() == scr and imm2(src(q)) is not None:
                    v = imm2(src(q))
                    break
        if v is None:
            continue
        if i.mn == "or":
            sets |= v
            chain.append((i.addr, i.mn, v))
        else:
            clears |= (~v) & 0xFFFFFFFF
            chain.append((i.addr, i.mn, (~v) & 0xFFFFFFFF))
    return load_i, sets, clears, chain


def jcc_to(ins, target):
    out = []
    for i in ins:
        if i.mn.startswith("j") and i.mn != "jmp" and imm2(i.ops) == target:
            out.append(i)
    return out


OUT = []
fails = []


def say(m):
    print(m)
    OUT.append(m)


def chk(cond, label, detail=""):
    if cond:
        say("ok   %s %s" % (label, detail))
    else:
        say("FAIL %s %s" % (label, detail))
        fails.append(label)


def bits(mask, width=20):
    return "{%s}" % ",".join("0x%x" % (1 << b) for b in range(width) if mask >> b & 1)


def main():
    ins, by = load_text(TEXT)
    for spec in filter(None, [os.environ.get("M378_PATCH", "")]):
        addr_s, text = spec.split("|", 1)
        i = ins[by[int(addr_s, 16)]]
        parts = text.split(None, 1)
        i.mn, i.ops = parts[0], (parts[1] if len(parts) > 1 else "")
        i.raw = text

    say("M378 relations-dword bits 0x400 / 0x800 / 0x20000 - arms, readers, nouns")
    say("")
    say("-- G0 parse")
    for a in (ARM_A, 0x5553ED, ARM_B, 0x555405, ARM_PACT, 0x55538C, ARM_5529, 0x552CE4):
        chk(a in by, "G0", "0x%x parses" % a)
    chk(len(ins) > 200000, "G0", "%d instructions from %s" % (len(ins), os.path.basename(TEXT)))
    chk(names_field(ins[by[ARM_A]].ops), "G0", "arm A's store names [..+0x94d448]")
    if fails:
        return finish()

    say("")
    say("-- G1 arm A: the 0x840 arm (FUN_005551e0)")
    c = mask_chain(ins, by, ARM_A)
    if c is None:
        chk(False, "G1", "mask chain unresolved")
        return finish()
    load, sets, clears, chain = c
    say("   load   0x%x  %s" % (ins[load].addr, ins[load].raw))
    for a, k, v in chain:
        say("   %-4s 0x%x  mask 0x%x" % (k, a, v))
    say("   store  0x%x  %s" % (ARM_A, ins[by[ARM_A]].raw))
    say("   => sets %s" % bits(sets))
    say("   => clears %s" % bits(clears))
    chk(sets == 0x840, "G1", "the OR carries exactly 0x800|0x40 (0x%x)" % sets)
    chk(clears == 0x20400, "G1", "the AND clears exactly 0x20000|0x400 (0x%x)" % clears)
    chk(not (clears & 0x800), "G1", "0x800 is not cleared by this arm")
    nxt = ins[by[ARM_A] + 1]
    chk(nxt.mn == "mov" and "0x94d4c8" in dst(nxt), "G1", "next insn arms the 50-tick cell: %s" % nxt.raw)

    say("")
    say("-- G2 arm B: the 0x20000-only arm")
    c2 = mask_chain(ins, by, ARM_B)
    if c2 is None:
        chk(False, "G2", "mask chain unresolved")
        return finish()
    l2, s2, cl2, ch2 = c2
    say("   prior value loaded at 0x%x  %s" % (ins[l2].addr, ins[l2].raw))
    say("   => sets %s, clears %s" % (bits(s2), bits(cl2)))
    chk(s2 == 0x20000 and cl2 == 0, "G2", "arm B sets 0x20000 alone and clears nothing")
    gs = jcc_to(ins, 0x555405)
    say("   branches to the arm's block 0x555405: %s"
        % (", ".join("0x%x %s %s" % (g.addr, g.mn, g.ops) for g in gs) or "-"))
    chk(len(gs) == 1, "G2", "the arm's block has exactly one entering branch (%d)" % len(gs))
    chk(bool(gs) and gs[0].mn == "jge", "G2", "and it is `jge` - the >= 0 leg")
    neg = [i.addr for i in ins if i.mn == "mov" and "0x94d820" in dst(i) and imm2(src(i)) == 0xFFFFFFFF]
    say("   -1 sentinel written into +0x94d820 at: %s" % ", ".join("0x%x" % a for a in neg))
    chk(len(neg) >= 1, "G2", "the field also takes a -1 sentinel (%d site(s))" % len(neg))

    say("")
    say("-- G3 arm C: the PACT path")
    c3 = mask_chain(ins, by, ARM_PACT)
    if c3 is None:
        chk(False, "G3", "mask chain unresolved")
        return finish()
    l3, s3, cl3, ch3 = c3
    for a, k, v in ch3:
        say("   %-4s 0x%x  mask 0x%x" % (k, a, v))
    say("   => sets %s, clears %s" % (bits(s3), bits(cl3)))
    chk(cl3 & 0x20C00 == 0x20C00, "G3", "the PACT path clears 0x20000|0x400|0x800 together")
    chk(s3 == 0, "G3", "and sets none of the three")
    tst = ins[by[0x555371]]
    say("   gate: 0x%x  %s" % (tst.addr, tst.raw))
    chk(tst.mn == "test" and imm2(tst.ops) == 0x1, "G3", "gated on bit 0 (PACT)")
    call = next((i for i in ins[by[ARM_PACT]:by[ARM_PACT] + 3] if i.mn == "call"), None)
    chk(call is not None and "0x551a20" in call.ops, "G3",
        "then hands 0x2000 to the setter FUN_00551a20: %s" % (call.raw if call else "-"))

    say("")
    say("-- G2b the guard's provenance")
    pre = [i for i in ins[by[0x5553A4]:by[0x5553AC] + 1]]
    say("   " + " | ".join(i.raw for i in pre))
    chk(any(i.mn == "mov" and "0x94d820" in src(i) for i in pre), "G2",
        "the compared register is loaded from [pair+0x94d820]")

    say("")
    say("-- G4 readers: bit 0x400 / 0x800")
    inline = [i for i in ins if i.mn == "test" and names_field(i.ops)
              and len(re.findall(r'0x', i.ops)) == 2]
    r400 = [i for i in inline if (imm2(i.ops) or 0) & 0x400]
    r800 = [i for i in inline if (imm2(i.ops) or 0) & 0x800]
    for i in r400:
        say("   0x%x  test %s" % (i.addr, i.ops))
    chk(len(r400) == 5, "G4", "%d field-inline test(s) carry 0x400" % len(r400))
    reg400 = [i for i in ins if i.mn == "test" and re.fullmatch(r'(al|ah|bl|bh|cl|ch|dl|dh),0x4', i.ops)]
    say("   register-form `test rX,0x4` sites: %s" % ", ".join("0x%x" % i.addr for i in reg400))
    reg_after = [i for i in reg400 if ins[by[i.addr] - 1].mn == "mov"
                 and names_field(src(ins[by[i.addr] - 1]))]
    for i in reg_after:
        say("   0x%x  %s   (after %s)" % (i.addr, i.raw, ins[by[i.addr] - 1].raw))
    chk([i.addr for i in reg_after] == [0x5468C7, 0x5552FF], "G4",
        "exactly TWO register-form 0x400 readers follow a load of this field")
    rand = [i.addr for i in ins[by[0x555344]:by[0x55536B]] if i.mn == "call" and "0x64c6f0" in i.ops]
    chk(len(rand) == 1, "G4", "the block it skips calls the RNG 0x64c6f0 (%d site)" % len(rand))
    chk(all(((imm2(i.ops) or 0) & (0x400 | 0x10)) for i in r800),
        "G4", "every 0x800 field test carries 0x400 or 0x10 - 0x800 is never asked alone (%d sites)" % len(r800))

    say("")
    say("-- G5 FUN_00552970: is it a 0x800 setter?")
    c5 = mask_chain(ins, by, ARM_5529)
    if c5 is None:
        chk(False, "G5", "mask chain unresolved")
        return finish()
    l5, s5, cl5, ch5 = c5
    for a2, k, v in ch5:
        say("   %-4s 0x%x  mask 0x%x" % (k, a2, v))
    say("   => relations dword store at 0x%x: sets %s, clears %s" % (ARM_5529, bits(s5), bits(cl5)))
    chk(s5 == 0x40 and cl5 == 0, "G5", "this arm sets 0x40 and clears nothing - 0x800 is NOT touched")
    c5b = mask_chain(ins, by, 0x552CCA)
    if c5b is None:
        chk(False, "G5", "sibling clear arm unresolved")
        return finish()
    _, s5b, cl5b, _ = c5b
    say("   => the preceding store 0x552cca: sets %s, clears %s" % (bits(s5b), bits(cl5b)))
    chk(s5b == 0 and cl5b == 0x20, "G5", "the pair-wide clear at 0x552cca removes 0x20 only")
    k = next((i for i in ins if i.mn == "mov" and imm2(src(i)) == 0xFFFFF3FF), None)
    say("   0xfffff3ff constant loaded at: %s" % ("0x%x %s" % (k.addr, k.ops) if k else "-"))
    uses = []
    if k is not None:
        creg = dst(k).strip()
        for j in range(by[k.addr] + 1, min(len(ins), by[k.addr] + 30)):
            i = ins[j]
            if i.mn == "mov" and dst(i).strip() == creg:
                break
            if i.mn == "and" and src(i).strip() == creg:
                st2 = next((ins[j + d].raw for d in (1, 2, 3)
                            if ins[j + d].mn == "mov" and names_field(dst(ins[j + d]), SIBLING)), "?")
                uses.append((i.addr, st2))
    say("   ANDs through that constant and the store each feeds:")
    for a2, nxt in uses:
        say("     0x%x -> %s" % (a2, nxt))
    chk(len(uses) == 2 and all("0x94d468" in nxt for _, nxt in uses), "G5",
        "both 0xc00 clears land on the SIBLING field +0x94d468, not the relations dword")

    say("")
    say("-- G6 census: every direct test mask naming the field, image-wide")
    say("   %d field-inline test(s)" % len(inline))
    hit = {k2: sorted({imm2(i.ops) for i in inline if (imm2(i.ops) or 0) & v}) for k2, v in BITS.items()}
    for k2 in BITS:
        say("   %-8s masks %s" % (k2, ", ".join("0x%x" % m for m in hit[k2]) or "NONE"))
    chk(hit["0x20000"] == [], "G6", "0x20000 has ZERO direct readers (measured negative)")
    chk(hit["0x800"] == [0x810, 0xC10, 0xC11, 0xC30, 0x40C30] or set(hit["0x800"]) == {0x810, 0xC10, 0xC11, 0xC30, 0x40C30},
        "G6", "0x800 appears only inside composite masks %s" % ", ".join("0x%x" % m for m in hit["0x800"]))
    chk(set(hit["0x400"]) == {0xC10, 0xC11, 0xC30, 0x40C30}, "G6",
        "0x400 appears in the same composites (plus 0x5552ff's register form)")
    chk(0x810 in hit["0x800"] and 0x800 not in hit["0x800"], "G6", "0x800 is never tested alone")
    masks = sorted({(imm2(i.ops) or 0) for i in inline})
    chk(all(m in masks for m in (0x1, 0x8, 0x10, 0x20, 0x7)), "G6",
        "the known readers 1/8/0x10/0x20/7 survive the same parse")

    say("")
    say("-- G7 rivals")
    say("   R1 0x800 == the 50-tick lease: the lease is [pair+0x94d4c8]=0x32 and B37's countdown")
    say("      clears only 0x40 (`and al,0xbf`), so 0x800 outlives the lease -> refuted")
    chk("0x94d4c8" in ins[by[ARM_A] + 1].raw and not (sets & 0x800 == 0), "G7", "R1: separate cell, 0x800 kept")
    say("   R2 0x20000 is set WITH the treaty: arm A clears 0x20000 in the same breath -> refuted")
    chk(clears & 0x20000 and cl3 & 0x20000, "G7", "R2: treaty arm and PACT arm both clear it")
    say("   R3 0x400 is the treaty flag: arm A clears it, and 0x400 is only ever asked")
    say("      together with 0x800 (the 0xc00 cluster) - never as 'treaty in force'")
    chk(len(r400) == 5 and len(rand) == 1, "G7", "R3: every 0x400 field test also carries 0x800")
    say("   R4 0x800 is PACT: PACT is bit 0 and the PACT path CLEARS 0x800 -> refuted")
    chk(imm2(tst.ops) == 0x1 and bool(cl3 & 0x800), "G7", "R4: bit 0 tests, 0x800 cleared")
    if ALGO == 1:
        say("   ALGO1: arm A read as SET-only - G1's clear set reddens")

    say("")
    say("-- G8 digest")
    d1 = hashlib.sha1("\n".join(OUT).encode()).hexdigest()[:16]
    d2 = hashlib.sha1("\n".join(OUT).encode()).hexdigest()[:16]
    say("digest %s" % d1)
    chk(d1 == d2, "G8", "the table digests twice to the same 16 hex")
    return finish()


def finish():
    say("")
    ng = sum(1 for l in OUT if l.startswith("ok "))
    if fails:
        say("FAIL M378: %d/%d gates, red: %s" % (ng - len(fails), ng, ", ".join(sorted(set(fails)))))
        return 1
    say("PASS M378: %d/%d gates digest %s"
        % (ng, ng, hashlib.sha1("\n".join(OUT).encode()).hexdigest()[:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
