#!/bin/sh
# Install the repo's git hooks. Run once per clone; hooks are not versioned by git itself,
# so a fresh checkout is unprotected until you run this.
set -e
root=$(git rev-parse --show-toplevel)
cd "$root"
chmod +x scripts/hooks/pre-push
cp scripts/hooks/pre-push .git/hooks/pre-push
chmod +x .git/hooks/pre-push
echo "installed: .git/hooks/pre-push (blocks direct pushes to main)"
