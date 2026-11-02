# Session notes archive — sessions 193-193

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 193 (2026-11-01, M242 — the save WRITE function; static first, then ONE box lifecycle; S192/M241's notes live on the open PR #180)

- **Static, zero box time** (`scripts/fn.py`, `scripts/name_global.py`, `scratch/m71/dis.py` windows on
  `ghidra_out/shard_015.c`): `FUN_00597ce0` (363 B) IS the writer — `FUN_0063c610(path, ds:0x692fa0)`
  open (return 1 at 0x597dcf), `FUN_00570640(s_TERRAN ds:0x692fa4)` magic, `FUN_0064c9a0(&local_c=0x56,
  4,1)` version, `FUN_00596850(handle, 1)` body, 4-byte timeGetTime, `FUN_0064c730` fclose, and
  `FUN_0064d710(path)` DELETES the file on any failure code. `FUN_00596850` is ONE codec both ways:
  0x59686b stores param_2 to `DAT_00926a0c`, every leg is `cmp/je` → `call 0x64cc00` (read) else
  `call 0x64c9a0` (write) — 30 write / 28 read sites, plus 28+28 swap siblings `0x596470`/`0x596540`
  gated on `DAT_00985ae8 & 0x10000000`. The writer's 8 call sites: 0x521697 (turn-loop autosave, 10
  insns after the "Writing save file" push at 0x521688), 0x52221e, 0x598c73 (UI Save browser),
  0x59a121/0x59a166/0x59a1bc, 0x59a372, 0x59bf46.
- **Acceptance** `sudo -n python3 scripts/m242_save_write.py` → `PASS M242: 5/5 gates`, rc 0, invocation
  2 (invocation 1 filled every gate then died in `tally()`: the ENCODEC line had no address token —
  fixed in 60a2afb, nothing weakened). `evidence/m242_save_write.txt` has both invocations. G1
  host-statted saves A 242,799 B mtime +11.2 s / B 242,799 B +4.5 s, each inside its own window; G2 131
  bps armed, zero insert warnings, TracerPid 0 after detach; G3 `ENT 597ce0 p=00bef174
  path16='Z:\home\n100\rev'` ×1 reached through exactly one armed site, `0x598c73`; G4 codec entry
  mode=1 swap=0, header leg `W 596883 dir=1 dst=0x985ab8 sz=796 n=1`, **23 hits at 23 of 30 write sites
  vs 0 at 28 read sites, 0 swap** (M109 measured 23 of 28 read sites on a load — the same legs are
  conditional both ways); G5 TERRAN + version 86 at file 8 + the live 796-B block verbatim at offset 12
  + year 2153 mem==file, on BOTH saves.
- **Corrections:** SAVE_FORMAT.md's "796 B at offset 0" → the block is at file offset **12** (8-byte
  `TERRAN\0\x1a` + 4-byte version 0x56 precede it), so its read-order table is also the write-order
  table. M241's premise is dead: the writer never touches 0x99aa38 — though `FUN_005985e0` does store
  +1c/+20 (advisor-text substitution) on the UI route.
- **Open:** which 7 write legs are dead and by which gate; the write-side sites OUTSIDE 0x596850 (M109:
  93,159 B of a load is issued by 105 sites outside it); `FUN_0059a0c0`/`0x59a2b0`/`0x59bec0` unnamed.
  #180 (M241) stays open, superseded by this answer. Box: one lifecycle, no relaunch, TracerPid 0.
- **Pitfall:** a census parser must give EVERY logged line an address token — mine crashed in tally()
  after the measurement was already complete, wasting an acceptance invocation.
