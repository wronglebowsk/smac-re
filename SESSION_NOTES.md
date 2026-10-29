

Older sessions: `docs/sessions/sessions-127-127.md` (1 sessions). Read it only when a question reaches back before session ## Session 129.

## Session 129 (2026-10-28) - M84: WHAT MAKES 0x496ad0 RETURN +9999 (static, bytes); ACCEPTANCE m84canc1 FAIL - the cancel statement runs but the sentinel never fires

The prompt opened with "M74" again; M74 is merged (#75). M83 is unmerged (m83cw2 FAIL, branch
milestone/m83), so the ledger's pick M84 ran on milestone/m84 from main 7a69b20.

STATIC (instruction bytes): 0x496ad0 (size 3310) picks its return value at 0x497680-0x4976ff -
0x497683 `cmp DWORD [ecx+0xa774],-1` (ecx = `[ebp-0x10]` = the 24 KB buffer the caller passes at
0x418601 `lea edx,[ebp-0x5e2c]`); if -1 and 0x49768f `cmp [edx+0xa778],0` is zero -> eax =
0xffffd8f1 = +9999 (0x4976ce); if -1 and result != 0 -> eax = 0 (0x497698); if the field != -1 ->
eax = the pump return (0x497704 ff15 0x401940, negated when 0x495480's bit 0x20 is clear). The
field is written -1 in exactly TWO places in .text: **0x496a43** (inside FUN_00496950, the dialog's
message handler: `mov [eax+0xa774],-1` right after `mov [ecx+0xa778],0` - handler case 7 = CANCEL:
result 0 + armed) and 0x495541 (inside FUN_004954e0, the dialog's own setup, called once from
0x496ad0). Handler FUN_00496950 (shard_009.c:14701) cases 0/2/5 `return` when the field is already
-1; 1/3/4/6/8 set result 2/3/4/6/7. So +9999 = THE DIALOG-CANCEL SENTINEL: cancel arms the field,
the next pump return becomes +9999, and the caller's 0x41861b/0x4186d2 `cmp edi,0xffffd8f1` is what
gates the 0x270f block (M83). The SAME +0xa774 offset is the chooser's guard: m57_ui_enqueue.py
reads `0x6A9E9C + 0xa774` as the chooser cell index, so the field is one UI-object convention, not
production-specific.

ACCEPTANCE FAIL (`python3 scripts/m84_cancel_sentinel.py --tag m84canc1 --escape --no-ok`, ONE
invocation, 3 silent bps 0x41860f/0x496a43/0x497683 + M83's 0x418d7d/0x577280): ARMED ptr=0x95ef70
fac=3 pend=0 head=2; enqueue rc=0 stopped with the chooser open (guard cell index 3, pending 1);
Escape rc=0 closed it. events SENT 1 (edi=2), ARM 2 (one is the ARMED line; the real ARM printed
**buf=0** + gdb "Cannot access memory at address 0xa774" - ecx was 0 at 0x496a43), GATE 1
(buf=0x6a9e9c cancel=3 result=5), BRANCH 0, ENTRY 0 -> G1 True, G2-G7 False -> FAIL. So the
cancel-arming STATEMENT does execute during a chooser session, but the buffer instance seen at the
return gate held cancel=3 (a cell index, not -1) and the pump returned 2, not -9999.

OPEN / NEXT (M84b): the ARM breakpoint's ecx is not the buffer there (register semantics, the trap
says so) - take the buffer address from the caller's own push at 0x418601-0x41860a (bp at 0x41860a
reads [esp+0xc]) and re-run the same 5-bp shape with events ORDERED by time; the claim to falsify
is "Escape on the chooser routes through handler case 7 (0x496a43) and the next pump return is
+9999". Also open: which widget message code reaches FUN_00496950 case 7 (no direct `call` to
0x496950 exists in .text - it is reached through a widget handler table); FUN_004954e0's -1 write
at 0x495541 (setup-time arm?); who owns 0x6a9e9c.
Evidence: evidence/m84canc1.gdblog, scratch/m84canc1.gdb, scratch/m84_tmpl.py (m83's script, the
shape this reused). No new evidence dir files beyond the log (budget 27.5 MB, gate FAILs at 30).

## Session 130 (2026-10-28) — M84b: THE CANCEL SENTINEL IS LIVE (Escape -> arm -> -9999); ACCEPTANCE m84canc2 FAIL ON THE 0x270f LEG

s129's M84 sat unpushed (no PR): this session first ran `milestone.py submit` for it (PR #84; acceptance FAIL -> merge nothing), then ran the pick M84b on milestone/m84b from main 7a69b20, carrying the m84 footing forward (`git checkout milestone/m84 -- NEXT_PROMPT.md SESSION_NOTES.md NAMED.md scripts/m84_cancel_sentinel.py scripts/m57_ui_enqueue.py evidence/m84canc1.gdblog`) — an unmerged branch is the only place that footing lives.

INSTRUMENT BUGS FOUND FROM BYTES BEFORE MEASURING (all three were s129's, not the game's): B1 0x496a40 `mov eax,[ebp-0x4]`, 0x496a43 `mov [eax+0xa774],-1` — the object is in EAX; m84canc1 printed $ecx (0), gdb faulted on 0xa774, its commands block aborted and gdb DETACHED, so that run died at the ARM. B2 0x496af1 `mov [ebp-0x10],ecx` + 0x497680 `mov ecx,[ebp-0x10]` — the guard field lives on the thiscall chooser_sub the caller loads at 0x418604 `lea ecx,[ebx+0xa1c]` = 0x6a9e9c, NOT the 24 KB `[ebp-0x5e2c]` buffer pushed at 0x418601 (live CALL: buf=0xbe3984, a stack address). B3 the sentinel is NEGATIVE: printf %d prints -9999, so m84canc1's `edi == 9999` gate could never pass; every sentinel read is now the unsigned 0xffffd8f1.

ACCEPTANCE m84canc2 FAIL (`python3 scripts/m84_cancel_sentinel.py --tag m84canc2 --escape --no-ok`, ONE invocation, 6 silent bps 0x41860a/0x41860f/0x496a43/0x497683/0x418d7d/0x577280, events printed in log order; `python3 scratch/m84b_selftest.py` shows the shape discriminates — positive ALL, 6 negatives each fail >= 1 gate). Box was BLOCKED (screen 'base' -> one Escape -> hud; then its printed FIX `m57_ui_enqueue.py --base-index 18 --cell-item 2 --inserts 1` made it READY, pending 1). ORDERED: CALL obj=0x6a9e9c cancel=3 mode=0 slot=1 -> GATE cancel=3 mode=5 -> SENT edi=2 -> CALL obj=0x6a9e9c cancel=3 mode=5 slot=3 -> ARM obj=0x6a9e9c pre=3 mode=0 (the Escape; a real transition) -> GATE cancel=0xffffffff mode=0 -> SENT edi=-9999 edi_hex=0xffffd8f1. G1/G2/G3/G8 True; BRANCH 0, ENTRY 0 -> G4-G7 False -> FAIL, merge nothing.

THE FAILED LEG IS THE FINDING (bytes, not instrument): 0x41861b `cmp edi,0xffffd8f1`/`jne 0x41864c` — on -9999 the loop 0x418623-0x41863f restores the ten queue slots into base+0x50..+0x78 and 0x418649 restores pending at base+0x4c from [ebp-0x20]; 0x4186d2 `cmp edi,0xffffd8f1`/`jle 0x419967` then leaves via 0x419967 (`push 1; mov [ebx+0x3ff5c],0; call 0x416080`). RETRACT s129's "0x41861b/0x4186d2 gate the 0x270f block": the ONLY branch to 0x418d7d is 0x4187be `cmp edi,0x270f`/`je`, i.e. POSITIVE +9999, reached on the mode 5/7 paths (0x4187a2/0x4187ad) only when [ebp+0x8] != 0. So 0x577280 (sole bit-7 clearer 0x577ca8) runs on a +9999 chooser result, not on cancel. OPEN: what puts 9999 in the chooser item list / makes 0x496ad0 return +9999.
Evidence: evidence/m84canc2.gdblog, scratch/m84canc2.gdb, scratch/m84b_selftest.py (evidence 27.5 MB).

## Session 131 (2026-10-28) — M84c: THE MODAL IS A 3-VALUE CHOOSER; +9999 IS A ROW KEY NO CODE INSERTS (acceptance m84cprobe1 FAIL)

