# Session notes archive — sessions 175-175

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 175 (2026-10-31) — cap triage (#153, merged), then M188-M190 all PASS (static batch of three, one instrument)

- **CAP TRIAGE first, as its own PR (#153):** `NEXT_PROMPT.md` measured 15,466 chars (> the 15,300 triage
  line), so the settled era was SPLIT not shaved — the s171-s174e milestone lines moved verbatim to
  `docs/pick-archive.md` §the s171-s174e milestone lines, the footing keeps one archive pointer + the M181
  lead: 15,466 -> 14,003 chars. The same PR fixed the gate's `skill sync` FAIL: the tracked `skill/` copy
  was CONTENT-STALE in 4 files (70,000-BYTE cap wording, NEXT_PROMPT char-vs-byte cap, batch-DOC-cost rule,
  numbers-as-assertions law, bit-leg census + per-site argument-tuple laws). `git log -S<string> -- skill/`
  returns NOTHING for each, proving the live copy was the newer side — it was rsynced INTO the repo, not the
  reverse.
- **Acceptance (ONE invocation, rc 0):** `python3 scripts/m188_m190_uses.py` -> `evidence/m188_m190_uses.txt`
  (11,794 B) -> `SUMMARY M188a=PASS M188b=PASS M188c=PASS M189a=PASS M189b=PASS M190a=PASS M190b=PASS
  M190c=PASS`. Two earlier invocations died on MY parser, not the game: a `%`-format with 7 specs and 2 args
  (traceback rc 1), and `is_store_dest` missing objdump's `dword ptr ds:` spelling (undercounted stores -> 3
  gates FAIL, and 23/27 RMWs invisible until the byte-op bit shift was fixed). No floor was edited.
- **M188 — the entry count is private bookkeeping.** FUN_0053a9c0 entry: `edx=ds:0x920720`, `eax=ds:0x9204ac`,
  `add eax,edx` -> `[ebp-4]` at 0x53a9dc, +1 ONLY when `ds:0x920720 != 0` (test 0x53a9da / je 0x53a9df / inc
  0x53a9e1 / re-store 0x53a9e2). 43 mentions of `[ebp-4]` = 11 reads + 10 re-stores + 8 inc + 11 dec + 2
  reg-arithmetic; ZERO `push [ebp-4]`, ZERO scaled/index forms; 11/11 reads are consumed by arithmetic or
  cmp/test on the register and NONE reaches a call, so the sum is never forwarded; 4 windows name the rank
  field 0x94d434, the round counter 0x985afc or 0x920720 — the ±1 steps are rank/round-conditioned.
- **M189 — FUN_004e0260 writes 3 non-spill places** (staging pair `ds:0x99aa1c`/`ds:0x99aa20`, and
  `[block(fac)+0x0] = ds:0x999fa4` at 0x4e0336) + 1 spill to `[ebp-4]`; everything else leaves through 4
  emitter calls (0x626634 x2, 0x626581, 0x626ec4); its loop walks 7 records at stride 0x59c = 1436 B (359
  dwords) while ebx walks the 0x20bc = 8380 B faction blocks (0x94f70c + i*8380). **FUN_005a2930 writes
  NOTHING**: 0 stores, 5 tests, exactly 5 callees (0x4d9fb0/0x4b6060/0x4b5f90/0x5844f0/0x5a1950), the last
  reached only when `ds:0x920434` reads 0.
- **M190 — 23 of the 27 "plain mov" stores at 0x94d448 are the store half of a REGISTER-level bit RMW of the
  same field**, which qualifies M186's "ZERO bit-setters" (true only of memory-operand `or/and [..+disp],imm`):
  `or al,0x40` (0x552ce4), `or ecx,0x40020` (0x55487f), `or esi,0xc0020` (0x554d42) SET; `and edx,ecx` with
  ecx=0xffffffdf at 4 sites and `and al,0xbf` CLEAR. Sets union 0xe0c60, clears union 0x8513aee7. Of the
  0x40030 mask: 0x20 set at 2 / cleared at 4, 0x40000 set at 2 / cleared at 0, and **0x10 is never set or
  cleared by any of the 27** — it arrives only via the 4 whole-value assignments (0x52b9c7/0x52b9d0 load
  `[ebp-0x50]`/`[ebp-0x4c]` in FUN_0052a720; 0x55540a/0x55580f store `lea`-built ADDRESSES).
