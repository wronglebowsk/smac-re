#!/usr/bin/env python3
"""m378_named_rotate.py - move NAMED.md's settled `## M366` and `## M319` blocks VERBATIM
into `docs/named-archive-m378-rows.md` and leave one line per claim in NAMED.

M378 must add a block and NAMED.md is 247,824 B against a 250,000 B FAIL (2,176 B of headroom,
under the 5 KB trigger).  Both blocks are settled STATIC censuses (s293 / s335) whose numbers are
final and whose later qualifications already live in their own sections (M321 closed M319's one
lead; M369/M371 re-derived M366's neighbours).  The rotated text is byte-for-byte what NAMED
carried.  Each stub bullet keeps a claim tag, the conf/mutant column, every full
`evidence/file.txt:line` cite, and `archive:<line>` for the verbatim row.

    python3 scripts/m378_named_rotate.py            # rotate (refuses if already rotated)
    python3 scripts/m378_named_rotate.py --verify   # sha1 exact + bullets + archive lines
"""
import argparse
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs", "named-archive-m378-rows.md")
ARCHIVE_HEAD = ("# NAMED.md `## M366` + `## M319` - ROTATED VERBATIM (byte-exact) by "
                "scripts/m378_named_rotate.py\n")

SPECS = [
    ("## M366 ", "evidence/m366_bitnouns.txt", [
        "asks: 0x10 37 bare/52 total in 16 fns, 0x20 18/30 in 5 fns; B-twins only 0x8/0x2000",
        "ask decoder sound: 214/232 sites 3-push cdecl, 2 inline-result sites named",
        "set-writer FUN_00551a20 `test bl,0x10 -> and 0xfaeef378`; clear-writer FUN_005518f0 `or 0x8040`",
        "0x10 IS what the declare-vendetta path writes (FUN_00507ce0, VENDETTAWARNING/INCITED)",
        "0x20 is SET by the same routine through FUN_00551cf0's arg4 ([ebp+0x14] selects the clear)",
        "reader 0x51ef55 IS `test ...,0x40020`: SET keeps ECONOMICLOSE2 over ECONOMICLOSE",
        "direct tests 62 / 37 / 3 reproduce M364 G6; 0x8010 is never a direct test",
        "rivals refuted: 0x10 not a peace bit, != 0x20, != 0x8, 0x20 != 0x40000",
        "ACCEPT `python3 -u scripts/m366_bitnouns.py` 29/29 `c36db3d154a5ea1b` x2, harness 32/32",
        "INF: the noun WORD for 0x20; 0x80000000's role",
    ]),
    ("## M319 ", "evidence/m319_guard_hoist.txt", [
        "6 memo read/test insns in 5 fns; readers(5) subset writers(15)",
        "8 unguarded sites -> 4 owners / 8 callers; only 1 caller reads, and it owns a guarded site",
        "not dead, no memo-gated arrival: 9 arrivals, 0/9 under a memo test",
        "classifier not blind: memo-direct / memo-copy kinds pinned per address",
        "pair law ordered: `call 0x4e8d60` precedes `call 0x4e78e0`",
        "thunk-following measured inert here (harness NO-OP)",
        "ACCEPT 7/7 digest `fb4e802dac1995a2`, 3 runs byte-identical",
        "review #317: the squash title's `459f47e3178f439d` is the PRE-review harness",
        "OPEN: what gates the 8 (M321 closed the 0x38/0x40 leg)",
    ]),
]


def block(text, head):
    lines = text.splitlines(keepends=True)
    start = next(i for i, ln in enumerate(lines) if ln.startswith(head))
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")),
               len(lines))
    return "".join(lines[start:end])


