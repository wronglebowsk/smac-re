#!/usr/bin/env python3
# M327 (s304, pick (vii), STATIC, zero box): what a unit record's +10 "band" encodes,
# and why 25 of m54b_clean.SAV's 67 unit records are exempt from sim/save._unit_ok's
# coord test.
#
# ANSWER MEASURED HERE (table FIRST, then asserts):
#  * the save carries the game's OWN type-record array: 512 slots x 52 B at
#    count_off+4+count_len+3584, exactly 4,096 B before the unit array (M80's live
#    array DAT_0098ad88 = 8 FACTION BANDS x 64); 32 slots hold an ASCII name at +0
#    (band 0 = 0..13 the shared design list, bands 1-7 = 18 faction designs);
#  * in .text a unit record's +10 is read SIGN-EXTENDED and used as an INDEX into
#    that array: 0x4bdec4-0x4bded4 (imul idx*52; movsx ecx,[eax+0x933282]; imul
#    ecx*52; add ecx,0x98ad88) and inside unit_set_position 0x5ab3a2-0x5ab3b1
#    (movsx eax,[esi+0x933282]; x3 -> x13; mov al,[edx*4+0x98adac] = type+0x24);
#  * so the 25 "+10 band" records are UNITS OF A FACTION-BAND DESIGN: 25/25 have
#    owner byte (+14) == value//64 and 67/67 resolve to a NAMED type slot, while the
#    42 non-band records all point into band 0 (8 distinct owners);
#  * THEREFORE the premise shipped at sim/save.py:52 ("+10 >= 64: production-queue
#    band record, not a unit") is FALSE, and B25's "INFERRED that the .exe shares the
#    rule" is RETRACTED: the .exe has no coord rule there at all - the tile writer
#    stores +0/+2 on the unique entry path with no branch before them;
#  * the exemption's only empirical justification ("m113map.SAV has 3076/56832 in
#    one") is OUR OWN poke: m113map.SAV == m54b_clean.SAV except 20 dword markers
#    0xc0de0001..0xc0de0014 on a 128-B stride from 222000 (file-aligned, so a marker
#    can straddle a record boundary), 13 of them inside the unit array; the
#    out-of-grid records are unit 12 (marker 0xc0de000c at +1 -> x=3076, y=56832)
#    and unit 17 (the 0xc0de000e marker straddling unit 16+49..17+0 -> x=192).
# LIMITS (declared): linear scan windows (8/10 instrs) for the chain; text-dump
# mutants patch the DISASSEMBLY CACHE (scratch/m574/text.txt copy), never the exe;
# no claim about what the game validates when it LOADS a save (the loader is not in
# scope); type-record fields other than +0 (name) / +0x24 / +0x30 bit 2 unnamed.
# Rivals R1-R4 are computed and must come out False on the printed numbers.
# Mutants: M327_PATCH addr|mnem ops (text cache), M327_SAVE / M327_POKED =<file> (a
# temp copy of a save), M327_ALGO 1=chain window whole-file 2=band//32 3=poke window
# alignment 3 4=every branch counts as a store guard 5=every slot counts as named
# 6=variant B becomes the shipped rule 7=type +0x2d law declared true 8=owner from
# +15 9=type-array offset -4, M327_PIN overrides the G10 anchor.
# Harness PLANT sites (documented for review_lint L2b - the code mutants rewrite
# disassembly lines the instrument reads): MU1 0x4bded1 (the x52 fold after the
# pinned movsx at 0x4bdeca), MU2 0x5ab3a2 (unit_set_position's own +10 read), MU3
# 0x4bdeca (the read itself, moved to +4), MU4 0x5ab369 (the FIRST branch after the
# +0/+2 stores, retargeted into the store range), MU5 0x5ab355 (the +0 store, retyped
# to +4), MU21 0x5ab345 (an out-of-scope test -> the declared NO-OP: reddens
# NOTHING, which proves no gate is decoration on prose).
import bisect, csv, hashlib, os, re, struct, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M327_TEXT", os.path.join(ROOT, "scratch/m574/text.txt"))
IDX = os.path.join(ROOT, "ghidra_out/index.csv")
EV = os.environ.get("M327_EVIDENCE_ROOT", ROOT)
ALGO = os.environ.get("M327_ALGO", "0")
PRIMARY = os.environ.get("M327_SAVE", os.path.join(ROOT, "programs/saves/m54b_clean.SAV"))
POKED = os.environ.get("M327_POKED", os.path.join(ROOT, "programs/saves/m113map.SAV"))
SAVES = [PRIMARY, os.path.join(ROOT, "programs/saves/m112poke.SAV"),
         os.path.join(ROOT, "programs/saves/m112auto1.SAV"), POKED]
