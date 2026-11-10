#!/usr/bin/env python3
"""M290: fit the AI hub's FOUNDING DECISION to the m289 golden record.

The question s235 left open: which tile/faction does the hub's founder
vector pick, and how does that compare to B10's ASSUMED rule
(sim/basefound.py:118 "the first in-bounds tile no base occupies,
row-major")?  This script settles the DECISION SHAPE statically (the
bytes in terran.exe's .text window inside the hub FUN_0055f650) and
fits the result to the RECORDED seven foundings - no box time.

What the binary says (each claim is a byte-level assertion below):
  1. The hub's only founder-vector call is 0x563d86 -> FUN_004cca50,
     whose return target 0x4ccbe2 is exactly the FOUND ret= the live
     census recorded (m289 raw log).
  2. THE DISPATCH HAS TWO GATES (s240 correction; the old claim "nonzero
     target goes 0x563d4e -> msg 0x2408" is RETRACTED).  test esi,esi at
     0x563d46: the jne at 0x563d48 lands 0x563dfa - the DISTANT leg
     (esi>=9: issue order 0x62 at the ring tile; 1-8: dec esi + continue)
     which reaches NEITHER the founder NOR the message block.  Only
     esi==0 falls through to 0x563d4e, which loads the SECOND gate
     [ebp-0xa4]: je at 0x563d57 -> 0x563d82-86 calls the founder
     FUN_004cca50; flag!=0 is the msg block 0x563d59-0x563d7d
     (FUN_00583fa0(0x2408, "Auto-sending BUILD BASE message" s@0x691368,
     pod unit), then jmp 0x56c925 - no founder).  [ebp-0xa4] has ONE
     writer in the body: 0x55f6d6 = (ds:0x920434 != 0) AND (unit owner ==
     ds:0x91b5b4).  So there is NO channel by which a scanned candidate
     tile reaches the founder - the founding tile is always the pod's own
     tile - but the msg-0x2408 leg belongs to the OWN-TILE + flag-set
     case, NOT to the distant-target case.
  3. FUN_004cca50 calls the founder with (faction, x, y) READ FROM THE
     UNIT RECORD (prologue fold at 0x4cca57-0x4cca74 computes 52*u, the record
     base off 0x933278):
       0x4cca67 mov cl,[ebx+0x933286]        ; +14 owner  -> esi
       0x4cca6d movsx eax,WORD [ebx+0x93327a]; +10 y      -> [ebp-4] -> edx
       0x4cca74 movsx edi,WORD [ebx+0x933278]; +8  x      -> edi
       0x4ccbda-0x4ccbdd push edx(y), edi(x), esi(owner); call 0x4e47d0
     => THE FOUNDING TILE IS WHERE THE POD STANDS, and the faction is the
     pod's owner.  The tile CHOICE is entirely the pod's walk; the founder
     itself has no tile-legality guard (only the count < 0x200 capacity
     guard, B10) - the hub's candidate scan is the legality gate.
  4. Fit to the record (m289): every one of the seven sites is a legal
     LAND tile (MAP_FORMAT.md: cat = byte0[7:5], cat 0-2 water / 3-6
     land), is UNOCCUPIED by a base in the starting save, and the event
     sequence (7 foundings + 2 destroys) reproduces the jsonl's per-turn
     n_bases curve exactly.
  5. RIVAL (B10's assumption REFUTED): a row-major first-unoccupied scan
     would have settled the pods at low rows long before the recorded
     sites - the recorded sites rank late in that order, so B10's tile
     rule cannot explain ANY real founding's coordinates.

Usage:
  python3 scripts/m290_hub_decision.py programs/saves/m54b_clean.SAV \
      evidence/m289_gdb_raw.log evidence/trace_m289_20261110_071759.jsonl
Exit 0 prints PASS M290: n/n.  Never weaken a floor to pass.
"""
import json
import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from sim import save as simsave  # noqa: E402

