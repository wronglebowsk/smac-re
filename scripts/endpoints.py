"""Where the local model servers live: an env file outside the repo, then the environment.

The repo ships no host. Set STRATA_URL / SUMMARY_URL / EMBEDDING_URL in your shell, or put
KEY=value lines in $XDG_CONFIG_HOME/smac-re/env (default ~/.config/smac-re/env) — outside the
repo, so it can never be committed. The real environment wins over the file.

    # ~/.config/smac-re/env
    EMBEDDING_URL=http://<host>:8000/v1/embeddings
    SUMMARY_URL=http://<host>:8080/v1/chat/completions
"""

import os

CONFIG = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"),
                      "smac-re", "env")


def _from_file(var):
    try:
        with open(CONFIG, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                if key.strip() == var:
                    return val.strip().strip("'\"")
    except OSError:
        return ""
    return ""


def get(var):
    """The endpoint for VAR: environment first, then the config file. '' means unset."""
    return (os.environ.get(var, "").strip() or _from_file(var)).rstrip("/")
