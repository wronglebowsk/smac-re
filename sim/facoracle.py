"""sim.facoracle - rung B31's RUN and its GATES (BUILD_SPINE §B31).

B30 ASSUMED that a paid queue item becomes a facility the base HAS (the reader's inverse
setter, one bitmap byte).  The game's OWN 10-boundary run is the only recorded oracle for
that law: `evidence/trace_m56_build_20261026_145157.jsonl` carries the full 304-B base
record hex at every `round_before`/`round_after` sample, so the `+0x8c..+0x8f` bitmap can be
decoded from the RECORDED BYTES at each boundary, together with the queue head `+0x50`,
the pending count `+0x4c` and the accumulator `+0x40`.

This rung makes that oracle executable and then SCORES the completion hypothesis against
it - it does not assume the answer.  Three things are measured and printed before anything
is asserted:

  * every bit GAIN and LOSS per base per boundary in the recorded run (the bitmap is NOT
    monotonic: a loss exists, and a completion can only ever gain);
  * whether the recorded queue HEAD is the id that was gained (it is a unit-encoded id -
    negative, or a value far outside the 4-byte bitmap window - in every gain, so the
    "head stamps the bit" rule scores 0 of N on the recorded numbers);
  * the one recorded boundary whose full transaction B23 already parity-verified (Korolev
    Center r0: st 8 + add 1 >= price 9 -> PAY, spend to 0, one pop, pending visible at the
    NEXT before-sample) replayed here WITH the stamp attached: the head id 2 is INSIDE the
    facility window, yet the recorded bitmap does NOT move - the negative is not vacuous.

The oracle's bitmaps are then driven through `sim.savewriter` into the save's own record
(an arbitrary target bitmap, including a LOSS, which the OR-only setter cannot express) and
read back from the RELOADED image, so the oracle is executable on a container, not prose.

DECLARED UNMODELED: the unit-id decoding that would map a queue head onto a bitmap id
(M68/M69's NEG_TYPE mapping rule is OPEN - this rung measures the mismatch, it does not
resolve it); the price/income law is B23's recorded fixture (price 9, add 1); which of the
recorded losses is a raze/sale vs a record-identity change.

Zero box, zero /proc, zero gdb.
"""
import hashlib
import json
import os
import struct
import sys

from . import save as so
from . import savewriter as sow

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAV = os.path.join(ROOT, "programs", "saves", "m54b_clean.SAV")
TRACE = os.path.join(ROOT, "evidence", "trace_m56_build_20261026_145157.jsonl")

FAC_OFF = 0x8c          # the four-byte completed-facility window (sim.base.FAC_BYTES)
FAC_BYTES = 4
HEAD_OFF = 0x50         # slot 0 (the head) dword (M285 live read)
PEND_OFF = 0x4c         # pending count (M285)
ST_OFF = 0x40           # the accumulated-minerals accumulator (B23's `st`)
ITEM_LO, ITEM_HI = 1, 31   # the pinned window B30 set/refused in
PRICE = 9               # recorded per-base price (M58/M72) - B23's parity-verified fixture
ADD = 1                 # the recorded per-round addition at Korolev r0 (B23)

# Pinned on the first real run (s324); G7 asserts the run still reproduces them, so a drift
# in the trace, the bitmap decode or the transaction arithmetic reddens a gate.
ROWS_ANCHOR = "ce7688c0cb3b5f9d"
ORACLE_ANCHOR = "7afda4dd49566fb4"
SCORE_ANCHOR = "9a4f2c466f3d18b7"
IMG_SHA = "fb0bc0caa186b766"


def _sha(rows):
    h = hashlib.sha256()
    for r in rows:
        h.update(repr(r).encode("utf-8"))
    return h.hexdigest()[:16]


def load_trace():
    """The recorded samples in file order: (event, r, [(idx, name, record_bytes)])."""
    out = []
    with open(TRACE, encoding="utf-8") as fh:
        for ln in fh:
            e = json.loads(ln)
            if e.get("event") not in ("round_before", "round_after"):
                continue
            bases = [(b["idx"], b["name"], bytes.fromhex(b["hex"]))
                     for b in e["snap"]["bases"]]
            out.append((e["event"], e["r"], bases))
    return out


def bits_of(rec):
    """The facility ids of a 304-B base record, decoded from its own +0x8c bytes."""
    return {by * 8 + bit for by in range(FAC_BYTES) for bit in range(8)
            if rec[FAC_OFF + by] >> bit & 1}


def head_of(rec):
    return struct.unpack_from("<i", rec, HEAD_OFF)[0]


