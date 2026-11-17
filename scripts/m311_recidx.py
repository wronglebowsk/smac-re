#!/usr/bin/env python3
"""M311 - ds:0x68cbb0 is the CURRENT-RECORD INDEX of the 304-B entity record array, and
ds:0x8f0d60 is its derived record POINTER.  Purely static: objdump text + PE bytes are the
arbiter; Ghidra's C is never cited as evidence.  No box time, no /proc, no gdb, no
game-binary load.

The measurement order is fixed: PRINT every table, then assert every number printed.
"""
import os
import re
import sys
import csv
import bisect
import hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m308_site_list as M  # noqa: E402  (the shared parse engine - do not re-implement)

IDX = 0x68cbb0        # the dword under census
PTR = 0x8f0d60        # the record pointer this fire names
LAST = 0x68cbb4       # the neighbouring dword, written with IDX at one site
REC_BASE = 0x95da10   # the 304-B array whose element the pointer is
REC_LEN = 304         # 0x130

# Store sites of ds:IDX, transcribed from `python3 scripts/name_global.py 0x68cbb0`
IDX_STORES = [
    (0x4efe8e, "FUN_004ef6d0", "esi"),
    (0x4f21e0, "FUN_004ef6d0", "edi"),
    (0x4f5a7c, "FUN_004f5a70", "ebx"),
    (0x4f5c36, "FUN_004f5a70", "ebx"),
    (0x4e3476, "FUN_004e3470", "eax"),   # the 11-insn setter, 57 callers
    (0x4e4dd0, "FUN_004e47d0", "esi"),
]
# Store sites of ds:PTR, from `python3 scripts/name_global.py 0x8f0d60`
PTR_STORES = [
    (0x4e348a, "FUN_004e3470", "edx"),
    (0x4e4dd6, "FUN_004e47d0", "ecx"),
    (0x4efea2, "FUN_004ef6d0", "ecx"),
    (0x4f21f9, "FUN_004ef6d0", "ecx"),   # this fire re-found it: the census print scrolled past
    (0x4f5a93, "FUN_004f5a70", "ecx"),   # this fire re-found it: same
    (0x4f5c3c, "FUN_004f5a70", "eax"),
]
SETTER = 0x4e3470
SETTER_END = 0x4e3491
N_IDX_REFS = 340      # printed by name_global.py
N_PTR_REFS = 929


def load():
    ins, order = M.parse_text()
    rows = []
    with open(M.INDEX) as f:
        for r in csv.DictReader(f):
            rows.append((int(r["addr"], 16), r["name"], int(r["size_bytes"]),
                         int(r["n_insns"])))
    rows.sort()
    return ins, order, rows


def win(ins, order, lo, hi):
    a = bisect.bisect_left(order, lo)
    b = bisect.bisect_right(order, hi - 1)
    return [(x, ins[x][0], ins[x][1]) for x in order[a:b]]


def owner(rows, addr):
    i = bisect.bisect_right(rows, (addr, "\xff" * 8, 0, 0)) - 1
    return rows[i][1]


def refs_of(ins, addr):
    """Every instruction in the cache that names this global."""
    pat = "0x%x" % addr
    return [(a, mn, op) for a, (mn, op) in ins.items() if pat in op]


def classify(addr, mn, op):
    """W (a store whose DESTINATION is the global), T (a test), R (a plain read)."""
    head = op.rsplit(",", 1)[0].strip() if "," in op else op.strip()
    if mn.startswith("mov") and ("ds:0x%x" % IDX) in head:
        return "W"
    if mn in ("cmp", "test"):
        return "T"
    return "R"


def fold_chain(body):
    """Recognise the index->byte-offset fold  (n + (n+n*8)*2) << 4  = 304n.

    Returns [(lea9_addr, lea19_addr, shl_addr), ...] for every occurrence in the window.
    The three steps need NOT be adjacent - at 0x4f5a82 the compiler interleaves two pushes -
    so the scan allows arbitrary instructions between them but requires the ORDER, and it
    refuses a match whose steps are more than 24 bytes apart (a wider window would start
    joining folds that belong to the neighbouring store site).
    """
    hits = []
    n = len(body)
    for i in range(n):
        a1, m1, o1 = body[i]
        if not (m1 == "lea" and re.match(r"^\w+,\[\w+\+\w+\*8\]$", o1)):
            continue
        for j in range(i + 1, n):
            a2, m2, o2 = body[j]
            if not (m2 == "lea" and re.match(r"^\w+,\[\w+\+\w+\*2\]$", o2)):
                continue
            for k in range(j + 1, n):
                a3, m3, o3 = body[k]
                if m3 == "shl" and o3.endswith(",0x4") and a3 - a1 <= 24:
                    hits.append((a1, a2, a3))
            if hits and hits[-1][0] == a1:
                break
    return hits


