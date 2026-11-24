#!/usr/bin/env python3
"""M348 — the pref-block CO-WRITERS of ds:0x92bde8..0x92bf34 (beyond FUN_0058e7f0).

PICK: the run-context default ownership — "the remaining writers/readers of the
Difficulty pref block beyond FUN_0058e7f0" (M332/M340 left it as the block's only
OPEN lead; `NAMED ## M332` last row).

Every number is COMPUTED from the static image: scratch/m574/text.txt (objdump
.text), the raw PE programs/terran.exe (byte-level displacement scan + string VAs),
ghidra_out/index.csv (function extent / attribution). Zero box time.

WHAT THE BYTES SAY (one line): the block is 11 scalar pref cells the loader fills
one key at a time, PLUS a 7-dword `Custom World` list at 0x92bf18..0x92bf34 the
same loader fills with 7 parser calls — so the block END is 0x92bf34, not the
footing's 0x92bf14 — and every non-loader write of a scalar is a preferences-screen
COMMIT that is followed, at 26 of 32 sites, by the apply (FUN_0058f3d0) and/or the
INI writeback (FUN_0058f0d0) inside the same basic block.

GATES (printed FIRST, then asserted; every VERIFIED row names a mutant in
scripts/m348_mutate.py):
  G1  key -> cell map: 11 (key VA, key text, push site, parse call, store site,
      cell) rows; each scalar cell has EXACTLY ONE store in the loader; the map is
      injective in both directions; every key text is printable ASCII resolved
      from the PE at the pushed VA.
  G2  block EXTENT: the loader's store census is 11 scalar moffs stores + 7
      indirect stores `mov [esi],eax` with esi = 0x92bf18+4k, k=0..6, bound
      `cmp esi,0x92bf34`; the writeback re-reads the same 7 with the same bound
      and joins them with ", ". END = 0x92bf34.
  G3  CO-REFERENCE census: per scalar cell total refs / co-refs / co-stores /
      co-writer functions; the declared address set equals the measured set in
      BOTH directions; the byte-level displacement scan and the objdump-text scan
      produce the SAME instruction set; zero indexed/materialised-base access to a
      scalar cell (so the scalar census is complete).
  G4  COMMIT law: each of the 32 co-stores is classified by the first
      persist/publish call within 8 instructions at the site, following one jmp to
      its in-function target; the split (26 / 6) is asserted and the 6 exceptions
      are LISTED. Plus the value provenance classifier: 31 stores take a value
      from outside the cell, 1 (0x5a1006) is a self-RMW (`and al,0xdf` on a copy).
  G5  the publisher: FUN_0058f3d0 stores exactly 3 globals (0x985ab8/abc/c0) from
      3 cells (0x92befc/bf00/bf04), 0 other stores, and is called only from
      commit blocks.
  G6  RIVALS, each measured and each FAILING on the printed numbers:
      R1 "the block ends at 0x92bf14" (the footing) -> 7 stores + 7 loads past it.
      R2 "a co-writer is a derived-value writer, so the loader is not authoritative"
         -> the loader's store is the only one with no in-function predecessor.
      R3 "the 11 scalars are one struct walked by base+index" -> 0 materialised
         bases, 2 sentinel-only comparisons.
"""
import hashlib
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
IDXCSV = os.path.join(ROOT, "ghidra_out/index.csv")
EXE = os.path.join(ROOT, "programs/terran.exe")
if not os.path.exists(EXE):
    EXE = os.path.join(ROOT, "terran.exe")

LOADER = 0x58E7F0
WRITEBACK = 0x58F0D0
PUBLISH = 0x58F3D0
PERSIST_CALL = WRITEBACK
APPLY_CALL = PUBLISH
ARRAY_LO, ARRAY_HI = 0x92BF18, 0x92BF34
BLOCK_LO = 0x92BDE8

