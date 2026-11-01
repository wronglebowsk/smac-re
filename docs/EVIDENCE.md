# Evidence & context budget

The binding constraint is the model context: **262,144 tokens ≈ 1.05 M characters**. A session
that loads the skill, the prompt, the notes and a raw watch log can spend a quarter of that
before doing any work. This doc defines what gets read, what gets archived, and what gets
pruned — and the tools that enforce it.

## What a session may read

| Artifact | How | Budget |
|---|---|---|
| `skill/SKILL.md` | always loaded | ≤ 55 k chars (warn), 70 k (fail) |
| `NEXT_PROMPT.md` | always, in full | ≤ 12 k (warn), 16 k (fail) |
| `AGENTS.md` | always | ≤ 6 k |
| newest 2 `## Session` sections | `sed -n` / targeted read | ~20 k |
| `NAMED.md` | **grep only, never whole** | no read budget |
| `SESSION_NOTES.md` | tail, or the rotated archive | ≤ 110 k (warn), 150 k (fail) |
| any `evidence/*.log` | `evidence.py show <file>:<line>` | one window at a time |
| a log you must understand | `evidence.py digest` first | digest ≤ 3 k |

Ritual target: **~60 k chars ≈ 15 k tokens (6 % of context)**, leaving the rest for the work.
`evidence.py budget` prints the live numbers with the percentage of context each file costs — and those numbers
are **BYTES** (`os.path.getsize`, exactly what `wc -c` reports), not characters: the table's caps are byte caps.
A doc full of arrows and em-dashes is a few dozen characters smaller than the number `budget` prints, so quote
the `budget` figure and call it bytes (s179: NEXT_PROMPT.md 14,018 B = 13,954 chars).

## Three tiers

- **Hot — the working tree.** The skill, `NEXT_PROMPT.md`, the last ~8 sessions, and every
  evidence file cited by them. This is what a session reads; it must stay small.
- **Warm — `docs/sessions/`.** When `SESSION_NOTES.md` passes ~110 k chars,
  `scripts/session_rotate.py --keep 8 --apply` moves the oldest sections into
  `docs/sessions/sessions-<first>-<last>.md` and leaves a one-line index. Nothing is lost; the
  file is simply no longer read by default.
- **Cold — git history.** Pruned images and any archived-and-later-removed file remain
  reachable: `git log --all --diff-filter=D -- <path>` → `git show <commit>^:<path>`.
  `evidence/.prune_log.jsonl` records path, sha256, size and the commit that removed each file,
  so `evidence.py log` answers "where did this go?" without a repo-wide search.

## Pruning rules

`python3 scripts/evidence.py prune --apply` (dry-run by default):

- **Text evidence is never pruned.** All logs together are ~2 MB — cheaper than the bookkeeping
  needed to archive them, and citations point straight at them.
- **Images are pruned** when they are not named anywhere in the Markdown (exact names and glob
  mentions such as `m49c_check*.png` both count) and are older than the keep window
  (`--keep-days`, default 1). A screenshot nobody cites is not evidence, and git still has it.
- The prune log is append-only and committed with the change.

Run it when `evidence.py budget` reports `warn` (20 MB) — the gate fails at 30 MB.

## Writing a citation that survives

- Cite a **line** (`evidence/m50a_watch.log:185`), never "see the log". A line cite is what
  `evidence.py show` needs to give the next agent a 5-line window instead of 258 lines.
- Cite the file you actually read. If you later digest it, the digest lives at
  `evidence/digests/<name>.md` and the original line numbers still apply.
- The gate fails a PR whose added citations do not resolve to a real line.

## Rotation

```bash
python3 scripts/session_rotate.py            # what would move
python3 scripts/session_rotate.py --apply    # keep newest 8, archive the rest
```

Rotate when `SESSION_NOTES.md` warns (>110 k chars, ~8 more sessions at the current rate), not
on a calendar. After rotating, commit both `SESSION_NOTES.md` and the new archive file — the
gate's checkpoint check still expects a new `## Session` section in the hot file.

## Why not git-lfs or an external archive

Neither helps the constraint. LFS keeps binaries out of the clone but they still land on disk;
an external bucket adds a network dependency to a repo an agent must work offline. The working
tree is the hot set, git is the archive, and the tools above keep the hot set small.
