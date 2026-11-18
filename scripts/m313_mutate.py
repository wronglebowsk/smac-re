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
    ("MU4_pumpA_swap", "\"FUN_0050bea0\", \"FUN_0050c170\", \"FUN_0050cab0\", \"FUN_005103b0\",\n        \"FUN_00510730\", \"FUN_00510bd0\", \"FUN_00511960\", \"FUN_00512450\"],\n        \"pumpA", "\"FUN_0050bde0\", \"FUN_0050c170\", \"FUN_0050cab0\", \"FUN_005103b0\",\n        \"FUN_00510730\", \"FUN_00510bd0\", \"FUN_00511960\", \"FUN_00512450\"],\n        \"pumpA", "A4a_pumpA_band_callees"),
    ("MU5_pumpB_swap", "\"FUN_004e10c0\", \"FUN_0050c170\", \"FUN_0050cab0\", \"FUN_005103b0\",\n        \"FUN_00510730\", \"FUN_00510bd0\"],\n        \"pumpB", "\"FUN_004e10c0\", \"FUN_0050c170\", \"FUN_0050cab0\", \"FUN_005103b0\",\n        \"FUN_00510730\", \"FUN_0050bb20\"],\n        \"pumpB", "A4b_pumpB_band_callees"),
    ("MU6_pumpA_callers", "[\"FUN_0041bda0\", \"FUN_004c5d60\"]", "[\"FUN_0041bda0\", \"FUN_004c5d61\"]", "A4c_pumpA_callers"),
    ("MU7_mapclick_swap", "\"FUN_004739a0\", \"FUN_0050bde0\", \"FUN_0050ca10\", \"FUN_0050cab0\",", "\"FUN_004739a0\", \"FUN_0050bde0\", \"FUN_0050ca11\", \"FUN_0050cab0\",", "A4e_mapclick_band_callees"),
    ("MU8_hubsite_swap", "pa_hub == [0x51319E, 0x5137CF, 0x51562D, 0x51567D, 0x5163D4, 0x5164A5,", "pa_hub == [0x51319E, 0x5137CF, 0x51562E, 0x51567D, 0x5163D4, 0x5164A5,", "A4f_pumps_contain_hub_sites"),
    ("MU9_slot415", "slot(415) == 0x5F6AA3", "slot(415) == 0x5F6AA4", "A5a_vtable_slots"),
    ("MU10_slot0", "slot(0) == 0x422310", "slot(0) == 0x422311", "A5a_vtable_slots"),
    ("MU11_vdigest", "vsum == \"f2e2c9dfae9ba011\"", "vsum == \"f2e2c9dfae9ba012\"", "A5b_vtable_digest"),
    ("MU12_tab_base", "(0x512BA7, 0x5165CC), (0x513219, 0x516628)", "(0x512BA7, 0x5165C8), (0x513219, 0x516628)", "A6a_pumpA_tables"),
    ("MU13_drop_tab", ", (0x516096, 0x516A6C)],", "],", "A6a_pumpA_tables"),
    ("MU14_tabB_swap", "(0x517CBB, 0x5185C4), (0x518007, 0x5185E8)],", "(0x517CBB, 0x5185C4), (0x518008, 0x5185E8)],", "A6b_pumpB_tables"),
    ("MU15_cmd_sz", "slots_between(0x5165CC, 0x516628) == 23", "slots_between(0x5165CC, 0x516628) == 24", "A6c_command_table_size"),
    ("MU16_vk_sz", "slots_between(0x516628, 0x516698) == 28", "slots_between(0x516628, 0x516698) == 27", "A6d_vk_table_size"),
    ("MU17_letter_sz", "slots_between(0x5181D0, 0x518204) == 13", "slots_between(0x5181D0, 0x518204) == 12", "A6e_letter_table_size"),
    ("MU18_hits_expect", "hits == [0x51892E]", "hits == [0x51892F]", "A7_pumpB_entry_callback_registration"),
    ("MU19_init_owner", "calls_to(0x518820)}) == [\"FUN_00580260\"]", "calls_to(0x518820)}) == [\"FUN_00580261\"]", "A7_pumpB_entry_callback_registration"),
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