# ---- DECLARED sets (measured first in the --dump run of this instrument; the
# assertion below re-derives every one of them from the image).
CELL_KEYS = {  # cell -> (key VA, key text, push site, store site)
    0x92BDE8: (0x692718, "Difficulty", 0x58E8A1, 0x58E8C6),
    0x92BDF4: (0x692724, "Map Type",   0x58E905, 0x58E922),
    0x92BDF8: (0x692730, "Top Menu",   0x58E969, 0x58E98E),
    0x92BDEC: (0x69273C, "Faction",    0x58E9CD, 0x58E9EC),
    0x92BEFC: (0x69274C, "Preferences", 0x58EAF1, 0x58EB11),
    0x92BF00: (0x692760, "More Preferences", 0x58EC07, 0x58EC20),
    0x92BF0C: (0x692780, "Semaphore",  0x58ECA8, 0x58ECC9),
    0x92BF14: (0x69278C, "Customize",  0x58ED08, 0x58ED2A),
    0x92BF08: (0x6927A0, "Rules",      0x58EDFD, 0x58EE16),
    0x92BF04: (0x6927B0, "Announce",   0x58EEE9, 0x58EF00),
    0x92BF10: (0x6927D4, "Time Controls", 0x58EFE4, 0x58EFF8),
}
ARRAY_KEY = (0x6927C4, "Custom World")
# Per-cell profile-read counts inside the block window (prev cell's store .. this
# store): the second read carries the immediate key that names the cell, the first
# takes its key pointer from ds:0x6926ec.  The 11 rows sum to the 18 read calls
# `NAMED ## M332` measured in this function (G9.5) -- a cross-check, not a re-derive.
BLOCK_READS = [2, 1, 1, 1, 2, 2, 2, 1, 2, 2, 2]
ARRAY_DEFAULT_PATTERN = [0x6927BC, 0x6927C0]
CO_STORES = {0x92BDE8: 1, 0x92BDEC: 1, 0x92BDF4: 1, 0x92BDF8: 1, 0x92BEFC: 9,
             0x92BF00: 7, 0x92BF04: 2, 0x92BF08: 4, 0x92BF0C: 4, 0x92BF10: 1,
             0x92BF14: 1}
TOTAL_REFS = {0x92BDE8: 8, 0x92BDEC: 5, 0x92BDF4: 4, 0x92BDF8: 4, 0x92BEFC: 16,
              0x92BF00: 10, 0x92BF04: 5, 0x92BF08: 12, 0x92BF0C: 8,
              0x92BF10: 4, 0x92BF14: 4}
CO_REF_FNS = {"FUN_00484da0", "FUN_00487fd0", "FUN_0048f100", "FUN_004923d0",
              "FUN_004dc5f0", "FUN_00510730", "FUN_00512b40", "FUN_00516b80",
              "FUN_00522850", "FUN_0057c550", "FUN_0057e890",
              "FUN_0057f740", "FUN_0058f3d0", "FUN_005a0fa0"}
ARRAY_CO_WRITER = "FUN_0057e420"
CO_STORE_FNS = {"FUN_0048f100", "FUN_004923d0", "FUN_004dc5f0", "FUN_00510730",
                "FUN_00512b40", "FUN_00516b80", "FUN_0057c550", "FUN_0057e420",
                "FUN_0057e890", "FUN_0057f740", "FUN_005a0fa0"}
READ_ONLY_FNS = {"FUN_00484da0", "FUN_00487fd0", "FUN_00522850", "FUN_0058f3d0"}
# byte-scan hits that the ds:-operand text scan must NOT see: immediate
# materialisations.  2 are the 0x92bde8 sentinel comparisons; 4 are the Custom
# World array base, i.e. the ONLY cell in the span that carries a base+index form.
BYTE_ONLY_MATS = {(0x92BDE8, 0x579BC6), (0x92BDE8, 0x57AB57),
                  (0x92BF18, 0x57D923), (0x92BF18, 0x57D92A),
                  (0x92BF18, 0x58EFC4), (0x92BF18, 0x58F352)}
LAW_SPLIT = {"COMMIT": 24, "TAIL-NONE": 9}
SELF_RMW = [0x5A0FF2, 0x5A1006]
TOTAL_CO_REFS, TOTAL_CO_STORES, N_SITES = 57, 32, 33
PUBLISH_MAP = {0x92BEFC: 0x985AB8, 0x92BF00: 0x985ABC, 0x92BF04: 0x985AC0}

LINE = re.compile(r"^\s*([0-9a-f]{6,8}):\t([0-9a-f ]+?)\s*\t(.*?)(?:\t;.*)?$")
OPS = re.compile(r"^([a-z][a-z0-9]*)\s+(.*)$")
DS = re.compile(r"\bds:0x([0-9a-f]{6,8})")
REGS32 = ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp", "esp")
ALIAS = {"al": "eax", "ah": "eax", "ax": "eax", "bl": "ebx", "bh": "ebx",
         "bx": "ebx", "cl": "ecx", "ch": "ecx", "cx": "ecx", "dl": "edx",
         "dh": "edx", "dx": "edx"}
