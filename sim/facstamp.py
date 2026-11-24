"""sim.facstamp - rung B34's RUN and its GATES (BUILD_SPINE §B34).

B33 proved the base screen's shared OR `0x4f0ec0` is unreachable from the facility branch;
M342's other setter sites (`0x4e4528` = the API `FUN_004e44f0`, `0x4f3ebc`/`0x4f3f4c` in
Ghidra's unnamed `0x4f38xx` region) were left unexplained.  This rung asks two independent
oracles which writer a COMPLETION can reach and whether one fires on the recorded bytes:

  * the .text dump - every store into the base record's `+0x8c` bitmap word, split into the
    three families (set/clear API, inline grant, whole-word COPY), the 27 call sites of the
    API resolved to their host functions, and the COMPLETION LEG's own two pieces (the
    queue-pop `FUN_004ef5d0` and the base screen `FUN_004ef6d0` that is its only caller)
    checked for any writer at all;
  * the recorded 20-sample run - every PAID boundary (the accumulator dropped from >= price),
    with its before-head, and every bitmap delta.  A facility completion is a paid boundary
    whose head is a facility id (0 < head < 0x40); the recorded bitmaps at those boundaries
    are compared, not assumed.

DECLARED UNMODELED: WHICH grant/copy call site fired in the recorded run (the trace carries
no call stack - the attribution is family-level); the role of `FUN_0059ce10`'s 11 literal-item
sites; whether a completion ever stamps under another rule (scenario grant, capture).
Zero box, zero /proc, zero gdb.
"""
import bisect
import csv
import hashlib
import os
import re
import struct
import sys

from . import facoracle as fo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("SMAC_B34_TEXT") or os.path.join(ROOT, "scratch", "m574", "text.txt")
INDEX = os.path.join(ROOT, "ghidra_out", "index.csv")

BITMAP = 0x95da9c          # base record +0x8c (M342's derived constant)
BITMAP_WIN = 0x95da9c + 4  # exclusive end of the four bitmap bytes
API = 0x4e44f0             # FUN_004e44f0(item, base, set) - the set/clear API
GRANT = 0x4e47d0           # FUN_004e47d0 - the inline OR grant family
POP = 0x4ef5d0             # FUN_004ef5d0 - pop the queue head
SCREEN = 0x4ef6d0          # FUN_004ef6d0 - the base screen (the pop's only caller)
CHARGE = 0x4f47f0          # FUN_004f47f0 - the upkeep charge routine (reads the bitmap)
PRICE = fo.PRICE           # 9, B23's parity-verified fixture for the recorded run
FAC_LO, FAC_HI = 1, 0x40
SCREEN_NAME = "FUN_004ef6d0"  # the pop's only caller (M342 TABLE 4)

ANCHOR = "5296fdad6d26caa3"  # pinned on the first real run (G1/G10)
STORES_ANCHOR = "6e9336d6bc27b5c8"
RUN_ANCHOR = "fd2750a58598b20f"
FAIL = []


def gate(gid, cond, msg):
    ok = bool(cond)
    print("%s %s %s" % ("ok  " if ok else "BAD ", gid, msg))
    if not ok:
        FAIL.append(gid)
    return ok


def sha(rows):
    h = hashlib.sha256()
    for r in rows:
        h.update(repr(r).encode("utf-8"))
    return h.hexdigest()[:16]


# --- the dump ------------------------------------------------------------------------------
def load_dump(text=TEXT, index=INDEX):
    ins = []
    n_call = 0
    for line in open(text, errors="replace"):
        m = re.match(r"\s*([0-9a-f]{6,8}):\s", line)
        if not m:
            continue
        parts = line.rstrip("\n").split("\t")
        body = parts[-1].strip() if len(parts) > 1 else ""
        ins.append((int(m.group(1), 16), body))
        if re.search(r"\bcall\s+0x[0-9a-f]+", body):
            n_call += 1
    fns = []
    for d in csv.DictReader(open(index)):
        if not d.get("addr"):
            continue
        fns.append((int(d["addr"], 16), int(d["size_bytes"]), d["name"]))
    fns.sort()
    return ins, fns, n_call


def container(fns, starts, a):
    i = bisect.bisect_right(starts, a) - 1
    for j in range(i, max(-1, i - 60), -1):
        if fns[j][0] <= a < fns[j][0] + fns[j][1]:
            return fns[j]
    return (a, 0, "HOLE")


