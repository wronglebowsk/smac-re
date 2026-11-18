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
    def producer(addr):
        line = "%s %s" % ins[addr]
        m = re.match(r"mov\s+(?:DWORD PTR )?ds:0x68cbb4,(\w+)", line.strip())
        if not m:
            return None, None, None
        reg = m.group(1)
        lo, hi = span(owner(addr))
        i = bisect.bisect_left(order, lo)
        j = bisect.bisect_right(order, addr) - 1
        while j >= i:
            a = order[j]
            mn, ops = ins[a]
            ops = ops.strip()
            if mn in E.WRITES_DST or mn == "lea":
                d = E.dst_reg(mn, ops)
                if d and E.reg_norm(d) == E.reg_norm(reg):
                    return a, mn, ops
            j -= 1
        return None, None, None

    sent_or, src_rows = [], []
    for a in stores:
        p, mn, ops = producer(a)
        if p is None:
            if not ins[a][1].strip().endswith(",0xffffffff"):
                src_rows.append((a, "parse-fail", "?"))
            continue
        kind = ("imm--1-via-or" if (mn == "or" and ops.endswith(",0xffffffff")) else
                "reads-index" if "ds:0x68cbb0" in ops else
                "stack-slot" if "[" in ops else
                "other: %s %s" % (mn, ops))
        if kind == "imm--1-via-or":
            sent_or.append(a)
        src_rows.append((a, kind, "%s %s @%s" % (mn, ops, hex(p))))
    print("-- producer kinds --")
    for a, k, d in src_rows:
        print("   %s %-14s %-22s %s" % (hex(a), owner(a), k, d))
    kinds = {}
    for _, k, _ in src_rows:
        kinds[k] = kinds.get(k, 0) + 1
    measured["A2"] = "sentinel_direct=%d sentinel_via_or=%s kinds=%s" % (
        len(sent_direct), [hex(x) for x in sent_or], dict(sorted(kinds.items())))
    ck("A2 the only value ever stored is the -1 sentinel (8 direct + 2 via `or r,0xffffffff`)",
       len(sent_direct) == 8 and sorted(sent_or) == [0x41B7A7, 0x5984B4] and
       {k for k in kinds if k.startswith("other")} == set(), measured["A2"])
    ck("A2b every register store's value def-walks to the CURRENT INDEX or a stack slot (never arithmetic)",
       all(k in ("reads-index", "stack-slot", "imm--1-via-or") for _, k, _ in src_rows) and
       kinds.get("reads-index") == 8 and kinds.get("stack-slot") == 4,
       "reads-index=%s stack-slot=%s" % (kinds.get("reads-index"), kinds.get("stack-slot")))

    # A3 THE LAW: a memo update is exactly a store the refresh pair follows
    def has_pair(a):
        for b in order[bisect.bisect_right(order, a):bisect.bisect_right(order, a) + 4]:
            if b - a > 16:
                break
            if ins[b][0] != "call":
                continue
            t = ins[b][1].strip().split()[0]
            if not re.match(r"^0x[0-9a-f]+$", t):
                continue
            if int(t, 16) == REFRESH[0]:
                for c in order[bisect.bisect_right(order, b):bisect.bisect_right(order, b) + 4]:
                    if ins[c][0] == "call" and re.match(r"^0x[0-9a-f]+$", ins[c][1].strip()):
                        if int(ins[c][1].strip(), 16) == REFRESH[1]:
                            return True
        return False

    memo = [a for a in stores if has_pair(a)]
    clear = [a for a in stores if not has_pair(a)]
    print("-- memo updates (refresh pair within 16 B): %s" % [hex(x) for x in memo])
    print("-- clears (no pair): %s" % [hex(x) for x in clear])
    measured["A3"] = "memo=%d clear=%d pair=%s" % (len(memo), len(clear),
                                                  [hex(x) for x in REFRESH])
    ck("A3 LAW: the 22 stores partition EXACTLY into 12 memo updates followed by call 0x4e8d60+call 0x4e78e0 and 10 sentinel clears",
       len(memo) == 12 and len(clear) == 10 and
       set(clear) == set(sent_direct) | set(sent_or), measured["A3"])

    # A4 the guard shape: read bb4, cmp it with the value about to be stored, je PAST the store
    # TWO guard shapes: (a) cmp directly against ds:0x68cbb4; (b) load bb4 into a
    # register, cmp that register, je PAST the store. Both must skip the memo store.
    guarded, unguarded = [], []
    for a in memo:
        i0 = bisect.bisect_left(order, a)
        found = None
        for k in range(max(0, i0 - 12), i0):
            b = order[k]
            mn, ops = ins[b]
            ops = ops.strip()
            if mn == "cmp" and re.search(r"\bds:0x68cbb4\b", ops):
                found = (b, "direct")
                break
            if mn == "mov" and re.search(r"\bds:0x68cbb4\b", ops) and not ops.startswith(("ds:", "DWORD")):
                reg = E.reg_norm(E.dst_reg(mn, ops) or "")
                for c in order[k + 1:i0 + 1]:
                    if ins[c][0] == "cmp" and reg in re.split(r",", ins[c][1].strip()):
                        found = (c, "via-" + reg)
                        break
                if found:
                    break
        je = [c for c in order[bisect.bisect_right(order, found[0]):bisect.bisect_right(order, found[0]) + 4]
              if ins[c][0] == "je" and int(ins[c][1].strip(), 16) > a] if found else []
        if je:
            guarded.append((a, found[0], found[1], je[0]))
        else:
            unguarded.append(a)
    measured["A4"] = "guarded=%d %s unguarded=%d %s" % (
        len(guarded), [(hex(x), hex(y), z, hex(w)) for x, y, z, w in guarded],
        len(unguarded), [hex(x) for x in unguarded])
    ck("A4 a LOCAL dedup guard (cmp of bb4 or of its loaded copy, + je PAST the store) sits at exactly 4 of the 12 memo sites; the other 8 refresh unconditionally",
       [x for x, _, _, _ in guarded] == [0x4EB6C7, 0x4EFEAA, 0x4F2201, 0x4F5C4A] and
       len(unguarded) == 8, measured["A4"])

    # A5 lockstep with the index, with the operand regex FIXED (M311's 6 stores)
    idx = [a for a in order if ins[a][0] == "mov" and
           re.match(r"(DWORD PTR )?ds:0x68cbb0,", ins[a][1].strip())]
    win32 = [a for a in stores if any(abs(a - b) <= 32 for b in idx)]
    inwin = [a for a in stores if any(abs(a - b) <= WIN for b in idx)]
    measured["A5"] = ("index_stores=%d %s; bb4<=32B=%d %s; bb4<=96B=%d %s" %
                      (len(idx), [hex(x) for x in idx], len(win32),
                       [hex(x) for x in win32], len(inwin), [hex(x) for x in inwin]))
    ck("A5 M311's 6 index stores reproduce (regex now operand-bared, both mov forms); the window is 5/22 at +-96 B and 3/22 at +-32 B - M311's unwindowed '3' is the 32-B reading, pairing still REFUSED",
       len(idx) == 6 and idx == [0x4E3476, 0x4E4DD0, 0x4EFE8E, 0x4F21E0, 0x4F5A7C, 0x4F5C36] and
       len(win32) == 3 and len(inwin) == 5, measured["A5"])

    # A6 the decisive windows, byte-pinned
    def pin(lo, hi, want):
        win = {a: (mn, ops.strip()) for a, mn, ops in E.window(lo, hi)}
        bad = [(hex(a), w, win.get(a)) for a, w in want
               if win.get(a) != tuple(w)]
        return bad
    p1 = pin(0x4EFE74, 0x4EFEAE, [
        (0x4EFE74, ["mov", "esi,DWORD PTR ds:0x68cbb0"]),
        (0x4EFE83, ["mov", "eax,ds:0x68cbb4"]),
        (0x4EFE8E, ["mov", "DWORD PTR ds:0x68cbb0,esi"]),
        (0x4EFEA0, ["cmp", "eax,esi"]),
        (0x4EFEA2, ["mov", "DWORD PTR ds:0x8f0d60,ecx"]),
        (0x4EFEA8, ["je", "0x4efed8"]),
        (0x4EFEAA, ["mov", "DWORD PTR ds:0x68cbb4,esi"])])
    p2 = pin(0x4F5C36, 0x4F5C50, [
        (0x4F5C36, ["mov", "DWORD PTR ds:0x68cbb0,ebx"]),
        (0x4F5C3C, ["mov", "ds:0x8f0d60,eax"]),
        (0x4F5C41, ["mov", "eax,ds:0x68cbb4"]),
        (0x4F5C46, ["cmp", "eax,ebx"]),
        (0x4F5C48, ["je", "0x4f5c69"]),
        (0x4F5C4A, ["mov", "DWORD PTR ds:0x68cbb4,ebx"])])
    measured["A6"] = "window1_bad=%s window2_bad=%s" % (p1, p2)
    ck("A6 both decisive windows pinned instruction-for-instruction (index store, fold, cmp bb4,new, je-skip, memo store, refresh calls)",
       not p1 and not p2, measured["A6"])

    # A7 image .data init for the pair
    v = struct.unpack("<II", at(BB0, 8))
    measured["A7"] = "init bb0=%s bb4=%s" % (hex(v[0]), hex(v[1]))
    ck("A7 the image carries BOTH dwords initialised to -1 (the 'nothing memoised yet' state)",
       v == (0xFFFFFFFF, 0xFFFFFFFF), measured["A7"])

    # A9 THE RIVAL - a store fed by the OTHER index would survive the memo law
    # (bb4 := ds:0x68cbac would keep the pair-follows invariant), so A2b alone is
    # the refutation: no store traces to a second index, a literal, or arithmetic.
    other_idx = [a for a in stores
                 if any(n in (producer(a)[2] or "") for n in ("ds:0x68cbac", "ds:0x68cbb8"))]
    print("-- A9 stores whose producer reads a neighbouring candidate index: %d %s"
          % (len(other_idx), [hex(x) for x in other_idx]))
    kinds_txt = ",".join("%s=%d" % (k, v) for k, v in sorted(kinds.items()))
    measured["A9"] = "kinds{%s} foreign_index_stores=%d non_index_or_sentinel=%d" % (
        kinds_txt, len(other_idx), len(memo) - kinds.get("reads-index", 0) - kinds.get("stack-slot", 0))
    ck("A9 rival 'bb4 is a second cursor fed from elsewhere' dies on the def-walk: every memo value = the current index or a caller slot",
       other_idx == [] and not any(k.startswith("other") for k in kinds) and
       kinds.get("reads-index") + kinds.get("stack-slot") == len(memo),
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
