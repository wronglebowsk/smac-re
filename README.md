# SMAC Reverse Engineering

Static + dynamic reverse engineering of Sid Meier's Alpha Centauri (`terran.exe`, 32-bit PE,
run under Wine) to recover exact game rules: production, minerals/energy economy, growth,
unit orders, map format, UI behavior.

## What is tracked

- `*.md` — findings and living documentation. Start with `NEXT_PROMPT.md` (current footing
  and the next queued milestone), then `SESSION_NOTES.md` (dated milestone log),
  `NAMED.md` (verified addresses / function registry), `ALPHA_RULES.md`, `FINDINGS.md`.
- `scripts/` — the live-driving harness (`m*_drive.py` gdb+Wine drivers, `smac_state.py`,
  `fn.py`, boot/OCR helpers).
- `evidence/` — gdb watch logs, run logs, screenshots cited by line number from the notes.
- `data/` — parsed rules data (`alpha.json`) and extracted tables.

## What is deliberately NOT tracked

- Game binaries and assets (`programs/`, `terran.exe`, `smac.iso`, `*.cvr`, `*.flc`, saves) —
  copyrighted, and unnecessary: point the harness at a local install.
- `glsmac/` (upstream clone, own repository).
- Regenerable artifacts: `ghidra_out/`, `ghidra_proj/`, `flc_out/`, `png/`, scratch dumps.

## Method

Dynamic proof under Wine: gdb attaches only while the game is idle (`TracerPid: 0`), sets
watchpoints/breakpoints on verified addresses, and the driver advances turns through the UI
with colour/OCR-based clicks. Every claim in the notes is either VERIFIED (disassembly +
live log lines) or marked INFERRED/OPEN.

## Working in this repo

One milestone per branch, landed as one PR. Start any session with:

```bash
python3 scripts/milestone.py brief    # state, open PRs, queued milestones
python3 scripts/milestone.py start M51a
python3 scripts/milestone.py submit   # commits, pushes, opens the PR
python3 scripts/milestone.py merge 12
```

`scripts/gate.py` is the mechanical merge gate (no binaries, size limits, docs checkpoint,
evidence citations resolve, skill copy in sync). It runs locally and in CI. Protocol:
`AGENTS.md` (short) and `docs/WORKFLOW.md` (full).
