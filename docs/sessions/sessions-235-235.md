# Session notes archive — sessions 235-235

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-234-234.md` (inserted at s292: the hot file cites only the newest archive, so without this line the older archives were orphans).

## Session 235 (2026-11-10, ANALYSE, M289 LIVE 7/7, box time) - which founder vector the recorded AI used: the AI HUB FUN_0055f650 -> FUN_004cca50 -> founder FUN_004e47d0; 7/7 live foundings on a 30-turn m54b_clean window, the 0x4408 action-dispatch leg 0, the 5a0aa0 chain entered 3x but completed 0; count 18->23 exact with 2 destroys; MERGED #241
- track_mode ANALYSE -> the M282 G5 frontier (NEXT_PROMPT pick): which founder
  vector the recorded AI used - 0x4408 vs 0x5f650 vs the 5a0aa0 chain.  Live-box
  milestone (the one open live question).  scripts/m289_founder_vector.py arms
  ONE silent breakpoint PER VECTOR at the call site unique to it (image-wide
  proof: exactly 3 call sites load FUN_004cca50, 3 load FUN_0059ec90) + the
  founder entry (ret/fac/x/y/live count) + the destroyer -1 store (0x4e515d) +
  the sweep-entry control (0x4e8d60); drives the clean save with the AI for 30
  turns (smac_play --no-orders so OUR side stays inert), then detaches and
  classifies every founder hit by the vector site that fired just before it.
- MEASURED: 7/7 founder hits ALL vec=hub (ret 0x4ccbe2 via FUN_004cca50, caller
  site 0x563d86 inside FUN_0055f650); fac 6,6,6,5,7,1,6 at (20,48)(63,51)(12,48)
  (27,19)(23,33)(27,29)(1,43); 3 "VEC chain" entries (FUN_005a0aa0->59ec90) with
  ZERO completed foundings (the faction-create path bailed each time - open
  why); 0 v4408, 0 hotkey.  Count accounting strict: 18,19,20 (+3) DESTROY
  (21), 20,21,22,23 (+4) DESTROY (24) -> box end 23, late=0.  Control: 1627
  sweep rows; driver rc 0; yama toggled and verified restored.
- REFUTES M282's static thesis ("reached live via the 0x4408 action-dispatch
  leg"): the 0x4408 path EXISTS (G5 static) but the live AI never took it in
  this window - it calls the founder through the hub's DIRECT call.
- ACCEPTANCE 1: python3 scripts/m289_founder_vector.py 30 -> rc 0, VERDICT
  MEASURED (evidence/m289_founder_vector.txt + scratch/m289_gdb_raw.log copied
  to evidence/m289_gdb_raw.log).  ACCEPTANCE 2 (independent re-walk of the raw
  log): python3 scripts/m289_accept.py -> PASS M289: 6/6 - founder vector(s):
  {'hub': 7} (evidence/m289_accept.txt).
- BONUS: the census produced a NEW golden trace evidence/trace_m289_20261110_
  071759.jsonl (30 turns, year 2150->2180, n_bases 18->23) - the first trace
  carrying 7 REAL founding (faction,x,y) events for the sim to fit.
- BOX HYGIENE (two NEW traps, both fixed in-session): (a) yama ptrace_scope=1
  blocks n100's own /proc/pid/mem reads (smac_state/accept_ready EACCES) - the
  box's working default is 0 and the census must restore the PRE-toggle value,
  not hardcode 1; (b) root-owned /tmp/acceptready* frames (left by an earlier
  sudo run) make accept_ready's freeze fail silently and it classifies a STALE
  frame (byte-identical quit-prompt ghost) - chown them back to n100.  Also:
  the reallyquit dialog dismisses via click Oops row (400,268) then OK (~319),
  Escape/Return alone looped.
- OPEN: why the 5a0aa0 chain bailed 3x; the hub's founding DECISION rule (which
  pod/tile/faction) vs B10's assumed first-unoccupied; M247; M70 x2.  Next:
  ANALYSE - fit the hub founder decision to the m289 trace.
