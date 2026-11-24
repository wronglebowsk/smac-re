#!/usr/bin/env python3
"""M371 - the four war-initiation hosts and the 0x8 bit they write:
COMMLINK (contact, M369) or a war companion?  One bit or two?

Hosts under test (run context): FUN_00554350, FUN_005551e0, FUN_00554d10,
FUN_00507460, plus the 0x88000008 / 0x80000008 / 0x18 / 0x80000018 call masks
and the setter FUN_00551a20 (the one choke point every mask is stored through).

Acceptance:  python3 -u scripts/m371_war_contact.py
The tables print FIRST, then the gates assert them; every gate names a mutant in
scripts/m371_mutate.py.  `:N` in NAMED.md = a line of evidence/m371_war_contact.txt.
"""
import csv
import glob
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M371_TEXT") or os.path.join(ROOT, "scratch/m574/text.txt")
SHARDS = os.environ.get("M371_SHARDS") or os.path.join(ROOT, "ghidra_out/*.c")
LABELS = os.environ.get("M371_LABELS") or os.path.join(ROOT, "programs/labels.txt")
EXE = os.environ.get("M371_EXE") or os.path.join(ROOT, "programs/terran.exe")

A20 = 0x551A20                      # FUN_00551a20(f1, f2, mask): the symmetric setter
A20_END = 0x551C32
BUILDER = "FUN_004db480"            # the relations page builder: (id, label) rows
HOSTS = [(0x554350, "FUN_00554350"), (0x554D10, "FUN_00554d10"),
         (0x5551E0, "FUN_005551e0"), (0x507460, "FUN_00507460")]
WINDOW = 14                         # ALG mutant target: argument-push lookback
REQUIRE_SOLE = True                 # ALG mutant target: exactly one immediate push

# measured pins (scripts/m371_war_contact.py prints these before asserting)
HOST_WARISH = {(0x554389, 0x80000008, "FUN_00554350"),
               (0x554426, 0x88000008, "FUN_00554350"),
               (0x554E88, 0x18, "FUN_00554d10"),
               (0x55566E, 0x88000008, "FUN_005551e0"),
               (0x555BB9, 0x88000008, "FUN_005551e0"),
               (0x507653, 0x80000018, "FUN_00507460")}
CENSUS_PIN = {0x1: 4, 0x2: 1, 0x4: 1, 0x8: 4, 0x10: 14, 0x18: 1, 0x43: 1,
              0x50: 1, 0x58: 1, 0x2000: 7, 0x8010: 1, 0x10004: 1,
              0x400000: 1, 0x40000000: 2, 0x80000000: 1, 0x80000008: 1,
              0x80000018: 1, 0x88000008: 3}
CALLS_TOTAL, LITERAL, CARRIED = 70, 46, 24
PURE8 = {(0x42999D, "FUN_00429950"), (0x4DAE13, "FUN_004dadd0"),
         (0x56F5AD, "FUN_0056df40"), (0x5A7C0A, "FUN_005a7970")}
WAR_ALONE = {(0x507AC0, "FUN_005076d0"), (0x507C71, "FUN_005076d0"),
             (0x507D21, "FUN_00507ce0")}

out, gates = [], []


def say(s=""):
    out.append(s)


def gate(gid, ok, msg):
    gates.append((gid, bool(ok)))
    say("  %-5s %s  %s" % (gid, "PASS" if ok else "FAIL", msg))


ADDR = re.compile(r"\s*([0-9a-f]{6,8}):\s+((?:[0-9a-f]{2} )+)\s*\t(.*)$")
STOP = ("call", "ret", "jmp")


def load_text(path):
    ins = []
    for line in open(path, "r", errors="replace"):
        m = ADDR.match(line)
        if m:
            ins.append((int(m.group(1), 16), re.sub(r"\s+", " ", m.group(3)).strip()))
    return ins


def win(ins, lo, hi):
    return [(a, t) for a, t in ins if lo <= a <= hi]


def push_imm(t):
    m = re.match(r"push +(?:0x)?([0-9a-f]+)$", t)
    return int(m.group(1), 16) if m else None


def imm_of(t):
    """the immediate of `mnemonic reg,imm` (and/or/test), else None."""
    m = re.search(r",(0x[0-9a-f]+)$", t)
    return int(m.group(1), 16) if m else None


