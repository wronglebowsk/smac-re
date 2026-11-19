#!/usr/bin/env python3
"""M319 (s292, STATIC, zero box): pick (v) - the 8 memo sites with NO local dedup guard.

M315 established ds:0x68cbb4 is the refresh MEMO ("the index the pair
`call 0x4e8d60; call 0x4e78e0` has already run for") and pinned its partition:
12 stores are followed by the pair, and only 4 of those 12 carry a LOCAL guard
(`0x4eb6c7, 0x4efeaa, 0x4f2201, 0x4f5c4a`); the other 8 refresh unconditionally.
M315 explicitly refused to claim who guards the 8 (Greptile P2 on #301, accepted):
"the absence of a local guard does NOT establish a caller-side guard".

THIS SCRIPT ANSWERS IT: census the callers of the 8 sites' owner functions and ask
whether the dedup is HOISTED there. It computes three independent things:
  1. every instruction in the image that READS or TESTS the memo (a hoisted guard
     has to read the memo to compare against it);
  2. every DIRECT call site of each memo-site owner, thunk-resolved, grouped by
     caller function, plus callers that no direct call reaches (dispatch-only);
  3. the CFG arrival condition of each such call site (block preds -> jcc -> the
     instruction that set the flags -> what that test reads).

Print the table FIRST, then assert the printed numbers; the rivals FAIL on the
printed numbers. Mutation harness: scripts/m319_mutate.py.
"""
import bisect
import collections
import csv
import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import m308_site_list as E

IDX = os.path.join(REPO, "ghidra_out", "index.csv")
BB0, BB4 = 0x68CBB0, 0x68CBB4
REFRESH = (0x4E8D60, 0x4E78E0)
PAIR_REACH = 17   # M315's review round (#301) moved the bound 16->17 B: the SECOND callee
                  # sits 17 B after the store at 0x4f5ab7; a 16-B reach loses that site.
MEMO_SRC = ("ds:0x68cbb4", "DWORD PTR ds:0x68cbb4")
JCC = {"je", "jne", "jz", "jnz", "jb", "jnb", "ja", "jae", "jbe", "jae", "jge",
       "jg", "jl", "jle", "js", "jns", "jo", "jno", "jc", "jnc"}
HEXOP = re.compile(r"^0x([0-9a-f]+)$")
M315_GUARDED = [0x4EB6C7, 0x4EFEAA, 0x4F2201, 0x4F5C4A]
M315_MEMO12 = [0x4E4DDC, 0x4EB6C7, 0x4EE6C9, 0x4EE883, 0x4EFEAA, 0x4F2201,
               0x4F3F7F, 0x4F44A8, 0x4F455D, 0x4F5AB7, 0x4F5B32, 0x4F5C4A]
checks, measured = [], {}


def ck(name, ok, det=""):
    checks.append(bool(ok))
    print(("OK   " if ok else "FAIL ") + name + ": " + det)