Prompt said M74 (merged #75 long ago); the repo pick was **M84c** — what makes 0x496ad0 return POSITIVE +9999 = 0x270f, the only value that enters 0x418d7d and thunks 0x577280. Branch milestone/m84c from main 7a69b20, carrying s128-s130 footing (`git checkout milestone/m84b -- NEXT_PROMPT.md SESSION_NOTES.md NAMED.md scripts/m84_cancel_sentinel.py evidence/m84canc[12].gdblog`). PITFALL: `milestone.py start` resets the tree to main, so the carried docs AND SESSION_CURSOR.md must be re-written AFTER it (mine reverted to s127's M82 line).

STATIC (instruction bytes, scratch/m71/dis.py windows): the pump 0x497704 `mov ecx,[obj+0xa774]; push ecx; add ecx,0xa780; call 0x4026b0` = SEEK the list at obj+0xa780 (0x4026b0: index > [c+0x10]-1 -> return 0; cursor=[c+8]; walk `node=[cursor+0xc]`; [c+0x14]=index), then 0x497725 `call 0x495480; and eax,0x20` — bit SET -> 0x49773a `call 0x401940` (0x401940: `[c+8]==0 -> 0` else **return [[c+0xc]+4]**) -> 0x4977ab returns eax; bit CLEAR -> 0x497777 same call then `neg eax`. So the modal's THREE value sources are: -9999 (armed, mode 0), 0 (armed, mode != 0), and +/- the +4 word (the KEY) of the seeked node. Caller: 0x41860f `mov edi,eax`, 0x418616 snapshots it to [ebp-0x10], 0x418794/0x4187a2 reload it, 0x4187be `cmp edi,0x270f`. n_callers: 0x496ad0 = 1 (0x41860a only), FUN_004954e0 = 1, and the ONLY writers of that list are 4 functions calling FUN_0042ee20 — 0x4954e0 (2 sites, key = the setup loop var), 0x42e4d0/0x42ef40 (`(&DAT_00997120,0,4,0)`), 0x4b0a80; NO caller passes 9999.

ACCEPTANCE FAIL (`python3 scripts/m84c_item_pump.py --tag m84cprobe1`, ONE invocation, 8 silent bps 0x41860a/0x42ee20/0x497704/0x4977ab/0x41860f/0x4187be/0x418d7d/0x577280): PUMP obj=0x6a9e9c idx=3 count=13 cur plus4=42 -> VAL eax=2 -> SENT 2 -> CHK edi=2 -> CALL mode=5 slot=3 -> PUMP cur plus4=2 -> VAL 2 -> SENT 2 -> CHK 2. gates G1 True G2 True **G3 False** G4 True **G5 False** G6 True G7 True; counts PUMP 2 NODE 2 VAL 2 SENT 2 INS-on-chooser-list 13 CHK 2 BRANCH 0 ENTRY 0; node+4 [2, 42]; inserted words [0,1,2,3,6,16,17,18,32,34,38,39,41,42,161,192,193,194]. G3 is MY INSTRUMENT: the NODE print sits at 0x497704, BEFORE the seek at 0x497717, so it prints the PREVIOUS cursor (fix: print at 0x49771c). G5 is the finding: the list keys are dialog category ids 0..0x2a — no 9999 item exists, so 0x418d7d/0x577280 is unreachable from the build chooser. merge nothing. OPEN: 0x4a99e0 `cmp [ebp+0x8],0x270f; jle` then `sub ecx,0x270f` + stride-0xb4c table at 0x888514 is where keys > 9999 mean something else — the next lead. Evidence: evidence/m84cprobe1.gdblog (27.5 MB).

## Session 132 (2026-10-28) — M84d: WHO CALLS 0x4a99e0 WITH A KEY > 9999 — NOT THE PRODUCTION PATH (acceptance m84dky1 FAIL, merge nothing)

Prompt said M74 (merged #75); the repo pick was M84d. Branch milestone/m84d from main, carrying
the s128-s131 footing (`git checkout milestone/m84c -- NEXT_PROMPT.md SESSION_NOTES.md NAMED.md
scripts/m84c_item_pump.py scripts/m84_cancel_sentinel.py evidence/...`).

STATIC (bytes + a live /proc/pid/mem census, before measuring). (1) THE >9999 LEG IS A PER-FACTION
CONTEXT SWITCH: 0x4a99e0 `cmp [ebp+0x8],0x270f`/`jle 0x4a9ad3`; 0x4a99fc `[this+0x1d6f0]=1`,
0x4a9a09 `sub ecx,0x270f` (stored back at 0x4a9a0f), edx=(ds:0x888514-1)*0xb4c -> 0x4a9a24
`[this+edx+0xb38]=-1`, 0x4a9a60 `call [[this+(fac-1)*0xb4c+0x80]+0xf0]`, 0x4a9a75
`[this+(key-9999-1)*0xb4c+0xb38]=2`, 0x4a9aac the same notify on the new slot, 0x4a9ac9
`call 0x4a72c0(this, ds:0x86ae40, key-9999, [this+0x1d6e0])`; records are 2892 B at this+0x80.
The <=9999 leg needs `[this+8]==4` and `[this+0x1d6dc]==ds:0x91b5b4` (=3 live) and switches on
0xcef..0xcf4, so the same argument is a message code below 10000 and an index above it.
(2) WHO OWNS IT: the dword 0x4a99e0 appears ONCE in the image, 0x67671c, inside a 197-slot pointer
run 0x676584-0x676894; 0x498ea6/0x498eac store vptr 0x67658c at [obj] and 0x676584 at [obj+0x444]
(0x498f00 `sub ecx,0x444` is the secondary thunk), i.e. primary vtable slot 100 / secondary slot
102, reached by a computed index (no `call [reg+0x190]` anywhere in .text); only 2 .text
references to that table exist, both constructors (0x498ea8, 0x49988c). A scan of every rw region
of terran.exe found ZERO objects with vptr 0x67658c/0x676584/0x67673c. (3) ds:0x888514 IS A
FACTION INDEX (live 0): 0x4a0c17 loops i < ds:0x985af4 (=19) over stride-0x130 records at 0x95da14
comparing BYTE[i] to it, and those 19 records read "University Base"(3), "Gaia's Landing"(2),
"The Hive"(2), "Morgan Industries"(4), "Sparta Command"(5), "New Jerusalem"(6), "U.N.
Headquarters"(2) ... "Korolev Center"(3) — base records with the OWNER FACTION at +0, ours = 3 =
cur_player; 0x499f13 indexes a second per-faction array the same way (`imul eax,0x20bc` over
0x94d7fc, 8380-byte records, slots 0..8 populated, slot 0 reads -1).

ACCEPTANCE FAIL — `python3 scripts/m84d_faction_key.py --tag m84dky1 --boundaries 8 --timeout 380`
(ONE invocation): gdb armed 8 silent bps (0x4a99ec entry, 0x4a9a24 OUT store, 0x4a9a60 notify-out,
0x4a9a75 IN store, 0x4a9aac notify-in, 0x4a9ab2 AFTER, plus the sibling writers 0x4a7d84 and
0x4a759f of [x+0x1d6f0]); the log shows "Breakpoint 1 at 0x4a99ec" ... "Breakpoint 8 at 0x4a759f"
and a clean "[Inferior 1 (process 29779) detached]". Driver m56_build rc=0 in 83 s: "positive
predictions 1/1 verified; boundaries 8/8" (a real production arrival). Events: keys 0, low 0,
OUT 0, IN 0, AFTER 0, notify 0/0, SETFLAG2 0, CLEARFLAG 0 -> G1..G8 all False -> FAIL, merge
nothing. So 0x4a99e0 was entered ZERO times (neither leg) in 8 boundaries and neither sibling flag
writer ran: the class is not instantiated in a normal game loop, so the >9999 vocabulary is not on
the build/production path — this closes the M84c lead (0x4a99e0 is not where 9999 means something
ELSE for the chooser).
OPEN: who calls the constructor FUN_00498e20 (n_callers=1) — that names the screen/mode that owns
this object; the dispatcher that computes slot 100; who WRITES ds:0x888514 (all 37 .text
references to it are reads — the writer is not a `mov ds:0x888514` in .text). NEXT pick: the
0x4194b3 handler / widget message 0x4d00, or ds:0x888514's writer.
Evidence: evidence/m84dky1.gdblog (36 lines), scratch/m84d/{peek,probe2,probe3}.py; evidence 28.0 MB.

## Session 133 (2026-10-28) — M84e: 0x4d00 IS A QUEUE POST, NOT A CALL; ITS HANDLER IS 0x52ed7d (acceptance m84edisp1/2/3 FAIL, merge nothing)

Prompt said M74 (merged #75); the repo pick was M84e. Branch milestone/m84e from main 7a69b20, carrying the s128-s132 footing (`git checkout milestone/m84d -- NAMED.md NEXT_PROMPT.md SESSION_NOTES.md scripts/m84_cancel_sentinel.py scripts/m84c_item_pump.py scripts/m84d_faction_key.py skill/`).

STATIC (instruction bytes only, scratch/m71/dis.py windows): (1) 0x584010 is a POST, not a dispatcher — it builds a 32-byte record on its OWN stack ([ebp-0x20]: +0 WORD code, +4 ds:0x91b5b4, +8 the 0x671368 result, +0xc ds:0x91f694, +0x10..+0x1c the sender's args 2..5) and enqueues it `push [ebp+0xc]; push 0x20; push &rec; mov ecx,0x91db70; call 0x52a260` under the re-entrancy guard inc/dec ds:0x920438. (2) the pumps pop it back: `mov ecx,0x91db70; call 0x6361ff`, `test eax,eax; je` else `push edx; push ecx; push eax; mov ecx,esi; call 0x52bce0` (16 such loops, 0x5262ff-0x526707). (3) 0x52bce0 IS the dispatcher: 0x52bd33 `mov ebx,[ebp+0x8]` = the record, 0x52bd3b `mov ax,[ebx]` = the code, 53 `cmp eax,...` arms; the ONLY 0x4d00 arm in .text is 0x52eb61 `cmp eax,0x4d00` / 0x52eb66 `jg 0x52ef74` / 0x52eb6c `je 0x52ed7d`, and 0x4194a4 (`push 0x4d00; call 0x584010`, inside the chooser function 0x417ee0) is the ONLY sender of 0x4d00 in .text. (4) the handler 0x52ed7d: eax = [rec+0x10] (the sender's arg2 = 0xffffffd9 - edi), then 0x52ed89 `lea edx,[eax+eax*2+0x75]` + shl 4 + 0x52ed97 `lea eax,[edx+0x984d38]` = 0x984d38 + a2*48 + 1872, and 1872 = 39*48 cancels the -39 sentinel -> 0x984d38 - tid*48: a THIRD stride-48 site for the M67 stride conflict. rec+0x14 (0/1/2, pushed at 0x419486/0x419473/neither) selects three sub-behaviours over 1436-byte records at 0x927590 / 0x927894 + player*1436. (5) RETRACT M70's mechanism: 0x52ed7d-0x52f756 writes NOTHING at +0x3ff5c / 0x6e93dc — 0x4194b3 `mov [ebx+0x3ff5c],0` is the instruction right after `call 0x584010` RETURNS, in the SENDER.

LIVE (`python3 scripts/m84e_msg_dispatch.py --tag m84edisp3 --base-index 0`, ONE invocation, 7 silent bps 0x4194a9 POST / 0x4194b3 ZERO / 0x4194bd ZEROAFTER / 0x52bd3e-if-$ax==0x4d00 DISP / 0x52eb6c-if-$eax==0x4d00 ARM / 0x52ed7d HND / 0x52eda4 IDX; `--tag selftest` = positive ALL, negative 6 gates False, so the shape discriminates): 7 bps armed, enqueue rc=0 "pane closed after 1 Escape(s): class hud", events ZERO obj=0x6a9480 pre=15 -> ZEROAFTER post=0: the cursor store IS live and lands (15 -> 0 read back), but POST 0, DISP 0, ARM 0, HND 0, IDX 0 -> G1-G8 FAIL. Two findings from that: (a) ebx at 0x4194b3 was 0x6a9480 = the STATIC PANE (m57's PANE_BASE_IDX base), so the cursor is a PANE-RELATIVE field +0x3ff5c = 0x6aa9dc here, not the fixed 0x6e93dc M70/M71 named; (b) the post IS CONDITIONAL — 0x419464/0x419479/0x41948e/0x419492 all jump to 0x4194b1 past 0x4194a9, so "cursor zeroed, no 0x4d00 posted" is a real path, not a miss. m84edisp1/m84edisp2 (--base-index 18) also 0 events: the INSERT clicks landed on the PANE's base (University pending 0->8->14) while m57 read base 18 and printed "INSERT 1 never landed" — a pane/target mismatch, plus a quit-prompt mid-window (the very failure normalize_screen's docstring names).
OPEN: the -39 branch that POSTS needs a chooser selection to complete (enqueue --no-ok, then close the chooser on a row) — re-run the same 7-bp instrument unchanged; the handler's mode 0/1/2 semantics (0x626634/0x6265a2 list ops over 1436-byte records at 0x927590/0x927894, builders at 0x997b28/0x99aa48, ids 0x68f4e8/0x68fc10 read as zeros in RAM); who else owns a +0x3ff5c cursor. NEXT pick: FUN_00498e20's single caller (names the mode that owns the 0x270f keys) or ds:0x888514's writer.
Evidence: evidence/m84edisp1.gdblog, m84edisp2.gdblog, m84edisp3.gdblog; scratch/m84edisp{1,2,3}.gdb (evidence 27.5 MB).

## Session 134 (2026-10-28) — M84e follow-up (bytes only): the 0x4d00 POST is GATED on ds:0x920434, the OPENING-MENU flag — s133's POST 0 is THE GAME, not the instrument

Prompt said M74 (merged #75); the repo pick was M84e, and a sibling cron session had already run it while I was briefing (milestone/m84e 592e177 + dae5049, acceptance m84edisp1/2/3 FAIL, PR #88 gate pass, merge nothing). One box: I did NOT arm a second gdb (s125/s126 collision rule) and instead verified its zero from instruction bytes.

STATIC (scratch/m71/dis.py windows, no box): the POST 0x4194a9 sits behind THREE gates inside FUN_00417ee0: 0x4193b2 `mov eax,ds:0x920434` / 0x4193b7 test / 0x4193b9 `je 0x4194b1`; 0x4193bf `mov eax,[ebp+0x8]` / `jne 0x4194b1` (arg1 must be 0); 0x4193ca `mov edi,[esi+0x50]` (= base+0x50, the queue HEAD) / 0x4193d0 `cmp edi,[ebp-0x1c]` / `je 0x4194b1` (no post when the head equals the snapshot). 0x4194b1 is the block's COMMON exit — four jumps land on it (0x4193b9, 0x4193c4, 0x4193d2, plus the ladder's 0x419462/0x419479/0x41948e/0x419492) — and it is `push 1; mov [ebx+0x3ff5c],0; call 0x4eb6b0`: the cursor zero happens WITHOUT any POST, which is exactly s133's read-back cursor 15 -> 0. Before the gates, 0x41937c-0x4193b0 walks base+0x50 for i < [base+0x4c] and `inc`s the byte at 0x94de84 + item + tid*8380 (M63's queued-count; 8380 = 0x20bc = M84d's per-faction stride), so the mutation the block performs is a queued-count bump.
WHO SETS THE GATE: `grep -n "ds:0x920434," scratch/m574/text.txt` (comma = store) lists the stores (0x50fe70, 0x50fff5, 0x510196, 0x515ad8, 0x515fb1, 0x516f30, 0x516fd4, 0x51f267, 0x52280c, 0x52289d, ...); `grep -rn -B80 "DAT_00920434 = " ghidra_out/*.c` shows every writer stores 0 (FUN_0050fea0, FUN_00522850 twice, shard_015 twice, ...) and exactly ONE stores 1 — FUN_0057ecf0 (0x57ecf0, 2639 B) at its entry, whose strings are INTRO / SCENARIO / TOPMENU / MULTIMENU / ALPHA / openinga_pcx / openingb_pcx / fx_opening_menu_wav, i.e. the opening movie + scenario/top-menu loop; it stores 0 again on exit. Live ds:0x920434 = 0 on the hud (the footing's gate globals).
CONSEQUENCE: in a loaded game the build-queue block can only leave via 0x4194b1, so POST 0 / DISP 0 / ARM 0 / HND 0 in m84edisp1/2/3 is the branch outcome, not an arming failure. The mode that owns message 0x4d00 is the OPENING MENU — the same dead-leg shape as M84d's vtable with no instance. OPEN (one variable): is FUN_00417ee0 (n_callers=10) ever entered with ds:0x920434 == 1 — poke 0x920434 = 1, mutate the queue, re-run `scripts/m84e_msg_dispatch.py` unchanged; shard_001.c:9463 `for (; DAT_00920434 = iVar2, ...)` is a variable store I did not chase.
Evidence: no new evidence file (bytes only; scratch/m71/dis.py windows 419340-41940f, 52bce0-52be60, 52ed7d-52ee10).

## Session 135 (2026-10-28) — M84f: the NETGAME gate is LIVE-measured; the poke leg is blocked by BOX STATE (m84fpath1 census, m84fleg4/5 invalid)

Prompt said M74; the repo pick was M84f (make the 0x4d00 POST leg fire). Branch milestone/m84f from main, carrying m84e's footing (instrument + docs + skill).

MEASURED (`python3 scripts/m84f_path_census.py --tag m84fpath1 --base 17 --inserts 1`, ONE invocation, 7 print-only bps + a /proc read-back): the netgame-gated block DOES run on a real UI insert — CHOOSER 2 (the 0x41860a modal call), CASE 1 (0x419355), BUMP 7 (`inc [0x94de84 + item + tid*8380]`, one per queue slot), EXIT 1 (0x4194b1), NETCALL 1 (0x528760 from 0x419368), netgame 0, pend 5 -> 6 read back. So s134's static reading is confirmed live: the block walks the queue, reaches `mov eax,ds:0x920434` at 0x4193b2 and, with the flag 0, takes `je 0x4194b1` = `push 1; mov [ebx+0x3ff5c],0; call 0x4eb6b0` — cursor zero plus a call, NO 0x4d00 post. Gates G1/G2/G3/G5 True, G4 False — G4 was MY wrong prediction ("the case never runs"); the case runs and stops AT the gate.

INSTRUMENT PITFALL (cost two runs): a MEMORY WRITE inside a gdb breakpoint command list — `set {int}0x920434 = 1` or `set var *(int *)0x920434 = 1` — aborts the batch with "Left operand of assignment is not an lvalue" at the FIRST hit and gdb DETACHES (m84fleg1/2/3: 36-line log = ARMED + 9 "Breakpoint at" lines + the error, 0 events; the driver's insert still lands because detaching resumes the inferior). The working poke is python-side: os.pwrite to /proc/pid/mem succeeds WHILE gdb is attached (m84fleg4: 632 writes, 0 errors, print-only bps logged cleanly).

BLOCKED (box state, not bytes): after `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` the game is 2150 r50 — University Base only, pend 0, credit 0, and the chooser's candidate array is EMPTY (`m57_ui_enqueue: FAIL: item 2 not in candidate array []`), so no insert can be driven; ds:0x8f0d60 is 0 until a pane opens, which killed the ARMED printf (`*(int *)($b + 0x4c)` on 0x4c -> EIO). The 2163 r63 state (chooser [192,195,194,193,2,0,1,196], Korolev pend 1) was LOST by that reload. NEXT: get a buildable state (fresh save + turns, or a later save), then `python3 scripts/m84f_post_leg.py --tag m84fleg6 --base <buildable idx> --inserts 2` — poke on odd visits, control on even, 9 print-only bps; the flag-1 arm is the only unmeasured leg.
Evidence: evidence/m84fpath1.gdblog (valid), evidence/m84fleg4.gdblog, evidence/m84fleg5.gdblog; scratch/m84f*.gdb; evidence 27.6 MB.

## Session 136 (2026-10-28) — M85: the tech/upkeep trio splits into "MP-only by design" and "reachable helper"; the live arm is blocked by the TURN TRIGGER (m85cens1 FAIL)

Static (deterministic: `ghidra_out/index.csv` addr/size_bytes + call lines in `scratch/m574/text.txt`): 0x52145e is inside FUN_00521070 (+1006), whose ONLY call site is 0x522376 — and m55_boundary.py's docstring identifies FUN_00521070 as the MULTIPLAYER 7-stage driver (mode_flags & 0x10). So the M67 "zero events" at 0x52145e is BY DESIGN in solo, not a bad breakpoint. 0x5a7d00 (+912) and 0x5a7f67 (+1527) are both inside FUN_005a7970: 47 call sites, one at 0x507e57 inside the human-turn loop FUN_0050f420 — so those zeros are an untaken branch, not unreachable code.

Live (`python3 scripts/m85_tech_census.py --tag m85cens1 --timeout 120`): FAIL — round 50 -> 50, year 2150 -> 2150, driver rc=1 ("no round boundary (year never moved) within 120.0s"), events = {ARMED: 1}. ONE VARIABLE ISOLATED: the same driver without gdb (`python3 scripts/m55_boundary.py --timeout 90`) fails identically, so the instrument is innocent — the box cannot end a turn.

Input probe (measured): game window = X id 10485761 "Sid Meier's Alpha Centauri" inside Wine desktop "smac - Wine Desktop"; state cur_player 3 (us), turn_flags 0, stage 0, round 50 — it IS our turn. Return is inert BOTH ways: XSendEvent (`xdotool key --window 10485761 Return`) and XTEST after focus (`xdotool windowfocus 10485761; xdotool key Return`) leave round/year unchanged. s132/s133 logged "one Enter fires the boundary within 0.2 s" on this box, so the trigger, not the code, changed with state. Next: CLICK the on-screen END TURN control (clicks still land — m57_ui_enqueue's do), or restore a state where Enter is the end-turn key (no unit selected).

CONFLICT recorded, unresolved: ds:0x920434 is "save_later" in m55_boundary.py's G table and "NETGAME" in the M84e/s134-135 docs. Compatible story (a chooser save-for-later mode would explain why FUN_0057ecf0 is the only 1-writer) but unproved.
Evidence: evidence/m85cens1.gdblog; scratch/m85cens1.gdb; scratch/m85diag.png (root grab, unread).

### s136 addendum — the live blocker is BOX-LEVEL INPUT FOCUS, not a driver choice

- `m85cens2` (driver switched to m44_idle, the pane-clicking turn advancer): driver rc=1 in 0 s, round 50 -> 50.
- `m85cens3` printed the child's stderr: a bare traceback, so the census is not the place to debug it.
- Run standalone, `m44_idle.py --tag m85probe --rounds 1 --budget 60` exits rc=0 and reports `reason: "1 rounds"`, but its own snapshot line still reads `[round 1] {"year": 2150 ...}` and `m85cens3_drv` (budget 420) does the same: the driver walks its loop and the YEAR NEVER MOVES.
- `xdotool getactivewindow` returns EMPTY and `windowfocus 10485761` does not change that: this X session has NO input focus at all. The game window is 800x600 at (0,0) (id 10485761, "Sid Meier's Alpha Centauri" inside "smac - Wine Desktop") and it IS rendering — mean luma 19.3, 19% of pixels > 32 in a fresh 800x600 grab — so this is not a blank window.
- Consequence: no keyboard OR pane-click path can end a turn on this box right now (keys: 6x Return inert via XSendEvent and via XTEST; clicks: m44's find_ok_bar route leaves year at 2150). s133's successful boundary runs happened while the window still had focus.
- NEXT (one command, before any boundary work): restore X focus — `xdotool windowactivate --sync 10485761` (needs a WM) or start/attach a WM, then re-check `xdotool getactivewindow` is non-empty; only then `python3 scripts/m85_tech_census.py --tag m85cens4 --rounds 1`.

## Session 137 (2026-10-28) — M85 CLOSED: the solo boundary IS live and DOES enter the helper; the M67 zeros split into "MP-only by design" + "branch not taken" (m85cens5 PASS)

Prompt said M74; the repo pick was M85 (PR #90 open, m85cens1-3 FAIL, blocker named as "no X focus").

BOX REPAIR (measured): s136's focus diagnosis was a red herring — `getactivewindow` ALWAYS errors on :99 (no WM supports _NET_ACTIVE_WINDOW); `xdotool windowfocus 10485761` sticks (`getwindowfocus getwindowname` returns the game window) and keys DO reach the game (one Escape flipped classify base->hud). But the s135-state box (2150 r50) swallowed every turn-end input: XTEST Return for 90 s did nothing, and a click on the MEASURED TURN COMPLETE center (OCR bbox (675,416); the vision tool's coords are scale-shifted — real bar y 405-427, the white box at y 484 is the recenter button) produced no confirm dialog and no round change. Cause NOT isolated (confounded: s135's 0x920434 /proc pokes, repeated gdb attach/detach, or a load artifact are all candidates). `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` restored the boundary immediately (m55_boundary fired, round 50->52).

INSTRUMENT DEFECT (why m85cens1/2/3 died): census's driver m44_idle asserts `TracerPid == 0` at entry — it cannot run under census's own gdb (m85cens4: driver rc=1 in 0 s, "AssertionError: tracer attached"); and its `--rounds 1` snapshot condition `y > last_year - 1 and not rounds` counts the CURRENT turn as a completed round, so it exits rc=0 in 0 s never having clicked. Census now drives with m55_boundary.py (no tracer assert, windowfocuses itself).

ACCEPTANCE PASS — `python3 scripts/m85_tech_census.py --tag m85cens5 --timeout 240` (ONE invocation): all six gates True; round 52->53, year 2152->2153 read back from /proc/201960/mem; EVENT COUNTS {ARMED:1, HELPER:1, ROUNDINC:1, STAGE:0, MP45E:0, H1:0, H2:0}; driver rc=0 "PASS boundary 2152->2153: player walk observed (cur_player [0,1,2,3,5,6,7])".

OUTCOME: (1) FUN_00521070 (MP 7-stage driver) never entered in a solo boundary — 0x52145e silence is BY DESIGN (G2/G3). (2) FUN_005a7970 IS entered once per boundary, eax=0, return site 0x569948 = inside FUN_0055f650 (0x55f650, 54483 B, call sites 0x50dd84/0x56cf12) — NOT the human-loop site 0x507e57 — so the M67 zeros at 0x5a7d00 (+912) / 0x5a7f67 (+1527) are UNTAKEN BRANCHES inside a live helper, not dead code (G4). (3) The round increment 0x51f320 fired once per boundary.

OPEN: which leg eax=0 takes inside FUN_005a7970 and what gates the two tails; who calls FUN_0055f650 at 0x50dd84 (round driver?); ds:0x920434 save_later-vs-NETGAME conflict still recorded (G6). NEXT pick: M86 — the helper's boundary visit: disassemble 0x5a7970 entry + the branches to 0x5a7d00/0x5a7f67, add a bp printing eax and the branch inputs, re-run census unchanged on a fresh-loaded box.
Evidence: evidence/m85cens5.gdblog (975 B), evidence/m85cens4.gdblog, scratch/m85cens5_bnd.jsonl; evidence 27.9 MB.

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

## Session 139 (2026-10-28) — M88: the per-record slot IS written by FUN_005aa880 through a pointer; a mnemonic grep and a store-list census both miss it (m88slot6 PASS 7/7)

Same Hermes session as s138 (M86/M87) continued; branch milestone/m88, commits 0cef077 -> 554deab -> cb25a0d -> e8e900b -> da4de47.

ACCEPTANCE `python3 scripts/m88_slot_watch.py --tag m88slot6 --poke-index 5 --rounds 4 --timeout 120` (ONE invocation): **VERDICT PASS 7/7** — poke slot(5)=0x957ba8 13 -> -1 (read back); STORE EVENTS on the watched address: n=1 val=-1 in FUN_005aaa20 (aaa20's own consumption, instruction 0x5aaac1 `c7 87 fc d7 94 00 ff...`), n=2 pc=**0x5aa9d3 `mov DWORD PTR [esi],ebx` in FUN_005aa880 val=36**; read-back slots(0..7)=[-1,44,13,32,5,36,32,48], final slot(5)=36 == the last attributed store's value; control watchpoint on the ROUND counter fired 4x, writer 0x51f53c `a3 fc 5a 98 00 mov ds:0x985afc,eax` in FUN_0051f320; AAA 4 hits, CALL 4 hits with kind==slot every time (idx 4 kind 3 slot 3 etc.); round 64->68.

HOW IT DIED BEFORE IT PASSED (three instrument defects, all mine, all fixed in place):
1. `m88slot1` (scripts/m88_slot_writer.py) enumerated writers by grepping the mnemonic text for `0x94d7fc` and got only the DIRECT forms (0x51038c, 0x59cfce, the -1 stores). The slot is also written through pointers built by `lea esi,[eax*4+0x94d7fc]` (0x5aa9c5 in FUN_005aa880, 0x52ae09 in FUN_0052a720 - a 4859-B field accessor with 64 callers) and stored as `mov [esi],ebx` — invisible to that grep. It poked slot(5) 8 -> -1 and read 13 back with ZERO events: outcome UNEXPLAINED. It also carried my second typo of the s138 session (0x5aacc1 for 0x5aaac1) and printed `$esi` at aaa20's entry, where esi is not arg0 yet (the load is at 0x5aaa25) - so it reported idx=41900 (= 5*8380, the caller's byte offset).
2. `m88slot2`/`m88slot3` armed `watch *(int *)0x957ba8` (and 0x94f8b8): gdb confirmed "Hardware watchpoint 4", CTRL fired, the value visibly changed - and zero events. `m88slot4` added a control watchpoint on ds:0x985afc and the mechanism fired there (writer 0x51f53c), so the watchpoints are NOT broken; what they miss is a write that happens while gdb is stopped between my poke and the game's next access - see 3.
3. `m88slot5` PASSed 6/7 and died only on my own G6, which demanded that aaa20 process THE POKED record in the window. aaa20 rotates records (slot2: 4, 6, 1; slot4: 3; slot5: none; slot6: 4 of them), so that was an assumption about the game, not a game requirement; G6 became the invariant that WAS observed - every CALL event has kind == the slot value it read (4/4 in slot2, 4/4 in slot6).

LIVE FACTS: the eight slots [0x94d7fc + idx*8380] right after a fresh m54b_clean load are [-1,3,8,22,49,8,5,48] - record 5 holds 8, which is the kind M86/M87 measured being handed to FUN_005a7970. A poke to -1 is refilled within one boundary by FUN_005aa880 (0x5aa9d3), and aaa20 stores -1 there itself at 0x5aaac1 just before it calls the helper. So the slot is a WORK ITEM ALLOCATION, not a constant: 45, 13, 36 were allocated in three consecutive windows.

OPEN (M89 pick): FUN_005aa880 has 4 callers - name them (containment of the call sites), and decide what the allocated value indexes (the 1436-byte record at 0x9275c4 + idx*1436 and the 3-entry table 0x93325c/68/74 with shorts 10/25/26 are the two candidates FUN_005a7970 reads). Evidence: evidence/m88slot1.gdblog ... m88slot6.gdblog; scratch/m88slot*.gdb.

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

## Session 141 (2026-10-28) — M90: the slot value is a TECHNOLOGY INDEX into the 89-entry table at 0x92fdd4, chosen by FUN_005aa030(faction) (m90tech1 FAIL on my own slice bug, m90tech2 PASS 8/8)

Prompt said M74; the repo pick was M90. Branch milestone/m90, commit df1acd7 -> acceptance.

BOX: brief BLOCKED twice, both printed FIXes run: (1) screen 'dialog' -> `normalize_screen()` -> hud; (2) `m57_ui_enqueue.py --base-index 0 --cell-item 2 --inserts 1` FAILED — "INSERT 1 never landed", pending stayed 0, because University Base now has minerals 0 / credit 0 (the pane left the screen 'base'; normalized again). M90 needs no queue, only boundaries, so this does not block it.

STATIC (shard_009.c:9288 FUN_0048b9a0 8514 B 1 caller; shard_015.c:22025 FUN_005aa030 554 B 3 callers; scratch/m71/dis.py windows): FUN_005ab000 is a THIN wrapper — 0x5ab047 `call 0x48b9a0` -> 0x5ab04c `mov esi,eax` -> 0x5ab0bf `mov eax,esi` -> ret; its 0xc5c frame is SEH + 4 C++ locals (destructors 0x6170f3), not a candidate array. FUN_0048b9a0's non-human leg (shard_009.c:9359) is `if ((param_2 == 0 && ((round == 0 || !(0x985b10 & (1<<param_1))) || bVar14)) && param_3 < 0) { pcVar2 = FUN_005aa030(); ...; return pcVar2; }` — call site 0x48bae4 `e8 47 e5 11 00`, landing 0x48bae9; bVar14 is NOT decoded. FUN_005aa030(faction) loops `iVar4 < 0x59` (= 89) over `(&DAT_0092fdd4)[iVar4*0xb]` (stride 44), gates candidates with FUN_005a6cd0, scores with FUN_005a90a0, tie-breaks `_rand() % (local_8+1)` (human: FUN_00625af1), keeps the max and returns the INDEX.

THE DOMAIN IS THE TECH TABLE — `python3 scratch/m90/txthex.py 262651 10 13 25 26 36 45`: the 8-byte name at +16 reads 10 Alloys, 13 Surface, 25 SingMec, 26 ConSing, 36 Integ, 45 IndAuto; all 89 names from live memory run Indust InfNet Physic Psych Mobile Ecology Super Chaos E=Mc2 Fusion Alloys ... DigSent ... User0..User9 ... TranT. Corroboration from the same records: Alloys' prereq fields are +0=30 (Solids) and +4=7 (Chaos) = SMAC's Alloy Theory <- Solid State Physics + Chaos Theory. M86's table shorts 10/25/26 are Alloys/SingMec/ConSing.

ACCEPTANCE `python3 scripts/m90_tech_choice.py --tag m90tech2 --poke-index 5 --rounds 3 --timeout 100` -> **VERDICT PASS 8/8**: 4 allocations traced to named entries in 2 rounds — fac5 val 36 'Integ' and fac7 val 32 'DigSent' (round 77), fac2 val 32 'DigSent' and fac6 val 13 'Surface' (round 79); each matched the FUN_005aa030 return printed at its landing 0x48bae9 with param1 == the faction; every store came from FUN_005aadf0 (ret 0x5aaff3); every slot read back from /proc; round 77->80, ctrl 3, a030 calls 4, CONS 3 (aaa20 consumed 48/36/32 first). `--tag m90tech1` FAILed ONE gate (G6) from my own bug — the pairing sliced `events` by the ST event's index inside `st`, so the TECH event was never in range; its data already showed the agreement (CHR printed idx_from_5aa030=22 == eax=22, A030 arg1 = 4 and 5). Fixed in place; the same slice in m89_alloc_census.py's informational column fixed too (no m89 gate used it).

OUTCOME: the per-faction slot IS the faction's next research project (tech index 0..88, -1 = none). M89's "who asks" + this "what" close the loop: aaa20 consumes the INDEX and hands it to FUN_005a7970, whose 3-entry table (Alloys/SingMec/ConSing) is exactly why M86/M87 measured WALK 3, LOOP 0. OPEN (M91): what FUN_005a90a0 scores (the cost/benefit model that picks the winner), the human leg (bVar14 + FUN_00625af1), and where the chosen tech becomes the ACTIVE project (pay-site conflict 0x4f0ca6 vs 0x4efedd still open).
Evidence: evidence/m90tech1.gdblog, evidence/m90tech2.gdblog; scratch/m90/tabscan.py, scratch/m90/txthex.py, scratch/m90tech*.out. evidence 27.6 MB.

## Session 142 (2026-10-28) — M91: scorer BASE = SUM (demand*m+1)*cost, predicted 12/12 EXACT; the pick is max-of-random-DRAWS, not max score (m91score1 FAIL 6/7 on G3)

Prompt said M74 (merged #75); repo pick M91. Branch milestone/m91, commit f078138 -> acceptance -> docs.

BOX: brief BLOCKED (pend 0), its FIX ran first (`m57_ui_enqueue --base-index 0 --cell-item 2 --inserts 1` -> pending 1 head 2); accept_ready then BLOCKED on "credit 0 <= 0" (income add gated on d0>0; printed FIX = clean reload) — M91 needs only boundaries, so the census ran on the live box (pid 262651, round 80) with NO reload.

STATIC (scratch/m71/dis.py): FUN_005a90a0(idx, fac, arg2) 0x5a921d-0x5a92ab: [ebp-0x4] = (Y14*m+1)*T4 + (Y18*m+1)*T8 + (Y10*m+1)*T0 + (Y1c*m+1)*Tc, m = 1 if arg2 != 0 else 4/2 by 0x985ac4 bit 0x200 (live SET). Costs T0/T4/T8/Tc = *(0x92fdc4+idx*44+0,+4,+8,+0xc) — that record's prereq1 is +16 (= 0x92fdd4) and its 8-char name +32 (= 0x92fdd4+16), so M90's "base 0x92fdd4" is the +16 FIELD, not the record start. Demand Y10/Y14/Y18/Y1c = *(fac*8380+0x94d810/14/18/1c). Halved at 0x5a92fd iff all four pairs inert: (Tc==0 or (Y1c==0 and bc==0)) and (T4==0 or Y14==0) and (T8==0 or Y18==0) and (T0==0 or (Y10==0 and [fac*8380+0x94e488]>=4)), bc = bit-0x10 popcount of 0x94d448 dwords 1..7. The level leg 0x5a93b3-0x5a94f2 runs ONLY when arg2 != 0 (0x5a9375 `je 0x5a9500`); a human faction skips it (0x5a931a). Tail 0x5a94fd-0x5a95f8: esi=1..62, adds byte[fac*8380+0x94e5a8+esi]*Tc over divisors keyed by byte[+0x94eda8+esi] in {7,2,0}. In FUN_005aa030: score = score*256/level (0x5aa1e4 `shl eax,8; idiv edi`; level = max FUN_005a6d40(p1,1), FUN_005a6d40(p2,1)); DRAW = _rand() % (score+1) (0x5aa217-0x5aa230, 0 when score <= 0); the scan keeps the STRICTLY greater draw (0x5aa232, best starts -999).

ACCEPTANCE `python3 scripts/m91_scorer_census.py --tag m91score1 --poke-index 5 --rounds 3 --timeout 120` (ONE invocation, 3 boundaries, driver rc=0 each): **VERDICT FAIL 6/7** — G1 poke 36->-1 read back; **G2 TRUE 12/12: predicted BASE == the engine's [ebp-0x4] at 0x5a930b** (fac5 idx 4/22/32/36/45 -> 10/26/24/15/7; fac4 idx 8/13/35/43/48/60/72 -> 4/14/3/15/5/19/11); G4 TRUE 2/2 (winner == strictly-largest draw, every draw in [0, score*256/level]); G5 TRUE (ST 0x5aa9d3 + RB 0x5aa9d5 read back); G6 TRUE (Integ 36, EthCalc 43 read from live memory); G7 TRUE (round 80->83, 2 qualifying windows, >=2 distinct bases each). **G3 FALSE: the fac4 winner 43 had final 16 while candidate 60 had 38 (draws 1838 vs 2)** — max-score is not the game's rule; fac5 agreed only by luck (36 was both max score 112 and max draw 6903).

OPEN: the tail's arithmetic (final != base at fac5 idx36 15->112, fac4 idx60 19->38, +1 at 4/22/32/43/72, unchanged where Tc==0); who writes [fac*8380+0x94e488] and the 0x94e5a8/0x94eda8 category bytes; the human leg (FUN_00625af1, bVar14); where the chosen index becomes the ACTIVE project (pay-site conflict 0x4f0ca6 vs 0x4efedd); SIBLING slot [esi+0x94d800]. NEXT: M92 — decode the tail loop, census final == base + tail on >= 2 windows with the same instrument.
Evidence: evidence/m91score1.gdblog; scratch/m91score1.gdb, scratch/m91/probe.py.

## Session 143 (2026-10-28) — M91 CLOSED: m91score5 PASS 7/7 (one invocation, fresh box, 4 AI windows, 27 candidates, 0 base mismatches)

Same milestone as s142 (branch milestone/m91, commits 95fa804 + fe55c33 + this docs commit). Two gates were MY instrument defects, both fixed in place, each fix justified by instruction bytes or event order, never by weakening a floor:
1. G3 demanded winner == max FINAL — my hypothesis, not a byte rule; 0x5aa232/0x5aa235 `cmp eax,[ebp-0x8]; jle` (esi asc 0..88, best starts -999 at 0x5aa03c) proves the engine keeps the strictly-greatest DRAW and equal draws never replace. G3 became: winner holds the max draw AND no higher-index candidate ties it.
2. G5 read RB from a {addr: last-mem} dict: slot5 was allocated twice in one window (36 then 4), the dict held only 4 -> m91score3 FAIL 6/7. Pairing each ST with the RB that follows it in the event stream (0x5aa9d5 runs right after 0x5aa9d3) is the honest pairing.

ACCEPTANCE `python3 scripts/m91_scorer_census.py --tag m91score5 --poke-index 5 --rounds 4 --timeout 120` (ONE invocation on a fresh m54b_clean load, pid 347970 r50): **VERDICT PASS 7/7** — G1 poke 8->-1 read back; G2 TRUE (every traced BASE == predicted (demand*m+1)*cost sum, m=4 via 0x985ac4 bit 0x200, halving rule; 27 candidates 0 mismatches); G3 TRUE 4/4; G4 TRUE (all draws in [0, final*256/level]); G5 TRUE 4/4 ST/RB pairs; G6 names Integ/AGrav/E=Mc2/PlaEcon/Surface read from 0x92fdd4; G7 TRUE (4 qualifying windows fac5/5/4/6, round 50->55). Windows DISPROVE max-score twice: fac5 win 22 'AGrav' final 31 vs max_final 56; fac6 win 13 'Surface' final 36 vs 63. Prior runs same session: m91score2 6/7 (G7 one AI window — box state, only fac5 had a work item), m91score3 6/7 (G5 dict bug; its 4 windows already showed G3/G4/G6/G7 True), m91score4 5/7 HARNESS DEATH: the tool's 420 s foreground cap killed the census mid-run and left Wine hung at round 92 (CTRL=0, no year move even after detach) — recovered via m54a_load --relaunch.

OPEN (M92): the tail 0x5a94fd-0x5a9698 arithmetic (final != base at 6-8 candidates/window; who writes [fac*8380+0x94e488] + the 0x94e5a8/0x94eda8 category bytes); the human leg (bVar14, FUN_00625af1); where the chosen index becomes the ACTIVE project (pay-site 0x4f0ca6 vs 0x4efedd); SIBLING slot [esi+0x94d800]. Evidence: evidence/m91score2-5.gdblog; scratch/m91score*.gdb/.out. evidence 27.6 MB.

## Session 144 (2026-10-28) — M92: the tail 0x5a9503-0x5a9698 DECODED and validated against the engine's own finals; the census harness is still not green (m92tail2-7 all FAIL)

Prompt said M74 (merged #75); repo pick M92. A sibling session had m92tail3/4 in flight on
milestone/m92; I adopted its commits (6c15d37 mine) instead of competing, then verified the MODEL
offline from committed evidence (scratch/m92/verify7.py reads evidence/m92tail7.gdblog +
scratch/m92tail7_snaps.bin + /proc — no gdb, no poke).

THE TAIL, leg by leg (scratch/m71/dis.py 5a9500 5a96a0): 0x5a9503 `mov ebx,[ecx+0x94e488]` is the
divisor, `je 0x5a9698` skips the whole loop when 0; loop esi=1..62 (0x5a9518 `and eax,0x3f` skips
esi==63, 0x5a9692 `jl 0x5a9516`). Category byte = [fac*8380+0x94eda8+esi], multiplier =
[fac*8380+0x94e5a8+esi], Tc = the tech record's +0xc (0x5a955b `imul eax,[edx+0x92fdd0]`).
CAT 7 (0x5a9536): gate `mov ecx,[ebp-0x18]; je` — [ebp-0x18] is the CALLEE's own prologue counter
(0x5a90ae zeroed, 0x5a90d6 `inc edx` per control dword [0x94d448+4*i] with bit 0x10 set, i=0..7) =
the bc the BASE print already carries, NOT a caller slot (the census never writes caller [ebp-0x18]:
FUN_005aa030 sub esp,0xc, locals -0xc..-0x4); then 0x5a9541 skips when the faction IS human; adds
`idiv mult*Tc, ebx` — divisor NOT doubled. CAT 2: mult*Tc*4 / (div*(1+human)). CAT 0: factor 4 if
[blk+0x94dc44] >= [blk+0x94dc58] else 2, / (div*(1+human)). ELSE (0x5a95fd): 0x5a960e skips the inner
loop when arg2 == the faction; edi=1..7 over GLOBAL band tables 0x950664 + edi*0x20bc (stride 844):
the edi-th table's OWN byte at +esi must be nonzero (0x5a9615 — a SECOND multiplier, not the block
byte); gate on the control dword [0x94d448+(fac+edi)*4] needing bit 0x8 set and NOT (bits 0-1 set with
bit 5 clear) (0x5a9640/45/4a, index 0x5a9628-0x5a9637 = (fac+edi)*13 dwords); adds mult*Tc/(div*2 if
human else div). The tail mutates [ebp-0x4] in place; 0x5aa159 `mov [ebp-0x4],eax` is the FINAL.

THE MODEL DISCRIMINATES, against the engine's own numbers (m92tail5 CAND line, fac7): observed finals
19/32/57/28/24/45 for bases 10/15/28/15/23/41 == base + idiv(16*Tc, 1) = the cat-7 leg with mult
[fac7*8380+0x94eda8+40] = 16 and div 1; the old model (cat-7 gated on a caller slot, band tables read
from [blk+0x2bc0+esi*32]) predicted 12322/24639/18483/6197 — off by >3 orders. m92tail7 fac3 (bc 0,
div 1, cats all 0, mults nz only at esi 0,4,24,36,40,44,48,52): finals are base + 0/1 exactly where
Tc is 0, i.e. the band legs contribute 0 because the control dwords are 0 at that round (snap0 ctrl
[0x94d448..] all zero) — the gate is real, not decorative. cats and mults hold EQUAL nonzero bytes at
the same esi (0,4,24,36,40,44,48,52 = powers of 4), values per faction (fac3 5/18/1/2/1/4/2/2,
fac5 12/10/4/3/2/4/2/1, fac7 1/6/1/1/24/1/255...).

INSTRUMENT DEFECTS found and fixed (all mine/mine-adopted, none a floor): (1) windows closed at the
ENT print 0x48bae9, which fires BEFORE the scan's BASE events -> candidates=0 in m92tail2/3/4; windows
now open at the CALL print (0x5aa030) and close at ENT/TECH (m92tail5/6/7 collect 6-13 BASE per
boundary, G2 TRUE). (2) snapshots: `dump binary memory %s ...` is invalid; a multi-line gdb `python`
block inside a bp command list aborts the sourced file ("Argument to arithmetic operation not a
number or boolean"); read_memory threw OverflowError; and an ARITHMETIC dump range with a substituted
path poisons the address expression — the range must be LITERAL (0x94e488 0xd61c88 = 8*8380), the
reader's SNAPREGION must not conflate offset with range (0x41b80+0x4000-0x94e488 < 0 -> ValueError).
(3) the TAIL print had idx/fac swapped ($esi is arg0 = the tech index, [ebp+0xc] = the faction) and
printed $edi as a mask (at 0x5a9503 edi is esi+0x950664); BASE `human=` printed $edx = 1<<fac.

OPEN (M92 continues): the census has NEVER been green — the next run needs the dump range extended to
0x94d448..0x966000 so the band gate's control dwords are per-round (they move between rounds: snap0
all 0, live at round 63+ nonzero for records 1-7), plus WHO WRITES 0x94e488 / 0x94e5a8 / 0x94eda8 /
the 0x950664 band tables (the 8 esi positions are powers of 4). Human leg (bVar14, FUN_00625af1) and
the pay-site conflict 0x4f0ca6 vs 0x4efedd still open. Evidence: evidence/m92tail2-7.gdblog;
scratch/m92/{tailcheck,verify7}.py; scratch/m92tail*.out.

## Session 145 (2026-10-28) — M92 NOT accepted: the tail is predicted from the live block (38/41 exact), the offsets were the bug and the block MOVES inside a round

Branch milestone/m92, nothing merged. Three instrument truths, each from instruction bytes or measured adds:
1. category byte `[eax+esi+0x94eda8]` and multiplier `[eax+esi+0x94e5a8]` with `eax=fac*8380` are at
   **+0x920 / +0x120** from 0x94e488 — the +0x1000/+0x1860 I used read zeros and produced the 12312 tails.
2. `0x94dc44`/`0x94dc58` are **BEFORE** the block (+0x7fc/+0x810 from 0x94d448) and the cat-0 factor is
   **2 when [0x94dc44] >= [0x94dc58], else 4** (0x5a95be setge / dec / and 2 / add 2) — inverted in the
   s144 note, which is why fac 2 read 16 where the engine added 8.
3. **The divisor moves INSIDE a round** (fac6 snapshot 1 live 6; fac2 8 live 9), and so can the category
   byte: take the divisor from the TAIL record (read at 0x5a9503 for that candidate), the arrays from the
   round snapshot.
MEASURED, not modelled: the four add sites (scratch/m92probe_adds.gdb) show ONE term per candidate,
`mult*Tc*4/div`; `TAILOUT` at 0x5a9698 is the tail output, and `final` (0x5aa159) is a **POST-tail leg**
on top of it (+1, +29 at r76) — gating on `final` conflated two legs.
ACCEPTANCE `scripts/m92_tail_census.py --tag m92tail14 --poke-index 7 --poke-extra 2,6 --rounds 4
--timeout 100` (fresh load, 41 candidates, 6 scans): **FAIL 5/8** — 41/41 divisors and TAILOUTs clean,
**3 wrong** (fac 5: model Tc, engine 2Tc = a category byte that moved after the snapshot). Replaying the
same snapshots offline with the fixed model: **38/41 exact (m92tail14), 5/5 (m92tail12)**.
NEXT: append the two arrays AT the score (0x94e488+fac*8380+0x120 and +0x920, 128 B at the TAIL hit) so
the last 3 go exact; then the post-tail leg 0x5a9698 -> 0x5aa022.
Evidence: evidence/m92tail9-14.gdblog, m92adds1.gdblog; scratch/m92adds.py, m92probe_adds.gdb.

## Session 146 (2026-10-28) — M92 ACCEPTED: m92tail18 PASS 8/8. The tail rule is exact 39/39; the block is FROZEN within a round and the stale reads were WINDOWS, not the block

Branch milestone/m92. ACCEPTANCE `python3 scripts/m92_tail_census.py --tag m92tail18 --poke-index 7
--poke-extra 2,6 --rounds 4 --timeout 100` (ONE invocation on a fresh m54b_clean load, r51->55):
**VERDICT PASS 8/8** — G3: TAILOUT(0x5a9698) == BASE + simulated tail on **39/39 traced candidates, 0
mismatches, 2 qualifying windows (fac2 win=44 IndEcon nz5/splits5, fac5)**; G8: divisor cross-check
39/39 proven, round +4, TAIL events for the scored factions. Naive one-factor model splits on 19
candidates (the shape discriminates).

THREE HARNESS DEFECTS found and fixed (mine, none a floor) — each one had been reported as a game
finding, which it was not:
1. `c["tdiv"]` was NEVER assigned although G8 reads it -> **G8 was structurally False in every run**
   (m92tail14/15/16/17 all failed it regardless of the game).
2. `tailout[(fac,idx)]` was LAST-wins while the model used the FIRST scan: a re-scan in a later round
   has a different block, so m92tail16's 4 "mismatches" (idx8 tailout 29 then 39) were pairing scan-1's
   model with scan-4's output. tailout + tailbyidx are now FIRST-wins.
3. windows are opened by a CALL and can span rounds (no WIN/ENT close), and the census simulated every
   candidate from the WINDOW's CALL-round snapshot. Candidates now carry their OWN live round (the
   BASE print reads *(0x985afc) at the hit) and are simulated from THAT round's snapshot.

RETRACTION (this session, from the new instrument): **the category/multiplier arrays and the divisor do
NOT move inside a round.** The TAIL hit now appends 64 B mults (0x94e5a8+fac*8380) + 64 B cats
(0x94eda8+fac*8380) per candidate (scratch/<tag>_tailarrs.bin, hit-ordered); compared to the
candidate's own round snapshot: **0/39 (m92tail15) and 0/19 (m92tail17) differ**, and
divisor_cross_check_proven == 39/39 bad=0 (m92tail15/18). So s145's "the divisor moves inside a round
(fac6 snapshot 1 live 6)" and "3 misses = a category byte that moved after the snapshot" were defects
2/3 above, not block motion. The block DOES move BETWEEN rounds (m92tail16: fac2 mult(esi1) 4->5 at
r56, dc58 1->2 at r57 and 2->4 at r58 -> the cat-0 factor flipped 2->4) — which is exactly what the
per-candidate round stamp now tracks.

BOX: brief BLOCKED twice (screen 'dialog' -> normalize_screen() -> hud; credit 0 -> the printed reload
recipe m54a_load --relaunch -> m54g_prep -> smac_play --turns 1 -> m57_ui_enqueue --base-index 18
--cell-item 2 --inserts 1 -> READY). m92tail17 (r59, a degraded box) scanned only 3 factions -> 0
qualifying windows -> FAIL 5/8: the census needs a FRESH load (8 factions queued); the acceptance was
re-run as m92tail18 on a reload, not weakened.
NEXT (M93): the POST-tail leg 0x5a9698 -> 0x5aa022 (the SCORE at 0x5aa159 minus TAILOUT: +1/+29 at
r76, +155 for fac2 idx8 in m92tail15/18 — final 186 vs tailout 31). Evidence:
evidence/m92tail15-18.gdblog; scratch/m92tail1[5-8].out, scratch/m92tail18_snaps.bin + _tailarrs.bin.

## Session 148 (2026-10-29) — M93 NOT accepted: the POST ladder predicts 9/13; 4 apply sites have no breakpoint, the specials' within-round freeze is unproven

Branch milestone/m93. ACCEPTANCE `python3 scripts/m93_post_census.py --tag m93post2 --poke-index 7
--poke-extra 2,6 --rounds 4 --timeout 100` (fresh m54b_clean load, r50->55): **FAIL 8/9** — G1-G8 all
green (base 27/27, tail exact on 40 candidates, divisor cross-check 40/40 bad=0, 2 qualifying windows
fac2/fac5, ST/RB + winner name read back), **G9_post_tail_ladder_final False: 13 candidates predicted,
4 mismatches; splits vs the final==tailout null 11, vs the final==tailout*5 null 13.**

THE POST LEG 0x5a9698-0x5aa022, from instruction bytes: ebx = idx reloaded at 0x5a969b; the leg is
SKIPPED (return = tailout) when `[0x985c1c+idx]` carries the faction bit (0x5a96e0); else `call
0x5312d0` — it returned 0 for all 82 traced candidates in both runs — and only if nonzero the
ds:0x985a9c leg may ×4 (0x5a9738 `lea edi,[ecx*4]`). Then a cascade, each stage applying iff idx is IN
its set = {a hard-coded tech} ∪ {prereq-ancestors of a LIVE special}: A(47, 0x9305e8/ec) ×3, B(61,
0x930850/854) ×2, C(64, 0x9308d4/8d8, depth 2) ×2, D(35, 0x9303d8/3dc, depth 1) ×2, E(59, 0x9307f8/7fc)
×2, FIM ((demand[0x94d81c]+1)×2; needs rec+4 bit 1, no faction knowing idx, ac4 bit 0x200 clear), G
(0x98582c) ×2 only when [0x927a8c+fac*1436] > 0, else the 0x93325c/0x933268 legs (×2, ×2, +1 at
0x5a99cc `inc edi`, then ×2 at 0x5a9a21 when ac4 bit 0x200 clear), q = [blk+0x94dc28]/clamp
([blk+0x94e488],1,0x270f) added once when q > demand[0x94d81c] and idx is in the closure of
0x984fec/0x984fbc/0x98531c/0x98534c, **0x5a9c17 ×2 keyed on 0x9851cc and 0x5a9c68 ×3/2 keyed on
0x9851fc (both only when [0x927a80+fac*1436] > 0) — NEITHER is in the model**, the 21-entry era table
0x92b954 (flag byte at -4; idx == id → ×3/×4, idx == pr1/pr2(id) → ×2/×3), 0x5a9df3 ×3 over the
89-tech scan, 0x5a9eb5 ×2 (×4 human) keyed on 0x98adee, then the 0x92b076 exit gate and the band scan
0x5a9f83-0x5aa022 (×3/×6 at 0x5aa004, ×2+4 at 0x5aa01b — 0 events in 82 candidates).
`0x5a9020(a, X, d)` = a == X or a is a prereq-ANCESTOR of X within d levels.

RETRACTION: the s146 ledger line "the 0x5aa022 block makes final = TAILOUT*5" is WRONG — the ×3/×2
epilogues never ran; the ×5-looking deltas are the cascade (×2+1, ×2×2, ×3 then ×2).

MISMATCH CAUSES, both model/instrument and not the game: (1) fac2 idx44 (19->39) and fac5 idx13
(28->56): the engine applied an ×2 the model has no leg for (the missing 0x5a9c17/0x9851cc leg), and 4
apply sites have NO breakpoint — 0x5a9c17, 0x5a9c77, 0x5a9df3, 0x5a9eb5. (2) fac5 idx4 (model 21,
engine 11) and idx45 (model 14, engine 7): the MODEL fires PE2 where the engine did not — and note the
`fired=` list on a LADDER-MISMATCH line is the model's own prediction, not observed events. Likely
cause: the model reads the specials from the candidate's ROUND-BOUNDARY snapshot while the ladder reads
them live mid-round; M92 proved the within-round freeze only for the 0x94e488 block, NOT for the
0x9307xx specials.

NEXT (M93 continues): add the 5 apply-site breakpoints (gdb blocks ready in scratch/m93/apply_patches.py
at 0x5a9c14/0x5a9c74/0x5a9df0/0x5a9eb5/0x5a9f83), add the 0x9851cc/0x9851fc legs and the
0x98531c/0x98534c q-gates, print the specials at the PENTRY hit (live timing) instead of the round
snapshot, re-run. Evidence: evidence/m93post1.gdblog (run-1 trace, 6 scans / 41 candidates),
evidence/m93post2.gdblog (the failing acceptance); scratch/m93post2.out, scratch/m93/{analyze1,
analyze2}.py. Box: fresh load r50->55, census ran, nothing queued at U. Base.
