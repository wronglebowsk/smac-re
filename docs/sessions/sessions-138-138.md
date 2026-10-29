# Session notes archive — sessions 138-138

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 138 (2026-10-28) — M86: the boundary's leg in FUN_005a7970 is the TABLE MISS; both bit-set tails are gated out upstream (m86cens1 FAIL, m86cens2 FAIL)

Prompt said M74 (merged #75); the repo pick was M86. Branch milestone/m86, commits edc6371 -> 0d78e3e.

STATIC (scratch/m71/dis.py windows over scratch/m574/text.txt): FUN_005a7970(arg0, arg1, arg2); [ebp-0x10] = 1 << arg0 written at 0x5a7a69 (0x5a7a55 mov eax,1 / 0x5a7a5a mov ecx,edi / 0x5a7a5c shl eax,cl) so arg0 is a FACTION BAND index (8 bands x 64, M80). Leg ladder: 0x5a7e00 `0f 84 77 11 00 00 je 0x5a8f7d` (round==0 exits), 0x5a7e0d `jne 0x5a8f7d` (ds:0x926bcc != 0 exits), then a 3-entry table walk (0x93325c/0x933268/0x933274, stride 0xc, live shorts 10/25/26): 0x5a7e73 `0f 85 26 01 00 00 jne 0x5a7f9f` — the 64-record band loop (esi = band*3328 + i*52 over 0x98ad88, ebx = tid = band*64+i, 0x5a7f90 cmp ecx,0x40) runs ONLY when arg1 == that entry's short. In the loop: call 0x573a90 -> eax; 0x5a7f48 `je 0x5a7f83` skips eax == ebx (self); gate 0x5a7f4a = `74 1d je 0x5a7f71` on ds:0x920434 then `74 10 je 0x5a7f71` on ([ebp-0x10] & ds:0x985b10); only then 0x5a7f67 `or BYTE PTR [eax*4+0x98adb9],0x1` = type record 0x98ad88 + (eax/13)*52 + 0x31 bit 0 (bit 8 of the +0x30 flag word). Else leg 0x5a7f71 calls 0x572800 then 0x4ef540. Twin block 0x5a7cd7-0x5a7d1c, same gate (0x5a7ceb/0x5a7cf8), same OR at 0x5a7d00.

LIVE cens1 `python3 scripts/m86_helper_legs.py --tag m86cens1 --timeout 300`: ENTRY 1 (eax=0 a0=5 a1=8 a2=0 ret=0x5aaad0), E13 1 (round already 51, [edx+0x94d78c]=10, +0x94d790=0, +0x94d798=0), ALT 3, LOOP 0, GATE1/2 0, OR1/2 0, ELSE1/2 0; round 50->52 year 2150->2152; save(0x920434)=0, table shorts [10,25,26], human mask 8. a1=8 matches NO entry -> jne every time -> band loop unreachable -> both tails gated out BEFORE their own gate. cens1 FAILed on my own G4/G5, which demanded loop-tail hits the game cannot make.

LIVE cens2 (same script + WALK/DOWN/FD1) `--tag m86cens2 --timeout 300`: driver rc=0 "PASS boundary 2152->2153: player walk observed (cur_player [0,1,2,3,5,6,7]), upkeep income read for 8 factions, research advanced", round 52->53, but ENTRY 0 and every helper counter 0 — the clean boundary did NOT enter the helper. RETRACT s137's "entered once per boundary" (cens1's hit came in a 2-boundary window whose driver accounting FAILED).

OPEN: what triggers the call — candidates the [edx+0x94d78c/90/98] counters the prologue bumps, load-time record re-init, or round-10/25/26 events (the table shorts are round-like). The tails' own operands were read live and fail independently: 0x920434 = 0 and (1<<5)=0x20 & 0x08 = 0. Evidence: evidence/m86cens1.gdblog, evidence/m86cens2.gdblog; scratch/m86cens*.gdb. evidence 27.5 MB.

### s138 addendum — M87: the caller of FUN_005aaa20 IS FUN_005aadf0, on the FIRST boundary after a fresh load, carrying a stored kind 8 (m87trig2 PASS)

Branch milestone/m87 (merged milestone/m86's docs forward), commits 24b2d89 -> 2ffc923 -> merge.

ACCEPTANCE `python3 scripts/m87_aaa20_trigger.py --tag m87trig2 --rounds 4 --timeout 120` (ONE invocation, right after `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch`): **VERDICT PASS, all 8 gates True** — AAA 1 (a0=5 ret=0x5aaf4b), NET 0, LIVE 1 (faction 5, slot 8, save 0), KIND 0, CALL 1 (faction=5 kind=8 slot_pre=8), EXIT 1 (eax=0), HENTRY 1 (a0=5 a1=8 a2=0 ret=0x5aaad0), WALK 3 (table short 10 vs arg1 8), LOOP 0, ALT 3; round 50->52 read back from /proc/250234/mem; attribution ret=0x5aaf4b -> site 0x5aaf46 -> **FUN_005aadf0**, bytes `5aaf46: e8 d5 fa ff ff call 0x5aaa20`; branch bytes 0x5aaa6d/0x5aaa76/0x5aaaa8/0x5aaab7/0x5aaacb/0x5a7e73 all resolved. `--tag m87trig1` (identical run, same numbers) FAILed ONE gate only because my BRANCH constant was typed 0x5aaccb instead of 0x5aaacb — a letter, not the game.

STATIC (`scratch/m71/dis.py 5aaa20 5aab65`): aaa20(arg0=faction): edi = faction*191 so [edi+0x94d7fc] is a PER-FACTION SLOT (stride 191 dwords = 764 B); ebx = [ecx*4+0x9275c4] = the 1436-byte faction record (stride 359 dwords); 0x5aaa63 `mov eax,ds:0x920434` / 0x5aaa6d `je 0x5aaaa0` (live save=0 -> LIVE leg), 0x5aaa6f `cmp ds:0x926bd4,1` / 0x5aaa76 `jne 0x5aaaa0`; 0x5aaaa0 `jge 0x5aaabd` uses a stored slot AS-IS (KIND 0 -> FUN_005aa880 never ran); 0x5aaabd pushes (faction, slot, 0), 0x5aaac1 stores -1 into the slot, 0x5aaacb calls the helper. FUN_005aadf0 (528 B) has ONE call site: 0x4f35cb inside FUN_004f34b0 (298 B, 1 caller).

CONFOUNDED, not causal: both windows that produced an AAA hit ended with driver rc=1 "FAIL boundary accounting" and a 2-round jump (50->52); the clean single-boundary windows (m86cens2, rc=0) produced no AAA. Two variables moved together.

OPEN (M88 pick): who calls FUN_004f34b0, and what writes faction 5's slot = 8 during a fresh load (the kind FUN_005a7970 then refuses, because its table holds 10/25/26). Evidence: evidence/m87trig1.gdblog, evidence/m87trig2.gdblog; scratch/m87trig*.gdb. evidence 27.5 MB.
