#!/usr/bin/env python3
"""M315 mutation harness (review #301 round 2): two mutant families.

(1) EXPECTATION mutants (MU*) - rewrite one measured literal in
    scripts/m315_bb4_census.py so the claim is FALSE on the real bytes.
(2) CODE mutants (PC*) - run the instrument against a REWRITTEN DISASSEMBLY
    (env M315_PATCH="addr|mn ops;addr|mn ops"): change the code the census reads
    and show which gate must notice. Review #301 asked for parsed-instruction
    tests rather than count tests - a provenance classifier that keys on operand
    TEXT alone passes family (1) and is caught by family (2).

Every mutant must redden EXACTLY its declared gate SET: a missing red is a
decorative assert, an extra red is an undeclared dependency. A crash is not a red.
Baseline must be green or the run refuses.
"""
import os, re, subprocess, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "scripts", "m315_bb4_census.py")
src = open(SRC).read()
env0 = dict(os.environ, PYTHONPATH=os.path.join(REPO, "scripts"))


def run(text, patch=None):
    fd, path = tempfile.mkstemp(suffix=".py", dir=os.path.join(REPO, "scripts"))
    os.write(fd, text.encode()); os.close(fd)
    env = dict(env0, M315_PATCH=patch) if patch else env0
    try:
        p = subprocess.run([sys.executable, "-u", path], capture_output=True,
                           text=True, env=env, cwd=REPO, timeout=600)
        return p.returncode, p.stdout + p.stderr
    finally:
        os.unlink(path)


def gates(out):
    return sorted(set(re.findall(r"^FAIL (\S+)", out, re.M)))


# ---- family 1: expectation mutants (id, old literal, new literal, gate set) --
MUT = [
    ("MU1_census_drop", "0x416E60, 0x41B7A7", "0x41B7A7", {"A1"}),
    ("MU2_census_read", "RD = [0x4E5155, 0x4EFE83", "RD = [0x4E5155, 0x4EFE84", {"A1"}),
    ("MU3_sent_count", "len(sent_direct) == 8 and sorted(sent_or)",
     "len(sent_direct) == 7 and sorted(sent_or)", {"A2"}),
    ("MU4_sent_or", "[0x41B7A7, 0x5984B4]", "[0x41B7A7, 0x5984B5]", {"A2"}),
    ("MU5_kind_count", 'kinds.get("reads-index") == 8 and kinds.get("stack-slot:ebp") == 4',
     'kinds.get("reads-index") == 7 and kinds.get("stack-slot:ebp") == 4', {"A2b"}),
    ("MU5b_slot_ops", 'slot_ops == {"[ebp+0x8]": 3, "[ebp-0x18]": 1}',
     'slot_ops == {"[ebp+0x8]": 4}', {"A2b"}),
    ("MU6_pair_const", "REFRESH = (0x4E8D60, 0x4E78E0)", "REFRESH = (0x4E8D60, 0x4E78E1)",
     {"A3", "A4", "A9"}),
    ("MU7_memo_count", "len(memo) == 12 and len(clear) == 10", "len(memo) == 11 and len(clear) == 10", {"A3"}),
    ("MU8_partition_blind", "set(clear) == set(sent_direct) | set(sent_or)",
     "set(clear) == set(sent_direct)", {"A3"}),
    ("MU9_dist_pin", "(12, 17), (5, 10), (6, 11)] and", "(12, 16), (5, 10), (6, 11)] and", {"A3"}),
    ("MU10_absence_claim", "set(absence) == {(0, 0)}", "set(absence) == {(1, 0)}", {"A3"}),
    ("MU11_guard_site", "[0x4EB6C7, 0x4EFEAA, 0x4F2201, 0x4F5C4A]",
     "[0x4EB6C7, 0x4EFEAA, 0x4F2202, 0x4F5C4A]", {"A4"}),
    ("MU12_unguarded", 'len(unguarded) == 8, measured["A4"]', 'len(unguarded) == 9, measured["A4"]', {"A4"}),
    ("MU13_fwd_window", "fwd32 == [0x4E4DDC, 0x4EFEAA, 0x4F5C4A]",
     "fwd32 == [0x4E4DDC, 0x4EFEAB, 0x4F5C4A]", {"A5"}),
    ("MU14_closure", "len(closure) == 10 and len(out_fwd) - len(closure) == 9",
     "len(closure) == 9 and len(out_fwd) - len(closure) == 10", {"A5"}),
    ("MU15_idx_list", "idx == [0x4E3476, 0x4E4DD0", "idx == [0x4E3477, 0x4E4DD0", {"A5"}),
    ("MU16_fold_expect", '["lea", "ecx,[esi+ecx*2]"]', '["lea", "ecx,[esi+ecx*3]"]', {"A6"}),
    ("MU17_je_w4", '["je", "0x4eb6e5"]', '["je", "0x4eb6e6"]', {"A6"}),
    ("MU18_init_pair", "v == (0xFFFFFFFF, 0xFFFFFFFF)", "v == (0x00000000, 0xFFFFFFFF)", {"A7"}),
    ("MU19_unclaimed", "unclaimed == [0x4F3F7F]", "unclaimed == [0x4F3F7E]", {"A10"}),
    ("MU20_rival_blind", "other_idx == [] and sum(non_sent.values()) == len(memo)",
     "other_idx != [] and sum(non_sent.values()) == len(memo)", {"A9"}),
    ("MU21_pair_reach", "    PAIR_REACH = 17", "    PAIR_REACH = 10", {"A3", "A4", "A9"}),
]
# ---- family 2: code mutants (id, M315_PATCH spec, gate set) -----------------
CODE = [
    ("PC1_add_is_not_read", "0x4f3f76|add ecx,DWORD PTR ds:0x68cbb0", {"A2", "A2b", "A6", "A9"}),
    ("PC2_lea_is_not_load", "0x4e4dbc|lea esi,DWORD PTR [ebp+0x8]", {"A2", "A2b", "A9"}),
    ("PC3_cmp_wrong_side", "0x4eb6bf|cmp DWORD PTR ds:0x68cbb4,edx", {"A4", "A6"}),
    ("PC4_second_callee_gone", "0x4efeb5|call 0xdead00", {"A3", "A4", "A9"}),
    ("PC5_fold_corrupt", "0x4efe94|lea ecx,[esi+ecx*3]", {"A6"}),
    ("PC6_index_store_gone", "0x4efe8e|nop", {"A5", "A6"}),
    ("PC7_clear_gains_pair", "0x416e6a|call 0x4e8d60;0x416e70|call 0x4e78e0", {"A3", "A4", "A9"}),
]


