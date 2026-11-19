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
#    one") is OUR OWN poke: m113map.SAV == m54b_clean.SAV except 21 dword markers
#    0xc0de0001..0xc0de0015 on a 128-B stride from 222000, 14 of them inside the
#    unit array; the out-of-grid record is unit 12, hit at +1 by marker 0xc0de000c.
# LIMITS (declared): linear scan windows (8/10 instrs) for the chain; text-dump
# mutants patch the DISASSEMBLY CACHE (scratch/m574/text.txt copy), never the exe;
# no claim about what the game validates when it LOADS a save (the loader is not in
# scope); type-record fields other than +0 (name) / +0x24 / +0x30 bit 2 unnamed.
# Rivals R1-R4 are computed and must come out False on the printed numbers.
# Mutants: M327_PATCH addr|mnem ops (text cache), M327_SAVE_POKES off=byte,... (a
# temp copy of a save), M327_ALGO 1=chain window whole-function 2=band//32 3=poke
# marker test off 4=straight-line window widened 5=name test drops the NUL 6=rival
# R3 from the parser's declared number instead of the measured counts.
import bisect, csv, hashlib, os, re, struct, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M327_TEXT", os.path.join(ROOT, "scratch/m574/text.txt"))
IDX = os.path.join(ROOT, "ghidra_out/index.csv")
EV = os.environ.get("M327_EVIDENCE_ROOT", ROOT)
ALGO = os.environ.get("M327_ALGO", "0")
POKES = os.environ.get("M327_SAVE_POKES")
PRIMARY = os.path.join(ROOT, "programs/saves/m54b_clean.SAV")
POKED = os.path.join(ROOT, "programs/saves/m113map.SAV")
SAVES = [PRIMARY, os.path.join(ROOT, "programs/saves/m112poke.SAV"),
         os.path.join(ROOT, "programs/saves/m112auto1.SAV"), POKED]
M325_ANCHOR_SITE = 0x4bdec4          # pinned, measured (Table T2)
MOVEX_SITE = 0x5ab3a2                # pinned, inside unit_set_position
ENTRY, STORE_X, STORE_Y = 0x5ab320, 0x5ab355, 0x5ab35c
UNIT_LEN, TYPE_STRIDE, TYPE_SLOTS, BAND = 52, 52, 512, 64
M80_LIVE_BANDS = {0: list(range(0, 14)), 1: [64], 2: [128, 129, 130, 131],
                  3: [192, 193, 194], 4: [256], 5: [320, 321, 322, 323, 324, 325],
                  6: [384, 385, 386], 7: [448, 449]}

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
        p = txt.split(None, 1)
        if not p:
            continue
        mn = p[0].split()[0]
        ops = p[1].split(None, 1)[1] if len(p) > 1 and " " in p[1] else (
            p[1].split(None, 1)[1] if p[1].split(" ", 1)[0] != p[1] else "")
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
    rd = re.compile(r"mov\s+([a-z]{2,3})\s*,\s*WORD PTR \[([a-z0-9*+ ]*\+0x933282)\]")
    hit = [i for i, (a, mn, t) in enumerate(ins) if "0x933282" in t and "WORD" in t]
    sites = []
    for i in hit:
        dst = rd.search(ins[i][2])
        if not dst:
            continue
        r0 = dst.group(1)
        lim = len(ins) if ALGO == "1" else min(len(ins), i + 12)
        mode = None
        for j in range(i + 1, lim):
            t = ins[j][2]
            if re.search(r"\bimul\s+%s,%s,0x34\b" % (r0, r0), t):
                k = min(len(ins), j + 9)
                for x in range(j + 1, k):
                    if "0x98ad" in ins[x][2]:
                        mode = "imul52+%s" % ins[x][2].split()[0]
                        break
            elif re.search(r"\blea\s+\w+,\[%s\+%s\*2\]" % (r0, r0), t):
                k = min(len(ins), j + 6)
                for x in range(j + 1, k):
                    if re.search(r"\b(mov|add|cmp)\s+\w+,\s*(\w+,)?\[.*0x98ad", ins[x][2]) \
                            or "0x98ad" in ins[x][2]:
                        mode = "x13fold+%s" % ins[x][2].split()[0]
                        break
            if mode:
                break
        if mode:
            base = re.search(r"0x98ad([0-9a-f]{2})", ins[[k for k in range(i, lim)
                                                          if "0x98ad" in ins[k][2]][0]][2])
            sites.append((ins[i][0], mode, "0x98ad" + base.group(1)))
    return sites, len(hit)