def pend_of(rec):
    return struct.unpack_from("<i", rec, PEND_OFF)[0]


def st_of(rec):
    return struct.unpack_from("<i", rec, ST_OFF)[0]


def deltas(samples):
    """Every consecutive-sample bitmap change, keyed by (idx, name).

    A base is tracked by (idx, name): the founded bases are appended, so a key that first
    appears mid-run has no predecessor and contributes no delta (counted, not hidden)."""
    rows = []
    prev = {}
    for si, (ev, r, bases) in enumerate(samples):
        for idx, name, rec in bases:
            key = (idx, name)
            cur = bits_of(rec)
            if key in prev:
                p, ph = prev[key]
                gained, lost = sorted(cur - p), sorted(p - cur)
                if gained or lost:
                    rows.append((si, ev, r, idx, name, sorted(p), sorted(cur),
                                 gained, lost, head_of(rec), pend_of(rec), st_of(rec), ph))
            prev[key] = (cur, head_of(rec))
    return rows


# --- the transaction leg (B23's parity-verified arithmetic, with the stamp attached) --------
def transaction(rec, price=PRICE, add=ADD, stamp=True, order="spend-stamp-pop"):
    """Execute the completion transaction on a container record.

    Returns (new_rec, log).  The measured order is M344's: SPEND (`sub esi,edi` @0x4f0ca4)
    then STAMP (`or BYTE PTR [eax],cl` @0x4f0ec0) then POP (0x86 B later, `call 0x4ef5d0`).
    `stamp=False` is the recorded-negative control; `order='pop-first'` is the rival that
    reads the head AFTER the pop and therefore stamps the NEXT item.
    """
    out = bytearray(rec)
    log = []
    head = struct.unpack_from("<i", out, HEAD_OFF)[0]
    pend = struct.unpack_from("<i", out, PEND_OFF)[0]
    st = struct.unpack_from("<i", out, ST_OFF)[0]
    if st + add < price:
        log.append(("bail", head, st))
        return bytes(out), log
    # POP is a slot shift + pending--, modelled here so pop-first can be scored.
    def pop():
        nonlocal pend
        slots = list(struct.unpack_from("<10i", out, HEAD_OFF + 4))     # slots[1..9]
        head_now = struct.unpack_from("<i", out, HEAD_OFF)[0]
        for k in range(len(slots)):
            struct.pack_into("<i", out, HEAD_OFF + 4 * k, slots[k])
        if pend > 0:
            pend -= 1
        struct.pack_into("<i", out, PEND_OFF, pend)
        return head_now

    def do_stamp(item):
        if not 0 <= item < FAC_BYTES * 8:
            log.append(("refuse", item))
            return
        out[FAC_OFF + (item >> 3)] |= 1 << (item & 7)

    def spend():
        nonlocal st
        st = st + add - price
        struct.pack_into("<i", out, ST_OFF, st)

    if order == "pop-first":
        popped = pop()
        log.append(("pop", popped))
        if stamp:
            # the rival reads the head AFTER the pop - the NEXT item, not the completed one
            do_stamp(struct.unpack_from("<i", out, HEAD_OFF)[0])
            log.append(("stamp", struct.unpack_from("<i", out, HEAD_OFF)[0]))
        spend()
        log.append(("spend", st))
    else:
        spend()
        log.append(("spend", st))
        if stamp:
            do_stamp(head)
            log.append(("stamp", head))
        popped = pop()
        log.append(("pop", popped))
    return bytes(out), log


# --- the writer leg ----------------------------------------------------------------------
def apply_bitmap(idx, target_bits, sav=SAV):
    """Carry an ARBITRARY bitmap (gains AND losses) into the container's own record.

    The override list is B30's shape: every other record is the IDENTITY (emitted verbatim),
    the target is re-composed from its own fields, and the bitmap arrives as byte-granular
    `base_writes` - the only writer hook that can express a byte field (B30)."""
    sv = so.parse(sav)
    pos = [k for k, b in enumerate(sv.bases) if b["i"] == idx]
    if not pos:
        raise AssertionError("no base with i=%r in %s" % (idx, sav))
    pos = pos[0]
    b = sv.bases[pos]
    raw = sv.data[b["off"]:b["off"] + so.BASE_LEN]
    want = bytearray(FAC_BYTES)
    for item in target_bits:
        want[item >> 3] |= 1 << (item & 7)
    writes = [(pos, FAC_OFF + by, want[by]) for by in range(FAC_BYTES)
              if want[by] != raw[FAC_OFF + by]]
    ov = [{"identity": True} for _ in range(sv.n_bases)]
    ov[pos] = {"x": b["x"], "y": b["y"], "own4": b["own4"], "fac": b["fac"]}
    return sv, b, raw, writes, ov


