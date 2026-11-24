#!/usr/bin/env python3
"""M344 (ANALYSE, static) - the COMPLETION CALLER: which caller of the set/clear API stamps a
BUILD-FINISHED facility?

M342 answered "what writes base+0x8c" and left the successor OPEN: of the 27 call sites of
FUN_004e44f0(item, base, set) (16 set=1 / 7 set=0 / 4 variable), which one is the path that
runs when production finishes?  This instrument answers it from the .text dump alone:

  * it re-derives the 27-site set, then resolves EACH item argument down a short dataflow chain
    (push operand -> nearest definition -> stack slot chase, <=4 hops) and classifies the
    terminal source (literal / function parameter / base-record queue window / record field /
    computed / call return);
  * it measures, per call site, whether the enclosing function first READS the same bitmap byte
    (a membership test => a UI toggle) and whether the function calls the queue-pop at all;
  * it then traces the ONE stamp that sits inside a completion block - the inline `or` at
    0x4f0ec0 in FUN_004ef6d0 - and pins the block: mapper(item=edi) -> 304*base(0x68cbb0) fold
    -> or-store, then the item-table row [edi*48 + 0x984d38] and the pop call 0x86 bytes later,
    plus the spend pair (sub [base+0x40], edi).

The RIVALS are printed with their numbers: "an API site is the completion call" (0/27 pass the
queue-provenance + pop-adjacency test), "the pop stamps the bit" (0 bitmap refs), and "the
unnamed region 0x4f3ebc is the completion" (no spend, no item-table row, no pop).

  python3 -u scripts/m344_completion_caller.py [--text PATH] [--index PATH]

Prints the tables FIRST, then asserts them.  Every gate has a named mutant in
scripts/m344_mutate.py; zero box, zero /proc, zero gdb.
"""
import argparse
import bisect
import csv
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
INDEX = os.path.join(ROOT, "ghidra_out/index.csv")

API = 0x4e44f0            # FUN_004e44f0(item, base, set): or BYTE [rec],cl / and
POP = 0x4ef5d0            # FUN_004ef5d0: pop the queue head
MAPPER = 0x507410         # FUN_00507410(item, &idx, &mask)
BITMAP = 0x95da9c         # base record +0x8c
CURBASE = 0x68cbb0        # current base index
ITEMTAB = 0x984d38        # 72 x 48-B item table (M337); +0xc = price (0x984d44)
STAMP = 0x4f0ec0          # the completion block's inline or-store
POP_AT = 0x4f0f46         # its pop call
BLOCK_LO, BLOCK_HI = 0x4f0e90, 0x4f0f50

DIGEST_EXPECT = "034bf0e1a1606d2c"

FAIL = []


def gate(gid, cond, msg):
    ok = bool(cond)
    print("%s %s %s" % ("ok  " if ok else "BAD ", gid, msg))
    if not ok:
        FAIL.append(gid)
    return ok


# ------------------------------------------------------------------------------ loading
def load(text=TEXT, index=INDEX):
    ins = []
    for line in open(text, errors="replace"):
        m = re.match(r"\s*([0-9a-f]{6,8}):\s", line)
        if not m:
            continue
        parts = line.rstrip("\n").split("\t")
        ins.append((int(m.group(1), 16), parts[2].strip() if len(parts) > 2 else ""))
    rows = [r for r in csv.DictReader(open(index)) if r.get("addr")]
    fns = sorted((int(r["addr"], 16), int(r["size_bytes"]), r["name"]) for r in rows
                 if r.get("size_bytes"))
    return ins, fns


def body(ins, f):
    lo, hi = f[0], f[0] + f[1]
    return [(a, t) for a, t in ins if lo <= a < hi]


def container(fns, a):
    for f in fns:
        if f[0] <= a < f[0] + f[1]:
            return f
    return None


def find(ins, addr):
    return dict(ins).get(addr, "")