ANCHOR_READ = 0x4bdeca               # movsx of unit+10 in FUN_004bdce0 (Table T2)
MOVEX_SITE = 0x5ab3a2                # movsx of unit+10 inside unit_set_position
ENTRY, STORE_X, STORE_Y = 0x5ab320, 0x5ab355, 0x5ab35c
UNIT_LEN, TYPE_STRIDE, TYPE_SLOTS, BAND = 52, 52, 512, 64
M80_LIVE_BANDS = {0: list(range(0, 14)), 1: [64], 2: [128, 129, 130, 131],
                  3: [192, 193, 194], 4: [256], 5: [320, 321, 322, 323, 324, 325],
                  6: [384, 385, 386], 7: [448, 449]}
# G10 anchor: sha256-prefix of the MEASURED table rows (every T line). Re-measured at
# every acceptance run. MU1-MU4 / MU7-MU8 / MU10 / MU12-MU14 all move it; MU21 (a
# comments-only edit that changes no number) must NOT move it.
PIN = "ee77ddb39e8ec202"
N_CHAIN = 659            # measured chain sites in the .text cache (G2 pin)
N_READ = 774             # measured unit+10 word refs (G2 pin)

sys.path.insert(0, ROOT)
from sim import save as SV                                   # noqa: E402

INS = re.compile(r"^ +([0-9a-f]{6,8}):\t([0-9a-f ]+)\t(.*)$")


def load_funcs():
    fs = []
    for r in csv.DictReader(open(IDX)):
        try:
            fs.append((int(r["addr"], 16), int(r["addr"], 16) + int(r["size_bytes"]),
                       r["name"]))
        except ValueError:
            pass
    fs.sort()
    return fs


def fn_of(fs, a):
    starts = [f[0] for f in fs]
    i = bisect.bisect_right(starts, a) - 1
    return fs[i][2] if i >= 0 and fs[i][0] <= a < fs[i][1] else None


def load_text(fs):
    """one pass over the objdump cache -> list of (addr, mnem, ops) + index"""
    ins, addrs = [], []
    for line in open(TEXT, errors="replace"):
        m = INS.match(line)
        if not m:
            continue
        txt = m.group(3).strip()
        if not txt:
            continue
        mn = txt.split()[0]
        a = int(m.group(1), 16)
        addrs.append(a)
        ins.append((a, mn, txt))
    return ins, addrs


def patch_cache(ins, addrs):
    p = os.environ.get("M327_PATCH")
    if not p:
        return ins
    addr, want = p.split("|", 1)
    a = int(addr, 16)
    n = 0
    out = []
    for (ad, mn, txt) in ins:
        if ad == a:
            if txt.strip() == want.strip():
                raise SystemExit("M327_PATCH applied to nothing (already equal)")
            out.append((ad, want.split()[0], want))
            n += 1
        else:
            out.append((ad, mn, txt))
    if n == 0:
        raise SystemExit("M327_PATCH address not in .text cache: %s" % addr)
    return out


def chain_sites(ins, addrs):
    """unit+10 (0x933282 = DAT_00933278 + 10 in the u16 view) -> *52 -> 0x98ad88."""
    rd = re.compile(r"(?:movsx|movzx|mov)\s+([a-z]{2,3})\s*,\s*WORD PTR "
                    r"\[([a-z0-9*+ ]*\+0x933282)\]")
    hit = [i for i, (a, mn, t) in enumerate(ins) if "0x933282" in t and "WORD" in t]
    sites = []
    for i in hit:
        dst = rd.search(ins[i][2])
        if not dst:
            continue
        r0 = dst.group(1)
        lim = len(ins) if ALGO == "1" else min(len(ins), i + 12)
        mode, end = None, None
        for j in range(i + 1, lim):
            t = ins[j][2]
            if re.search(r"\bimul\s+%s,%s,0x34\b" % (r0, r0), t):
                for x in range(j + 1, min(len(ins), j + 9)):
                    if "0x98ad" in ins[x][2]:
                        mode, end = "imul52+" + ins[x][2].split()[0], x
                        break
            elif re.search(r"\blea\s+\w+,\[%s\+%s\*2\]" % (r0, r0), t):
                for x in range(j + 1, min(len(ins), j + 6)):
                    if "0x98ad" in ins[x][2]:
                        mode, end = "x13fold+" + ins[x][2].split()[0], x
                        break
            if mode:
                break
        if mode:
            base = re.search(r"0x98ad([0-9a-f]{2})", ins[end][2])
            sites.append((ins[i][0], mode, "0x98ad" + (base.group(1) if base else "??")))
    return sites, len(hit)


