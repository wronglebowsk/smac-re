"""sim.grantcall - rung B35's RUN and its GATES (BUILD_SPINE §B35).

B34 closed the completion leg and left two things unmodeled: WHICH grant writer fired in
the recorded run, and what `FUN_0059ce10`'s 11 literal-item sites are.  This rung asks
"who calls the grant family" with three independent measurements and then scores them
against the game's own recorded bytes:

  * the DIRECT call sites in the .text dump - every `call 0x4e47d0` (the founder) and
    `call 0x59ce10` (the new-game setup), each resolved to a host function by ADDRESS
    RANGE (the Ghidra index) and cross-checked against the index's own `n_callers`;
  * the ITEM SITES - the pushes before each grant call, decoded as (item, base, set-flag),
    plus the mapper `FUN_00507410`'s own arithmetic (byte = item>>3, mask = 1<<(item&7)),
    which is what makes an item id and a bitmap bit the same number;
  * the recorded BIRTHS - a base that first appears mid-run carries whatever bitmap its
    creator wrote.  A founder birth is ZERO-then-OR (a 4+1 byte LEA-then-zero pair before
    every OR); an API grant only ORs.  That asymmetry is the separator, not the bit value.

DECLARED UNMODELED: which of the founder's three call sites fired per birth (the trace has
no call stack); why base 20 was born EMPTY while 19/21 got bit 1; which of the 27 mid-round
callers of `0x4e44f0` added bits 3 and 6 at r5/r7.  Zero box, zero /proc, zero gdb.
"""
import bisect
import hashlib
import os
import re
import sys

from . import facoracle as fo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("SMAC_B35_TEXT") or os.path.join(ROOT, "scratch", "m574", "text.txt")
INDEX = os.path.join(ROOT, "ghidra_out", "index.csv")

FOUNDER = 0x4e47d0        # FUN_004e47d0 - THE founder; grants the new base's starting items
NEWGAME = 0x59ce10        # FUN_0059ce10 - new-game/scenario setup; 11 literal-item grants
API = 0x4e44f0            # FUN_004e44f0(item, base, set) - the set/clear API
MAPPER = 0x507410         # FUN_00507410(item, &byte, &mask) - item i -> bit i
BITMAP = 0x95da9c         # base record +0x8c (B34's derived constant)
STRIDE = 0x130            # 304-byte base record (M342/B34)

SITES_FOUNDER = [0x4CCBDD, 0x59D894, 0x5A01F8]
SITES_NEWGAME = [0x5A1579]
HOSTS_FOUNDER = ["FUN_004cca50", "FUN_0059ce10", "FUN_0059ec90"]
HOST_NEWGAME = "FUN_005a0fa0"
ITEMS_NEWGAME = [6, 3, 7, 27, 8, 4, 6, 3, 6, 3, 27]
ITEMS_FOUNDER = [1, 3, 6, 7, 3, 6, 7, 26]
FOUNDER_SIG = {1, 3, 6, 7, 26}
NEWGAME_SET = {3, 4, 6, 7, 8, 27}

# The founder's bitmap init: a LEA of the window, a zero of the dword and the 5th byte,
# both through the LEA'd register - so no `95da9c`-operand store grep can ever see them.
INIT_SEQ = [(0x4E4A5D, "lea", "eax,[esi+0x95da9c]"), (0x4E4A63, "xor", "ecx,ecx"),
            (0x4E4A65, "mov", "DWORD PTR [eax],ecx"), (0x4E4A67, "mov", "BYTE PTR [eax+0x4],cl")]
FIRST_OR = 0x4E4B5A
ZERO_AT = 0x4E4A65

# Pinned on the first real run (G10 asserts the run still reproduces them).
ANCHOR = "fa541d0a2445cacf"
SITES_DIGEST = "995a09b96d05da54"
ITEMS_DIGEST = "f1c53db1f332d830"
BIRTH_DIGEST = "a814c53516649303"
DELTA_DIGEST = "5a5c124ccb32e35c"

FAIL = []
INSN = re.compile(r"^\s+([0-9a-f]{4,8}):\t[0-9a-f ]+\t(\S+)(?:\s+(.*))?$")


