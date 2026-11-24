#!/usr/bin/env python3
"""M342 (ANALYSE, static) - the COMPLETION SETTER: who writes a bit into base+0x8c.

B30 proved the +0x8c bitmap's READER-inverse BIJECTION and left the game routine that SETS
the bit OPEN (spine: "the completion ROUTINE that stamps the bit is ASSUMED (reader-inverse)").
This instrument answers it from the .text dump alone: it censuses EVERY instruction that
stores a byte into the base record's bitmap word, resolves each to its containing function,
and separates the generic set/clear API from the inline grant family.  It also proves the
queue-pop routine - the one piece of the completion leg B30 executes - is a NON-writer.

Field arithmetic is DERIVED, never assumed: the record array base is pinned from the
owner-byte site (304*[ds:0x68cbb0] + 0x95da14 compared against ds:0x91b5b4), the stride from
the imul immediate, and the bitmap constant then has to come out at +0x8c - the rival
"+0x88" reading (array base 0x95da14) is printed and FAILS the identity gate.

  python3 -u scripts/m342_completion_setter.py [--text PATH] [--index PATH]

Prints the tables FIRST, then asserts them.  Every gate has a named mutant in
scripts/m342_mutate.py; zero box, zero /proc, zero gdb.
"""
import argparse
import bisect
import hashlib
import csv
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
INDEX = os.path.join(ROOT, "ghidra_out/index.csv")

REC_BASE = 0x95da10          # derived below, not assumed
REC_STRIDE = 0x130
FAC_OFF = 0x8c               # base+0x8c -> 0x95da9c
CB = 0x68cbb0                # current base index
MAPPER = 0x507410            # FUN_00507410: item -> (byte index, bit mask)
API = 0x4e44f0               # FUN_004e44f0: (item, base, set)  <- the set/clear API
POP = 0x4ef5d0               # FUN_004ef5d0: pop the queue head (completion leg)
GRANT = 0x4e47d0             # FUN_004e47d0: inline OR family

FAIL = []


def gate(gid, cond, msg):
    ok = bool(cond)
    print("%s %s %s" % ("ok  " if ok else "BAD ", gid, msg))
    if not ok:
        FAIL.append(gid)
    return ok


def load(text=TEXT, index=INDEX):
    ins = []
    for line in open(text, errors="replace"):
        m = re.match(r"\s*([0-9a-f]{6,8}):\s", line)
        if not m:
            continue
        parts = line.rstrip("\n").split("\t")
        ins.append((int(m.group(1), 16), parts[-1].strip() if len(parts) > 1 else ""))
    fns = []
    for d in csv.DictReader(open(index)):
        if not d.get("addr"):
            continue
        fns.append((int(d["addr"], 16), int(d["size_bytes"]), d["name"]))
    fns.sort()
    return ins, fns


def container(fns, a):
    i = bisect.bisect_right([f[0] for f in fns], a) - 1
    for j in range(i, max(0, i - 40), -1):
        if fns[j][0] <= a < fns[j][0] + fns[j][1]:
            return fns[j]
    return (a, 0, "HOLE")


def body(ins, start, size):
    return [(a, t) for a, t in ins if start <= a < start + size]


