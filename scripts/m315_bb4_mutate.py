#!/usr/bin/env python3
"""M315 mutation harness: each mutant rewrites one MEASURED literal in
scripts/m315_bb4_census.py and must redden EXACTLY its named gate (non-zero rc,
that gate FAIL, no crash). Baseline must be green or the run refuses.
Mutations are states the REAL BYTES could have had (a wrong address in a pinned
census, a weaker sentinel count, a wrong pair callee), never a dict entry the
assert reads whole (Trap 24).
"""
import os, re, subprocess, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "scripts", "m315_bb4_census.py")
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


def gates(out):
    # gate IDs are the first token of each FAIL line; set-equality against the
    # declared set is the whole test (a gate token is unique per assertion)
    return sorted(re.findall(r"^FAIL (\S+)", out, re.M))


# (id, old literal, new literal, expected FAIL gate set). A mutation that
# reddens MORE than its declared set means the fact is load-bearing somewhere the
# doc does not say; fewer means the assert is decorative. Both are BAD.
MUT = [
    ("MU1_census_drop", "0x416E60, 0x41B7A7", "0x41B7A7", "A1"),
    ("MU2_census_read", "RD = [0x4E5155, 0x4EFE83", "RD = [0x4E5155, 0x4EFE84", "A1"),
    ("MU3_sent_count", "len(sent_direct) == 8 and sorted(sent_or)", "len(sent_direct) == 7 and sorted(sent_or)", "A2"),
    ("MU4_sent_or", "[0x41B7A7, 0x5984B4]", "[0x41B7A7, 0x5984B5]", "A2"),
    ("MU5_idx_reads", 'kinds.get("reads-index") == 8', 'kinds.get("reads-index") == 7', "A2b"),
    ("MU6_pair_const", "REFRESH = (0x4E8D60, 0x4E78E0)", "REFRESH = (0x4E8D60, 0x4E78E1)",
     {"A3", "A4", "A9"}),   # the refresh pair IS the memo definition: 3 gates see it
    ("MU7_memo_count", "len(memo) == 12 and len(clear) == 10", "len(memo) == 11 and len(clear) == 10", "A3"),
    ("MU8_partition_blind", "set(clear) == set(sent_direct) | set(sent_or)",
                            "set(clear) == set(sent_direct)", "A3"),  # drops the 2 via-or sentinels: size 8 != 10
    ("MU9_guard_site", "[0x4EB6C7, 0x4EFEAA, 0x4F2201, 0x4F5C4A]",
                       "[0x4EB6C7, 0x4EFEAA, 0x4F2202, 0x4F5C4A]", "A4"),
    ("MU10_unguarded", "len(unguarded) == 8, measured[\"A4\"]", "len(unguarded) == 9, measured[\"A4\"]", "A4"),
    ("MU11_fwd_window", "fwd32 == [0x4E4DDC, 0x4EFEAA, 0x4F5C4A]",
                        "fwd32 == [0x4E4DDC, 0x4EFEAB, 0x4F5C4A]", "A5"),
    ("MU12b_closure", "len(closure) == 10 and len(out_fwd) - len(closure) == 9",
                      "len(closure) == 9 and len(out_fwd) - len(closure) == 10", "A5"),
    ("MU12_win96", "idx == [0x4E3476, 0x4E4DD0", "idx == [0x4E3477, 0x4E4DD0", "A5"),
    ("MU13_pin_cmp", '(0x4EFEA0, ["cmp", "eax,esi"])', '(0x4EFEA0, ["cmp", "eax,edi"])', "A6"),
    ("MU14_pin_je", '(0x4F5C48, ["je", "0x4f5c69"])', '(0x4F5C48, ["je", "0x4f5c6a"])', "A6"),
    ("MU15_init_pair", "v == (0xFFFFFFFF, 0xFFFFFFFF)", "v == (0x00000000, 0xFFFFFFFF)", "A7"),
    ("MU16_rival_blind", "other_idx == [] and not any(k.startswith(\"other\") for k in kinds)",
                         "other_idx != [] and not any(k.startswith(\"other\") for k in kinds)", "A9"),
    ("MU17_identity", "kinds.get(\"reads-index\") + kinds.get(\"stack-slot\") == len(memo)",
                      "kinds.get(\"reads-index\") + kinds.get(\"stack-slot\") == len(memo) + 1", "A9"),
    # a threshold mutation: the 16-B reach of the pair scan is what makes memo=12
    ("MU18_pair_reach", "            if b - a > 16:", "            if b - a > 4:",
     {"A3", "A4", "A9"}),   # a tighter reach shrinks the memo set: all 3 gates see it
]


def main():
    rc, out = run(src)
    if rc != 0:
        print("BASELINE NOT GREEN - refusing:\n" + out[-1500:]); return 2
    print("baseline green:", out.strip().splitlines()[-1])
    bad = 0
    for mid, old, new, want in MUT:
        want = {want} if isinstance(want, str) else set(want)
        n = src.count(old)
        if n != 1:
            print("BAD  %s anchor count %d (not 1) - HARNESS BUG" % (mid, n)); bad += 1; continue
        rc, out = run(src.replace(old, new))
        if "Traceback" in out:
            print("BAD  %s CRASHED - rejected per law (a crash is not a red gate)" % mid)
            bad += 1; continue
        fails = gates(out)
        if rc != 0 and set(fails) == want:
            print("OK   %s reddened exactly %s" % (mid, "/".join(sorted(want))))
        else:
            print("BAD  %s rc=%d want=%s fails=%s" % (mid, rc, sorted(want), fails)); bad += 1
    print("== M315-mutate: %d/%d mutations reddened exactly their declared gates =="
          % (len(MUT) - bad, len(MUT)))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
