#!/usr/bin/env python3
"""M73 — unit cases for the price-split instrument: the parser, the gdb script, the
pre-attach candidate builder and the acceptance.  No game, no gdb: everything here is pure.

    python3 scripts/test_m73_split.py
"""
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import m73_price_split as S       # noqa: E402

CASES, FAILS = [], []


def case(name):
    def deco(fn):
        CASES.append((name, fn))
        return fn
    return deco


def eq(got, want, why=""):
    if got != want:
        raise AssertionError(f"got {got!r} want {want!r} {why}")


# ---------------------------------------------------------------- fake memory
class FakeMem:
    """Sparse /proc/pid/mem: seek/read over a dict of absolute addresses, zeros elsewhere."""
    def __init__(self, patches=b""):
        self.p = {}
        for a, b in patches:
            self.p[a] = bytes(b)
        self.pos = 0

    def seek(self, a):
        self.pos = a

    def read(self, n):
        out = bytearray(self.p.get(self.pos, b""))
        while len(out) < n:
            out.append(0)
        return bytes(out[:n])


def d32(v):
    return struct.pack("<i", v)


def image(**kw):
    """A box-shaped fake: owner 3 in-mask, era mult unused, [0x92a294] 10, [0x92ada8] 1
    -> A = 9; option dword 0x92a2d4 = 50 selected by type[+0x24] == 1; guards open."""
    patches = [
        (0x985B10, d32(0x08)), (0x985AEC, d32(0)), (0x68CBB8, d32(10)),
        (0x92A294, d32(10)), (0x92ADA8, d32(1)), (0x94D6A0 + 3 * 0x20BC, d32(0)),
        (S.OPT_TABLE + 144 * 1, b"\x01"), (0x92A2D4, d32(kw.get("P", 50))),
        (S.GUARD_CAT + 1436 * 3, d32(kw.get("flag200", 0))),
        (S.GUARD_ERA + 8380 * 3, d32(kw.get("era", 5))),
    ]
    for tid, cost, cat_field, lvl, f26, f27 in kw["types"]:
        rec = bytearray(52)
        rec[0x24], rec[0x25], rec[0x26], rec[0x27] = cat_field, lvl, f26, f27
        rec[0x29], rec[0x2a] = cost, 0
        struct.pack_into("<I", rec, 0x30, kw.get("flags30", 0))
        patches.append((S.TYPE_ARR + tid * S.TYPE_STRIDE, bytes(rec)))
    return FakeMem(patches)


TWO_IDS = dict(types=[(2, 1, 0, 1, 1, 0), (193, 2, 1, 2, 3, 0), (194, 3, 1, 3, 3, 0)])
IDS = [193, 194]


def build(m):
    A, si, cands = S.candidates(m, 3, IDS)
    eq(A, 9, "the fake box's cost_multiplier is 9")
    return A, si, cands


# ---------------------------------------------------------------- parse
@case("parse reads every tag with ints, hex and negatives")
def t1():
    ev, bad = S.parse("""ARMED base=0x95da10 head=193 pending=1 storage=120
VISIT pend=1 s0=193 s1=192 min=120
FLAG id=193 f30=0x45 byte=2
FACTORA id=193 own=3 A=9
FACTORB id=193 A=9 B=3
POSAFF storage=120 edi=27 ebx=193
BAILAFF storage=-1 edi=27 ebx=193
PAYA storage=120 edi=27 ebx=193
CREATE id=193 arg3=3 storage=111
PRICE_C id=193 P=50 byte=2 C=2 p2=-1 ret=0x4efa52
PRICE_M id=193 Mpre=1
PRICE_B id=193 B=3 M=1""")
    eq(bad, [])
    eq([e["tag"] for e in ev], ["ARMED", "VISIT", "FLAG", "FACTORA", "FACTORB", "POSAFF",
                                "BAILAFF", "PAYA", "CREATE", "PRICE_C", "PRICE_M", "PRICE_B"])
    eq(ev[2]["f30"], 0x45)
    eq(ev[3]["A"], 9); eq(ev[4]["B"], 3); eq(ev[6]["storage"], -1)
    eq(ev[9]["ret"], 0x4efa52); eq(ev[9]["p2"], -1)


@case("parse keeps gdb chatter out of the unknown-line bucket")
def t2():
    ev, bad = S.parse("""warning: Target and debugger are in different PID namespaces
[Inferior 1 (Process 1234) attached]
0x004efa52 in ?? ()
Thread 1 received signal SIGINT
junk line that is not ours""")
    eq([e["tag"] for e in ev], [])
    eq(bad, ["junk line that is not ours"])


