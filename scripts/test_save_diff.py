#!/usr/bin/env python3
"""Tests for scripts/save_diff.py — the region guard that M114 needed. Offline, no game, no box.

    python3 scripts/test_save_diff.py      # exits 0 on PASS
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import save_diff as S

CASES = []


def case(fn):
    CASES.append(fn)
    return fn


@case
def regions_group_by_k():
    rs = S.regions()
    assert len(rs) == 11, "expected 11 regions, got %d" % len(rs)
    block_a = [r for r in rs if r[2] == 0x94D104]
    assert len(block_a) == 1 and block_a[0][3] == 5, "block A must hold 5 anchors: %r" % (block_a,)
    assert block_a[0][0] == 16384 and block_a[0][1] == 68096, "block A span %r" % (block_a[0],)


@case
def spans_are_contiguous():
    rs = S.regions()
    for a, b in zip(rs, rs[1:]):
        assert a[1] == b[0], "gap/overlap between regions at %d" % a[1]


@case
def accepts_a_range_inside_block_a():
    k, (lo, hi) = S.check_range(66048, 67840)
    assert k == 0x94D104, hex(k)


@case
def accepts_the_whole_grid():
    k, (lo, hi) = S.check_range(82432, 172200)
    assert k == 0x40925B0, hex(k)


@case
def refuses_the_m114_window():
    """The exact window M114 merged as 'block A tail rewriting' — it crosses 67,072."""
    try:
        S.check_range(67072, 69120)
    except SystemExit as e:
        assert "67072" in str(e), "must name the boundary it crosses: %s" % e
        return
    raise AssertionError("M114's straddling window was NOT refused")


@case
def refuses_the_second_m114_window():
    """'map header tail 81,408..82,100' crosses the grid start at 82,088."""
    try:
        S.check_range(81408, 82100)
    except SystemExit as e:
        assert "82074" in str(e) or "82088" in str(e), "must name a boundary: %s" % e
        return
    raise AssertionError("the map-header straddling window was NOT refused")


@case
def refuses_a_one_byte_overrun_of_a_boundary():
    try:
        S.check_range(66000, 68096)
    except SystemExit:
        return
    raise AssertionError("a range ending past the boundary must be refused")


def main():
    bad = 0
    for fn in CASES:
        try:
            fn()
            print("PASS %s" % fn.__name__)
        except AssertionError as e:
            bad += 1
            print("FAIL %s — %s" % (fn.__name__, e))
    print("PASS %d/%d save_diff cases" % (len(CASES) - bad, len(CASES)) if not bad else
          "FAIL %d/%d" % (len(CASES) - bad, len(CASES)))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
