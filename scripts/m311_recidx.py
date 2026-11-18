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
# the register each site stores into the index (informational; fold_chain does NOT use it, and
# the reason is documented in its docstring - review P1 on PR #289 forced that measurement)
IDX_REG = {site: reg for site, _fn, reg in IDX_STORES}

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


def fold_chain(body, proximity=24, identity=True):
    """Recognise the index->byte-offset fold  (n + (n+n*8)*2) << 4  = 304n.

    Returns [(lea9_addr, lea19_addr, shl_addr), ...].  Each discipline below is paired with a
    mutant in scripts/m311_mutate.py, so "this clause does work" is measured, not asserted.

      FIRST STEP IS A TRUE *9 - the two OPERANDS are the same register, `lea d,[n+n*8]` (the
        destination d is a DIFFERENT register; demanding d == n there is wrong and breaks all
        six sites, which is exactly what the first attempt at this fix did).  Without the
        operand check the first step may be `lea d,[a+b*8]` = a + 9b, and the chain then
        computes 2*(a+9b) + a, not 19a - the reviewer's counterexample, and my original code's
        actual bug (a chained `a != b != c` is not pairwise-disequality either).  Relax this
        clause and the setter gains a second, arithmetically wrong fold at
        (0x4e347e, 0x4e3481, ...) that multiplies the wrong register: MU12/MU13.
      ORDER - the three steps appear in program order but may be INTERLEAVED: at 0x4f5a82 the
        compiler inserts two pushes between the two leas, so no contiguity may be required.
      PROXIMITY - at most `proximity` bytes between the first step and the closing `shl 0x4`.
        This is what keeps a NEIGHBOURING function's fold out of the window (0x4e34cc sits 86 B
        past the store at 0x4e3476); widen it and the count goes 1 -> 2 (MU14).

    DELIBERATELY NOT CHECKED, and this is a measurement, not an omission: the matcher does NOT
    require the second step's base operand to be the same register as the first step's.  The
    compiler re-loads the index into a different register at some sites, and requiring name
    equality there is FALSE at the setter - `0x4e3476 mov ds:0x68cbb0,eax` stores eax, then
    `0x4e347e lea edx,[eax+ecx*2]` reads eax, so the two steps' "n" registers differ and the
    only reason a naive rule passes is that eax still holds the value.  Register NAMES are a
    proxy for value identity; without intervening-write tracking (which this fire declined to
    write) that proxy is unsound, so the value of the index operand is declared UNPROVEN here
    and the claim is limited to the shape of the arithmetic.
    """
    hits = []
    n = len(body)
    for i in range(n):
        a1, m1, o1 = body[i]
        g = re.match(r"^(\w+),\[(\w+)\+(\w+)\*8\]$", o1) if m1 == "lea" else None
        if not g:
            continue
        if identity and not (g.group(2) == g.group(3)):   # `[n+n*8]`: OPERANDS equal, dest free
            continue
        d9 = g.group(1)
        for j in range(i + 1, n):
            a2, m2, o2 = body[j]
            g2 = re.match(r"^(\w+),\[(\w+)\+(\w+)\*2\]$", o2) if m2 == "lea" else None
            if not g2 or g2.group(3) != d9:
                continue
            d19 = g2.group(1)
            for k in range(j + 1, n):
                a3, m3, o3 = body[k]
                g3 = re.match(r"^(\w+),0x4$", o3) if m3 == "shl" else None
                if g3 and g3.group(1) == d19 and a3 - a1 <= proximity:
                    hits.append((a1, a2, a3))
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
    # ALL SIX index stores, not the three I first chose to look at - restricting this dict to
    # hand-picked sites made `all(folds[st] ...)` and `len(folds)` vacuous - they can only pass
    # (worse than a uniqueness-only check like sorted(x)==sorted(set(x)), which at least fails on
    # duplicates: review P2 on PR #289).  The per-site right-hand reach RIGHT[st] is
    # measured: 0x4e4dd0's fold sits 78 B past the store, so it needs the +90 window.
    RIGHT = {0x4e3476: 32, 0x4e4dd0: 90, 0x4efe8e: 32,
             0x4f21e0: 32, 0x4f5a7c: 32, 0x4f5c36: 32}
    for site, fn, reg in IDX_STORES:
        body = win(ins, order, site - 24, site + RIGHT[site])
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

    FOLD_SITES = [st for st in sorted(folds) if folds[st]]
    NONFOLD_SITES = [st for st in sorted(folds) if not folds[st]]
    base_refs = {st: [(a, mn, op) for a, mn, op in win(ins, order, st - 40, st + RIGHT[st] + 40)
                      if "0x%x" % REC_BASE in op] for st in FOLD_SITES}
    # What the encoding pins: the fold's CLOSING instruction (shl 0x4 / lea +base) at each
    # of the three sites, the base reference within 24 B, and the stride arithmetic. The
    # fold's OPENING `lea [n+n*8]` is NOT always a fresh instruction - at the setter the
    # scale-8 term was computed earlier and is re-read by `lea edx,[eax+ecx*2]` - so this
    # gate claims the end-points, not a shape it has not measured. (Fold triplets below are
    # reported for information; the gate does not require all three sites to be complete.)
    FOLD_TRIPLETS = {0x4e3476: (0x4e347b, 0x4e347e, 0x4e3481),
                     0x4efe8e: (0x4efe88, 0x4efe94, 0x4efe97),
                     0x4f5a7c: (0x4f5a82, 0x4f5a87, 0x4f5a8a),
                     0x4e4dd0: (0x4e4e1e, 0x4e4e21, 0x4e4e24),
                     0x4f21e0: (0x4f21dd, 0x4f21e6, 0x4f21ee)}
    i347e = ins[0x4e347e]
    i4e81 = ins[0x4e3481]
    # Every fold the matcher finds must equal the transcribed triplet EXACTLY (a
    # mis-transcribed address reddens this: MU4), and the transcription must cover exactly
    # the sites that fold - not the three I first chose to look at.
    triplet_exact = (set(FOLD_TRIPLETS) == set(FOLD_SITES)
                     and all(folds.get(st, []) == [FOLD_TRIPLETS[st]] for st in FOLD_TRIPLETS))
    pinned_end = (i347e == ("lea", "edx,[eax+ecx*2]")
                  and i4e81 == ("shl", "edx,0x4")
                  and ins[0x4efe97] == ("shl", "ecx,0x4")
                  and ins[0x4f5a8a] == ("shl", "eax,0x4"))
    # (an earlier `a_ - st <= 24` proximity filter here was simply WRONG arithmetic and made
    # every set empty; the claim that survives is the weaker, true one: the base is named in
    # the same instruction window as the fold)
    base_close = all(base_refs[st] for st in FOLD_SITES) and len(FOLD_SITES) == 5
    a3 = (pinned_end and triplet_exact and base_close and stride == REC_LEN
          and len(FOLD_SITES) == 5 and NONFOLD_SITES == [0x4f5c36]
          and all(all(("0x%x" % REC_BASE) in op_ for _, _, op_ in base_refs[st])
                  for st in FOLD_SITES))
    tri_s = "; ".join("0x%x <- %s" % (st, " + ".join("0x%x" % x for x in FOLD_TRIPLETS[st]))
                      for st in sorted(FOLD_TRIPLETS))
    base_s = "; ".join("0x%x: %s" % (st, ", ".join("0x%08X %s %s" % (a_, mn_, op_)
                                                   for a_, mn_, op_ in base_refs[st]))
                       for st in sorted(FOLD_SITES))
    near_s = "; ".join("0x%x: %d base-ref instruction(s) in window" % (st, len(base_refs[st]))
                       for st in sorted(base_refs))
    msg_a3 = ("A3 the stride law, in the encoding's own words: the fold ENDS are pinned - "
              "0x4e347e `%s %s` then 0x4e3481 `%s %s` (and the shl 0x4 closer at 0x4efe97, "
              "0x4f5a8a), so 19n<<4 = 304n - and the array base 0x%x is referenced within "
              "24 B of all 3 folding sites (%s); arithmetic n=1:%d, n=2:%d - stride %d = the "
              "%d-B record length. Fold triplets for the record: [%s]. Window base refs: [%s]. "
              "CLAIM NARROWED HONESTLY: the fold's OPENING lea [n+n*8] is not a fresh "
              "instruction at every site (at the setter the scale-8 term is re-read), so this "
              "gate asserts the end-points it measured, not a uniform 3-step shape"
              % (i347e[0], i347e[1], i4e81[0], i4e81[1], REC_BASE, near_s, fold_val(1),
                 fold_val(2), stride, REC_LEN, tri_s, base_s))
    W.append((msg_a3, a3))

    # Measured, not guessed: my first guess "the remaining 3 sites have no fold" was WRONG
    # for 2 of them - 0x4e4dd0 and 0x4f21e0 DO fold, so 5 of the 6 index stores recompute
    # the record address. 0x4f5c36 is the one exception: it takes the pointer from a saved
    # stack slot (`mov eax,[ebp-0x8]` at 0x4f5c33, stored at 0x4f5c3c) instead of folding.
    MATCH_TRUTH = {0x4e3476: 1, 0x4e4dd0: 1, 0x4efe8e: 1,
                   0x4f21e0: 1, 0x4f5a7c: 1, 0x4f5c36: 0}
    # Per-site right-hand reach, chosen from the MEASURED fold offsets (all five folds are
    # 0..78 B past their store; the next function's spurious fold is 86 B past 0x4e3476), so
    # each site's window is wide enough to contain its own fold and too narrow to absorb a
    # neighbour's.  WIDE_W deliberately overshoots 86 to demonstrate the cap actually biting.
    NARROW_W, WIDE_W = 32, 110
    WIDE_TRUTH = {0x4e3476: 2}   # at +-110 B the 0x4e34cc fold of the NEXT function is absorbed
                                 # (fold at 0x4e34cc, 86 B past the store) - proximity does that

    wide = {st: fold_chain(win(ins, order, st - 24, st + WIDE_W)) for st in WIDE_TRUTH}
    # `.get(st, 0)` so a MISSING store site degrades to "no fold found" and the gate reddens,
    # instead of crashing the instrument with a KeyError (a traceback is not a measurement -
    # the mutation harness rightly refuses to score it).
    nfold = {st: len(folds.get(st, [])) for st in MATCH_TRUTH}
    matched = nfold   # via .get(): a deleted store site reports count 0 and reddens A8, no crash
    a8 = (all(matched.get(st, 0) == MATCH_TRUTH[st] for st in (0x4e3476, 0x4efe8e, 0x4f5a7c))
          and triplet_exact
          and all(len(wide[st]) == WIDE_TRUTH[st] for st in WIDE_TRUTH)
          and all(nfold[st] == MATCH_TRUTH[st] for st in MATCH_TRUTH)
          and len(folds) == len(IDX_STORES) == 6
          and folds[0x4e3476] == [FOLD_TRIPLETS[0x4e3476]])
    # Is each matcher clause load-bearing?  ANSWERED BY RUNNING THE WEAKENED MATCHER, not by
    # prose (this gate claimed register discipline worked without ever running that comparison,
    # then claimed the operand and proximity clauses worked when they do not - both caught here).
    st0 = 0x4e3476
    STRICT_LBL = "strict -24/+%d" % RIGHT[st0]
    clauses = {}
    for label, kw, L, Wd in ((STRICT_LBL, {}, 24, RIGHT[st0]),
                             ("operand-clause OFF", {"identity": False}, 24, RIGHT[st0]),
                             ("proximity OFF", {"proximity": 10**6}, 24, RIGHT[st0]),
                             ("window -24/+110", {}, 24, WIDE_W)):
        clauses[label] = fold_chain(win(ins, order, st0 - L, st0 + Wd), **kw)
    inert = sorted(k for k in ("operand-clause OFF", "proximity OFF") if clauses[k] == clauses[STRICT_LBL])
    # What IS load-bearing: the window's right-hand reach.  At 0x4e4dd0 (fold 78 B past the
    # store) a tight +-32 window loses the fold entirely; overshooting absorbs the next one.
    reach = {}
    for Wd in (32, 90, 144):
        reach["-24/+%d" % Wd] = len(fold_chain(win(ins, order, 0x4e4dd0 - 24, 0x4e4dd0 + Wd)))
    P("  matcher clause audit at 0x4e3476: %s" % {k: len(v) for k, v in clauses.items()})
    P("  INERT clauses (no mutant can redden a gate for them): %s" % (", ".join(inert) or "none"))
    P("  window right-hand reach audit at 0x4e4dd0: %s" % reach)
    a8 = a8 and len(inert) == 2 and reach["-24/+32"] == 0 and reach["-24/+90"] == 1 \
        and len(clauses["window -24/+110"]) == 2
    W.append(("A8 the matcher is pinned, not trusted: fold_chain finds EXACTLY one fold at each "
              "of the 5 index stores that recompute the address (%s) and EXACTLY zero at 0x4f5c36, "
              "the ONE selection site that does not fold - it re-stores a SAVED pointer read from "
              "[ebp-0x8] at 0x4f5c33 - and at the setter the single accepted fold is the pinned "
              "triplet %s; %d of the 6 stores materialise REC_BASE+304n themselves. "
              "WHAT THE AUDIT ACTUALLY SUPPORTS: the only matcher property that changes any result on "
              "this binary is the window's right-hand reach - at 0x4e4dd0 the window -24/+32 B finds "
              "%d folds, -24/+90 B finds %d (its fold sits 78 B past the store), -24/+144 B finds %d, "
              "and widening 0x4e3476 to -24/+110 B absorbs the neighbouring function's fold at "
              "0x4e34cc (%d instead of 1). DECLARED INERT (kept as cheap insurance, NOT claimed "
              "load-bearing, and no mutant is aimed at them): the *8-term operand-equality clause and "
              "the 24 B proximity cap - switching either OFF returns byte-identical results at all 6 "
              "sites over windows -24/+32, -24/+90, -24/+144 and -64/+144 B. My two earlier prose "
              "claims to the contrary were unmeasured and are retracted here. NOT claimed either: that "
              "the second step's base register holds the index VALUE (at the setter it reads eax again "
              "after 0x4e3476 stored eax; register names are only a proxy for value identity without "
              "intervening-write tracking), so the index operand's value stays UNPROVEN and the claim "
              "stops at the arithmetic shape"
              % (", ".join("0x%x:%d" % (st, nfold[st]) for st in sorted(MATCH_TRUTH)),
                 "+".join("0x%x" % x for x in FOLD_TRIPLETS[0x4e3476]),
                 sum(1 for st in MATCH_TRUTH if MATCH_TRUTH[st]),
                 reach["-24/+32"], reach["-24/+90"], reach["-24/+144"],
                 len(clauses["window -24/+110"])), a8))

    n48 = 0x95da40 - REC_BASE
    b_site = 0x4f5aab
    b_mn, b_op = ins[b_site]
    a4 = (n48 == 48
          and b_mn == "mov" and b_op == "edx,DWORD PTR [eax+0x95da40]"
          and owner(rows, b_site) == "FUN_004f5a70"
          and all(base_refs[st] for st in FOLD_SITES)
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
                  "%d" % len([a for a, (mn, op) in ins.items() if "0x95da40" in op]),
                  "".join(str(matched.get(st, 0)) for st in sorted(MATCH_TRUTH))]
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
