#!/usr/bin/env python3
"""M337 (pick x8) — the item table's RUNTIME ROW ORDER, read off the loader itself.

Claim under test: the "39-row item table" at `0x984d48` is not a table of its own. It is the
`+0x10` dword of the 72-record array based at `0x984d38` (M53i), addressed by
`[48*idx + 0x984d48]` (M333/B28).  This instrument reads the LOADER at `0x57a7ef..0x57a899`
out of `programs/terran.exe` and settles the row order statically:

  * the section opened is the ASCII `FACILITIES` (pushed at `0x57a7f5`, ini open `0x5ea431`);
  * the cursor starts at `0x984d74` = record 1 + 0xc, steps `+0x30`, stops at `0x985ac4`
    = record 72 + 0xc  => records 1..71 written, record 0 (the placeholder) untouched;
  * each iteration reads ONE line and advances the cursor ONE record, so the k-th row read
    goes to record k: order = file order by construction;
  * records 1..38 take the 6-token path, records 39..71 the 11-token path (`cmp esi,0x985494`
    at `0x57a85d`), and alpha.txt's FIRST 11-token row is row index 38 (`The Human Genome
    Project`, alpha.txt:629) — so record i == alpha row i-1 for every row this loader writes;
  * the token reader `0x5ea985` consumes one comma-delimited token per call (stops on 0x2c,
    advances `[this+0x150]`), and all three converters (`0x5ea466/0x5ea475/0x5ea484`) call it,
    so the store order IS the file column order;
  * the consumers' loop bound is 39 (`cmp esi,0x27` at `0x4f4a35`), the ARRAY end is record 72,
    so "39 rows" is a consumer window, not the table size.

Zero box time: bytes from terran.exe + alpha.txt only.

    python3 -u scripts/m337_item_order.py                 # PASS/FAIL + table
    python3 -u scripts/m337_item_order.py --json          # machine line for the harness
    python3 -u scripts/m337_item_order.py --exe X --alpha Y
"""
import hashlib
import json
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, "programs", "terran.exe")
ALPHA = os.path.join(ROOT, "programs", "alpha.txt")

IMG = 0x400000
BASE = 0x984D38           # record array base (M53i: 72 x 48 B, alpha #FACILITIES verbatim)
STRIDE = 0x30
VIEW = 0x984D48           # what M46 called "the 39-row item table"
REC_FIELD = 0x10          # upkeep dword inside a record: VIEW - BASE
LOOP_LO, LOOP_HI = 0x57A81A, 0x57A89F
CONSUMER_BOUND = 0x4F4A35  # `cmp esi,0x27` at the bottom of the upkeep loop

# instruction sites (VA, expected bytes) — every number below is decoded from bytes
SITES = {
    "push_sec":      (0x57A7F5, "68 cc 1c 69 00"),        # push 0x691ccc ("FACILITIES")
    "start":         (0x57A810, "be 74 4d 98 00"),        # mov esi,0x984d74
    "branch_cmp":    (0x57A85D, "81 fe 94 54 98 00"),     # cmp esi,0x985494
    "branch_jl":     (0x57A866, "7c 28"),                 # jl 0x57a890 (skip trailing cols)
    "stride":        (0x57A890, "83 c6 30"),              # add esi,0x30
    "end_cmp":       (0x57A893, "81 fe c4 5a 98 00"),     # cmp esi,0x985ac4
    "back_edge":     (0x57A899, "0f 8c 7b ff ff ff"),     # jl 0x57a81a
    "consumer_bound": (CONSUMER_BOUND, "83 fe 27"),       # cmp esi,0x27 (upkeep loop bound)
    "tok_comma":     (0x5EA9B6, "83 f9 2c"),              # cmp ecx,0x2c  (',' in the token reader)
    "tok_advance":   (0x5EA9DD, "83 c2 01"),              # add edx,1
    "tr1":           (0x57A86D, "89 46 10"),              # rec+0x1c <- 1st trailing token
    "tr2":           (0x57A875, "89 46 20"),              # rec+0x2c <- 2nd
    "tr3":           (0x57A87D, "89 46 18"),              # rec+0x24 <- 3rd
    "tr4":           (0x57A885, "89 46 1c"),              # rec+0x28 <- 4th
    "tr5":           (0x57A88D, "89 46 14"),              # rec+0x20 <- 5th
    "tok_store":     (0x5EA9E3, "89 90 50 01 00 00"),     # mov [eax+0x150],edx (cursor advance)
    "fold_lea":      (0x4F48C8, "8d 04 76"),              # lea eax,[esi+esi*2]
    "fold_shl":      (0x4F48CB, "c1 e0 04"),              # shl eax,4  (=> *48)
    "fold_load":     (0x4F48CE, "8b 80 48 4d 98 00"),     # mov eax,[eax+0x984d48]
}
CONVERTERS = {"str": 0x5EAA3F, "int": 0x5EAA5D, "tech": 0x5EAA79}   # call sites in 0x5ea466/75/84
NEXT_TOK = 0x5EA985


