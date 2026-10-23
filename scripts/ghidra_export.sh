#!/bin/sh
# ghidra_export.sh — pinned, provenance-stamped regeneration of ghidra_out/.
#
# Runs analyzeHeadless exactly as skill/references/ghidra-batch-export.md documents
# it (import programs/terran.exe into a throwaway project, postScript ExportAll.java,
# -deleteProject), then appends ONE provenance line to ghidra_out/index.csv:
#
#   #provenance ghidra=<version> args="<analyzeHeadless argv>" exported_utc=<UTC>
#
# Why the stamp exists: scripts/summarize.py + scripts/index.py key 2,786 LLM
# summaries on a hash of each function body. A silent change to the Ghidra version
# or the headless args can shift every body and invalidate them. The stamp makes
# the recipe explicit on disk; with --force this script also diffs the replaced
# export's provenance against the new one (ignoring the timestamp) and shouts when
# they differ.
#
#   scripts/ghidra_export.sh            # refuses if ghidra_out/ already exists
#   scripts/ghidra_export.sh --force    # replaces it, provenance diff first
#
# Preflight fails loudly BEFORE anything is deleted: missing programs/terran.exe,
# a non-PE file there, a missing Ghidra install, or a missing ExportAll.java.
# Post-run self-checks gate the stamp: index.csv header matches ExportAll.java,
# index rows == MANIFEST functions, shard files == MANIFEST shards, budget_hit
# must be false, and the provenance line must land as the single last line. An
# export that fails any check is left UNSTAMPED — the missing provenance is
# itself the signal that the corpus is not trustworthy.
#
# Env: GHIDRA            Ghidra install (default ~/tools/ghidra_12.1.4_PUBLIC)
#      SMAC_MAX_SECONDS  decompile budget passed to ExportAll.java (default 5400)
# Cost: ~205 s import + minutes of decompilation. ghidra_out/ is gitignored.

set -eu

PROG=ghidra_export.sh
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
OUT="$REPO/ghidra_out"
EXE="$REPO/programs/terran.exe"
PROJ_DIR="$REPO/ghidra_proj"
SCRIPTS="$REPO/ghidra_scripts"
GHIDRA="${GHIDRA:-$HOME/tools/ghidra_12.1.4_PUBLIC}"
HEADLESS="$GHIDRA/support/analyzeHeadless"
MAX_SECONDS="${SMAC_MAX_SECONDS:-5400}"
# The header ExportAll.java writes; keep in lockstep with it and with the two
# consumers (scripts/fn.py, scripts/coverage.py), which skip "#provenance" lines.
HDR='addr,name,size_bytes,n_insns,n_callers,n_callees,n_strings,ok,chars,shard'

die() { echo "$PROG: FATAL: $*" >&2; exit 1; }
note() { echo "$PROG: $*" >&2; }

usage() {
    cat <<'EOF'
usage: scripts/ghidra_export.sh [--force]

Regenerate ghidra_out/ (index.csv + shard_NNN.c + MANIFEST.txt) with the pinned
analyzeHeadless recipe from skill/references/ghidra-batch-export.md, then stamp
ghidra_out/index.csv with a provenance line (Ghidra version, headless args, UTC).

  --force  replace an existing ghidra_out/; its provenance is diffed against
           the new one first and a recipe change is reported loudly
  --help   this message
EOF
}

FORCE=0
for arg in "$@"; do
    case "$arg" in
        --force) FORCE=1 ;;
        -h|--help) usage; exit 0 ;;
        *) usage >&2; die "unknown argument '$arg'" ;;
    esac
done

# ---------- preflight: fail loudly before touching anything ----------
[ -r "$EXE" ] || die "no readable terran.exe at $EXE — programs/ holds the game install; point the harness at a real copy"
if [ "$(head -c 2 "$EXE")" != "MZ" ]; then
    die "$EXE does not start with the MZ header — that is not the PE binary the corpus was built from"
fi
[ -x "$HEADLESS" ] || die "Ghidra not usable: $HEADLESS missing or not executable — set GHIDRA=/path/to/ghidra_XX_X_X_PUBLIC (default expects ~/tools/ghidra_12.1.4_PUBLIC)"
[ -f "$SCRIPTS/ExportAll.java" ] || die "missing $SCRIPTS/ExportAll.java — that postScript IS the exporter; without it analyzeHeadless would pay the import and write nothing"

GHIDRA_VERSION=$(sed -n 's/^application\.version=//p' "$GHIDRA/Ghidra/application.properties" 2>/dev/null | head -n 1)
[ -n "$GHIDRA_VERSION" ] || GHIDRA_VERSION=$(basename "$GHIDRA" | sed -n 's/^ghidra_\([0-9.]*\)_PUBLIC$/\1/p')
[ -n "$GHIDRA_VERSION" ] || die "cannot determine the Ghidra version from $GHIDRA — a provenance line without it would be meaningless"

