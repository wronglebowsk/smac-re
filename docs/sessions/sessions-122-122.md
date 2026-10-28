# Session notes archive — sessions 122-122

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 122 (2026-10-28) — M80: THE RECORD ARRAY IS 8 FACTION BANDS OF 64; FUN_00573a90'S ARG 1 IS A FACTION; indices >= 256 ARE LIVE DESIGN SLOTS

The prompt opened with "M74", but M74 is already merged (#75, NAMED M74-RESOLVED, tag `m74flag3`,
s116): this session ran the cursor's pick M80 instead.

STATIC (bytes, `python3 scratch/m71/dis.py 573a90 573b60` / `5740e0 5741a0` / `5741a0 574210`):
FUN_00573a90 `0x573aa3 mov esi,[ebp+8]` = param_1 for the whole function; scan counter lives in
`[ebp-0x18]` and stops at 0x80 (`cmp ebx,0x80` 0x573fbd); record index = counter<0x40 ? counter :
`(counter&0x3f) + param_1<<6` (0x573bc7-0x573bec); `0x574167-0x574176` computes `(i+i%64)>>6` and
`cmp eax,esi` REJECTS unless band 0 or band == esi; `0x574178-0x57417e lea ecx,[edi+edi*2];
lea edx,[edi+ecx*4]; lea eax,[edx*4+0x98ad88]` = record 0x98ad88 + idx*52; 0x574142 writes the plan
byte; `0x5741d9-0x5741e1 push 0x20; lea edx,[ebx+0x98ad88]; call 0x64c5e0` copies 32 B INTO the
record; 0x5741e9 clears record+0x1f; 0x5741f0 `and BYTE [ebx+0x98adb8],0xfd`; `0x5741fe push 0;
push eax([ebp-0x4]); push esi; call 0x572800`, and FUN_00572800's own band base is
`param_1*0xd00` = faction*64*52 (shard_014.c:17568, FUN_00572800 head).

BASELINE census (`python3 scripts/m80_band_census.py --json`, fresh m54b_clean r50, pid 4073650):
b0 0..13 (Colony Pod..Unity Foil), b1 64, b2 128..131, b3 192..194 (ours), b4 256, b5 320..325,
b6 384..386 (387 EMPTY), b7 448..449 — every band contiguous from band_start; owner byte +0x2c is
0 for 320/321/322/323/324/325 and 0x40 only on 385.

ACCEPTANCE `m80band1` PASS on ONE invocation (`python3 scripts/m80_band_sweep.py`, 2 boundaries,
5 silent breakpoints): SW573 visits 2 facs [5] idx [(5,324),(5,325)] (ebx=16848=324*52); SWENTER 2
owner=5 tid=324/325 mode=0 ret=0x574203; CLR4 2 fac=5 ebxidx=324/325 **pre=0xc1** (bit 2 already
clear — the `and ~4` was a no-op here); MARKHIGH 0; census flag-diffs {324:(0,193), 325:(0,193)};
BOUNDARY 0 hi=256,320-323,384-386,448,449 → BOUNDARY 1 hi adds **324,325**, which now read
"Impact Squad" / "Impact Rover" flags 0xc1 — they were EMPTY at window start and are the next two
free slots after 323. F573IN printed ret=0x5749a7 x6, 0x574da9, 0x575424.

CONSEQUENCES. M78's "FUN_00573a90 on indices 324/325/385/387" was never a record index in esi —
esi is the FACTION (live 5) and 324/325 are the sweep's tid argument; a census limited to 0..255
never looked at factions 4-7, which is why 128/322/323 looked like anomalies (they are factions
2/5's slots). OPEN: who writes the record's `+0x30 = 0xc1` (bits 0/6/7) before 0x5741f0
(unattributed — no breakpoint there); what bits 6/7 mean; who calls FUN_00573a90 (ret
0x5749a7/0x574da9/0x575424); why the sweep's band-walk/mark path (guard `tid<0x40 || flags&4`)
never engages for a fresh record. NEXT pick: M81 — the +0x30 bits 6/7 and the record-creation
writer. Evidence: `evidence/m80band1.gdblog`, `_seq.jsonl`, `_census.json`.