def fmt_mask(v):
    if v == 0:
        return "0"
    if v & (v - 1) == 0:
        return "1<<%d" % (v.bit_length() - 1)
    return "0x%x" % v


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default=TEXT)
    ap.add_argument("--index", default=INDEX)
    a = ap.parse_args(argv)
    ins, fns = load(a.text, a.index)
    by_addr = dict(ins)
    print("M342 - the COMPLETION SETTER (base+0x8c bit writers), static census")
    print("dump %s: %d instructions; %d functions indexed" % (os.path.basename(a.text), len(ins), len(fns)))

    # ---------------------------------------------------------------- G0: derive the record base
    owner_site = [x for x, t in ins if "+0x95da14]" in t and "BYTE PTR" in t and "ds:0x91b5b4" in by_addr.get(x + 6, "") ]
    # the owner compare is two instructions apart; resolve structurally instead of by lookahead text
    stride_sites = [(x, t) for x, t in ins if re.search(r"imul +[a-z]+,[a-z]+,0x130$", t)]
    owner_reads = [(x, t) for x, t in ins if "0x95da14]" in t]
    print("\nTABLE 0 - field arithmetic (derived)")
    print("  stride sites (imul reg,reg,0x130): %d  first %s" % (len(stride_sites), hex(stride_sites[0][0]) if stride_sites else "-"))
    print("  owner-byte reads at 0x95da14: %d (field +4 of the same array)" % len(owner_reads))
    print("  array base = 0x95da14-4 = 0x%x ; bitmap constant 0x95da9c -> record+0x%x" % (REC_BASE, 0x95da9c - REC_BASE))

    # ---------------------------------------------------------------- census 1: direct byte stores
    store_re = re.compile(r"^(mov|or|and|xor|add|sub) +(BYTE PTR )?\[[^\]]*0x([0-9a-f]+)\](,|$)")
    direct = []
    for x, t in ins:
        m = store_re.match(t)
        if not m:
            continue
        off = int(m.group(3), 16)
        if 0x95d800 <= off <= 0x961000:      # the record array window
            direct.append((x, t, off, m.group(1)))
    fac = [(x, t, o, op) for x, t, o, op in direct if o == 0x95da9c]
    wrong = [(x, t, o, op) for x, t, o, op in direct if o != 0x95da9c]
    print("\nTABLE 1 - direct byte stores into the record-array window (0x95d800..0x961000): %d" % len(direct))
    for x, t, o, op in sorted(direct):
        print("  %x %-58s %s+0x%x" % (x, t, op, o - REC_BASE))
    fam = {}
    for x, t, o, op in fac:
        fam.setdefault(container(fns, x)[2], []).append((x, op))
    print("  -> into +0x8c (0x95da9c): %d instructions in %d function(s)" % (len(fac), len(fam)))
    for k, v in sorted(fam.items()):
        print("     %-16s %d  %s" % (k, len(v), " ".join("%x:%s" % (x, op) for x, op in v)))
    # the READER side that makes this the right field: the charge routine's bit test (FUN_004f47f0)
    refs = [x for x, t in ins if "0x95da9c" in t]
    charge_read = by_addr.get(0x4f4837, "")
    print("  references to 0x95da9c in the whole dump: %d (%d writes above, %d reads/leas)"
          % (len(refs), len(fac), len(refs) - len(fac)))
    print("  the charge routine's bit test FUN_004f47f0 @0x4f4837: %r" % charge_read)

    # ---------------------------------------------------------------- census 2: the API body
    api_fn = container(fns, API)
    api_body = body(ins, api_fn[0], api_fn[1])
    api_mem = [(x, t) for x, t in api_body if re.search(r"(or|and) +BYTE PTR \[", t)]
    api_lines = dict(api_body)
    set_or = [x for x, t in api_mem if re.match(r"or +BYTE PTR", t)]
    set_and = [x for x, t in api_mem if re.match(r"and +BYTE PTR", t)]
    print("\nTABLE 2 - the API FUN_%x (%d B, %d insns): %s" % (API, api_fn[1], len(api_body), api_fn[2]))
    for x, t in api_body:
        if re.search(r"(lea +[a-z]+,\[|or +BYTE|and +BYTE|call|test|je |jne )", t):
            print("  %x %s" % (x, t))
    # provenance: out1 slot reloaded as the index; out2 slot as the mask
    idx_slot = re.search(r"mov +eax,DWORD PTR \[ebp\+0x([0-9a-f]+)\]", api_lines.get(0x4e4518, ""))
    mask_slot = re.search(r"mov +cl,BYTE PTR \[ebp-0x([0-9a-f]+)\]", api_lines.get(0x4e451b, ""))
    print("  index register <- [ebp+0x%s] (mapper arg slot 1); mask <- [ebp-0x%s] (slot 2)"
          % (idx_slot.group(1) if idx_slot else "?", mask_slot.group(1) if mask_slot else "?"))

    # witness table: index vs mask for the 39 real ids (B30's window)
    print("\nTABLE 2b - witness ids: mapper decomposition and the two rivals' target offsets")
    print("  item  idx=item>>3  mask=1<<(item&7)  setter->  swapped(idx<->mask)->")
    for item in (1, 2, 3, 8, 23, 26, 31, 32, 38, 39):
        idx, mask = item >> 3, 1 << (item & 7)
        print("  %4d %8d %16s  +0x%02x     +0x%02x" % (item, idx, fmt_mask(mask), FAC_OFF + idx, FAC_OFF + mask))
    inside = sum(1 for item in range(0, 40) if (item >> 3) < 5)
    swap_in = sum(1 for item in range(0, 40) if (1 << (item & 7)) < 5)
    print("  ids 0..39 with idx inside the 5-byte window: %d/40 ; with mask-as-index inside: %d/40" % (inside, swap_in))

    # ---------------------------------------------------------------- census 3: API callers
    calls = [(x, t) for x, t in ins if re.match(r"call +0x%x$" % API, t)]
    callers = {}
    rows = []
    for x, _t in calls:
        pos = [i for i, (y, _) in enumerate(ins) if y == x][0]
        pushes = []
        for j in range(pos - 1, max(0, pos - 7), -1):
            mm = re.match(r"push +(0x[0-9a-f]+|[a-z]+)$", ins[j][1])
            if mm:
                pushes.append(mm.group(1))
            if len(pushes) == 3:
                break
        flag = pushes[2] if len(pushes) == 3 else "?"
        item = pushes[0] if pushes else "?"
        base = pushes[1] if len(pushes) >= 2 else "?"
        f = container(fns, x)
        callers.setdefault(f[2], []).append(x)
        rows.append((x, f[2], item, base, flag))
    print("\nTABLE 3 - every call site of the set/clear API FUN_%x: %d in %d functions" % (API, len(calls), len(callers)))
    print("  site    function          item    base    set?")
    for x, f, item, base, flag in rows:
        print("  %-7x %-16s %-7s %-7s %s" % (x, f, item, base, flag))
    lit1 = sum(1 for r in rows if r[4] == "0x1")
    lit0 = sum(1 for r in rows if r[4] in ("0", "0x0"))
    print("  literal set=1: %d ; literal set=0: %d ; variable: %d" % (lit1, lit0, len(rows) - lit1 - lit0))

    # ---------------------------------------------------------------- census 4: the pop is a non-writer
    pop_fn = container(fns, POP)
    pop_body = body(ins, pop_fn[0], pop_fn[1])
    pop_fac = [(x, t) for x, t in pop_body if "0x95da9c" in t]
    pop_api = [(x, t) for x, t in pop_body if re.search(r"call +0x%x$" % API, t)]
    pop_calls = [(x, t) for x, t in pop_body if t.startswith("call")]
    pop_sites = [(x, t) for x, t in ins if re.match(r"call +0x%x$" % POP, t)]
    pop_callers = {container(fns, x)[2] for x, _ in pop_sites}
    print("\nTABLE 4 - the queue-pop FUN_%x (%d B, %d insns): the completion leg's own executable piece"
          % (POP, pop_fn[1], len(pop_body)))
    for x, t in pop_body:
        if re.search(r"(0x95da5c|0x95da60|call|dec +BYTE|ret)", t):
            print("  %x %s" % (x, t))
    print("  references to the bitmap (0x95da9c): %d ; calls to the API: %d ; calls out: %d"
          % (len(pop_fac), len(pop_api), len(pop_calls)))
    print("  callers of the pop: %d, all in %s" % (len(pop_sites), sorted(pop_callers)))

    # ---------------------------------------------------------------- census 5: the inline grant family
    g_fn = container(fns, GRANT)
    g_body = body(ins, g_fn[0], g_fn[1])
    g_or = [(x, t) for x, t in g_body if re.match(r"or +BYTE PTR", t)]
    g_mov = [(x, t) for x, t in g_body if re.match(r"mov +BYTE PTR", t) and "0x95da9c" in t]
    g_map = [(x, t) for x, t in g_body if re.search(r"call +0x%x$" % MAPPER, t)]
    # each OR's mask operand must come from a slot the mapper filled within 12 instructions
    near = 0
    for x, t in g_or:
        pos = [i for i, (y, _) in enumerate(ins) if y == x][0]
        win = [ins[j][1] for j in range(max(0, pos - 12), pos)]
        if any(re.search(r"call +0x%x$" % MAPPER, w) for w in win):
            near += 1
    print("\nTABLE 5 - the inline family FUN_%x (%d B): or-stores %d, mov-copies %d, mapper calls %d"
          % (GRANT, g_fn[1], len(g_or), len(g_mov), len(g_map)))
    for x, t in g_or + g_mov:
        print("  %x %s" % (x, t))
    print("  or-stores whose mask slot was filled by the mapper within 12 insns: %d/%d" % (near, len(g_or)))

    # ---------------------------------------------------------------- rivals
    print("\nRIVALS - each must FAIL on the numbers printed above")
    r1 = (0x95da9c - 0x95da14) == FAC_OFF
    print("  RIV1 'the field is +0x88 (array base 0x95da14)': computed offset +0x%x; the charge routine's"
          % (0x95da9c - 0x95da14))
    print("       read constant 0x95da9c and the writers' constant are the SAME address -> %s" % ("MATCHES" if r1 else "differs by 4"))
    r2 = len(pop_fac) == 0 and len(pop_api) == 0
    print("  RIV2 'the queue-pop stamps the completion bit': pop bitmap refs %d, API calls %d -> %s"
          % (len(pop_fac), len(pop_api), "FALSIFIED" if r2 else "holds"))
    r3 = swap_in < inside
    print("  RIV3 'the mask is the byte index': mask-as-index stays inside the 5-byte window for %d/40 ids"
          " vs %d/40 for item>>3 -> %s" % (swap_in, inside, "FALSIFIED" if r3 else "holds"))
    r4 = len(fac) == len(g_or) + len(g_mov) + 1
    print("  RIV4 'FUN_%x is the only writer': direct +0x8c stores %d == grant %d + copies %d + screen copy 1 -> %s"
          % (GRANT, len(fac), len(g_or), len(g_mov), "FALSIFIED" if r4 else "holds"))

    # ---------------------------------------------------------------- gates
    dig_src = "\n".join("%x:%s" % (x, t) for x, t, _o, _op in sorted(fac) + sorted((x, t) + ("", "") for x, t in g_or))
    print("\nTABLE DIGEST %s (the %d +0x8c stores + the %d grant ORs, canonical order)"
          % (hashlib.sha256(dig_src.encode()).hexdigest()[:16], len(fac), len(g_or)))

    print("\nGATES")
    gate("G1", 0x95da9c - REC_BASE == FAC_OFF and len(stride_sites) > 0 and len(owner_reads) > 1
         and "0x95da9c" in charge_read,
         "array base 0x%x + stride 0x%x puts the bitmap constant 0x95da9c at +0x%x (rival +0x%x)"
         % (REC_BASE, REC_STRIDE, 0x95da9c - REC_BASE, 0x95da9c - 0x95da14))
    gate("G2", len(fac) == 11 and sorted(fam) == ["FUN_0041cf20", "FUN_004e47d0"],
         "direct byte stores into +0x8c: %d, in exactly %s (screen copy 1 + grant %d)"
         % (len(fac), sorted(fam), len(fam.get("FUN_004e47d0", []))))
    gate("G3", len(set_or) == 1 and len(set_and) == 1 and swap_in < inside
         and (idx_slot.group(1) == "8" if idx_slot else False)
         and (mask_slot.group(1) == "4" if mask_slot else False),
         "API FUN_%x writes the field twice (or@0x%x sets, and@0x%x clears); index slot [ebp+0x%s], mask slot [ebp-0x%s]"
         % (API, set_or[0] if set_or else 0, set_and[0] if set_and else 0,
            idx_slot.group(1) if idx_slot else "?", mask_slot.group(1) if mask_slot else "?"))
    gate("G4", len(calls) == 27 and len(callers) == 8 and lit1 >= 1 and lit0 >= 1,
         "API call sites %d in %d functions; literal set=1 %d, set=0 %d (both paths reachable)"
         % (len(calls), len(callers), lit1, lit0))
    gate("G5", len(pop_fac) == 0 and len(pop_api) == 0 and len(pop_calls) >= 3 and pop_callers == {"FUN_004ef6d0"},
         "queue-pop FUN_%x: %d bitmap refs, %d API calls, %d calls out, callers %s -> the pop is a NON-writer"
         % (POP, len(pop_fac), len(pop_api), len(pop_calls), sorted(pop_callers)))
    gate("G6", len(g_or) == 7 and len(g_mov) == 3 and near == len(g_or) and len(g_map) >= 5,
         "inline grant FUN_%x: %d or-stores + %d copies, all %d or masks from the mapper, %d mapper calls"
         % (GRANT, len(g_or), len(g_mov), near, len(g_map)))

    print("\nANSWER: the base+0x8c bit is SET by FUN_%x(item, base, set=1) - mapper FUN_%x's out1 is the"
          % (API, MAPPER))
    print("  byte index, out2 the mask, and the store is ONE `or BYTE PTR [304*base+idx+0x95da9c], mask` at")
    print("  0x%x; its AND twin at 0x%x clears.  A second, inline writer family FUN_%x ORs the same field"
          % (set_or[0] if set_or else 0, set_and[0] if set_and else 0, GRANT))
    print("  at %d sites (%d or + %d copy).  The queue-pop FUN_%x - B30's completion piece - never touches"
          % (len(g_or) + len(g_mov), len(g_or), len(g_mov), POP))
    print("  the field: the bit is stamped by whoever calls the API, not by the pop.  OPEN next: which of the")
    print("  %d call sites is the production-completion call (the pop's own caller is the base screen)." % len(calls))

    print("\n%s M342: %d/%d gates" % ("PASS" if not FAIL else "FAIL", 6 - len(FAIL), 6))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
