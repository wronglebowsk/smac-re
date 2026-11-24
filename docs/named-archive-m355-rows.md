# NAMED.md `## M293` - ROTATED VERBATIM (byte-exact) by scripts/m355_named_rotate.py
<!-- block: every byte below is the original NAMED.md block -->
sha1 e548f949cfd953c8705381d58b80455a17948a11  rows 6

## M293 (s240, CORRECTION, MERGED #250) - three verified Greptile P1s fixed; two registry claims retracted
- D1 hub dispatch (the M290/B13 correction above; bytes re-derived from the
  disasm cache): msg block [0x563d4e,0x563d7d] entered ONLY by the esi==0 +
  flag!=0 fallthrough - no branch in .text targets it from outside
  (scripts/m290_hub_decision.py:160, G4 = real CFG parse: branch table
  0x563d40->0x563e48, 0x563d48->0x563dfa, 0x563d57->0x563d82,
  0x563d7d->0x56c925, 0x563e04->0x563e12; [ebp-0xa4] single writer
  0x55f6d6, producer chain 0x55f6b0/0x55f6c0/0x55f6c6/0x55f6cd/0x55f6d1
  bytes asserted). The OLD G4 sliced its own address table at
  0x563d4e..0x563d81 - vacuous (the founder je-target 0x563d82 abuts the
  end). ACCEPTANCE: python3 scripts/m290_hub_decision.py
  programs/saves/m54b_clean.SAV evidence/m289_gdb_raw.log
  evidence/trace_m289_20261110_071759.jsonl -> PASS M290: 9/9
  (evidence/m290_hub_decision.txt:33). 3 runs; runs 1-2 were the
  instrument (byte transcription; in-block skip), floors never cut.
- D1b read-only /proc probe (pid 4087359, TracerPid 0): ds:0x920434=0,
  ds:0x91b5b4=3, ds:0x9208f8=0 -> the msg leg is UNREACHABLE in this solo
  save; name of 0x920434 OPEN (scenario/multiplayer gate?).
- D2 sim/hubfound.py:94 legs (distant/msg/found): ACCEPTANCE
  python3 -m sim.selftest --b13 programs/saves/m54b_clean.SAV -> PASS
  B13: 12/12 (evidence/b13_hubfound.txt:4).
- D3 guards >=0x1000000 -> >=0x400000 in m284_dialog_dispatch.py:246,
  m285_chooser_dispatch.py:185, m286_reallyquit_dispatch.py:181,
  m287_menu_dispatch.py:279; M284-M287 live claims now carry INVALID
  banners in their blocks. Static closure (0 direct callers of
  FUN_005f6aa3, create/key-path containment) UNAFFECTED.
- D4 sim/selftest.py:177 (run_save): walk() returns (rows, notes) and
  prints nothing - the old redirect+splitlines()[-1] raised IndexError
  every run (the except caught only SystemExit). ACCEPTANCE
  python3 -m sim.selftest --sav programs/saves/m54b_clean.SAV -> PASS
  B2: 7/7 (evidence/s240_b2_run.txt:2 "21 sections, 0 problems").
- Cites per AGENTS.md:50 (path:line) added to every claim touched here.