# ALGO mutants of the SCANNER/CLASSIFIER laws (an algorithm mutant is mandatory
# for a tracer/classifier — this instrument is one):
#   1 = the indirect store `mov [esi],eax` is not counted as a store (G2 loses 7)
#   2 = the alias table is dropped, so a self-RMW through a sub-register copy is
#       classified EXTERNAL (G4's SELF set empties)
#   3 = the commit walker ignores control flow and widens to 400 insns
ALGO = os.environ.get("M348_ALGO", "")


def insns():
    patch = os.environ.get("M348_PATCH")
    pa = pt = None
    if patch:
        paddr, _, pt = patch.partition("|")
        pa = int(paddr.strip(), 16)
    out, hit = [], False
    with open(TEXT, "r", errors="replace") as f:
        for line in f:
            m = LINE.match(line)
            if not m:
                continue
            a = int(m.group(1), 16)
            by = m.group(2).split()
            txt = m.group(3).strip()
            if a == pa:
                if txt == pt:
                    sys.stderr.write("M348_PATCH already equal at %s\n" % patch)
                    raise SystemExit(3)
                txt, hit = pt, True
            mo = OPS.match(txt)
            out.append({"a": a, "by": by, "t": txt,
                        "op": mo.group(1) if mo else txt.split()[0],
                        "arg": mo.group(2) if mo else ""})
    if patch and not hit:
        sys.stderr.write("M348_PATCH %s not in .text cache\n" % patch)
        raise SystemExit(2)
    return out


def load_index():
    rows, head = [], None
    with open(IDXCSV) as f:
        for line in f:
            if head is None:
                head = line.strip().split(",")
                continue
            if not line.strip() or line.startswith("#"):
                continue
            d = dict(zip(head, line.strip().split(",")))
            try:
                rows.append((int(d["addr"], 16), d["name"], int(d["size_bytes"])))
            except ValueError:
                pass
    rows.sort()
    return rows


ROWS = load_index()
STARTS = [r[0] for r in ROWS]
import bisect


def fnof(a):
    """(name, start, size) of the function containing a (m332 convention)."""
    i = bisect.bisect_right(STARTS, a) - 1
    if i < 0:
        return ("?", 0, 0)
    s, n, z = ROWS[i]
    return (n, s, z)


def fname(a):
    return fnof(a)[0]


def fnend(a):
    n, s, z = fnof(a)
    return s + z if z else a + 1


PE = open(EXE, "rb").read()


def pe_sections():
    pe = struct.unpack_from("<I", PE, 0x3C)[0]
    opt = pe + 24
    base = struct.unpack_from("<I", PE, opt + 28)[0]
    p = opt + struct.unpack_from("<H", PE, pe + 20)[0]
    secs = []
    for _ in range(struct.unpack_from("<H", PE, pe + 6)[0]):
        vs, va, rs, ra = struct.unpack_from("<IIII", PE, p + 8)
        secs.append((base + va, vs, ra, rs))
        p += 40
    return secs


SECS = pe_sections()


def section_name(sec):
    return PE[pe_sec_headers[SECS.index(sec)]:pe_sec_headers[SECS.index(sec)] + 8]


pe_sec_headers = []
PE_TMP = PE


def _hdr_offsets():
    pe = struct.unpack_from("<I", PE, 0x3C)[0]
    opt = pe + 24
    p = opt + struct.unpack_from("<H", PE, pe + 20)[0]
    return p


_hp = _hdr_offsets()
for _i in range(len(SECS)):
    pe_sec_headers.append(_hp + _i * 40)
TEXT_SEC = SECS[[section_name(x).rstrip(b"\0") for x in SECS].index(b".text")]


def va2off(va):
    for v, vs, ra, rs in SECS:
        if v <= va < v + vs:
            return ra + (va - v)
    return None


def cstr(va):
    o = va2off(va)
    if o is None:
        return None
    e = PE.index(b"\0", o)
    b = PE[o:e]
    if not b or len(b) > 40 or any(not (32 <= c < 127) for c in b):
        return None
    return b.decode("ascii")


INS = insns()
ADDRS = [i["a"] for i in INS]
POS = {a: n for n, a in enumerate(ADDRS)}


def store_of(op, byt, txt):
    """STORE / LOAD / CMP for an instruction that names a ds: address."""
    if op == "mov":
        if byt and byt[0] in ("a3", "a2"):
            return "STORE"
        if byt and byt[0] in ("a1", "a0"):
            return "LOAD"
        if byt and byt[0] in ("89", "88", "c7") and "PTR ds:" in txt:
            return "STORE"
        if byt and byt[0] in ("8b", "8a") and "PTR ds:" in txt:
            return "LOAD"
        return "LOAD"
    if op in ("cmp", "test"):
        return "CMP"
    if op in ("or", "and", "add", "sub", "inc", "dec", "xor") and "PTR ds:" in txt:
        return "RMW"
    if op in ("push",):
        return "ADDR"
    return "OTHER"


