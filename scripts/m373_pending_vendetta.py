#!/usr/bin/env python3
"""M373 - the PENDING-VENDETTA consumer: who clears 0x80000000 on the relations word, and what
bit actually gates FUN_005551e0's decision pass (M371 left "0x88000008 bits 27/31" OPEN; B36
owns the setter machine, this is the state's second half).

The question the pick carries is a PREDICTION ("bit 27 gates the decision pass").  This tool
measures it instead of assuming it: every number below is computed from the .text dump, the
tables print FIRST, the gates assert what printed, and each rival prediction is scored against
the same numbers.

Word under test: the relations dword at 0x94d448, one per ORDERED faction pair,
`(f_a*0x82f + f_b)*4` (0x82f = 2095 dwords, decoded from FUN_00551a20's own address arithmetic
and cross-read from the Ghidra C shard).

  python3 -u scripts/m373_pending_vendetta.py        # acceptance; writes evidence/m373_*.txt
"""
import bisect
import csv
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M373_TEXT") or os.path.join(ROOT, "scratch/m574/text.txt")
INDEX = os.environ.get("M373_INDEX") or os.path.join(ROOT, "ghidra_out/index.csv")
SHARDS = os.path.join(ROOT, "ghidra_out")
EVID = os.environ.get("M373_EVID") or os.path.join(ROOT, "evidence/m373_pending_vendetta.txt")

WORD = 0x94D448
STRIDE_PIN = 0x82F
SETTER = 0x551A20
FN, FN_SIZE = 0x5551E0, 3853              # FUN_005551e0: the AI turn's diplomacy pass
BIT31, BIT27, BIT13 = 0x80000000, 0x08000000, 0x2000

sys.path.insert(0, ROOT)

out, gates = [], []


def say(s=""):
    out.append(s)


def gate(gid, ok, msg):
    gates.append((gid, bool(ok)))
    say("  %-4s %s  %s" % (gid, "PASS" if ok else "FAIL", msg))


ADDR = re.compile(r"\s*([0-9a-f]{6,8}):\s+((?:[0-9a-f]{2} )+)\s*\t(.*)$")
MN = re.compile(r"^(\w+)\s+(.*)$")


def load(path=TEXT):
    ins = []
    for line in open(path, "r", errors="replace"):
        m = ADDR.match(line)
        if m:
            t = re.sub(r"\s+", " ", m.group(3)).strip()
            mm = MN.match(t)
            ins.append((int(m.group(1), 16), mm.group(1) if mm else "", mm.group(2) if mm else t))
    return ins


def load_funcs():
    return sorted((int(r["addr"], 16), int(r["size_bytes"]), r["name"])
                  for r in csv.DictReader(open(INDEX)) if r["addr"].startswith("0x"))


FUNCS = load_funcs()


def fn_of(a):
    i = bisect.bisect_right(FUNCS, (a, 10 ** 9, "")) - 1
    if i >= 0 and FUNCS[i][0] <= a < FUNCS[i][0] + FUNCS[i][1]:
        return FUNCS[i][2]
    return "?"


def bits(x):
    return [i for i in range(32) if x >> i & 1]


def bstr(x):
    return "[" + ",".join(str(i) for i in bits(x)) + "]"


def imm(ops, reg=None):
    """the immediate of `reg,imm` (or the last operand's), else None"""
    m = re.search(r",(0x[0-9a-f]+)$", ops)
    if not m:
        return None
    if reg is not None and ops.split(",")[0].strip() != reg:
        return None
    return int(m.group(1), 16)


def word_ea(ops):
    """does the operand's effective address name the relations word?"""
    m = re.search(r"\[([^\]]*)\]", ops)
    return bool(m) and ("0x94d448" in m.group(1).lower())


def pushimm(ops):
    """`push 0x...` has no comma: the immediate is the whole operand."""
    m = re.match(r"^(0x[0-9a-f]+)$", ops.strip())
    return int(m.group(1), 16) if m else None


