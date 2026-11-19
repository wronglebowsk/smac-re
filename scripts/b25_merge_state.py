#!/usr/bin/env python3
"""scripts/b25_merge_state.py - the closeout facts of #319/B25, COMPUTED not asserted from prose.

Why this exists: #320's review (P1-2, P2-5/6/7) said the post-merge doc lines claim a merge SHA, a
doc byte-count, a VERBATIM move of two NEXT_PROMPT blocks and a rotation, and named no measurement
that could FAIL. Each of those is a fact about bytes in this repo, so every one is measured here.
RIVAL explanations carried: (i) the two blocks were COPIED not MOVED - they are still in the hot
doc; (ii) the rotation mangled the archive's evidence cites - a cite past EOF or to an untracked
file; (iii) the merge claim names a commit that is not on main or not the PR's squash.
"""
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)
PR = 319
CAP = 12000
# A cite is any `evidence/<path>` mention, BACKTICKED or BARE - the rotated archives use the bare
# form (that was #320's P2 finding), so a backtick-only regex silently measured 0 cites in exactly
# the files the rotation had just moved.
CITE = re.compile(r"evidence/[A-Za-z0-9_./-]+(?::\d+(?:-\d+)?(?:,\s*:\d+(?:-\d+)?)*)?")


def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True, check=True).stdout


def sha_of_pr_merge(pr):
    hits = [ln for ln in git("log", "--format=%H %s", "origin/main").splitlines()
            if ln.strip().endswith("(#%d)" % pr)]
    return hits[-1].split()[0] if hits else None


def fenced_blocks(path, heading_rx):
    """The fenced block that follows each heading matching heading_rx (None if the section has no
    complete fence pair - that becomes a FAILING row, never a skipped one)."""
    txt = open(path, encoding="utf-8").read().split("\n")
    out = []
    for i, ln in enumerate(txt):
        if re.match(heading_rx, ln):
            try:
                j = next(k for k in range(i, len(txt)) if txt[k].startswith("```"))
                k = next(m for m in range(j + 1, len(txt)) if txt[m].startswith("```"))
                out.append((i + 1, "\n".join(txt[j + 1:k])))
            except StopIteration:
                out.append((i + 1, None))
    return out


def revs(path, n=140):
    """Newest-first list of commits on origin/main that touched `path`."""
    return [h for h in git("log", "--format=%H", "-%d" % n, "origin/main", "--", path).split("\n") if h]


def newest_blob_with(path, needle, n=140):
    """The newest origin/main blob of `path` that still CONTAINS needle -> (sha, text) or (None, None).
    A rotated-out section's pre-rotation state is not `origin/main`'s tip (main moved on), so history
    is the only honest reference: this asks 'what did the file look like before the move?'."""
    for h in revs(path, n):
        t = git("show", h + ":" + path)
        if needle in t:
            return h, t
    return None, None


def resolve_cites(path):
    """(total, resolved, broken[]) for every evidence/<path> cite (backticked or bare) in a doc."""
    total, ok, broken = 0, 0, []
    tracked = set(git("ls-tree", "-r", "--name-only", "origin/main").split("\n")) | set(
        git("ls-files").split("\n"))
    blob = {}
    def blob_of(f):
        # Read the COMMITTED bytes, never the working file: this doc cites its own evidence file, and
        # a `> evidence/<self>.txt` acceptance run truncates that file before python starts, so a
        # worktree read would measure an empty file and report its own anchor as past EOF.
        if f not in blob:
            for spec in (":" + f, "origin/main:" + f):
                try:
                    blob[f] = git("show", spec)
                    break
                except subprocess.CalledProcessError:
                    continue
            else:
                blob[f] = open(f, encoding="utf-8").read()
        return blob[f]
    for ln in open(path, encoding="utf-8").read().split("\n"):
        for m in CITE.finditer(ln):
            tok = m.group(0).rstrip(".")
            f, _, anchors = tok.partition(":")
            total += 1
            if f not in tracked:
                broken.append("%s: %s not tracked on main or in HEAD" % (path, f))
                continue
            n = blob_of(f).count("\n") + 1
            nums = [int(x) for x in re.findall(r"\d+", anchors)]
            bad = [x for x in nums if x > n]
            if bad:
                broken.append("%s: %s cites %s past EOF (%d lines)" % (path, f, bad, n))
            else:
                ok += 1
    return total, ok, broken