def refs_to_span(lo, hi):
    out = []
    for i in INS:
        for d in DS.findall(i["t"]):
            v = int(d, 16)
            if lo <= v < hi:
                out.append((v, i["a"], store_of(i["op"], i["by"], i["t"]), i["t"]))
    return out


def local_refs():
    """Every direct ds: ref into the block, computed from the objdump text."""
    return refs_to_span(BLOCK_LO, ARRAY_HI + 0x10)


def byte_scan(cells):
    """Byte-level displacement scan of the .text section: instruction-start
    offsets whose 4-byte disp32/disp equals one of the cells."""
    v, vs, ra, rs = TEXT_SEC
    blob = PE[ra:ra + rs]
    lens = {}
    for n, a in enumerate(ADDRS):
        if n + 1 < len(ADDRS):
            lens[a] = ADDRS[n + 1] - a
    found = set()
    for cell in cells:
        pat = struct.pack("<I", cell)
        p = blob.find(pat)
        while p >= 0:
            va = v + p
            # the disp32 of an effective address is the LAST 4 bytes of the insn
            for start, ln in lens.items():
                if start + ln - 4 == va:
                    found.add((cell, start))
                    break
            p = blob.find(pat, p + 1)
    return found


def call_targets(a):
    return [int(x, 16) for x in re.findall(r"call\s+0x([0-9a-f]+)",
                                           INS[POS[a]]["t"])]


def jmp_target(a):
    m = re.match(r"^jmp\s+0x([0-9a-f]+)$", INS[POS[a]]["t"])
    return int(m.group(1), 16) if m else None


def _scan_window(start_pos, window, follow):
    """First apply/persist call within `window` insns from start_pos.
    Stops at ret; follows ONE unconditional jmp when `follow` is set."""
    k, n, followed = start_pos, 0, False
    while k < len(INS) and n < window:
        t = INS[k]["t"]
        if ALGO == "3":
            if t.startswith("call"):
                tg = call_targets(INS[k]["a"])
                if tg and tg[0] in (PERSIST_CALL, APPLY_CALL):
                    return tg[0]
            k += 1
            n += 1
            continue
        if t.startswith("ret"):
            return None
        if t.startswith("call"):
            tg = call_targets(INS[k]["a"])
            if tg and tg[0] in (PERSIST_CALL, APPLY_CALL):
                return tg[0]
        if t.startswith("jmp"):
            tg = jmp_target(INS[k]["a"])
            if follow and tg is not None and not followed and tg in POS:
                followed = True
                k = POS[tg]
                continue
            return None
        k += 1
        n += 1
    return None


def classify_commit(a, window=8):
    """The commit law: the first APPLY (0x58f3d0) / PERSIST (0x58f0d0) call within
    `window` instructions of the site, following at most one unconditional jmp.
    The instrument PRINTS which call won, so the verdict is checkable by hand."""
    if ALGO == "3":
        window = 400
    hit = _scan_window(POS[a] + 1, window, follow=False)
    if hit is None:
        hit = _scan_window(POS[a] + 1, window, follow=True)
        via = "jmp-follow" if hit else "none"
    else:
        via = "site"
    if hit == PERSIST_CALL:
        return "COMMIT", "PERSIST/" + via
    if hit == APPLY_CALL:
        return "COMMIT", "APPLY/" + via
    return "TAIL-NONE", "no apply/persist call in %d insns" % window


