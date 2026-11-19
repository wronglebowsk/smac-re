#!/usr/bin/env python3
"""m327 doc-cap rotation: move a SETTLED NAMED.md block VERBATIM into
docs/named-archive-*.md (NAMED.md FAILs at 250,000 B and this milestone must add a block).
Byte-exactness is ASSERTED: sha1 of the extracted block must appear in the archive, and the
archive must contain the block verbatim. The stub (given in --stub-file) is checked to keep
the block's evidence cites. Print FIRST, assert AFTER.

Applied by this milestone:
  --head '## M316 ' --archive docs/named-archive-m316-rows.md  (6,699 B moved, sha1 d3dffc67fcb5)
  --head '## M311 ' --archive docs/named-archive-m311-rows.md  (5,248 B moved)
"""
import argparse, hashlib, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAIL_LINE = 250000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--head", required=True)
    ap.add_argument("--archive", required=True)
    ap.add_argument("--stub-file", required=True)
    a = ap.parse_args()
    named = os.path.join(ROOT, "NAMED.md")
    arc = os.path.join(ROOT, a.archive)
    lines = open(named).read().split("\n")
    idx = [i for i, l in enumerate(lines) if l.startswith("## ")]
    st = [i for i in idx if lines[i].startswith(a.head)]
    assert len(st) == 1, "expected exactly one %r block, got %d" % (a.head, len(st))
    top = lines[0]
    after = [i for i in idx if i > st[0]]
    b = after[0] if after else len(lines)
    a0 = st[0]
    # a block that starts the file must not swallow the file's own preamble
    if a0 == 0:
        pre = [i for i, l in enumerate(lines) if l.startswith("# ")]
        assert not pre or pre[0] > b, "refusing to move the file preamble"
    block = "\n".join(lines[a0:b]).rstrip("\n")
    sha = hashlib.sha1(block.encode()).hexdigest()
    stub = open(os.path.join(ROOT, a.stub_file)).read().strip()
    stub = stub.replace("BLOCKSHA1", sha[:12])
    for cite in [c for c in _cites(block)][:12]:
        assert cite in stub, "stub dropped the cite %s" % cite
    before = len("\n".join(lines).encode())
    tail = "\n".join(lines[b:])
    new = (stub + "\n" + tail) if a0 == 0 else ("\n".join(lines[:a0]) + "\n" + stub + "\n" + tail)
    new = new.lstrip("\n")
    if not new.endswith("\n"):
        new += "\n"
    hdr = ("# %s rows, moved VERBATIM out of NAMED.md by scripts/m327_named_rotate.py\n"
           "# (doc-cap rotation, s304/M327). sha1 of the moved block: %s\n"
           "# NAMED.md keeps one line per claim with the same gates/cites.\n\n"
           % (a.head.strip("# ").strip(), sha))
    old_arc = open(arc).read() if os.path.exists(arc) else ""
    arc_txt = (old_arc + "\n" + block + "\n") if old_arc.strip() else (hdr + block + "\n")
    nb = len(new.encode())
    print("moved block lines=%d bytes=%d sha1=%s" % (b - a0, len(block.encode()), sha))
    print("NAMED.md %d -> %d B (headroom vs the %d B FAIL line: %d)" % (before, nb, FAIL_LINE,
                                                                        FAIL_LINE - nb))
    assert len(block.encode()) > 3000, "the block to rotate is implausibly small"
    assert block in arc_txt and sha in arc_txt, "archive is not byte-exact"
    assert nb < before - 2000, "rotation saved too little to be worth doing"
    assert FAIL_LINE - nb > 3000, "still no headroom after the rotation"
    assert top.startswith("# ") or top.startswith("## "), "unexpected first line %r" % top[:40]
    open(arc, "w").write(arc_txt)
    open(named, "w").write(new)
    chk = open(named, "rb").read().decode()
    assert block not in chk, "NAMED.md still holds the full block"
    arc2 = open(arc).read()
    assert block in arc2 and sha in arc2, "archive re-read check failed"
    print("PASS rotate %r: NAMED.md %d B, archive %d B, byte-exact sha1 %s" %
          (a.head.strip(), len(chk.encode()), len(arc_txt.encode()), sha[:12]))
    return 0


def _cites(block):
    import re
    return sorted(set(re.findall(r"evidence/[A-Za-z0-9_.-]+(?::\d+(?:-\d+)?)?", block)))


if __name__ == "__main__":
    sys.exit(main())