@case("parse reads a negative hex operand (the bug test_m72_gate caught there)")
def t3():
    ev, bad = S.parse("PRICE_M id=-0x1 Mpre=-0x10")
    eq(bad, []); eq(ev[0]["id"], -1); eq(ev[0]["Mpre"], -16)


# ---------------------------------------------------------------- gdb script
@case("gdb script leaves no placeholder and arms 11 breakpoints")
def t4():
    s = S.gdb_script(0x95DA10, IDS)
    eq("@@" in s, False)
    eq(s.count("break *"), 12)
    for a in (S.ENTRY, S.VISIT, S.FACTORA, S.FACTORB, S.POSAFF, S.BAILAFF, S.PAYA, S.CREATE,
              S.PRICE_C, S.PRICE_M, S.PRICE_B, 0x5AC99C):
        eq(f"break *0x{a:x}" in s, True, f"breakpoint 0x{a:x} missing")
    eq("193" in s and "194" in s, True, "the armed ids must be in the conditions")


@case("every printf newline in the generated script is exactly one backslash + n")
def t5():
    s = S.gdb_script(0x95DA10, IDS)
    lines = [ln for ln in s.splitlines() if ln.startswith("printf ")]
    eq(len(lines) >= 12, True, f"{len(lines)} printf lines")
    for ln in lines:
        eq("\\n" in ln, True, ln)
        eq("\\\\n" in ln, False, f"double backslash in {ln}")


@case("the markup sites read the id from the frame, not from esi (esi holds the markup there)")
def t6():
    s = S.gdb_script(0x95DA10, IDS)
    at = {ln.split()[1]: ln for ln in s.splitlines() if ln.startswith("break *")}
    eq("($ebp + 8)" in at[f"*0x{S.PRICE_M:x}"], True)
    eq("($ebp + 8)" in at[f"*0x{S.PRICE_B:x}"], True)
    eq("$esi == 193" in at[f"*0x{S.PRICE_C:x}"], True, "0x5aca28 still has the id in esi")


# ---------------------------------------------------------------- candidates
@case("price_of is a candidate and equals A*cost for both ids")
def t7():
    A, si, cands = build(image(**TWO_IDS))
    po = [c for c in cands if c["name"] == "price_of"]
    eq(len(po), 1)
    eq(po[0]["vector"], {193: 18, 194: 27})


@case("the shape discriminates: readable-C candidates predict different edi pairs")
def t8():
    A, si, cands = build(image(**TWO_IDS))
    vecs = {tuple(c["vector"][t] for t in IDS) for c in cands}
    eq([18, 27] in [list(v) for v in vecs], True)
    eq([27, 45] in [list(v) for v in vecs], True, "C = cost with P 50 -> 27 and 45")
    eq(len(vecs) >= 2, True, f"only {vecs}")


@case("a guarded category collapses every candidate to price_of (gate 6 must FAIL that shape)")
def t9():
    kw = dict(TWO_IDS); kw["flag200"] = 0x200
    A, si, cands = build(image(**kw))
    eq(si[193]["guard_zero"], True)
    eq(si[193]["P"], 0, "the function multiplies by 0 when the flag fires")
    vecs = {tuple(c["vector"][t] for t in IDS) for c in cands}
    eq(len(vecs), 1, f"guarded ids cannot discriminate: {vecs}")