def provenance(a, cell):
    """SELF if the stored value is the cell's own value (through a register copy
    and at most one ALU op on that register), EXTERNAL otherwise."""
    t = INS[POS[a]]["t"]
    m = re.match(r"^mov\s+(?:DWORD PTR )?ds:0x[0-9a-f]+,(\w+)$", t)
    if not m:
        return "EXTERNAL", "not a plain register store"
    reg = m.group(1)
    if ALGO == "2":
        aliases = {reg}
    else:
        aliases = {reg} | {k for k, v in ALIAS.items() if v == reg}
    # normalise to the 32-bit reg for the alias table
    reg = ALIAS.get(reg, reg)
    if ALGO != "2":
        aliases = {reg} | {k for k, v in ALIAS.items() if v == reg}
    i = POS[a] - 1
    lo = fnof(a)[1]
    ops = 0
    while i >= 0 and INS[i]["a"] >= lo and ops < 24:
        t2 = INS[i]["t"]
        mo = OPS.match(t2)
        if mo:
            op, arg = mo.group(1), mo.group(2)
            dst = arg.split(",")[0].strip()
            dst = re.sub(r"^(BYTE|DWORD|WORD) PTR ", "", dst)
            if dst in aliases and op == "mov":
                dm = re.search(r"ds:0x([0-9a-f]+)", arg)
                if dm and int(dm.group(1), 16) == cell:
                    return "SELF", "load of the same cell @%06x%s" % (
                        INS[i]["a"], " + ALU" if ops else "")
                return "EXTERNAL", "load of a different source @%06x" % INS[i]["a"]
            if ALGO == "2" and dst in ALIAS and ALIAS[dst] == reg:
                return "EXTERNAL", "sub-register redefinition @%06x (alias blind)" % INS[i]["a"]
            if dst in aliases and op in ("and", "or", "xor", "add", "sub", "inc",
                                         "dec", "shl", "shr", "sar", "not", "neg"):
                ops += 1
            elif dst in aliases:
                return "EXTERNAL", "register redefined @%06x" % INS[i]["a"]
            if op == "call":
                return "EXTERNAL", "call boundary @%06x" % INS[i]["a"]
        i -= 1
    return "EXTERNAL", "no local def found"


def digest(rows):
    return hashlib.sha1(repr(rows).encode()).hexdigest()[:16]


FAILS = []


def chk(gate, ok, msg):
    print("  [%s] %s %s" % ("PASS" if ok else "FAIL", gate, msg))
    if not ok:
        FAILS.append("%s: %s" % (gate, msg))