def gate(gid, cond, msg):
    ok = bool(cond)
    print("%s %s %s" % ("ok  " if ok else "BAD ", gid, msg))
    if not ok:
        FAIL.append(gid)
    return ok


def sha16(rows):
    h = hashlib.sha256()
    for r in rows:
        h.update(repr(r).encode("utf-8"))
    return h.hexdigest()[:16]


def load_dump(path=TEXT):
    """(addr, mnemonic, operands) for every instruction line of the .text dump."""
    ins = []
    with open(path, errors="replace") as fh:
        for ln in fh:
            m = INSN.match(ln)
            if m:
                ins.append((int(m.group(1), 16), m.group(2), (m.group(3) or "").strip()))
    return ins


def load_funcs(path=INDEX):
    rows = []
    with open(path) as fh:
        head = fh.readline().strip().split(",")
        for ln in fh:
            if not ln.strip() or ln.startswith("#"):
                continue
            d = dict(zip(head, ln.rstrip("\n").split(",")))
            rows.append((int(d["addr"], 16), int(d["size_bytes"]), d["name"], int(d["n_callers"])))
    rows.sort()
    return rows


def owners_of(ins, funcs):
    starts = [r[0] for r in funcs]
    out = []
    for a, _m, _o in ins:
        i = bisect.bisect_right(starts, a) - 1
        s, sz, n, _c = funcs[i]
        out.append(n if s <= a < s + sz else None)
    return out


def pushes_before(ins, owners, i, want=3):
    """The nearest `want` pushes before instruction i, never crossing a call or the fn wall."""
    args, fn, j = [], owners[i], i - 1
    while j >= 0 and owners[j] == fn and len(args) < want and i - j <= 8:
        if ins[j][1] == "call":
            break
        if ins[j][1] == "push":
            args.append(ins[j][2])
        j -= 1
    return list(reversed(args))


def call_sites(ins, owners, target):
    return [(a, owners[i], pushes_before(ins, owners, i))
            for i, (a, m, o) in enumerate(ins)
            if m == "call" and o.strip() == "0x%x" % target]


def fn_body(ins, owners, name):
    return [i for i, h in enumerate(owners) if h == name]


def births(samples):
    """Bases whose FIRST recorded sample is after r0: the birth oracle, one row each."""
    seen, out = {}, []
    for si, (ev, r, bases) in enumerate(samples):
        for idx, name, rec in bases:
            if idx in seen:
                continue
            seen[idx] = si
            if si:
                out.append((idx, name, tuple(sorted(fo.bits_of(rec))), si, r, fo.head_of(rec)))
    return out


def changes(samples):
    prev, out = {}, []
    for si, (ev, r, bases) in enumerate(samples):
        for idx, name, rec in bases:
            cur = set(fo.bits_of(rec))
            if idx in prev and cur != prev[idx]:
                out.append((idx, name, tuple(sorted(prev[idx])), tuple(sorted(cur)),
                            r, fo.head_of(rec)))
            prev[idx] = cur
    return out


