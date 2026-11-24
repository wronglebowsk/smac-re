"""sim.unitoracle - rung B32's RUN and its GATES (BUILD_SPINE §B32).

B31 scored "the queue head id is the bit that appeared" 0/6 on the game's own recorded run,
treating a negative head as a bulk id, and DECLARED the unit-id decoding unmodeled.  M349
answered that decode (`## M349`): head < 0 is the NEGATED UNIT TYPE, head >= 0 the facility
item id, -38 the sentinel; ONE mapper FUN_00507410 - (byte = id/8 truncating toward zero,
mask = 1<<(id&7)) - serves both legs over the SAME per-player record (0x95da9c + 304*p).

This rung attaches that decoder to B31's oracle and re-scores the head->bit rule PER LEG on
the recorded bytes, before asserting anything:

  * the six changed boundaries of the recorded run, each with BOTH heads (the before-sample
    head, which is the completed item, and the after-sample head, the rival shape);
  * the mapper bit of each head, printed beside the gains and losses the trace actually shows;
  * the unit leg against the facility leg: 4/4 unit heads gain exactly the mapper bit, 0/2
    facility-range heads do - the same OR site, two different outcomes on the record.

The write is replayed: the before window OR the mapper mask at the mapper byte is compared to
the recorded after window at every unit boundary, so the stamp is executed, not described.
Rivals (the after head; a swapped byte/mask orientation; the raw head as the bit; the facility
stamp) are scored on the same printed numbers and must fail.

DECLARED UNMODELED: WHY a facility-range head does not stamp while its unit twin does (the
facility path's own branch to the shared OR is not walked here); which recorded loss is a
raze/sale vs a record-identity change.

Zero box, zero /proc, zero gdb.
"""
import hashlib
import importlib.util
import os
import struct
import sys

from . import facoracle as fa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACE = fa.TRACE
HEAD_OFF = fa.HEAD_OFF
FBASE = 0x8c            # the per-record item bitmap (B30 pinned +0x8c..+0x8f; ids 0..63 = 8 bytes)
FB = 8
SENTINEL = -38
BIG = 0x40              # the facility leg's item<0x40 gate (M349 G2)

# Pinned on the first real run (s328); a trace, decode or arithmetic drift reddens G10.
ROWS_ANCHOR = "e6875c63c8c2f911"
SCORE_ANCHOR = "59b0b5e3647555b7"
LEG_ANCHOR = "26d1c63c2861b182"
MAP_ANCHOR = "da981620c0e3ef18"

# The mapper rows G5 pins, in TWO domains: the ITEM domain the measured path passes
# (-head for a unit, head for a facility) and the RAW domain M349's signed-division rows use.
# The first five are the recorded boundaries' decoded items; the last two are M349's own pins.
MAP_ROWS = ((2, 0, 4), (8, 1, 1), (3, 0, 8), (6, 0, 64), (321, 40, 2))
MAP_NEG = ((-3, 0, 32), (-8, -1, 1))


def _sha(rows):
    h = hashlib.sha256()
    for r in rows:
        h.update(repr(r).encode("utf-8"))
    return h.hexdigest()[:16]


# --- the laws, as code ----------------------------------------------------------------
def trunc8(item):
    """Signed divide by 8 truncating toward zero (FUN_00507410's `sar`/add pair)."""
    return item // 8 if item >= 0 else -((-item) // 8)


def mapper(item):
    """FUN_00507410: (byte, mask).  The same form for both legs (M349 G9)."""
    return trunc8(item), 1 << (item & 7)


def mapper_swapped(item):
    """RIVAL orientation: byte = id&7, mask = 1<<(id>>3)."""
    return item & 7, 1 << (item >> 3) if item >= 0 else 0


def decode(head):
    """The decode block FUN_004ef6d0 @0x4ef88b: (kind, item)."""
    if head == SENTINEL:
        return ("SENTINEL", None)
    if head < 0:
        return ("UNIT", -head)
    if head < BIG:
        return ("FACILITY", head)
    return ("BIGITEM", head)


def head_bit(head):
    """(kind, item, byte, bit) or (kind, item, byte, None) when the byte is off the map."""
    kind, item = decode(head)
    if item is None:
        return kind, item, None, None
    by, mask = mapper(item)
    if by < 0 or by >= FB:
        return kind, item, by, None
    return kind, item, by, by * 8 + (mask.bit_length() - 1)


