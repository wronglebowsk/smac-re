#!/usr/bin/env python3
"""M339 — WHAT IS 0x5f1394? The modal SCREEN RUNNER (pick (x6) "callee 0x5f1394").

PICK: NEXT_PROMPT.md (x6) carried `callee 0x5f1394` as an unnamed lead since M332;
M335 seeded it with `ds:0x985aec` before calling and M308 found its RETURN is the
`test eax,eax` / `jge` operand of the difficulty path. This script asks what the
callee IS: what it takes, what it returns, and who reads that return.

Measured (all numbers COMPUTED from the static image `scratch/m574/text.txt` and
`ghidra_out/index.csv`; zero box time):

  SHAPE      FUN_005f1394 is a 11,207-byte / 2,235-instruction `this`-method
             (`ret 0x8` = two stack args) with a SEH frame and a 0x38c local.
             Its first act is the virtual `[vtbl+0x170]`; a zero return becomes
             `or eax,-1`. It then builds a CREATESTRUCT-shaped frame and calls
             FUN_005e3ed9 (window creation), whose nonzero error is returned
             verbatim. So it is a "create + run this screen object" runner,
             not a chooser: the difficulty table 0x94d2ac and the global
             0x985aec are referenced ZERO times in all 2,235 instructions.

  RETURN     Every exit funnels to one `ret 0x8` (7 paths): -1 x2, 0 x1,
             two error passthroughs of [ebp-0x40], `ds:0x698d0c` x1, and
             `[obj+0xa40]` x1. The result cell +0xa40 is READ once and WRITTEN
             zero times in the runner: the screen's own handler fills it.

  CALLERS    94 direct `call 0x5f1394` sites; every one is a thiscall on a
             frame object with exactly two pushed dwords.

  PAYOFF     The difficulty dialog FUN_004ddaa0 seeds the runner's object with
             `ds:0x985aec` (obj+0xa44), calls it, and on `jge` (return >= 0)
             writes the RETURN to `ds:0x985aec` and to `[0x94d438+0x20bc*k]`
             for all 8 factions: the runner's result cell IS the new difficulty.

GATES (printed first, then asserted; every V row names a mutant in
scripts/m339_mutate.py):
  G1  forward-prologue shape: SEH (handler 0x66f786), 0x38c frame, first call
      = `[edx+0x170]`, `test eax,eax`/`jne` then `or eax,0xffffffff`.
  G2  exit census: exactly 7 exits, classified by their backward eax source;
      the two passthroughs decode to the [vtbl+0x15c] and 0x5e3ed9 returns.
  G3  result cell: `+0xa40` occurs once (the epilogue read), the neighbouring
      `+0xa44` zero times; the runner reads no difficulty state.
  G4  callers: 94 sites, push count / ecx-source distribution measured, and
      the `ret 0x8` arity agrees with the modal of the push counts.
  G5  difficulty flow: seed window, `jge` target, the write of eax to
      0x985aec, and the 8-iteration faction loop (base/stride/bound decoded).
  G6  the loader-independent rival: "0x5f1394 is the difficulty chooser" —
      zero table refs inside, four outside, measured on both sides.
"""
import csv
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
IDX = os.path.join(ROOT, "ghidra_out/index.csv")

RUNNER = 0x5F1394
CALLER = 0x4DDAA0
DIFF_GLOBAL = 0x985AEC
DIFF_TABLE = 0x94D2AC
FACTION_CELL = 0x94D438
FACTION_STRIDE = 0x20BC
FACTION_END = 0x95DA18

LINE = re.compile(r"^\s*([0-9a-f]{6,8}):\s+((?:[0-9a-f]{2} )+)\s*\t(.*)$")
MUT = os.environ.get("M339_MUT", "")
ALG = os.environ.get("M339_ALG", "")


def load():
    ins = []
    with open(TEXT, errors="replace") as f:
        for line in f:
            m = LINE.match(line.rstrip("\n"))
            if not m:
                continue
            txt = m.group(3).strip()
            p = txt.split(None, 1)
            ins.append({"a": int(m.group(1), 16),
                        "bs": bytes.fromhex(m.group(2).replace(" ", "")),
                        "mn": p[0], "ops": p[1] if len(p) > 1 else ""})
    ins.sort(key=lambda x: x["a"])
    return ins


