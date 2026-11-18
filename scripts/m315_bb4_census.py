#!/usr/bin/env python3
"""M315 (s284, STATIC, zero box): WHAT IS ds:0x68cbb4? - ANSWERED: it is the
MEMO "the selection-refresh chain has already run for record index N", the
dedup key of the refresh pair call 0x4e8d60; call 0x4e78e0. Cleared to -1 to
force the next refresh; never written from an independent value.

M311 refused the pairing (22 stores vs the index's 6, "19 writers
unexplained"). This census resolves every writer: the 22 stores partition
EXACTLY into sentinel clears and guarded memo updates, and the memo updates
are exactly the sites the refresh pair follows.

Print the table FIRST, then assert the printed numbers; rivals FAIL on the
printed numbers. Mutation harness: scripts/m315_bb4_mutate.py.
"""
import bisect
import csv
import hashlib
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import m308_site_list as E

IDX = os.path.join(REPO, "ghidra_out", "index.csv")
EXE = os.path.join(REPO, "terran.exe")
BB0, BB4 = 0x68CBB0, 0x68CBB4
REFRESH = (0x4E8D60, 0x4E78E0)      # the pair that follows every memo update
WIN = 96                            # M311's pairing window
checks, measured = [], {}


def ck(name, ok, det=""):
    checks.append((name, bool(ok), det))
    print(("OK   " if ok else "FAIL ") + name + ": " + det)