def main(argv=None):
    ins = load_dump()
    funcs = load_funcs()
    owners = owners_of(ins, funcs)
    print("dump %s: %d instructions, %d functions indexed" % (os.path.basename(TEXT), len(ins), len(funcs)))

    # ---------------- G1/G2: who calls the two writers ----------------
    sf = call_sites(ins, owners, FOUNDER)
    sn = call_sites(ins, owners, NEWGAME)
    print("\nTABLE 1 - direct calls into the grant family")
    for a, h, _args in sf:
        print("  call 0x%x  site 0x%x  host %s" % (FOUNDER, a, h))
    for a, h, _args in sn:
        print("  call 0x%x  site 0x%x  host %s" % (NEWGAME, a, h))
    site_rows = [(a, h) for a, h, _ in sf] + [(a, h) for a, h, _ in sn]
    sd = sha16(site_rows)
    print("  site-table digest %s" % sd)

    nc = {n: c for _a, _s, n, c in funcs}
    gate("G1", [a for a, _h, _r in sf] == SITES_FOUNDER and [a for a, _h, _r in sn] == SITES_NEWGAME,
         "3 sites into FUN_004e47d0 %s and 1 into FUN_0059ce10 %s (digest %s)"
         % (["0x%x" % a for a, _h, _r in sf], ["0x%x" % a for a, _h, _r in sn], sd))
    hosts_f = [h for _a, h, _r in sf]
    gate("G2", sorted(hosts_f) == sorted(HOSTS_FOUNDER) and len(hosts_f) == nc["FUN_004e47d0"]
         and sn[0][1] == HOST_NEWGAME and nc["FUN_0059ce10"] == 1 and None not in (hosts_f + [sn[0][1]]),
         "hosts %s (index n_callers %d) / %s (n_callers %d), 0 unattributed"
         % (hosts_f, nc["FUN_004e47d0"], sn[0][1], nc["FUN_0059ce10"]))

    # ---------------- G3/G4: the item sites ----------------
    b59 = fn_body(ins, owners, "FUN_0059ce10")
    api = [(ins[i][0], pushes_before(ins, owners, i)) for i in b59
           if ins[i][1] == "call" and ins[i][2].strip() == "0x%x" % API]
    print("\nTABLE 2 - FUN_0059ce10's grants (call 0x%x), items in ADDRESS order" % API)
    for a, args in api:
        print("  site 0x%x  push-order %s -> item %s, base %s, set %s"
              % (a, args, args[2] if len(args) > 2 else "?", args[1] if len(args) > 1 else "?",
                 args[0] if args else "?"))
    items59 = [int(args[2], 16) for _a, args in api if len(args) == 3]
    regbase = [a for a, args in api
               if len(args) == 3 and args[0] == "0x1" and re.fullmatch(r"[a-z]{2,3}", args[1])]
    odd = [a for a, args in api if len(args) == 3 and args[0] != "0x1"]
    id_d = sha16([(a, args) for a, args in api])
    print("  item order %s, distinct %s, digest %s" % (items59, sorted(set(items59)), id_d))
    if odd:
        print("  ARG-ORDER ANOMALY at %s: the base is pushed FIRST and the set flag LAST - the"
              " item (last push) is unaffected" % ["0x%x" % a for a in odd])
    gate("G3", len(api) == 11 and items59 == ITEMS_NEWGAME and len(regbase) == 10 and len(odd) == 1,
         "11 API grants, items %s; 10/11 (set 0x1, base register), 1 anomalous order at %s"
         % (items59, ["0x%x" % a for a in odd]))

    b4e = fn_body(ins, owners, "FUN_004e47d0")
    mpr = [(ins[i][0], pushes_before(ins, owners, i)) for i in b4e
           if ins[i][1] == "call" and ins[i][2].strip() == "0x%x" % MAPPER]
    print("\nTABLE 3 - FUN_004e47d0's grants (call 0x%x mapper), items in ADDRESS order" % MAPPER)
    for a, args in mpr:
        print("  site 0x%x  push-order %s -> item %s" % (a, args, args[2] if len(args) > 2 else "?"))
    lit = [int(args[2], 16) for _a, args in mpr
           if len(args) == 3 and re.fullmatch(r"0x[0-9a-f]{1,3}", args[2])]
    dyn = [a for a, args in mpr
           if len(args) != 3 or not re.fullmatch(r"0x[0-9a-f]{1,3}", args[2])]
    gate("G4", len(mpr) == 10 and lit == ITEMS_FOUNDER and len(dyn) == 2,
         "10 mapper grants: 8 literal items %s (%d distinct) + 2 computed at %s"
         % (lit, len(set(lit)), ["0x%x" % a for a in dyn]))

    # ---------------- G5: one mapper, so item i IS bit i ----------------
    mapb = [(ins[i][0], ins[i][1], ins[i][2]) for i in fn_body(ins, owners, "FUN_00507410")]
    print("")
    print("TABLE 4 - the mapper FUN_00507410 (%d insns)" % len(mapb))
    for a, m, o in mapb:
        print("  0x%x %-5s %s" % (a, m, o))
    forms = {(m, o) for _a, m, o in mapb}
    apib = [(ins[i][0], ins[i][1], ins[i][2]) for i in fn_body(ins, owners, "FUN_004e44f0")]
    stride = {"lea ecx,[eax+eax*8]", "lea edx,[eax+ecx*2]", "shl edx,0x4"}
    hit = {(m, o) for _a, m, o in apib} & set()
    print("  the API computes the %d-byte record stride instead of embedding it:" % STRIDE)
    for a, m, o in apib:
        if ("%s %s" % (m, o)) in {"lea ecx,[eax+eax*8]", "lea edx,[eax+ecx*2]", "shl edx,0x4"} or \
           "0x95da9c" in o:
            print("  0x%x %-5s %s" % (a, m, o))
    api_st = [(a, m) for a, m, o in apib if m in ("or", "and") and o.startswith("BYTE PTR [eax],")]
    print("  the API's two bitmap stores: %s" % ["0x%x %s" % (a, m) for a, m in api_st])
    gate("G5", len(mapb) == 17 and ("and", "ecx,0x7") in forms and ("sar", "eax,0x3") in forms
         and ("shl", "eax,cl") in forms
         and {"%s %s" % (m, o) for _a, m, o in apib} >= stride
         and [m for _a, m in api_st] == ["or", "and"],
         "mapper = byte(item>>3) + mask(1<<(item&7)); API stride = (base*19)<<4 = base*0x%x,"
         " OR at 0x4e4528 / AND at 0x4e4546" % STRIDE)

    # ---------------- G6: the founder's ZERO-then-OR birth signature ----------------
    by_addr = {a: (m, o) for a, m, o in ins}
    seq = [(a, by_addr[a][0], by_addr[a][1]) for a in [x[0] for x in INIT_SEQ] if a in by_addr]
    print("")
    print("TABLE 5 - the founder's bitmap init (the birth signature)")
    for a, m, o in seq:
        print("  0x%x %-5s %s" % (a, m, o))
    ors = [ins[i][0] for i in b4e if ins[i][1] == "or" and "0x95da9c" in ins[i][2]]
    print("  %d OR stores in the founder, the first at 0x%x (after the zero at 0x%x)"
          % (len(ors), min(ors) if ors else 0, ZERO_AT))
    gate("G6", seq == INIT_SEQ and len(ors) == 7 and bool(ors) and min(ors) > ZERO_AT,
         "LEA+XOR+DWORD-zero+5th-byte-zero through the LEA'd register at 0x%x..0x%x, then %d ORs"
         % (INIT_SEQ[0][0], INIT_SEQ[-1][0], len(ors)))

    # ---------------- G7: the recorded births ----------------
    S = fo.load_trace()
    bt = births(S)
    print("")
    print("TABLE 6 - bases that first appear MID-RUN in %s (%d samples)"
          % (os.path.basename(fo.TRACE), len(S)))
    for idx, name, bits, si, r, head in bt:
        print("  idx %2d %-22r born at sample %2d (r%s) bits %s head %d"
              % (idx, name, si, r, list(bits), head))
    bd = sha16(bt)
    gate("G7", len(bt) == 3 and [(x[0], x[2]) for x in bt] == [(19, (1,)), (20, ()), (21, (1, 3))],
         "3 births, bits %s (digest %s)" % ([list(x[2]) for x in bt], bd))

    # ---------------- G8: score the two entries on the births ----------------
    def cover(sig):
        hit = [x for x in bt if set(x[2]) <= sig]
        nonvac = [x for x in bt if x[2]]
        return len(hit), len(nonvac), [x[0] for x in hit]

    fh_, fnv, fids = cover(FOUNDER_SIG)
    nh_, nnv, nids = cover(NEWGAME_SET)
    print("")
    print("TABLE 7 - which entry explains the births")
    print("  founder  signature %s -> %d/%d births (non-vacuous %d), hits %s"
          % (sorted(FOUNDER_SIG), fh_, len(bt), fnv, fids))
    print("  new-game set        %s -> %d/%d births (non-vacuous %d), hits %s"
          % (sorted(NEWGAME_SET), nh_, len(bt), nnv, nids))
    miss = [x[0] for x in bt if x[2] and not set(x[2]) <= NEWGAME_SET]
    print("  bit 1 (item 1) is in NO new-game item, so it is unexplained on rows %s" % miss)
    gate("G8", fh_ == 3 and fnv == 2 and nh_ == 1 and len(miss) == 2,
         "founder 3/3 (2 discriminating) vs new-game 1/3 - the founder fired, the 11-item path did not")

    # ---------------- G9: a mid-round change is NOT a birth ----------------
    ch = changes(S)
    print("")
    print("TABLE 8 - every recorded bitmap change")
    for idx, name, pb, cb, r, head in ch:
        shape = "OR" if set(pb) <= set(cb) else "REPLACE"
        print("  idx %2d %-22r r%s  %s -> %s  %-7s added %s lost %s head %d"
              % (idx, name, r, list(pb), list(cb), shape,
                 sorted(set(cb) - set(pb)), sorted(set(pb) - set(cb)), head))
    cd = sha16(ch)
    ors_ = [c for c in ch if set(c[2]) <= set(c[3])]
    rep = [c for c in ch if not set(c[2]) <= set(c[3])]
    in_sig = [c for c in ors_ if set(c[3]) - set(c[2]) <= FOUNDER_SIG]
    birth_shaped = [c for c in ch if set(c[3]) <= FOUNDER_SIG and not set(c[2]) <= set(c[3])]
    print("  shapes: %d OR (%d of them add ONLY founder-signature bits, so bit identity alone"
          " cannot separate them from a birth), %d REPLACE (loss-capable, B34's COPY family);"
          " %d birth-shaped (zero-then-OR)"
          % (len(ors_), len(in_sig), len(rep), len(birth_shaped)))
    gate("G9", len(ch) == 6 and len(ors_) == 4 and len(rep) == 2 and len(in_sig) == 2
         and birth_shaped == [],
         "6 changes = 4 OR (+2/+8/+3/+6) + 2 REPLACE ([1]->[4], [27]->[4]); no row carries the"
         " founder's ZERO, so none is a birth")

    # ---------------- G10: anchors survive a second pass ----------------
    ins2 = load_dump()
    ow2 = owners_of(ins2, funcs)
    sf2 = call_sites(ins2, ow2, FOUNDER)
    sn2 = call_sites(ins2, ow2, NEWGAME)
    d2 = sha16([(a, h) for a, h, _r in sf2] + [(a, h) for a, h, _r in sn2])
    api2 = [(ins2[i][0], pushes_before(ins2, ow2, i)) for i in fn_body(ins2, ow2, "FUN_0059ce10")
            if ins2[i][1] == "call" and ins2[i][2].strip() == "0x%x" % API]
    id2 = sha16(api2)
    S2 = fo.load_trace()
    bd2, cd2 = sha16(births(S2)), sha16(changes(S2))
    print("")
    print("  second pass: sites %s items %s births %s deltas %s" % (d2, id2, bd2, cd2))
    run_d = sha16([sd, id_d, bd, cd, len(ins)])
    print("  run digest %s (dump %d insns)" % (run_d, len(ins)))
    gate("G10", (sd, id_d, bd, cd) == (d2, id2, bd2, cd2) and (sd, id_d, bd, cd) ==
         (SITES_DIGEST, ITEMS_DIGEST, BIRTH_DIGEST, DELTA_DIGEST) and len(ins) == len(ins2)
         and run_d == ANCHOR,
         "second pass over the dump and a fresh trace decode reproduce all four digests + the run digest")

    # ---------------- G11: the rivals FAIL on the printed numbers ----------------
    r1 = cover(NEWGAME_SET)[0]                      # 1/3
    r2 = len([x for x in bt if not x[2]])           # 1/3 - "nothing grants at birth"
    r3 = len(birth_shaped)                          # 0/6 births
    print("")
    print("RIVALS - each scored on the tables above")
    print("  R1 'the 11-item new-game path made these births'      -> %d/3 (needs bit 1)" % r1)
    print("  R2 'no grant writer runs at birth'                    -> %d/3 (only the empty row)" % r2)
    print("  R3 'the recorded mid-round gains are births'          -> %d/6 (no ZERO anywhere)" % r3)
    gate("G11", r1 == 1 and r2 == 1 and r3 == 0,
         "R1 1/3, R2 1/3, R3 0/6 - the founder model is the only one the bytes do not refute")

    print("")
    if FAIL:
        print("FAIL B35: %d/%d gates red: %s" % (len(FAIL), 11, FAIL))
        return 1
    print("PASS B35: 11/11 gates  digest %s" % ANCHOR)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
