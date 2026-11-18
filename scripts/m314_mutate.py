#!/usr/bin/env python3
"""M314 mutation harness: each mutant rewrites one MEASURED literal in
scripts/m314_tour_family.py and must redden EXACTLY its named gate (non-zero rc
with that gate FAIL and no crash). Baseline must be green or the run refuses.
Per Trap 24 (a passing assertion is not a gate): every mutation is a state the
real bytes could have had, not a dict entry the assert reads whole.
"""
import os, re, subprocess, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "scripts", "m314_tour_family.py")
src = open(SRC).read()
env = dict(os.environ, PYTHONPATH=os.path.join(REPO, "scripts"))

def run(text):
    fd, path = tempfile.mkstemp(suffix=".py", dir=os.path.join(REPO, "scripts"))
    os.write(fd, text.encode()); os.close(fd)
    try:
        p = subprocess.run([sys.executable, "-u", path], capture_output=True,
                           text=True, env=env, cwd=REPO, timeout=600)
        return p.returncode, p.stdout + p.stderr
    finally:
        os.unlink(path)

def gate_of(out):
    return sorted(re.findall(r"^FAIL (\S+?)\s", out, re.M))

# (id, old literal, new literal, gate prefix that must go red)
MUT = [
    ("MU1_call_count",   "len(sites) == 31 and len(pinned) == 31",
                         "len(sites) == 30 and len(pinned) == 31", "A1"),
    ("MU2_token_bound",  "len(toks) == 31 - 3 and len(quoted) == 24",
                         "len(toks) == 31 - 3 and len(quoted) == 23", "A1b"),
    ("MU2b_fwd", 'forwarded == ["param_1", "param_2"]',
                 'forwarded == ["param_1", "param_3"]', "A1b"),
    ("MU3_wrapper_prod", "W = {0x4C2E90: 0x4C3F90,", "W = {0x4C2E90: 0x4C3F91,", "A2"),
    ("MU4_formula_cnt",  "n_formula == 4,", "n_formula == 3,", "A2b"),
    ("MU5_je_off", "JE_OFF = {0x4C5C40: 0xD, 0x4C5CA0: 0xD, 0x4C5CF0: 0x2D}",
                   "JE_OFF = {0x4C5C40: 0xE, 0x4C5CA0: 0xD, 0x4C5CF0: 0x2D}", "A3"),
    ("MU5d_cmp_off", "CMP_OFF = {0x4C5C40: 0x9, 0x4C5CA0: 0x9, 0x4C5CF0: 0x29}",
                      "CMP_OFF = {0x4C5C40: 0x9, 0x4C5CA0: 0x9, 0x4C5CF0: 0x19}", "A3"),
    ("MU5b_delta", 'int(win[je_a[0]][1], 16) - add_a[0] == 10',
                   'int(win[je_a[0]][1], 16) - add_a[0] == 9', "Ax3"),
    ("MU5c_movpos", "mov_a[0] == add_a[0] - 3", "mov_a[0] == add_a[0] - 4", "Ax3"),
    ("MU6_abs_target",   "0x4C5CF0: 0x5510F0}", "0x4C5CF0: 0x5510F1}", "A3"),
    ("MU7_jl_target", '(0x4C5D01, "jl", "0x4c5d0e")', '(0x4C5D01, "jl", "0x4c5d0f")', "A3b"),
    ("MU8_add444_cnt",   "add444 == 3,", "add444 == 6,", "A3c"),
    ("MU9_push_owner", 'own == {"0x4c5d60"}', 'own == {"0x4c5d61"}', "A4"),
    ("MU9b_leg_split", 'len(legA) == 3 and len(legB) == 3',
                       'len(legA) == 2 and len(legB) == 3', "A4"),
    ("MU9c_leg_order", '[t for _, t in order(legA)] == [t for _, t in order(legB)]',
                       '[t for _, t in order(legA)] == [t for _, t in order(legB)][::-1]', "A4"),
    ("MU9b_push_count",  "and len(pushes) == 3", "and len(pushes) == 4", "A4"),
    ("MU10_pumpB_site",  '== ["0x517858"]', '== ["0x517859"]', "A5"),
    ("MU11_offband6",    "missing == [] and 0x4D3F70 in called",
                         "missing == [] and 0x4D3F71 in called", "A5b"),
    ("MU12_pumpA_swap",  "all(t != 0x4D3F70 for _, t in pa)",
                         "all(t == 0x4D3F70 for _, t in pa)", "A5c"),
    ("MU13_bandmember",  '== ["0x50cab0"]', '== ["0x50cab1"]', "A6"),
    ("MU14_offdistinct", "len({t for _, t in off}) == 22",
                         "len({t for _, t in off}) == 21", "A6"),
    ("MU15_callers5",    '"0x512450", "0x516b80"]', '"0x512450"]', "A6b"),
    ("MU15b_dup_owner",  '["0x475d57", "0x477222", "0x511a3e", "0x5124e3", "0x517858"]',
                         '["0x475d57", "0x477222", "0x511a3e", "0x5124e3", "0x475d57"]', "A6b"),
    ("MU18_push_census",  'no_pushA == [] and no_pushB == []',
                          'no_pushA == [] and no_pushB == [] and len(push_hex) == 1', "A4b"),
    ("MU18b_pumpBcnt",   "len(pumpA) == 3 and len(pumpB) == 1",
                         "len(pumpA) == 3 and len(pumpB) == 2", "A4b"),
    ("MU16_token_str",   '("0x68c260", "Activate")', '("0x68c260", "Activatf")', "A6c"),
    ("MU17_a7_baseoff",  "len(usesda12) >= 1 and len(baseoff) >= 1",
                         "len(usesda12) >= 3 and len(baseoff) >= 1", "A7"),
]

def main():
    rc, out = run(src)
    if rc != 0:
        print("BASELINE NOT GREEN - refusing:\n" + out[-2000:]); return 2
    print("baseline green:", out.strip().splitlines()[-1])
    bad = 0
    for mid, old, new, gate in MUT:
        if src.count(old) != 1:
            print("MU-ANCHOR %s: anchor count %d (not 1) - HARNESS BUG"
                  % (mid, src.count(old))); bad += 1; continue
        rc, out = run(src.replace(old, new))
        fails = gate_of(out)
        if "Traceback" in out:
            print("MU-CRASH %s rejected per law (not a red gate)" % mid); bad += 1; continue
        if gate.endswith("x3"):  # one defect legitimately reddens 3 sibling gates
            hit = [f for f in fails if f.startswith(gate[:-2])]
            okg = rc != 0 and len(hit) == 3 and len(fails) == 3
        else:
            hit = [f for f in fails if f.startswith(gate)]
            okg = rc != 0 and len(hit) == 1 and len(fails) == 1
        if okg:
            print("OK   %s reddened exactly %s (%s)" % (mid, gate, fails[0][:48]))
        else:
            print("BAD  %s rc=%d fails=%s" % (mid, rc, fails)); bad += 1
    n = len(MUT)
    print("== M314-mutate: %d/%d mutations reddened their target gates ==" % (n - bad, n))
    return 0 if bad == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
