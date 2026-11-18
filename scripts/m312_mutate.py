#!/usr/bin/env python3
"""M312 mutation harness: re-introduce, one at a time, the defect each named
gate exists to catch; require that EXACTLY its named gate reddens and nothing
else crashes. Baseline must be green first; a mutant carrying a traceback is
rejected (rc==1 is also what an exception returns)."""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SRC = os.path.join(HERE, "m312_goal_callers.py")
OUT = os.path.join(REPO, "evidence", "m312_mutate.txt")

# (id, gate name that MUST redden, (anchor, replacement) applied to the source)
MUTS = [
    ("MU1_span", "A1_spans",
     ("F_25A: 544", "F_25A: 672")),
    ("MU2_dropped_direct_site", "A2_calls_470b90",
     ("(0x4719C7, F_15D),", "")),
    ("MU3_swap_callee_order", "A3a_fe0_callee_order",
     ("ORDER = [0x46A1B0, 0x4710A0", "ORDER = [0x4710A0, 0x46A1B0")),
    ("MU4_fe0_arg_slot_written", "A3b_fe0_argpair_never_written",
     ('    ins, _order = E.parse_text()',
      '    ins, _order = E.parse_text()\n    ins[0x471010] = ("mov", "DWORD PTR [ebp+0xc],eax")')),
    ("MU5_tail_guard_je_retarget", "A4a_fe0_tail_guard",
     ('    ins, _order = E.parse_text()',
      '    ins, _order = E.parse_text()\n    ins[0x471054] = ("je", "0x471091")')),
    ("MU6_forwarder_pushes_1", "A4b_all4_forwarders_pass_literal0",
     ('    ins, _order = E.parse_text()',
      '    ins, _order = E.parse_text()\n    ins[0x472140] = ("push", "0x1")')),
    ("MU7_x_store_missing", "A5a_slot_store_sets",
     ("0x471898, 0x47198B]", "0x471898]")),
    ("MU8_y_minus3_gone", "A5b_y_two_laws_all4",
     ('    ins, _order = E.parse_text()',
      '    ins, _order = E.parse_text()\n    ins[0x47166F] = ("nop", "")')),
    ("MU21_y_delta_gone", "A5b_y_two_laws_all4",
     ('    ins, _order = E.parse_text()',
      '    ins, _order = E.parse_text()\n    ins[0x47195B] = ("nop", "")')),
    ("MU22_x_store_not_result", "A5f_every_x_store_is_a_469010_result",
     ('    ins, _order = E.parse_text()',
      '    ins, _order = E.parse_text()\n    ins[0x47198B] = ("mov", "DWORD PTR [ebp-0x10],edx")')),
    ("MU9_bitmask_changed", "A5d_0x2000_pregate_skips_all3_direct_sites",
     ('    ins, _order = E.parse_text()',
      '    ins, _order = E.parse_text()\n    ins[0x471837] = ("and", "eax,0x4000")')),
    ("MU10_422060_gate_retarget", "A5e_loop_site_gated_on_FUN_00422060_nonzero",
     ('    ins, _order = E.parse_text()',
      '    ins, _order = E.parse_text()\n    ins[0x4719B8] = ("jne", "0x47196b")')),
    ("MU11_block_table_wrong", "A6a_block_law",
     ('    ins, _order = E.parse_text()',
      '    ins, _order = E.parse_text()\n    ins[0x4725C3] = ("mov", "ecx,DWORD PTR ds:0x91b5c4")')),
    ("MU12_setl_dropped", "A6b_sweep_call_args",
     ('    ins, _order = E.parse_text()',
      '    ins, _order = E.parse_text()\n    ins[0x4725D2] = ("nop", "")')),
    ("MU13_cursor_list_wrong", "A7a_thunk_encoding",
     ("[edx*4+0x91b5f0]", "[edx*4+0x91b5f4]")),
    ("MU14_fanout_bound", "A8a_fanout_law",
     ('    ins, _order = E.parse_text()',
      '    ins, _order = E.parse_text()\n    ins[0x47377B] = ("cmp", "DWORD PTR [ebp-0x4],0x9")')),
    ("MU20_this_pointer_law", "A8a_fanout_law",
     ('    ins, _order = E.parse_text()',
      '    ins, _order = E.parse_text()\n    ins[0x4737BE] = ("mov", "ecx,DWORD PTR [ebp-0x4]")')),
    ("MU15_direct_store_filter_blind", "A8b_entry0_store_and_zero_indexed_stores",
     ('    stores_tbl = sorted(a for a, (b, ops) in ins.items()',
      '    stores_tbl = sorted(a for a, (b, ops) in ins.items() if True) #MUT\n    _dead = sorted(a for a, (b, ops) in ins.items()')),
    ("MU23_indexed_store_mnemonic_blind", "A8b_entry0_store_and_zero_indexed_stores",
     ('if b == "mov" and firstop(ops).endswith("*4+0x7cdecc]"))',
      'if firstop(ops).endswith("*4+0x7cdecc]"))  #MUT')),
    ("MU16_hub_arm_address_off_by_one", "A9a_hub_arms_full_window",
     ('(0x47334C, "mov", "ecx,DWORD PTR ds:0x985ae8"),',
      '(0x47334D, "mov", "ecx,DWORD PTR ds:0x985ae8"),')),
    ("MU24_hub_mask_nulled", "A9a_hub_arms_full_window",
     ('    ins, _order = E.parse_text()',
      '    ins, _order = E.parse_text()\n    ins[0x473352] = ("nop", "")')),
    ("MU25_hub_setl_nulled", "A9a_hub_arms_full_window",
     ('    ins, _order = E.parse_text()',
      '    ins, _order = E.parse_text()\n    ins[0x473459] = ("nop", "")')),
    ("MU17_hub_owner_count", "A9b_hub_53_sites_28_owners",
     ("n281 == 53 and len(grp) == 28", "n281 == 53 and len(grp) == 29")),
]