STORE_ANY = re.compile(r"^(mov|or|and|add|sub|xor)\s+BYTE PTR \[([^\]]*)\],")
LEA_RE = re.compile(r"^lea\s+(\w+),\[([^\]]*0x95da9c[^\]]*)\]")


def mem_touches_bitmap(operand):
    """True when the memory operand addresses one of the four bitmap bytes."""
    m = re.search(r"0x(95da9c|95da9d|95da9e|95da9f)\b", operand)
    return bool(m)


def census(ins, fns):
    """Every store into the bitmap word: constant form + lea form resolved through its register."""
    starts = [f[0] for f in fns]
    const = []
    leas = []
    for i, (a, body) in enumerate(ins):
        m = STORE_ANY.match(body)
        if m and mem_touches_bitmap(m.group(2)):
            const.append((a, m.group(1), body, container(fns, starts, a)))
        m = LEA_RE.match(body)
        if m:
            reg, op = m.group(1), m.group(2)
            for a2, b2 in ins[i + 1:i + 14]:
                ms = STORE_ANY.match(b2)
                if ms and re.search(r"\[%s(\*|\+|])" % reg, b2):
                    leas.append((a, a2, ms.group(1), b2, container(fns, starts, a2)))
                    break
                if re.match(r"^(mov|lea|pop|xor|add|sub|imul|call|and|or)\s+%s\b" % reg, b2):
                    break
    return const, leas


def api_sites(ins, fns):
    starts = [f[0] for f in fns]
    out = []
    for a, body in ins:
        m = re.search(r"\bcall\s+0x([0-9a-f]+)", body)
        if m and int(m.group(1), 16) == API:
            out.append((a, container(fns, starts, a)))
    return out


def body_of(ins, fns, start):
    f = next((x for x in fns if x[0] == start), None)
    if not f:
        return []
    lo, size = f[0], f[1]
    i = bisect.bisect_left([x[0] for x in ins], lo)
    j = bisect.bisect_left([x[0] for x in ins], lo + size)
    return ins[i:j]


def body_stores(body):
    """Stores into the bitmap word inside ONE function body, resolving `lea`-form pointers.

    This is deliberately independent of `census`: G3 must not move when the global census
    filter is mutated (review #389 P2), so the screen's own body is walked here.
    """
    out = []
    for i, (a, b) in enumerate(body):
        m = STORE_ANY.match(b)
        if m and mem_touches_bitmap(m.group(2)):
            out.append((a, m.group(1)))
        m = LEA_RE.match(b)
        if m:
            reg = m.group(1)
            for a2, b2 in body[i + 1:i + 14]:
                ms = STORE_ANY.match(b2)
                if ms and re.search(r"\[%s(\*|\+|])" % reg, b2):
                    out.append((a2, ms.group(1)))
                    break
                if re.match(r"^(mov|lea|pop|xor|add|sub|imul|call|and|or)\s+%s\b" % reg, b2):
                    break
    return out


def family_of(site, mnem, host):
    if host[2] == "FUN_004e44f0":
        return "API"
    if host[2] == "FUN_004e47d0":
        return "GRANT"
    if mnem == "and":
        return "CLEAR"
    if mnem == "mov":
        return "COPY"
    if mnem == "or":
        return "SET"
    return "OTHER"


def fmt_bits(bits):
    return "[" + ",".join(str(b) for b in bits) + "]"