def m349_table():
    """Import the M349 acceptance module (its UNIVERSE/decode); it is `__main__`-guarded."""
    path = os.path.join(ROOT, "scripts", "m349_unit_id.py")
    spec = importlib.util.spec_from_file_location("m349_unit_id_b32", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --- the measurement ------------------------------------------------------------------
def _record(samples, si, key):
    for i, n, rec in samples[si][2]:
        if (i, n) == key:
            return rec
    return None


def measure(samples=None):
    """One row per recorded bitmap change: both heads, both decodes, both windows."""
    samples = fa.load_trace() if samples is None else samples
    rows = []
    for r in fa.deltas(samples):
        si, ev, rr, idx, name, pbits, cbits, gain, loss, h, pend, st, ph = r
        key = (idx, name)
        before, after = _record(samples, si - 1, key), _record(samples, si, key)
        assert before is not None and after is not None, key
        bh = struct.unpack_from("<i", before, HEAD_OFF)[0]
        ah = struct.unpack_from("<i", after, HEAD_OFF)[0]
        kb, ib, byb, bitb = head_bit(bh)
        ka, ia, bya, bita = head_bit(ah)
        rows.append((si, rr, idx, name, bh, ah, kb, ib, byb, bitb, ka, ia, bya, bita,
                     tuple(sorted(gain)), tuple(sorted(loss)),
                     before[FBASE:FBASE + FB].hex(), after[FBASE:FBASE + FB].hex()))
    return rows


def score(rows, head_col=4):
    """Score `the head's mapper bit is a bit that appeared` on the recorded gains."""
    out = []
    for r in rows:
        si, rr, idx, name = r[0], r[1], r[2], r[3]
        kind, item, by, bit = r[6:10] if head_col == 4 else r[10:14]
        gains = r[14]
        out.append((si, idx, kind, r[head_col], item, by, bit,
                    bit is not None and bit in gains))
    return out


def bulk_score(rows):
    """B31's rule: the raw head id is the bit that appeared (no decode)."""
    return [(r[0], r[2], r[4], r[4] in r[14] and 0 <= r[4] < FB * 8) for r in rows]


def replay(rows):
    """OR the mapper mask at the mapper byte in the BEFORE window; compare to the record."""
    out = []
    for r in rows:
        before = bytes.fromhex(r[16])
        kind, item, by, bit = r[6], r[7], r[8], r[9]
        if by is None or bit is None or by < 0 or by >= FB:
            out.append((r[0], r[2], kind, item, "refused", None, None))
            continue
        pred = bytearray(before)
        pred[by] |= 1 << (item & 7)
        diff = [k for k in range(FB) if pred[k] != before[k]]
        out.append((r[0], r[2], kind, item, pred.hex(), r[17], tuple(diff)))
    return out


# --- output ---------------------------------------------------------------------------
GATES = []


def p(line=""):
    print(line)


def g(ok, label, detail=""):
    GATES.append((label.split()[0], bool(ok)))
    print(("ok   %s%s" if ok else "FAIL %s%s") % (label, ("  " + detail) if detail else ""))


def main(argv=None):
    del argv
    GATES.clear()
    samples = fa.load_trace()
    rows = measure(samples)
    sc_before = score(rows, 4)
    sc_after = score(rows, 5)
    bulk = bulk_score(rows)
    rep = replay(rows)
    tbl = m349_table()

    p("B32 - the unit leg of the completion law, scored on the recorded run")
    p("trace: %s" % os.path.relpath(TRACE, ROOT))
    p("")
    p("TABLE 1  the six changed boundaries, both heads, both decodes")
    for r in rows:
        p("  s%-2d r%-2d base %-2d %-24s headB=%-5d headA=%-5d  B:%-8s item=%-4s by=%-3s bit=%-4s"
          % (r[0], r[1], r[2], (r[3] or "")[:24], r[4], r[5], r[6], r[7], r[8], r[9]))
        p("      A:%-8s item=%-4s by=%-3s bit=%-4s  gain=%-6s loss=%-6s  win %s -> %s"
          % (r[10], r[11], r[12], r[13], list(r[14]), list(r[15]), r[16], r[17]))

    p("")
    p("TABLE 2  the head->bit rule, scored per leg on the before-sample head")
    for si, idx, kind, head, item, by, bit, hit in sc_before:
        p("  base %-2d %-9s head=%-5d item=%-4s mapper=(%s,%s) bit=%-4s gain_has_bit=%s"
          % (idx, kind, head, item, by, (1 << (item & 7)) if item is not None else "-", bit, hit))
    unit = [s for s in sc_before if s[2] == "UNIT"]
    fac = [s for s in sc_before if s[2] in ("FACILITY", "BIGITEM")]
    uhits = sum(1 for s in unit if s[7])
    fhits = sum(1 for s in fac if s[7])
    p("  unit %d/%d   facility-range %d/%d   B31 bulk rule %d/%d"
      % (uhits, len(unit), fhits, len(fac), sum(1 for b in bulk if b[3]), len(bulk)))

    p("")
    p("TABLE 3  rivals, scored on the same rows")
    ahits = sum(1 for s in sc_after if s[7])
    sw = sw_n = 0
    for r, s in zip(rows, sc_before):
        item = s[4]
        if item is None or s[6] is None:
            continue
        sw_n += 1                      # rows the swapped orientation CAN score (321 is off-map)
        sby, smask = mapper_swapped(item)
        if 0 <= sby < FB and sby * 8 + (smask.bit_length() - 1) in r[14]:
            sw += 1
    p("  R1 the AFTER-sample head stamps        -> %d/%d matches" % (ahits, len(sc_after)))
    p("  R2 swapped orientation (byte=id&7)     -> %d/%d matches (%d off-map row excluded)"
      % (sw, sw_n, len(sc_before) - sw_n))
    p("  R3 the raw head id is the bit (B31)    -> %d/%d matches"
      % (sum(1 for b in bulk if b[3]), len(bulk)))
    p("  R4 a facility-range head stamps too    -> prediction %d/%d, recorded %d/%d"
      % (len(fac), len(fac), fhits, len(fac)))

    p("")
    p("TABLE 4  the bitmap write, replayed from the before window")
    for si, idx, kind, item, pred, got, diff in rep:
        p("  base %-2d %-9s item=%-4s pred=%-18s recorded=%-18s changed_bytes=%s"
          % (idx, kind, item, pred, got, list(diff) if diff else "-"))
    unit_rep = [x for x, s in zip(rep, sc_before) if s[2] == "UNIT"]
    exact = sum(1 for x in unit_rep if x[4] not in (None, "refused") and x[4] == x[5])
    only_byte = sum(1 for x in unit_rep if x[6] is not None and len(x[6]) == 1)
    refusals = [x for x in rep if x[4] == "refused"]

    p("")
    p("GATES")
    d_rows, d_sc, d_leg = _sha(rows), _sha(sc_before), _sha((uhits, len(unit), fhits, len(fac)))
    d_map = _sha([(it,) + mapper(it) for it, _b, _m in MAP_ROWS + MAP_NEG])
    heads = [r[4] for r in rows]
    kinds = [r[6] for r in rows]

    after_heads = [r[5] for r in rows]
    tie = all(r[6] == decode(r[4])[0] and r[10] == decode(r[5])[0]
              and (r[8] is None or r[8] == mapper(r[7])[0]) for r in rows)
    g(len(rows) == 6 and len(samples) == 20 and all(r[16] != r[17] for r in rows)
      and all(r[4] != r[5] for r in rows) and tie
      and after_heads == [128, -6, -24, 133, -2, -8],
      "G1 the six changed boundaries are READ with BOTH heads, each decoded and mapped",
      "rows=%d samples=%d before=%s after=%s digest=%s"
      % (len(rows), len(samples), heads, after_heads, d_rows))
    same = all(tbl.decode(h)[:2] == decode(h) for h in tbl.UNIVERSE)
    g(same and len(tbl.UNIVERSE) == 30 and heads == [321, -2, -8, 2, -3, -6]
      and kinds.count("UNIT") == 4 and kinds.count("FACILITY") == 1 and kinds.count("BIGITEM") == 1,
      "G2 the decode IS M349's: 30-row universe equal, heads [321,-2,-8,2,-3,-6] = 4 UNIT / 1 FAC / 1 BIG",
      "universe=%d heads=%s" % (len(tbl.UNIVERSE), heads))
    g(uhits == len(unit) == 4 and fhits == 0 and len(fac) == 2
      and sum(1 for b in bulk if b[3]) == 0,
      "G3 scored PER LEG: %d/%d unit heads gain the mapper bit, %d/%d facility-range heads do; "
      "B31's bulk rule 0/%d" % (uhits, len(unit), fhits, len(fac), len(bulk)))
    g(ahits == 0 and len(sc_after) == 6,
      "G4 the AFTER-sample head is the rival: 0/6 - the stamp reads the head BEFORE the pop",
      "after_head_hits=%d/%d" % (ahits, len(sc_after)))
    map_ok = (all(mapper(it) == (ex_by, 1 << (it & 7)) == (ex_by, ex_mask)
                  for it, ex_by, ex_mask in MAP_ROWS)
              and all(mapper(it) == (ex_by, 1 << (it & 7)) == (ex_by, ex_mask)
                      for it, ex_by, ex_mask in MAP_NEG))
    g(map_ok and sw == 0,
      "G5 the mapper is the DERIVED form on %d item rows + %d signed-division rows; the swapped "
      "orientation fails %d/%d" % (len(MAP_ROWS), len(MAP_NEG), sw, sw_n),
      "digest=%s" % d_map)
    g(exact == 4 and only_byte == 4,
      "G6 the write REPLAYS: before OR mask == the recorded after window at %d/4 unit boundaries, "
      "only the mapper byte moves" % exact)
    v = [x for x in rep if x[2] == "FACILITY"]
    bad_v = sum(1 for x in v if x[4] != x[5])
    g(len(refusals) == 1 and refusals[0][3] == 321 and refusals[0][2] == "BIGITEM"
      and head_bit(321)[2] == 40
      and v and v[0][4] == "0400000800000000" and v[0][5] == "1000000000000000"
      and bad_v == len(v) == 1,
      "G7 the facility side is a counter-result: 321 maps to byte 40 (off the eight-byte map, "
      "1 refusal) and the facility stamp misses the recorded bytes at %d/%d" % (bad_v, len(v)))
    losses = sum(len(r[15]) for r in rows)
    uloss = sum(1 for r in rows if r[6] == "UNIT" and r[15])
    nonunit = [r for r in rows if r[6] != "UNIT"]
    one_each = len(nonunit) == 2 and all(len(r[15]) == 1 for r in nonunit)
    g(losses == 2 and uloss == 0 and one_each
      and sorted(r[15][0] for r in nonunit) == [1, 27]
      and all(r[14] == (r[9],) for r in rows if r[6] == "UNIT"),
      "G8 the two recorded losses sit one per non-unit row (ids 1 and 27); every unit row's gain "
      "set is exactly its mapper bit", "nonunit_losses=%s" % [list(r[15]) for r in nonunit])
    rows2 = measure(samples)
    g(_sha(rows2) == d_rows and _sha(score(rows2, 4)) == d_sc,
      "G9 two in-process passes give identical row and score digests")
    g(d_rows == ROWS_ANCHOR and d_sc == SCORE_ANCHOR and d_leg == LEG_ANCHOR
      and d_map == MAP_ANCHOR,
      "G10 every anchor is pinned to a literal",
      "rows=%s score=%s leg=%s map=%s" % (d_rows, d_sc, d_leg, d_map))

    failed = [lab for lab, ok in GATES if not ok]
    print("")
    print("DIGEST %s universe=%d gates=%d" % (d_rows, len(rows), len(GATES)))
    if failed:
        print("FAIL B32: %d/%d gates" % (len(GATES) - len(failed), len(GATES)))
        for lab in failed:
            print("  red: %s" % lab)
        return 1
    print("PASS B32: %d/%d gates" % (len(GATES), len(GATES)))
    print("ANCHORS rows=%s score=%s leg=%s map=%s" % (d_rows, d_sc, d_leg, d_map))
    return 0


class _Tee:
    """`--evidence` writes the exact stdout it prints to evidence/b32_unitoracle.txt."""

    def __init__(self, *fhs):
        self.fhs = fhs

    def write(self, s):
        for f in self.fhs:
            f.write(s)

    def flush(self):
        for f in self.fhs:
            f.flush()


if __name__ == "__main__":
    _argv = sys.argv[1:]
    if "--evidence" in _argv:
        _path = os.path.join(ROOT, "evidence", "b32_unitoracle.txt")
        with open(_path, "w", encoding="utf-8") as _fh:
            _old = sys.stdout
            sys.stdout = _Tee(_old, _fh)
            try:
                _rc = main([])
            finally:
                sys.stdout = _old
        sys.exit(_rc)
    sys.exit(main(_argv))