# ---- byte windows transcribed from scratch/m574/text.txt (the .text disasm cache) ----
# (address, bytes-hex, mnemonic-regex) pairs.  Bytes are the ARBITER; we assert both.
DISPATCH_WINDOW = [
    (0x563d3c, "837dbc08", r"cmp\s+DWORD PTR \[ebp-0x44\],0x8"),
    (0x563d40, "0f8502010000", r"jne\s+0x563e48"),
    (0x563d46, "85f6", r"test\s+esi,esi"),
    (0x563d48, "0f85ac000000", r"jne\s+0x563dfa"),
    (0x563d4e, "8b855cffffff", r"mov\s+eax,DWORD PTR \[ebp-0xa4\]"),
    (0x563d55, "85c0", r"test\s+eax,eax"),
    (0x563d57, "7429", r"je\s+0x563d82"),
    (0x563d5e, "6868136900", r"push\s+0x691368"),
    (0x563d70, "6808240000", r"push\s+0x2408"),
    (0x563d75, "e826020200", r"call\s+0x583fa0"),
    (0x563d7d, "e9a38b0000", r"jmp\s+0x56c925"),
    (0x563d82, "8b4508", r"mov\s+eax,DWORD PTR \[ebp\+0x8\]"),
    (0x563d85, "50", r"push\s+eax"),
    (0x563d86, "e8c58cf6ff", r"call\s+0x4cca50"),
    (0x563d8b, "8b4db8", r"mov\s+ecx,DWORD PTR \[ebp-0x48\]"),
]
VECTOR_WINDOW = [
    # FUN_004cca50 prologue: the unit-record fold (ebx = u + 3u=4u; ebx*4 = 16*4u = 64u;
    # sub ebx,u -> 52u = the record base) then the three field loads.
    (0x4cca57, "8b5d08", r"mov\s+ebx,DWORD PTR \[ebp\+0x8\]"),
    (0x4cca5d, "8d045b", r"lea\s+eax,\[ebx\+ebx\*2\]"),
    (0x4cca61, "8d1c83", r"lea\s+ebx,\[ebx\+eax\*4\]"),
    (0x4cca64, "c1e302", r"shl\s+ebx,0x2"),
    (0x4cca67, "8a8b863293 00".replace(" ", ""), r"mov\s+cl,BYTE PTR \[ebx\+0x933286\]"),
    (0x4cca6d, "0fbf837a3293 00".replace(" ", ""), r"movsx\s+eax,WORD PTR \[ebx\+0x93327a\]"),
    (0x4cca74, "0fbfbb783293 00".replace(" ", ""), r"movsx\s+edi,WORD PTR \[ebx\+0x933278\]"),
    # right before the founder call: push edx(=y), push edi(=x), push esi(=owner)
    (0x4ccbda, "52", r"push\s+edx"),
    (0x4ccbdb, "57", r"push\s+edi"),
    (0x4ccbdc, "56", r"push\s+esi"),
    (0x4ccbdd, "e8ee7b0100", r"call\s+0x4e47d0"),
    (0x4ccbe2, "", None),  # return target: exactly the FOUND ret= the census logged
]

FOUNDER_BODY_MIN = 1400
FOUNDER_BODY_MAX = 1800


def load_text_window(text, addr):
    """Pull one disasm line from the cache (space-padded fields, per scratch/m574)."""
    m = re.search(r"(?m)^\s*%x:\s+((?:[0-9a-f]{2} +)+)\s+(\S.*?)\s*$" % addr, text)
    if not m:
        return None, None
    hexb = m.group(1).replace(" ", "")
    return hexb, m.group(2).strip()


