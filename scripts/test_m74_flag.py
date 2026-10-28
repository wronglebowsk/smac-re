#!/usr/bin/env python3
"""M74 unit cases: the gdb script, the log parser, and the 10-gate scorer.

Fixtures are saved gdb rows + saved memory read-backs, so a FAIL here is the instrument, not
the game.  Run: python3 scripts/test_m74_flag.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import m74_flag_watch as W       # noqa: E402

PASS, FAIL = [], []


def check(name, got, want):
    (PASS if got == want else FAIL).append(name)
    if got != want:
        print(f"FAIL {name}\n  got  {got!r}\n  want {want!r}")


# ---------------------------------------------------------------- parser
LOG = """warning: Target disconnect not supported
Breakpoint 1 at 0x4eed18
ARMED base=0x95da10 head=194 pending=2 storage=200
[New Thread 0x7200]
0x004efa5e in FUN_004efed0 ()
W1 site=0x4eed18 tid=194 f30=0x41 own=3
POSAFF storage=200 edi=45 id=194 f30=0x41
W6 site=0x595f91 tid=193 f30=0x41 word=0x105
W2 site=0x573fed tid=-0x10 f30=0x45
a line that is not a row
"""

ev, bad = W.parse(LOG)
check("parse drops chatter and keeps rows", len(ev), 5)
check("parse reports the unparsed line", bad, ["a line that is not a row"])
check("parse W row fields", ev[1], {"tag": "W1", "site": 0x4eed18, "tid": 194, "f30": 0x41,
                                    "own": 3})
check("parse negative hex operand", ev[4]["tid"], -0x10)
check("parse ARMED", ev[0], {"tag": "ARMED", "base": 0x95da10, "head": 194, "pending": 2,
                             "storage": 200})
check("parse POSAFF flag byte", ev[2]["f30"], 0x41)

# ---------------------------------------------------------------- gdb script
s = W.gdb_script(0x95DA10, [193, 194])
check("script arms 12 breakpoints", s.count("\nbreak *"), 12)
check("script has all eleven writer sites",
      [f"break *{a:#x}" in s for a, _t, _f, _w, _se, _cl in W.SITES].count(True), 11)
wb = [b for b in s.split("break *")[1:] if "tid=%d" in b]
check("eleven writer blocks", len(wb), 11)
check("scaled-index sites test tid*13, the value [reg*4+0x98adb8] encodes",
      all(f"== {193 * 13}" in b and f"== {194 * 13}" in b for b in wb if "/ 13" in b), True)
check("six scaled-index sites divide their register by 13 to name the tid",
      sum("/ 13" in b for b in wb), 6)
check("byte-address sites test 0x98adb8 + tid*52",
      all(f"== {W.FLAG_ADDR + 193 * 0x34:#x}" in b and f"== {W.FLAG_ADDR + 194 * 0x34:#x}" in b
          for b in wb if "/ 52" in b), True)
check("five byte-address sites divide by 52 to name the tid", sum("/ 52" in b for b in wb), 5)
check("no condition compares a register to the bare tid", "== 193" in s, False)
check("printf newline is one backslash + n", s.count("\\n"), s.count("printf"))
check("no unsubstituted placeholders", [t in s for t in ("@@", "$X")].count(True), 0)
check("the visit gate is conditioned on the armed base",
      "break *0x4efa5e if *(int *)0x8f0d60 == $b" in s, True)
check("armed base substituted", "set $b = 0x95da10" in s, True)

# ---------------------------------------------------------------- scorer
IDS = [193, 194]
ARMED = {"addr": 0x95DA10, "slots": [194, 193, -39, -39, -39, -39], "pending": 2,
         "minerals": 200, "round": 54, "fac": 3, "armed_ok": True}
AFTER = {"addr": 0x95DA10, "slots": [193, -39, -39, -39, -39, -39], "pending": 1,
         "minerals": 155, "round": 55, "fac": 3, "armed_ok": True}
CB = {t: 0x41 for t in range(256)}
CB.update({64: 0x45, 128: 0x45, 129: 0x45, 192: 0x45})      # 193/194 cleared by the poke
CA = {**CB, 193: 0x45, 194: 0x45}
POKE = [(193, 0x45, 0x41), (194, 0x45, 0x41)]
GOOD_EV = [{"tag": "ARMED", "base": 0x95DA10, "head": 194, "pending": 2, "storage": 200},
           {"tag": "POSAFF", "storage": 200, "edi": 45, "id": 194, "f30": 0x41},
           {"tag": "W1", "site": 0x4EED18, "tid": 194, "f30": 0x41, "own": 3},
           {"tag": "POSAFF", "storage": 155, "edi": 18, "id": 193, "f30": 0x45},
           {"tag": "W1", "site": 0x4EED18, "tid": 193, "f30": 0x41, "own": 3}]


def run(ev=GOOD_EV, armed=ARMED, after=AFTER, cb=CB, ca=CA, ids=IDS, poke=POKE,
        rc=True, bad=(), tracer="0"):
    ok, gates, find = W.score(armed, cb, ca, ev, ids, poke, after, rc, list(bad), tracer)
    return ok, {n: g for n, g, _d in gates}, find


ok, gates, find = run()
check("green shape passes 10 gates", (ok, len(gates)), (True, 10))
check("green shape is all-PASS", sorted(g for g in gates.values()), [True] * 10)
check("finding names the fired site and function",
      any("W1 FUN_004eec30" in f and "id 194" in f for f in find), True)
check("finding reports the markup state at the visit",
      any("POSAFF id 193" in f and "markup OFF" in f for f in find), True)

noW = [e for e in GOOD_EV if not e["tag"].startswith("W")]
ok, gates, _ = run(ev=noW)
check("no writer row FAILs 'fired'", gates["fired"], False)
check("no writer row still arms", gates["armed"], True)

unmapped = GOOD_EV + [{"tag": "W3", "site": 0xDEADBEEF, "tid": 193, "f30": 0x41}]
ok, gates, _ = run(ev=unmapped)
check("an unmapped writer pc FAILs 'mapped'", gates["mapped"], False)

orphan = [e for e in GOOD_EV if e.get("tid") != 193]
ok, gates, _ = run(ev=orphan)
check("a flip with no writer row FAILs 'attributed'", gates["attributed"], False)

wrong = [{"tag": "ARMED", "base": 0x95DA10, "head": 194, "pending": 2, "storage": 200},
         {"tag": "POSAFF", "storage": 200, "edi": 45, "id": 194, "f30": 0x41},
         {"tag": "W5", "site": 0x595F82, "tid": 194, "f30": 0x41, "word": 1},
         {"tag": "W5", "site": 0x595F82, "tid": 193, "f30": 0x41, "word": 1}]
ok, gates, _ = run(ev=wrong)
check("a 0->1 flip explained only by the clearing site FAILs 'direction'",
      gates["direction"], False)
check("that run is still attributed", gates["attributed"], True)

# a whole-word = 0x105 write is a SETTER: the same flips must pass direction
setter = [{"tag": "ARMED", "base": 0x95DA10, "head": 194, "pending": 2, "storage": 200},
          {"tag": "POSAFF", "storage": 200, "edi": 45, "id": 194, "f30": 0x41},
          {"tag": "W6", "site": 0x595F91, "tid": 194, "f30": 0x41, "word": 0x105},
          {"tag": "W7", "site": 0x595F9C, "tid": 193, "f30": 0x41, "word": 0x115}]
ok, gates, _ = run(ev=setter)
check("whole-word setters pass direction", (gates["direction"], gates["attributed"]),
      (True, True))

# a 1->0 transition needs the clearing site
cb2 = {**CB, 193: 0x45, 194: 0x45}
ca2 = dict(CB)
clr = [{"tag": "ARMED", "base": 0x95DA10, "head": 194, "pending": 2, "storage": 200},
       {"tag": "POSAFF", "storage": 200, "edi": 45, "id": 194, "f30": 0x45},
       {"tag": "W5", "site": 0x595F82, "tid": 194, "f30": 0x45, "word": 1},
       {"tag": "W5", "site": 0x595F82, "tid": 193, "f30": 0x45, "word": 1}]
ok, gates, _ = run(ev=clr, cb=cb2, ca=ca2)
check("a 1->0 transition with the clearing site passes", (ok, gates["direction"]), (True, True))

# a record outside the armed set moved, and no writer row names it -> confounded
ca_conf = {**CA, 200: 0x45}
ok, gates, _ = run(ca=ca_conf)
check("an unexplained third record FAILs 'onevar'", gates["onevar"], False)
ok, gates, _ = run(ev=GOOD_EV + [{"tag": "W8", "site": 0x59D273, "tid": 200, "f30": 0x41}],
                   ca=ca_conf)
check("a third record that a writer row names is not confounded", gates["onevar"], True)

ok, gates, _ = run(after=dict(AFTER, pending=2, minerals=200, slots=ARMED["slots"]))
check("no pop FAILs 'completion'", gates["completion"], False)

ok, gates, _ = run(bad=["garbage line"])
check("an unparsed line FAILs 'parse'", gates["parse"], False)

ok, gates, _ = run(tracer="1234")
check("a stuck tracer FAILs 'clean'", gates["clean"], False)

ok, gates, _ = run(after=dict(AFTER, addr=0x95DD10))
check("a moved base FAILs 'stability'", gates["stability"], False)

ok, gates, _ = run(rc=False)
check("a non-zero boundary rc FAILs 'stability'", gates["stability"], False)

print(f"\n{len(PASS)}/{len(PASS) + len(FAIL)} pass"
      + ("" if not FAIL else " — " + ", ".join(FAIL)))
sys.exit(0 if not FAIL else 1)
