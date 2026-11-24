#!/usr/bin/env python3
"""M369 - the noun of relations bit 0x8: COMMLINK (contact established).

M364 called 0x8 AT WAR off the declare-vendetta case keys; M367 found the page's
label for id 8 reads "Commlink".  This instrument decides the reconciliation from
the bytes, and retracts the AT WAR reading.

Acceptance:  python3 -u scripts/m369_commlink.py
The table is printed FIRST, then asserted; every gate carries a mutant in
scripts/m369_mutate.py.
"""
import glob
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M369_TEXT") or os.path.join(ROOT, "scratch/m574/text.txt")
LABELS = os.environ.get("M369_LABELS") or os.path.join(ROOT, "programs/labels.txt")
SHARDS = os.environ.get("M369_SHARDS") or os.path.join(ROOT, "ghidra_out/*.c")

BUILDER = 0x4DB480                      # FUN_004db480: the relations page builder
ADD_ITEM = 0x604FD2                     # add_item(text, id, 0)
A20 = (0x551A20, 0x551C32)              # FUN_00551a20: symmetric setter + implications
A7 = (0x442BB6, 0x442CCE)               # menu case 7 (option A): mask-8 guard
A8 = (0x442CD3, 0x442E42)               # menu case 8 (declare vendetta)
ACCEPT_PC = 0x442D7D                    # where the candidate row is built
SKIP_PC = 0x442CF5                      # loop increment branch
WAR = (0x5076D0, 0x507CD6)              # FUN_005076d0: the declare-vendetta writer
MASK8_SITES = 0                         # placeholder, measured below

out = []
gates = []


def say(s=""):
    out.append(s)


def gate(gid, ok, msg):
    gates.append((gid, bool(ok)))
    say("  %-5s %s  %s" % (gid, "PASS" if ok else "FAIL", msg))


# ------------------------------------------------------------------ text cache
ADDR = re.compile(r"\s*([0-9a-f]{6,8}):\s+((?:[0-9a-f]{2} )+)\s*\t(.*)$")


def load_text(path):
    ins = []
    with open(path, "r", errors="replace") as f:
        for line in f:
            m = ADDR.match(line)
            if m:
                ins.append((int(m.group(1), 16), re.sub(r"\s+", " ", m.group(3)).strip()))
    return ins


def win(ins, lo, hi):
    return [(a, t) for a, t in ins if lo <= a <= hi]


def push_imm(t):
    m = re.match(r"push +(?:0x)?([0-9a-f]+)$", t)
    return int(m.group(1), 16) if m else None


def call_tgt(t):
    m = re.match(r"call +(0x[0-9a-f]+)$", t)
    return int(m.group(1), 16) if m else None


def last_test_before(ws, addr):
    cand = [(a, t) for a, t in ws if a < addr and re.match(r"test +(bl|byte)", t) and "0x94d448" not in t]
    return cand[-1] if cand else (None, "")


# --------------------------------------------------------------- shard index
HDR = re.compile(r"^// ==== (\S+) @ (0x[0-9a-f]+) size=(\d+)")


def load_functions():
    funcs, per_file = {}, {}
    for path in sorted(glob.glob(SHARDS)):
        cur = None
        for i, line in enumerate(open(path, "r", errors="replace"), 1):
            m = HDR.match(line)
            if m:
                cur = (m.group(1), int(m.group(2), 16), int(m.group(3)))
                funcs.setdefault(cur[0], {"addr": cur[1], "size": cur[2], "body": []})
                per_file[(os.path.basename(path), i)] = cur[0]
            if cur is not None:
                funcs[re.match(r"^// ==== (\S+)", line).group(1)]["body"].append(line) if HDR.match(line) else funcs[cur[0]]["body"].append(line)
    return funcs, per_file


def shard_sites(pattern):
    """(file, line, func, text) for every match of pattern inside a function."""
    sites = []
    for path in sorted(glob.glob(SHARDS)):
        cur = None
        for i, line in enumerate(open(path, "r", errors="replace"), 1):
            m = HDR.match(line)
            if m:
                cur = m.group(1)
            if cur and pattern.search(line):
                sites.append((os.path.basename(path), i, cur, line.rstrip()))
    return sites