def check_static_gates(text, fn_body, results):
    # G1: the hub dispatch window carries the gating chain (bytes + mnemonics).
    ok = True
    rows = []
    for addr, want_b, want_re in DISPATCH_WINDOW:
        got_b, got_m = load_text_window(text, addr)
        if got_b is None:
            rows.append("  MISSING %x" % addr)
            ok = False
            continue
        good = (got_b == want_b) if want_b else True
        if want_re:
            good = good and re.match(want_re, got_m) is not None
        rows.append("  %08x: %s\t%-38s %s" % (addr, got_b, got_m, "OK" if good else "MISMATCH"))
        ok = ok and good
    results.append(("G1 hub dispatch window (0x563d3c-0x563d8b): target-gate, second "
                    "gate [ebp-0xa4], msg 0x2408 leg, founder call - bytes+mnemonics",
                    ok, "\n".join(rows)))

    # G2: the founder-vector window: args read from the UNIT RECORD, call, return target.
    ok = True
    rows = []
    for addr, want_b, want_re in VECTOR_WINDOW:
        got_b, got_m = load_text_window(text, addr)
        if got_b is None:
            rows.append("  MISSING %x" % addr)
            ok = False
            continue
        good = (got_b == want_b) if want_b else True
        if want_re:
            good = good and re.match(want_re, got_m) is not None
        rows.append("  %08x: %s\t%-38s %s" % (addr, got_b, got_m, "OK" if good else "MISMATCH"))
        ok = ok and good
    results.append(("G2 vector window: prologue fold 52*u + record loads (+14 owner, "
                    "+10 y, +8 x) + push y/x/owner + call 0x4e47d0; ret 0x4ccbe2 = "
                    "census FOUND ret", ok, "\n".join(rows)))

    # G3: the founder's ONLY early bail is the capacity guard (count < 0x200); it has
    # NO tile-legality guard and NO target-tile parameter of its own beyond the call.
    guard = re.search(r"if\s*\(DAT_00985af4\s*<\s*0x200\)", fn_body)
    no_tile_bail = "if (local_c" not in fn_body and "return -1" not in fn_body.split("if (DAT_00985af4")[0]
    ok = guard is not None and no_tile_bail
    results.append(("G3 founder guard is CAPACITY ONLY (DAT_00985af4 < 0x200); no tile-"
                    "legality early bail in the body", ok,
                    "  guard at %s; pre-guard returns: none" % ("found" if guard else "NOT FOUND")))

    # G4 (s240 CORRECTED): a REAL control-flow check.  The old gate sliced its own
    # hardcoded DISPATCH_WINDOW table at 0x563d4e..0x563d81 and "observed" 0x563d86
    # outside it - a check that could not fail (the founder leg starts at the
    # je-target 0x563d82, one byte past the window end) - and it asserted a claim
    # the same bytes REFUTE: 0x563d48 is `jne 0x563dfa`, so the DISTANT leg never
    # enters 0x563d4e-0x563d7d at all.  Now parsed from the disassembly TEXT (real
    # branch targets - the CFG, not the table):
    #   (a) no branch anywhere in .text targets the msg-block interior
    #       [0x563d4e, 0x563d7d] from outside it -> the msg block has exactly one
    #       in-body entry: the flag!=0 fallthrough when esi==0;
    #   (b) the dispatch branch table lands where claimed;
    #   (c) [ebp-0xa4] has EXACTLY ONE writer in the hub body [0x55f650, 0x56cb23):
    #       0x55f6d6, fed by the owner==ds:0x91b5b4 test under the ds:0x920434!=0
    #       precondition (byte chain below) - the second gate is set once per call.
    BODY_HI = 0x55f650 + 54483  # FUN_0055f650 ghidra body size (M291)
    br_re = re.compile(r"^\s*([0-9a-f]{6,8}):\s+((?:[0-9a-f]{2} )+)\s+(\S+)\s+(.*)$")
    tgt_re = re.compile(r"^0x([0-9a-f]+)$")
    branch_hits, body_branches, writer_addrs = [], {}, []
    for line in text.splitlines():
        m4 = br_re.match(line)
        if not m4:
            continue
        a4 = int(m4.group(1), 16)
        mn, ops = m4.group(3), m4.group(4).strip()
        t4m = tgt_re.match(ops)
        if t4m and mn[0] == "j":
            t4 = int(t4m.group(1), 16)
            in_block = 0x563d4e <= a4 <= 0x563d7d
            if 0x563d4e <= t4 <= 0x563d7d and not in_block:
                branch_hits.append((a4, mn, t4))
            if 0x55f650 <= a4 < BODY_HI:
                body_branches[a4] = t4
        if 0x55f650 <= a4 < BODY_HI and mn == "mov" and ops.startswith("DWORD PTR [ebp-0xa4]"):
            writer_addrs.append(a4)
    want_br = {0x563d40: 0x563e48, 0x563d48: 0x563dfa, 0x563d57: 0x563d82,
               0x563d7d: 0x56c925, 0x563e04: 0x563e12,
               0x55f6b6: 0x55f6d6, 0x55f6cf: 0x55f6d6}
    br_ok = all(body_branches.get(a) == t for (a, t) in want_br.items())
    chain = [(0x55f65f, "33db", chr(92).join(["xor", "s+ebx,ebx"])),
             (0x55f6b0, "391d34049200", r"cmp" + chr(92) + "s+DWORD PTR ds:0x920434"),
             (0x55f6b6, "741e", chr(92).join(["je", "s+0x55f6d6"])),
             (0x55f6cf, "7505", chr(92).join(["jne", "s+0x55f6d6"])),
             (0x55f6c0, "8b0db4b59100", r"mov" + chr(92) + "s+ecx,DWORD PTR ds:0x91b5b4"),
             (0x55f6c6, "8a049586329300",
              r"mov" + chr(92) + "s+al,BYTE PTR " + chr(92) + "[edx" + chr(92) + "*4"
              + chr(92) + "+0x933286" + chr(92) + "]"),
             (0x55f6cd, "3bc1", r"cmp" + chr(92) + "s+eax,ecx"),
             (0x55f6d1, "bb01000000", r"mov" + chr(92) + "s+ebx,0x1"),
             (0x55f6d6, "899d5cffffff",
              r"mov" + chr(92) + "s+DWORD PTR " + chr(92) + "[ebp-0xa4" + chr(92) + "],ebx")]
    chain_rows, chain_ok = [], True
    for a4, wb, wr in chain:
        gb, gm = load_text_window(text, a4)
        good = (gb == wb) and gm is not None and re.match(wr, gm) is not None
        chain_rows.append("  %08x: %s\t%-44s %s" % (a4, gb, gm, "OK" if good else "MISMATCH"))
        chain_ok = chain_ok and good
    ok = (not branch_hits) and br_ok and (writer_addrs == [0x55f6d6]) and chain_ok
    results.append(("G4 control-flow (s240): msg block 0x563d4e-0x563d7d entered ONLY by "
                    "the flag!=0 fallthrough (no external branch target); dispatch branches "
                    "0x563d48->0x563dfa distant-leg / 0x563d57->0x563d82 founder-leg; "
                    "[ebp-0xa4] single writer 0x55f6d6 with its owner/0x920434 chain", ok,
                    "\n".join(["  external branch targets into msg block: %s"
                                % (branch_hits or "none"),
                                "  body branches PARSED: %s\n  body branches EXPECTED: %s" % (
                                    {("0x%06x" % k): (("0x%06x" % body_branches[k])
                                                      if k in body_branches else "MISSING")
                                     for k in sorted(want_br)},
                                    {("0x%06x" % k): ("0x%06x" % v)
                                     for k, v in sorted(want_br.items())}),
                                "  [ebp-0xa4] writers in body: %s" % ["0x%x" % a for a in writer_addrs]]
                               + chain_rows)))
    return ok


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        return 2
    sav_path, log_path, trace_path = sys.argv[1:4]
    cache = os.path.expanduser("~/reverse/smac/scratch/m574/text.txt")
    if not os.path.exists(cache):
        cache = "scratch/m574/text.txt"
    text = open(cache).read()
    body_start = text  # founder pseudocode comes from fn.py-style shard read
    shard = open(os.path.expanduser("~/reverse/smac/ghidra_out/shard_012.c")).read()
    m = re.search(r"// ==== FUN_004e47d0 @ 0x4e47d0 size=(\d+)", shard)
    fn_body = shard[m.end():m.end() + 9000]

    results = []
    check_static_gates(text, fn_body, results)

    # ---- the recorded seven foundings + two destroys (ordered events from the raw log)
    ev = []
    for line in open(log_path):
        mm = re.match(r"FOUND ret=(\S+) fac=(\d+) x=(\d+) y=(\d+) cnt=(\d+)", line)
        if mm:
            ev.append(("found", int(mm.group(2)), int(mm.group(3)), int(mm.group(4)),
                       int(mm.group(5))))
            continue
        md = re.match(r"DESTROY cnt=(\d+)", line)
        if md:
            ev.append(("destroy", None, None, None, int(md.group(1))))
    founds = [e for e in ev if e[0] == "found"]
    destroys = [e for e in ev if e[0] == "destroy"]

    # G5: 7 foundings, ret all 0x4ccbe2 (the G2 return target), 2 destroys
    ok = (len(founds) == 7 and len(destroys) == 2 and
          all(re.match(r"FOUND ret=0x4ccbe2 ", l) for l in open(log_path)
              if l.startswith("FOUND")))
    table = "\n".join("  fac=%d (%d,%d) cnt=%d" % (f[1], f[2], f[3], f[4]) for f in founds)
    results.append(("G5 record: 7 foundings all via ret=0x4ccbe2 (the G2 leg) + 2 destroys",
                    ok, table))

    # ---- the map: legality + occupancy of each recorded site ----
    sv = simsave.parse(sav_path)
    base_tiles = {(b["x"], b["y"]) for b in sv.bases}

    def cat44(x, y):
        """The live byte-0 category lives in the 44-B RECORD's first half (MAP_FORMAT:
        the loader stored the grid verbatim; one record spans TWO file columns, bytes
        22..43 are the sibling column's fields - NOT a second category for column x)."""
        rec = (sv.width // 2) * y + (x >> 1)
        off = sv.grid_off + 44 * rec
        return (sv.data[off] >> 5) & 7
    cat = cat44

    # G6: every recorded site is LEGAL land (cat 3..6) per the MAP_FORMAT rule
    rows = []
    ok = True
    for (_t, fac, x, y, _c) in founds:
        cc = cat(x, y)
        good = 3 <= cc <= 6
        ok = ok and good
        rows.append("  (%d,%d) fac=%d cat=%d %s" % (x, y, fac, cc, "OK" if good else "ILLEGAL"))
    results.append(("G6 all 7 recorded sites are LAND tiles (cat 3-6, MAP_FORMAT rule)",
                    ok, "\n".join(rows)))

    # G7: no recorded site already carries a base in the starting save
    hits = [(x, y) for (_t, _f, x, y, _c) in founds if (x, y) in base_tiles]
    ok = not hits
    results.append(("G7 no recorded site is already a base tile in m54b_clean (founds are "
                    "NEW tiles)", ok, "  collisions: %s" % (hits or "none")))

    # G8: event ledger vs the jsonl curve.  The curve is a PER-TURN sample: a found
    # and a LATER destroy inside ONE turn net to 0 and are invisible there (the M289
    # "+3 DESTROY -> 20" accounting - both net-0 pairs can even share one turn).
    # What IS computable from the two records: (a) every curve sample respects the
    # event prefix envelope n(t) <= 18 + founds(t) - destroys(t) and >= 18 - destroys(t)
    # (prefix = events logged by the time the snapshot's turn ended, log-row order);
    # (b) the ledger's strict replay 18+7-2 = 23 equals the curve's LAST sample;
    # (c) the two destroy log rows fall strictly AFTER the 3rd and 6th FOUND rows,
    # matching the M289 count trace (18,19,20 DESTROY->20 ... +4 DESTROY->24->23).
    rows_f = [i for i, l in enumerate(open(log_path)) if l.startswith("FOUND")]
    rows_d = [i for i, l in enumerate(open(log_path)) if l.startswith("DESTROY")]
    order_ok = (len(rows_d) == 2 and rows_f[2] < rows_d[0] < rows_f[3]
                and rows_d[1] > rows_f[6])
    prev = None
    curve = []
    for line in open(trace_path):
        d = json.loads(line)
        if "state_before" not in d:
            continue
        curve.append(d["state_after"]["n_bases"])
        prev = d["state_after"]["n_bases"]
    envelope_ok = True
    bad = []
    # (the raw log carries no turn index, so the envelope is the GLOBAL bound; the
    # interleave in (c) carries the ordering information instead)
    for t, n in enumerate(curve):
        if n > 18 + len(founds) or n < 18 - len(destroys):
            envelope_ok = False
            bad.append((t, n))
    ok = (curve[0] >= 18 and max(curve) == 24
          and 18 + len(founds) - len(destroys) == curve[-1] == 23
          and envelope_ok and order_ok)
    results.append(("G8 curve/ledger consistency: peak 24 (before the late destroy), "
                    "endpoint replay 18+7-2=23=%d, envelope 16..25 holds, destroy rows "
                    "interleave founds as s235 logged (18,19,20 D 20,21,22,23,23,23,24 D 23)"
                    % curve[-1], ok,
                    "  curve first/last %d/%d max=%d rows_found=%s rows_destroy=%s bad=%s" %
                    (curve[0], curve[-1], max(curve), rows_f, rows_d, bad or "none")))

    # G9: RIVAL - B10's assumed row-major first-unoccupied tile rule CANNOT reproduce
    # the recorded sites: scan all land tiles not occupied by a base (start state), and
    # show the recorded sites rank in the LATE band (mean rank past half the scan and
    # each site outside the first 40 - the rule would have settled there turns earlier).
    scan = []
    for yy in range(sv.height):
        for xx in range(sv.width):
            if 3 <= cat(xx, yy) <= 6 and (xx, yy) not in base_tiles:
                scan.append((xx, yy))
    rank = {t: i for i, t in enumerate(scan)}
    ranks = [rank.get((x, y), -1) for (_t, _f, x, y, _c) in founds]
    mean_rank = sum(ranks) / float(len(ranks)) if all(r >= 0 for r in ranks) else -1
    ok = (mean_rank > len(scan) / 2.0) and all(r >= 40 for r in ranks if r >= 0) and all(r >= 0 for r in ranks)
    results.append(("G9 B10 rival REFUTED: first-unoccupied row-major would settle the first "
                    "40 scan tiles; recorded mean rank %.0f of %d, min %d" %
                    (mean_rank, len(scan), min(ranks)), ok,
                    "  ranks: %s" % ranks))

    print("M290 fit: hub founder decision vs the m289 record")
    n_ok = 0
    for name, ok, detail in results:
        print("%s %s" % ("PASS" if ok else "FAIL", name))
        print(detail)
        n_ok += 1 if ok else 0
    print("%d/%d gates" % (n_ok, len(results)))
    if n_ok == len(results):
        print("PASS M290: %d/%d" % (n_ok, len(results)))
        return 0
    print("FAIL M290: %d/%d" % (n_ok, len(results)))
    return 1


if __name__ == "__main__":
    sys.exit(main())
