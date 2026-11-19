#!/usr/bin/env python3
"""s292 one-off: repair the session-archive pointer chain that scripts/session_rotate.py
used to break (the hot file cites only the NEWEST archive, so every older archive was an
orphan - found by the local review of #316, P1). Dry run by default, `--apply` writes.

Inserting nothing but a pointer line under each archive's existing header, so no session
text is touched. `scripts/s292_cap_check.py` C3 is the gate on the result.

  python3 -u scripts/s292_chain_fix.py [--apply]
"""
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCH = os.path.join(REPO, "docs", "sessions")
NAME_RX = re.compile(r"sessions-(\d+)-(\d+)\.md")
POINTER_RX = re.compile(r"^Older sessions: `docs/sessions/sessions-\d+-\d+\.md`", re.M)
ANCHOR = "file readable in one context window. Same evidence file paths apply.\n"
LINE = ("Older sessions: `docs/sessions/%s` (inserted at s292: the hot file cites only the "
        "newest archive, so without this line the older archives were orphans).\n")


def main():
    apply = "--apply" in sys.argv
    if apply and "--force" not in sys.argv and subprocess.run(
            ["git", "-C", REPO, "status", "--porcelain"],
            capture_output=True, text=True).stdout.strip():
        print("REFUSING --apply on a dirty tree (the point is a clean, reviewable chain diff); "
              "--force when you are re-writing this script's own output")
        return 2
    spans, touched, pending = {}, 0, []
    for nm in os.listdir(ARCH):
        m = NAME_RX.fullmatch(nm)
        if m:
            spans[nm] = (int(m.group(1)), int(m.group(2)))
    for nm, (lo, hi) in sorted(spans.items(), key=lambda kv: kv[1]):
        # Total order by (lo, hi): the archives OVERLAP (82-82 and 82-83, 144-148 and 147-151,
        # 173-174 and 174-174 - rotations that did not line up), so a "nearest strictly older"
        # rule orphans the overlapping ones. Walking (lo, hi) descending covers all of them.
        older = [o for o in spans if (spans[o][0], spans[o][1]) < (lo, hi)]
        if not older:
            print("     %-28s oldest archive - no pointer needed" % nm)
            continue
        prev = max(older, key=lambda o: (spans[o][0], spans[o][1]))
        path = os.path.join(ARCH, nm)
        text = open(path, encoding="utf-8").read()
        have = POINTER_RX.search(text)
        if have and ("`docs/sessions/%s`" % prev) in have.group(0):
            print("     %-28s already chained -> %s OK" % (nm, prev))
            continue
        if have:
            new = POINTER_RX.sub((LINE % prev).rstrip("\n"), text, count=1)
            print("     %-28s re-target pointer -> %s (%+d B)" % (nm, prev, len(new) - len(text)))
        elif ANCHOR not in text:
            print("     %-28s NO ANCHOR - skipped, fix by hand" % nm)
            continue
        else:
            new = text.replace(ANCHOR, ANCHOR + "\n" + (LINE % prev), 1)
            print("     %-28s insert pointer -> %s (%+d B)" % (nm, prev, len(new) - len(text)))
        pending.append(nm)
        if apply:
            open(path, "w", encoding="utf-8").write(new)
            touched += 1
    print("== chain fix: %d archive(s) %s ==" % (touched if apply else len(pending),
                                                 "written" if apply else
                                                 "would be written (dry run; rerun with --apply)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