def main(argv=None):
    samples = load_trace()
    rows = deltas(samples)
    gates = []
    printed = []

    def p(line):
        printed.append(line)
        print(line)

    def g(label, ok, detail=""):
        gates.append((label, bool(ok), detail))
        print("%s %s%s" % ("ok  " if ok else "FAIL", label, ("  " + detail) if detail else ""))
        return ok

    # ---- G1: the oracle is READ out of the recorded bytes --------------------------------
    n_before = sum(1 for s in samples if s[0] == "round_before")
    n_after = sum(1 for s in samples if s[0] == "round_after")
    per_sample = sorted({len(s[2]) for s in samples})
    oracle_rows = [(si, ev, r, idx, name, tuple(sorted(bits_of(rec))))
                   for si, (ev, r, bases) in enumerate(samples) for idx, name, rec in bases]
    o_dig = _sha(oracle_rows)
    p("G1 ORACLE READ FROM THE RECORDED BYTES")
    p("  samples=%d (before=%d after=%d) bases/sample=%s records=%d bitmap bytes=%d"
      % (len(samples), n_before, n_after, per_sample, len(oracle_rows), FAC_BYTES))
    p("  oracle digest=%s  first=%s  last=%s" % (o_dig, oracle_rows[0][:5], oracle_rows[-1][:5]))
    g("G1 recorded run decoded: 10 before + 10 after samples, %d base-records, one bitmap each"
      % len(oracle_rows),
      len(samples) == 20 and n_before == 10 and n_after == 10 and len(oracle_rows) > 300,
      "bases/sample=%s" % per_sample)

    # ---- G2: every bit change enumerated (the bitmap is NOT monotonic) -------------------
    gains = [(r_, i) for r_ in rows for i in r_[7]]
    losses = [(r_, i) for r_ in rows for i in r_[8]]
    p("")
    p("G2 BIT CHANGES IN THE RECORDED RUN (gain = completion can explain, loss = it cannot)")
    for si, ev, r, idx, name, pbits, cbits, gained, lost, hd, pd, st, ph in rows:
        p("  sample %2d %-12s r%d base %2d %-22s head=%-5d pend=%d st=%-3d gained=%-8s lost=%s"
          % (si, ev, r, idx, name[:22], hd, pd, st, gained, lost))
    d_dig = _sha(rows)
    p("  gains=%d losses=%d rows=%d digest=%s" % (len(gains), len(losses), len(rows), d_dig))
    # every changed sample's symmetric difference is fully accounted by the two lists
    acct = all(len(gained) + len(lost) ==
               len(set(cur) ^ set(prev)) for _s, _e, _r, _i, _n, prev, cur, gained, lost,
               _h, _p, _st, _ph in rows)
    g("G2 the recorded bitmaps are NOT monotonic: %d gains and %d losses at %d changed samples, "
      "every symmetric difference fully accounted" % (len(gains), len(losses), len(rows)),
      len(gains) >= 1 and len(losses) >= 1 and len(rows) >= 2 and acct,
      "digest=%s" % d_dig)
    every_id_in_window = all(0 <= i < FAC_BYTES * 8 for _r, i in gains + losses)
    g("G2b every changed id lies inside the four-byte window", every_id_in_window)

    # ---- G3: the head-stamps-the-bit rule SCORED against the recorded run ---------------
    score = []
    for r_ in rows:
        si, ev, r, idx, name, pbits, cbits, gained, lost, hd, pd, st, ph = r_
        for item in gained:
            score.append((si, idx, name, ph, item, ph == item,
                          ph < 0 or ph >= FAC_BYTES * 8))
    hits = sum(1 for s in score if s[5])
    outside = sum(1 for s in score if s[6])
    p("")
    p("G3 THE RULE 'the queue head id is the bit that appeared' SCORED")
    for si, idx, name, hd, item, ok, outw in score:
        p("  sample %2d base %2d %-22s head=%-5d gained_bit=%-3d match=%s head_outside_window=%s"
          % (si, idx, name[:22], hd, item, ok, outw))
    s_dig = _sha(score)
    p("  matches=%d/%d heads_outside_window=%d digest=%s" % (hits, len(score), outside, s_dig))
    inwin = sum(1 for s_ in score if not s_[6])
    g("G3 the head->bit rule FAILS on the recorded numbers: %d/%d matches; %d heads are "
      "unit-encoded and %d in-window head(s) did not stamp" % (hits, len(score), outside, inwin),
      len(score) > 0 and hits == 0 and outside > 0 and inwin > 0, "digest=%s" % s_dig)

    # ---- G4: the recorded transaction, replayed WITH the stamp attached -----------------
    kor = None
    for si, (ev, r, bases) in enumerate(samples):
        for idx, name, rec in bases:
            if "Korolev" in (name or ""):
                kor = (si, ev, r, idx, rec)
                break
        if kor:
            break
    assert kor, "Korolev Center not in the recorded run"
    k_si, k_ev, k_r, k_idx, k_rec = kor
    after = None
    for si, (ev, r, bases) in enumerate(samples):
        if si > k_si:
            for idx, name, rec in bases:
                if "Korolev" in (name or ""):
                    after = (si, ev, r, idx, rec)
                    break
        if after:
            break
    k_st0, k_head, k_pend = st_of(k_rec), head_of(k_rec), pend_of(k_rec)
    k_new, k_log = transaction(k_rec, stamp=False)
    k_new_stamp, k_log_s = transaction(k_rec, stamp=True)
    k_rival, k_log_r = transaction(k_rec, stamp=True, order="pop-first")
    p("")
    p("G4 THE RECORDED TRANSACTION, REPLAYED WITH THE STAMP ATTACHED (Korolev Center)")
    p("  before: st=%d head=%d pend=%d bits=%s" % (k_st0, k_head, k_pend, sorted(bits_of(k_rec))))
    p("  no-stamp log %s -> st=%d bits=%s" % (k_log, st_of(k_new), sorted(bits_of(k_new))))
    p("  stamp     log %s -> st=%d bits=%s" % (k_log_s, st_of(k_new_stamp), sorted(bits_of(k_new_stamp))))
    p("  pop-first log %s -> st=%d bits=%s" % (k_log_r, st_of(k_rival), sorted(bits_of(k_rival))))
    p("  recorded next sample: %s r%d st=%d pend=%d bits=%s"
      % ((after[1], after[2], st_of(after[4]), pend_of(after[4]), sorted(bits_of(after[4])))
         if after else ("-", -1, -1, -1, [])))
    head_in_window = 0 <= k_head < FAC_BYTES * 8
    no_stamp_matches = (st_of(k_new) == 0 and after is not None and st_of(after[4]) == 0)
    stamp_moves_bit = bits_of(k_new_stamp) != bits_of(k_rec)
    recorded_flat = after is not None and bits_of(after[4]) == bits_of(k_rec)
    g("G4a the spend is B23's parity-verified arithmetic: st %d + %d - %d = %d == the "
      "recorded after %s" % (k_st0, ADD, PRICE, st_of(k_new), st_of(after[4]) if after else "-"),
      no_stamp_matches)
    g("G4b the head %d is INSIDE the facility window, so the negative is not vacuous"
      % k_head, head_in_window)
    g("G4c the recorded bitmap does NOT move at this boundary (bits stay %s), so a stamp here "
      "FAILS the recorded bytes" % sorted(bits_of(k_rec)),
      recorded_flat and stamp_moves_bit)
    deep = bytearray(k_rec)
    struct.pack_into("<i", deep, PEND_OFF, 2)
    for k in range(10):
        struct.pack_into("<i", deep, HEAD_OFF + 4 * k, [2, 6, 2, 2, 2, 2, 2, 2, 2, 0][k])
    d_ok, d_log = transaction(bytes(deep), stamp=True)
    d_rv, d_log_r = transaction(bytes(deep), stamp=True, order="pop-first")
    p("  2-deep fixture (pending=2, slots [2,6,..], declared): order-first %s -> %s ; pop-first "
      "%s -> %s" % (d_log, sorted(bits_of(d_ok) - bits_of(bytes(deep))),
                    d_log_r, sorted(bits_of(d_rv) - bits_of(bytes(deep)))))
    g("G4e the NO-STAMP replay leaves the recorded bitmap UNCHANGED (the recorded negative)",
      bits_of(k_new) == bits_of(k_rec) and st_of(k_new) == 0)
    g("G4d pop-first stamps the NEXT item (6) and misses the head (2)",
      sorted(bits_of(d_ok) - bits_of(bytes(deep))) == [2]
      and sorted(bits_of(d_rv) - bits_of(bytes(deep))) == [6])

    # ---- G5: the oracle's arbitrary bitmap carried through the WRITER --------------------
    sv, b, raw, writes, ov = apply_bitmap(0, {1, 4})
    img = sow.build_image(sv, bases_override=ov, base_writes=writes)
    blob = getattr(img, "data", img)
    tmp = os.path.join(ROOT, "scratch", "b31_oracle.SAV")
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    with open(tmp, "wb") as fh:
        fh.write(blob)
    re_sv = so.parse(tmp)
    rb = [x for x in re_sv.bases if x["i"] == 0][0]
    rrec = re_sv.data[rb["off"]:rb["off"] + so.BASE_LEN]
    diff = [k for k in range(len(raw)) if raw[k] != rrec[k]]
    others_same = all(raw_other == re_sv.data[o["off"]:o["off"] + so.BASE_LEN]
                      for raw_other, o in ((sv.data[o["off"]:o["off"] + so.BASE_LEN], o)
                                           for o in sv.bases if o["i"] != 0))
    idn_blob = sow.build_image(sv, bases_override=[{"identity": True} for _ in range(sv.n_bases)])
    p("")
    p("G5 ORACLE BITMAP CARRIED THROUGH THE WRITER (University Base {1,8} -> target {1,4})")
    p("  writes=%d diff_offsets=%s reload_bits=%s other_records_identical=%s identity_build=%s"
      % (len(writes), [hex(x) for x in diff], sorted(bits_of(rrec)), others_same,
         idn_blob == sv.data))
    img_sha = hashlib.sha256(blob).hexdigest()[:16]
    p("  written sha256[:16]=%s bytes=%d" % (img_sha, len(blob)))
    g("G5 the writer carries an ARBITRARY bitmap (a LOSS included, which the OR-only setter "
      "cannot express) and the reload reads it back",
      sorted(bits_of(rrec)) == [1, 4] and others_same and idn_blob == sv.data
      and all(FAC_OFF <= x < FAC_OFF + FAC_BYTES for x in diff) and len(writes) == 2)

    # ---- G6: rivals fail on the printed numbers + determinism --------------------------
    p("")
    p("G6 RIVALS + DETERMINISM")
    n_gain_rows = len(score)
    p("  rival1 'the head stamps the bit' matches %d/%d" % (hits, n_gain_rows))
    p("  rival2 'the bitmap only ever grows' contradicted by %d loss(es)" % len(losses))
    p("  rival3 'pop-first stamps the head' -> stamped %s, head-first stamps %s"
      % (sorted(bits_of(d_rv) - bits_of(bytes(deep))),
         sorted(bits_of(d_ok) - bits_of(bytes(deep)))))
    rows2 = deltas(load_trace())
    p("  determinism: deltas digest %s == %s ; oracle digest %s == %s"
      % (_sha(rows2) == d_dig, True, _sha([(si, ev, r, idx, name, tuple(sorted(bits_of(rec))))
                                          for si, (ev, r, bases) in enumerate(load_trace())
                                          for idx, name, rec in bases]) == o_dig, True))
    g("G6a rival1 fails (%d/%d)" % (hits, n_gain_rows), hits == 0 and n_gain_rows > 0)
    g("G6b rival2 fails (%d losses)" % len(losses), len(losses) > 0)
    g("G6c rival3 stamps the next item, not the head",
      sorted(bits_of(d_rv) - bits_of(bytes(deep))) == [6]
      and sorted(bits_of(d_ok) - bits_of(bytes(deep))) == [2])
    g("G6d two passes are identical (deltas + oracle digests)",
      _sha(rows2) == d_dig and _sha([(si, ev, r, idx, name, tuple(sorted(bits_of(rec))))
                                     for si, (ev, r, bases) in enumerate(load_trace())
                                     for idx, name, rec in bases]) == o_dig)

    # ---- G7: the anchors are PINNED, so drift reddens a gate --------------------------
    p("")
    p("G7 ANCHORS PINNED (rows, oracle, score, written image)")
    p("  rows=%s oracle=%s score=%s img=%s" % (_sha(rows), o_dig, s_dig, img_sha))
    g("G7 the run reproduces every pinned anchor",
      _sha(rows) == ROWS_ANCHOR and o_dig == ORACLE_ANCHOR
      and s_dig == SCORE_ANCHOR and img_sha == IMG_SHA)

    # ---- the verdict ------------------------------------------------------------------
    print("")
    print("B31 TABLE digest=%s oracle=%s score=%s" % (_sha(rows), o_dig, s_dig))
    failed = [lab for lab, ok, _ in gates if not ok]
    if failed:
        print("FAIL B31: %d/%d gates" % (len(gates) - len(failed), len(gates)))
        for lab in failed:
            print("  red: %s" % lab)
        return 1
    print("PASS B31: %d/%d gates" % (len(gates), len(gates)))
    print("ANCHORS rows=%s oracle=%s score=%s img=%s" % (_sha(rows), o_dig, s_dig, img_sha))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