def run(text, tag):
    path = os.path.join(REPO, "scratch", "m312_mut_%s.py" % tag)
    with open(path, "w") as f:
        f.write(text)
    env = dict(os.environ, PYTHONPATH=os.path.join(REPO, "scripts"))
    p = subprocess.run([sys.executable, "-u", path], capture_output=True, text=True,
                       env=env)
    os.remove(path)
    return p

def main():
    src = open(SRC).read()
    base = run(src, "base")
    lines = ["== M312 mutation harness =="]
    if base.returncode != 0:
        print("\n".join(lines + ["BASELINE NOT GREEN - refusing to score", base.stdout[-400:]]))
        return 1
    lines.append("baseline: green (rc=0)")
    ok = 0
    for mid, gate, (anchor, repl) in MUTS:
        if anchor not in src:
            lines.append("%-38s ANCHOR-MISS (%r)" % (mid, anchor[:40]))
            continue
        mut = src.replace(anchor, repl, 1)
        p = run(mut, mid)
        if "Traceback" in p.stdout or "Traceback" in p.stderr:
            lines.append("%-38s REJECTED (crash, not a red gate)" % mid)
            continue
        fails = set(re.findall(r"FAIL (\S+?):", p.stdout))
        if fails == {gate}:
            ok += 1
            lines.append("%-38s reds %s" % (mid, gate))
        else:
            lines.append("%-38s WEAK/WRONG (reddened: %s)" % (mid, sorted(fails) or "none"))
    lines.append("%d/%d mutations reddened their target checks" % (ok, len(MUTS)))
    txt = "\n".join(lines) + "\n"
    print(txt, end="")
    with open(OUT, "w") as f:
        f.write(txt)
    return 0 if ok == len(MUTS) else 1

if __name__ == "__main__":
    sys.exit(main())