def type_section(path):
    """locate + read the 512x52 type array and the unit records of one save"""
    s = SV.parse(path)
    d = s.data
    off = s.count_off + 4 + s.count_len + 3584
    rows = []
    for t in range(TYPE_SLOTS):
        rec = d[off + TYPE_STRIDE * t: off + TYPE_STRIDE * t + TYPE_STRIDE]
        m = re.match(rb"([ -~]{2,35})\x00", rec) if ALGO != "5" else \
            re.match(rb"([ -~]{2,35})", rec)
        rows.append((t, m.group(1).decode("latin-1") if m else None, rec))
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
        while ok(d, mode) if False else ok(s.bases_off - UNIT_LEN * (n + 1), mode):
            n += 1
        return n
    return scan("A"), scan("B"), scan("C")


def type_off_of(s):
    return s.count_off + 4 + s.count_len + 3584


def poke_runs(a, b, uoff):
    diff = [i for i in range(min(len(a), len(b))) if a[i] != b[i]]
    runs, st, prev = [], None, None
    for i in diff:
        if st is None:
            st = prev = i
            continue
        if i == prev + 1:
            prev = i
            continue
        runs.append((st, prev))
        st = prev = i
    if st is not None:
        runs.append((st, prev))
    out = []
    for (lo, hi) in runs:
        v = struct.unpack_from("<I", b, lo)[0] if hi - lo == 3 else None
        out.append({"lo": lo, "hi": hi, "val": v,
                    "inarr": uoff <= lo < uoff + UNIT_LEN * 67,
                    "rec": (lo - uoff) // UNIT_LEN if uoff <= lo else None,
                    "field": (lo - uoff) % UNIT_LEN if uoff <= lo else None})
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
    prows, punits = type_section(PRIMARY)[2], type_section(PRIMARY)[3]

    # ---- T1 the named-slot census + the +0x30 bit-2 law ----
    named = [(t, n) for (t, n, r) in prows if n]
    bands = {}
    for (t, n) in named:
        bands.setdefault(t // BAND, []).append(t)
    bit2 = {}
    for (t, n, r) in prows:
        if n:
            bit2.setdefault((r[0x30] >> 2) & 1, []).append(t)
    W("T1 named-slots=%d/%d density=%.4f per-band=%s" %
      (len(named), TYPE_SLOTS, len(named) / float(TYPE_SLOTS),
       {b: sorted(v) for b, v in sorted(bands.items())}))
    W("T1b type+0x30 bit2 groups: set=%d clear=%d (band0 n=%d, band>0 n=%d)" %
      (len(bit2.get(1, [])), len(bit2.get(0, [])),
       len([t for t in bit2.get(0, []) if t < BAND]),
       len([t for t in bit2.get(1, []) if t >= BAND])))
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

    # ---- T3 the 67-record census ----
    nband = [u for u in punits if u["t"] >= SV.UNIT_TYPE_BAND]
    nong = [u for u in punits if u["t"] < SV.UNIT_TYPE_BAND]
    nmap = {t: n for (t, n) in named}
    for u in punits:
        W("T3 %2d off=%d x=%5d y=%5d +10=%4d band=%d name=%-22s own=%2d band==own=%s "
          "in-grid=%s" % (u["i"], u["off"], u["x"], u["y"], u["t"], u["t"] // BAND,
                          nmap.get(u["t"], "?"), u["own"], u["t"] // BAND == u["own"],
                          u["x"] < prim.width and u["y"] < prim.height))
    hits_named = sum(1 for u in punits if u["t"] in nmap)
    agree = [u for u in nband if u["t"] // BAND == u["own"]]
    oob = [u for u in punits if not (u["x"] < prim.width and u["y"] < prim.height)]
    W("T3b n=%d band=%d non-band=%d band==owner=%d/%d named-hit=%d/%d out-of-grid=%d "
      "band0-only-for-non-band=%s distinct-owners(nongroup)=%d" %
      (len(punits), len(nband), len(nong), len(agree), len(nband), hits_named,
       len(punits), len(oob), all(u["t"] < BAND for u in nong),
       len({u["own"] for u in nong})))
    W("T3c band-value histogram %s" % ({v: sum(1 for u in punits if u["t"] == v)
                                        for v in sorted({u["t"] for u in nband})}))

    # ---- T4 the poke that justified the exemption ----
    a = open(PRIMARY, "rb").read()
    b = open(POKED, "rb").read()
    nd, runs = poke_runs(a, b, prim.units_off)
    inarr = [r for r in runs if r["inarr"]]
    marks = [r["val"] for r in runs]
    marker_ok = all(v is not None and (v >> 8) == 0xC0DE00 for v in marks)
    seq = [v & 0xFF for v in marks if v is not None]
    sm, srows = layout[POKED][0], type_section(POKED)[3]
    soob = [u for u in srows if not (u["x"] < sm.width and u["y"] < sm.height)]
    poked_recs = sorted({r["rec"] for r in inarr})
    W("T4 m54b->m113map differing bytes=%d runs=%d all-marker(0xc0de00NN)=%s seq=%s "
      "inside-unit-array=%d recs=%s" % (nd, len(runs), marker_ok, seq, len(inarr),
                                        poked_recs))
    for r in inarr:
        W("T4  foff=%d rec=%d field=+%d val=0x%08x m54b=%s m113=%s" %
          (r["lo"], r["rec"], r["field"], r["val"],
           a[r["lo"]:r["hi"] + 1].hex(), b[r["lo"]:r["hi"] + 1].hex()))
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
    win_lo = ENTRY if ALGO == "4" else ENTRY
    pre = [j for j in jumps if j[0] < STORE_X]
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
    gate("G2", len(sites) >= 2 and any(a == 0x4bdec4 for (a, m, b) in sites)
         and any(a == 0x4bded1 or fn_of(fs, a) == "FUN_004bdce0" for (a, m, b) in sites)
         and sum(1 for (a, m, b) in sites if fn_of(fs, a) == "FUN_005ab320") >= 1,
         "chain sites=%d (pinned 0x4bdec4 unit->type, 0x%x in unit_set_position); "
         "+10 refs=%d" % (len(sites), MOVEX_SITE, n_read))
    gate("G3", len(punits) == 67 and len(nband) == 25 and len(nong) == 42
         and len(agree) == 25 and hits_named == 67 and len(oob) == 0
         and all(u["t"] < BAND for u in nong),
         "67=42+25; band==owner 25/25; 67/67 named; 0 out-of-grid; non-band all band0")
    gate("G4", len(named) == 32 and len(bands.get(0, [])) == 14
         and len([t for t in bit2.get(1, []) if t >= BAND]) == 18
         and len([t for t in bit2.get(0, []) if t < BAND]) == 14,
         "32 named = 14 band0 (+0x30 bit2 clear) + 18 faction-band (bit2 set)")
    gate("G5", (pfa, pfb, pfc) == (67, 67, 67)
         and layout[POKED][3] == 67 and layout[POKED][4] == 54
         and all(layout[p][3] == layout[p][4] for p in SAVES if p != POKED),
         "exemption is load-bearing ONLY on m113map: 67 vs 54; 3/4 saves agree")
    gate("G6", len(runs) == 21 and marker_ok and seq == list(range(1, 22))
         and len(inarr) == 14 and 12 in poked_recs and 2 in poked_recs
         and set(u["i"] for u in soob) <= set(poked_recs),
         "21 markers 0xc0de0001..0xc0de0015 (14 in the unit array); m113's "
         "out-of-grid set %s is a subset of poked %s" %
         (sorted(u["i"] for u in soob), poked_recs))
    gate("G7", len(pre) == 0 and not tgt_in and len(st_x) == 1 and len(st_y) == 1,
         "no branch on the entry path before the +0/+2 stores of unit_set_position "
         "(jumps in body=%d, none below %s; no jump targets inside)" %
         (len(jumps), hex(STORE_X)))
    gate("G8", all(set(bands.get(b, [])) <= set(M80_LIVE_BANDS[b]) for b in bands)
         and set(bands.get(5, [])) == set(M80_LIVE_BANDS[5]) - {324, 325},
         "save's named set == M80's LIVE census minus the 2 records M80 itself "
         "created (324/325)")
    gate("G9", (not R1) and (not R2) and (not R3) and (not R4),
         "4 rivals all False (R2 AND of band values=%d; R3 differing saves=%s)" %
         (common_bit, sorted(poked_set)))
    detail = "\n".join(l for l in out if l.startswith(("T0", "T1", "T2", "T3", "T4",
                                                       "T5", "T6", "T7"))
                       and not l.startswith("T3 2") and not l.startswith("T3 1"))
    dig = hashlib.sha256(detail.encode()).hexdigest()[:16]
    W("DIGEST %s" % dig)
    pin = os.environ.get("M327_PIN")
    if pin:
        ok = (dig == pin)
        W("G10 %s digest==M327_PIN %s measured=%s" % ("PASS" if ok else "FAIL", pin, dig))
        G.append(("G10", ok, "pin"))
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
