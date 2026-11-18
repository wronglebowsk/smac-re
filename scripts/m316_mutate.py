#!/usr/bin/env python3
# M316 mutation harness: every mutant must redden EXACTLY its declared gate set.
# Family 1 = rewrite a measured literal/constant in the instrument.
# Family 2 = corrupt the PARSED CODE via M316_PATCH="addr|mnem ops;..." (never an expected constant).
import os, re, subprocess, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "scripts", "m316_addgoal.py")

# expectation mutants: (name, old_snippet, new_snippet, expected_reddened_gates)
MUTS = [
 ("MU01_band_want_addr", 'want = {0x56d44b: (4, "DWORD", "ecx")', 'want = {0x56d44c: (4, "DWORD", "ecx")', ["A1_band_absolute_writes_exactly6"]),
 ("MU02_layout_swap_sizes", 'lay == {4: "DWORD", 8: "DWORD", 0: "WORD", 2: "WORD", 12: "DWORD"}',
    'lay == {4: "DWORD", 8: "DWORD", 0: "DWORD", 2: "WORD", 12: "DWORD"}', ["A2_record_layout"]),
 ("MU03_shl16_list_short", "shl16 == [0x56d395, 0x56d404, 0x56d442]", "shl16 == [0x56d395, 0x56d404]",
    ["A2b_entry16B_fold_via_shl_and_lea"]),
 ("MU04_bound68", '"cmp" and re.fullmatch(r".*,0x4b"', '"cmp" and re.fullmatch(r".*,0x44"',
    ["A3_all_goal_list_bounds_are_75"]),
 ("MU05_evict_addr", '{"free1000": 0x56d3e6', '{"free1000": 0x56d3e7', ["A4_eviction_score_constants"]),
 ("MU06_duptriple_target", '(0x56d3b3, "je", "0x56d404")', '(0x56d3b3, "je", "0x56d405")',
    ["A5_duplicate_triple_and_16B_stride"]),
 ("MU07_stride8", '(0x56d3b6, "add", "ecx,0x10")', '(0x56d3b6, "add", "ecx,0x8")',
    ["A5_duplicate_triple_and_16B_stride"]),
 ("MU08_evictcmpform", 'INS[0x56d436] == ("cmp", "edi,0x4b")', 'INS[0x56d436] == ("cmp", "edi,0x4c")',
    ["A5b_max_tail_and_eviction_backedge"]),
 ("MU09_ownercount", 'len(set(o for _, o, _, _ in siteinfo)) == 12', 'len(set(o for _, o, _, _ in siteinfo)) == 13',
    ["A6_sites_exactly50"]),
 ("MU10_kinds_minus3", "imm_kinds == [0, 2, 3, 6, 7, 8, 9, 11, 16, 25, 41]",
    "imm_kinds == [0, 2, 6, 7, 8, 9, 11, 16, 25, 41]", ["A6c_immediate_kinds_constructed"]),
 ("MU11_string_nul", 'sbytes[:20] == b"Bad GOAL\\x00\\x00\\x00\\x00Bad SITE"', 'sbytes[:20] == b"Bad GOAL\\x00\\x00\\x00\\x00Bad SITES"',
    ["A7_bad_goal_assertion"]),
 ("MU12_dbgbit_test", "dbgtest == [0x56d369]", "dbgtest == [0x56d368]", ["A7_bad_goal_assertion"]),
 ("MU13_parity_test", 'INS[0x56d360] == ("test", "al,0x1")', 'INS[0x56d360] == ("test", "al,0x2")',
    ["A7b_parity_predicate_shape"]),
 ("MU14_accessor_callers", '"FUN_0056d5d0": (0, 15)', '"FUN_0056d5d0": (0, 14)', ["A8_accessor_family"]),
 ("MU15_engine_offsets", "dict(offs) == {0: 8, 2: 2, 4: 12, 8: 12, 12: 1}", "dict(offs) == {0: 8, 2: 2, 4: 12, 8: 12, 12: 2}",
    ["A9_engine_band_access_shape"]),
 ("MU16_engine_callers", 'engcall == ["0x52094f", "0x59dd43"]', 'engcall == ["0x52094f", "0x59dd42"]',
    ["A9_engine_band_access_shape"]),
 ("MU17_token_live3", "tok_live == [0, 2, 3, 6, 8, 9, 41]", "tok_live == [0, 2, 6, 8, 9, 41]",
    ["A10_token_kinds_constructed"]),
 ("MU18_rel_kill_dropped", '0x56d6be: (0, "WORD", "0xffff"), 0x56d6c8', '0x56d6c8',
    ["A11_band_relative_writes_exactly13"]),
 ("MU19_rel_addr_typo", "wantrel = {0x56d41c: (2, \"WORD\", \"ax\")", "wantrel = {0x56d41d: (2, \"WORD\", \"ax\")",
    ["A11_band_relative_writes_exactly13"]),
]
# code mutants: (name, patch, expected gates) - patch the ENGINE'S INSTRUCTIONS, not the instrument
CODE = [
 ("PC01_store_prio_clobbers_owner", "0x56d469|mov WORD PTR [eax+0x94ee34],dx",
   ["A1_band_absolute_writes_exactly6", "A2_record_layout"]),
 ("PC02_dup_bound_widens", "0x56d3b9|cmp eax,0x4c",
   ["A3_all_goal_list_bounds_are_75"]),
 ("PC03_dupstride24", "0x56d3b6|add ecx,0x18", ["A5_duplicate_triple_and_16B_stride"]),
 ("PC04_je_deadtarget", "0x56d3b3|je 0x56d3c0", ["A5_duplicate_triple_and_16B_stride"]),
 ("PC05_free1000_becomes100", "0x56d3e6|and ebx,0x64", ["A4_eviction_score_constants"]),
 ("PC06_base20_becomes21", "0x56d3fb|mov eax,0x15", ["A4_eviction_score_constants"]),
 ("PC07_parity_gate_off", "0x56d360|test al,0x0", ["A7b_parity_predicate_shape"]),
 ("PC08_dbgbit_wrongreg", "0x56d369|test al,0x10", ["A7_bad_goal_assertion"]),
 ("PC09_killstore_to_prio", "0x470d5c|mov WORD PTR [ecx+edx*1+0x94ee2a],0xffff",
   ["A1_band_absolute_writes_exactly6"]),
 ("PC10_site_removed", "0x4ce2dd|nop", ["A6_sites_exactly50", "A6b_site_owner_digest"]),
 ("PC11_setter_field2_gone", "0x56d75f|mov WORD PTR [eax+0x20],cx", ["A11_band_relative_writes_exactly13"]),
 ("PC12_kill_store_gone", "0x56d6be|nop", ["A11_band_relative_writes_exactly13"]),
]

