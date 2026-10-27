#!/usr/bin/env bash
# Launch ONE milestone session on the local model (provider qwen125b, Strata). No host is
# committed: endpoints are environment variables, see docs/WORKFLOW.md (STRATA_URL, EMBEDDING_URL).
#
#   scripts/agent_session.sh m52a              # planned milestone from NEXT_PROMPT.md
#   scripts/agent_session.sh m52a brief.md     # same, with extra instructions appended
#
# The prompt is deliberately SHORT and points at files instead of pasting them: the previous
# agent run died at ~101k tokens because it read the whole skill and dumped disassembly listings
# into context. Budget in this prompt is part of the design, not decoration.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

TAG="${1:?usage: agent_session.sh <tag> [extra-brief]}"
BRIEF="${2:-}"
MODEL="${MODEL:-qwen125b}"
LOG="evidence/agent_${TAG}.log"

[ -z "$(git status --porcelain)" ] || { echo "refusing: working tree is not clean"; exit 1; }
[ -f NEXT_PROMPT.md ] || { echo "refusing: run from the repo root"; exit 1; }

git checkout -q main
git pull -q --ff-only 2>/dev/null || true
git checkout -q -B "milestone/${TAG}"

PROMPT_FILE="$(mktemp)"
trap 'rm -f "$PROMPT_FILE"' EXIT

cat > "$PROMPT_FILE" <<EOF
You are running ONE milestone of a reverse-engineering loop in $ROOT (branch milestone/${TAG}).

READ, IN THIS ORDER AND NOTHING ELSE FIRST:
  1. NEXT_PROMPT.md — the full footing. It is ~12 KB; read all of it.
  2. \`tail -80 SESSION_NOTES.md\` — the latest milestone's section only.

CONTEXT DISCIPLINE — the last run died at ~101k tokens and lost the session:
  - Never paste a whole file into context. Use \`grep -n\`, \`sed -n 'A,Bp'\`, \`wc -l\`.
  - Never dump more than ~40 disassembly instructions at once.
  - If a command's output would exceed ~100 lines, write it to evidence/ and grep that file.
  - \`skill_view('smac-cvr-format')\` returns ~53k chars. Call it only when you need a specific
    harness recipe, and prefer grepping $ROOT/skill/references/wine-headless-harness.md instead.
  - Keep roughly 60k tokens in reserve: compression triggers at 86k and can be refused on cooldown.

LIVE-HARNESS RULES (violating any of these has cost a full run):
  - NEVER signal a process by name or pattern: no pkill, no killall, no \`pgrep -f\` piped to kill.
    Your own argv contains this prompt, so a name match kills YOUR session.
    Stop a driver only with: \`python3 scripts/m51a_drive.py --stop <tag>\`
  - Run drivers as tracked background jobs, never in a foreground command that a short timeout kills.
  - If a round is not advancing (final_year unchanged, ocr_passes climbing), OCR the screen and
    dismiss panes by hand before arming. 3-row COMM pane: windowfocus, key Down, 0.4s, key Return.
    Leader-profile pane ("UNIVERSITY INTELLIGENCE FILES"): Escape.
  - Leave the game running: TracerPid must be 0 and no gdb attached when you finish.

THE JOB: do exactly the milestone NEXT_PROMPT.md names as THE PICK, with live evidence. Then:
  - evidence under evidence/, cited in notes as evidence/<file>:<line>
  - append a dated "## Session N" section to SESSION_NOTES.md (VERIFIED vs INFERRED, log-line cites)
  - rewrite NEXT_PROMPT.md (next session number, new footing, next pick)
  - \`python3 scripts/gate.py --base main\` until green
  - \`python3 scripts/milestone.py submit --title "..."\`, \`gh pr checks <n>\`, then
    \`python3 scripts/milestone.py merge <n>\`
If two attempts yield no usable data, STOP and report the blocker precisely. A clean negative
result is acceptable; a fabricated address is not.
EOF

if [ -n "$BRIEF" ]; then
  [ -f "$BRIEF" ] || { echo "brief not found: $BRIEF"; exit 1; }
  printf '\n## Extra instructions for this run\n\n' >> "$PROMPT_FILE"
  cat "$BRIEF" >> "$PROMPT_FILE"
fi

echo "== launching $MODEL on branch milestone/${TAG}; log: $LOG"
hermes chat -q "$(cat "$PROMPT_FILE")" --yolo --model "$MODEL" 2>&1 | tee "$LOG"