# ---------- refuse or replace the existing export ----------
OLD_PROV=""
if [ -e "$OUT" ]; then
    if [ "$FORCE" != 1 ]; then
        die "$OUT already exists — refusing to overwrite a corpus the index depends on; pass --force to regenerate (~1 h of work)"
    fi
    if [ -f "$OUT/index.csv" ]; then
        OLD_PROV=$(grep '^#provenance ' "$OUT/index.csv" 2>/dev/null | tail -n 1 || true)
    fi
    [ -n "$OLD_PROV" ] || note "--force: the export being replaced carries no provenance line (it predates this script); nothing to compare against"
    note "--force: removing existing $OUT"
    rm -rf "$OUT" || die "cannot remove $OUT"
fi

# ---------- the export: invocation exactly as the reference documents it ----------
export SMAC_EXPORT_DIR="$OUT"
export SMAC_MAX_SECONDS="$MAX_SECONDS"
note "exporting $EXE -> $OUT (Ghidra $GHIDRA_VERSION, budget ${MAX_SECONDS}s)"
if ! "$HEADLESS" "$PROJ_DIR" smac \
        -import "$EXE" \
        -postScript ExportAll.java -scriptPath "$SCRIPTS" \
        -deleteProject; then
    die "analyzeHeadless exited non-zero — $OUT is partial or empty and is left UNSTAMPED on purpose"
fi

# ---------- integrity checks BEFORE the stamp ----------
[ -f "$OUT/index.csv" ] || die "analyzeHeadless exited 0 but wrote no index.csv — export left UNSTAMPED"
[ "$(head -n 1 "$OUT/index.csv")" = "$HDR" ] || die "index.csv header differs from the pinned ExportAll.java header — ExportAll.java changed; update this script and re-check scripts/fn.py and scripts/coverage.py before trusting the corpus"
[ -f "$OUT/MANIFEST.txt" ] || die "no MANIFEST.txt — ExportAll did not finish; export left UNSTAMPED"
NROWS=$(grep -c '^0x' "$OUT/index.csv" || true)
FUNCS=$(sed -n 's/^functions: //p' "$OUT/MANIFEST.txt")
SHARDS=$(sed -n 's/^shards: //p' "$OUT/MANIFEST.txt")
BUDGET=$(sed -n 's/^budget_hit: \([a-z]*\).*/\1/p' "$OUT/MANIFEST.txt")
NSHARD=$(ls "$OUT"/shard_*.c 2>/dev/null | wc -l | tr -d ' ')
[ "$NROWS" = "$FUNCS" ] || die "index.csv has $NROWS function rows but MANIFEST says functions: $FUNCS — inconsistent export, left UNSTAMPED"
[ "$NSHARD" = "$SHARDS" ] || die "$NSHARD shard files on disk but MANIFEST says shards: $SHARDS — inconsistent export, left UNSTAMPED"
[ "$BUDGET" = "false" ] || die "SMAC_MAX_SECONDS=${MAX_SECONDS}s budget hit — the corpus is PARTIAL; re-run with a larger SMAC_MAX_SECONDS (left UNSTAMPED so the partial state is obvious)"

# ---------- the stamp ----------
UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)
ARGS_Q="analyzeHeadless $PROJ_DIR smac -import $EXE -postScript ExportAll.java -scriptPath $SCRIPTS -deleteProject"
PROV_LINE="#provenance ghidra=$GHIDRA_VERSION args=\"$ARGS_Q\" exported_utc=$UTC"
printf '%s\n' "$PROV_LINE" >> "$OUT/index.csv"
[ "$(tail -n 1 "$OUT/index.csv")" = "$PROV_LINE" ] || die "provenance line is not the last line of index.csv — append failed"
[ "$(grep -c '^#provenance ' "$OUT/index.csv")" = 1 ] || die "index.csv does not hold exactly one provenance line — stamp failed"

# ---------- provenance diff against the export --force replaced ----------
if [ -n "$OLD_PROV" ]; then
    KEY_OLD=$(printf '%s\n' "$OLD_PROV" | sed -n 's/^#provenance \(.*\) exported_utc=.*/\1/p')
    KEY_NEW=$(printf '%s\n' "$PROV_LINE" | sed -n 's/^#provenance \(.*\) exported_utc=.*/\1/p')
    if [ "$KEY_OLD" != "$KEY_NEW" ]; then
        note "EXPORT RECIPE CHANGED — this re-export replaced a different recipe:"
        note "  was: $KEY_OLD"
        note "  now: $KEY_NEW"
        note "Function-body hashes may have shifted: re-run scripts/summarize.py and"
        note "scripts/index.py build before trusting index hits (2,786 LLM summaries"
        note "are keyed on those hashes). Diff ghidra_out/index.csv provenance to confirm."
    else
        note "provenance unchanged by this re-export (Ghidra $GHIDRA_VERSION, same args) — summaries stay keyed correctly"
    fi
fi

note "done: $OUT regenerated and stamped: $PROV_LINE"