def call_tgt(t):
    m = re.match(r"call +(0x[0-9a-f]+)$", t)
    return int(m.group(1), 16) if m else None


def bits(m):
    return [i for i in range(32) if m >> i & 1]


def bstr(m):
    return "[" + ",".join("%d" % i for i in bits(m)) + "]"


def load_funcs():
    rows = []
    for r in csv.DictReader(open(os.path.join(ROOT, "ghidra_out/index.csv"))):
        if r["addr"].startswith("0x"):
            rows.append((int(r["addr"], 16), int(r["size_bytes"]), r["name"]))
    return rows


FUNCS = None


def fn_of(a):
    global FUNCS
    if FUNCS is None:
        FUNCS = load_funcs()
    best = None
    for ad, sz, n in FUNCS:
        if ad <= a < ad + sz and (best is None or ad > best[0]):
            best = (ad, n)
    return best[1] if best else "?"


def mask_at(ins, idx, a):
    """the mask is the sole immediate push in the argument run before `call 0x551a20`."""
    i = idx.get(a)
    if i is None:
        return None, []
    j, ps = i - 1, []
    while j >= 0 and i - j <= WINDOW:
        t = ins[j][1]
        if t.startswith(STOP):
            break
        if t.startswith("push"):
            ps.append(t)
        j -= 1
    imms = [p for p in ps if push_imm(p) is not None]
    if len(imms) == 1:
        return push_imm(imms[0]), ps
    if not REQUIRE_SOLE and imms:
        return push_imm(imms[0]), ps
    return None, ps


def load_builder_rows():
    body = []
    for path in sorted(glob.glob(SHARDS)):
        lines = open(path, "r", errors="replace").read().split("\n")
        for i, line in enumerate(lines):
            if line.startswith("// ==== %s " % BUILDER):
                body = lines[i:i + 600]
    rows, pend = [], None
    for line in body:
        m = re.search(r"uVar5 = (0x[0-9a-f]+|\d+);", line)
        if m:
            pend = int(m.group(1), 16)
        m = re.search(r"FUN_0061482f\(\*\(undefined4 \*\)\(DAT_00997b20 \+ (0x[0-9a-f]+)\)\)", line)
        if m and pend is not None:
            rows.append((pend, int(m.group(1), 16)))
            pend = None
    return rows


def cstring(va):
    if not os.path.exists(EXE):
        return "<no exe>"
    off = va - 0x400000
    with open(EXE, "rb") as f:
        f.seek(off)
        raw = f.read(80).split(b"\x00")[0]
    return raw.decode("latin-1", "replace")