def main():
    blob = open(os.path.join(REPO, "terran.exe"), "rb").read()
    ib, secs = E.pe_sections(blob)
    E._INS, E._ORDER = E.parse_text()
    ins, order = E._INS, E._ORDER
    # M319_PATCH="addr|mn ops;addr|mn ops" rewrites PARSED INSTRUCTIONS before any measurement,
    # so the mutation harness can falsify a guard, a memo read or an arrival test by changing the
    # CODE, never by changing an expected count (the M315 #301 review law).
    for spec in [s for s in os.environ.get("M319_PATCH", "").split(";") if s.strip()]:
        aa, text = spec.split("|", 1)
        a = int(aa, 16)
        if a in ins:
            mn, _, ops = text.strip().partition(" ")
            ins[a] = (mn, ops)
    E._SPANS = E.load_spans()
    funcs = []
    with open(IDX) as f:
        for r in csv.DictReader(f):
            funcs.append((int(r["addr"], 16), r["name"], int(r["size_bytes"])))
    funcs.sort()
    fstarts = [a for a, _, _ in funcs]

    def owner(a):
        i = bisect.bisect_right(fstarts, a) - 1
        s, n, sz = funcs[i]
        return n if s <= a < s + sz else "UNRANGED:%s" % n

    def span(nm):
        for s, n, sz in funcs:
            if n == nm:
                return s, s + sz
        return 0, 0

    def tgt_of(a):
        """direct call target, THUNK-RESOLVED (a one-instruction `jmp` body)."""
        o = ins[a][1].strip()
        if ins[a][0] != "call" or not HEXOP.match(o):
            return None
        t = int(HEXOP.match(o).group(1), 16)
        for _ in range(3):
            j = ins.get(t)
            if not j or j[0] != "jmp" or not HEXOP.match(j[1].strip()):
                break
            nt = int(HEXOP.match(j[1].strip()).group(1), 16)
            if nt == t:
                break
            t = nt
        return t

    CALLS = collections.defaultdict(list)      # target -> [call site]
    for a in order:
        t = tgt_of(a)
        if t is not None:
            CALLS[t].append(a)

    # ---- T1 re-measure M315's inputs: the 22 stores, the 12 memo sites, the 4/8 guard split
    def is_store(mn, ops):
        return mn == "mov" and bool(re.match(r"(DWORD PTR )?ds:0x68cbb4,", ops.strip()))

    stores = [a for a in order if is_store(ins[a][0], ins[a][1])]

    def pair_at(a):
        js = bisect.bisect_right(order, a)
        w = order[js:js + 6]
        d1 = next((b - a for b in w if b - a <= PAIR_REACH and tgt_of(b) == REFRESH[0]), None)
        if d1 is None:
            return None
        d2 = next((b - a for b in w if b - a <= PAIR_REACH and tgt_of(b) == REFRESH[1]), None)
        return None if d2 is None else (d1, d2)

    memo = [a for a in stores if pair_at(a)]
    clears = [a for a in stores if not pair_at(a)]

    def store_reg(addr):
        mn, ops = ins[addr]
        parts = [x.strip() for x in ops.split(",")]
        return None if parts[-1].startswith("0x") else parts[-1]

    def memo_copy(addr):
        """registers holding a copy of the memo, loaded within 14 insns before `addr`
        and not overwritten since (a hoisted or local guard must compare against one).
        Scanning BACKWARDS, the NEAREST event for a register decides it: a second,
        earlier write to the same register must NOT re-open a decided copy (the first
        version of this walk discarded `eax` on `lea eax,[edi+edi*8]` that ran BEFORE
        the memo load - it lost 2 of the 4 real guards)."""
        i0 = bisect.bisect_left(order, addr)
        copies, decided = set(), set()
        for b in reversed(order[max(0, i0 - 14):i0]):
            mn, ops = ins[b]
            parts = [x.strip() for x in ops.split(",")]
            if mn == "mov" and parts[-1] in MEMO_SRC:
                r = E.reg_norm(parts[0])
                if r not in decided:
                    copies.add(r)
                    decided.add(r)
                continue
            d = E.dst_reg(mn, ops) if mn in E.WRITES_DST else None
            if d:
                r = E.reg_norm(d)
                if r in decided:
                    continue        # nearest event already decided it: an EARLIER write
                                    # (seen later in this backwards walk) must not discard
                                    # the copy - that was the bug that lost 2 of 4 guards
                decided.add(r)
                copies.discard(r)
        return copies

    def guarded(a):
        """INDEPENDENT re-derivation of M315's guard partition: a jcc in the 24 bytes
        before the store whose target lies PAST the store (it skips the store), and a
        cmp of the memo (directly, or of an unclobbered copy of it) upstream of that jcc."""
        i0 = bisect.bisect_left(order, a)
        for k in range(max(0, i0 - 12), i0):
            b = order[k]
            mn, ops = ins[b]
            o = ops.strip()
            if mn not in JCC or not HEXOP.match(o):
                continue
            t = int(HEXOP.match(o).group(1), 16)
            if not (b < a < t):
                continue
            j0 = bisect.bisect_left(order, b)
            for c in reversed(order[max(0, j0 - 12):j0]):
                cmn, cops = ins[c]
                if cmn != "cmp":
                    continue
                parts = [x.strip() for x in cops.split(",")]
                if any(p in MEMO_SRC for p in parts):
                    return (b, t, "direct", c)
                cp = memo_copy(b)
                if cp and any(E.reg_norm(p) in cp for p in parts):
                    return (b, t, "via-copy", c)
        return None

    guards = {a: guarded(a) for a in memo}
    G = sorted([a for a, g in guards.items() if g])
    U = sorted([a for a, g in guards.items() if not g])
    print("-- T1 the memo-site partition, RE-DERIVED here (not imported) --")
    for a in memo:
        print("   %s %-16s pair=%s guard=%s" % (hex(a), owner(a), pair_at(a),
                                                "-" if not guards[a] else "%s jcc %s->%s cmp %s"
                                                % (guards[a][2], hex(guards[a][0]),
                                                   hex(guards[a][1]), hex(guards[a][3]))))
    print("   stores=%d memo=%d clears=%d  guarded=%s  unguarded=%s"
          % (len(stores), len(memo), len(clears), [hex(x) for x in G], [hex(x) for x in U]))
    ck("G1 M315's inputs re-measure identically: 22 stores, the 12 pair-fed memo sites, "
       "and an INDEPENDENT guard rule reproduces exactly the 4-guarded / 8-unguarded split",
       len(stores) == 22 and sorted(memo) == sorted(M315_MEMO12) and G == sorted(M315_GUARDED)
       and len(U) == 8, "stores=%d memo=%d guarded=%d unguarded=%d" % (len(stores), len(memo), len(G), len(U)))

    # ---- T2 who READS or TESTS the memo anywhere in the image (a hoisted guard must read it)
    def is_ref(mn, ops):
        """any instruction that READS or TESTS the memo. Only a store's DESTINATION
        operand is not a read: `cmp DWORD PTR ds:0x68cbb4, esi` also starts with the
        memo and IS a read (the first version excluded it and found 5 refs, not 6)."""
        return "0x68cbb4" in ops.strip() and not is_store(mn, ops)

    refs = [a for a in order if is_ref(ins[a][0], ins[a][1])]
    ref_owner = collections.Counter(owner(a) for a in refs)
    print("-- T2 every instruction that READS/TESTS the memo (image-wide): %d --" % len(refs))
    for a in refs:
        print("   %s %-16s %s %s" % (hex(a), owner(a), ins[a][0], ins[a][1].strip()))
    print("   by owner: %s" % dict(ref_owner))
    measured["T2"] = "refs=%d owners=%d" % (len(refs), len(ref_owner))

    # ---- T3 the callers of each memo-site owner
    own_of = {a: owner(a) for a in memo}
    rows = {}
    print("-- T3 direct call sites of each memo-site OWNER (thunk-resolved) --")
    for a in sorted(memo):
        nm = own_of[a]
        if nm.startswith("UNRANGED"):
            print("   site %s owner %s -> NO FUNCTION RANGE (M315 A10): callers not nameable"
                  % (hex(a), nm))
            rows[a] = None
            continue
        ent = span(nm)[0]
        sites = CALLS.get(ent, [])
        callers = collections.Counter(owner(s) for s in sites)
        rows[a] = (nm, ent, sites, callers)
        print("   site %s owner %-16s entry=%s direct_calls=%d callers=%s"
              % (hex(a), nm, hex(ent), len(sites), dict(callers)))
    unguarded_owners = sorted({own_of[a] for a in U if not own_of[a].startswith("UNRANGED")})
    by_owner = collections.OrderedDict()
    for a in sorted(U):
        r = rows[a]
        if r:
            by_owner.setdefault(r[0], []).append(a)
    all_callers = collections.Counter()
    for nm, ss in by_owner.items():
        all_callers.update(rows[ss[0]][3])
    unranged_sites = [a for a in U if own_of[a].startswith("UNRANGED")]
    memo_readers = set(ref_owner)
    hoisted = sorted(c for c in all_callers if c in memo_readers)
    print("-- T3b the caller population of the 8 UNGUARDED sites --")
    print("   unguarded sites=%d nameable owners=%d %s | owner-less sites (M315 A10 gap)=%s"
          % (len(U), len(unguarded_owners), unguarded_owners, [hex(x) for x in unranged_sites]))
    own_set = sorted({own_of[a] for a in memo})
    print("   distinct direct callers=%d; of them %d READ the memo somewhere: %s"
          % (len(all_callers), len(hoisted), hoisted))
    print("   are those readers themselves memo-site owners? %s -> their read is a LOCAL guard, "
          "not a hoist onto a caller"
          % {c: (c in own_set) for c in hoisted})
    print("   call count by caller: %s" % dict(all_callers))
    measured["T3"] = "unguarded=%d owners=%d callers=%d callers_reading_memo=%d readers_that_are_owners=%d" % (
        len(U), len(unguarded_owners), len(all_callers), len(hoisted),
        sum(1 for c in hoisted if c in own_set))

    # ---- T4 CFG arrival condition of every call to an unguarded owner
    def cfg(lo, hi):
        i0 = bisect.bisect_left(order, lo)
        i1 = bisect.bisect_right(order, hi)
        win = order[i0:i1]
        targets = set()
        for a in win:
            mn, ops = ins[a]
            if (mn in JCC or mn == "jmp") and HEXOP.match(ops.strip()):
                t = int(HEXOP.match(ops.strip()).group(1), 16)
                if lo <= t < hi:
                    targets.add(t)
        heads = set(win[:1]) | (targets & set(win))
        blocks, prev_term = [], False
        for a in win:
            if a in heads or not blocks or prev_term:
                blocks.append([a, a])
            else:
                blocks[-1][1] = a
            prev_term = ins[a][0] in ("ret", "jmp") or ins[a][0] in JCC
        idx = {s: i for i, (s, _e) in enumerate(blocks)}
        a2b, bi = {}, 0
        for a in win:
            while a > blocks[bi][1]:
                bi += 1
            a2b[a] = bi
        preds = collections.defaultdict(set)
        for i, (s, e) in enumerate(blocks):
            mn, ops = ins[e]
            if mn == "ret":
                continue
            if mn == "jmp" and HEXOP.match(ops.strip()):
                t = int(HEXOP.match(ops.strip()).group(1), 16)
                if t in idx:
                    preds[idx[t]].add(i)
                continue
            if mn in JCC and HEXOP.match(ops.strip()):
                t = int(HEXOP.match(ops.strip()).group(1), 16)
                if t in idx:
                    preds[idx[t]].add(i)
            if i + 1 < len(blocks):
                preds[i + 1].add(i)
        return win, blocks, a2b, preds

    def flag_setter(blocks, b, at):
        s, e = blocks[b]
        i0 = bisect.bisect_left(order, s)
        i1 = bisect.bisect_right(order, e)
        fs = None
        for a in order[i0:i1]:
            if ins[a][0] in ("cmp", "test"):
                fs = a
            if a == at:
                break
        return fs

    arrival = collections.Counter()
    print("-- T4 CFG arrival of each call to an UNGUARDED owner (pred edge -> flag setter -> what it reads) --")
    ARR = []
    for nm, ss in by_owner.items():            # one walk per OWNER: two unguarded sites can
        ent, sites = rows[ss[0]][1], rows[ss[0]][2]   # share a function and would double-count
        for c in sites:
            lo, hi = span(owner(c))
            win, blocks, a2b, preds = cfg(lo, hi)
            b = a2b[c]
            pe = sorted(preds[b])
            kinds = []
            for p in pe:
                term = blocks[p][1]
                mn = ins[term][0]
                fs = flag_setter(blocks, p, term)
                src = "-"
                if fs is not None:
                    ops = ins[fs][1]
                    if "0x68cbb4" in ops:
                        src = "MEMO"
                    elif "0x68cbb0" in ops:
                        src = "INDEX"
                    else:
                        src = ops.strip()[:38]
                kinds.append(("jcc" if mn in JCC else mn,
                              "%s|%s" % (hex(fs) if fs is not None else "-", src)))
            arr = ("memo-test" if any(k[1].endswith("|MEMO") for k in kinds)
                   else "index-test" if any(k[1].endswith("|INDEX") for k in kinds)
                   else "fallthrough-only" if not pe else "other-test")
            arrival[arr] += 1
            ARR.append((c, nm, owner(c), arr, kinds))
    for c, nm, cn, arr, kinds in ARR:
        print("   call %s -> %-16s in %-16s arrival=%-16s preds=%s"
              % (hex(c), nm, cn, arr, [(k, s) for k, s in kinds] or "NONE(entry)"))
    print("   arrival totals: %s" % dict(arrival))
    measured["T4"] = "calls=%d arrivals=%s" % (len(ARR), dict(arrival))

    # ---- gates on the printed numbers (all pins are MEASURED here, then Bitten by
    # scripts/m319_mutate.py - a declared gate-set is never authored) ----------------
    REF_PIN = [0x4E5155, 0x4EB6BF, 0x4EFE83, 0x4F21E9, 0x4F5C41, 0x5AB74D]
    ck("G2 the memo has EXACTLY 6 read/test instructions IMAGE-WIDE, at these pinned addresses in "
       "5 functions - so any hoisted guard would have to live in one of those 5",
       refs == REF_PIN, "refs=%d %s" % (len(refs), [hex(x) for x in refs]))
    readers = set(ref_owner)
    memo_writers = set(owner(a) for a in stores)
    ck("G5 the memo is PRIVATE to the refresh chain: every function that reads it also writes it "
       "(no read-only consumer exists to have hoisted a guard)",
       readers <= memo_writers and len(readers) == 5,
       "readers=%d writers=%d readers_not_writers=%s" % (len(readers), len(memo_writers),
                                                         sorted(readers - memo_writers)))
    outside = [c for c in hoisted if c not in own_set]
    ck("G3 RIVAL 'the dedup guard is HOISTED into the callers' FAILS: of the 8 distinct direct "
       "callers of the unguarded owners, exactly 1 reads the memo (FUN_004f5a70) and it is itself a "
       "memo-site owner - its read is the LOCAL guard of its own site, not a hoist. Callers that are "
       "not memo-site owners and read the memo: %d" % len(outside),
       len(all_callers) == 8 and len(hoisted) == 1 and not outside,
       measured["T3"] + " non-owner memo-readers=%s" % outside)
    min_calls = min([len(rows[ss[0]][2]) for ss in by_owner.values()] or [0])
    ck("G4 RIVAL 'the 8 unguarded sites are dead code' FAILS: every nameable unguarded owner has at "
       "least one direct call site (min=%d, total calls=%d); the 8th site 0x4f3f7f has no function "
       "range at all (M315 A10) so its callers are not nameable - stated, not counted"
       % (min_calls, len(ARR)),
       min_calls >= 1 and len(ARR) == 9 and unranged_sites == [0x4F3F7F],
       "min_calls_per_owner=%d calls=%d unranged=%s" % (min_calls, len(ARR),
                                                        [hex(x) for x in unranged_sites]))
    ck("G6 no call to an unguarded owner arrives under a MEMO test (the PRECISE form of G3: the CFG "
       "pred edge's flag-setter is never a memo compare)",
       all(a[3] != "memo-test" for a in ARR),
       "calls=%d arrivals=%s" % (len(ARR), dict(arrival)))
    rows_txt = "|".join("%s|%s|%s" % (k, v, "") for k, v in sorted(measured.items()))
    dig = hashlib.sha256((rows_txt + "|" + ",".join(hex(a) for a in refs)
                          + "|" + ",".join("%s:%s" % (hex(a), r[3]) for a, r in sorted(rows.items()) if r)
                          ).encode()).hexdigest()[:16]
    print("-- measurement digest %s (T2+T3+T4 rows + the pinned ref list + per-site callers) --" % dig)
    n_ok = sum(checks)
    print("== M319: %d/%d ==" % (n_ok, len(checks)))
    return 0 if n_ok == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