@case("P is read from the option dword the type[+0x24] selector picks")
def t10():
    A, si, cands = build(image(P=150, **TWO_IDS))
    eq(si[193]["P"], 150); eq(si[193]["sel"], 1)
    c = [c for c in cands if c["name"] == "C=cost"][0]
    eq(c["vector"][193], 9 * (2 + (2 * 150 + 50) // 100), "markup (C*P+50)/100")


# ---------------------------------------------------------------- score
def rows(*specs):
    out = []
    for tag, kv in specs:
        d = {"tag": tag}
        d.update(kv)
        out.append(d)
    return out


def good_rows():
    r = [("ENTRY", dict(base=0x95DA10, storage=120, s0=2, pend=2)),
         ("VISIT", dict(pend=2, s0=2, s1=194, min=120))]
    for tid, cost, mk, edi in ((2, 1, 0, 9), (194, 3, 2, 45), (193, 2, 1, 27)):
        r += [("FACTORA", dict(id=tid, own=3, A=9)),
              ("FACTORB", dict(id=tid, A=9, B=cost + mk)),
              ("POSAFF", dict(storage=120, edi=edi, ebx=tid)),
              ("PAYA", dict(storage=120, edi=edi, ebx=tid)),
              ("CREATE", dict(id=tid, arg3=cost, storage=120 - edi))]
        if tid != 2:
            r += [("FLAG", dict(id=tid, f30=0x41, byte=cost)),
                  ("PRICE_C", dict(id=tid, P=50, byte=cost, C=cost, p2=5, ret=0x4EFA52)),
                  ("PRICE_M", dict(id=tid, Mpre=mk)),
                  ("PRICE_B", dict(id=tid, B=cost + mk, M=mk, ret=0x4EFA52))]
    return rows(*r)


SHAPE = [2, 194, 193] + [0] * 9


def state(slot, minerals, round_, addr=0x95DA10, name="University Base", slots=None):
    return dict(slots=list(slots if slots is not None else SHAPE), minerals=minerals,
                round=round_, addr=addr, name=name, pending=2, fac=3)


def storages_for(kw, n=4):
    """The read-backs the instrument records: the arm poke plus one re-poke per boundary."""
    A, si_all, cands_all = S.candidates(image(**kw), 3, [t for t in SHAPE if t > 0])
    need = max(max(c["vector"][t] for c in cands_all) for t in SHAPE if t > 0)
    return [need + 30] * (1 + n)


def run(ev=None, before=None, after=None, kw=None, storages=None, flag_reads=()):
    kw = kw or TWO_IDS
    A, si, cands = build(image(**kw))
    ev = good_rows() if ev is None else ev
    before = state(2, 120, 60) if before is None else before
    after = state(192, 21, 62) if after is None else after
    storages = storages_for(kw) if storages is None else storages
    return S.score(before, after, ev, A, si, cands, storages, flag_reads) + (A, si, cands,)


def only(ev, **kw):
    return run(ev=ev, **kw)


@case("the good run passes every gate")
def t11():
    ok, gates, find, A, si, cands = run()
    bad = [g[0] for g in gates if not g[1]]
    eq(bad, [], f"failed gates: {bad}")
    eq(ok, True)
    eq(any("C=cost" in f for f in find), True, "the readable-C candidate should be named")


@case("gate 3 fails when A*B does not equal the edi the gate row used")
def t12():
    ev = [e for e in good_rows()]
    for e in ev:
        if e["tag"] == "POSAFF" and e["ebx"] == 193:
            e["edi"] = 18
    ok, gates, *_ = only(ev)
    eq(gates[2][1], False, gates[2][2])


@case("gate 4 fails when a FACTORA row disagrees with Python's cost_multiplier")
def t13():
    ev = good_rows()
    ev[2]["A"] = 10
    ok, gates, *_ = only(ev)
    eq(gates[3][1], False, gates[3][2])


@case("gate 5 fails when the markup is not (C*P+50)/100")
def t14():
    ev = good_rows()
    for e in ev:
        if e["tag"] == "PRICE_M" and e["id"] == 194:
            e["Mpre"] = 3
    ok, gates, *_ = only(ev)
    eq(gates[4][1], False, gates[4][2])


@case("gate 5 fails when an armed id's route through 0x5ac950 is unmeasured, not assumed")
def t15():
    ev = [e for e in good_rows()
          if not (e.get("id") == 193 and e["tag"] in ("FLAG", "PRICE_C", "PRICE_M", "PRICE_B"))]
    ok, gates, *_ = only(ev)
    eq(gates[4][1], False, gates[4][2])


@case("gate 5 fails when the only PRICE rows come from another caller (a display call)")
def t16():
    ev = good_rows()
    for e in ev:
        if e["tag"].startswith("PRICE_C"):
            e["ret"] = 0x4194B3
    ok, gates, *_ = only(ev)
    eq(gates[4][1], False, gates[4][2])


@case("gate 5 fails when the visit's FACTORB B is not the composed cost + markup")
def t17():
    ev = good_rows()
    for e in ev:
        if e["tag"] == "FACTORB" and e["id"] == 194:
            e["B"] = 6
    ok, gates, *_ = only(ev)
    eq(gates[4][1], False, gates[4][2])


@case("the early path is accepted when the logged flag has bit 2 and B is the bare cost")
def t17b():
    ev = good_rows()
    for e in ev:
        if e["tag"] == "FLAG" and e["id"] == 193:
            e["f30"] = 0x45
        elif e["tag"] == "PRICE_C" and e["id"] == 193:
            e["ret"] = 0x4194B3          # only a display call reached the markup path
        elif e["tag"] == "PRICE_M" and e["id"] == 193:
            e["Mpre"] = 0
        elif e["tag"] == "FACTORB" and e["id"] == 193:
            e["B"] = 2
        elif e["tag"] in ("POSAFF", "PAYA") and e.get("ebx") == 193:
            e["edi"] = 18
    ok, gates, *_ = only(ev)
    eq(gates[4][1], True, gates[4][2])
    eq(gates[6][1], True, "194 still differs from price_of, so the economic gate holds")


@case("gate 5 fails when the early path's B is not the bare cost the flag implies")
def t17c():
    ev = good_rows()
    for e in ev:
        if e["tag"] == "FLAG" and e["id"] == 193:
            e["f30"] = 0x45
        elif e["tag"] == "PRICE_C" and e["id"] == 193:
            e["ret"] = 0x4194B3
        elif e["tag"] == "FACTORB" and e["id"] == 193:
            e["B"] = 3
    ok, gates, *_ = only(ev)
    eq(gates[4][1], False, gates[4][2])


@case("gate 6 fails a shape where every candidate predicts the same edi")
def t18():
    kw = dict(TWO_IDS); kw["era"] = 1          # the [0x94d438] guard zeroes markup for the category
    ok, gates, *_ = run(kw=kw)
    eq(gates[5][1], False, gates[5][2])


@case("gate 7 fails when edi IS price_of for both ids (the repo model stands)")
def t19():
    ev = []
    for tid, cost, edi in ((2, 1, 9), (194, 3, 27), (193, 2, 18)):
        ev += rows((("FACTORA"), dict(id=tid, own=3, A=9)),
                   (("FACTORB"), dict(id=tid, A=9, B=cost)),
                   (("POSAFF"), dict(storage=120, edi=edi, ebx=tid)))
    ev = rows(("VISIT", dict(pend=2, s0=2, s1=194, min=120))) + ev
    ok, gates, *_ = only(ev)
    eq(gates[6][1], False, gates[6][2])


@case("gate 8 fails when one id's edi has two values inside the window (state moved)")
def t20():
    ev = good_rows() + rows(("POSAFF", dict(storage=90, edi=36, ebx=193)))
    ok, gates, *_ = run(ev=ev)
    eq(gates[7][1], False, gates[7][2])


@case("gate 9 fails when the base record moved mid-window")
def t21():
    ok, gates, *_ = run(after=state(192, 21, 62, addr=0x95DDA0))
    eq(gates[8][1], False, gates[8][2])


@case("gate 10 fails on an unparsed log line")
def t22():
    A, si, cands = build(image(**TWO_IDS))
    ok2, gates2, *_ = S.score(state(2, 120, 60), state(192, 21, 62), good_rows(), A, si, cands,
                              storages_for(TWO_IDS), bad_lines=("weird",))
    eq(gates2[9][1], False, gates2[9][2])
    ok3, gates3, *_ = S.score(state(2, 12, 60), state(192, 21, 62), good_rows(), A, si, cands,
                              [12, 12, 12])
    eq(gates3[0][1], False, "a storage read-back under the largest candidate edi must FAIL arm")
    ok4, gates4, *_ = S.score(state(2, 120, 60), state(192, 21, 62), good_rows(), A, si, cands,
                              storages_for(TWO_IDS, n=0) + [5])
    eq(gates4[0][1], False, "a boundary re-poke that read back short must FAIL arm too")


@case("markup zeroed by the base mask test is reported, not failed")
def t23():
    # the mask test at 0x5aca81 runs INSIDE the same 0x5ac950 call, so the markup, the return
    # value and the gate's edi all move together: 193 pays 18, not 27.
    ev = good_rows()
    for e in ev:
        tag = e["tag"]
        if tag == "PRICE_B" and e["id"] == 193:
            e["M"], e["B"] = 0, 2
        elif tag == "FACTORB" and e["id"] == 193:
            e["B"] = 2
        elif tag in ("POSAFF", "PAYA") and e.get("ebx") == 193:
            e["edi"] = 18
    ok, gates, find, A, si, cands = only(ev)
    eq(gates[4][1], True, gates[4][2])
    eq(any("base mask test" in f for f in find), True, "the mask zeroing must be reported")
    eq(gates[6][1], True, gates[6][2])
    eq(gates[2][1], True, "A*B == edi must still hold at 18")


@case("gate 1 fails when any storage read-back is short of the largest candidate edi")
def t24():
    ok, gates, *_ = run(storages=[120, 20])
    eq(gates[0][1], False, gates[0][2])


@case("gate 1 fails when a type[+0x30] poke did not read back with bit 2 clear")
def t26():
    ok, gates, *_ = run(flag_reads=[(193, 0x45, 0x45), (194, 0x45, 0x41)])
    eq(gates[0][1], False, gates[0][2])


@case("gate 3 counts only the ARMED ids: measuring the head plus one armed id is not two")
def t25():
    ev = [e for e in good_rows() if not (e.get("id") == 193 or e.get("ebx") == 193)]
    ok, gates, *_ = run(ev=ev)
    eq(gates[2][1], False, gates[2][2])


def main():
    for name, fn in CASES:
        try:
            fn()
            print(f"  ok   {name}")
        except Exception as e:
            FAILS.append(name)
            print(f"  FAIL {name}: {type(e).__name__}: {e}")
    print(f"{len(CASES) - len(FAILS)}/{len(CASES)} pass")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