def main():
    ins = load_text(TEXT)
    idx = {a: i for i, (a, t) in enumerate(ins)}
    L = [x.rstrip(b"\r") for x in open(LABELS, "rb").read().split(b"\n")]

    say("M371 - war-initiation hosts and the 0x8 bit: COMMLINK or war companion?")
    say("")

    # ---------------------------------------------------------------- G1 hosts
    say("G1  the four hosts: every setter call in the function's byte range, mask + bits")
    host_calls = []
    for lo, name in HOSTS:
        w = win(ins, lo, lo + dict((n, s) for a, s, n in load_funcs())[name] - 1)
        calls = [(a, t) for a, t in w if call_tgt(t) == A20]
        say("    %-14s 0x%06x  %d setter call(s)" % (name, lo, len(calls)))
        for a, t in calls:
            m, ps = mask_at(ins, idx, a)
            host_calls.append((a, m, name))
            say("      0x%06x mask=%-10s bits=%s" % (a, "CARRIED" if m is None else "0x%x" % m,
                                                     "-" if m is None else bstr(m)))
    warish = {(a, m, n) for a, m, n in host_calls if m is not None and (m & 0x18)}
    say("    warish (bit 8 or 0x10) host writes: %d" % len(warish))
    for a, m, n in sorted(warish):
        say("      0x%06x 0x%-9x %s" % (a, m, n))
    gate("G1a", warish == HOST_WARISH and len(host_calls) == 10,
         "10 host setter calls; the %d bit-8/war rows are exactly the pinned set" % len(HOST_WARISH))
    g1b = all((m & 8) and (m & 0x10 or m & 0x80000000) for _, m, _ in warish) and \
        all((m & 8) for _, m, _ in warish)
    gate("G1b", g1b, "every host war-ish mask carries bit 8; 0x18/0x80000018 carry war 0x10, "
                     "0x88000008/0x80000008 carry only bit31+8 (pending, no 0x10)")

    # ---------------------------------------------------------------- G2 setter
    say("")
    say("G2  the setter FUN_00551a20: where a war (0x10) request becomes a stored 0x18")
    w = win(ins, A20, A20_END)
    ors = [(a, t) for a, t in w if t.startswith("or ebx,")]
    ors8 = [(a, t) for a, t in w if t.startswith("or ebx,") and (imm_of(t) or 0) & 8]
    tests = [(a, t) for a, t in w if t.startswith("test bl,")]
    or_guard = [x for x in tests if x[0] < ors8[0][0]] if ors8 else []
    guard = or_guard[-1] if or_guard else (None, "")
    ands = [(a, t) for a, t in w if re.match(r"and e(dx|x),0x", t)]
    stores = [(a, t) for a, t in w if t.startswith("or edx,ebx")]
    say("    or ebx,imm: %s" % ", ".join("0x%06x %s" % (a, t) for a, t in ors))
    say("    guard before the bit-8 OR: 0x%06x %s" % (guard[0] or 0, guard[1] or "NONE"))
    say("    and-masks: %s" % ", ".join("0x%06x %s" % (a, t) for a, t in ands))
    say("    final symmetric ORs: %s" % ", ".join("0x%06x %s" % (a, t) for a, t in stores))
    gate("G2a", len(ors8) == 1 and ors8[0][0] == 0x551B11 and imm_of(ors8[0][1]) == 0x80000108
         and guard[1] == "test bl,0x10",
         "exactly one mask OR of bit 8: `or ebx,0x80000108` at 0x551b11, inside the `test bl,0x10` branch")
    gate("G2b", bits(0x80000108) == [3, 8, 31],
         "0x80000108 = bits %s: a war request also sets 0x100, bit 8 (contact) and bit 31" % bstr(0x80000108))
    keep = {}
    for a, t in ands:
        v = imm_of(t)
        keep.setdefault(v, []).append(a)
    say("    and-mask table:  mask        bit8  bit4(0x10)")
    for v in sorted(keep):
        say("      0x%08x   %-5s %-5s (%d site)" % (v, "KEPT" if v & 8 else "CLEAR",
                                                    "KEPT" if v & 0x10 else "CLEAR", len(keep[v])))
    gate("G2c", set(keep) == {0xffee7faf, 0xfaeef378, 0xff7fffff}
         and all(v & 8 for v in keep) and not (0xffee7faf & 0x10) and (0xfaeef378 & 0x10),
         "three clear masks, NONE clears bit 8; only the 0x7 (peace) mask 0xffee7faf clears 0x10: "
         "contact survives war -> peace")
    gate("G2d", stores == [(0x551BE6, "or edx,ebx"), (0x551C09, "or edx,ebx")]
         and (0x551BEA, "mov eax,esi") in w,
         "the war-augmented mask register (ebx) is stored in BOTH directions (0x551be6 / 0x551c09)")

    # ---------------------------------------------------------------- G3 census
    say("")
    say("G3  census of all %d `call 0x551a20` sites: literal masks, carried masks, bit classes" % CALLS_TOTAL)
    calls = [(a, t) for a, t in ins if call_tgt(t) == A20]
    census, carried = {}, []
    for a, _ in calls:
        m, ps = mask_at(ins, idx, a)
        if m is None:
            carried.append((a, fn_of(a), ps))
        else:
            census[m] = census.get(m, 0) + 1
    say("    literal masks (%d sites):" % len([1 for a, _ in calls if mask_at(ins, idx, a)[0] is not None]))
    for m in sorted(census):
        say("      0x%-10x %2d  bits=%s" % (m, census[m], bstr(m)))
    say("    carried (not linearly visible) %d sites, first 6: %s"
        % (len(carried), ", ".join("0x%06x %s" % (a, f) for a, f, _ in carried[:6])))
    gate("G3a", census == CENSUS_PIN and len(calls) == CALLS_TOTAL
         and sum(census.values()) == LITERAL and len(carried) == CARRIED,
         "%d calls = %d literal + %d carried; 18 distinct literal masks as pinned"
         % (len(calls), sum(census.values()), len(carried)))
    w_only = sorted(a for a, _ in calls if (mask_at(ins, idx, a)[0] or 0) & 0x10
                    and not (mask_at(ins, idx, a)[0] & 8))
    c_only = sorted(a for a, _ in calls if (mask_at(ins, idx, a)[0] or 0) & 8
                    and not (mask_at(ins, idx, a)[0] & 0x10))
    say("    war(0x10) WITHOUT bit 8: %d sites %s" % (len(w_only), " ".join("0x%06x" % a for a in w_only)))
    say("    bit 8 WITHOUT war(0x10): %d sites %s" % (len(c_only), " ".join("0x%06x" % a for a in c_only)))
    gate("G3b", len(w_only) == 16 and WAR_ALONE <= {(a, fn_of(a)) for a in w_only},
         "16 callers request war (14x0x10, 0x8010, 0x50) and NEVER name contact; "
         "both exits of the human declare path FUN_005076d0 are in the set")
    gate("G3c", len(c_only) == 8,
         "8 callers request bit 8 with no war bit (4 pure 0x8 + 3 0x88000008 + 1 0x80000008)")

    # ---------------------------------------------------------------- G4 independence
    say("")
    say("G4  contact is written and read on its own - the independence leg")
    p8 = {(a, fn_of(a)) for a, _ in calls if mask_at(ins, idx, a)[0] == 8}
    for a, f in sorted(p8):
        say("    mask == 0x8 exactly: 0x%06x  %s" % (a, f))
    gate("G4a", p8 == PURE8,
         "4 pure-contact writes: new game FUN_005a7970, council FUN_00429950, "
         "page commit FUN_004dadd0, goody pod FUN_0056df40")
    w55 = win(ins, 0x5551E0, 0x5560ED)
    r40018 = [a for a, t in w55 if t == "and eax,0x40018"]
    c8 = [a for a, t in w55 if t == "cmp eax,0x8"]
    r8018 = [a for a, t in w55 if t == "and edx,0x8018"]
    c8018 = [a for a, t in w55 if t == "cmp edx,0x8018"]
    r18 = [a for a, t in w55 if t == "and edx,0x18"]
    cdl8 = [a for a, t in w55 if t == "cmp dl,0x8"]
    say("    FUN_005551e0 read gates: and 0x40018 @%s -> cmp 0x8 @%s | and 0x8018 @%s -> cmp 0x8018 @%s"
        " | and 0x18 @%s -> cmp dl,0x8 @%s"
        % (["0x%06x" % x for x in r40018], ["0x%06x" % x for x in c8],
           ["0x%06x" % x for x in r8018], ["0x%06x" % x for x in c8018],
           ["0x%06x" % x for x in r18], ["0x%06x" % x for x in cdl8]))
    gate("G4b", r40018 == [0x555491] and 0x555496 in c8 and min(x for x in c8 if x > 0x555491) - 0x555491 < 8
         and r8018 == [0x5554DC] and c8018 == [0x5554E2] and r18 == [0x555502] and cdl8 == [0x555505],
         "the AI's war gate reads (rel & 0x40018) == 8 = contacted AND not at war; "
         "the third-faction test reads (& 0x18) == 8 = contacted, not at war: 8 is the contact predicate")
    atro_reads = [a for a, t in win(ins, 0x554D10, 0x55501D)
                  if re.match(r"test (al|eax|e[a-z]{2}),0x10$", t)
                  or re.search(r"test (DWORD PTR )?\[?[^,]*0x94d448[^,]*,0x10", t)]
    say("    FUN_00554d10 (atrocity) reads of 0x10 before its 0x18 write: %s"
        % ["0x%06x" % x for x in atro_reads])
    gate("G4c", bool(atro_reads) and all(x < 0x554E88 for x in atro_reads),
         "the atrocity host asks `at war already?` (bit 0x10) BEFORE writing 0x18 - the war bit is the "
         "state, bit 8 rides along as contact")

    # ---------------------------------------------------------------- G5 labels
    say("")
    say("G5  the page nouns (builder FUN_004db480 -> labels.txt line 11+elem)")
    rows = load_builder_rows()
    got = {}
    for bid, off in rows:
        ln = 11 + off // 4
        got[bid] = L[ln - 1].decode("latin-1") if ln - 1 < len(L) else "<eof>"
        say("    id 0x%-9x elem %d -> line %d = %r" % (bid, off // 4, ln, got.get(bid)))
    gate("G5a", len(rows) == 13 and got.get(0x8) == "Commlink" and got.get(0x10) == "Vendetta",
         "id 8 = 'Commlink', id 0x10 = 'Vendetta': two different nouns on the page")

    # ---------------------------------------------------------------- G6 roles
    say("")
    say("G6  host identities in game words (string-table resolution + caller edge)")
    roles = {}
    for lo, name in HOSTS:
        size = dict((n, s) for a, s, n in load_funcs())[name]
        ws = win(ins, lo, lo + size - 1)
        strs = []
        for a, t in ws:
            v = push_imm(t) if t.startswith("push") else imm_of(t)
            if v and 0x670000 <= v <= 0x6B0000:
                s = cstring(v)
                if s not in strs:
                    strs.append(s)
        roles[name] = strs
        say("    %-14s strings: %s" % (name, ", ".join(strs[:4]) if strs else "<none>"))
    edges = [(a, fn_of(a)) for a, t in ins if call_tgt(t) == 0x554350]
    say("    callers of FUN_00554350: %s" % ", ".join("0x%06x %s" % e for e in edges))
    gate("G6a", "MAJORATROCITY" in roles["FUN_00554d10"]
         and "AIDSTHEM" in roles["FUN_00507460"] and "AIDSUS" in roles["FUN_00507460"],
         "FUN_00554d10 is the atrocity consequence (MAJORATROCITY), FUN_00507460 the AI aid/join "
         "(AIDSTHEM/AIDSUS): both are war-declaration contexts")
    gate("G6b", (0x5558CF, "FUN_005551e0") in edges,
         "the AI turn pass FUN_005551e0 calls FUN_00554350 at 0x5558cf after the contact gate (G4b)")

    # ---------------------------------------------------------------- decision
    say("")
    say("DECISION TABLE - three independent tests of '0x8 is a war companion (one bit)'")
    say("    test                     companion predicts          measured")
    say("    pure-8 writes            none                        %d sites %s" %
        (len(p8), " ".join("0x%06x" % a for a, _ in sorted(p8))))
    say("    peace clear (test bl,0x7) clears bit 8               keeps bit 8 (0xffee7faf, G2c)")
    say("    page noun for id 8       a war word                  %r (G5a)" % got.get(0x8))
    gate("R1", len(p8) > 0 and all(v & 8 for v in keep) and got.get(0x8) == "Commlink",
         "RIVAL '8 = war companion / one bit' is DEAD on all three printed predictions")
    say("")
    say("R2  RIVAL '0x88000008 / 0x80000008 are war writes' - refuted by decomposition")
    say("    0x88000008 bits %s | 0x80000008 bits %s | war bit 0x10 present in neither"
        % (bstr(0x88000008), bstr(0x80000008)))
    gate("R2", not (0x88000008 & 0x10) and not (0x80000008 & 0x10) and (0x88000008 & 8)
         and (0x80000008 & 8),
         "the vendetta-pending masks set bit 31/27 + contact; they never set war 0x10")
    say("")
    say("R3  RIVAL 'war can be stored without contact' - refuted at the choke point")
    say("    any 0x10 request leaves FUN_00551a20 with 0x18 (or ebx,0x80000108 in the 0x10 branch,")
    say("    stored in both directions) - the 16 war-alone callers (G3b) all store contact too")
    gate("R3", bool(ors8) and (imm_of(ors8[0][1]) & 8) and not (imm_of(ors8[0][1]) & 0x10)
         and len(stores) == 2,
         "bit 8 in a war write is the setter's implication, not a second war meaning")

    say("")
    npass = sum(1 for _, ok in gates if ok)
    say("SUMMARY  %d/%d gates" % (npass, len(gates)))
    digest = hashlib.sha256(("\n".join(out)).encode()).hexdigest()[:16]
    say("DIGEST   %s" % digest)
    print("\n".join(out))
    if npass == len(gates):
        print("\nPASS M371: %d/%d gates digest %s" % (npass, len(gates), digest))
        return 0
    bad = [g for g, ok in gates if not ok]
    print("\nFAIL M371: %d/%d gates failed %s digest %s" % (len(bad), len(gates), bad, digest))
    return 1


if __name__ == "__main__":
    sys.exit(main())