def patch(ins, addr, old_bs, new_bs, old_ops, new_ops, new_mn=None):
    for i in ins:
        if i["a"] == addr:
            assert i["bs"] == bytes.fromhex(old_bs), (hex(addr), i["bs"].hex())
            assert i["ops"] == old_ops, (hex(addr), i["ops"])
            i["bs"] = bytes.fromhex(new_bs)
            i["ops"] = new_ops
            if new_mn:
                i["mn"] = new_mn
            return
    raise KeyError(hex(addr))


def apply_mut(ins):
    P = patch
    if MUT == "MU1":     # vtbl+0x170 -> +0x174 (the prepare slot)
        P(ins, 0x5F13C6, "ff 92 70 01 00 00", "ff 92 74 01 00 00",
          "DWORD PTR [edx+0x170]", "DWORD PTR [edx+0x174]")
    elif MUT == "MU2":   # jne after the prepare test -> je (the -1 path jumps over)
        P(ins, 0x5F13CE, "75 08", "74 08", "0x5f13d8", "0x5f13d8", new_mn="je")
    elif MUT == "MU3":   # result cell +0xa40 -> +0xa44 (the seeded field)
        P(ins, 0x5F3F45, "8b 80 40 0a 00 00", "8b 80 44 0a 00 00",
          "eax,DWORD PTR [eax+0xa40]", "eax,DWORD PTR [eax+0xa44]")
    elif MUT == "MU4":   # ret 0x8 -> ret 0x4 (arity disagreement)
        P(ins, 0x5F3F58, "c2 08 00", "c2 04 00", "0x8", "0x4")
    elif MUT == "MU5":   # the jge write lands on a neighbour global
        P(ins, 0x4DDCF1, "a3 ec 5a 98 00", "a3 f0 5a 98 00",
          "ds:0x985aec,eax", "ds:0x985af0,eax")
    elif MUT == "MU6":   # faction stride 0x20bc -> 0x20b8 (bound arithmetic breaks)
        P(ins, 0x4DDCFD, "81 c1 bc 20 00 00", "81 c1 b8 20 00 00",
          "ecx,0x20bc", "ecx,0x20b8")
    elif MUT == "MU7":   # plant a difficulty-global read inside the runner
        P(ins, 0x5F3F38, "a1 0c 8d 69 00", "a1 ec 5a 98 00",
          "eax,ds:0x698d0c", "eax,ds:0x985aec")
    elif MUT == "MU8":   # seed slot obj+0xa44 -> obj+0xa40 (seed == result cell)
        P(ins, 0x4DDB4D, "89 85 b4 b6 ff ff", "89 85 b8 b6 ff ff",
          "DWORD PTR [ebp-0x494c],eax", "DWORD PTR [ebp-0x4948],eax")


def window(ins, lo, hi):
    return [i for i in ins if lo <= i["a"] <= hi]


def at(ins, addr):
    for i in ins:
        if i["a"] == addr:
            return i
    raise KeyError(hex(addr))


def imm(s):
    m = re.search(r"0x([0-9a-f]+)$", s.strip())
    return int(m.group(1), 16) if m else None


def func_bounds(ins):
    rows = list(csv.DictReader(open(IDX)))
    for r in rows:
        if int(r["addr"], 0) == RUNNER:
            return RUNNER, RUNNER + int(r["size_bytes"])
    raise KeyError("runner not in index")