def main():
    rows = []
    # 1. the merge is real, on main, and is PR #319's squash
    squash = sha_of_pr_merge(PR)
    rows.append(("origin/main carries a commit whose subject ends `(#%d)`" % PR,
                 squash or "NONE", squash is not None))
    short = squash[:7] if squash else "-"
    base = git("rev-parse", squash + "^").strip() if squash else None
    rows.append(("...and its PARENT (%s) is a readable NEXT_PROMPT state, so a VERBATIM move can be "
                 "diffed against a real pre-move blob" % (base[:7] if base else "-"),
                 base[:7] if base else "-", base is not None))

    # 2. what the docs CLAIM about the merge must equal the git fact
    named = open("NAMED.md", encoding="utf-8").read()
    claims = sorted(set(re.findall(r"MERGED s295 as #%d -> main ([0-9a-f]{7,40})" % PR, named)))
    rows.append(("NAMED ## B25 header names main %s (claims found: %s)"
                 % (short, claims), str(claims), len(claims) == 1 and claims[0] == short))
    notes = open("SESSION_NOTES.md", encoding="utf-8").read()
    rows.append(("SESSION_NOTES names the same sha in the s296 section",
                 notes.count("**main %s**" % short), notes.count("**main %s**" % short) == 1))

    # 3. the doc cap the notes quote
    np_bytes = os.path.getsize("NEXT_PROMPT.md")
    rows.append(("NEXT_PROMPT.md measures %d B (cap warn %d); the notes must state THAT number"
                 % (np_bytes, CAP), str(np_bytes),
                 np_bytes < CAP and ("%d" % np_bytes in notes
                                     or "{:,}".format(np_bytes) in notes)))

    # 4. every VERBATIM block the archive claims since s292 (the generation this instrument covers):
    # present, byte-for-byte, in the NEWEST NEXT_PROMPT blob that still carries it - history, because
    # main moves on and a block's pre-move state is not main's tip - AND absent from the hot doc.
    blocks = fenced_blocks("docs/pick-archive.md", r"^## §trim-s(?:29[2-9]|[3-9][0-9])\b")
    now_np = open("NEXT_PROMPT.md", encoding="utf-8").read()
    for ln, body in blocks:
        if body is None:
            rows.append(("pick-archive:%d claims a VERBATIM move but its section has NO fenced block "
                         "(a heading that measures nothing)" % ln, "no fence", False))
            continue
        lines = [l for l in body.split("\n") if l.strip()]
        first, last = lines[0][:44], lines[-1][:44]
        src, _ = newest_blob_with("NEXT_PROMPT.md", body)
        moved = src is not None
        dup = any(l in now_np for l in lines)
        rows.append(("pick-archive:%d block (%r .. %r) VERBATIM in %s:NEXT_PROMPT.md, and NOT "
                     "still in the hot doc (the COPIED-not-MOVED rival)"
                     % (ln, first, last, src[:7] if src else "NO BLOB"), "%s / dup=%s" % (moved, dup),
                     moved and not dup))

    # 5. the rotation: the 3 NEWEST rotated archives (numeric, not lexicographic - the old sort
    # picked sessions-9x and never measured the file this PR had just rotated), and every evidence
    # cite in them - bare or backticked - must still resolve on main.
    rot = sorted((f for f in os.listdir("docs/sessions")
                  if re.match(r"sessions-\d+-\d+\.md$", f)),
                 key=lambda f: [int(x) for x in re.findall(r"\d+", f)])[-3:]
    tot = res = 0
    broken = []
    for f in rot:
        t, r, b = resolve_cites(os.path.join("docs/sessions", f))
        tot, res, broken = tot + t, res + r, broken + b
    rows.append(("the 3 numerically-newest rotated files %s resolve %d/%d evidence cites "
                 "(the rotation-mangled-cites rival); %s" % (rot, res, tot, broken[:2] or "no breaks"),
                 "%d/%d" % (res, tot), res == tot and tot > 0))
    # 6. the rotation was FAITHFUL: every line of the pre-rotation sections survives in the archive -
    # either byte-identical, or ADDITIVELY annotated (every original word still present, in order, so a
    # cite can grow a :line anchor but a finding can never be silently dropped or rewritten). The
    # pre-rotation state is found in HISTORY (the newest SESSION_NOTES blob on origin/main that still
    # holds the section) - main's tip no longer has it, which is exactly what a rotation means. Plus the
    # copy-not-move rival: the sections must be GONE from the hot file.
    def words(s):
        return [w.strip("`'\"()[]{}.,;:!?'\"") for w in s.split()]

    def additive(old, new):
        # every word of the original line survives, in order, in the archive line: a word may GAIN a
        # suffix (a cite growing a :line anchor) and words may be inserted, but nothing is dropped or
        # reworded - that is what makes an annotation auditable instead of editorial.
        it = iter(words(new))
        return all(any(n == w or n.startswith(w) for n in it) for w in words(old))

    import difflib
    arch_txt = open("docs/sessions/" + rot[-1], encoding="utf-8").read()
    same = annotated = mangled = 0
    refs = set()
    for sm in re.finditer(r"^## Session .*$", arch_txt, re.M):
        lbl = sm.group(0)
        j = arch_txt.find("\n## Session ", sm.end())
        a_sec = arch_txt[sm.start():len(arch_txt) if j < 0 else j].split("\n")
        # the newest origin/main blob that STILL held this section = the state it was rotated out of
        src, pre_notes = newest_blob_with("SESSION_NOTES.md", lbl + "\n")
        if src is None or pre_notes is None:
            mangled += 1
            continue
        refs.add(src[:7])
        k = pre_notes.find(lbl)
        n = pre_notes.find("\n## Session ", k)
        o_sec = pre_notes[k:len(pre_notes) if n < 0 else n].rstrip().split("\n")
        for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, o_sec, a_sec).get_opcodes():
            if op == "equal":
                same += i2 - i1
            elif op == "insert":
                pass
            elif op == "replace" and (j2 - j1) == (i2 - i1) and all(
                    additive(o, a) for o, a in zip(o_sec[i1:i2], a_sec[j1:j2])):
                annotated += i2 - i1
            else:
                mangled += 1
    still_hot = any(("## Session " + m.group(1)) in notes for m in
                    re.finditer(r"^## Session (\d+)", arch_txt, re.M))
    rows.append(("rotation: %s -> %d lines byte-identical to the pre-rotation blob(s) %s of "
                 "SESSION_NOTES.md, %d additively annotated, %d lost/mangled; sections absent from the "
                 "hot file=%s (the hand-move / copy-not-move / silent-rewrite rivals)"
                 % (rot[-1], same, sorted(refs) or ["NONE"], annotated, mangled, not still_hot),
                 "%s / same=%d / annotated=%d / mangled=%d"
                 % (os.path.exists("scripts/session_rotate.py"), same, annotated, mangled),
                 os.path.exists("scripts/session_rotate.py") and same > 0 and mangled == 0
                 and not still_hot))
    # 7. every hex digest quoted on a cite-bearing line in those archives must reconcile with the
    # tracked blob it is cited to: either the digest IS in that file, or the same line names a
    # second digest that is (i.e. a superseded head is paired with its replacement in one breath).
    # Fails on a stale cite - and it found one in this PR's own archive before the line was fixed.
    unexplained = []
    dig_checked = 0
    for f in rot:
        for ln_no, ln in enumerate(open(os.path.join("docs/sessions", f),
                                        encoding="utf-8").read().split("\n"), 1):
            cites = [m.group(0).rstrip(".").partition(":")[0] for m in CITE.finditer(ln)]
            digs = re.findall(r"\b[0-9a-f]{12,16}\b", ln)
            if not cites or not digs:
                continue
            blobs = [git("show", "origin/main:" + c) for c in set(cites)
                     if c in set(git("ls-tree", "-r", "--name-only", "origin/main").split("\n"))]
            for d in digs:
                dig_checked += 1
                if not any(d in b for b in blobs) and not any(x in b for b in blobs
                                                               for x in re.findall(r"\b[0-9a-f]{12,16}\b", ln) if x != d):
                    unexplained.append("%s:%d %s" % (f, ln_no, d))
    rows.append(("all %d hex digests on cite-bearing lines of the 3 newest archives reconcile with "
                 "the cited blob (or share the line with their replacement); unexplained: %s"
                 % (dig_checked, unexplained[:3] or "none"), "%d/%d" % (dig_checked - len(unexplained),
                                                                        dig_checked), not unexplained))

    print("== B25/#319 closeout facts (measured; each row can FAIL) ==")
    for desc, got, ok in rows:
        print("%-4s %-104s %s" % ("ok" if ok else "BAD", desc[:104], got))
    bad = [d for d, _, ok in rows if not ok]
    if bad:
        print("FAIL b25_merge_state: %d/%d checks failed: %s" % (len(bad), len(rows), bad))
        return 1
    print("PASS b25_merge_state: %d/%d checks (merge %s on main, NEXT_PROMPT %d B < %d, "
          "%d VERBATIM trim blocks located in history and gone from the hot doc, %d/%d rotated cites "
          "resolve)"
          % (len(rows), len(rows), short, np_bytes, CAP, sum(1 for r in rows
                                                              if "VERBATIM in" in r[0]), res, tot))
    return 0


if __name__ == "__main__":
    sys.exit(main())