def parse_labels(path):
    raw = open(path, "rb").read().split(b"\n")
    return [x.rstrip(b"\r") for x in raw]


def rel_arg(line):
    """third arg of FUN_00551a20(a,b,MASK) when MASK is a literal."""
    m = re.search(r"FUN_00551a20\(([^;]*)\)", line)
    if not m:
        return None
    parts = [p.strip() for p in m.group(1).split(",")]
    if len(parts) < 3:
        return None
    try:
        return int(parts[-1], 0)
    except ValueError:
        return None


def main():
    ins = load_text(TEXT)
    L = parse_labels(LABELS)
    funcs = {}

    say("M369 - relations bit 0x8: reconciling M364's AT WAR with M367's Commlink label")
    say("")

    # ---------------------------------------------------------------- G1 builder
    say("G1  the page builder FUN_004db480 - 13 (id, label offset) rows, read from its body")
    body = []
    for path in sorted(glob.glob(SHARDS)):
        lines = open(path, "r", errors="replace").read().split("\n")
        for i, line in enumerate(lines):
            if line.startswith("// ==== FUN_004db480 "):
                body = lines[i:i + 500]
    rows, pend = [], None
    for line in body:
        m = re.search(r"uVar5 = (0x[0-9a-f]+|\d+);", line)
        if m:
            pend = int(m.group(1), 16)
        m = re.search(r"FUN_0061482f\(\*\(undefined4 \*\)\(DAT_00997b20 \+ (0x[0-9a-f]+)\)\)", line)
        if m and pend is not None:
            rows.append((pend, int(m.group(1), 16)))
            pend = None
    say("    rows (id, offset, element=off/4):")
    for i, (bid, off) in enumerate(rows, 1):
        say("      %2d  id=0x%-9x off=0x%-5x elem=%d" % (i, bid, off, off // 4))
    ids = [r[0] for r in rows]
    want_ids = [0x8, 0x10, 0x4, 0x2, 0x1, 0x1000, 0x2000, 0x20, 0x2000000, 0x400, 0x40000, 0x80000008, 0x80002000]
    say("    %d rows, ids %s" % (len(rows), "[" + ", ".join("0x%x" % i for i in ids) + "]"))
    gate("G1a", len(rows) == 13 and ids == want_ids,
         "13 add_item rows, ids exactly %s" % "".join("0x%x " % i for i in want_ids).strip())
    gate("G1b", all(off % 4 == 0 for _, off in rows) and len({o for _, o in rows}) == 13,
         "all 13 offsets are distinct multiples of 4 (a dword element index)")

    # ---------------------------------------------------------------- G2 labels
    say("")
    say("G2  id -> element -> labels.txt line (11+elem; line 10 is the count) -> text")
    want = {0x8: "Commlink", 0x10: "Vendetta", 0x4: "Truce", 0x2: "Treaty", 0x1: "Pact",
            0x1000: "I have infiltrator", 0x2000: "I want to talk", 0x20: "I want revenge",
            0x2000000: "I have surrendered", 0x400: "I shall betray",
            0x40000: "I am atrocity victim", 0x80000008: "Fight to the death",
            0x80002000: "Fix current status as permanent"}
    got, ok = {}, True
    say("      id          elem  line  text")
    for bid, off in rows:
        elem = off // 4
        ln = 11 + elem
        text = L[ln - 1].decode("latin-1") if ln - 1 < len(L) else "<past eof>"
        got[bid] = text
        say("      0x%-9x %4d  %4d  %s" % (bid, elem, ln, text))
        ok = ok and want.get(bid) == text
    gate("G2a", ok, "13/13 id -> text rows match; id 0x8 -> elem 875 -> line 886 = %r" % got.get(0x8))
    gate("G2b", got.get(0x8) == "Commlink" and got.get(0x10) == "Vendetta",
         "the two ids are separate nouns: 0x8=%r, 0x10=%r" % (got.get(0x8), got.get(0x10)))

    # ---------------------------------------------------------------- G3 case 8
    say("")
    say("G3  the declare-vendetta case block (0x442cd3..0x442e42): mask-8 reads, no bit-8 stores")
    w8 = win(ins, *A8)
    p8 = [(a, t) for a, t in w8 if t.startswith("push") and push_imm(t) == 8]
    c60 = [(a, t) for a, t in w8 if call_tgt(t) == 0x426D60]
    st8 = [(a, t) for a, t in w8 if re.match(r"mov .*0x94d44", t) or re.match(r"or .*0x94d44", t)
           or re.match(r"and .*0x94d44", t)]
    say("    push 0x8: %s" % ", ".join("%08x" % a for a, _ in p8))
    say("    call 0x426d60: %s" % ", ".join("%08x" % a for a, _ in c60))
    say("    writes to 0x94d448/0x94d468 in the block: %d" % len(st8))
    gate("G3a", len(p8) == 2 and len(c60) == 2,
         "exactly 2 mask-8 reads (%d pushes, %d calls)" % (len(p8), len(c60)))
    gate("G3b", len(st8) == 0,
         "the block STORES nothing into either relations dword (%d stores): 0x8 is tested here, not written" % len(st8))

    # ---------------------------------------------------------------- G4 polarity
    say("")
    say("G4  the guard's polarity: a zero pair skips the candidate, a hit accepts it")
    mask_jne = []
    for i, (a, t) in enumerate(w8):
        if call_tgt(t) == 0x426D60:
            nxt = w8[i + 1:i + 4]
            if any(x[1].startswith("test eax,eax") for x in nxt):
                j = [x for x in nxt if x[1].startswith("jne")]
                if j:
                    mask_jne.append(j[0])
    tgt = [int(re.search(r"0x([0-9a-f]+)$", t).group(1), 16) for _, t in mask_jne]
    extra = [(a, t) for a, t in w8 if t.startswith("jne") and int(t.split("0x")[-1], 16) == ACCEPT_PC
             and a not in [x for x, _ in mask_jne]]
    say("    jne after each mask ask: %s" % ", ".join("%08x -> %08x" % (a, g) for (a, _), g in zip(mask_jne, tgt)))
    say("    other jne to 0x%x: %s (the faction-exists bit test)" % (ACCEPT_PC, ", ".join("%08x" % a for a, _ in extra)))
    jumps_to_skip = [(a, t) for a, t in w8 if t.startswith("jmp") and "0x442cf5" in t]
    say("    jmp back to the loop increment: %d" % len(jumps_to_skip))
    gate("G4a", len(mask_jne) == 2 and len(extra) == 1 and all(g == ACCEPT_PC for g in tgt)
         and all(int(t.split("0x")[-1], 16) == ACCEPT_PC for _, t in extra),
         "3 jne land on 0x%x (two after the mask asks, one after 0x985b10's bit): the tested state ENABLES the option"
         % ACCEPT_PC)
    gate("G4b", len(jumps_to_skip) >= 1,
         "the fall-through is a jmp to the loop increment 0x%x (next candidate)" % SKIP_PC)

    # ---------------------------------------------------------------- G4c case 7
    say("")
    say("G4c the SAME two-direction mask-8 guard on the preceding option (case 7)")
    w7 = win(ins, *A7)
    p87 = [(a, t) for a, t in w7 if t.startswith("push") and push_imm(t) == 8]
    c67 = [(a, t) for a, t in w7 if call_tgt(t) == 0x426D60]
    j7 = [(a, t) for a, t in w7 if t.startswith("jne") and "0x442c1f" in t or t.startswith("je") and "0x442c40" in t]
    say("    push 0x8: %s | call 0x426d60: %s" % (", ".join("%08x" % a for a, _ in p87),
                                                ", ".join("%08x" % a for a, _ in c67)))
    gate("G4c", len(p87) == 2 and len(c67) == 2,
         "a non-war option also demands the mask in BOTH directions (%d reads): 8 is reachability, not a war state"
         % len(p87))

    # ---------------------------------------------------------------- G5 setter rules
    say("")
    say("G5  FUN_00551a20's byte-level implications: the OR 0x80000108 lives in the 0x10 branch only")
    wa = win(ins, *A20)
    ors = [(a, t) for a, t in wa if re.match(r"or +ebx,0x[0-9a-f]+", t)]
    tst = [(a, t) for a, t in wa if re.match(r"test +bl,0x[0-9a-f]+", t)]
    for a, t in tst:
        say("    test %08x  %s" % (a, t))
    for a, t in ors:
        say("    or   %08x  %s" % (a, t))
    or108 = [a for a, t in ors if t.endswith("0x80000108")]
    near = last_test_before(tst, or108[0]) if or108 else (None, "")
    say("    nearest test above the 0x80000108 OR: %08x %s" % near)
    gate("G5a", len(or108) == 1 and near[0] is not None and "0x10" in near[1] and "0x7" not in near[1],
         "the 0x80000108 OR is gated by test bl,0x10 (%s) - NOT by test bl,0x7 as M364's row 184 read"
         % near[1])
    branch7 = [a for a, t in wa if 0x551A35 <= a < 0x551ABF and t.endswith("0x80000108")]
    gate("G5b", len(branch7) == 0,
         "the 0x7 branch never ORs 0x80000108 (%d): making peace clears 0x10/0x40/0x8000/0x100000 and does NOT set 0x8"
         % len(branch7))
    # mask 8 alone: 8 & each branch test == 0
    say("    mask 8 alone and each branch test: 8&7=%d 8&1=%d 8&0x10=%d 8&0x17=%d"
        % (8 & 7, 8 & 1, 8 & 0x10, 8 & 0x17))
    gate("G5c", (8 & 7) == 0 and (8 & 1) == 0 and (8 & 0x10) == 0 and (8 & 0x17) == 0,
         "8 triggers no clear branch: setting it is a pure symmetric OR")

    # ---------------------------------------------------------------- G6 symmetric store
    say("")
    say("G6  the setter writes BOTH directions: two ORs, the index pair swapped between them")
    orstore = [(a, t) for a, t in wa if re.match(r"or +edx,ebx", t)]
    stores_after = []
    for a, _ in orstore:
        nxt = [(x, y) for x, y in wa if x > a][:2]
        stores_after += [x for x, y in nxt if y.startswith("mov DWORD PTR [eax],edx")]
    swap = [a for a, t in wa if 0x551BE6 < a < 0x551C09 and t == "mov eax,esi"]
    say("    or edx,ebx: %s | stores through [eax]: %d | index reload between the ORs: %s"
        % (", ".join("%08x" % a for a, _ in orstore), len(stores_after),
           "yes" if swap else "no"))
    gate("G6a", len(orstore) == 2 and len(stores_after) == 2 and bool(swap),
         "2 ORs (%d) + 2 stores (%d), and the second OR reloads the index from the other register %s"
         % (len(orstore), len(stores_after), "at %08x" % swap[0] if swap else "-"))

    # ---------------------------------------------------------------- G7 census
    say("")
    say("G7  every explicit mask-8 write site (literal mask & 8 at a setter call)")
    sites = shard_sites(re.compile(r"FUN_00551a20\("))
    m8 = [(f, ln, fn, rel_arg(t)) for f, ln, fn, t in sites]
    m8 = [s for s in m8 if s[3] is not None and s[3] & 8]
    say("    id  file:line          enclosing        mask")
    for f, ln, fn, mk in m8:
        say("      %-4s %s:%-6d %-16s 0x%x" % ("", f, ln, fn, mk))
    masks = sorted(s[3] for s in m8)
    say("    masks: %s" % ", ".join("0x%x" % m for m in masks))
    fns = sorted({s[2] for s in m8})
    plain8 = [s for s in m8 if s[3] == 8]
    say("    plain-8 writes (mask has no other bit): %d in %s"
        % (len(plain8), ", ".join(sorted({s[2] for s in plain8}))))
    gate("G7a", masks == [0x8, 0x8, 0x8, 0x18, 0x80000008, 0x80000018, 0x88000008, 0x88000008, 0x88000008, 0x88000008],
         "exactly 10 explicit bit-8 setter calls, masks %s" % " ".join("0x%x" % m for m in masks))
    gate("G7b", len(fns) == 8 and len(plain8) == 3,
         "8 distinct enclosing functions; 3 of the 10 write bit 8 with NO other bit (contact-only writes)")

    # ---------------------------------------------------------------- G8 byte verification
    say("")
    say("G8  the claim-critical sites are byte-verified: push <mask> -> call 0x551a20 in their own function")
    pinned = {"FUN_00429950": 0x42999D, "FUN_004dadd0": 0x4DAE13,
              "FUN_0056df40": 0x56F5AD, "FUN_00554d10": 0x554E88}
    ok_byte = 0
    for f, ln, fn, mk in m8:
        if fn not in funcs:
            for path in sorted(glob.glob(SHARDS)):
                lines = open(path, "r", errors="replace").read().split("\n")
                for i, line in enumerate(lines):
                    m = HDR.match(line)
                    if m:
                        body, j = [], i
                        while j < len(lines) and not (j > i and HDR.match(lines[j])):
                            body.append(lines[j])
                            j += 1
                        funcs[m.group(1)] = {"addr": int(m.group(2), 16), "size": int(m.group(3)),
                                             "body": body}
        fn_info = funcs.get(fn)
        if not fn_info:
            say("      %-16s MISSING from shard headers" % fn)
            continue
        ws = win(ins, fn_info["addr"], fn_info["addr"] + fn_info["size"] - 1)
        hit = []
        for k, (a, t) in enumerate(ws):
            if call_tgt(t) == 0x551A20:
                back = ws[max(0, k - 6):k + 1]
                pm = [push_imm(t2) for _, t2 in back if t2.startswith("push")]
                pm = [x for x in pm if x is not None]
                if pm and (pm[-1] & 8):
                    hit.append((a, pm[-1]))
        say("      %-16s @0x%06x -> %s" % (fn, fn_info["addr"],
                                           ", ".join("%08x/0x%x" % h for h in hit) or "none"))
        if fn in pinned and any(a == pinned[fn] and (m & 8) for a, m in hit):
            ok_byte += 1
    gate("G8a", ok_byte == len(pinned),
         "%d/%d claim-critical sites carry the exact push-immediate at the pinned address"
         % (ok_byte, len(pinned)))

    # ---------------------------------------------------------------- G9 event semantics
    say("")
    say("G9  what the non-menu writers are: first contact (pod) and the council")
    pod = funcs.get("FUN_0056df40")
    council = funcs.get("FUN_00429950")
    podtxt = "\n".join(pod["body"]) if pod else ""
    cntxt = "\n".join(council["body"]) if council else ""
    pod_goody = podtxt.count("GOODYPOD")
    pod_guard = re.search(r"\[\(uVar13 \* 0x82f \+ uVar9\) \* 4\] & 8\) == 0", podtxt)
    cnt_call = cntxt.count("CALLSCOUNCIL")
    cnt_loop = re.search(r"for \(local_c = 1; local_c < (\d+); local_c = local_c \+ 1\)", cntxt)
    cnt_inner = re.search(r"for \(local_8 = 1; local_8 < local_c;", cntxt)
    say("    FUN_0056df40 GOODYPOD literals: %d | (rel&8)==0 guard before the set: %s"
        % (pod_goody, "yes" if pod_guard else "no"))
    say("    FUN_00429950 CALLSCOUNCIL literals: %d | outer loop bound: %s | inner loop: %s"
        % (cnt_call, cnt_loop.group(1) if cnt_loop else "?", "yes" if cnt_inner else "no"))
    gate("G9a", pod_goody >= 2 and bool(pod_guard),
         "the pod handler only contacts a faction it has NOT met ((rel & 8)==0) and then sets 8 - first contact")
    gate("G9b", cnt_call >= 1 and bool(cnt_loop) and cnt_loop.group(1) == "8" and bool(cnt_inner),
         "the council routine sets 8 for every ordered faction pair (1..7 x <outer) as the council convenes")

    # ---------------------------------------------------------------- G10 war writer
    say("")
    say("G10 the declare path FUN_005076d0 sets 0x10 and never names 8")
    ww = win(ins, *WAR)
    p10 = [(a, t) for a, t in ww if t.startswith("push") and push_imm(t) == 0x10]
    p8w = [(a, t) for a, t in ww if t.startswith("push") and push_imm(t) == 8]
    calls_a20 = [(a, t) for a, t in ww if call_tgt(t) == 0x551A20]
    say("    push 0x10: %s | push 0x8: %d | calls to 0x551a20: %s"
        % (", ".join("%08x" % a for a, _ in p10), len(p8w),
           ", ".join("%08x" % a for a, _ in calls_a20)))
    gate("G10a", len(p10) == 2 and len(p8w) == 0,
         "the war write is mask 0x10 on both exits (%d push 0x10, %d push 0x8): bit 8 arrives only as a20's implication"
         % (len(p10), len(p8w)))

    # ---------------------------------------------------------------- rivals
    say("")
    say("R1  RIVAL '0x8 = AT WAR' (M364) - refuted on the printed numbers")
    say("      war bit written by the declare path: 0x10 (G10a); page noun of 0x10: %r (G2a)" % got.get(0x10))
    say("      bit-8 writes that are NOT war: pod first contact (G9a), council convening (G9b)")
    say("      bit-8 reads in the vendetta block are guards that ENABLE the option (G4a/G4b)")
    gate("R1", got.get(0x10) == "Vendetta" and len(p8w) == 0 and pod_goody >= 2 and len(st8) == 0,
         "AT WAR is 0x10; 0x8 is the contact precondition it implies - RETRACT M364's 0x8 noun")

    say("")
    say("R2  RIVAL 'the Commlink label is the other dword half' - refuted")
    plain = [i for i in ids if not (i & 0x80000000)]
    high = [i for i in ids if i & 0x80000000]
    say("      11 plain ids %s | 2 composite high ids %s" % (plain, ["0x%x" % h for h in high]))
    gate("R2", got.get(0x8) == "Commlink" and got.get(0x80000008) == "Fight to the death" and len(plain) == 11,
         "plain 8 -> %r, high-dword bit 8 is only reachable as 0x80000008 -> %r"
         % (got.get(0x8), got.get(0x80000008)))

    say("")
    say("R3  RIVAL '0x8 is a bookkeeping met-flag with no page noun' - refuted")
    gate("R3", 0x8 in [r[0] for r in rows],
         "id 8 is builder row 1 - a page noun with its own label (%r)" % got.get(0x8))

    say("")
    say("R4  RIVAL 'M364's block membership proves war' - refuted by the same guard on a non-war option")
    gate("R4", len(p87) == 2 and len(st8) == 0,
         "case 7 pairs the same two-direction mask-8 reads (%d) with zero stores; the guard is reachability"
         % len(p87))

    # ---------------------------------------------------------------- accept
    say("")
    npass = sum(1 for _, ok in gates if ok)
    say("SUMMARY  %d/%d gates" % (npass, len(gates)))
    digest = hashlib.sha256(("\n".join(out)).encode()).hexdigest()[:16]
    say("DIGEST   %s" % digest)
    print("\n".join(out))
    if npass == len(gates):
        print("\nPASS M369: %d/%d gates digest %s" % (npass, len(gates), digest))
        return 0
    bad = [g for g, ok in gates if not ok]
    print("\nFAIL M369: %d/%d gates failed %s digest %s" % (len(bad), len(gates), bad, digest))
    return 1


if __name__ == "__main__":
    sys.exit(main())
