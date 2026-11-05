# Session notes archive — sessions 194-194

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 194 (2026-11-01, M243 — the 7 dead write legs of the save codec and their gates; static, zero box time)

- **Acceptance:** `sudo -n python3 scripts/m243_leg_gates.py` → `PASS M243: 4/4 gates` (one
  invocation) → `evidence/m243_leg_gates.txt`.
- **Instrument:** the codec's CFG from `scratch/m574/text.txt` (1500 insns, 359 blocks),
  forward-interpreted under the LIVE state read from `/proc/<pid>/mem` (`ds:0x926a0c`=1 mode,
  `ds:0x926a14`=0 swap, `ds:0x985dbc`=9, `ds:0x985af0`=72 units, `ds:0x985af4`=18 bases,
  `ds:0x985ae8`=0x2). Guards are evaluated, edges the state falsifies are pruned, and each dead leg
  is attributed the pruned edges that are NECESSARY for it (full-CFG reachability with that one edge
  removed). The dead set comes from two COMMITTED box logs — no new box time:
  `evidence/m242_b.gdblog` (a save: 23 of 30 write sites hit) and `evidence/m109c4.log` (a load: 23
  of 30 read sites hit).
- **G1** the two logs agree on the SAME 7 legs — dead write `596927 596976 5969cb 596af5 597203
  597384 59762f`, dead read `59692e 59697d 5969d2 596afc 59720a 59738b 597636` (twins by index) ⇒
  state gates, not mode gates. **G2** the model marks exactly those 7 unreachable and reaches all 23
  measured-hot legs (37 pruned edges). **G4** `242799-149640 = 242539-149380 = 93159` — the codec
  moves 93,159 B less than the file in BOTH directions, so the dead legs are not hidden bytes; the
  7 dead legs' static sizes total 67,716 B, which is why no save is ever that much bigger.
- **G3, 7/7 named gates, 3 families.** (1) `0x5968b6 je 0x5969f0` on `and eax,0x10000000`
  (ds:0x985ae8=0x2, swap bit CLEAR): region 0x5968bc-0x5969d7 is the swap-only region and the three
  PLAIN legs inside it are unreachable in *both* swap states — 0x596927 (0x91f750, 3296 B), 0x596976
  (0x92046c, 4 B), 0x5969cb (0x92fc50, 192 B) are unreachable code either way. (2) version<3 legacy:
  0x596a4a `cmp ds:0x985dbc,3`, 0x597165 `cmp eax,ebx` (eax=9), 0x5972d1 `cmp ds:0x985dbc,ebx`
  (ebx=3, propagated from `mov ebx,0x3` at 0x59715e) — these legs serialize a scratch buffer
  malloc'd by `call 0x5be090` (0x596ab2 push 0xe5e0 = 58,848; 0x59733c push 48·n): 0x596af5 58,848 B,
  0x597203 1,664 B, 0x597384 48·n = 3,456 at n=72. (3) feature bit: 0x5975ed `test ds:0x985ae8,0x10`
  (live 0x2) → 0x59762f writes the 256 B at 0x991698 only when that bit is set.
- **RETRACTION:** the codec has **30** `call 0x64cc00` read sites, not 28 — M242's armed list missed
  `0x5979f8`/`0x597a19`, which the M109 load DID execute. Symmetry restored: 30 write / 30 read, 23
  hot each way, the same 7 dead each way. NAMED's M242 row corrected.
- **Pitfalls (into the skill's instrument-laws.md):** `test reg,reg` + `je` is TAKEN when the result
  is ZERO — opposite polarity to `cmp`, so a model reading `je` as "nonzero" routes every leg wrong;
  `and`/`or`/`add` are flag-SETTERS, not clobbers (as clobbers they make the swap gate unresolvable);
  a call clobbers only eax/ecx/edx — ebx/esi/edi survive it, which is what makes the handle and the
  loop constants resolvable across legs.
- **OPEN:** who writes the 93,159-B tail outside the codec — the codec's handle-carrying callees are
  the only candidates (0x596fb7 `FUN_005821e0`, 0x596fd0 `FUN_00582260`, 0x5972af `FUN_00571380`,
  0x597970/0x597991 `FUN_00596620` push `esi`=handle), since every codec leg is now accounted;
  roles of `FUN_0059a0c0`/`0x59a2b0`/`0x59bec0`. #180 (M241) still open. Box untouched (no gdb, no
  ptrace; `/proc/mem` reads only).