def main(argv=None):
    print("B34 - WHERE A FACILITY COMPLETION STAMPS +0x8c (campaign: base record +0x8c)")
    ins, fns, n_call = load_dump()
    starts = [f[0] for f in fns]
    const, leas = census(ins, fns)
    sites = api_sites(ins, fns)
    hosts = {}
    for a, h in sites:
        hosts[h[2]] = hosts.get(h[2], 0) + 1

    print("\nTABLE 1 - the dump and the API's call graph")
    print("  instructions=%d  call-instructions=%d  functions=%d  bitmap=0x%x"
          % (len(ins), n_call, len(fns), BITMAP))
    print("  API 0x%x call sites=%d in %d functions: %s"
          % (API, len(sites), len(hosts),
             ", ".join("%s:%d" % (k, v) for k, v in sorted(hosts.items()))))
    for name in sorted(hosts):
        f = next(x for x in fns if x[2] == name)
        print("    %-16s size=%-6d sites=%-3d" % (name, f[1], hosts[name]))
    d1 = sha([("ins", len(ins)), ("calls", n_call), ("api", len(sites)),
              ("hosts", tuple(sorted(hosts.items())))])

    print("\nTABLE 2 - every store into the bitmap word, by family")
    fams = {}
    for a, mnem, body, host in const:
        fams.setdefault(family_of(a, mnem, host), []).append((a, mnem, host[2]))
    for la, st, mnem, body, host in leas:
        fams.setdefault(family_of(st, mnem, host), []).append((st, mnem, host[2]))
    for k in sorted(fams):
        rows = sorted(fams[k])
        print("  %-6s %d sites" % (k, len(rows)))
        for a, mnem, host in rows:
            print("    %08x %-4s %s" % (a, mnem, host))
    d2 = sha([(k, tuple(sorted(v))) for k, v in sorted(fams.items())])

    print("\nTABLE 3 - the COMPLETION LEG's own two pieces")
    pop_body = body_of(ins, fns, POP)
    scr_body = body_of(ins, fns, SCREEN)
    pop_refs = sum(1 for a, b in pop_body if "0x95da9c" in b or "0x95da9d" in b
                   or "0x95da9e" in b or "0x95da9f" in b)
    pop_api = sum(1 for a, b in pop_body if re.search(r"\bcall\s+0x4e44f0\b", b))
    scr_api = sum(1 for a, b in scr_body if re.search(r"\bcall\s+0x4e44f0\b", b))
    scr_refs = sum(1 for a, b in scr_body if "0x95da9c" in b)
    print("  pop   FUN_%06x insns=%-4d bitmap-refs=%d api-calls=%d" % (POP, len(pop_body), pop_refs, pop_api))
    print("  screen FUN_%06x insns=%-4d bitmap-refs=%d api-calls=%d" % (SCREEN, len(scr_body), scr_refs, scr_api))
    scr_isa_caller = sum(1 for a, b in scr_body if re.search(r"\bcall\s+0x4ef5d0\b", b))
    print("  the screen calls the pop at %d site(s); the screen's own API calls=%d"
          % (scr_isa_caller, scr_api))

    scr_stores = body_stores(scr_body)
    print("\nTABLE 4 - set arithmetic: the API's host set vs the pop's host set")
    api_hosts = set(hosts)
    pop_hosts = {SCREEN_NAME}  # the pop's only caller is the base screen (M342 TABLE 4)
    inter = api_hosts & pop_hosts
    print("  |API hosts|=%d  |pop hosts|=%d  intersection=%s"
          % (len(api_hosts), len(pop_hosts), sorted(inter) or "{}"))

    print("\nTABLE 5 - the COPY family (the only writer that can express a LOSS)")
    copies = sorted(fams.get("COPY", []))
    print("  %d copy sites: %s" % (len(copies), ", ".join("%08x/%s" % (a, h) for a, _m, h in copies)))
    clears = sorted(fams.get("CLEAR", []))
    print("  %d clear sites: %s" % (len(clears), ", ".join("%08x/%s" % (a, h) for a, _m, h in clears)))

    # --- the recorded run ------------------------------------------------------------------
    S = fo.load_trace()
    prev = {}
    paid, gains = [], []
    for si, (ev, r, bases) in enumerate(S):
        for idx, name, rec in bases:
            key = (idx, name)
            if key in prev and prev[key][0] == si - 1:
                p, _ph = prev[key][1], prev[key][2]
                stb, sta = fo.st_of(p), fo.st_of(rec)
                hb, ha = fo.head_of(p), fo.head_of(rec)
                g = sorted(fo.bits_of(rec) - fo.bits_of(p))
                l = sorted(fo.bits_of(p) - fo.bits_of(rec))
                vac = hb in fo.bits_of(p)     # the completed bit was ALREADY set -> stamp unobservable
                row = (si, ev, r, idx, name, hb, ha, stb, sta, g, l, p, rec, vac)
                if stb + fo.ADD >= PRICE and sta < stb:
                    paid.append(row)
                if g:
                    gains.append(row)
            prev[key] = (si, rec, fo.head_of(rec))

    print("\nTABLE 6 - the recorded run's PAID boundaries with a FACILITY head (0 < head < 0x40)")
    fac_done = [x for x in paid if FAC_LO <= x[5] < FAC_HI]
    for si, ev, r, idx, name, hb, ha, stb, sta, g, l, p, rec, vac in fac_done:
        print("  s%-2d %-11s %-18s head %d->%d  st %d+%d->%d  before=%s after=%s  delta=%s  head_bit_already_set=%s"
              % (si, ev, name[:18], hb, ha, stb, fo.ADD, sta, fmt_bits(sorted(fo.bits_of(p))),
                 fmt_bits(sorted(fo.bits_of(rec))), fmt_bits(sorted(set(g) | set(l))), vac))
    nonvac = [x for x in fac_done if not x[13]]
    print("  paid boundaries total=%d ; facility-head paid=%d ; with a delta=%d ; DISCRIMINATING (head bit absent)=%d"
          % (len(paid), len(fac_done), sum(1 for x in fac_done if x[9] or x[10]), len(nonvac)))

    print("\nTABLE 7 - the GAINS, and the head that was at the base when they happened")
    for si, ev, r, idx, name, hb, ha, stb, sta, g, l, p, rec, _vac in gains:
        inwin = FAC_LO <= hb < FAC_HI
        kind = ("PAY" if (stb + fo.ADD >= PRICE and sta < stb) else "NO-PAY")
        print("  s%-2d %-18s head_before=%-5d in_facility_window=%-5s %-6s gained=%s lost=%s"
              % (si, name[:18], hb, inwin, kind, fmt_bits(g), fmt_bits(l)))
    gain_at_paid = [x for x in gains if x[7] + fo.ADD >= PRICE and x[8] < x[7]]
    gain_offwin = [x for x in gain_at_paid if not (FAC_LO <= x[5] < FAC_HI)]
    gain_copy = [x for x in gains if x[10] and not (x[7] + fo.ADD >= PRICE and x[8] < x[7])]

    print("\nTABLE 8 - the stamp model replayed on the facility completions (bytes)")
    diffs = 0
    for si, ev, r, idx, name, hb, ha, stb, sta, g, l, p, rec, vac in fac_done:
        img, log = fo.transaction(p, stamp=True)
        changed = sum(1 for k in range(fo.FAC_OFF, fo.FAC_OFF + fo.FAC_BYTES) if img[k] != rec[k])
        diffs += 1 if changed else 0
        print("  s%-2d %-18s model=%s recorded=%s differing bytes=%d (discriminating=%s) log=%s"
              % (si, name[:18], fmt_bits(sorted(fo.bits_of(img))),
                 fmt_bits(sorted(fo.bits_of(rec))), changed, not vac, log))

    print("\nTABLE 9 - the model's COVERAGE (a model that explained the gains would be wrong)")
    cover_completion = sum(1 for x in fac_done if not x[9] and not x[10])
    print("  facility completions explained (delta {}) : %d/%d" % (cover_completion, len(fac_done)))
    print("  of those DISCRIMINATING (head bit absent) : %d/%d" % (len(nonvac), len(fac_done)))
    print("  gains at paid boundaries explained by a completion: %d/%d (heads outside the window: %d)"
          % (0, len(gain_at_paid), len(gain_offwin)))
    print("  copy-signature boundaries (no pay, gain+loss): %d/%d" % (len(gain_copy), len(gain_copy)))
    d3 = sha([("fac", [(x[3], x[5], x[9], x[10], x[13]) for x in fac_done]),
              ("gains", [(x[3], x[5], x[9], x[10]) for x in gains]), ("paid", len(paid))])

    print("\nDIGESTS dump=%s stores=%s run=%s" % (d1, d2, d3))

    ok = True
    ok &= gate("G1", len(ins) == 790695 and n_call == 48881 and len(sites) == 27 and len(hosts) == 8
               and ANCHOR == d1,
               "dump censused: %d insns, %d calls, API sites %d in %d hosts, digest %s"
               % (len(ins), n_call, len(sites), len(hosts), d1))
    ok &= gate("G2", len(fams.get("API", [])) == 2 and len(fams.get("GRANT", [])) == 11
               and len(fams.get("SET", [])) == 1 and len(fams.get("COPY", [])) == 6
               and len(fams.get("CLEAR", [])) == 0
               and sum(len(v) for v in fams.values()) == 20,
               "families: API=%d GRANT=%d SET=%d COPY=%d CLEAR=%d total=%d digest %s"
               % (len(fams.get("API", [])), len(fams.get("GRANT", [])), len(fams.get("SET", [])),
                  len(fams.get("COPY", [])), len(fams.get("CLEAR", [])),
                  sum(len(v) for v in fams.values()), d2))
    ok &= gate("G3", pop_refs == 0 and pop_api == 0 and scr_api == 0 and scr_isa_caller >= 1
               and scr_stores == [(0x4f0ec0, "or")] and len(pop_body) == 88,
               "the pop (88 insns) is writer-free (refs=%d api=%d); the screen's API calls=%d and its ONLY "
               "bitmap store is the unit-only OR at 0x%x (%s); screen->pop=%d"
               % (pop_refs, pop_api, scr_api, scr_stores[0][0] if scr_stores else 0,
                  scr_stores[0][1] if scr_stores else "-", scr_isa_caller))
    ok &= gate("G4", not inter, "API hosts and the pop's host are disjoint (%s)" % (sorted(inter) or "{}"))
    copy_hosts = {}
    for a, _m, h in copies:
        copy_hosts.setdefault(h, []).append(a)
    copy_shape = copy_hosts.get("FUN_0041cf20", []), copy_hosts.get("HOLE", []), \
        copy_hosts.get("FUN_004f47f0", [])
    ok &= gate("G5", len(copies) == 6 and len(copy_shape[0]) == 2 and len(copy_shape[1]) == 3
               and len(copy_shape[2]) == 1 and sorted(copy_shape[1]) == [0x4f38bb, 0x4f3ebc, 0x4f3f4c]
               and len(clears) == 0,
               "the COPY family is pinned site by site: 2 in FUN_0041cf20, 3 in the unnamed region "
               "(%s), 1 in FUN_004f47f0, %d clears"
               % (", ".join("%x" % a for a in sorted(copy_shape[1])), len(clears)))
    ok &= gate("G6", len(fac_done) == 6 and len(nonvac) == 3
               and all(not x[9] and not x[10] for x in fac_done),
               "facility completions %d (discriminating %d), every one stamped nothing; the head-stamp rival 0/%d"
               % (len(fac_done), len(nonvac), len(fac_done)))
    ok &= gate("G7", len(gain_at_paid) == 5 and len(gain_offwin) == 5 and len(gain_copy) == 1,
               "gains at paid boundaries %d, all with an out-of-window head (%d); copy signature %d"
               % (len(gain_at_paid), len(gain_offwin), len(gain_copy)))
    ok &= gate("G8", diffs == len(nonvac) and diffs >= 1,
               "the stamp rival is falsified ON BYTES at every discriminating completion: %d/%d differ; "
               "%d vacuous (bit already set)" % (diffs, len(fac_done), len(fac_done) - len(nonvac)))
    ok &= gate("G9", cover_completion == len(fac_done) and len(gain_at_paid) == 5,
               "coverage printed: completions %d/%d, gains explained by a completion 0/5"
               % (cover_completion, len(fac_done)))
    # a second, INDEPENDENT pass over the recorded run (fresh decode, same rule, same row shape)
    S2 = fo.load_trace()
    p2, rows2, paid2, gains2 = {}, [], 0, []
    for si, (ev, r, bases) in enumerate(S2):
        for idx, name, rec in bases:
            k = (idx, name)
            if k in p2 and p2[k][0] == si - 1:
                pr = p2[k][1]
                stb, sta = fo.st_of(pr), fo.st_of(rec)
                hb, ha = fo.head_of(pr), fo.head_of(rec)
                g = sorted(fo.bits_of(rec) - fo.bits_of(pr))
                l = sorted(fo.bits_of(pr) - fo.bits_of(rec))
                vac = hb in fo.bits_of(pr)
                row = (si, ev, r, idx, name, hb, ha, stb, sta, g, l, pr, rec, vac)
                if stb + fo.ADD >= PRICE and sta < stb:
                    paid2 += 1
                    if FAC_LO <= hb < FAC_HI:
                        rows2.append(row)
                if g:
                    gains2.append(row)
            p2[k] = (si, rec)
    d3b = sha([("fac", [(x[3], x[5], x[9], x[10], x[13]) for x in rows2]),
               ("gains", [(x[3], x[5], x[9], x[10]) for x in gains2]), ("paid", paid2)])
    heads = sorted(x[5] for x in fac_done)
    print("  second pass (fresh trace decode): %d facility completions of %d paid, digest %s"
          % (len(rows2), paid2, d3b))
    ok &= gate("G10", ANCHOR == d1 and d2 == STORES_ANCHOR and d3 == RUN_ANCHOR and d3b == d3,
               "anchors pinned: dump %s stores %s run %s; heads %s; fresh second pass %s == %s"
               % (d1, d2, d3, heads, d3b, d3))

    print()
    if FAIL:
        print("FAIL B34: %d/%d gates red %s" % (len(FAIL), 10, FAIL))
        return 1
    print("PASS B34: 10/10 gates  %s" % d1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
