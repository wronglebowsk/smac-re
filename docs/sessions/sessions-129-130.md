# Session notes archive — sessions 129-130

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

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