def main():
    ins, order, rows = load()
    out = []
    P = out.append
    P("M311 ds:0x68cbb0 census - the CURRENT-RECORD INDEX and its derived record POINTER")
    P("static only: objdump text cache + index.csv (no box time, no /proc, no gdb)")
    P("")

    # ---- table 1: the store census, with live containment -------------------------
    P("TABLE 1  stores to ds:0x68cbb0 (site, containing function from index.csv, source reg)")
    live_stores = []
    for a, claim_fn, reg in IDX_STORES:
        mn, op = ins[a]
        fn = owner(rows, a)
        live_stores.append((a, fn, reg, mn, op))
        P("  0x%08X  %-14s %-6s  %-9s %s" % (a, fn, reg, mn, op))
    P("  total stores: %d ; distinct functions: %d"
      % (len(live_stores), len({f for _, f, _, _, _ in live_stores})))
    P("")

    idx_reads = refs_of(ins, IDX)   # every instruction naming the index (kinded in table 4)

    # ---- table 2: the pointer's stores, and where they sit relative to table 1 -----
    P("TABLE 2  stores to ds:0x%x, paired to their nearest PRECEDING ds:0x%x store" % (PTR, IDX))
    idx_wsites = sorted(a for a, mn, op in idx_reads
                        if mn.startswith("mov") and ("ds:0x%x" % IDX) in op.rsplit(",", 1)[0])
    ptr_wsites = sorted(a for a, mn, op in refs_of(ins, PTR)
                        if mn.startswith("mov") and ("ds:0x%x" % PTR) in op.rsplit(",", 1)[0])
    pairs = []
    for pa in ptr_wsites:
        pre = [i for i in idx_wsites if i < pa]
        fn = owner(rows, pa)
        reg = ins[pa][1].rsplit(",", 1)[1].strip()
        d = pa - pre[-1] if pre else None
        pairs.append((pa, fn, reg, pre[-1] if pre else None, d))
        P("  ptr 0x%08X  %-14s src %-4s   idx store %s  +%s B"
          % (pa, fn, reg, hex(pre[-1]) if pre else "NONE", d))
    P("  index stores %d / pointer stores %d -> unpaired index stores: %s"
      % (len(idx_wsites), len(ptr_wsites),
         [hex(i) for i in idx_wsites if not any(i < p <= i + 32 for p in ptr_wsites)] or "none"))
    P("")

    # ---- table 3: the fold identity ------------------------------------------------
    P("TABLE 3  the index->pointer fold, per site (must be n*19*16 + 0x95da10 = n*304)")
    folds = {}
    for site, fn, reg in [(0x4e3476, "FUN_004e3470", "eax"),
                          (0x4efe8e, "FUN_004ef6d0", "esi"),
                          (0x4f5a7c, "FUN_004f5a70", "ebx")]:
        body = win(ins, order, site - 24, site + 34)
        f = fold_chain(body)
        folds[site] = f
        add = [(a, o) for a, m, o in body if m == "add" and "0x95da10" in o]
        P("  0x%08X %-14s folds=%d  base-add=%s"
          % (site, fn, len(f), [hex(int(o.split(",")[1], 16)) for _, o in add] or "none"))
    # the arithmetic itself, independent of any disassembly
    # (n + n*8) = 9n ; (n + 9n) = 10n ... NO: the encoding is lea d,[n+n*8] = 9n then
    # lea e,[n+d*2] = n + 18n = 19n, then shl 4 -> 19n*16 = 304n.
    fold_val = lambda n: (((n + (n + n * 8) * 2) << 4))
    stride = fold_val(1) - fold_val(0)
    P("  pure arithmetic: (n + (n+n*8)*2) << 4  ->  n=0:%d n=1:%d n=2:%d  stride=%d "
      "(record length %d)"
      % (fold_val(0), fold_val(1), fold_val(2), stride, REC_LEN))
    P("  REC_BASE %d + 304*0 = %d ; the deferred pick named the table at 0x95da40 = %d (+48)"
      % (REC_BASE, REC_BASE, 0x95da40))
    P("")

    # ---- table 4: the reader/test split over the whole cache -----------------------
    idx_refs = idx_reads
    kinds = {"W": [], "T": [], "R": []}
    for a, mn, op in idx_refs:
        kinds[classify(a, mn, op)].append((a, mn, op))
    P("TABLE 4  every reference to ds:0x68cbb0 in the .text cache, by kind")
    P("  writes %d / tests (cmp|test) %d / reads %d / total %d"
      % (len(kinds["W"]), len(kinds["T"]), len(kinds["R"]), len(idx_refs)))
    P("  the 6 writes:")
    for a, mn, op in sorted(kinds["W"]):
        P("    0x%08X %-9s %s" % (a, mn, op))
    P("  the tests (first 8 of %d):" % len(kinds["T"]))
    for a, mn, op in sorted(kinds["T"])[:8]:
        P("    0x%08X %-9s %s" % (a, mn, op))
    ptr_refs = refs_of(ins, PTR)
    ptr_w = [x for x in ptr_refs
             if x[1].startswith("mov")
             and ("ds:0x%x" % PTR) in x[2].rsplit(",", 1)[0]]
    P("  ds:0x8f0d60: %d references, %d stores" % (len(ptr_refs), len(ptr_w)))
    P("")

    setter_body = win(ins, order, SETTER, SETTER_END + 1)
    setter_f = fold_chain(setter_body)
    s57 = sum(1 for r in rows if r[1] == owner(rows, SETTER))
    idx_set = {n_ins for a, n, _, _ in rows for n_ins in [n] if a == SETTER}

    # =============================== the gates =====================================
    W = []
    a1 = (len(live_stores) == 6
          and all(ins[sa][0].split()[0] == "mov" and ("0x%x" % IDX) in ins[sa][1]
                  for sa, _, _, _, _ in live_stores)
          and [f for _, f, _, _, _ in live_stores]
              == [owner(rows, sa) for sa, _, _, _, _ in live_stores]
          and len({f for _, f, _, _, _ in live_stores}) == 4)
    W.append(("A1 EXACTLY %d stores to ds:0x%x, all of them `mov DWORD PTR ds:..,reg`, living "
              "in %d distinct functions (%s) - the census's own count of %d referencing "
              "instructions is the denominator"
              % (6, IDX, 4, ", ".join(sorted({f for _, f, _, _, _ in live_stores})),
                 N_IDX_REFS), a1))

    dists = [d for *_, d in pairs if d is not None]
    unpaired_idx = [i for i in idx_wsites if not any(i < p <= i + 32 for p in ptr_wsites)]
    unpaired_ptr = [p for p in ptr_wsites if not any(p - 32 <= i < p for i in idx_wsites)]
    a2 = (sorted(a for a, _, _ in PTR_STORES) == ptr_wsites
          and sorted(a for a, _, _ in IDX_STORES) == idx_wsites
          and all(owner(rows, a) == f for a, f, _ in PTR_STORES)
          and len(pairs) == 6 and len(ptr_wsites) == 6 and len(idx_wsites) == 6
          and len(dists) == 6 and all(d is not None for _, _, _, _, d in pairs)
          and min(dists) == 6 and max(dists) == 25
          and not unpaired_idx and not unpaired_ptr
          and len({f for _, f, _, _, _ in pairs}) == 4)
    W.append(("A2 THE PAIRING IS 1:1: ds:0x%x has EXACTLY %d stores, every one %d-%d B after "
              "exactly one of the %d index stores and every index store has one (unpaired: %s), "
              "across the same %d functions (%s) - the engine NEVER moves the index without "
              "refreshing the pointer in the same instruction window, which is what makes the "
              "pair one field with two representations rather than two independent globals"
              % (PTR, len(pairs), min(dists), max(dists), len(idx_wsites),
                 (unpaired_idx or unpaired_ptr) or "none",
                 len({f for _, f, _, _, _ in pairs}),
                 ", ".join(sorted({f for _, f, _, _, _ in pairs}))), a2))

    FOLD_TRIPLETS = {0x4e3476: (0x4e347b, 0x4e347e, 0x4e3481),
                     0x4efe8e: (0x4efe88, 0x4efe94, 0x4efe97),
                     0x4f5a7c: (0x4f5a82, 0x4f5a87, 0x4f5a8a)}
    pinned = [h for st in folds for h in folds[st]]
    triplets_ok = all(folds[st] and FOLD_TRIPLETS[st] in folds[st] for st in FOLD_TRIPLETS)
    base_refs = {st: [(a, mn, op) for a, mn, op in win(ins, order, st - 24, st + 34)
                      if "0x%x" % REC_BASE in op] for st in folds}
    complete = [st for st in folds if folds[st]]
    a3 = (triplets_ok and len(pinned) == 3
          and stride == REC_LEN and len(complete) == 3
          and all(base_refs[st] for st in folds)
          and all(owner(rows, a) in {f for _, f, _ in IDX_STORES}
                  for st in folds for a, _, _ in base_refs[st])
          and all(ins[pa][1].endswith(",ecx") or ins[pa][1].endswith(",eax") or
                  ins[pa][1].endswith(",edx") for pa, _, _, _, _ in pairs))
    tri_s = "; ".join("0x%x <- %s" % (st, " + ".join("0x%x" % x for x in FOLD_TRIPLETS[st]))
                      for st in sorted(FOLD_TRIPLETS))
    base_s = "; ".join("0x%x: %s" % (st, ", ".join("0x%08X %s" % (a_, mn_) for a_, mn_, _ in base_refs[st]))
                       for st in sorted(folds))
    W.append(("A3 the stride law, in the encoding's own words: %d of the 6 store sites carry a "
              "complete ((n + (n+n*8)*2) << 4) fold, each one EXACTLY at the pinned triplet "
              "[%s], and all %d reference the array base 0x%x within their window [%s]; the "
              "arithmetic gives n=1:%d, n=2:%d - stride %d = the %d-B record length, so the "
              "index counts 304-B entities"
              % (len(complete), tri_s, len(folds), REC_BASE, base_s,
                 fold_val(1), fold_val(2), stride, REC_LEN), a3))

    n48 = 0x95da40 - REC_BASE
    b_site = 0x4f5aab
    b_mn, b_op = ins[b_site]
    a4 = (n48 == 48
          and b_mn == "mov" and b_op == "edx,DWORD PTR [eax+0x95da40]"
          and owner(rows, b_site) == "FUN_004f5a70"
          and all(any("0x%x" % REC_BASE in op for _, _, op in win(ins, order, st - 24, st + 34))
                  for st in folds)
          and len([1 for a, (mn, op) in ins.items() if "0x95da40" in op]) == 96)
    W.append(("A4 THE TWO DEFERRED PICKS ARE ONE OBJECT: the pointer is 0x%x + 304n, and the "
              "table pick (b) named - 0x95da40 - is that base + %d, i.e. field +%d of the SAME "
              "record. Pinned by the instruction that says so: 0x%08X in %s `%s %s` reads "
              "element+48 off the very register the fold produced; 0x95da10 appears in %d "
              "instructions and 0x95da40 in %d across .text"
              % (REC_BASE, n48, n48, b_site, owner(rows, b_site), b_mn, b_op,
                 len([1 for a, (mn, op) in ins.items() if "0x%x" % REC_BASE in op]),
                 len([1 for a, (mn, op) in ins.items() if "0x95da40" in op])), a4))

    a5 = (len(kinds["W"]) == 6 and len(kinds["T"]) > 0 and len(kinds["R"]) > 0
          and len(kinds["W"]) + len(kinds["T"]) + len(kinds["R"]) == len(idx_refs)
          and len(idx_refs) == N_IDX_REFS)
    W.append(("A5 the full-cache split is %d writes / %d tests / %d reads = %d references "
              "(matches the census's %d) - the field IS tested (%s), so a 'read-only cursor' or "
              "'never compared' claim would be FALSE and is not made"
              % (len(kinds["W"]), len(kinds["T"]), len(kinds["R"]), len(idx_refs),
                 N_IDX_REFS, "0x%08X %s %s" % tuple(sorted(kinds["T"])[0])), a5))

    n_setter, i_setter, c_setter = next(
        (sz, ni, nc) for a, nm, sz, ni, nc in [
            (int(r["addr"], 16), r["name"], int(r["size_bytes"]), int(r["n_insns"]),
             int(r["n_callers"])) for r in __import__("csv").DictReader(open(M.INDEX))]
        if nm == "FUN_004e3470")
    a6 = (owner(rows, SETTER) == "FUN_004e3470" and len(setter_body) == 11
          and setter_f and ins[0x4e348a][0].startswith("mov")
          and ("0x%x" % PTR) in ins[0x4e348a][1]
          and n_setter == 34 and i_setter == 11 and c_setter == 57
          and next(sz for a, nm, sz, _ in rows if nm == "FUN_004e3470") == 34)
    W.append(("A6 the setter FUN_004e3470 is %d B / %d instructions with %d recorded callers: "
              "it stores the argument to the index, folds it, and stores the result to the "
              "pointer - so 57 call sites move the selection through ONE 11-insn leg"
              % (n_setter, len(setter_body), c_setter), a6))

    last_stores = [(a, mn, op) for a, mn, op in refs_of(ins, LAST)
                   if mn.startswith("mov")
                   and ("ds:0x%x" % LAST) in op.rsplit(",", 1)[0]]
    paired_last = [a for a, _, _ in last_stores
                   if any(s <= a <= s + 96 for s, _, _, _, _ in live_stores)]
    in_window = [a for a, _, _ in last_stores
                 if any(i <= a <= i + 32 for i in idx_wsites)]
    a7 = (len(last_stores) == 22 and len(in_window) == 3
          and all(owner(rows, a) in {f for _, f, _ in IDX_STORES}
                  for a in in_window)
          and all(("ds:0x%x" % LAST) in op.rsplit(",", 1)[0] for _, _, op in last_stores))
    W.append(("A7 NOT AN INVARIANT, MEASURED: the adjacent dword ds:0x%x is stored %d times - "
              "far more than the index's %d - and only %d of those stores fall in an "
              "index-store window. So it is a SEPARATE field in the same selection block, not a "
              "shadow of the index: the pairing claim is made for the pointer (A2) and explicitly "
              "REFUSED for this dword, whose extra %d writers are not explained here"
              % (LAST, len(last_stores), len(idx_wsites), len(in_window),
                 len(last_stores) - len(in_window)), a7))

    digest = hashlib.sha256(
        "|".join(["%d" % len(live_stores), "%d" % len(pairs), "%d" % stride,
                  "%d" % len(idx_refs), "%d" % len(kinds["T"]), "%d" % len(last_stores),
                  "%d-%d" % (min(d for *_, d in pairs if d), max(d for *_, d in pairs if d)),
                  "%d" % len([a for a, (mn, op) in ins.items() if "0x95da40" in op])]
                 ).encode()).hexdigest()
    bad = [n for n, ok in W if not ok]
    for name, ok in W:
        P(("  ok   " if ok else "  BAD  ") + name)
    P("")
    P("census digest %s" % digest[:16])
    if bad:
        P("RESULT: FAIL (%d/%d gates bad: %s)"
          % (len(bad), len(W), "; ".join(b.split(" ")[0] for b in bad)))
        print("\n".join(out))
        print("RESULT: FAIL (%d/%d gates bad)" % (len(bad), len(W)), file=sys.stderr)
        return 1
    P("PASS M311: %d/%d gates - ds:0x%x is the CURRENT-RECORD INDEX of the 304-B entity array "
      "at 0x%x (the object the deferred pick called 'the 0x95da40 table' is the same array at "
      "+%d), ds:0x%x is its derived record POINTER, the two are written together at every "
      "selection change, and 57 callers move the selection through the 11-insn setter "
      "FUN_004e3470 (no box time, no /proc, no gdb)"
      % (len(W), len(W), IDX, REC_BASE, 0x95da40 - REC_BASE, PTR))
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