def band_of(t):
    """ALGO=2 mutant: derive the band with the WRONG stride (32 instead of 64)."""
    return t // (32 if ALGO == "2" else BAND)


def owner_of(u, d):
    """ALGO=8 mutant: read the owner from the neighbouring byte (+15)."""
    return d[u["off"] + (15 if ALGO == "8" else 14)]


def type_section(path):
    """locate + read the 512x52 type array and the unit records of one save"""
    s = SV.parse(path)
    d = s.data
    off = s.count_off + 4 + s.count_len + (3580 if ALGO == "9" else 3584)
    rows = []
    for t in range(TYPE_SLOTS):
        rec = d[off + TYPE_STRIDE * t: off + TYPE_STRIDE * t + TYPE_STRIDE]
        if ALGO == "5":                 # mutant: treat EVERY slot as named
            nm = "TRIVIAL"
        else:
            mm = re.match(rb"([ -~]{2,35})\x00", rec)
            nm = mm.group(1).decode("latin-1") if mm else None
        rows.append((t, nm, rec))
    units = []
    for i in range(s.n_units):
        o = s.units_off + UNIT_LEN * i
        units.append({"i": i, "off": o, "x": struct.unpack_from("<H", d, o)[0],
                      "y": struct.unpack_from("<H", d, o + 2)[0],
                      "t": struct.unpack_from("<H", d, o + 10)[0],
                      "own": d[o + 14], "raw": d[o:o + UNIT_LEN]})
    return s, off, rows, units


def found_units_variants(s, d):
    """A: as shipped (band exemption ON). B: coord-check EVERY record.
       C: type-sound: named type slot AND coord in grid AND owner<24."""
    def ok(o, mode):
        if o < 0 or o + UNIT_LEN > len(d):
            return False
        if d[o + 14] >= 24:
            return False
        t = struct.unpack_from("<H", d, o + 10)[0]
        if mode == "B" and ALGO == "6":            # mutant: B becomes the shipped rule
            if t < SV.UNIT_TYPE_BAND:
                x, y = struct.unpack_from("<HH", d, o)
                return x < s.width and y < s.height
            return True
        if mode == "B" or (mode == "C"):
            x, y = struct.unpack_from("<HH", d, o)
            inb = x < s.width and y < s.height
            if mode == "C":
                named = bool(re.match(rb"([ -~]{2,35})\x00",
                                      d[type_off_of(s) + 52 * t: type_off_of(s)
                                        + 52 * t + 36]))
                return inb and named and t < TYPE_SLOTS
            return inb
        if t < SV.UNIT_TYPE_BAND:
            x, y = struct.unpack_from("<HH", d, o)
            return x < s.width and y < s.height
        return True

    def scan(mode):
        n = 0
        while ok(s.bases_off - UNIT_LEN * (n + 1), mode):
            n += 1
        return n
    return scan("A"), scan("B"), scan("C")


def type_off_of(s):
    return s.count_off + 4 + s.count_len + 3584


