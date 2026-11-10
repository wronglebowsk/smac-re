#!/usr/bin/env python3
"""M288: dialog CREATE-time and the Return-key path do NOT dispatch family +0x4c
(M287 frontier: +0x4c's remaining shapes.  M284-M287 measured FOUR click paths
with zero +0x4c dispatch; the two residual shapes were (a) dialog CREATE-time
(FUN_00405ef0 installs vptr 0x67164c: is the slot dispatched AT CREATE?) and
(b) the Return-key / keystroke path.  This milestone closes BOTH statically,
zero box time.)

How the chain works (established M284-M287 + this census):
- FUN_005f6aa3 (the family +0x4c slot target, the dialog row-click dispatcher:
  FUN_005e7917 row finder + [ecx+0xa8] row-cb dispatch) has ZERO direct callers
  image-wide (instruction-cache authoritative).  Its ONLY references anywhere
  are 5 data dwords = the +0x4c entries of the 5 family vtables (0x67164c /
  0x6717cc / 0x6728c0 / 0x675cc4 / 0x6776c8).  So it is reachable ONLY through
  a `call [reg+0x4c]` with a family-class object in reg.
- CREATE-time: the 466 family-vptr install sites live in 72 functions and NONE
  of those functions contains one of the 12 +0x4c dispatch sites (install-owner
  set ∩ site-owner set = empty).  The 0x67164c installer FUN_00405ef0 and its
  two callees (FUN_005ee350, FUN_005f6b8c) contain no +0x4c call and no
  0x5f6aa3 reference.  A vptr install never dispatches the slot.
- Return-key: WM_KEYDOWN (0x100) -> FUN_005d1576 -> vtable +0x12c (all 5 family
  vtables: 0x5d629d) -> hotkey dispatcher FUN_005d629d -> (non-hotkey)
  FUN_005cf43a -> vtable +0x60 dispatch (0x5f59bf) / FUN_005cf2d6.  WM_CHAR
  0x102 -> FUN_005d15d5, WM_SYSKEYDOWN 0x104 -> FUN_005d1601.  None of these
  chain bodies contains a `call [reg+0x4c]` or a 0x5f6aa3 reference; the pump
  FUN_005f1394 (which carries the INLINE row callback, M286) also contains
  neither.  The only vtable slots the keyboard path dispatches are +0x12c and
  +0x60 -- never +0x4c.
- The 11 site-owner functions' DIRECT callers are all outside both paths (none
  is a family-vptr installer, none is in the key chain) - listed in the table.

Pre-registered verdicts (same contract as the M284-M287 family):
  static PASS (5/5 gates) = both residual shapes closed statically.
  Any FAIL = the census contradicts the reading; the number is the finding.

    python3 scripts/m288_create_key_dispatch.py
"""
import os, re, sys, csv, bisect, struct, json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from m284_dialog_dispatch import dw  # noqa: E402  (proven file-image reader)

FAMILY = [0x67164c, 0x6717cc, 0x6728c0, 0x675cc4, 0x6776c8]
FAM_SLOT = 0x5f6aa3
SITES = [(0x4b83f3, "edx"), (0x4ba2e3, "edx"), (0x4c6da9, "ecx"),
         (0x5b7cec, "edx"), (0x5b7dc4, "edx"), (0x5ceec2, "edx"),
         (0x5d9b8e, "eax"), (0x5d9bae, "eax"),
         (0x5fa9df, "edx"), (0x5faddc, "edx"),
         (0x5ffb3b, "eax"), (0x63cfa4, "eax")]
KEY_CHAIN = [0x5d1576, 0x5d629d, 0x5cf43a, 0x5d15d5, 0x5d1601]
PUMP = 0x5f1394
CTOR = [0x405ef0, 0x5ee350, 0x5f6b8c]   # 0x67164c installer + its two callees

CACHE = "/tmp/ins_cache.json"


def load_ins():
    if os.path.exists(CACHE):
        data = json.load(open(CACHE))
        return {d[0]: (d[1], d[2], " ".join(str(x) for x in d[3:])) for d in data}
    # fallback: regenerate from the git-kept blob via the repo's own extractor
    import subprocess
    out = subprocess.run(["git", "cat-file", "-p", "bfcefd0659579ae97b619593b461313d6c19f3b7"],
                         capture_output=True).stdout
    data = json.loads(out)
    return {d[0]: (d[1], d[2], " ".join(str(x) for x in d[3:])) for d in data}


