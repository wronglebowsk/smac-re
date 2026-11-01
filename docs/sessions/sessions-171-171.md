# Session notes archive — sessions 171-171

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 171 (cont. 14) — M118 ACCEPTED (m118flag, PASS): bit 0x40 has NO setter and no save carries it — the second ask is inert BY CONSTRUCTION

`python3 scripts/m118_flag_never_set.py` — four independent checks, no box time:

- **A** exactly one `test BYTE PTR [..+0x94d430],0x40` in the image: **0x5aaf7f** (FUN_005aadf0+0x18f, take 0x5aaf88).
- **B** the 17 dword `or` sites at that displacement set 0x800000..0x80000000 and 0x2 — **none sets 0x40**.
- **C** the byte-bit setters are REGISTER ops (`or al,0x40`), which a dword-immediate scan cannot see: 22 such sites,
  and exactly ONE (0x4dc226) reaches a flag store — 0x4dc296 — but that store takes `eax` **reloaded from the flag**
  and masked `0xfc3fffff`, so the or'd bit never reaches the source; the derived value goes to `ds:0x99aa38` and
  **0 instructions move it back** into a +0x94d430 slot. The block is a bit TRANSLATION (source bit 0x800000 ->
  derived bit 0x40), not a setter.
- **D** bit 0x40 is clear for all 8 factions in **all 12 saves** on disk (m54b_clean + 8 autosaves + the three pokes)
  — and block A is restored 1:1 (M114), so a save carrying the bit would set it.

**Verdict: the M89 second ask cannot fire on this build and this save version.** M117's "inert on this state" is
strengthened to "inert by construction" — while the branch stays live and reachable (17 hits a turn).
Lesson recorded in the skill: a byte-field bit test/set is `test BYTE PTR [x],0x40` / `or al,0x40`; scanning only
`or DWORD PTR [disp],imm` misses every real setter (I nearly concluded "no setter" from exactly that gap).

## Session 171 (cont. 15) — M119-M123, five field questions settled from the static image (all PASS, zero box time)

`python3 scripts/field_census.py` (evidence/fields_m119_m123.log) — SUMMARY stride=PASS bit5=PASS readonly=PASS
copy=PASS dual=PASS.

- **M119 stride conflict RESOLVED.** The array at 0x984d38 is addressed with **0x30 (48 B)** at all 52 indexed sites:
  45 via `lea X,[v+v*2]; shl X,4` and 7 via `imul X,0x30`; **0 standalone `shl 4`** on a bare index. M67's "conflict"
  was a misread: the ×16 in the listing is `shl 4` applied to 3v — the tail of the ×48 computation, not a second stride.
- **M120 bit 0x20 at 0x531782 NAMED.** `test BYTE PTR [eax*4+0x94d448],0x1` at 0x531778, `je 0x5317a2` at 0x531780,
  then `or BYTE PTR [ebx+0x98adb8],0x20`: the entity-status bit is set **iff the faction-block dword at
  0x94d448+inner*4 has bit 0**. The index is `esi*2095 + edi` — 2095 dwords = 8,380 B, so the "array" is the faction
  block with the stride folded in (a second independent confirmation of 8,380 after M117).
- **M121 ds:0x98adee is READ-ONLY.** 7 `movsx` readers (0x4e499d, 0x4eeb35, 0x4f948c, 0x51ff61, 0x5a9e06, 0x5a9e5f,
  0x5aa1a6), **0 writers of any width**, and no access to the enclosing dwords (0x98ade8/0x98adec/0x98adf0). The
  "forced-pick key, live 6" therefore arrives with the LOAD — save/scenario data, not a gameplay counter.
- **M122 the 0x1c loop is a COPY, not a third stride.** 0x52b744-0x52b76a copies **0x91cb80 -> 0x98aaf8**, 28-B
  records, 24 of them ((0x98ad98-0x98aaf8)/0x1c exact), and never references 0x984d38. The two arrays merely sit in
  the same address neighbourhood.
- **M123 ds:0x94d78c is ONE dword, two addressing forms.** 72 refs: 48 `[reg+0x94d78c]`, 24 `[reg*4+0x94d78c]`, 6
  writes. All **24** array-form sites carry a 2095-scaled index (`shl 6 / add / lea *2 / shl 4 / sub`), so the *4 is
  the compiler's folded faction stride — same field, no second array (M116's law applied: read the encoding, not the
  syntax). Third confirmation of 8,380.
Instrument note: `open(p,"w").write(open(p).read()...)` truncated field_census.py to 0 bytes — read BEFORE opening for
write; the file was rebuilt from the conversation, not from a backup.