def poke_runs(a, b, uoff):
    """the poke law: the two files differ ONLY inside 4-byte windows whose value in b
    is 0xc0de00NN, the windows are 128 B apart, and every changed byte is covered.
    Record attribution is PER CHANGED BYTE: the marker grid is file-aligned, so a
    dword can straddle a 52-B record boundary."""
    diff = [i for i in range(min(len(a), len(b))) if a[i] != b[i]]
    align = 3 if ALGO == "3" else 4
    wins = sorted({(i // align) * align for i in diff})
    wset = set(wins)
    out = []
    for w in wins:
        v = struct.unpack_from("<I", b, w)[0]
        o = struct.unpack_from("<I", a, w)[0]
        bytes_ = []
        for i in range(w, w + align):
            if a[i] != b[i] and uoff <= i < uoff + UNIT_LEN * 67:
                bytes_.append((i, (i - uoff) // UNIT_LEN, (i - uoff) % UNIT_LEN))
        out.append({"lo": w, "hi": w + align - 1, "val": v, "oval": o,
                    "covered": all((i // align) * align in wset for i in range(w, w + align)),
                    "ndiff": sum(1 for i in range(w, w + align) if a[i] != b[i]),
                    "inarr": bool(bytes_), "bytes": bytes_,
                    "recs": sorted({r for (_i, r, _f) in bytes_})})
    return len(diff), out


def main():
    fs = load_funcs()
    ins, addrs = load_text(fs)
    ins = patch_cache(ins, addrs)
    out = []
    W = out.append
    W("== M327: unit-record +10 = the TYPE INDEX into the save's own 8-band type array ==")

    # ---- T0 layout on four saves ----
    layout = {}
    for p in SAVES:
        s, off, rows, units = type_section(p)
        gap = s.units_off - (off + TYPE_STRIDE * TYPE_SLOTS)
        fa, fb, fc = found_units_variants(s, s.data)
        layout[p] = (s, off, gap, fa, fb, fc)
        W("T0 %s type_off=%d span=%d gap_to_units=%d closes=%s n_units=%d "
          "found A(exempt)=%d B(all-coord)=%d C(type-sound)=%d"
          % (os.path.basename(p), off, TYPE_STRIDE * TYPE_SLOTS, gap, s.closes,
             s.n_units, fa, fb, fc))
    prim, poff, pgap, pfa, pfb, pfc = layout[PRIMARY]
    dprim = prim.data
    prows, punits = type_section(PRIMARY)[2], type_section(PRIMARY)[3]

    # ---- T1 the named-slot census + the +0x30 bit-2 law ----
    named = [(t, n) for (t, n, r) in prows if n]
    bands = {}
    for (t, n) in named:
        bands.setdefault(t // BAND, []).append(t)
    W("T1 named-slots=%d/%d density=%.4f per-band=%s" %
      (len(named), TYPE_SLOTS, len(named) / float(TYPE_SLOTS),
       {b: sorted(v) for b, v in sorted(bands.items())}))
    bit2 = {}
    ff2c = {}
    for (t, n, r) in prows:
        if n:
            bit2.setdefault((r[0x30] >> 2) & 1, []).append(t)
            ff2c.setdefault(True if ALGO == "7" else (r[0x2d] == 0xFF), []).append(t)
    W("T1b type+0x30 bit2: set=%d clear=%d (band0 clear=%d band>0 set=%d) -> NOT a "
      "band marker; type BYTE +0x2d==0xff groups: true=%d false=%d band0-true=%d "
      "band>0-true=%d" %
      (len(bit2.get(1, [])), len(bit2.get(0, [])),
       len([t for t in bit2.get(0, []) if t < BAND]),
       len([t for t in bit2.get(1, []) if t >= BAND]),
       len(ff2c.get(True, [])), len(ff2c.get(False, [])),
       len([t for t in ff2c.get(True, []) if t < BAND]),
       len([t for t in ff2c.get(True, []) if t >= BAND])))
    W("T1c M80 live census diff: save-minus-live=%s live-minus-save=%s" %
      ({b: sorted(set(bands.get(b, [])) - set(M80_LIVE_BANDS[b])) for b in bands
        if set(bands.get(b, [])) - set(M80_LIVE_BANDS[b])},
       {b: sorted(set(M80_LIVE_BANDS[b]) - set(bands.get(b, []))) for b in M80_LIVE_BANDS
        if set(M80_LIVE_BANDS[b]) - set(bands.get(b, []))}))

    # ---- T2 the .exe chain ----
    sites, n_read = chain_sites(ins, addrs)
    W("T2 unit+10 word refs in .text=%d chain sites=%d funcs=%d" %
      (n_read, len(sites), len({fn_of(fs, a) for (a, m, b) in sites})))
    for (a, m, b) in sites:
        W("T2  0x%x %s -> %s owner=%s" % (a, m, b, fn_of(fs, a)))

    # ---- T2b the two pinned chains, as disassembled ----
    def win(a, back, fwd):
        i = [k for k, (ad, _m, _t) in enumerate(ins) if ad == a]
        return [t for (ad, m, t) in ins[max(0, i[0] - back):i[0] + fwd]] if i else []
    w1 = win(ANCHOR_READ, 3, 8)
    w2 = win(MOVEX_SITE, 1, 10)
    W("T2b 0x4bdec4 chain: %s" % " | ".join(w1))
    W("T2b 0x5ab3a2 chain: %s" % " | ".join(w2))
    a1 = (any("WORD PTR" in l and "0x933282" in l and l.startswith("movsx") for l in w1)
          and any(re.search(r"imul\s+\w+,\w+,0x34", l) for l in w1)
          and any("add    ecx,0x98ad88" in l or "0x98ad88" in l for l in w1))
    a2 = (any("WORD PTR" in l and "0x933282" in l and l.startswith("movsx") for l in w2)
          and any("0x98adac" in l for l in w2))
    W("T2b pinned-chain shapes: 0x4bdec4=%s 0x5ab3a2=%s (type rec field +0x24 read)"
      % (a1, a2))

    # ---- T3 the 67-record census ----
    nband = [u for u in punits if u["t"] >= SV.UNIT_TYPE_BAND]
    nong = [u for u in punits if u["t"] < SV.UNIT_TYPE_BAND]
    nmap = {t: n for (t, n) in named}
    for u in punits:
        W("T3 %2d off=%d x=%5d y=%5d +10=%4d band=%d name=%-22s own=%2d band==own=%s "
          "in-grid=%s" % (u["i"], u["off"], u["x"], u["y"], u["t"], band_of(u["t"]),
                          nmap.get(u["t"], "?"), owner_of(u, dprim),
                          band_of(u["t"]) == owner_of(u, dprim),
                          u["x"] < prim.width and u["y"] < prim.height))
    hits_named = sum(1 for u in punits if u["t"] in nmap)
    agree = [u for u in nband if band_of(u["t"]) == owner_of(u, dprim)]
    oob = [u for u in punits if not (u["x"] < prim.width and u["y"] < prim.height)]
    W("T3b n=%d band=%d non-band=%d band==owner=%d/%d named-hit=%d/%d out-of-grid=%d "
      "band0-only-for-non-band=%s distinct-owners(nongroup)=%d" %
      (len(punits), len(nband), len(nong), len(agree), len(nband), hits_named,
       len(punits), len(oob), all(u["t"] < BAND for u in nong),
       len({owner_of(u, dprim) for u in nong})))
    W("T3c band-value histogram %s" % ({v: sum(1 for u in punits if u["t"] == v)
                                        for v in sorted({u["t"] for u in nband})}))

    # ---- T4 the poke that justified the exemption ----
    a = open(PRIMARY, "rb").read()
    b = open(POKED, "rb").read()
    nd, runs = poke_runs(a, b, prim.units_off)
    inarr = [r for r in runs if r["inarr"]]
    marks = [r["val"] for r in runs]
    marker_ok = all((v >> 8) == 0xC0DE00 for v in marks)
    seq = [v & 0xFF for v in marks]
    stride_ok = all(runs[i + 1]["lo"] - runs[i]["lo"] == 128 for i in range(len(runs) - 1))
    cover_ok = all(r["covered"] for r in runs)
    sm, srows = layout[POKED][0], type_section(POKED)[3]
    soob = [u for u in srows if not (u["x"] < sm.width and u["y"] < sm.height)]
    poked_recs = sorted({r for w in runs for r in w["recs"]})
    W("T4 m54b->m113map differing bytes=%d windows=%d all-marker(0xc0de00NN)=%s "
      "seq=%s stride128=%s covered=%s windows-in-unit-array=%d records-touched=%s" %
      (nd, len(runs), marker_ok, seq, stride_ok, cover_ok, len(inarr), poked_recs))
    for r in inarr:
        W("T4  foff=%d recs=%s m54b=0x%08x m113=0x%08x ndiff=%d fields=%s" %
          (r["lo"], r["recs"], r["oval"], r["val"], r["ndiff"],
           ["%d+%d" % (rec, f) for (_i, rec, f) in r["bytes"]]))
    W("T4b m113map out-of-grid records=%s subset-of-poked=%s" %
      (sorted(u["i"] for u in soob),
       set(u["i"] for u in soob) <= set(poked_recs)))

    # ---- T5 the tile writer's straight-line path ----
    lo = [i for i, (ad, mn, t) in enumerate(ins) if ad == ENTRY]
    hi = [i for i, (ad, mn, t) in enumerate(ins) if ad >= ENTRY + 0x100]
    body = ins[lo[0]:hi[0]] if lo and hi else []
    def isjump(mn):
        return mn.startswith("j") and mn not in ("jmp",) or mn == "jmp"
    jumps = [(ad, mn, t) for (ad, mn, t) in body if isjump(mn)]
    # ALGO=4 mutant: treat EVERY branch in the function as a guard on the store
    pre = jumps if ALGO == "4" else [j for j in jumps if j[0] < STORE_X]
    tgt_in = []
    for (ad, mn, t) in jumps:
        m = re.search(r"0x([0-9a-f]+)", t)
        if m:
            tv = int(m.group(1), 16)
            if ENTRY < tv <= STORE_Y:
                tgt_in.append((ad, tv))
    st_x = [ (ad, t) for (ad, mn, t) in body if ad == STORE_X ]
    st_y = [ (ad, t) for (ad, mn, t) in body if ad == STORE_Y ]
    r10 = [(ad) for (ad, mn, t) in body if "0x933282" in t]
    W("T5 unit_set_position 0x%x body=%d insns jumps=%d jumps-before-+0-store=%d "
      "branch-targets-inside-(entry,%s]=%s store+0=%s store+2=%s reads-of-+10=%s" %
      (ENTRY, len(body), len(jumps), len(pre), hex(STORE_Y), tgt_in,
       [t for (_a, t) in st_x], [t for (_a, t) in st_y], [hex(x) for x in r10]))

    # ---- T6 M26's "+10 bits" under the index reading ----
    both = sum(1 for u in punits if (u["t"] & 0x40) and (u["t"] & 0x400))
    bit40 = sum(1 for u in punits if u["t"] & 0x40)
    w12 = [(u["i"], struct.unpack_from("<H", u["raw"], 12)[0]) for u in punits]
    W("T6 records with +10(word)&0x40=%d &0x400=%d both=%d; word@+12 nonzero=%d" %
      (bit40, sum(1 for u in punits if u["t"] & 0x400), both,
       sum(1 for _i, v in w12 if v)))

    # ---- T7 rivals: each must be FALSE ----
    common_bit = 0
    vals = sorted({u["t"] for u in nband})
    if vals:
        common_bit = vals[0]
        for v in vals[1:]:
            common_bit &= v
    R1 = (len(nband) - len(agree)) > 0 or (hits_named < len(punits))
    R2 = common_bit != 0
    poked_set = {os.path.basename(p) for p in SAVES
                 if layout[p][3] != layout[p][4]}
    unpoked = {os.path.basename(p) for p in SAVES if p != POKED}
    R3 = bool(poked_set & unpoked)
    R4 = len(pre) > 0 or bool(tgt_in)
    W("T7 R1(band-records-are-not-units)=%s R2(+10-is-a-flag-word:%d)=%s "
      "R3(exemption-bites-on-an-unpoked-save:%s)=%s R4(tile-store-is-guarded)=%s" %
      (R1, common_bit, R2, sorted(poked_set), R3, R4))

    # ---- gates ----
    G = []
    def gate(name, cond, detail):
        G.append((name, bool(cond), detail))
        W("%s %s %s" % (name, "PASS" if cond else "FAIL", detail))

    gate("G1", all(layout[p][2] == 4096 and layout[p][0].closes and
                   layout[p][1] == layout[p][0].count_off + 4 + layout[p][0].count_len
                   + 3584 for p in SAVES),
         "type array at count+4+len+3584 on 4/4 saves, 4096-B gap, closes=%s" %
         [layout[p][0].closes for p in SAVES])
    gate("G2", len(sites) == N_CHAIN and n_read == N_READ and a1 and a2
         and any(a == ANCHOR_READ for (a, m, b) in sites)
         and any(a == MOVEX_SITE for (a, m, b) in sites)
         and all(b.startswith("0x98ad") for (a, m, b) in sites),
         "chain sites=%d (pinned %d), +10 word refs=%d (pinned %d), pinned at 0x%x "
         "(unit idx->type rec) and 0x%x (unit_set_position -> type+0x24); shapes=%s/%s" %
         (len(sites), N_CHAIN, n_read, N_READ, ANCHOR_READ, MOVEX_SITE, a1, a2))
    gate("G3", len(punits) == 67 and len(nband) == 25 and len(nong) == 42
         and len(agree) == 25 and hits_named == 67 and len(oob) == 0
         and all(u["t"] < BAND for u in nong),
         "67=42+25; band==owner 25/25; 67/67 named; 0 out-of-grid; non-band all band0")
    gate("G4", len(named) == 32 and len(bands.get(0, [])) == 14
         and len([t for t in ff2c.get(True, []) if t < BAND]) == 14
         and len([t for t in ff2c.get(True, []) if t >= BAND]) == 0
         and len(bit2.get(1, [])) == 12 and len(bit2.get(0, [])) == 20,
         "32 named = 14 band0 + 18 faction-band; type byte +0x2d==0xff exactly on the "
         "14 band0 slots (0 of the 18); +0x30 bit2 NOT a band marker (12/20)")
    gate("G5", (pfa, pfb, pfc) == (67, 67, 67)
         and layout[POKED][3] == 67 and layout[POKED][4] == 49
         and all(layout[p][3] == layout[p][4] for p in SAVES if p != POKED),
         "exemption is load-bearing ONLY on m113map: 67 vs 49; 3/4 saves agree "
         "(the type-sound predicate C matches B on 4/4)")
    gate("G6", len(runs) == 20 and marker_ok and seq == list(range(1, 21))
         and stride_ok and cover_ok and len(inarr) == 13 and 12 in poked_recs
         and 17 in poked_recs and set(u["i"] for u in soob) <= set(poked_recs),
         "20 markers 0xc0de0001..0xc0de0014, stride 128, all diffs covered, 13 "
         "windows in the unit array touching 14 records; m113's out-of-grid set %s "
         "is a subset of the poked records %s" %
         (sorted(u["i"] for u in soob), poked_recs))
    gate("G7", len(pre) == 0 and not tgt_in and len(st_x) == 1 and len(st_y) == 1
         and "[esi+0x933278]" in st_x[0][1] and "[esi+0x93327a]" in st_y[0][1]
         and st_x[0][0] == STORE_X and st_y[0][0] == STORE_Y,
         "no branch on the entry path before the +0/+2 stores of unit_set_position "
         "(jumps in body=%d, none below %s; no jump target inside; stores pinned at "
         "%s/%s)" % (len(jumps), hex(STORE_X), hex(STORE_X), hex(STORE_Y)))
    gate("G8", all(set(bands.get(b, [])) <= set(M80_LIVE_BANDS[b]) for b in bands)
         and set(bands.get(5, [])) == set(M80_LIVE_BANDS[5]) - {324, 325},
         "save's named set == M80's LIVE census minus the 2 records M80 itself "
         "created (324/325)")
    import math
    p_named = (len(named) / float(TYPE_SLOTS)) ** len(punits)
    logp = math.log10(p_named) if p_named > 0 else -999
    gate("G11", hits_named == len(punits) and logp < -30,
         "67/67 records hit a NAMED type slot out of density 32/512: chance of that "
         "by coincidence = 10^%.1f (a flag-word or junk-field reading has no way to "
         "pick the 6%% of the array that carries names)" % logp)
    gate("G9", (not R1) and (not R2) and (not R3) and (not R4),
         "4 rivals all False (R2 AND of band values=%d; R3 differing saves=%s)" %
         (common_bit, sorted(poked_set)))
    detail = "\n".join(l for l in out if l.startswith("T"))
    dig = hashlib.sha256(detail.encode()).hexdigest()[:16]
    W("DIGEST %s" % dig)
    pin = os.environ.get("M327_PIN", PIN)
    ok = (dig == pin)
    G.append(("G10", ok, "digest==PIN"))
    W("G10 %s digest==PIN %s measured=%s (any drift in the measured rows reddens this)"
      % ("PASS" if ok else "FAIL", pin, dig))
    n = sum(1 for _x, c, _d in G if c)
    W("== M327: %d/%d ==" % (n, len(G)))
    txt = "\n".join(out) + "\n"
    sys.stdout.write(txt)
    dst = os.path.join(EV, "evidence/m327_typeband_census.txt")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, "w").write(txt)
    return 0 if n == len(G) else 1


if __name__ == "__main__":
    sys.exit(main())
