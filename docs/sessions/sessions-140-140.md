# Session notes archive — sessions 140-140

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 140 (2026-10-28) — M89: the slot value is FUN_005ab000's return; FUN_005aadf0 asks for one the moment the slot is negative (m89alloc1 PASS 8/8, m89alloc2 PASS 8/8)

Prompt said M74 (merged #75); the repo pick was M89. Branch milestone/m89 from main d4b54cc.

BOX: the brief said BLOCKED (pend 0) — the FIX ran first: `python3 scripts/m57_ui_enqueue.py --base-index 0 --cell-item 2 --inserts 1` -> pending 0->1, head=2, slots=[2,2,0,0,0,0]. No relaunch was needed: 5aadf0 -> aaa20 is a per-base upkeep tail (M88's own PASS ran on this box at r64-68).

ACCEPTANCE, two invocations, both green:
`python3 scripts/m89_alloc_census.py --tag m89alloc1 --poke-index 5 --rounds 3 --timeout 100` (pid 262651, round 68, slots(0..7) [-1,44,13,32,5,36,32,48], save 0): **VERDICT PASS 8/8** — poke 36->-1 read back; 2 allocations, both stores 0x5aa9d3 `mov [esi],ebx`: (slot5 0x957ba8 val 36 round 68 ret 0x5aaff3) and (slot2 0x951974 val 36 round 69 ret 0x5aaff3); chooser line for each eax=36; ctrl=3 aaa=1 cons=1 a2st=0; round 68->71; /proc read-back slot5=36, slot2=36 (the only later write to slot2 is aaa20's own -1 at 0x5aaac1, which is in the log).
`python3 scripts/m89_alloc_census.py --tag m89alloc2 --poke-index 5 --rounds 3 --timeout 100` (round 71): **PASS 8/8**, 1 allocation (slot5 val 36 ret 0x5aaff3), chooser `CHR n=1 eax=36 args=(5,0,-1,0) fac=5`, inferior read-back mem=36, round 71->74 (boundary 3 driver rc=1 while the round still moved — the harness race, not a gate).

MECHANISM (scratch/m71/dis.py 5aaf00 5ab000): FUN_005aadf0's tail is the answer to "who and when" — 0x5aafcf `mov eax,[esi+0x94d7f8]; jl 0x5aaffc`, 0x5aafda `mov eax,[esi+0x94d7fc]; test; jge 0x5aaffc` (NO ask while the slot is >= 0), 0x5aafe4 `cmp DWORD PTR ds:0x926bd4,1; je 0x5aaffc`, 0x5aafee `call 0x5aa880` -> 0x5aaff6 `mov [esi+0x94d7fc],eax` (the caller stores it too). It is the SAME invocation whose aaa20 call (0x5aaf46) consumed the slot: run1's faction-2 order AAA(2) ret 0x5aaf4b -> CONS(slot2, kind 13) -> ENT(2) ret 0x5aaff3 -> CHR -> ST(slot2, 36) is that path, in that order. Inside FUN_005aa880 nothing is invented: 0x5aa892 `je 0x5aa9a5` (save 0 -> live leg), pushes 0/-1/0/edi, 0x5aa9ac `call 0x5ab000`, 0x5aa9b3 `mov ebx,eax`, 0x5aa9c5 `lea esi,[eax*4+0x94d7fc]`, 0x5aa9d3 stores. G5 (stored == chooser return) held 3/3.

WHAT THE VALUE IS NOT: `python3 scratch/m89/recname.py 262651 36 44 13 32 5 48 45 192 193 196` — 36, 44, 32, 48, 45 name NOTHING at 0x98ad88+id*52 (empty, cost 0), while 13 Unity Foil, 5 Supply Crawler, 3 Transport Foil, 8 Mind Worms, 10 Locusts of Chiron are real ANY-faction units (owner 0xff00). So 36 is NOT a global type-record id. Every observed value (3,5,8,13,22,32,36,44,45,48,49) is < 50 and 0x5aaf10 compares the slot against 0x59 = 89, so the domain reaches >= 89. FUN_005ab000 reserves a 0xc5c-byte local (0x5ab018 `sub esp,0xc5c`), calls 0x489fd0 on it, then re-pushes its four args to 0x48b9a0 — a candidate scan, not a constant. CONFOUNDED: factions 5 and 2 allocated the SAME 36 in one window, so per-faction uniqueness is NOT established.

INSTRUMENT DEFECT fixed in place: the first m89alloc1 attempt died before arming — my site_line treated the objdump section header `00401000 <.text>:` as an instruction line (ValueError); fixed to require `^[0-9a-f]{6,8}:\t`. Run 1 also printed the chooser args shifted by one (esp+4..esp+16 = arg2..arg4 + the saved edi); labels corrected to esp..esp+12 before run 2, which reads (5,0,-1,0).

OPEN (M90 pick): what FUN_005ab000's scan selects and what the 0..89 domain is (10/25/26 are the values FUN_005a7970's table 0x93325c/68/74 accepts); the SIBLING slot [esi+0x94d800], which 5aadf0 fills from FUN_005aab70 (0x5aaf67 stores -1, 0x5aaf79 stores eax, 0x5aaf02 calls the same provider); and the band flag [esi+0x94d430] bit 0x40, tested at 0x5aaf7f and cleared at 0x5aafb1 before 5aadf0's second aaa20 call at 0x5aafbb.
Evidence: evidence/m89alloc1.gdblog (49 lines), evidence/m89alloc2.gdblog; scratch/m89alloc*.gdb/.out. evidence 27.5 MB.