def pe_reader(path):
    b = open(path, "rb").read()
    pe = struct.unpack_from("<I", b, 0x3C)[0]
    nsec = struct.unpack_from("<H", b, pe + 6)[0]
    optsz = struct.unpack_from("<H", b, pe + 20)[0]
    base = pe + 24 + optsz
    secs = []
    for i in range(nsec):
        o = base + i * 40
        vs, va, rs, rp = struct.unpack_from("<IIII", b, o + 8)
        secs.append((IMG + va, rs, rp))

    def read(va, n):
        for v, rs, rp in secs:
            if v <= va < v + rs:
                return b[rp + (va - v): rp + (va - v) + n]
        raise KeyError("va %#x not mapped" % va)

    def u32(va):
        return struct.unpack("<I", read(va, 4))[0]
    return read, u32


def parse_alpha(path):
    """the #FACILITIES rows of alpha.txt, file order; one list of stripped fields each.

    ';' starts a comment (alpha.txt convention): six later rows carry their trailing columns
    as text after a ';'.  Short rows are kept — the gates report them."""
    rows = []
    lines = open(path, "r", errors="replace").read().splitlines()
    started = False
    for n, ln in enumerate(lines, 1):
        s = ln.strip()
        if s.upper() == "#FACILITIES":
            started = True
            continue
        if not started:
            continue
        if not s or s.startswith(";") or s.startswith("#"):
            break
        s = s.split(";")[0]
        f = [x.strip() for x in s.split(",")]
        while f and f[-1] == "":
            f.pop()
        rows.append((n, f))
    return rows


def build_table(rows):
    """the 72 printed rows; a short/missing alpha row prints a marker instead of raising."""
    out = []
    for i in range(72):
        if i == 0:
            out.append("%3d %6s %-32s %4s %3s %-8s %2s" % (
                i, "-", "<placeholder: this loop never writes record 0>", "-", "-", "-", "-"))
            continue
        if i - 1 >= len(rows):
            out.append("%3d %6s %-32s %4s %3s %-8s %2s" % (
                i, "-", "<MISSING alpha row>", "-", "-", "-", "-"))
            continue
        ln, f = rows[i - 1]
        g = (f + ["?"] * 4)[:4]
        out.append("%3d %6d %-32s %4s %3s %-8s %2d" % (i, ln, g[0][:32], g[1], g[2], g[3], len(f)))
    return out


def decode_stores(read, lo, hi):
    """every `mov [esi(+disp8)], r32` in [lo,hi): (pc, reg, record_offset from record+0xc)."""
    out = []
    va = lo
    while va < hi:
        b = read(va, 3)
        if b[0] == 0x89 and b[1] == 0x06:                 # [esi],eax
            out.append((va, 0, 0x0C))
            va += 2
        elif b[0] == 0x89 and b[1] in (0x46, 0x7E):       # [esi+disp8],eax/edi
            disp = struct.unpack_from("<b", b, 2)[0]
            out.append((va, (b[1] >> 3) & 7, 0x0C + disp))
            va += 3
        else:
            va += 1
    return out