def main():
    rc, out = run(src)
    if rc != 0:
        print("BASELINE NOT GREEN - refusing:\n" + out[-1500:]); return 2
    print("baseline green:", out.strip().splitlines()[-1])
    bad = 0
    for mid, old, new, want in MUT:
        n = src.count(old)
        if n != 1:
            print("BAD  %s anchor count %d (not 1) - HARNESS BUG" % (mid, n)); bad += 1; continue
        rc, out = run(src.replace(old, new))
        fails = gates(out)
        if "Traceback" in out:
            print("BAD  %s CRASHED - rejected per law (a crash is not a red gate)" % mid); bad += 1; continue
        if rc != 0 and set(fails) == set(want):
            print("OK   %s reddened exactly %s" % (mid, "/".join(sorted(want))))
        else:
            print("BAD  %s rc=%d want=%s fails=%s" % (mid, rc, sorted(want), fails)); bad += 1
    for mid, patch, want in CODE:
        rc, out = run(src, patch=patch)
        fails = gates(out)
        if "Traceback" in out:
            print("BAD  %s CRASHED - rejected per law" % mid); bad += 1; continue
        if "patches applied: 0/" in out:
            print("BAD  %s patch applied to nothing - vacuous" % mid); bad += 1; continue
        if rc != 0 and set(fails) == set(want):
            print("OK   %s [%s] reddened exactly %s"
                  % (mid, patch.split(";")[0], "/".join(sorted(want))))
        else:
            print("BAD  %s rc=%d want=%s fails=%s" % (mid, rc, sorted(want), fails)); bad += 1
    print("== M315-mutate: %d/%d mutations reddened exactly their declared gate sets "
          "(%d expectation + %d code) =="
          % (len(MUT) + len(CODE) - bad, len(MUT) + len(CODE), len(MUT), len(CODE)))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