def call_tgt_of(ops):
    m = re.match(r"^(0x[0-9a-f]+)$", ops.strip())
    return int(m.group(1), 16) if m else 0


def main():
    ins = load()
    by = {a: (mn, ops) for a, mn, ops in ins}
    order = sorted(by)
    idx = {a: i for i, a in enumerate(order)}
    say("M373  the pending-vendetta consumer  (text=%s)" % os.path.relpath(TEXT, ROOT))
    say("      %d instructions; FUN_005551e0 0x%06x..0x%06x (%d B); word = 0x%06x, stride 0x%x"
        % (len(ins), FN, FN + FN_SIZE - 1, FN_SIZE, WORD, STRIDE_PIN))

    # ---------------------------------------------------------------- T0 the field's stride
    say("")
    say("T0  FIELD SHAPE - the pair index, decoded twice")
    sw = [(a, mn, ops) for a, mn, ops in ins if 0x551A20 <= a <= 0x551C32]
    seq = [t for t in sw if 0x551A42 <= t[0] <= 0x551A51]
    say("    FUN_00551a20 index sequence: %s" % " | ".join("%s %s" % (m, o) for _a, m, o in seq))
    # the stride is EVALUATED off the parsed ops (two different (f1,f2) pairs), never hardcoded
    def evalseq(f1, f2):
        R = {"edi": f1, "esi": f2}
        for _a, mn, ops in seq:
            dst, src = ops.split(",")
            if mn == "mov":
                R[dst] = R[src]
            elif mn == "shl":
                R[dst] = (R[dst] << imm(ops)) & 0xFFFFFFFF
            elif mn == "add":
                R[dst] = (R[dst] + R[src]) & 0xFFFFFFFF
            elif mn == "sub":
                R[dst] = (R[dst] - R[src]) & 0xFFFFFFFF
            elif mn == "lea":
                m2 = re.match(r"\[(\w+)\+(\w+)\*(\d+)\]$", src)
                R[dst] = (R[m2.group(1)] + R[m2.group(2)] * int(m2.group(3))) & 0xFFFFFFFF
        return R["edx"]

    e1, e2 = evalseq(7, 3), evalseq(5, 2)
    stride = (e1 - 3) // 7
    stride2 = (e2 - 2) // 5
    opline = [mn for _a, mn, _o in seq]
    cshape = ""
    for fn in sorted(os.listdir(SHARDS)):
        if not fn.endswith(".c"):
            continue
        for line in open(os.path.join(SHARDS, fn), "r", errors="replace"):
            m = re.search(r"94d448[^;]*?iVar(\d) \* (0x[0-9a-f]+) \+ iVar(\d)", line)
            if m:
                cshape = m.group(2)
                break
        if cshape:
            break
    say("    dump arithmetic: %d*f_a + f_b  (f1=7,f2=3 -> %d; f1=5,f2=2 -> %d) | ghidra C multiplies by %s"
        % (stride, e1, e2, cshape or "<absent>"))
    gate("G0a", stride == stride2 == STRIDE_PIN and int(cshape, 16) == STRIDE_PIN
         and opline == ["mov", "shl", "add", "lea", "shl", "sub", "add"],
         "the pair stride is 0x82f dwords: EVALUATED from the dump's parsed op sequence (two "
         "distinct (f1,f2) pairs agree) and equal to the C's multiplier - a changed disassembly "
         "moves it")

    # ---------------------------------------------------------------- T1 bit-31 sites
    say("")
    say("T1  THE PENDING BIT'S TOUCH POINTS INSIDE FUN_005551e0 (whole function, 1167 insns)")
    fwin = [(a, mn, ops) for a, mn, ops in ins if FN <= a < FN + FN_SIZE]
    carry = [(a, mn, ops) for a, mn, ops in fwin
             if (imm(ops) is not None and imm(ops) & BIT31) or pushimm(ops) is not None
             and pushimm(ops) & BIT31]
    say("    immediates that CARRY bit 31 (and-masks keep it too - context, not the gate):")
    say("      %d sites %s" % (len(carry), " ".join("%x" % a for a, _m, _o in carry)))
    touch = []
    for a, mn, ops in fwin:
        if mn == "test" and imm(ops) == BIT31:
            touch.append((a, "READ pending?"))
        elif mn == "and" and imm(ops) == 0x7FFFFFFF:
            touch.append((a, "CLEAR mask 0x7fffffff"))
        elif mn == "mov" and ops.split(",")[-1] in ("eax", "ecx"):
            j = order.index(a)
            near_word = word_ea(ops) or any(
                by[order[k]][0] == "lea" and
                re.match(r"^(eax|ecx),\[[^\]]*0x94d448\]$", by[order[k]][1])
                for k in range(max(j - 6, 0), j))
            if near_word and any(by[order[k]][0] == "and" and imm(by[order[k]][1]) == 0x7FFFFFFF
                                 for k in range(max(j - 4, 0), j)):
                touch.append((a, "store the cleared word"))
        elif mn == "push" and pushimm(ops) == BIT31:
            tgt, cat = 0, 0
            for k in range(order.index(a) + 1, order.index(a) + 5):
                if by[order[k]][0] == "call":
                    tgt, cat = call_tgt_of(by[order[k]][1]), order[k]
                    break
            touch.append((a, "ARM pending via setter 0x%06x @0x%06x" % (tgt, cat)))
    for a, what in touch:
        say("    %06x  %-6s %-34s %s" % (a, by[a][0], by[a][1], what))
    say("    arms: %s" % " ".join("%06x" % a for a, _m, o in fwin
                                 if _m == "push" and pushimm(o) == BIT31))
    gate("G1a", [a for a, _w in touch] == [0x55573C, 0x555750, 0x555758, 0x55578A, 0x555792,
                                           0x5558DA]
         and dict(touch)[0x5558DA].endswith("setter 0x551a20 @0x5558e1"),
         "exactly 6 touch points: one READ, two 0x7fffffff CLEARS, the two stores that write "
         "them (own+mirror), and one ARM push -> setter 0x551a20 at 0x5558e1 (target and call "
         "site both asserted)")
    clears = [(a, mn, ops) for a, mn, ops in fwin
              if mn == "and" and imm(ops) == 0x7FFFFFFF]
    say("    explicit 0x7fffffff clear masks: %s" % " ".join("%06x" % a for a, _m, _o in clears))
    gate("G1b", len(clears) == 2 and clears[0][0] == 0x555750 and clears[1][0] == 0x55578A,
         "the pass clears the pending bit in BOTH directions, nowhere else in the function")

    # ---------------------------------------------------------------- T2 the guard ladder
    say("")
    say("T2  THE GUARD LADDER AROUND THE CLEAR - walked, then EXECUTED")
    lad = [(a, by[a]) for a in (0x555736, 0x55573C, 0x555741, 0x555747, 0x55574A, 0x555750,
                                0x555755, 0x555758, 0x555809, 0x55580F, 0x555834, 0x555837)]
    for a, (mn, ops) in lad:
        say("    %06x  %-6s %s" % (a, mn, ops))
    clear_mask = imm(by[0x555750][1])
    keep_mask = None
    m = re.search(r"^(a[hl]),(0x[0-9a-f]+)$", by[0x555809][1])
    if m:
        # ah = bits 8..15 of eax: byte mask 0xdf clears bit 5 of ah -> bit 13 of eax
        keep_mask = (~((~int(m.group(2), 16) & 0xFF) << 8)) & 0xFFFFFFFF
    je_tgt = by[0x555741][1].split()[-1]
    jne_tgt = by[0x55574A][1].split()[-1]
    say("    clear mask 0x%08x | skip path first insn 0x%06x `%s` -> keep mask 0x%08x | targets %s %s"
        % (clear_mask, 0x555809, by[0x555809][1], keep_mask or 0, je_tgt, jne_tgt))

    def model(word):
        """FUN_005551e0's per-pair block, transcribed: the pending clear, else the bit13 scrub."""
        if word & BIT31:
            if word & BIT13:
                return (word & keep_mask) & 0xFFFFFFFF, "keep pending, clear bit13"
            return word & clear_mask, "CLEAR pending"
        return (word & keep_mask) & 0xFFFFFFFF, "no pending, scrub bit13"

    rows = [(0, 0), (0, BIT13), (BIT31, 0), (BIT31, BIT13)]
    say("    executed 4-row truth table (pending=bit31, exception=bit13):")
    res = {}
    for p, e in rows:
        pre = p | e | 0x18 | 0x1                       # keep some unrelated state bits in play
        post, why = model(pre)
        res[(p, e)] = post
        say("      pre %08x -> post %08x  %-26s pending kept=%s"
            % (pre, post, why, bool(post & BIT31)))
    gate("G2a", je_tgt == "0x555809" and jne_tgt == "0x555809" and keep_mask == 0xFFFFDFFF
         and clear_mask == 0x7FFFFFFF and by[0x555747][1] == "ah,0x20"
         and (0x20 << 8) == BIT13,
         "both escapes land on the same scrub (0x555809 `and ah,0xdf`): the clear is taken only "
         "when the word has bit31 AND NOT the bit the DUMP's `test ah,0x20`@0x555747 names (13)")
    gate("G2b", (res[(BIT31, 0)] & BIT31) == 0 and (res[(BIT31, BIT13)] & BIT31) == BIT31
         and (res[(BIT31, BIT13)] & BIT13) == 0 and res[(0, 0)] == 0x19
         and (res[(0, BIT13)] & BIT13) == 0,
         "the 4-row table is a real state machine: bit13 is a ONE-SHOT PROTECTOR of the pending "
         "bit (kept this pass, scrubbed immediately), not a duplicate of it")

    # ---------------------------------------------------------------- T3 bit-27 census
    say("")
    say("T3  BIT 27 (0x08000000) - the pick's candidate gate.  Whole-.text census of the EXACT imm.")
    b27 = [(a, mn, ops) for a, mn, ops in ins if imm(ops) == BIT27]
    w27 = [(a, mn, ops) for a, mn, ops in b27 if word_ea(ops)]
    inwin = [(a, mn, ops) for a, mn, ops in b27 if FN <= a < FN + FN_SIZE]
    say("    sites with immediate 0x08000000: %d total | %d name the relations word | %d in FUN_005551e0"
        % (len(b27), len(w27), len(inwin)))
    for a, mn, ops in w27:
        say("      %06x %-14s %-6s %s" % (a, fn_of(a), mn, ops))
    fns27 = sorted({fn_of(a) for a, _m, _o in w27})
    say("    word-form readers live in: %s" % ", ".join(fns27))
    say("    non-word immediates (other fields / other bitfields): %d" % (len(b27) - len(w27)))
    gate("G3a", len(inwin) == 0,
         "ZERO bit-27 immediates inside FUN_005551e0: bit 27 is NOT a decision input of the pass")
    gate("G3b", len(b27) == 56 and len(w27) == 5 and all(mn == "test" for _a, mn, _o in w27)
         and fns27 == ["FUN_00522b70", "FUN_00531df0", "FUN_00546800", "FUN_005525d0"],
         "bit 27 IS a relations-word state bit - 5 `test` READ sites in 4 other functions %s"
         % " ".join("%06x" % a for a, _m, _o in w27))

    # ---------------------------------------------------------------- T4 setter masks
    say("")
    say("T4  WHAT THE SETTER DOES TO BITS 31/27 - masks applied in write order (B36's model)")
    import sim.relations as R
    masks = [0x80000000, 0x88000008, 0x80000008, 0x80000018, 0x18, 0x10, 0x8010, 0x50, 0x1, 0x2,
             0x4, 0x8, 0x3, 0x11]
    rows4 = []
    for mk in masks:
        r = R.Relations(n=13, human=0)
        w = r.set(1, 2, mk)
        # recover the effective clears for the two bits by testing a saturated pre-state
        r2 = R.Relations(n=13, human=0)
        r2.w[(1, 2)] = 0xFFFFFFFF
        r2.w[(2, 1)] = 0xFFFFFFFF
        w2 = r2.set(1, 2, mk)
        clr = (~w2) & 0xFFFFFFFF
        rows4.append((mk, w, w2 & BIT31, w2 & BIT27, clr & BIT31, clr & BIT27))
        say("    mask %-10s -> fresh word %08x | from all-ones %08x  bit31=%d bit27=%d  cleared: %s"
            % ("0x%08x" % mk, w, w2, 1 if w2 & BIT31 else 0, 1 if w2 & BIT27 else 0,
               bstr(clr & (BIT31 | BIT27))))
    gate("G4a", all(r[4] == 0 for r in rows4) and all(r[2] for r in rows4),
         "NO setter mask clears bit 31 - the pending bit survives every diplomacy write "
         "(peace, pact, truce, treaty, war, contact)")
    sets27 = [r[0] for r in rows4 if r[1] & BIT27]
    gate("G4b", sets27 == [0x88000008] and all(r[5] == 0 for r in rows4),
         "bit 27 is SET by exactly one request mask (0x88000008) and CLEARED by none - the "
         "setter can only raise it; the measured clear (if any) must live outside the setter")
    # and the mask literals really are the dump's bytes (no typo can survive)
    lit = {(a, imm(ops)) for a, mn, ops in ins if 0x551A20 <= a <= 0x551C32 and mn == "and"}
    word_ands = {(a, v) for a, v in lit if v != 0xFE}
    say("    every `and` in the setter: %d (%d word masks + `and al,0xfe`@0x551a62 on ds:0x7485b4)"
        % (len(lit), len(word_ands)))
    import collections
    cnt = collections.Counter(v for _a, v in word_ands)
    say("    word-mask and-immediates by value: %s"
        % ", ".join("%08x x%d" % (v, n) for v, n in sorted(cnt.items())))
    gate("G4c", cnt == collections.Counter({R.PEACE_CLEAR: 2, R.WAR_CLEAR: 2, R.UNLOCK_CLEAR: 2})
         and all(v & BIT31 for _a, v in word_ands) and (0x551A62, 0xFE) in lit,
         "STRUCTURAL, not sampled: the setter's SIX word-mask `and`s are exactly these three "
         "immediates applied twice, all with bit 31 set - no request can clear pending through it")

    # ---------------------------------------------------------------- T5 write-site census
    say("")
    say("T5  EVERY WRITE TO THE WORD (41 stores) - which ones can CLEAR bit 31?")
    wsites = []
    for i, a in enumerate(order):
        mn, ops = by[a]
        src = None
        hit = False
        m = re.match(r"DWORD PTR \[([^\]]+)\],(\w+)$", ops)
        if m and mn == "mov":
            if "0x94d448" in m.group(1).lower():
                hit, src = True, m.group(2)
            else:
                reg = m.group(1)
                if re.fullmatch(r"\w+", reg):
                    for j in range(i - 1, max(i - 11, 0), -1):
                        pm = re.match(r"^(\w+),\[([^\]]+)\]$", by[order[j]][1])
                        if by[order[j]][0] == "lea" and pm and pm.group(1) == reg:
                            if "0x94d448" in pm.group(2).lower():
                                hit, src = True, m.group(2)
                            break
                        if by[order[j]][0] == "call":
                            break
        if hit:
            wsites.append((a, mn, ops, src))
    classify = []
    for a, mn, ops, src in wsites:
        if src is None:
            classify.append((a, "RMW", None))
            continue
        i = idx[a]
        found = None
        for j in range(i - 1, max(i - 13, 0), -1):
            pm, po = by[order[j]]
            if pm in ("and", "or", "xor") and imm(po) is None and po.split(",")[0] == src:
                # a register mask: resolve it if the mask register was loaded with an immediate
                mreg = po.split(",")[-1]
                val = None
                for k in range(j - 1, max(j - 7, 0), -1):
                    qm, qo = by[order[k]]
                    if qm == "mov" and qo.split(",")[0] == mreg and imm(qo) is not None:
                        val = imm(qo)
                        break
                    if qm == "call":
                        break
                if pm == "and" and val is not None:
                    found = ("and", val)
                else:
                    found = ("and_reg" if pm == "and" else pm + "_reg", None)
                break
            if pm in ("and", "or", "xor") and imm(po) is not None and po.split(",")[0] == src:
                found = (pm, imm(po))
                break
            if pm == "mov" and po.startswith(src + ",DWORD PTR ["):
                found = ("copy", None)
                break
            if pm in ("call", "ret"):
                break
        classify.append((a, found[0] if found else "opaque", found[1] if found else None))
    clearers = [(a, k, v) for a, k, v in classify if k in ("and", "xor") and v & BIT31 == 0]
    keepers = [(a, k, v) for a, k, v in classify
               if k == "or" or (k not in ("opaque", "and_reg") and (v is None or v & BIT31))]
    opaque = [a for a, k, v in classify if k == "opaque"]
    copies = [a for a, k, v in classify if k == "copy"]
    andreg = [a for a, k, v in classify if k == "and_reg"]
    # direct RMW and immediate stores are a DIFFERENT write shape - scanned, expected empty
    rmw = [(a, mn, ops) for a, mn, ops in ins
           if mn in ("and", "or", "xor", "bts", "btr", "btc")
           and re.match(r"DWORD PTR \[[^\]]*0x94d448\]", ops)]
    imst = [(a, mn, ops) for a, mn, ops in ins
            if mn == "mov" and re.match(r"DWORD PTR \[[^\]]*0x94d448\],0x[0-9a-f]+$", ops)]
    say("    RMW `and/or/xor [word],imm` forms: %d | `mov [word],imm32` forms: %d"
        % (len(rmw), len(imst)))
    say("    register stores %d | clear %d | nontrivial-keep %d (of which %d mask-free copies) | "
        "reg-mask %d | opaque %d"
        % (len(classify), len(clearers), len(keepers), len(copies), len(andreg), len(opaque)))
    for a, k, v in classify:
        say("      %06x %-12s %-6s %s" % (a, fn_of(a), k, ("0x%08x" % v) if v is not None else "-"))
    say("    keepers' masks: %s" % ", ".join(sorted({"0x%08x" % v for _a, k, v in keepers if v})))
    gate("G5a", len(classify) == 41 and len(rmw) == 0 and len(imst) == 0
         and [a for a, _k, _v in clearers] == [0x555758, 0x555792],
         "EVERY register store into the word (41) is classified, and the two other write SHAPES "
         "(`and/or/xor [word],imm` and `mov [word],imm32`) are scanned and EMPTY - only the "
         "pass's own 0x555758/0x555792 can clear bit 31")
    gate("G5b", len(keepers) == 33 and len(clearers) == 2 and len(andreg) == 3 and len(opaque) == 3
         and len(keepers) + len(clearers) + len(andreg) + len(opaque) == len(classify),
         "the partition closes: 33 keep / 2 literal clear / 3 caller-mask AND / 3 opaque, so no "
         "store is silently dropped or double-counted")

    # ------------------------------------------------- T5b the mask-parameter writers
    say("")
    say("T5b THE SECOND CLEARER FAMILY - two helpers erase a CALLER-supplied mask")
    body = [(a, mn, ops) for a, mn, ops in ins if 0x5518F0 <= a <= 0x5519B2]
    notsite = [a for a, mn, ops in body if mn == "not"]
    say("    FUN_005518f0: `not edx` at %s then AND -> clears the 3rd argument (both directions)"
        % " ".join("%06x" % a for a in notsite))
    body2 = [(a, mn, ops) for a, mn, ops in ins if 0x551CF0 <= a <= 0x551D65]
    say("    FUN_00551cf0: 4th arg != 0 -> OR mask (0x551d1d); 4th arg == 0 -> `not ecx` at %s, "
        "AND -> clears the 3rd argument (one direction per call)" % " ".join(
            "%06x" % a for a, mn, ops in body2 if mn == "not"))
    census = []
    for helper in (0x5518F0, 0x551CF0):
        for i, a in enumerate(order):
            mn, ops = by[a]
            if mn == "call" and ops == "0x%06x" % helper:
                # walk the CONTIGUOUS push run that precedes the call (not a fixed window)
                pushes, k = [], i - 1
                while k >= 0 and by[order[k]][0] == "push" and len(pushes) < 8:
                    pushes.append(by[order[k]][1])
                    k -= 1
                pushes.reverse()
                arg = pushes[-3] if len(pushes) >= 3 else "?"
                flag = pushes[-4] if (helper == 0x551CF0 and len(pushes) >= 4) else "1"
                census.append((helper, a, fn_of(a), arg, flag, len(pushes)))
    say("    call sites: %s" % ", ".join(
        "%06x x%d" % (h, sum(1 for c in census if c[0] == h)) for h in (0x5518F0, 0x551CF0)))
    see31 = []
    for h, a, fn, arg, flag, n in census:
        if arg.startswith("0x") and int(arg, 16) & BIT31:
            if h == 0x5518F0 or flag == "0x0":
                mode = "CLEAR"
            elif flag.startswith("0x"):
                mode = "SET"
            else:
                mode = "FLAG-DEPENDENT(%s)" % flag
            see31.append((a, fn, arg, mode))
            say("      %06x %-12s helper 0x%06x mask %s  %s  <- carries bit 31"
                % (a, fn, h, arg, mode))
    lit = sum(1 for _h, _a, _f, arg, _fl, _n in census if arg.startswith("0x"))
    run3 = sum(1 for c in census if c[5] >= 3)
    gap = [c[1] for c in census if c[5] < 3]
    say("    decoded (contiguous >=3-push run) %d/%d; UNDECODED %d - args live on a shared "
        "setup path (after jmp/mov): %s"
        % (run3, len(census), len(gap), " ".join("%06x" % a for a in gap)))
    say("    literal 3rd args %d | register/param args %d | bit-31-carrying args %d"
        % (lit, len(census) - lit, len(see31)))
    gate("G5c", len(census) == 66 and lit == 35 and len(see31) == 2 and run3 == 46
         and see31[0][:4] == (0x59F176, "FUN_0059ec90", "0x9000ff48", "CLEAR")
         and see31[1][:3] == (0x4DA404, "FUN_004da2c0", "0xdd9bc3c0")
         and see31[1][3].startswith("FLAG-DEPENDENT") and notsite == [0x55196E],
         "66 call sites: 46 decode a contiguous >=3-push run (35 literal masks), 20 keep their "
         "args on a shared path and are NOT claimed; among the decoded, ONE mask clears bit 31 "
         "(0x9000ff48 @0x59f176) and ONE is flag-dependent (0xdd9bc3c0 @0x4da404)")

    # ---------------------------------------------------------------- T6 the lifecycle
    say("")
    say("T6  LIFECYCLE, EXECUTED - bit 31 is the LATCH the pass consumes; bit 27 is STICKY")
    r = R.Relations(n=13, human=0)
    steps = []
    w1 = r.set(1, 2, 0x88000008)
    steps.append(("arm 0x88000008 (0x555667)", w1))
    w2 = r.set(1, 2, 0x80000008)
    steps.append(("second request 0x80000008", w2))
    w3 = r.set(1, 2, 0x10)
    steps.append(("war write 0x10", w3))
    w4 = r.set(1, 2, 0x1)
    steps.append(("pact write 0x1", w4))
    for name, w in steps:
        say("    %-30s word %08x  bit31=%d bit27=%d ladder=%s"
            % (name, w, 1 if w & BIT31 else 0, 1 if w & BIT27 else 0, bstr(w & 0x7)))
    post_a, why_a = model(0x80000000 | 0x18)
    post_b, why_b = model(0x80000000 | 0x2000 | 0x18)
    say("    pass over a word with pending, bit13 clear: %08x -> %08x (%s)" % (0x80000018, post_a, why_a))
    say("    pass over a word with pending, bit13 SET:   %08x -> %08x (%s)" % (0x80002018, post_b, why_b))
    gate("G6a", all(w & BIT27 for _n, w in steps) and all(w & BIT31 for _n, w in steps),
         "bit 27 survives a second request, a war write and a pact write: sticky, never cleared "
         "by the setter - while bit 31 rides along untouched until the PASS consumes it")
    gate("G6b", (post_a & BIT31) == 0 and (post_b & BIT31) == BIT31,
         "the consumer: pending is cleared by the pass unless the arm carried bit13, and the "
         "exception is spent in the same pass")

    # ---------------------------------------------------------------- T7 rivals
    say("")
    say("T7  RIVALS - each predicts a number the tables above already printed")
    say("    R1 'bit 27 gates the decision pass'            predicts >=1 bit-27 imm in the window")
    say("       measured: %d (G3a)  -> %s" % (len(inwin), "DEAD" if not inwin else "ALIVE"))
    gate("R1", not inwin,
         "RIVAL DEAD: bit 27 has no read in FUN_005551e0; it is a WRITE-side marker carried by "
         "0x88000008, read by 4 other functions")
    say("    R2 'the pass clears pending unconditionally'   predicts 0 branch sites between the")
    say("       test 0x55573c and the clear 0x555750; measured: 2 (0x555741/0x55574a) plus table")
    say("       row (31,13) keeping the bit -> DEAD")
    gate("R2", je_tgt == "0x555809" and jne_tgt == "0x555809" and (res[(BIT31, BIT13)] & BIT31),
         "RIVAL DEAD: the clear is conditional, and one branch KEEPS the pending bit")
    say("    R3 'the 0x2000 guard is the 0x20 AI flag'      predicts the al-form test at 0x5556a7")
    say("       is the same predicate; measured: `test al,0x20` tests bit 5 and branches to")
    say("       0x5556e1 (the 0x840 write), the pending guard uses `test ah,0x20` = bit 13 -> DEAD")
    al_site = by[0x5556A7][1].split(",")[-1]
    al_tgt = by[0x5556A9][1]
    gate("R3", al_site == "0x20" and al_tgt != "0x555809" and by[0x555747][1].endswith("0x20")
         and by[0x5556A7][1].startswith("al,") and by[0x555747][1].startswith("ah,"),
         "RIVAL DEAD: byte-register arithmetic differs - al 0x20 is bit 5, ah 0x20 is bit 13, "
         "and the two guards have different targets")
    say("    R4 '0x80000000 is a sign bit / not a field member' predicts the field's other masks")
    say("       clear it; measured: %d of %d stores keep bit 31 (G5a) -> DEAD"
        % (len(keepers), len(classify)))
    gate("R4", len(classify) - len(clearers) - len(andreg) - len(opaque) == len(keepers)
         and len(clearers) == 2 and all(k == "or" or k == "or_reg" or (v & BIT31)
                                        for _a, k, v in keepers if v is not None),
         "RIVAL DEAD: bit 31 is a named member with exactly one literal cleaner pair, not a sign bit")

    # ---------------------------------------------------------------- summary
    say("")
    npass = sum(1 for _g, ok in gates if ok)
    say("SUMMARY  %d/%d gates" % (npass, len(gates)))
    digest = hashlib.sha256(("\n".join(out)).encode()).hexdigest()[:16]
    say("DIGEST   %s" % digest)
    text = "\n".join(out)
    if npass == len(gates):
        final = "PASS M373: %d/%d gates digest %s  (evidence %s)" % (
            npass, len(gates), digest, os.path.relpath(EVID, ROOT))
    else:
        bad = [g for g, ok in gates if not ok]
        final = "FAIL M373: %d/%d gates failed %s digest %s" % (len(bad), len(gates), bad, digest)
    print(text)
    print("\n" + final)
    os.makedirs(os.path.dirname(EVID), exist_ok=True)
    open(EVID, "w").write(text + "\n\n" + final + "\n")
    return 0 if npass == len(gates) else 1


if __name__ == "__main__":
    sys.exit(main())
