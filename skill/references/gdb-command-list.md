# Command-list traps: `dump`, `python`, convenience arithmetic, loop-entry, scan windows

Everything here kills a run the same way: the failure happens INSIDE a breakpoint's `commands` block, so
gdb aborts the sourced script and DETACHES at the FIRST hit. The log keeps an `ARMED` line plus one
`Breakpoint N at` per breakpoint and then zero events, while the turn driver still exits 0 (the detach
resumed the inferior and the round keeps advancing) — so an aborted run looks exactly like "the mechanism
never ran". Read the gdblog tail for `Error in sourced command file` BEFORE attributing a zero-event
census to the game.

## `dump binary memory` inside a commands block

Three forms, three different failures, one symptom:

- **Non-literal target** — `dump binary memory %s …` and `dump binary memory $convvar …` are both
  refused: `%s` is not a format specifier in `dump` (it is parsed as an expression, and the error is
  `Argument to arithmetic operation not a number or boolean`). Bake the ABSOLUTE path as a literal, and
  substitute it in Python with `str.replace()` on a unique token (`SNAPFILE`) — never with `%`-formatting,
  which eats the block's own `%d`/`%x` printf conversions.
- **Arithmetic range** — `dump binary memory F <start> <start> + 0x41b80 + 0x4000 - 0x94e488` aborts the
  script. Write the range as two literal addresses and compute the end address in Python.
- **`python` blocks** — `read_memory` inside a `python … end` block in a command list raises
  `OverflowError: can't convert negative int to unsigned` and aborts the same way (and the reported line
  is the block's trailing `continue`, which names nothing). Prefer the native `dump` form with literals;
  if a `python` block is unavoidable, print the exact expression that failed before arming.

One file per RUN, not per hit: a second `dump` to the same path OVERWRITES the previous snapshot, so emit
`off=` in the log line (`($n_snap - 1) * REGION_LENGTH`) and have Python `seek` to it — one blob, many
regions, no filename arithmetic in gdb.

## Convenience-variable arithmetic is 32-bit SIGNED

`set $off = ($n - 1) * (0x41b80 + 0x4000 - 0x94e488)` yields a NEGATIVE offset: the subtraction underflows
(`-9472264`), and the sign then propagates into every later `$off` — the file is written correctly while
the reader dies on `OSError: [Errno 22] Invalid argument` at `f.seek(e['off'])`. Compute every region
LENGTH and OFFSET in Python (where the arithmetic is exact), bake the result as a hex literal, and never
express a length as `end - start` inside gdb. Symptom pair to recognise: a correctly-sized blob plus a
negative field in the log.

## A breakpoint at a branch target is often INSIDE the loop body

Placing a marker at the first instruction after a conditional jump records zero hits when a guard ahead of
that jump skips the whole loop. Walk the disassembly from the jump itself: the leg's ENTRY is the jump
TARGET, and any `test reg,reg; je <loop-end>` between the entry and the body is a skip the body-address
marker cannot observe. Concretely: `0x5a9375 je 0x5a9500` enters the tail leg at `0x5a9500`, `0x5a9503`
loads a divisor and `0x5a950b je 0x5a9698` skips the loop when it is 0, so a marker at `0x5a94fd` (inside
the body) reports "the leg never ran" for a faction whose divisor is 0. Print the guard's operand at the
entry so a skip is distinguishable from a non-run.

## Scan windows: pair a scan with its enclosing call, not with its exit site

Grouping events between a function's ENTRY and its documented RETURN-site breakpoint silently drops every
scan that exits early: an early-return path (`0x5aa251`) leaves without passing the normal exit site
(`0x5aa247`), and the entry site is hit more often than the scan of interest, so most measured candidates
never land in a window and the census reports a fraction of the events it logged. Close a window at the
ENCLOSING caller's entry breakpoint or at a change of the subject (faction/owner field), and never require
an exit event to make a window valid — a gate that needs the outcome (the winner) must skip that gate for
the window, not discard the window.

## Snapshot cadence must match the state's real change boundary

A per-round snapshot is stale for a field that moves more than once per round (a divisor recomputed during
upkeep, a queue shifting on a completion): the run shows half the candidates agreeing and half violently
disagreeing, which reads like a wrong model rather than a wrong snapshot. Prove the cadence FIRST — print
the field at every measurement site (the engine prints its own operand at the merge point) and compare it
against the snapshot the model used — and if it varies inside the boundary, capture the value AT the site
instead of snapshotting at the boundary. A cross-check that passes on 6 candidates and fails on 5 is a
cadence failure, not a model failure; say which is which instead of rewriting the model.

## Derive a bit-set membership at the width the code uses

`mov al,ds:MASK; shl edx,cl; test dl,al` tests ONE BYTE of a dword global. Deriving "which indices are in
the set" from the full dword read (`0x00FF28` -> bits 3,4,6) is wrong: at shift widths 0..7 only the low
byte (0x28 -> 3,5) can ever be consulted. Take the width from the instruction's operand encoding and mask
the live value to that width before naming the members — and prefer to PRINT the engine's own test result
(the shifted operand) at the site rather than recomputing membership in the harness.

## Per-hit dump series (s146, M92)

`append binary memory <path> <start> <end>` is what makes a PER-HIT series work — `dump` truncates, so a
series of dumps leaves only the last snapshot; `append` grows the file and Python reads hit *n* at
`n * (end - start)` (compute that product in Python and bake it as the gdb-side literal, because the same
subtraction inside gdb is 32-bit signed and underflows to a negative offset). Delete the file before the
Delete the file before the run, or a previous run's snapshots shift every offset.

## Template placeholders: one token, one payload

A harness that builds its gdb script by `str.replace()` on `@@TOKEN@@` markers must give every payload
its OWN token. A token used twice in the template is consumed by the FIRST replace call, so the second
payload silently overwrites the first slot — and a leftover-token grep proves nothing, because both
copies are gone. Symptom: a `printf` whose format string received a whole command block instead of an
address list dies with `Bad format string, non-terminated '"'`, and since the error sits on the LAST
sourced line the log holds `ARMED` plus one `Breakpoint N at` per breakpoint and ZERO events, with every
breakpoint already set and the inferior already detached — an attach spent for nothing.

- Emit the script and check it in ONE call before attaching: no leftover `@@`; each `printf` line's
  `%d`/`%x` count equals its argument (comma) count; each format string still a single quoted line.
  The arity check catches a swallowed payload and a missing/extra argument at the same time.
- Count token occurrences in the TEMPLATE before substituting — exactly one payload per token, or name
  them apart (`@@BLOCKS@@` for injected command blocks vs `@@BPS@@` for the address list inside the
  message).