def main():
    argv = sys.argv[1:]
    exe = EXE
    alpha_path = ALPHA
    as_json = "--json" in argv
    if "--exe" in argv:
        exe = argv[argv.index("--exe") + 1]
    if "--alpha" in argv:
        alpha_path = argv[argv.index("--alpha") + 1]

    read, u32 = pe_reader(exe)
    rows = parse_alpha(alpha_path)
    gates, results = {}, {}

    def gate(gid, label, fn):
        try:
            num = fn()
            gates[gid] = "PASS"
            results[gid] = num
            if not as_json:
                print("PASS %s %s %s" % (gid, label, num))
        except AssertionError as e:
            gates[gid] = "FAIL"
            results[gid] = str(e)
            if not as_json:
                print("FAIL %s %s %s" % (gid, label, e))

    def check(site):
        va, want = SITES[site]
        got = read(va, len(bytes.fromhex(want)))
        assert got.hex(" ") == want, "%s at 0x%x is %s, wanted %s" % (site, va, got.hex(" "), want)
        return got

    # ---- the table FIRST -------------------------------------------------------------
    table = build_table(rows)
    tbl_txt = "\n".join(table)
    tbl_digest = hashlib.sha1(tbl_txt.encode()).hexdigest()

    if not as_json:
        print("M337 — the item table's runtime row order (static, zero box)")
        print("exe=%s alpha=%s" % (os.path.basename(exe), os.path.basename(alpha_path)))
        print("VIEW 0x%x = record field +0x%x of the array at 0x%x (stride 0x%x)" %
              (VIEW, REC_FIELD, BASE, STRIDE))
        print("LOADER 0x57a7ef-0x57a899: push \"FACILITIES\" -> INI open; cursor esi = record+0xc")
        print("  start 0x%x (rec %d)  branch 0x%x (rec %d)  end 0x%x (rec %d)" %
              (u32(0x57A811), (u32(0x57A811) - 0xC - BASE) // STRIDE,
               u32(0x57A85F), (u32(0x57A85F) - 0xC - BASE) // STRIDE,
               u32(0x57A895), (u32(0x57A895) - 0xC - BASE) // STRIDE))
        print()
        print("rec  alpha_ln  name                             cost upk tech      nf")
        print(tbl_txt)
        print()

    # ---- G1: the section opened is #FACILITIES, and the loop shape is the cursor loop ----
    def g1():
        got = check("push_sec")
        sec_va = struct.unpack_from("<I", got, 1)[0]
        name = read(sec_va, 12).split(b"\0")[0].decode()
        assert name == "FACILITIES", "pushed string at 0x%x is %r" % (sec_va, name)
        check("stride")
        check("back_edge")
        return "section=%s @0x%x stride=0x%x back-edge-jl" % (name, sec_va, STRIDE)
    gate("G1", "loader opens the FACILITIES section and steps 0x30", g1)

    # ---- G2: the window arithmetic + the consumers' bound vs the array end ----
    def g2():
        check("start")
        check("branch_cmp")
        check("end_cmp")
        rec = {}
        for nm, imm in (("start", u32(0x57A811)), ("branch", u32(0x57A85F)), ("end", u32(0x57A895))):
            assert (imm - 0xC - BASE) % STRIDE == 0, "%s imm 0x%x not record-aligned" % (nm, imm)
            rec[nm] = (imm - 0xC - BASE) // STRIDE
        assert rec["start"] == 1, "cursor starts at record %d, not 1" % rec["start"]
        assert rec["branch"] == 39, "branch at record %d, not 39" % rec["branch"]
        assert rec["end"] == 72, "end at record %d, not 72" % rec["end"]
        assert rec["end"] - rec["start"] == 71, "loop writes %d records" % (rec["end"] - rec["start"])
        cb = check("consumer_bound")                      # 83 fe 27 -> cmp esi,0x27
        bound = cb[2]
        assert bound == 39, "consumer range-bound immediate is %d, not 39" % bound
        assert bound != rec["end"], "consumer bound %d equals the array end" % bound
        return "start=rec%d branch=rec%d end=rec%d iterations=%d; consumer-bound=%d != end=%d" % (
            rec["start"], rec["branch"], rec["end"], rec["end"] - rec["start"], bound, rec["end"])
    gate("G2", "window: records 1..71, branch 39, end 72; consumer bound 39 != 72", g2)

    # ---- G3: alpha has exactly as many rows as the loop writes ----
    def g3():
        n = len(rows)
        census = {}
        for _, f in rows:
            census[len(f)] = census.get(len(f), 0) + 1
        assert n == 71, "alpha #FACILITIES parsed %d rows" % n
        assert (u32(0x57A895) - u32(0x57A811)) // STRIDE == n, "loop iterations != row count"
        assert census.get(6, 0) == 42 and census.get(7, 0) == 2 and census.get(11, 0) == 27, \
            "field-count census %s" % census
        assert sum(census.values()) == n, "census rows %d != parsed %d" % (sum(census.values()), n)
        aj = os.path.join(ROOT, "data", "alpha.json")
        if os.path.exists(aj):
            ref = [len(r["fields"]) for r in json.load(open(aj))["FACILITIES"]]
            mine = [len(f) for _, f in rows]
            assert ref == mine, "in-tree parse differs from data/alpha.json on %d rows" % sum(
                1 for a, b in zip(ref, mine) if a != b)
        return "rows=%d census=%s" % (n, json.dumps(census, sort_keys=True))
    gate("G3", "alpha row count == loop iterations == 71", g3)

    # ---- G4: sequential mapping — one line read + one record step per iteration, branch on
    #          alpha's first 11-token row ----
    def g4():
        if len(rows) < 39 or len(rows[38][1]) < 4:
            raise AssertionError("alpha row 38 missing/short (%d rows)" % len(rows))
        first_long = next((i for i, (_, f) in enumerate(rows) if len(f) > 7), -1)
        branch_rec = (u32(0x57A85F) - 0xC - BASE) // STRIDE
        assert first_long == 38, "alpha's first >7-field row is index %d" % first_long
        assert branch_rec == first_long + 1, \
            "branch record %d != alpha row %d + 1" % (branch_rec, first_long)
        short_before = sum(1 for _, f in rows[:first_long] if len(f) <= 7)
        long_after = sum(1 for _, f in rows[first_long:] if len(f) == 11)
        assert short_before == first_long, "%d/%d rows before the boundary are <=7 fields" % (
            short_before, first_long)
        assert len(rows[first_long][1]) == 11, "row %d has %d fields" % (
            first_long, len(rows[first_long][1]))
        assert long_after >= 1, "no 11-token row at/after the boundary"
        # sequential mapping: exactly ONE line-read and ONE record step per iteration
        line_reads = [va for va in range(LOOP_LO, LOOP_HI)
                      if read(va, 1)[0] == 0xE8
                      and va + 5 + struct.unpack_from("<i", read(va + 1, 4))[0] == 0x5EA448]
        steps = [va for va in range(LOOP_LO, LOOP_HI) if read(va, 3).hex(" ") == "83 c6 30"]
        assert len(line_reads) == 1, "loop body has %d line-read calls" % len(line_reads)
        assert len(steps) == 1, "loop body has %d record steps" % len(steps)
        seven = [i for i, (_, f) in enumerate(rows) if len(f) == 7]
        return ("alpha first >7-token row=%d (%s, alpha.txt:%d) -> record %d; rows before=%d/%d "
                "short, 11-token at/after=%d/%d; 7-field rows %s (7th token stays on the line); "
                "line-reads/iter=%d record-steps/iter=%d => k-th line -> record k"
                % (first_long, rows[first_long][1][0], rows[first_long][0], branch_rec,
                   short_before, first_long, long_after, len(rows) - first_long, seven,
                   len(line_reads), len(steps)))
    gate("G4", "record i == alpha row i-1: one line read + one record step per iteration", g4)

    # ---- G5: decoded store sequence == file column order (bytes, not a hand list) ----
    def g5():
        for site in ("tok_comma", "tok_advance", "tok_store"):
            check(site)
        for nm, va in CONVERTERS.items():
            rel = struct.unpack_from("<i", read(va + 1, 4))[0]
            assert va + 5 + rel == NEXT_TOK, "%s converter calls 0x%x not 0x%x" % (
                nm, va + 5 + rel, NEXT_TOK)
        st = decode_stores(read, LOOP_LO, LOOP_HI)
        seq = [rec for _, _, rec in st]
        assert len(st) == 12, "decoded %d stores in the loop body: %s" % (len(st), seq)
        assert seq[:6] == [0x00, 0x0C, 0x10, 0x14, 0x18, 0x04], "primary store order %s" % seq[:6]
        assert st[6][1] == 7 and seq[6] == 0x18, "7th store is not the -2 edi overwrite: %r" % (
            st[6],)
        assert seq[7:] == [0x1C, 0x2C, 0x24, 0x28, 0x20], "trailing store order %s" % seq[7:]
        return "12 decoded stores: %s | trailing %s" % (
            ",".join("+0x%02x" % s for s in seq),
            ",".join("+0x%02x" % s for s in seq[7:]))
    gate("G5", "decoded store order == column order (one advancing token per call)", g5)

    # ---- G6: 0x984d48 is this array's +0x10 field ----
    def g6():
        for site in ("fold_lea", "fold_shl", "fold_load"):
            check(site)
        disp = u32(0x4F48D0)                                  # the mov's disp32
        assert disp == VIEW, "consumer disp 0x%x != 0x%x" % (disp, VIEW)
        assert VIEW - BASE == REC_FIELD == 0x10, "view offset 0x%x" % (VIEW - BASE)
        st = decode_stores(read, LOOP_LO, LOOP_HI)
        slots = [i for i, (_, _, rec) in enumerate(st) if rec == REC_FIELD]
        assert slots, "no store to rec+0x10 in the decoded sequence"
        assert st[slots[0]][1] == 0, "the rec+0x10 store is not an eax store"
        return "+0x%x field; fold = 48*idx + 0x%x; loader's store #%d lands at rec+0x10" % (
            REC_FIELD, VIEW, slots[0] + 1)
    gate("G6", "the 0x984d48 view is the array's +0x10 dword", g6)

    # ---- G7: rival explanations, each refuted on printed numbers ----
    def g7():
        rivals = {}
        end_rec = (u32(0x57A895) - 0xC - BASE) // STRIDE
        rivals["R1-array-is-39"] = (end_rec == 39, "loader end = record %d, not 39" % end_rec)
        branch_rec = (u32(0x57A85F) - 0xC - BASE) // STRIDE
        first_long = next((i for i, (_, f) in enumerate(rows) if len(f) > 7), -1)
        jl_va = SITES["branch_jl"][0]
        tgt = jl_va + 2 + struct.unpack_from("<b", read(jl_va + 1, 1))[0]
        trail_pcs = [SITES[s][0] for s in ("tr1", "tr2", "tr3", "tr4", "tr5")]
        skipped = tgt == 0x57A890 and all(jl_va < pc < tgt for pc in trail_pcs)
        rivals["R2-projects-elsewhere"] = (
            not skipped, "jl at 0x%x -> 0x%x skips all 5 trailing stores (%s); branch at rec %d "
            "== alpha row %d + 1" % (jl_va, tgt, skipped, branch_rec, first_long))
        costs = [int(f[1]) for _, f in rows if len(f) > 1 and f[1].lstrip("-").isdigit()]
        inv = sum(1 for a, b in zip(costs, costs[1:]) if b < a)
        rivals["R3-cost-sorted"] = (inv == 0, "cost inversions in file order: %d (first costs %s)"
                                    % (inv, costs[:10]))
        start = (u32(0x57A811) - 0xC - BASE) // STRIDE
        rivals["R4-starts-at-record-0"] = (
            start == 0, "cursor starts at record %d (+0x%x from base)"
            % (start, start * STRIDE + 0x0C))
        st = decode_stores(read, LOOP_LO, LOOP_HI)
        trail = [rec for _, _, rec in st][7:]
        rivals["R5-trailing-monotone"] = (trail == sorted(trail),
                                          "trailing store order %s is not monotone"
                                          % ",".join("0x%02x" % t for t in trail))
        dead = [k for k, (survives, _) in rivals.items() if survives]
        assert not dead, "rival(s) survived: %s" % dead
        return "5 rivals refuted: " + " | ".join("%s: %s" % (k, msg) for k, (_, msg) in rivals.items())
    gate("G7", "rival row-order models fail on the printed numbers", g7)

    # ---- G8: determinism ----
    def g8():
        rows2 = parse_alpha(alpha_path)
        d2 = hashlib.sha1("\n".join(build_table(rows2)).encode()).hexdigest()
        assert d2 == tbl_digest, "second pass digest %s != %s" % (d2, tbl_digest)
        assert tbl_digest == "39d82f0771690e15e5d9e3828f7b5cc000fd1c68", "table digest %s" % tbl_digest
        return "table digest %s (x2)" % tbl_digest
    gate("G8", "two passes give the pinned table digest", g8)

    if as_json:
        print(json.dumps({"gates": gates, "detail": results, "table_digest": tbl_digest},
                         sort_keys=True))
    else:
        print()
        print("table digest %s" % tbl_digest)
        npass = sum(1 for v in gates.values() if v == "PASS")
        verdict = "PASS" if npass == len(gates) else "FAIL"
        print("%s M337: %d/%d gates" % (verdict, npass, len(gates)))
    return 0 if all(v == "PASS" for v in gates.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
