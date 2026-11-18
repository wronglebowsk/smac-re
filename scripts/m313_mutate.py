#!/usr/bin/env python3
"""M313 mutation harness: every mutant rewrites exactly one literal in
scripts/m313_event_map.py and must redden EXACTLY its named gate (rc!=0 with
that gate FAIL, no crash). Baseline must be green or the run refuses."""
import os, re, subprocess, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "scripts", "m313_event_map.py")
src = open(SRC).read()
env = dict(os.environ, PYTHONPATH=os.path.join(REPO, "scripts"))

def run(text):
    fd, path = tempfile.mkstemp(suffix=".py",
                               dir=os.path.join(REPO, "scripts"))
    os.write(fd, text.encode()); os.close(fd)
    try:
        p = subprocess.run([sys.executable, "-u", path], capture_output=True,
                           text=True, env=env, cwd=REPO, timeout=300)
        return p.returncode, p.stdout + p.stderr
    finally:
        os.unlink(path)

# (id, old literal, new literal, gate that must go red)
MUT = [
    ("MU1_band_lo",  "LO, HI = 0x50BB20, 0x5175B4", "LO, HI = 0x50BB30, 0x5175B4", "A3a_band_hub_owners"),
    ("MU2_band_hi",  "LO, HI = 0x50BB20, 0x5175B4", "LO, HI = 0x50BB20, 0x5175C0", "A3b_band_thunk_owners"),
    ("MU3_drop_site", "0x47373E: \"FUN_004736e0\",", "", "A1_thunk_callers_exact"),
    ("MU4_drop_hub_site", "0x5175FA, 0x58C066,", "0x5175FA,", "A2b_hub_sites_exact"),
    ("MU5_pumpA_inb_swap", "\"FUN_00510730\", \"FUN_00510bd0\", \"FUN_00511960\", \"FUN_00512450\"]\n       and a_off", "\"FUN_00510730\", \"FUN_0050bb20\", \"FUN_00511960\", \"FUN_00512450\"]\n       and a_off", "A4a_pumpA_callees_split"),
    ("MU6_pumpA_off_swap", "a_off == [\"FUN_004736e0\", \"FUN_004738f0\", \"FUN_004739a0\", \"FUN_004e10c0\"]", "a_off == [\"FUN_004736e0\", \"FUN_004738f0\", \"FUN_004739a0\", \"FUN_004e10c1\"]", "A4a_pumpA_callees_split"),
    ("MU7_pumpB_inb_swap", "b_in == [\"FUN_0050c170\", \"FUN_0050cab0\", \"FUN_005103b0\", \"FUN_00510730\",", "b_in == [\"FUN_0050c170\", \"FUN_0050cab0\", \"FUN_005103b0\", \"FUN_00510731\",", "A4b_pumpB_callees_split"),
    ("MU8_pumpA_callers", "[\"FUN_0041bda0\", \"FUN_004c5d60\"]", "[\"FUN_0041bda0\", \"FUN_004c5d61\"]", "A4c_pumpA_callers"),
    ("MU9_mapclick_swap", "mc_in == [\"FUN_0050bde0\", \"FUN_0050ca10\",", "mc_in == [\"FUN_0050bde0\", \"FUN_0050ca11\",", "A4e_mapclick_mesh_callees"),
    ("MU10_hubsite_swap", "pa_hub == [0x51319E, 0x5137CF, 0x51562D", "pa_hub == [0x51319E, 0x5137CF, 0x51562E", "A4f_pumps_contain_hub_sites"),
    ("MU11_door_entry", "word(0x6724A8) == 0x41BDA0", "word(0x6724A8) == 0x41BDA1", "A5a_run_entries_by_address"),
    ("MU12_4c_entry", "word(0x67290C) == 0x5F6AA3", "word(0x67290C) == 0x5F6AA4", "A5a_run_entries_by_address"),
    ("MU13_run_digest", "rsum == \"f2e2c9dfae9ba011\"", "rsum == \"f2e2c9dfae9ba012\"", "A5b_run_extent_digest"),
    ("MU14_run_extent", "n == 490 and rsum", "n == 491 and rsum", "A5b_run_extent_digest"),
    ("MU15_cmd_bound", "(0x512B9A, (\"cmp\", \"eax,0x39\"))", "(0x512B9A, (\"cmp\", \"eax,0x38\"))", "A6a_switch_heads"),
    ("MU16_map_addr", "(\"mov\", \"cl,BYTE PTR [eax+0x5165ec]\")", "(\"mov\", \"cl,BYTE PTR [eax+0x5165ed]\")", "A6a_switch_heads"),
    ("MU17_T1_swap", "T1 == [0x512BC9, 0x512BDB, 0x512BB7", "T1 == [0x512BC9, 0x512BDB, 0x512BB8", "A6b_cmd_jump_targets"),
    ("MU18_T2_default", "T2 == [0x513220, 0x51330D, 0x51331C, 0x51322F]", "T2 == [0x513220, 0x51330D, 0x51331C, 0x513230]", "A6c_vk_jump_targets"),
    ("MU19_T3_swap", "0x516EE7, 0x516F6B],", "0x516EE7, 0x516F6C],", "A6d_letter_jump_targets"),
    ("MU20_layout", "0x5165CC + 4 * len(T1) == 0x5165EC", "0x5165CC + 4 * len(T1) == 0x5165E8", "A6e_table_map_layout"),
    ("MU21_hits_expect", "hits == [0x51892E]", "hits == [0x51892F]", "A7a_pumpB_entry_refcount"),
    ("MU22_push_instr", "ins[0x51892D] == (\"push\", \"0x5186b0\")", "ins[0x51892D] == (\"push\", \"0x5186b1\")", "A7b_push_site_verified"),
    ("MU23_init_owner", "calls_to(0x518820)}) == [\"FUN_00580260\"]", "calls_to(0x518820)}) == [\"FUN_00580261\"]", "A7b_push_site_verified"),
]

def main():
    rc, out = run(src)
    if rc != 0:
        print("BASELINE NOT GREEN - refusing to score"); print(out[-800:]); return 1
    print("baseline green")
    bad = 0
    for mid, old, new, want_gate in MUT:
        assert old in src, "%s: literal not found" % mid
        mut = src.replace(old, new, 1)
        assert mut != src
        rc, out = run(mut)
        crashed = "Traceback" in out
        reds = {m.group(1) for m in re.finditer(r"^FAIL (\S+?):", out, re.M)}
        ok = rc != 0 and reds == {want_gate} and not crashed
        print(("OK   " if ok else "BAD  ") + mid + " -> " + want_gate +
              ("" if ok else " reds=%s%s" % (sorted(reds), " (crash)" if crashed else "")))
        if not ok: bad += 1
    print("== M313 mutate: %d/%d ==" % (len(MUT) - bad, len(MUT)))
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