def main():
    ins = load_ins()
    rows = [r for r in csv.reader(open(os.path.join(ROOT, "ghidra_out/index.csv")))
            if len(r) >= 2 and re.fullmatch(r"0x[0-9a-f]+", r[0], re.I)]
    bnds = sorted((int(r[0], 16), r[1]) for r in rows)
    starts = [s for s, _ in bnds]
    names = [n for _, n in bnds]

    def fnof(a):
        i = bisect.bisect_right(starts, a) - 1
        return names[i] if i >= 0 else None

    RX4C = re.compile(r"\[[^\]]*\+\s*0x4c\]", re.I)   # cache formats "+ 0x4c" with a space

    # ---- g1: the 12 sites still read call [reg+0x4c] ----
    g1 = all(ins.get(s) and ins[s][1] == "call" and RX4C.search(ins[s][2])
             for s, _ in SITES)

    # ---- g2: FUN_005f6aa3 zero direct callers; only refs = 5 family +0x4c slots ----
    dc = 0
    for d in ins.values():
        if d[1] == "call" and re.search(r"\b0x%x\b" % FAM_SLOT, d[2], re.I):
            dc += 1
    refs = []
    for va in range(0x660000, 0x6a9000, 4):
        if dw(va) == FAM_SLOT:
            refs.append(va)
    want = sorted(b + 0x4c for b in FAMILY)
    g2 = (dc == 0 and refs == want)

    # ---- g3: family-vptr installs; owners never contain a +0x4c site ----
    RXFAM = re.compile(r",\s*0x(6[0-9a-f]{5})\s*$")
    install_owners = set()
    n_installs = 0
    for a, (sz, mn, op) in ins.items():
        if mn == "mov":
            m = RXFAM.search(op)
            if m and int(m.group(1), 16) in FAMILY and "[" in op:
                n_installs += 1
                install_owners.add(fnof(a))
    site_owners = set(fnof(s) for s, _ in SITES)
    overlap = install_owners.intersection(site_owners)
    # ctor bodies: no +0x4c call, no 5f6aa3 ref
    ctor_clean = []
    for a in CTOR:
        fn = fnof(a)
        bad = [x for x, (sz, mn, op) in ins.items() if fnof(x) == fn and
               (RX4C.search(op) or re.search(r"5f6aa3", op, re.I))]
        ctor_clean.append((fn, len(bad)))
    g3 = (not overlap and all(n == 0 for _, n in ctor_clean) and n_installs == 466)

    # ---- g4: key chain + pump contain no +0x4c CALL dispatch (M284 forms) ----
    # M284's dispatch forms: (a) call [reg+0x4c]; (b) load-then-call pair
    # (mov/lea r,[r+0x4c] followed <=40 insns later in the SAME fn by call r).
    # A lone `mov eax,[edx+0x4c]` whose value feeds a direct call is a DATA read
    # (e.g. FUN_005d629d@0x5d632d reads the hotkey binding at table+0x4c and
    # passes it to FUN_00631070) - not the family dispatch form.
    def dispatch_hits(fn):
        fns = [(a, mn, op) for a, (sz, mn, op) in ins.items() if fnof(a) == fn]
        hitsls = [(a, mn, op) for a, mn, op in fns if mn == "call" and RX4C.search(op)]
        # load-then-call pairs
        for i, (a, mn, op) in enumerate(fns):
            m = re.match(r"^(?:mov|lea)\s+([a-z0-9]+),\s*\[[^\]]*\+\s*0x4c\]", op, re.I)
            if not m:
                continue
            for j in range(i + 1, min(i + 41, len(fns))):
                if re.match(r"call\s+%s\b" % m.group(1), fns[j][2], re.I):
                    hitsls.append((a, "LTC->" + fns[j][0], op))
                    break
                if "ret" in fns[j][2]:
                    break
        return hitsls

    g4 = True
    kc_table = []
    for a in KEY_CHAIN + [PUMP]:
        fn = fnof(a)
        bad = dispatch_hits(fn)
        kc_table.append((fn, len(bad), [hex(x) for x, _, _ in bad]))
        if bad:
            g4 = False
    # family vtables: the key slots ARE +0x12c / +0x60, never +0x4c on the chain
    slots_ok = all(dw(b + 0x12c) == 0x5d629d for b in FAMILY)
    g4 = g4 and slots_ok

    # ---- g5: the 11 site owners' direct callers avoid both paths ----
    owner_addr = {n: a for a, n in bnds}
    CALLRX = re.compile(r"^0x([0-9a-f]{6,8})$")
    st, = struct.unpack("<I", b"\x00\x00\x00\x00")  # noqa: unused (kept None semantics)
    caller_tab = []
    for n in sorted(site_owners):
        tgt = owner_addr.get(n)
        if tgt is None:
            caller_tab.append((n, [])); continue
        cs = []
        for x, d in sorted(ins.items()):
            if fnof(x) == n:
                continue
            if d[1] == "call" and CALLRX.match(d[2]) and int(d[2], 16) == tgt:
                cs.append(fnof(x))
        caller_tab.append((n, sorted(set(cs))))
    path_fns = install_owners | {fnof(a) for a in KEY_CHAIN + CTOR}
    g5 = all(not (set(cs) and set(cs).intersection(path_fns)) for _, cs in caller_tab)

    print("M288 static census")
    print("g1 12 call [reg+0x4c] sites unchanged: %s" % g1)
    print("g2 0 direct call 0x5f6aa3 (dc=%d); 5 refs = family +0x4c slots: %s" % (dc, g2))
    print("   refs: %s  want: %s" % ([hex(r) for r in refs], [hex(w) for w in want]))
    print("g3 family-vptr installs=%d owners=%d, overlap=%s, ctor-bodies=%s: %s"
          % (n_installs, len(install_owners), sorted(overlap),
             [(fn, n) for fn, n in ctor_clean], g3))
    print("g4 key chain + pump clean=%s, family +0x12c==0x5d629d=%s: %s"
          % (["%s/%d%s" % (fn, n, "!" + ",".join(h) if h else "") for fn, n, h in kc_table],
             slots_ok, g4))
    print("g5 site-owner direct callers avoid installer/key/ctor paths: %s" % g5)
    for n, cs in caller_tab:
        print("   %s <- %s" % (n, cs))
    ok = g1 and g2 and g3 and g4 and g5
    print("STATIC %s (%d/5)" % ("PASS" if ok else "FAIL", sum([g1, g2, g3, g4, g5])))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