def run(text, patch=None):
    fd, path = tempfile.mkstemp(dir=os.path.join(REPO, "scripts"), suffix=".py", text=True)
    os.write(fd, text.encode()); os.close(fd)
    env = dict(os.environ)
    if patch: env["M316_PATCH"] = patch
    try:
        r = subprocess.run([sys.executable, "-u", path], capture_output=True, text=True, env=env, timeout=120)
        if "Traceback" in r.stderr:
            return None, r.stderr.strip().splitlines()[-1]
        reds = sorted(set(re.findall(r"^FAIL (\S+)  ", r.stdout, re.M)))
        return reds, r.returncode
    finally:
        os.unlink(path)

src = open(SCRIPT).read()
reds, rc = run(src)
if rc != 0:
    print("BASELINE NOT GREEN - refusing to score"); sys.exit(1)
print("baseline green:", [l for l in open(os.path.join(REPO, "evidence/m316_addgoal.txt")).read().splitlines()[-2:]].join(" ") if False else "green")

ok = 0
for name, old, new, want in MUTS:
    if src.count(old) != 1:
        print("BAD  %-28s anchor not unique (%d)" % (name, src.count(old))); continue
    reds, rc = run(src.replace(old, new))
    if reds is None:
        print("BAD  %-28s crashed: %s" % (name, rc)); continue
    if reds == sorted(want):
        print("OK   %-28s reddened exactly %s" % (name, want)); ok += 1
    else:
        print("BAD  %-28s want=%s got=%s" % (name, sorted(want), reds))
for name, patch, want in CODE:
    reds, rc = run(src, patch=patch)
    if reds is None:
        print("BAD  %-28s crashed: %s" % (name, rc)); continue
    if reds == sorted(want):
        print("OK   %-28s reddened exactly %s" % (name, want)); ok += 1
    else:
        print("BAD  %-28s want=%s got=%s" % (name, sorted(want), reds))
total = len(MUTS) + len(CODE)
print("== M316 mutate: %d/%d ==" % (ok, total))
sys.exit(0 if ok == total else 1)