# ------------------------------------------------------------------------------ operands
WRITE1 = re.compile(r"^(mov|movzx|movsx|lea|add|sub|xor|and|or|imul|inc|dec|shl|shr|sar|neg|not|pop|movsxd)\s+([a-z0-9]+)\s*(,|$)")
CALLEE_SAVED = {"esi", "edi", "ebx"}
QUEUE_WIN = re.compile(r"\+0x95da(5[c-f]|6[0-9a-f]|7[0-7])\b")
BITMAP_READ = re.compile(r"BYTE PTR \[[^\]]*\+0x95da9c\]")
REC_FIELD = re.compile(r"\+0x95da(1[0-9a-f]|2[0-9a-f]|3[0-9a-f]|4[0-9a-f])\b")


def writes_reg(text, reg):
    m = WRITE1.match(text)
    return bool(m and m.group(2) == reg)


def pushes_before(ins, addrs, at, want=3, span=16):
    """The pushes that feed the call at `at`, NEAREST-FIRST (the API is called as
    push set; push base; push item; call = api(item, base, set), so the item is the last
    push - M342's reviewed mapping, reproduced here)."""
    i = bisect.bisect_left(addrs, at)
    out = []
    j = i - 1
    while j >= 0 and len(out) < want and i - j <= span:
        w = ins[j][1]
        if w.startswith("push "):
            out.append((ins[j][0], w[4:].strip()))
        j -= 1
    return out


def classify_src(instr, fn_lo):
    """Classify one definition instruction's SOURCE (not the register)."""
    t = instr
    if re.match(r"^(mov|movzx|movsx|movsxd)\s+[a-z0-9]+,\s*0x[0-9a-f]+$", t):
        return "imm"
    m = re.match(r"^(mov|movzx|movsx|movsxd)\s+[a-z0-9]+,\s*(DWORD|WORD|BYTE) PTR \[([^\]]+)\]$", t)
    if m:
        mem = m.group(3)
        if QUEUE_WIN.search(mem):
            return "QUEUE"
        if re.match(r"ebp\+0x([0-9a-f]+)$", mem):
            return "param"
        if re.match(r"ebp-0x[0-9a-f]+$", mem):
            return "stack"
        if "+0x95da9c" in mem:
            return "bitmap"
        if re.match(r"0x[0-9a-f]+$", mem):
            return "global"
        return "mem"
    if t.startswith("call "):
        return "callret"
    if re.match(r"(lea|imul|shl|shr|sar|add|sub|xor|and|or|neg|not|inc|dec)\b", t):
        return "computed"
    return "other"


def resolve_item(ins, addrs, fn, site, reg):
    """Chain: register -> def -> (stack slot) -> def ... classify the terminal source."""
    chain = []
    cur_addr, cur_reg, hops = site, reg, 0
    while hops < 4:
        i = bisect.bisect_left(addrs, cur_addr) - 1
        defo = None
        while i >= 0 and ins[i][0] >= fn[0] and cur_addr - ins[i][0] < 20000:
            w = ins[i][1]
            if writes_reg(w, cur_reg):
                defo = (ins[i][0], w)
                break
            if w.startswith("call") and cur_reg not in CALLEE_SAVED:
                tgt = w.split()[-1] if len(w.split()) > 1 else "?"
                defo = (ins[i][0], "call %s -> return in %s" % (tgt, cur_reg))
                break
            i -= 1
        if defo is None:
            chain.append((cur_addr, "NO-DEF", "unresolved"))
            return "unresolved", chain
        chain.append((defo[0], defo[1], ""))
        src = classify_src(defo[1], fn[0])
        if src in ("imm", "param", "QUEUE", "bitmap", "global", "mem", "computed", "callret"):
            return src, chain
        # register-to-register move: one more hop
        mm = re.match(r"^mov\s+[a-z0-9]+,\s*([a-z]{2,4})$", defo[1])
        if mm and src == "other":
            cur_reg, cur_addr = mm.group(1), defo[0]
            hops += 1
            continue
        if src == "other":
            return "other", chain
        # stack slot: chase the last store to it
        m = re.search(r"\[(ebp-0x[0-9a-f]+)\]", defo[1])
        if not m:
            return "other", chain
        slot = m.group(1)
        k = bisect.bisect_left(addrs, defo[0]) - 1
        sto = None
        while k >= 0 and ins[k][0] >= fn[0] and defo[0] - ins[k][0] < 20000:
            w = ins[k][1]
            if re.match(r"^mov\s+\w+ PTR \[%s\]," % re.escape(slot), w) or \
               re.match(r"^mov\s+\[%s\]," % re.escape(slot), w):
                sto = (ins[k][0], w)
                break
            k -= 1
        if sto is None:
            chain.append((defo[0], "SLOT " + slot + " NO-STORE", "unresolved"))
            return "unresolved", chain
        chain.append((sto[0], sto[1], "store"))
        if re.match(r"^mov\s+\w+ PTR \[[^\]]+\],0x[0-9a-f]+$", sto[1]):
            return "imm", chain
        m2 = re.search(r",\s*([a-z]{2,4})$", sto[1])
        if not m2:
            return "other", chain
        cur_reg, cur_addr = m2.group(1), sto[0]
        hops += 1
    return "chain-too-long", chain