def main():
    blob = open(EXE, "rb").read()
    ib, secs = E.pe_sections(blob)

    def at(va, n):
        off, _ = E.va2off(secs, va)
        return blob[off:off + n] if off is not None else b""

    E._INS, E._ORDER = E.parse_text()
    ins, order = E._INS, E._ORDER
    # M315_PATCH="addr|mn ops;addr|mn ops" rewrites PARSED INSTRUCTIONS before any
    # measurement. It exists so the mutation harness can falsify a provenance or a
    # guard by changing the code, not by changing an expected count (review #301 P2).
    patches = [s for s in os.environ.get("M315_PATCH", "").split(";") if s.strip()]
    done = []
    for spec in patches:
        aa, text = spec.split("|", 1)
        a = int(aa, 16)
        if a in ins:
            mn, _, ops = text.strip().partition(" ")
            ins[a] = (mn, ops)
            done.append(spec)
    print("-- parsed-instruction patches applied: %d/%d %s --" % (len(done), len(patches), done))
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

    # mnemonic AND operand live in separate fields - match the BARE OPERAND
    def is_store(mn, ops):
        return mn == "mov" and bool(re.match(r"(DWORD PTR )?ds:0x68cbb4,", ops.strip()))

    def is_load(mn, ops):
        return mn == "mov" and bool(re.search(r"\bds:0x68cbb4\b", ops.strip())) \
            and not ops.strip().startswith(("DWORD PTR ds:0x68cbb4", "ds:0x68cbb4"))

    stores, reads, tests = [], [], []
    for a in order:
        mn, ops = ins[a]
        if "0x68cbb4" not in ops:
            continue
        if is_store(mn, ops):
            stores.append(a)
        elif mn in ("cmp", "test"):
            tests.append(a)
        elif is_load(mn, ops):
            reads.append(a)
    print("-- 22 stores --")
    for a in stores:
        print("   %s %-14s %s %s" % (hex(a), owner(a), ins[a][0], ins[a][1].strip()))
    print("-- %d reads / %d tests --" % (len(reads), len(tests)))
    for a in reads + tests:
        print("   %s %-14s %s %s" % (hex(a), owner(a), ins[a][0], ins[a][1].strip()))

    # A1 census pinned exactly
    ST = [0x40DC2A, 0x40DD7C, 0x416E60, 0x41B7A7, 0x41BCBD, 0x4E4DDC, 0x4E5165,
          0x4EB6C7, 0x4EE6C9, 0x4EE883, 0x4EFEAA, 0x4F2201, 0x4F3F7F, 0x4F44A8,
          0x4F455D, 0x4F5AB7, 0x4F5B32, 0x4F5C4A, 0x4F5EA3, 0x598032, 0x5984B4,
          0x5AB757]
    RD = [0x4E5155, 0x4EFE83, 0x4F21E9, 0x4F5C41, 0x5AB74D]
    TS = [0x4EB6BF]
    measured["A1"] = "stores=%d reads=%d tests=%d total=%d" % (
        len(stores), len(reads), len(tests), len(stores) + len(reads) + len(tests))
    ck("A1 census pinned to the byte: 22 stores / 5 reads / 1 cmp (28 refs)",
       stores == ST and reads == RD and tests == TS, measured["A1"])

    # A2 the ONLY immediate ever stored is the -1 sentinel; 2 more reach it via `or r,-1`
    sent_direct = [a for a in stores
                   if ins[a][1].strip().endswith(",0xffffffff")]
    print("-- sentinel stores (direct): %s" % [hex(x) for x in sent_direct])
    # def-walk of a store's register: last write inside the owner function
    MEMO_SRC = ("ds:0x68cbb4", "DWORD PTR ds:0x68cbb4")

    def store_reg(addr):
        """The register a store writes, or None for an immediate store - a
        REGISTERS-only group, else `mov ds:0x68cbb4,0xffffffff` "reads" a
        register named 0xffffffff and the sentinel census goes blind."""
        m = re.match(r"mov\s+(?:DWORD PTR )?ds:0x68cbb4,([a-z][a-z0-9]{1,3})\s*$",
                     ("%s %s" % ins[addr]).strip())
        return m.group(1) if m else None

    def own_span(addr):
        """(lo, hi, claimed) from index.csv. `claimed=False` means NO recorded
        function contains addr, so the caller still gets a MEASURED lower bound
        (the nearest preceding function start) - the walk never runs to the top
        of the cache, which is how an unrelated function's write could be borrowed."""
        i = bisect.bisect_right(fstarts, addr) - 1
        if i >= 0:
            s, n, sz = funcs[i]
            if s <= addr < s + sz:
                return s, s + sz, True
            return s, addr + 64, False
        return 0, addr + 64, False

    SCAN_INS = 12          # instructions walked back per hop - a measured cap, not a guess

    def producer(addr):
        """(kind, chain) - kind is set by the MOVING INSTRUCTION plus its SOURCE
        OPERAND, never by operand text alone: `add r,ds:0x68cbb0` is arithmetic
        on the index, and `lea r,[ebp+0x8]` is an address, not a load."""
        reg = store_reg(addr)
        if reg is None:
            return None, []
        lo, hi, claimed = own_span(addr)
        # A CLAIMED function bounds the walk by its own start (measured, from
        # index.csv); an unclaimed range gets the instruction cap, because a name
        # we cannot bound is exactly how a write from another function leaks in.
        i = bisect.bisect_left(order, lo) if claimed else \
            max(bisect.bisect_left(order, lo), bisect.bisect_left(order, addr) - SCAN_INS * 3)
        j = bisect.bisect_right(order, addr) - 1
        chain, hops, seen = [], 0, set()
        while hops <= 2 and reg and reg not in seen:
            seen.add(reg)
            k, hit = j, None
            while k >= i:
                a = order[k]
                mn, ops = ins[a]
                ops = ops.strip()
                if a < addr and (mn in E.WRITES_DST or mn == "lea") and \
                        E.reg_norm(E.dst_reg(mn, ops) or "") == E.reg_norm(reg):
                    hit = (a, mn, ops)
                    break
                k -= 1
            if hit is None:
                return "no-producer-in-%d-insn-window" % (SCAN_INS * 3), chain  # only possible for an unclaimed owner
            a, mn, ops = hit
            chain.append((a, mn, ops, claimed))
            if mn == "or" and ops.endswith(",0xffffffff"):
                return "imm--1-via-or", chain
            srcs = [x.strip() for x in ops.split(",")]
            src = srcs[-1] if len(srcs) > 1 else ""
            if mn != "mov":
                return "arith-%s" % mn, chain
            src = re.sub(r"^\w+ PTR ", "", src)          # DWORD PTR [...] / BYTE PTR ds:...
            # The KIND is the value class; where the bound came from is a property of
            # the WALK (A10), not of the class - folding it into the kind name would
            # split one class into two counts and the totals would stop meaning 22.
            if src in ("ds:0x68cbb0",):
                return "reads-index", chain
            if src.startswith("["):
                # KIND keys on the base register (a stack slot is a stack slot);
                # the exact offsets are pinned separately in A2b's detail.
                m2 = re.match(r"\[(\w+)", src)
                return "stack-slot:" + (m2.group(1) if m2 else src), chain
            if re.fullmatch(r"[a-z]{2,4}", src) and E.reg_norm(src):
                reg, j, hops = src, bisect.bisect_left(order, a) - 1, hops + 1
                continue
            return "other-src:" + src, chain
        return "chain-unresolved", chain

    sent_or, src_rows = [], []
    for a in stores:
        k, chain = producer(a)
        if k is None:
            k = "imm--1" if ins[a][1].strip().endswith(",0xffffffff") else "PARSE-FAIL"
            src_rows.append((a, k, "%s %s" % ins[a]))
            continue
        if k == "imm--1-via-or":
            sent_or.append(a)
        src_rows.append((a, k, " <- ".join(
            "%s %s @%s%s" % (mn, ops, hex(pa), "" if claimed else " [OWNER-UNCLAIMED]")
            for pa, mn, ops, claimed in chain)))
    print("-- producer kinds --")
    for a, k, d in src_rows:
        print("   %s %-14s %-22s %s" % (hex(a), owner(a), k, d))
    kinds = {}
    for _, k, _ in src_rows:
        kinds[k] = kinds.get(k, 0) + 1
    slot_ops = {}
    for _, k, d in src_rows:
        if k.startswith("stack-slot:"):
            for m2 in re.finditer(r"\[(?:ebp|esp)[-+][0-9a-fx]+\]", d):
                slot_ops[m2.group(0)] = slot_ops.get(m2.group(0), 0) + 1
                break
    measured["A2"] = "sentinel_direct=%d sentinel_via_or=%s kinds=%s" % (
        len(sent_direct), [hex(x) for x in sent_or], dict(sorted(kinds.items())))
    ck("A2 the only value ever stored is the -1 sentinel (8 direct + 2 via `or r,0xffffffff`); nothing else",
       len(sent_direct) == 8 and sorted(sent_or) == [0x41B7A7, 0x5984B4] and
       set(kinds) <= {"imm--1", "imm--1-via-or", "reads-index", "stack-slot:ebp"},
       measured["A2"])
    ck("A2b provenance is classified by MOVING INSTRUCTION + SOURCE OPERAND, not operand text: 8 x mov-from-index, 4 x mov-from-[ebp], 10 x sentinel, ZERO arith/lea/no-producer",
       kinds.get("reads-index") == 8 and kinds.get("stack-slot:ebp") == 4 and
       kinds.get("imm--1") == 8 and kinds.get("imm--1-via-or") == 2 and
       sum(kinds.values()) == 22 and slot_ops == {"[ebp+0x8]": 3, "[ebp-0x18]": 1},
       "kinds=%s slots=%s sum=%d" % (dict(sorted(kinds.items())), dict(sorted(slot_ops.items())),
                                      sum(kinds.values())))

    # A3 THE LAW: a memo update is exactly a store the refresh pair follows
    PAIR_REACH = 17       # measured worst gap store -> second callee (0x4f5ab7)
    ABSENCE_INS = 60      # instructions scanned after a CLEAR looking for either callee
    def pair_at(a):
        """(d1, d2): byte distance from the store to each callee, or None. The
        stated reach bounds BOTH calls - an earlier draft bounded only the first
        and accepted the second anywhere in the next four instructions."""
        js = bisect.bisect_right(order, a)

        def call_to(x, tgt):
            return (ins[x][0] == "call" and
                    re.fullmatch(r"0x[0-9a-f]+", ins[x][1].strip()) and
                    int(ins[x][1].strip(), 16) == tgt)
        d1 = next((b - a for b in order[js:js + 6] if b - a <= PAIR_REACH and call_to(b, REFRESH[0])), None)
        if d1 is None:
            return None
        d2 = next((b - a for b in order[js:js + 6] if b - a <= PAIR_REACH and call_to(b, REFRESH[1])), None)
        return None if d2 is None else (d1, d2)

    has_pair = lambda a: pair_at(a) is not None
    memo = [a for a in stores if has_pair(a)]
    clear = [a for a in stores if not has_pair(a)]
    # a memo site that somehow has no pair drops out of dist and the exact pin fails,
    # so this comprehension cannot hide a None behind an assert that unpacks it.
    dist = [d for a in memo if (d := pair_at(a)) is not None]

    def callees_within(a, n):
        """(n1, n2): how many of the next n instructions call 0x4e8d60 / 0x4e78e0."""
        js = bisect.bisect_right(order, a)
        w = order[js:js + n]
        return (sum(1 for b in w if b in _CAL and _CAL[b] == REFRESH[0]),
                sum(1 for b in w if b in _CAL and _CAL[b] == REFRESH[1]))

    def call_target(b):
        o = ins[b][1].strip()
        return int(o, 16) if ins[b][0] == "call" and re.fullmatch(r"0x[0-9a-f]+", o) else None
    _CAL = {b: call_target(b) for b in order if ins[b][0] == "call"}
    absence = [callees_within(a, ABSENCE_INS) for a in clear]
    print("-- clears: refresh calls in the next %d instructions: %s" % (ABSENCE_INS, absence))
    print("-- pair distances from store (d1,d2) B: %s" % [(hex(a), d) for a, d in zip(memo, dist)])
    print("-- memo updates (refresh pair within 16 B): %s" % [hex(x) for x in memo])
    print("-- clears (no pair): %s" % [hex(x) for x in clear])
    measured["A3"] = "memo=%d clear=%d pair=%s reach=%dB max(d1,d2)=%s" % (
        len(memo), len(clear), [hex(x) for x in REFRESH], PAIR_REACH,
        max(dist) if dist else None)
    measured["A3"] = "memo=%d clear=%d pair=%s reach=%dB max(d1,d2)=%s absence=%s" % (
        len(memo), len(clear), [hex(x) for x in REFRESH], PAIR_REACH,
        (max([d1 for d1, _ in dist], default=None), max([d2 for _, d2 in dist], default=None)),
        set(absence))
    ck("A3 LAW (two INDEPENDENT classifications coincide): the 22 stores split by PROVENANCE into 12 index/slot-fed and 10 -1-sentinel, and split by ADJACENCY into exactly those same 12 followed by call 0x4e8d60 (+5..12 B) then call 0x4e78e0 (+10..17 B, pinned per site) and the 10 clears with ZERO calls to either callee in the next 60 instructions",
       len(memo) == 12 and len(clear) == 10 and
       set(clear) == set(sent_direct) | set(sent_or) and
       dist == [(6, 11), (5, 10), (6, 11), (6, 11), (6, 11), (6, 11), (6, 11),
                (5, 10), (6, 11), (12, 17), (5, 10), (6, 11)] and
       set(absence) == {(0, 0)}, measured["A3"])

    # A4 the guard shape: read bb4, cmp it with the value about to be stored, je PAST the store
    # TWO guard shapes: (a) cmp directly against ds:0x68cbb4; (b) load bb4 into a
    # register, cmp that register, je PAST the store. Both must skip the memo store.
    def writes_to(reg, lo, hi):
        """instructions in (lo, hi) that overwrite reg - a cmp whose operand is
        clobbered before the store is NOT a dedup guard."""
        out = []
        for c in order[bisect.bisect_left(order, lo):bisect.bisect_right(order, hi)]:
            if not (lo < c < hi):
                continue
            mn, ops = ins[c]
            if mn in E.WRITES_DST or mn == "lea":
                d = E.dst_reg(mn, ops.strip())
                if d and E.reg_norm(d) == E.reg_norm(reg):
                    out.append(c)
        return out

    def guard_for(a):
        """A LOCAL dedup guard gates this memo store only if: the cmp compares
        ds:0x68cbb4 (or a copy of it) against THE REGISTER THIS STORE WRITES,
        nothing clobbers either register between the cmp and the store, and a je
        between them jumps PAST the store. (Review #301 P2: an earlier draft
        counted a cmp of the memo against ANY register, e.g. `edx`, as a guard.)"""
        stored = store_reg(a)
        if not stored:
            return None
        i0 = bisect.bisect_left(order, a)
        for k in range(max(0, i0 - 12), i0):
            b = order[k]
            mn, ops = ins[b]
            parts = [x.strip() for x in ops.strip().split(",")]
            cand = None
            if mn == "cmp" and any(x in MEMO_SRC for x in parts):
                other = [x for x in parts if x not in MEMO_SRC]
                cand = (b, "direct", other[0] if other else None)
            elif mn == "mov" and parts[-1] in MEMO_SRC:
                cp = E.reg_norm(parts[0])
                for c in order[k + 1:i0 + 1]:
                    if ins[c][0] != "cmp":
                        continue
                    ps = [x.strip() for x in ins[c][1].strip().split(",")]
                    if cp in [E.reg_norm(x) for x in ps]:
                        other = ps[0] if E.reg_norm(ps[-1]) == cp else ps[-1]
                        cand = (c, "via-" + cp, other)
                        break
            if not cand or not cand[2]:
                continue
            ca, shape, other = cand
            if E.reg_norm(other) != E.reg_norm(stored):
                continue                      # compares the memo against something ELSE
            if writes_to(stored, ca, a):
                continue                       # clobbered between cmp and store
            if shape.startswith("via-") and writes_to(shape[4:], ca, a):
                continue
            je = [c for c in order[bisect.bisect_right(order, ca):bisect.bisect_right(order, ca) + 4]
                  if ins[c][0] == "je" and int(ins[c][1].strip(), 16) > a]
            if je:
                return (ca, shape, je[0])
        return None

    guarded, unguarded = [], []
    for a in memo:
        g = guard_for(a)
        (guarded.append((a,) + g) if g else unguarded.append(a))
    measured["A4"] = "guarded=%d %s unguarded=%d %s" % (
        len(guarded), [(hex(x), hex(y), z, hex(w)) for x, y, z, w in guarded],
        len(unguarded), [hex(x) for x in unguarded])
    ck("A4 a LOCAL dedup guard (cmp of bb4 or of its loaded copy, + je PAST the store) sits at exactly 4 of the 12 memo sites; the other 8 refresh unconditionally",
       [x for x, _, _, _ in guarded] == [0x4EB6C7, 0x4EFEAA, 0x4F2201, 0x4F5C4A] and
       len(unguarded) == 8, measured["A4"])

    # A5 lockstep with the index, with the operand regex FIXED (M311's 6 stores), and
    # M311's refusal REPRODUCED from its own window definition rather than re-derived.
    idx = [a for a in order if ins[a][0] == "mov" and
           re.match(r"(DWORD PTR )?ds:0x68cbb0,", ins[a][1].strip())]
    # M311's window, reproduced from its own source (m311_recidx.py:449-450):
    # FORWARD 0..+32 B from an index store. Widening it is the only way to reach 5.
    fwd32 = [a for a in stores if any(0 <= a - b <= 32 for b in idx)]
    inwin = [a for a in stores if any(abs(a - b) <= WIN for b in idx)]
    # M311's refusal was stated on ITS window, so the closure is computed there too:
    # its "19 writers unexplained" = the 22 stores minus the 3 in the forward window.
    out_fwd = [a for a in stores if a not in fwd32]
    closure = sorted((set(out_fwd) & set(sent_direct)) | (set(out_fwd) & set(sent_or)))
    measured["A5"] = ("index_stores=%d %s; fwd+32=%d %s; outside+32=%d of which "
                      "sentinel=%d memo=%d; +-96=%d %s" %
                      (len(idx), [hex(x) for x in idx], len(fwd32), [hex(x) for x in fwd32],
                       len(out_fwd), len(closure), len(out_fwd) - len(closure),
                       len(inwin), [hex(x) for x in inwin]))
    ck("A5 M311's 6 index stores + its forward 0..+32 B window reproduce EXACTLY (3 lockstep sites, both mov forms); its '19 writers unexplained' closes as 10 sentinel clears + 9 memo updates away from the index store; widening to +-96 B only adds 2 more memo sites (5/22)",
       idx == [0x4E3476, 0x4E4DD0, 0x4EFE8E, 0x4F21E0, 0x4F5A7C, 0x4F5C36] and
       fwd32 == [0x4E4DDC, 0x4EFEAA, 0x4F5C4A] and len(inwin) == 5 and
       len(out_fwd) == 19 and len(closure) == 10 and len(out_fwd) - len(closure) == 9,
       measured["A5"])

    # A6 the decisive windows, byte-pinned
    def pin(lo, hi, want):
        win = {a: (mn, ops.strip()) for a, mn, ops in E.window(lo, hi)}
        bad = [(hex(a), w, win.get(a)) for a, w in want
               if win.get(a) != tuple(w)]
        return bad
    def pin_all(lo, hi, want):
        """The window must match the expected sequence IN FULL - same addresses,
        same count - so a change to ANY instruction inside it, the record-address
        fold included, reddens the gate. (Review #301 P2: the earlier pin checked
        7 listed addresses and skipped the fold between them entirely.)"""
        win = [(a, mn, ops.strip()) for a, mn, ops in E.window(lo, hi)]
        exp = [(a, w[0], w[1]) for a, w in want]
        if win != exp:
            wa = [x for x, _, _ in win]
            ea = [x for x, _, _ in exp]
            return [("SEQ len=%d want=%d missing=%s extra=%s" %
                     (len(win), len(exp), [hex(x) for x in ea if x not in wa][:6],
                      [hex(x) for x in wa if x not in ea][:6]),
                     [(hex(x), mn, ops) for x, mn, ops in win
                      if (x, mn, ops) not in exp][:3],
                     [(hex(x), mn, ops) for x, mn, ops in exp
                      if (x, mn, ops) not in win][:3])]
        return []

    W1 = pin_all(0x4EFE74, 0x4EFEAA + 1, [
        (0x4EFE74, ["mov", "esi,DWORD PTR ds:0x68cbb0"]),
        (0x4EFE7A, ["push", "0x0"]), (0x4EFE7C, ["push", "ebx"]), (0x4EFE7D, ["push", "eax"]),
        (0x4EFE7E, ["call", "0x572800"]),
        (0x4EFE83, ["mov", "eax,ds:0x68cbb4"]),
        (0x4EFE88, ["lea", "ecx,[esi+esi*8]"]),          # <-- the fold M311 named
        (0x4EFE8B, ["add", "esp,0xc"]),
        (0x4EFE8E, ["mov", "DWORD PTR ds:0x68cbb0,esi"]),
        (0x4EFE94, ["lea", "ecx,[esi+ecx*2]"]),          # <-- and its second step
        (0x4EFE97, ["shl", "ecx,0x4"]),                  # <-- and the 304n shift
        (0x4EFE9A, ["add", "ecx,0x95da10"]),             # <-- and the array base
        (0x4EFEA0, ["cmp", "eax,esi"]),
        (0x4EFEA2, ["mov", "DWORD PTR ds:0x8f0d60,ecx"]),
        (0x4EFEA8, ["je", "0x4efed8"]),
        (0x4EFEAA, ["mov", "DWORD PTR ds:0x68cbb4,esi"])])
    W2 = pin_all(0x4F5C36, 0x4F5C4A + 1, [
        (0x4F5C36, ["mov", "DWORD PTR ds:0x68cbb0,ebx"]),
        (0x4F5C3C, ["mov", "ds:0x8f0d60,eax"]),
        (0x4F5C41, ["mov", "eax,ds:0x68cbb4"]),
        (0x4F5C46, ["cmp", "eax,ebx"]),
        (0x4F5C48, ["je", "0x4f5c69"]),
        (0x4F5C4A, ["mov", "DWORD PTR ds:0x68cbb4,ebx"])])
    W3 = pin_all(0x4F3F76, 0x4F3F8A + 1, [
        (0x4F3F76, ["mov", "ecx,DWORD PTR ds:0x68cbb0"]),
        (0x4F3F7C, ["add", "esp,0xc"]),
        (0x4F3F7F, ["mov", "DWORD PTR ds:0x68cbb4,ecx"]),
        (0x4F3F85, ["call", "0x4e8d60"]),
        (0x4F3F8A, ["call", "0x4e78e0"])])
    W4 = pin_all(0x4EB6B8, 0x4EB6D1 + 1, [
        (0x4EB6B8, ["mov", "eax,ds:0x68cbb0"]),
        (0x4EB6BD, ["jne", "0x4eb6c7"]),
        (0x4EB6BF, ["cmp", "DWORD PTR ds:0x68cbb4,eax"]),
        (0x4EB6C5, ["je", "0x4eb6e5"]),
        (0x4EB6C7, ["mov", "ds:0x68cbb4,eax"]),
        (0x4EB6CC, ["call", "0x4e8d60"]),
        (0x4EB6D1, ["call", "0x4e78e0"])])
    measured["A6"] = "win1=%s win2=%s win3=%s win4=%s (pinned %d insns total)" % (
        W1, W2, W3, W4, len(W1[0]) if W1 else 16 + 6 + 5 + 7)
    ck("A6 all four decisive windows pinned IN FULL, every instruction between the bounds included (fold + 304n shift + array base among them)",
       not W1 and not W2 and not W3 and not W4, measured["A6"])

    # A10 coverage honesty: which of the 22 stores sit in a range index.csv does NOT
    # claim (so their provenance bound is the instruction cap, not a function span)?
    unclaimed = [a for a in stores if not own_span(a)[2]]
    print("-- A10 stores in index.csv-UNCLAIMED ranges: %d %s" % (len(unclaimed), [hex(x) for x in unclaimed]))
    measured["A10"] = "unclaimed=%d %s (provenance walk there is bounded to %d insns, not a function span)" % (
        len(unclaimed), [hex(x) for x in unclaimed], SCAN_INS * 3)
    ck("A10 the coverage gap is MEASURED and bounded, not silently absorbed: exactly 1 of the 22 stores (0x4f3f7f) sits outside every recorded function range, so only its provenance walk uses the instruction cap",
       unclaimed == [0x4F3F7F], measured["A10"])

    # A7 image .data init for the pair
    v = struct.unpack("<II", at(BB0, 8))
    measured["A7"] = "init bb0=%s bb4=%s" % (hex(v[0]), hex(v[1]))
    ck("A7 the image carries BOTH dwords initialised to -1 (the 'nothing memoised yet' state)",
       v == (0xFFFFFFFF, 0xFFFFFFFF), measured["A7"])

    # A9 THE RIVAL - a store fed by the OTHER index would survive the memo law
    # (bb4 := ds:0x68cbac would keep the pair-follows invariant), so A2b alone is
    # the refutation: no store traces to a second index, a literal, or arithmetic.
    other_idx = [a for a, k, d in src_rows
                 if any(n in d for n in ("ds:0x68cbac", "ds:0x68cbb8"))]
    print("-- A9 stores whose producer reads a neighbouring candidate index: %d %s"
          % (len(other_idx), [hex(x) for x in other_idx]))
    kinds_txt = ",".join("%s=%d" % (k, v) for k, v in sorted(kinds.items()))
    non_sent = {k: v for k, v in kinds.items() if not k.startswith(("imm--1"))}
    measured["A9"] = "kinds{%s} foreign_index_stores=%d memo-fed-by-index-or-slot=%d/%d" % (
        kinds_txt, len(other_idx), sum(v for k, v in non_sent.items()), len(memo))
    ck("A9 rival 'bb4 is a second cursor fed from elsewhere' dies on the def-walk: all 12 memo values = the current index (8) or a caller [ebp] slot (4); 0 stores read a neighbouring candidate index",
       other_idx == [] and sum(non_sent.values()) == len(memo) and
       all(k.startswith(("reads-index", "stack-slot:")) for k in non_sent),
       measured["A9"])

    fails = [c[0] for c in checks if not c[1]]
    print("census digest -")
    print("== M315: %d/%d ==" % (len(checks) - len(fails), len(checks)))
    if fails:
        print("FAILED:", fails)
        return 1
    rows = "\n".join("%s|%s|%s" % (nm, "PASS" if ok else "FAIL", det)
                     for nm, ok, det in checks)
    print("digest %s" % hashlib.sha256(rows.encode()).hexdigest()[:16])
    return 0


if __name__ == "__main__":
    sys.exit(main())
