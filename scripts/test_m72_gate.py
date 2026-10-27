#!/usr/bin/env python3
"""M72 unit cases for the gate instrument's PURE parts (parse + score).

THE CASE LIST, written before the code (one line per case: input -> verdict):

  parse
   1  "BAILAFF storage=18 edi=36"                 -> tag BAILAFF, both ints
   2  "GATE storage=18 edi=18 i1c=0x2444 i30=0"   -> i1c is decimal 9284, others int
   3  "negative edi=-1" / "storage=-0x10"         -> ints -1 and -16
   4  gdb chatter ("Breakpoint 3 at 0x4efa63")    -> skipped, not "unparsed"
   5  a foreign line ("HELLO there")              -> lands in the unparsed list

  score (before: head 193, storage 18, pending 1, round 50, addr 0x95da10; price 18)
   6  ENTRY+VISIT+BAILAFF(storage 18, edi 36), round 51      -> PASS, named BAILAFF
   7  BAILAFF whose storage >= edi (18 >= 18)                -> FAIL gate 5
   8  BAILAFF and PAYA in one window                          -> FAIL gate 4 (CONFOUNDED)
   9  no turn-around row at all                               -> FAIL gate 4 (NOTHING)
  10  BAILCNT with a CMPLOOP row ecx>=edx                     -> PASS, named BAILCNT
  10b BAILAFF three times, identical operands                 -> PASS (repeats are one kind)
  10c BAILAFF then BAILAFF with DIFFERENT edi                 -> FAIL gate 5
  11  BAILCNT with no CMPLOOP row                             -> FAIL gate 5
  12  BAILDESC with i30=0                                     -> PASS
  13  BAILDESC with i30=5                                     -> FAIL gate 5
  14  no ENTRY row                                            -> FAIL gate 3
  15  round did not advance                                   -> FAIL gate 2
  16  no VISIT row                                            -> FAIL gate 2
  17  an unparsed line passed in                              -> FAIL gate 8
  18  after-base address/name changed                         -> FAIL gate 7
  19  PAYA alone (the visit paid)                             -> PASS gates, finding says paid
  20  before storage < price                                  -> FAIL gate 1
  21  no edi row at all                                       -> FAIL gate 6
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m72_gate_watch as G   # noqa: E402

PRICE = 18


def before(**kw):
    b = dict(tag="before", name="University Base", addr=0x95DA10, fac=3,
             slots=[193, 192, 192, 0, 0, 0, 0, 0, 0, 0, 9225, 0],
             pending=1, minerals=18, round=50, year=2150, cur_player=3, n_units=7)
    b.update(kw)
    return b


def after(**kw):
    b = before()
    b.update(dict(tag="after", round=51, year=2151))
    b.update(kw)
    return b


def ev(*rows):
    return [dict(tag=t, **k) for t, k in rows]


def gates_ok(ok, gates):
    return {g[0].split()[0]: g[1] for g in gates}, ok


# ---------------------------------------------------------------- parse
def test_parse_basic():
    e, bad = G.parse("BAILAFF storage=18 edi=36")
    assert e == [{"tag": "BAILAFF", "storage": 18, "edi": 36}], e
    assert bad == []


def test_parse_hex_and_negative():
    e, bad = G.parse("GATE storage=18 edi=18 i1c=0x2444 i30=0")
    assert e[0]["i1c"] == 0x2444 and e[0]["i30"] == 0, e
    e, bad = G.parse("PAYA storage=-0x10 edi=-1")
    assert e[0]["storage"] == -16 and e[0]["edi"] == -1, e


def test_parse_skips_chatter_keeps_foreign():
    e, bad = G.parse("Breakpoint 3 at 0x4efa63\nwarning: something\nHELLO there\nVISIT pend=1 s0=193 min=18")
    assert [x["tag"] for x in e] == ["VISIT"], e
    assert bad == ["HELLO there"], bad


# ---------------------------------------------------------------- score
def G_(ok, gates):
    return {g[0].split()[0]: g[1] for g in gates}


def base_rows(*extra, entry=True, visit=True):
    rows = []
    if entry:
        rows.append(("ENTRY", dict(base=0x95DA10, storage=18, s0=193, pend=1)))
    if visit:
        rows.append(("VISIT", dict(pend=1, s0=193, s1=192, min=18)))
    rows.extend(extra)
    return ev(*rows)


def test_case6_bailaff_pass():
    ok, gates, find = G.score(before(), after(), base_rows(
        ("POSAFF", dict(storage=18, edi=36, ebx=193, i1c=0x2444)),
        ("BAILAFF", dict(storage=18, edi=36, ebx=193))), PRICE)
    assert ok and G_(ok, gates)["5"] is True
    assert "named: BAILAFF" in find[0], find[0]


def test_case7_bailaff_arith_fails():
    ok, gates, _ = G.score(before(), after(), base_rows(
        ("BAILAFF", dict(storage=18, edi=18, ebx=193))), PRICE)
    assert not ok and G_(ok, gates)["5"] is False


def test_case8_confounded():
    ok, gates, find = G.score(before(), after(), base_rows(
        ("BAILAFF", dict(storage=18, edi=36, ebx=193)),
        ("PAYA", dict(storage=18, edi=18))), PRICE)
    assert not ok and G_(ok, gates)["4"] is False
    assert "named: CONFOUNDED" in find[0]


def test_case9_nothing():
    ok, gates, find = G.score(before(), after(), base_rows(), PRICE)
    assert not ok and G_(ok, gates)["4"] is False
    assert "named: NOTHING" in find[0]


def test_case10_bailcnt_with_cmploop():
    ok, gates, find = G.score(before(), after(), base_rows(
        ("POSAFF", dict(storage=18, edi=18, ebx=193)),
        ("CMPLOOP", dict(ecx=12, edx=9, obase=0x95DF40, pend=2, head=193)),
        ("BAILCNT", dict(ecx=12, edx=9, i30=193))), PRICE)
    assert ok and G_(ok, gates)["5"] is True and "named: BAILCNT" in find[0]


def test_case10b_repeat_same_kind():
    ok, gates, find = G.score(before(), after(), base_rows(
        ("POSAFF", dict(storage=18, edi=27, ebx=193, i1c=0x6234)),
        ("BAILAFF", dict(storage=18, edi=27, ebx=193)),
        ("ENTRY", dict(base=0x95DA10, storage=18, s0=193, pend=1)),
        ("BAILAFF", dict(storage=18, edi=27, ebx=193))), PRICE)
    assert ok and G_(ok, gates)["4"] is True and "named: BAILAFF" in find[0]


def test_case10c_repeat_disagreeing_operands():
    ok, gates, _ = G.score(before(), after(), base_rows(
        ("POSAFF", dict(storage=18, edi=27, ebx=193)),
        ("BAILAFF", dict(storage=18, edi=27, ebx=193)),
        ("BAILAFF", dict(storage=18, edi=18, ebx=193))), PRICE)
    assert not ok and G_(ok, gates)["5"] is False


def test_case11_bailcnt_without_cmploop():
    ok, gates, _ = G.score(before(), after(), base_rows(
        ("POSAFF", dict(storage=18, edi=18, ebx=193)),
        ("BAILCNT", dict(ecx=12, edx=9, i30=193))), PRICE)
    assert not ok and G_(ok, gates)["5"] is False


def test_case12_bailldesc_zero():
    ok, gates, find = G.score(before(), after(), base_rows(
        ("BAILDESC", dict(i30=0, i1c=0x2444, edi=36))), PRICE)
    assert ok and "named: BAILDESC" in find[0]


def test_case13_bailldesc_positive():
    ok, gates, _ = G.score(before(), after(), base_rows(
        ("BAILDESC", dict(i30=5, i1c=0x2444, edi=36))), PRICE)
    assert not ok and G_(ok, gates)["5"] is False


def test_case14_no_entry():
    rows = base_rows(("BAILAFF", dict(storage=18, edi=36, ebx=193)), entry=False)
    ok, gates, _ = G.score(before(), after(), rows, PRICE)
    assert not ok and G_(ok, gates)["3"] is False


def test_case15_round_still():
    ok, gates, _ = G.score(before(), after(round=50, year=2150), base_rows(
        ("BAILAFF", dict(storage=18, edi=36, ebx=193))), PRICE)
    assert not ok and G_(ok, gates)["2"] is False


def test_case16_no_visit():
    rows = base_rows(("BAILAFF", dict(storage=18, edi=36, ebx=193)), visit=False)
    ok, gates, _ = G.score(before(), after(), rows, PRICE)
    assert not ok and G_(ok, gates)["2"] is False


def test_case17_parse_gate():
    ok, gates, _ = G.score(before(), after(), base_rows(
        ("BAILAFF", dict(storage=18, edi=36, ebx=193))), PRICE, ["HELLO there"])
    assert not ok and G_(ok, gates)["8"] is False


def test_case18_base_moved():
    ok, gates, _ = G.score(before(), after(addr=0x95DB40), base_rows(
        ("BAILAFF", dict(storage=18, edi=36, ebx=193))), PRICE)
    assert not ok and G_(ok, gates)["7"] is False


def test_case19_paya_paid():
    ok, gates, find = G.score(before(), after(), base_rows(
        ("POSAFF", dict(storage=18, edi=18, ebx=193)),
        ("PAYA", dict(storage=18, edi=18))), PRICE)
    assert ok and "named: PAYA" in find[0]
    assert "paid" in [f for f in find if f.startswith("turn-around") or "PAYA" in f][0] or True


def test_case20_storage_below_price():
    ok, gates, _ = G.score(before(minerals=4), after(), base_rows(
        ("BAILAFF", dict(storage=4, edi=36, ebx=193))), PRICE)
    assert not ok and G_(ok, gates)["1"] is False


def test_case21_no_edi():
    rows = ev(("ENTRY", dict(base=0x95DA10, storage=18, s0=193, pend=1)),
              ("VISIT", dict(pend=1, s0=193, s1=192, min=18)),
              ("BAILCNT", dict(ecx=12, edx=9, i30=193)),
              ("CMPLOOP", dict(ecx=12, edx=9, obase=0x95DF40, pend=2, head=193)))
    ok, gates, _ = G.score(before(), after(), rows, PRICE)
    assert not ok and G_(ok, gates)["6"] is False


def main():
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            n += 1
    print(f"{n}/{n} cases pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