# ------------------------------------------------------------------------------ main
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default=TEXT)
    ap.add_argument("--index", default=INDEX)
    a = ap.parse_args(argv)

    ins, fns = load(a.text, a.index)
    addrs = [x for x, _ in ins]
    print("M344 completion-caller census: %d instructions, %d functions in the index"
          % (len(ins), len(fns)))

    sites = [x for x, t in ins if re.match(r"call +0x%x$" % API, t)]
    by_fn = {}
    for s in sites:
        f = container(fns, s)
        if f is None:
            print("BAD  site 0x%x has no containing function" % s)
            return 1
        by_fn.setdefault(f[0], []).append(s)
    print("API FUN_%x: %d call sites in %d functions" % (API, len(sites), len(by_fn)))

    # ---------- TABLE 1: the sites, with item provenance + local shape
    rows = []
    print("\nTABLE 1 - the %d API sites: item argument, its dataflow class, and local shape" % len(sites))
    print("  site    function      item        class      set   bitpre pop  chain-terminal")
    for s in sorted(sites):
        f = container(fns, s)
        ps = pushes_before(ins, addrs, s)
        item, base, setv = (ps[0][1] if len(ps) > 0 else "?"), (ps[1][1] if len(ps) > 1 else "?"), \
                           (ps[2][1] if len(ps) > 2 else "?")
        if item.startswith("0x"):
            cls, chain, term = "imm", [], "literal " + item
        elif re.match(r"^[a-z]{2,4}$", item):
            cls, chain = resolve_item(ins, addrs, f, s, item)
            term = chain[-1][1] if chain else "?"
            si = bisect.bisect_left(addrs, s)
            near = [t for _x, t in ins[max(0, si - 14):si]]
            if cls == "imm" and any(re.match(r"(cmp +\w+,0x26|mov +\w+,0x26)$", t) for t in near):
                cls = "clamped"
            elif cls == "imm":
                if any(re.match(r"(inc|dec) +%s$" % re.escape(item), t)
                       for _x, t in ins[max(0, si - 30):si + 30]):
                    cls = "loopctr"
        else:
            cls, chain, term = "other", [], item
        b = body(ins, f)
        bitpre = any(BITMAP_READ.search(t) and abs(x - s) < 0x400 for x, t in b if x < s)
        popc = sum(1 for _x, t in b if re.match(r"call +0x%x$" % POP, t))
        setlbl = setv if setv.startswith("0x") else "var"
        rows.append(dict(site=s, fn=f[0], item=item, cls=cls, base=base, set=setlbl,
                         bitpre=bitpre, pop=popc, chain=chain, term=term))
        print("  %06x  %-13s %-11s %-10s %-5s %-6s %-4s %s"
              % (s, f[2], item, cls, setlbl, "Y" if bitpre else "-", popc, term))

    set1 = [r for r in rows if r["set"] == "0x1"]
    set0 = [r for r in rows if r["set"] == "0x0"]
    var = [r for r in rows if r["set"] not in ("0x0", "0x1")]
    cls_hist = {}
    for r in rows:
        cls_hist[r["cls"]] = cls_hist.get(r["cls"], 0) + 1
    print("\n  set=1 %d ; set=0 %d ; variable %d ; item classes %s"
          % (len(set1), len(set0), len(var), sorted(cls_hist.items())))

    # ---------- M342's push window vs this one: is the shipped 16/7/4 split exact?
    print("\nTABLE 1b - M342's 6-instruction push window re-run against this census's 16-instruction one")
    diverged = []
    for s in sorted(sites):
        f = container(fns, s)
        p_short = pushes_before(ins, addrs, s, span=6)
        p_long = pushes_before(ins, addrs, s, span=16)
        short_flag = p_short[2][1] if len(p_short) == 3 else "?"
        long_flag = p_long[2][1] if len(p_long) == 3 else "?"
        if short_flag != long_flag:
            diverged.append((s, short_flag, long_flag, len(p_short), len(p_long)))
    for s, sf, lf, ns, nl in diverged:
        print("  %06x  M342 reads set=%-4s (3 pushes found: %d) ; 16-insn window reads set=%s"
              " (3 pushes found: %d)  <- the set push sits 7 instructions back" % (s, sf, ns, lf, nl))
    print("  rows where the two windows disagree: %d" % len(diverged))

    # ---------- TABLE 2: the caller functions
    print("\nTABLE 2 - the %d caller functions: shape features (counted) and a role INFERRED from them" % len(by_fn))
    print("  function      size  sites set1 set0 var  bitpre queue itab pop  pred  role (INFERRED)")
    feats = {}
    for f0 in sorted(by_fn):
        f = container(fns, f0)
        b = body(ins, f)
        rs = [r for r in rows if r["fn"] == f0]
        q = sum(1 for _x, t in b if QUEUE_WIN.search(t))
        it = sum(1 for _x, t in b if "0x%x" % ITEMTAB in t or "0x%x" % (ITEMTAB + 0xc) in t)
        popc = sum(1 for _x, t in b if re.match(r"call +0x%x$" % POP, t))
        pred = sum(1 for _x, t in b if re.match(r"call +0x5a6e70$", t))
        bitpre = sum(1 for r in rs if r["bitpre"])
        s1 = sum(1 for r in rs if r["set"] == "0x1")
        s0 = sum(1 for r in rs if r["set"] == "0x0")
        vv = len(rs) - s1 - s0
        if pred:
            role = "set predicate-gated (calls the item checker)"
        elif s1 and s0:
            role = "mixed: set + clear"
        elif s1 and vv:
            role = "set, item from a register"
        elif s1:
            role = "set, literal item"
        elif s0:
            role = "clear only"
        else:
            role = "variable flag only"
        feats[f0] = dict(q=q, it=it, pop=popc, pred=pred, role=role, bitpre=bitpre)
        print("  %-13s %5d %5d %4d %4d %3d %6d %5d %4d %4d %5d  %s"
              % (f[2], f[1], len(rs), s1, s0, vv, bitpre, q, it, popc, pred, role))

    # ---------- TABLE 3: the completion block
    print("\nTABLE 3 - the completion block in the base screen FUN_004ef6d0")
    b = body(ins, container(fns, STAMP))
    blk = [(x, t) for x, t in b if BLOCK_LO <= x <= BLOCK_HI]
    for x, t in blk:
        print("  %06x  %s" % (x, t))
    spend = [(x, t) for x, t in b if 0x4f0ca1 <= x <= 0x4f0caa]
    print("  spend pair:")
    for x, t in spend:
        print("  %06x  %s" % (x, t))
    itrow = [(x, t) for x, t in b if 0x4f0f65 <= x <= 0x4f0f78]
    print("  item-table row consumed after the pop:")
    for x, t in itrow:
        print("  %06x  %s" % (x, t))

    # ---------- TABLE 4: rivals
    cand = [r for r in rows if r["set"] == "0x1" and not r["item"].startswith("0x")]
    cand_ok = [r for r in cand if r["pop"] > 0 or r["cls"] == "QUEUE"]
    print("\nTABLE 4 - rivals, scored on the same printed numbers")
    print("  RIV1 'an API site is the completion call': set=1 sites whose ITEM is a register %d;"
          " of those, queue-provenance or pop-adjacent %d -> %s"
          % (len(cand), len(cand_ok), "SURVIVES" if cand_ok else "FAILS"))
    for r in cand:
        print("       %06x %s item=%s class=%s queue=%s pop-in-fn=%d"
              % (r["site"], container(fns, r["site"])[2], r["item"], r["cls"],
                 "Y" if r["cls"] == "QUEUE" else "N", r["pop"]))
    pop_bit = sum(1 for x, t in body(ins, container(fns, POP)) if "0x95da9c" in t)
    pop_api = sum(1 for x, t in body(ins, container(fns, POP)) if re.match(r"call +0x%x$" % API, t))
    print("  RIV2 'the pop stamps the bit': pop bitmap refs %d, pop->API calls %d -> %s"
          % (pop_bit, pop_api, "SURVIVES" if (pop_bit or pop_api) else "FAILS"))
    gap = [(x, t) for x, t in ins if 0x4f3e80 <= x <= 0x4f3f60]
    gap_spend = [t for x, t in gap if re.match(r"(sub|add)\s+[a-z0-9]+,\s*edi$", t)]
    gap_pop = [x for x, t in gap if re.match(r"call +0x%x$" % POP, t)]
    print("  RIV3 'the unnamed region 0x4f3ebc is the completion': or-stores there %d,"
          " item-table rows %d, pop calls %d, spend pair %d -> %s"
          % (sum(1 for x, t in gap if "0x95da9c" in t), sum(1 for x, t in gap if "0x984d38" in t),
             len(gap_pop), len(gap_spend), "SURVIVES" if (gap_pop and gap_spend) else "FAILS"))

    # ---------- digest
    h = hashlib.sha256()
    for r in rows:
        h.update(("%x|%x|%s|%s|%s|%d|%s" % (r["site"], r["fn"], r["item"], r["cls"], r["set"],
                                            r["bitpre"], r["term"])).encode())
    for x, t in blk:
        h.update(("%x|%s" % (x, t)).encode())
    for x in (0x4f0f40, POP_AT):
        h.update(("%x|%s" % (x, find(ins, x))).encode())
    digest = h.hexdigest()[:16]
    print("\ntable digest sha256[:16] = %s" % digest)

    # ---------- gates
    print("\nGATES")
    mech = len(diverged) == 1 and diverged[0][0] == 0x40dd3c and diverged[0][1] == "?" \
        and diverged[0][2] == "0x0" and diverged[0][3] == 2 and diverged[0][4] == 3
    gate("G1", len(sites) == 27 and len(by_fn) == 8 and len(set1) == 16 and len(set0) == 8
         and len(var) == 3 and mech,
         "27 sites / 8 functions; RE-DERIVED split set=1 %d, set=0 %d, variable %d; the only row"
         " where M342's 6-insn window differs is 0x40dd3c (its set push sits 7 back: set=0x0,"
         " not '?')" % (len(set1), len(set0), len(var)))
    known = {"imm", "callret", "param", "clamped", "loopctr", "QUEUE", "mem", "computed", "global"}
    unresolved = [r for r in rows if r["cls"] not in known]
    want_hist = {"imm": 18, "callret": 3, "clamped": 2, "loopctr": 2, "param": 2}
    gate("G2", not unresolved and cls_hist == want_hist,
         "every item argument resolves and the census is EXACT (%d unresolved/%d): %s"
         % (len(unresolved), len(rows), sorted(cls_hist.items())))
    qch = [r for r in rows if r["cls"] == "QUEUE"]
    gate("G3", len(qch) == 0,
         "0/%d sites take their item from the base record's queue window (+0x4c..+0x77): %s"
         % (len(rows), [hex(r["site"]) for r in qch]))
    want = {0x41c6f8, 0x41d8fc, 0x508c85, 0x508cee}
    have = {r["site"] for r in cand}
    toggle_ok = bool([r for r in cand if r["site"] == 0x41c6f8 and r["bitpre"]
                      and r["cls"] == "callret"
                      and any("0x5f1394" in c[1] for c in r["chain"])])
    loop_ok = bool([r for r in cand if r["site"] == 0x41d8fc and r["cls"] == "loopctr"
                    and feats[r["fn"]]["pred"] > 0])
    clamp_ok = all(any(re.match(r"(cmp\s+\w+,0x26|mov\s+\w+,0x26)$", t)
                       for _x, t in ins[max(0, bisect.bisect_left(addrs, r["site"]) - 14):
                                       bisect.bisect_left(addrs, r["site"])])
                   for r in cand if r["site"] in (0x508c85, 0x508cee))
    gate("G4", have == want and toggle_ok and loop_ok and clamp_ok,
         "exactly %d set=1 sites pass a REGISTER item %s; 41c6f8 = call-return + bitmap pre-read"
         " (toggle), 41d8fc = loop counter under the 0x5a6e70 predicate, 508c85/508cee = the"
         " 1..0x26 clamp" % (len(cand), sorted(hex(x) for x in have)))
    want_blk = ["4f0e90 mov    edi,DWORD PTR [ebp-0x30]",
                "4f0e93 mov    esi,DWORD PTR ds:0x68cbb0",
                "4f0ea1 push   edi",
                "4f0ea2 call   0x507410",
                "4f0eaa lea    eax,[esi+esi*8]",
                "4f0eb0 lea    ecx,[esi+eax*2]",
                "4f0eb3 shl    ecx,0x4",
                "4f0eb6 lea    eax,[ecx+edx*1+0x95da9c]",
                "4f0ebd mov    cl,BYTE PTR [ebp-0x18]",
                "4f0ec0 or     BYTE PTR [eax],cl"]
    got = ["%x %s" % (x, re.sub(r"\s+", " ", t)) for x, t in blk
           if "%x" % x in [w.split()[0] for w in want_blk]]
    norm = lambda s: re.sub(r"\s+", " ", s)
    match = sum(1 for w in want_blk if any(norm(w) == norm(g) for g in got))
    fn_ok = container(fns, STAMP)[2] == "FUN_004ef6d0"
    gate("G5", match == len(want_blk) and fn_ok,
         "stamp block: %d/%d pinned instructions reproduced in %s (mapper item=edi ->"
         " 304*ds:0x68cbb0 fold -> or BYTE [%x])"
         % (match, len(want_blk), container(fns, STAMP)[2], BITMAP))
    edi_free = not [t for x, t in ins if STAMP < x < 0x4f0f65 and writes_reg(t, "edi")]
    g6 = (find(ins, 0x4f0ca4).startswith("sub    esi,edi")
          and find(ins, 0x4f0ca6) == "mov    DWORD PTR [edx+0x40],esi"
          and find(ins, 0x4f0f65) == "lea    ecx,[edi+edi*2]"
          and find(ins, 0x4f0f6a) == "shl    ecx,0x4"
          and find(ins, 0x4f0f6f) == "mov    edx,DWORD PTR [ecx+0x984d38]"
          and edi_free)
    gate("G6", g6,
         "the block spends [edx+0x40] by edi (0x4f0ca4/6; edx == the base record is INFERRED), edi"
         " is unwritten from the stamp to the item-table row (%s), and the row is [edi*48+0x%x]"
         " (0x4f0f65-6f)"
         % ("free" if edi_free else "WRITTEN", ITEMTAB))
    dist = POP_AT - STAMP
    pop_in_callers = sum(feats[f0]["pop"] for f0 in feats)
    ep_ok = (find(ins, POP_AT) == "call   0x4ef5d0"
             and find(ins, 0x4f0f40) == "mov    eax,ds:0x68cbb0"
             and container(fns, POP_AT)[0] == container(fns, STAMP)[0])
    gate("G7", dist == 0x86 and pop_in_callers == 0 and ep_ok,
         "stamp->pop distance 0x%x (0x%x -> 0x%x); pop calls inside the 8 API-caller functions %d"
         % (dist, STAMP, POP_AT, pop_in_callers))
    gate("G8", digest == DIGEST_EXPECT, "digest %s == pinned %s" % (digest, DIGEST_EXPECT))

    if FAIL:
        print("\nFAIL M344: %d/%d gates red %s" % (len(FAIL), 8, FAIL))
        return 1
    print("\nPASS M344: 8/8 gates; digest %s" % digest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
