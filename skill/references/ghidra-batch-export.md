# Ghidra batch export (whole binary → greppable C on disk)

> Reconstructed 2026-10-22 after accidental skill deletion; canonical sources are the live
> project files (`ghidra_scripts/ExportAll.java`, `COVERAGE.md`, `ROADMAP.md` §Ghidra).

## Why

One interactive Ghidra session costs ~205 s import + round-trips per question. One export makes
the entire decompiled corpus greppable with `grep`/`sed` instead.

## What it produces

- `ghidra_out/index.csv` — one row per function: `addr,name,size,insns,callers,...`
- `ghidra_out/shard_NNN.c` — decompiled C, 250 functions per shard, each block prefixed with
  `// ==== NAME @ ADDR size=N` so you can slice a single function with sed/awk
- `ghidra_out/MANIFEST.txt` — export stats

Corpus as of 2026-10-20: **10,284 functions, 100% decompiled, 2.48 MB of C, 42 shards.**

## Script

`ghidra_scripts/ExportAll.java` (GhidraScript, category `SMAC`). Env knobs:

- `SMAC_EXPORT_DIR` (default `~/reverse/smac/ghidra_out`)
- `SMAC_MAX_SECONDS` (default 5400) — hard budget; the script stops cleanly and reports

Progress goes to stdout as `progress <n> <name>` (captured by `analyzeHeadless`).

## Invocation shape

```bash
$GHIDRA/support/analyzeHeadless ~/reverse/smac/ghidra_proj smac \
  -import ~/reverse/smac/programs/terran.exe \
  -postScript ExportAll.java -scriptPath ~/reverse/smac/ghidra_scripts \
  -deleteProject
```

## Using the corpus

- `python3 scripts/fn.py 0xADDR` — slice one function's pseudocode out of the shards
- `grep -n "==== FUN_004f26e0" ghidra_out/shard_*.c` — locate, then read forward
- Ghidra is good for control flow and field offsets; it **loses register provenance**
  (`unaff_ESI`, `unaff_EDI`). For register-level questions use the gdb recipe in SKILL.md.

## Pitfalls

- `-deleteProject` keeps the 66 MB project from accumulating; the export dir is what you keep.
- Re-export after changing the analysis (x86 32-bit, no aggressive options) or offsets drift.
- Shard line numbers change between exports — cite `addr` + function name in notes, not lines.