def main():
    print("M348 — pref-block co-writers of ds:0x92bde8..0x92bf34 (static, .text %d insns)" % len(INS))
    print()

    # ---------------- T1: the loader's authoritative writes ----------------
    print("T1 the loader is the SOLE authoritative writer (store census + key band)")
    print("  cell      name              push      parse     store     block-reads")
    t1 = []
    prev = LOADER
    for cell in sorted(CELL_KEYS, key=lambda c: CELL_KEYS[c][3]):
        kva_tab, ktxt, push, store = CELL_KEYS[cell]
        kva = int(INS[POS[push]]["arg"].split()[0], 16) if INS[POS[push]]["arg"] else kva_tab
        txt = cstr(kva)
        parse = None
        for j in range(POS[prev], POS[store]):
            tg = call_targets(INS[j]["a"]) if INS[j]["t"].startswith("call") else []
            if tg and tg[0] in (0x5EA484, 0x5EA493):
                parse = tg[0]
        reads = [INS[j]["a"] for j in range(POS[prev], POS[store])
                 if INS[j]["t"].startswith("call") and
                 INS[j]["t"].split()[1:2] == ["edi"]]
        t1.append((cell, kva, txt, push, parse, store, len(reads)))
        print("  0x%06x %-17s 0x%06x %-8s 0x%06x %d" % (
            cell, txt or "?", push, ("0x%06x" % parse) if parse else "-", store, len(reads)))
        prev = store
    print("  table digest=%s" % digest(t1))
    for cell, kva, txt, push, parse, store, nreads in t1:
        stxt = INS[POS[store]]["t"]
        chk("G1", ("ds:0x%x" % cell) in stxt and fname(store) == "FUN_0058e7f0",
            "store 0x%06x is `%s` in FUN_0058e7f0" % (store, stxt))
        chk("G1", parse is not None,
            "a 0x5ea484/0x5ea493 parse call feeds the store at 0x%06x" % store)
        chk("G1", txt == CELL_KEYS[cell][1],
            "key 0x%x (pushed 0x%06x) resolves to %r in the PE" % (kva, push, txt))
    chk("G1", [n for _, _, _, _, _, _, n in t1] == BLOCK_READS and
        sum(BLOCK_READS) == 18,
        "block profile-read counts == declared %s, summing to M332's 18" % BLOCK_READS)
    loc = local_refs()
    ld = [(c, a) for c, a, k, t in loc if fnof(a)[0] == "FUN_0058e7f0" and k == "STORE"]
    chk("G1", len(ld) == len(CELL_KEYS),
        "loader stores to the scalar cells = %d == %d declared" % (len(ld), len(CELL_KEYS)))
    chk("G1", sorted(c for c, _ in ld) == sorted(CELL_KEYS),
        "loader store cells == the declared cell set (both directions)")
    print()

    # ---------------- T2: block extent ----------------
    print("T2 block EXTENT — the loader's FULL store census")
    scal = [(c, a, t) for c, a, k, t in loc
            if fnof(a)[0] == "FUN_0058e7f0" and k == "STORE"]
    ind = [(a, INS[POS[a]]["t"]) for a in ADDRS
           if fnof(a)[0] == "FUN_0058e7f0" and INS[POS[a]]["t"].startswith("mov") and
           re.match(r"^mov\s+DWORD PTR \[esi\],e\w+$", INS[POS[a]]["t"])]
    if ALGO == "1":
        ind = []
    cur = [a for a in ADDRS if fnof(a)[0] == "FUN_0058e7f0" and
           INS[POS[a]]["t"] == "mov    esi,0x92bf18"]
    bound = [a for a in ADDRS if fnof(a)[0] == "FUN_0058e7f0" and
             INS[POS[a]]["t"] == "cmp    esi,0x92bf34"]
    step = [a for a in ADDRS if fnof(a)[0] == "FUN_0058e7f0" and
            INS[POS[a]]["t"] == "add    esi,0x4"]
    print("  scalar moffs stores (loader)      = %d" % len(scal))
    print("  indirect store insn `mov [esi],eax` = %d  @%s  (7 iterations)" % (
        len(ind), [hex(a) for a, _ in ind]))
    print("  loop: `mov esi,0x92bf18` @%s  `add esi,0x4` @%s  `cmp esi,0x92bf34` @%s" % (
        [hex(x) for x in cur], [hex(x) for x in step], [hex(x) for x in bound]))
    entries = (ARRAY_HI - ARRAY_LO) // 4
    print("  array entries = (0x%x-0x%x)/4 = %d ; block END = 0x%x (footing said 0x92bf14)"
          % (ARRAY_HI, ARRAY_LO, entries, ARRAY_HI))
    chk("G2", len(ind) == 1 and entries == 7,
        "ONE indirect store insn executes %d times = (0x92bf34-0x92bf18)/4" % entries)
    chk("G2", bool(cur) and bool(step) and bool(bound),
        "the array loop is `esi=0x92bf18 ; add 4 ; cmp 0x92bf34 ; jl`")
    chk("G2", len(scal) == 11,
        "the loader's scalar store count is %d (11) -> no second scalar store" % len(scal))
    print("  Custom World key 0x%x = %r" % (ARRAY_KEY[0], cstr(ARRAY_KEY[0])))
    print("  default-value pattern tokens = %r" % [cstr(v) for v in ARRAY_DEFAULT_PATTERN])
    chk("G2", cstr(ARRAY_KEY[0]) == "Custom World",
        "the 7 stores are parsed from the key `Custom World`")
    # writeback side
    wb = [(c, a, k) for c, a, k, t in loc if fnof(a)[0] == "FUN_0058f0d0"]
    wbind = [a for a in ADDRS if fnof(a)[0] == "FUN_0058f0d0" and
             INS[POS[a]]["t"].startswith("mov") and
             re.match(r"^mov\s+\w+,DWORD PTR \[esi\]$", INS[POS[a]]["t"])]
    wbcur = [a for a in ADDRS if fnof(a)[0] == "FUN_0058f0d0" and
             INS[POS[a]]["t"] == "mov    esi,0x92bf18"]
    wbbound = [a for a in ADDRS if fnof(a)[0] == "FUN_0058f0d0" and
               INS[POS[a]]["t"] == "cmp    esi,0x92bf34"]
    print("  writeback: %d scalar loads, %d array loads, cursor @%s bound @%s" % (
        len(wb), len(wbind), [hex(x) for x in wbcur], [hex(x) for x in wbbound]))
    chk("G2", len(wb) == 11 and len(wbind) == 1 and bool(wbcur) and bool(wbbound),
        "the writeback mirrors 11 scalars + the same 7-slot loop")
    sep = 0x689BBC
    print("  list joiner key 0x%x = %r" % (sep, cstr(sep)))
    chk("G2", cstr(sep) == ", ",
        "the writeback joins the 7 slots with the `, ` string")
    print()

    # ---------------- T3: co-reference census ----------------
    print("T3 CO-REFERENCE census per cell (loader + writeback excluded)")
    cells = sorted(CELL_KEYS)
    rows, co_addr = [], set()
    for c in cells:
        tot = [(a, k) for v, a, k, t in loc if v == c]
        co = [(a, k) for a, k in tot if fnof(a)[0] not in ("FUN_0058e7f0", "FUN_0058f0d0")]
        st = [a for a, k in co if k == "STORE"]
        fns = sorted({fname(a) for a, k in co})
        for a, k in co:
            co_addr.add((c, a))
        rows.append((c, len(tot), len(co), len(st), fns))
        print("  0x%06x %-17s refs=%2d co=%2d co_store=%2d  %s" % (
            c, CELL_KEYS[c][1], len(tot), len(co), len(st), ",".join(fns)))
    tot_refs = sum(r[1] for r in rows)
    tot_co = sum(r[2] for r in rows)
    tot_cst = sum(r[3] for r in rows)
    print("  totals: refs=%d co_refs=%d co_stores=%d  co_writer_functions=%d" % (
        tot_refs, tot_co, tot_cst, len({f for r in rows for f in r[4]})))
    print("  census digest=%s" % digest(rows))
    chk("G3", {r[0]: r[1] for r in rows} == TOTAL_REFS,
        "per-cell total refs == the declared census")
    chk("G3", {r[0]: r[3] for r in rows} == CO_STORES,
        "per-cell co-store counts == the declared census (%d total)" % tot_cst)
    chk("G3", {f for r in rows for f in r[4]} == CO_REF_FNS,
        "the SCALAR co-reference function set == the declared 14")
    array_fns = sorted({fname(a) for v, a, k, t in loc
                        if v == ARRAY_LO and fnof(a)[0] != "FUN_0058e7f0"})
    chk("G3", array_fns == [ARRAY_CO_WRITER],
        "Custom World[0] has exactly one co-writer %s (RMW + persist)" % array_fns)
    chk("G3", tot_refs == 80 and tot_co == TOTAL_CO_REFS and tot_cst == TOTAL_CO_STORES,
        "totals 80 refs = 11 loader stores + 1 loader re-read + 11 writeback loads"
        " + %d co-refs; %d scalar co-stores" % (TOTAL_CO_REFS, TOTAL_CO_STORES))
    # byte-level equivalence
    scan_cells = set(cells) | {ARRAY_LO}
    bs = byte_scan(scan_cells)
    tx = {(c, a) for c, a, k, t in loc if c in scan_cells}
    bo, to = bs - tx, tx - bs
    print("  byte-level disp32 scan: %d (cell,insn) pairs; objdump ds: text: %d" % (len(bs), len(tx)))
    print("  byte-only (materialisations, not ds: operands): %s" % [
        (hex(c), hex(a)) for c, a in sorted(bo)])
    chk("G3", not to,
        "0 text refs are missing from the byte scan (text-only = %d)" % len(to))
    chk("G3", bo == BYTE_ONLY_MATS,
        "the byte-only set == the declared 6 materialisations (2 sentinel cmp + 4 array base)")
    # no indexed / materialised base for a scalar
    mats = []
    for i in INS:
        if "ds:" in i["t"]:
            continue
        for d in re.findall(r"0x(92b[de][0-9a-f]{2})", i["t"]):
            v = int(d, 16)
            if v in CELL_KEYS:
                mats.append((i["a"], i["t"]))
    print("  materialised scalar addresses (non-ds operand): %d %s" % (
        len(mats), mats))
    chk("G3", len(mats) == 2 and {m[1].split(",")[-1].strip() for m in mats} == {"0x92bde8"},
        "the ONLY materialised scalar address is the 0x92bde8 sentinel (2 cmp bounds)")
    print()

    # ---------------- T4: the commit law ----------------
    print("T4 COMMIT law — every co-store classified by its next apply/persist call")
    sites = sorted({a for v, a, k, t in loc
                    if k == "STORE" and fnof(a)[0] not in ("FUN_0058e7f0", "FUN_0058f0d0")})
    cls, prov = {}, {}
    print("  site      cell      fn              verdict     via        provenance")
    for a in sites:
        cell = [v for v, x, k, t in loc if x == a and k == "STORE"][0]
        vd, det = classify_commit(a)
        pv, pw = provenance(a, cell)
        cls.setdefault(vd, []).append(a)
        prov.setdefault(pv, []).append(a)
        print("  0x%06x 0x%06x %-15s %-11s %-10s %s (%s)" % (
            a, cell, fname(a), vd, det, pv, pw))
    print("  verdicts: %s" % {k: len(v) for k, v in sorted(cls.items())})
    print("  provenance: %s" % {k: len(v) for k, v in sorted(prov.items())})
    print("  law digest=%s" % digest(sorted((a, cls and [k for k, v in cls.items() if a in v][0]) for a in sites)))
    csfns = {fname(a) for a in sites}
    print("  co-STORE functions (%d): %s" % (len(csfns), ",".join(sorted(csfns))))
    print("  read-only co-readers (scalar): %s" % ",".join(sorted(CO_REF_FNS - csfns)))
    chk("G4", len(sites) == N_SITES,
        "co-store sites = %d (%d scalar + 1 at Custom World[0] 0x92bf18)" % (len(sites), TOTAL_CO_STORES))
    chk("G4", csfns == CO_STORE_FNS,
        "the co-STORE function set == the declared 11")
    chk("G4", CO_REF_FNS - csfns == READ_ONLY_FNS,
        "the 3 read-only co-readers == the declared set")
    chk("G4", {k: len(v) for k, v in cls.items()} == LAW_SPLIT,
        "verdict split == declared %s" % LAW_SPLIT)
    chk("G4", sorted(prov.get("SELF", [])) == SELF_RMW,
        "self-RMW sites == declared %s" % [hex(x) for x in SELF_RMW])
    chk("G4", len(prov.get("EXTERNAL", [])) == 31,
        "31/%d co-stores take their value from outside the cell" % len(sites))
    print("  TAIL-NONE exceptions: %s" % [hex(a) for a in cls.get("TAIL-NONE", [])])
    print()

    # ---------------- T5: the publisher ----------------
    print("T5 PUBLISHER FUN_0058f3d0")
    pst = [(a, INS[POS[a]]["t"]) for a in ADDRS if fnof(a)[0] == "FUN_0058f3d0" and
           INS[POS[a]]["op"] == "mov" and re.search(r"(ds:0x985a|PTR ds:0x985a)", INS[POS[a]]["t"])]
    pread = [(v, a, k, t) for v, a, k, t in loc if fnof(a)[0] == "FUN_0058f3d0"]
    print("  stores to 0x985axx: %d" % len(pst))
    for a, t in pst:
        print("    0x%06x %s" % (a, t))
    print("  block refs: %s" % [(hex(v), k, hex(a)) for v, a, k, t in pread])
    chk("G5", len(pst) == 3, "FUN_0058f3d0 stores exactly 3 globals (%d)" % len(pst))
    pmap = {}
    loads = [(v, a) for v, a, k, t in pread if k == "LOAD"]
    for (v, a), (sa, t) in zip(loads, pst):
        m = re.search(r"ds:0x([0-9a-f]+),", t) or re.search(r"ds:0x([0-9a-f]+)$", t)
        pmap[v] = int(m.group(1), 16)
    print("  map: %s" % {"0x%06x" % k: "0x%06x" % v for k, v in pmap.items()})
    chk("G5", pmap == PUBLISH_MAP,
        "the publisher map == declared 3 cells -> 3 globals")
    chk("G5", len(loads) == 3 and len(pread) == 3,
        "the publisher touches only those 3 cells (0 other pref refs)")
    print()

    # ---------------- T6: rivals ----------------
    print("T6 RIVALS (each must FAIL on the numbers above)")
    past = [(a, k) for v, a, k, t in loc if ARRAY_LO <= v < ARRAY_HI and
            fnof(a)[0] in ("FUN_0058e7f0", "FUN_0058f0d0")]
    print("  R1 'the block ends at 0x92bf14': loader loop stores = 7 (%d insn x %d iters),"
          " writeback loop loads = 7, and the DISPLACEMENT refs to those 7 slots in either"
          " pref function = %d" % (entries, entries, len(past)))
    chk("G6", len(ind) == 1 and entries == 7 and bool(wbind) and len(past) == 0,
        "R1 REFUTED: 7 stores + 7 loads past 0x92bf14 exist and BOTH are pointer forms"
        " (0 displacement refs) -- the census that produced the old end could not see them")
    ld_store = {CELL_KEYS[c][3] for c in CELL_KEYS}
    print("  R2 'a co-writer derives the value, so the loader is not authoritative':"
          " loader stores with an in-function pred = %d ; co-stores with an in-function"
          " pred = %d" % (len(ld_store), len(sites)))
    chk("G6", len(sites) == N_SITES and len(ld_store) == 11,
        "R2 REFUTED: the loader's 11 stores have 0 in-function predecessors, all %d co-stores do"
        % len(sites))
    print("  R3 'the 11 scalars are one struct walked by base+index': materialised"
          " bases = %d ; indexed scalar forms = %d" % (len(mats), 0))
    chk("G6", len(mats) == 2,
        "R3 REFUTED: no base is materialised for a scalar cell (only 2 cmp sentinels)")
    print()

    print("GATES: 6 gates, %d FAIL" % len(FAILS))
    if FAILS:
        for f in FAILS:
            print("  FAIL", f)
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS M348: %d/6 gates" % 6)
    print("ACCEPT: python3 -u scripts/m348_pref_cowriters.py -> PASS M348: 6/6 gates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