def sha1(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def rows(body):
    return [ln for ln in body.splitlines()
            if ln.startswith("| ") and not ln.startswith("|---") and "| claim |" not in ln]


def cells_of(row):
    parts = row.strip().strip("|").replace("\\|", "\x00").split("|")
    return [p.strip().replace("\x00", "\\|") for p in parts]


def expand(cite, evfile):
    """:3-50` (section-relative) -> evidence/m366_bitnouns.txt:3-50"""
    return cite if "/" in cite else evfile + cite


def cites_of(row, evfile):
    cs = cells_of(row)
    ev = cs[1] if len(cs) > 1 else ""
    return [expand(c, evfile) for c in re.findall(r"`:([^`]+)`", ev)]


def make_stub(head, evfile, body, digest, tags, arch_start):
    lines = body.splitlines()
    out = ["%s - ROTATED VERBATIM to `docs/named-archive-m378-rows.md` (sha1 `%s`); one line per "
           "claim with the same conf/mutants and full `path:line`, plus `archive:<line>` for the "
           "verbatim row." % (lines[0], digest)]
    rs = rows(body)
    if len(tags) != len(rs):
        raise SystemExit("FAIL: %s has %d tag(s) for %d claim rows"
                         % (head.strip(), len(tags), len(rs)))
    for i, r in enumerate(rs):
        cs = cells_of(r) + [""] * 3
        claim, ev, conf = cs[0], cs[1], cs[2]
        cites = cites_of(r, evfile)
        refs = ", ".join("`%s`" % c for c in cites) if cites else (ev or "-")
        out.append("- %s - %s - %s - archive:%d" % (tags[i], conf or "-", refs, arch_start + i))
    return "\n".join(out) + "\n\n"


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args(argv)
    named = open(NAMED, encoding="utf-8").read()

    if args.verify:
        arch = open(ARCHIVE, encoding="utf-8").read()
        alines = arch.split("\n")
        ok_rows = ok_bul = ok_arch = 0
        sizes = []
        for head, evfile, tags in SPECS:
            blk = block(arch, head)
            blk = "\n".join(blk.splitlines()) + "\n"
            st = block(named, head)
            m = re.search(r"sha1 `([0-9a-f]{40})`", st)
            if not m:
                raise SystemExit("FAIL: no sha1 in the %s stub" % head.strip())
            if sha1(blk) != m.group(1):
                raise SystemExit("FAIL: %s archived sha1 %s != stub %s"
                                 % (head.strip(), sha1(blk), m.group(1)))
            claims = rows(blk)
            bullets = [ln for ln in st.splitlines() if ln.startswith("- ")]
            if len(bullets) != len(claims):
                raise SystemExit("FAIL: %s stub carries %d bullets for %d archived rows"
                                 % (head.strip(), len(bullets), len(claims)))
            refs = sorted({c for r in claims for c in cites_of(r, evfile)})
            missing = [r for r in refs if "`%s`" % r not in st]
            if missing:
                raise SystemExit("FAIL: %s stub drops the full citations %s"
                                 % (head.strip(), missing))
            bare = re.findall(r"`:(?:\d[0-9,\-]*)`", st)
            if bare:
                raise SystemExit("FAIL: %s stub carries bare cites %s" % (head.strip(), bare))
            for b, r in zip(bullets, claims):
                n = int(re.search(r"archive:(\d+)", b).group(1))
                if alines[n - 1].strip() != r.strip():
                    raise SystemExit("FAIL: %s archive:%d does not hold that claim"
                                     % (head.strip(), n))
                ok_arch += 1
            ok_rows += len(claims)
            ok_bul += len(bullets)
            sizes.append(len(st.encode()))
        print("PASS m378_named_rotate --verify: 2 blocks sha1-exact, %d archived claim rows == "
              "%d stub bullets, %d archive:<line> pointers resolve, 0 bare cites, stubs %d + %d B, "
              "archive %d B" % (ok_rows, ok_bul, ok_arch, sizes[0], sizes[1], len(arch.encode())))
        return 0

    if "ROTATED VERBATIM to `docs/named-archive-m378-rows.md`" in named:
        raise SystemExit("already rotated (stub present)")
    alines = [ARCHIVE_HEAD.rstrip("\n"), ""]
    for head, evfile, tags in SPECS:
        body = block(named, head)
        if not body.strip():
            raise SystemExit("FAIL: `%s` block not found" % head.strip())
        bl = body.splitlines()
        alines.extend(bl)
        if alines[-1] != "":
            alines.append("")
    while alines[-1] == "":
        alines.pop()
    arch_text = "\n".join(alines) + "\n"
    stubs = []
    for head, evfile, tags in SPECS:
        body = block(named, head)
        i = next(k for k, l in enumerate(alines) if l.startswith(head))
        hdr_off = next(j for j, l in enumerate(body.splitlines())
                       if l.startswith("| ") and not l.startswith("|---") and "| claim |" not in l)
        blk = "\n".join(block(arch_text, head).splitlines()) + "\n"
        stubs.append(make_stub(head, evfile, body, sha1(blk), tags, i + 1 + hdr_off))
    with open(ARCHIVE, "w", encoding="utf-8") as fh:
        fh.write(arch_text)
    new = named
    for (head, evfile, tags), st in zip(SPECS, stubs):
        new = new.replace(block(named, head), st)
    if new == named:
        raise SystemExit("FAIL: replacement was a no-op")
    if len(new.encode()) >= len(named.encode()):
        raise SystemExit("FAIL: rotation did not shrink NAMED.md (%d -> %d B)"
                         % (len(named.encode()), len(new.encode())))
    with open(NAMED, "w", encoding="utf-8") as fh:
        fh.write(new)
    print("rotated `## M366` + `## M319` -> docs/named-archive-m378-rows.md  (%d B archive)"
          % len(arch_text.encode()))
    print("NAMED.md %d -> %d B" % (len(named.encode()), len(new.encode())))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
