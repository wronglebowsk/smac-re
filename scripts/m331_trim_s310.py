#!/usr/bin/env python3
"""M331 s310-chain2 NEXT_PROMPT cap trim: append the M331 result line; the
addition crosses the 12,000 B warn, so chain 2's OWN M330 one-liner is retired
VERBATIM to docs/pick-archive.md §trim-s310-chain2 (a) (sha1 + byte-substring
asserted). NAMED ## M330 governs the retired content. FAILs if still > warn.
"""
import hashlib, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NP = os.path.join(ROOT, "NEXT_PROMPT.md")
PA = os.path.join(ROOT, "docs", "pick-archive.md")

LINE = ("M331 (s310-chain2): +2fc/+308=upkeep INCOME siblings (per-base "
        "clamp(net,0,99999) phase-1 / 8f0d40 sums +c0-gated); +30c ledger verified "
        "8/8 save; interest=facprofile+4ec %/100 bit14; cap 546800 MIN(E/2,100*net)>=50. "
        "14/14 a9983cddad88fade x2; 33/33+1 75a8749314a13287. NAMED ## M331.\n")

s = open(NP).read()
assert "M331 (s310-chain2)" not in s, "M331 line already present"
lines = s.splitlines(keepends=True)
idx = [i for i, l in enumerate(lines) if l.startswith("M330 (s307-chain2):")]
assert len(idx) == 1, "expected exactly one M330 one-liner, got %d" % len(idx)
retired = lines[idx[0]]
# review #345 P2-3: the label says sha1 — compute SHA-1 (the first firing
# mislabeled a sha256 as sha1; fix-forwarded in the archive, true sha1
# 429295c00401, and this script now matches its label).
sha = hashlib.sha1(retired.encode()).hexdigest()[:12]

arch = open(PA).read()
assert "§trim-s310-chain2" not in arch, "section already exists"
sec = ("\n## §trim-s310-chain2 — NEXT_PROMPT cap trim at s310 (M331 fire): the M330 "
       "one-liner retired VERBATIM\n\n"
       "(a) THE M330 RESULT ONE-LINER, VERBATIM from `NEXT_PROMPT.md` (sha1 `%s`, "
       "byte-substring asserted by `scripts/m331_trim_s310.py`; `NAMED ## M330` governs; "
       "the M330 MERGED landing line stays in NEXT_PROMPT):\n\n%s" % (sha, retired))
arch2 = arch + sec
assert retired in arch2, "byte-substring assertion failed"
open(PA, "w").write(arch2)

del lines[idx[0]]
new = "".join(lines) + LINE
n = len(new.encode())
if n > 12000:
    print("FAIL: NEXT_PROMPT still %d B > 12000 after retirement" % n)
    sys.exit(1)
open(NP, "w").write(new)
print("retired M330 one-liner sha1=%s (%d B); NEXT_PROMPT %d -> %d B (<=12000 OK)"
      % (sha, len(retired.encode()), len(s.encode()), n))