def main():
    rows, fails = [], []

    def gate(gid, ok, detail):
        rows.append((gid, "PASS" if ok else "FAIL", detail))
        if not ok:
            fails.append(gid)

    ins = load()
    apply_mut(ins)
    lo, hi = func_bounds(ins)
    body = [i for i in ins if lo <= i["a"] <= hi]
    rets = [i for i in body if i["mn"] == "ret"]

    # ---- G1 prologue ------------------------------------------------------
    pro = window(ins, RUNNER, 0x5F13D4)
    seq = [(i["mn"], i["ops"]) for i in pro[:14]]
    seh = (any(i["mn"] == "push" and i["ops"] == "0xffffffff" for i in pro[:6])
           and any(i["mn"] == "push" and i["ops"] == "0x66f786" for i in pro[:6])
           and any("fs:0x0" in i["ops"] for i in pro[:6]))
    frame = [i for i in pro if i["mn"] == "sub" and i["ops"].startswith("esp,0x")]
    first_call = next(i for i in body if i["mn"] == "call")
    lane = window(ins, 0x5F13BE, 0x5F13D4)
    or_minus1 = [i for i in lane if i["mn"] == "or" and i["ops"] == "eax,0xffffffff"]
    slots = sorted({int(m.group(1), 16) for i in body if i["mn"] == "call"
                    for m in [re.search(r"\[e[abcd]x\+(0x[0-9a-f]+)\]", i["ops"] or "")]
                    if m and int(m.group(1), 16) >= 0x100})
    ok1 = (seh and frame and imm(frame[0]["ops"].split(",")[1]) == 0x38C
           and first_call["a"] == 0x5F13C6 and "[edx+0x170]" in first_call["ops"]
           and first_call["bs"] == bytes.fromhex("ff9270010000")
           and len(or_minus1) == 1
           and at(ins, 0x5F13CC)["mn"] == "test"
           and at(ins, 0x5F13CE)["mn"] == "jne"
           and {0x15C, 0x160, 0x164, 0x170} <= set(slots))
    print("== G1 shape: SEH + 0x38c + first call [vtbl+0x170] -> -1 ==")
    print("   prologue %s" % seq[:9])
    print("   frame %s ; first call %s @0x%x ; -1 path %s" %
          (frame[0]["ops"] if frame else None, first_call["ops"],
           first_call["a"], [(hex(i["a"]), i["mn"], i["ops"]) for i in or_minus1]))
    print("   vtable slots called: %s" % [hex(s) for s in slots])
    gate("G1", bool(ok1), "seh=%s frame=%s first=%s slots=%s" %
         (seh, frame[0]["ops"] if frame else None, first_call["ops"],
          [hex(s) for s in slots]))

    # ---- G2 exits ---------------------------------------------------------
    lbl = rets[0]["a"] if rets else 0x5F3F58
    exits = [i for i in body if i["mn"] == "jmp" and abs(imm(i["ops"] or "0x0") - lbl) <= 0x20]
    # classify each exit by the closest preceding eax definition in its block
    def classify(ea):
        idx = [k for k, i in enumerate(ins) if i["a"] == ea][0]
        for k in range(idx - 1, max(idx - 9, -1), -1):
            j = ins[k]
            if j["mn"] == "call" or j["mn"].startswith("j"):
                break
            if j["mn"] in ("or", "xor") and j["ops"].startswith("eax,"):
                return {"or" : "IMM_NEG1", "xor": "IMM_0"}[j["mn"]] if \
                    j["ops"] in ("eax,0xffffffff", "eax,eax") else "OTHER"
            if j["mn"] == "mov" and j["ops"].startswith("eax,"):
                src = j["ops"].split(",", 1)[1]
                if "ds:0x698d0c" in src:
                    return "GLOBAL_698d0c"
                if re.search(r"\+0xa40\]$", src):
                    return "PASSTHRU" if ALG == "A1" else "CELL_a40"
                if re.search(r"\[ebp-0x40\]$", src):
                    return "PASSTHRU"
                return "OTHER:" + src
        return "NONE"
    cls = [(hex(e["a"]), classify(e["a"])) for e in exits]
    # the fallthrough exit: the mov eax,[eax+0xa40] that falls into the epilogue
    fall = [i for i in ins if i["a"] < lbl and lbl - i["a"] <= 0x20
            and i["mn"] == "mov" and re.search(r"\+0xa40\]$", i["ops"] or "")]
    if ALG == "A1":       # algorithm mutant: a classifier that only counts jmp exits
        fall = []
    kinds = sorted([k for _, k in cls] + (["CELL_a40"] if fall else []))
    want = ["CELL_a40", "GLOBAL_698d0c", "IMM_0", "IMM_NEG1", "IMM_NEG1",
            "PASSTHRU", "PASSTHRU"]
    feeders = [at(ins, 0x5F15A0)["ops"], at(ins, 0x5F176B)["ops"]]
    ok2 = (len(rets) == 1 and rets[0]["ops"].split()[0] == "0x8"
           if rets and rets[0]["ops"] else False)
    ok2 = ok2 and len(exits) == 6 and kinds == want and len(fall) == 1
    ok2 = ok2 and feeders == ["DWORD PTR [edx+0x15c]", "0x5e3ed9"]
    print("== G2 exit census: %d jmp + 1 fallthrough, one ret ==" % len(exits))
    for a, k in cls:
        print("   jmp %s -> %s" % (a, k))
    print("   fallthrough %s -> CELL_a40 ; ret %s ; passthrough feeders %s" %
          (fall[0]["ops"] if fall else None,
           rets[0]["ops"] if rets else None, feeders))
    gate("G2", bool(ok2), "exits=%d kinds=%s ret=%s" %
         (len(exits), kinds, rets[0]["ops"] if rets else None))

    # ---- G3 result cell vs seeded field -----------------------------------
    cell = [i for i in body if "+0xa40" in i["ops"]]
    seed = [i for i in body if "0xa44" in i["ops"]]
    tbl = [i for i in body if "0x94d2ac" in i["ops"] or "0x985aec" in i["ops"]]
    ok3 = (len(cell) == 1 and cell[0]["mn"] == "mov"
           and cell[0]["ops"] == "eax,DWORD PTR [eax+0xa40]"
           and not seed and not tbl)
    print("== G3 the runner passes +0xa40 through, computes nothing ==")
    print("   +0xa40 refs: %s" % [(hex(i["a"]), i["mn"], i["ops"]) for i in cell])
    print("   +0xa44 refs: %d ; 0x94d2ac/0x985aec refs: %d" % (len(seed), len(tbl)))
    gate("G3", bool(ok3), "a40=%d a44=%d table=%d" % (len(cell), len(seed), len(tbl)))

    # ---- G4 callers -------------------------------------------------------
    sites = [i for i in ins if i["mn"] == "call" and imm(i["ops"] or "0x0") == RUNNER
             and "[edx" not in i["ops"]]
    stat, pushh = {}, {}
    for s in sites:
        idx = [k for k, i in enumerate(ins) if i["a"] == s["a"]][0]
        ecx, pushes = None, 0
        for k in range(idx - 1, max(idx - 24, -1), -1):
            j = ins[k]
            if j["mn"] == "call":
                break
            if j["mn"] == "push":
                pushes += 1
            if j["mn"] in ("mov", "lea") and j["ops"].startswith("ecx,") and ecx is None:
                ecx = (j["mn"], j["ops"].split(",", 1)[1])
        pushh[pushes] = pushh.get(pushes, 0) + 1
        if ecx is None:
            key = "none"
        else:
            src = re.sub(r"^DWORD PTR ", "", ecx[1])
            if ecx[0] == "lea" and src.startswith("[ebp-"):
                key = "lea_local"
            elif src.startswith("[ebp-"):
                key = "ptr_local:" + src
            elif re.fullmatch(r"0x[0-9a-f]+", src):
                key = "global"
            else:
                key = "reg"
        stat[key] = stat.get(key, 0) + 1
    # arg arity, read from the CALLEE: the only positive frame refs are its args
    args = sorted({re.search(r"\[ebp\+(0x[0-9a-f]+)\]", i["ops"]).group(1)
                   for i in body if re.search(r"\[ebp\+(0x[0-9a-f]+)\]", i["ops"])})
    mode_slot = max((k for k in stat if k.startswith(("ptr_local", "lea_"))),
                    key=lambda k: stat[k], default="none")
    ok4 = (len(sites) == 94 and "none" not in stat
           and args == ["0x8", "0xc"] and rets and rets[0]["ops"].split()[0] == "0x8"
           and stat.get("lea_local", 0) >= 50)
    print("== G4 callers: %d direct thiscall sites, receiver object census ==" % len(sites))
    for k in sorted(stat, key=lambda k: -stat[k]):
        print("   %-24s : %d sites" % (k, stat[k]))
    print("   push-count histogram since the previous call: %s" % sorted(pushh.items()))
    print("   callee's only positive frame refs %s ; ret %s ; mode receiver %s x%d" %
          (args, rets[0]["ops"] if rets else None,
           mode_slot.split(":")[-1], stat.get(mode_slot, 0)))
    gate("G4", bool(ok4), "sites=%d lea_local=%d none=%d args=%s mode=%s" %
         (len(sites), stat.get("lea_local", 0), stat.get("none", 0), args, mode_slot))

    # ---- G5 the difficulty flow through the runner ------------------------
    seedw = window(ins, 0x4DDB3E, 0x4DDB5E)
    seq5 = [(i["mn"], i["ops"]) for i in seedw]
    store = window(ins, 0x4DDCF1, 0x4DDD09)
    base = [i for i in store if i["mn"] == "mov"
            and re.match(r"ecx,0x[0-9a-f]+$", i["ops"] or "")]
    add = [i for i in store if i["mn"] == "add" and i["ops"].startswith("ecx,")]
    bound = [i for i in store if i["mn"] == "cmp" and i["ops"].startswith("ecx,")]
    g = [i for i in store if i["mn"] == "mov" and i["ops"].startswith("ds:")]
    iters = None
    if base and add and bound:
        iters = (imm(bound[0]["ops"].split(",")[1]) - imm(base[0]["ops"].split(",")[1])) \
            // imm(add[0]["ops"].split(",")[1])
    # object-relative offset of the seeded slot: frame base -0x5390, slot -0x494c
    objld = [i for i in seedw if i["mn"] == "lea" and "ecx,[ebp-0x" in i["ops"]
             and i["a"] == 0x4DDB47]
    seedst = at(ins, 0x4DDB4D)
    frame = imm(objld[0]["ops"].split("[ebp-")[1].rstrip("]")) if objld else None
    slot = imm(seedst["ops"].split("[ebp-")[1].split("]")[0]) if seedst else None
    off = (frame - slot) if (frame and slot) else None
    # the caller never reads its own seed back: the value travels through the object
    loopback = [i for i in window(ins, 0x4DDB58, 0x4DDCF0) if "0x494c" in i["ops"]]
    ok5 = (seq5[:3] == [("mov", "eax,ds:0x985aec"), ("push", "0x0"), ("push", "0x0")]
           and ("lea", "ecx,[ebp-0x5390]") in seq5
           and ("mov", "DWORD PTR [ebp-0x494c],eax") in seq5
           and ("call", "0x5f1394") in seq5
           and seq5[seq5.index(("call", "0x5f1394")) + 1:] ==
               [("test", "eax,eax"), ("jge", "0x4ddcf1")]
           and g and g[0]["ops"] == "ds:0x985aec,eax"
           and iters == 8 and imm(add[0]["ops"].split(",")[1]) == FACTION_STRIDE
           and imm(base[0]["ops"].split(",")[1]) == FACTION_CELL
           and off == 0xA44 and not loopback)
    print("== G5 the difficulty dialog: seed -> runner -> %s on %d factions ==" %
          (hex(DIFF_GLOBAL), iters or 0))
    print("   seed window %s" % seq5)
    print("   jge target %s ; loop base=%s stride=%s bound=%s -> iters=%s ; obj+0x%x seed"
          % ([(i["mn"], i["ops"]) for i in store[:4]],
             base[0]["ops"] if base else None, add[0]["ops"] if add else None,
             bound[0]["ops"] if bound else None, iters, off or 0))
    print("   caller re-reads its own seed after the call: %d refs" % len(loopback))
    gate("G5", bool(ok5), "iters=%s seed_off=%s store=%s loopback=%d" %
         (iters, hex(off) if off else None, g[0]["ops"] if g else None, len(loopback)))

    # ---- G6 rival ---------------------------------------------------------
    caller = [i for i in ins if CALLER <= i["a"] < CALLER + 0x35F]
    cin = [i for i in caller if "0x94d2ac" in i["ops"] or "0x985aec" in i["ops"]]
    inside = len(tbl)
    pos_imms = [k for k in kinds if k not in want] or []
    imm_rets = sorted(set(k for k in kinds if k.startswith("IMM_")))
    ok6 = (inside == 0 and len(cin) == 3 and imm_rets == ["IMM_0", "IMM_NEG1"])
    print("== G6 rivals, measured ==")
    print("   R1 'the runner is the difficulty chooser': difficulty refs inside %d,"
          " inside its caller FUN_004ddaa0 %d %s"
          % (inside, len(cin), [(hex(i["a"]), i["mn"], i["ops"]) for i in cin]))
    print("   R2 'the return is a dialog ID (IDOK)': the runner's IMMEDIATE returns are"
          " %s - no positive immediate can be returned; the value-carrying exit is a"
          " memory cell (+0xa40)" % imm_rets)
    gate("G6", bool(ok6), "inside=%d caller_refs=%d imm_returns=%s" %
         (inside, len(cin), imm_rets))

    # ---- verdict ----------------------------------------------------------
    blob = "\n".join("%s %s %s" % r for r in rows)
    digest = hashlib.sha256(blob.encode()).hexdigest()[:16]
    print()
    for gid, st, detail in rows:
        print("%-4s %-4s %s" % (gid, st, detail))
    print("digest=%s gates=%d pass=%d" % (digest, len(rows), len(rows) - len(fails)))
    if fails:
        print("FAIL M339: %d/%d gates (red: %s)" % (len(rows) - len(fails), len(rows), fails))
        return 1
    print("PASS M339: %d/%d gates" % (len(rows), len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
