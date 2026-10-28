#!/usr/bin/env python3
"""M74 — WHO sets `type[+0x30] & 4`, and WHEN.

M73 proved the bit is the switch that turns the 50 % production markup off inside
`0x5ac950` (test at `0x5ac99c`), and that it is live STATE: head 193 read `0x41` at arm and
`0x45` at its first visit, in one window, after a designed unit completed.  M73 left the
"who" to two static candidates, `0x4eec30` and `0x4d20f0`.  This instrument starts from the
whole `.text` instead of two guesses: the type-record flags word is addressed ABSOLUTELY
(`[reg*4+0x98adb8]` / `[reg+0x98adb8]`), so every access to it is greppable, and the complete
set of writers of bit 2 is NINE sites in FOUR functions (the byte ops and the whole-word
writes, both counted):

  W1 0x4eed18 FUN_004eec30  or  BYTE [ebx*4+0x98adb8],4   tid in ebx; the store is guarded by
                                                            `0x3f < param_2`, i.e. only a DESIGNED
                                                            type, and it is the NEW type of a
                                                            unit transformation (the same function
                                                            clears bit 0 on the OLD type at
                                                            `0x4eed2b and BYTE[..],0xfe`)
  W2 0x573fed FUN_00573a90  or  BYTE [eax*4+0x98adb8],4
  W3 0x574107 FUN_00573a90  or  BYTE [ebx+0x98adb8],4     ebx = the record byte address
  W4 0x574117 FUN_00573a90  or  BYTE [ebx+0x98adb8],4
  W5 0x595f82 FUN_00595b10  mov WORD [esi+0x98adb8],1     whole-word write: CLEARS bit 2
  W6 0x595f91 FUN_00595b10  mov WORD [esi+0x98adb8],0x105 whole-word write: SETS bit 2
  W7 0x595f9c FUN_00595b10  mov WORD [esi+0x98adb8],0x115 whole-word write: SETS bit 2
  W8 0x59d273 FUN_0059ce10  or  BYTE [eax*4+0x98adb8],4   guarded by `type[+0x30]&1` and the
                                                            owner mask `type[+0x2c]`
  W9 0x59db65 FUN_0059ce10  or  BYTE [ecx*4+0x98adb8],4

`0x4d20f0` (M73's second candidate) is NOT in that set: inside it the only touches of
`0x98adb8` are reads — `mov ax,BYTE[..]` at `0x4d258e`, `test BYTE[..],4` at `0x4d2f35` and
`0x4d3277`.  That is a CONFLICT with the M73 note and it is reported, not fixed by this run.

Shape: clear bit 2 on two armed designed ids (controlled poke, read back), arm 9 CONDITIONAL
writer breakpoints (each conditioned on the armed ids, so only writes to OUR records print) plus
the `0x4efa5e` visit gate (which prints the flag as the visit sees it), census all 256 type
records' +0x30 before and after, drive real turn boundaries with the base's storage re-poked and
read back before each one, then attribute every observed 0 -> 1 flip to a fired site.

Gates (10, all FAIL-closed):
  1 armed      gdb armed on the named base; both armed ids in the first six queue slots; bit 2
               cleared on both and READ BACK before attaching
  2 mapped     every W row's pc is one of the nine static sites (an unmapped pc FAILs)
  3 fired      at least one writer row fired for an armed id in the window
  4 completion a designed head actually completed: pending fell, the head changed, storage fell,
               and a POSAFF row for the armed base exists (all read back, not inferred)
  5 attributed every armed id whose bit 2 went 0 -> 1 has a writer row naming it, and no flip
               happened without one (a flip with no writer is a FAIL, not a shrug)
  6 direction  the fired site's write (or 4 / = 1 / = 0x105 / = 0x115) matches the observed
               transition — a whole-word `= 1` cannot explain a 0 -> 1
  7 onevar     no OTHER type record changed bit 2 in the window unless a writer row names it;
               any such record is reported and the gate FAILs (confounded)
  8 stability  the base is still the same base by name at the same address, the round advanced,
               every boundary returned rc=0
  9 parse      every non-chatter log line parsed into a known tag
  10 clean     gdb is gone and the game's TracerPid is back to 0

Usage:
    python3 scripts/m74_flag_watch.py [--base-name "University Base"] [--ids 193,194]
                                      [--boundaries 4] [--poke-minerals 200] [--no-poke-flags]
                                      [--timeout 500] [--tag m74flag]
"""
import argparse
import json
import os
import re
import signal
import struct
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import m55_boundary as M          # noqa: E402
import m56_build as B             # noqa: E402

BASE_ARR, BASE_SZ = 0x95DA10, 304
TYPE_ARR, TYPE_STRIDE, FLAG_ADDR = 0x98AD88, 0x34, 0x98ADB8
POSAFF = 0x4EFA5E
N_TYPES = 256
EVID = os.path.join(ROOT, "evidence")

# (addr, tag, function, what the store is, does it SET bit 2, does it CLEAR bit 2)
SITES = (
    (0x4EED18, "W1", "FUN_004eec30", "or BYTE [ebx*4+0x98adb8],4", True, False),
    (0x573FED, "W2", "FUN_00573a90", "or BYTE [eax*4+0x98adb8],4", True, False),
    (0x574107, "W3", "FUN_00573a90", "or BYTE [ebx+0x98adb8],4", True, False),
    (0x574117, "W4", "FUN_00573a90", "or BYTE [ebx+0x98adb8],4", True, False),
    (0x595F82, "W5", "FUN_00595b10", "mov WORD [esi+0x98adb8],1", False, True),
    (0x595F91, "W6", "FUN_00595b10", "mov WORD [esi+0x98adb8],0x105", True, False),
    (0x595F9C, "W7", "FUN_00595b10", "mov WORD [esi+0x98adb8],0x115", True, False),
    (0x59D273, "W8", "FUN_0059ce10", "or BYTE [eax*4+0x98adb8],4", True, False),
    (0x59DB65, "W9", "FUN_0059ce10", "or BYTE [ecx*4+0x98adb8],4", True, False),
)
SITE_BY_ADDR = {s[0]: s for s in SITES}
SITE_BY_TAG = {s[1]: s for s in SITES}


# ---------------------------------------------------------------- memory
def game_pid():
    return M.find_pid()


def base_row(m, name):
    for i in range(max(0, min(B.rd32(m, 0x985AF4), 64))):
        b = B.prod_fields(m, i)
        if b["name"] == name:
            rec = M.rd(m, BASE_ARR + i * BASE_SZ, BASE_SZ)
            b["slots"] = [struct.unpack("<i", rec[0x50 + 4 * k:0x54 + 4 * k])[0] for k in range(12)]
            b["addr"] = BASE_ARR + i * BASE_SZ
            tl = M.timeline_row(m)
            b["year"], b["round"], b["cur_player"] = tl["year"], tl["round"], tl["cur_player"]
            return b
    raise SystemExit(f"base {name!r} not found in the base array")


def flag_census(m, n=N_TYPES):
    """Every type record's +0x30 dword, by id.  Bit 2 is the markup switch M73 named.

    The records are 52 bytes apart, so this reads the whole span once and slices at the stride.
    """
    raw = M.rd(m, TYPE_ARR, TYPE_STRIDE * n)
    return {t: struct.unpack("<I", raw[t * TYPE_STRIDE + 0x30:
                                    t * TYPE_STRIDE + 0x34])[0] for t in range(n)}


def flags30(m, ids):
    out = {}
    for t in ids:
        out[t] = struct.unpack("<I", M.rd(m, TYPE_ARR + t * TYPE_STRIDE + 0x30, 4))[0]
    return out


# ---------------------------------------------------------------- gdb
TMPL = r"""set pagination off
set confirm off
set height 0
set verbose off
set can-use-hw-watchpoints 1
set $b = @@ADDR@@
@@BREAKS@@printf "ARMED base=0x%x head=%d pending=%d storage=%d\n", $b, *(int *)($b + 0x50), *(int *)($b + 0x4c), *(int *)($b + 0x40)
continue
"""

# one breakpoint block: the condition keeps every OTHER type record out of the log, so a
# writer row is by construction a write to one of the armed records.
BLOCK = r"""break *@@ADDR@@ if @@COND@@
commands
silent
printf "@@FMT@@\n", @@ARGS@@
continue
end
"""
POSAFF_BLOCK = r"""break *0x4efa5e if *(int *)0x8f0d60 == $b
commands
silent
printf "POSAFF storage=%d edi=%d id=%d f30=0x%x\n", *(int *)($b + 0x40), $edi, $ebx, *(unsigned char *)($ebx * 4 + 0x98adb8)
continue
end
"""
# tid register / record-address expression per site, straight from the instruction bytes.
# (tid expression, record-address expression, extra format text, extra argument expression)
SITE_EXPR = {
    "W1": ("$ebx", "$ebx * 4 + 0x98adb8", "own=%d", "*(int *)($ebp + 8)"),
    "W2": ("$eax", "$eax * 4 + 0x98adb8", "", ""),
    "W3": ("($ebx - 0x98adb8) / 4", "$ebx", "", ""),
    "W4": ("($ebx - 0x98adb8) / 4", "$ebx", "", ""),
    "W5": ("($esi - 0x98adb8) / 4", "$esi", "word=1", ""),
    "W6": ("($esi - 0x98adb8) / 4", "$esi", "word=0x105", ""),
    "W7": ("($esi - 0x98adb8) / 4", "$esi", "word=0x115", ""),
    "W8": ("$eax", "$eax * 4 + 0x98adb8", "", ""),
    "W9": ("$ecx", "$ecx * 4 + 0x98adb8", "", ""),
}


def gdb_script(addr, ids):
    """The gdb script: 9 conditional writer breakpoints + the visit gate, 10 total."""
    cond_idx = " || ".join(f"$X == {i}" for i in ids)
    cond_rec = " || ".join(f"$X == {FLAG_ADDR + i * 4:#x}" for i in ids)
    blocks = []
    for site_addr, tag, _fn, what, _sets, _clears in SITES:
        tid, rec, extra_fmt, extra_arg = SITE_EXPR[tag]
        mreg = re.search(r"\[(\w+)\*4\+0x98adb8\]", what) or re.search(r"\[(\w+)\+0x98adb8\]", what)
        reg = "$" + mreg.group(1).lower()
        # ebx/esi hold the RECORD ADDRESS at W3-W7, the INDEX everywhere else
        cond = (cond_rec if tag in ("W3", "W4", "W5", "W6", "W7") else cond_idx).replace("$X", reg)
        fmt = f"{tag} site={site_addr:#x} tid=%d f30=0x%x" + (
              (" " + extra_fmt) if extra_fmt else "")
        args = [tid, f"*(unsigned char *)({rec})"] + ([extra_arg] if extra_arg else [])
        blocks.append(BLOCK.replace("@@ADDR@@", "%#x" % site_addr).replace("@@COND@@", cond)
                      .replace("@@FMT@@", fmt).replace("@@ARGS@@", ", ".join(args)))
    blocks.append(POSAFF_BLOCK)
    return (TMPL.replace("@@ADDR@@", hex(addr))
            .replace("@@BREAKS@@", "".join(blocks)))


LINE = re.compile(r"^(ARMED|POSAFF|W[1-9])\s*(.*)$")
KV = re.compile(r"(\w+)=(-?0x[0-9a-f]+|-\d+|\d+)")
CHATTER = ("warning:", "Reading symbols", "0x", "Breakpoint", "[", "The program", "This GDB",
           "Enable debuginfod", "<https://debuginfod", "Debuginfod has been disabled",
           "To make this setting", "Thread ", "received signal SIGINT")


def parse(text):
    """Pure: gdb log text -> ordered event rows.  Returns (events, unparsed_lines)."""
    ev, bad = [], []
    for raw in text.splitlines():
        s = raw.strip()
        if not s:
            continue
        m = LINE.match(s)
        if not m:
            if s.startswith(CHATTER):
                continue
            bad.append(s)
            continue
        d = {"tag": m.group(1)}
        for k, v in KV.findall(m.group(2) or ""):
            neg = v.startswith("-")
            body = v[1:] if neg else v
            n = int(body, 16) if body.lower().startswith("0x") else int(body)
            d[k] = -n if neg else n
        ev.append(d)
    return ev, bad


# ---------------------------------------------------------------- acceptance
def score(armed, census_before, census_after, ev, ids, poke_reads, after, rc_ok, bad_lines,
          tracer_after):
    """Pure: everything the run read back -> (ok, gates, findings)."""
    g = []

    def gate(name, good, detail):
        g.append((name, bool(good), detail))

    wrows = [e for e in ev if e["tag"].startswith("W")]
    pos = [e for e in ev if e["tag"] == "POSAFF"]

    # 1 armed
    armed_ids_in_queue = [t for t in ids if t in armed["slots"][:6]]
    gate("armed", armed.get("armed_ok") and len(armed_ids_in_queue) == len(ids)
         and all(w & ~0x04 == back or (w & 4) == 0 for _t, w, back in poke_reads)
         and all((back & 4) == 0 for _t, _w, back in poke_reads),
         f"ARMED row {bool(armed.get('armed_ok'))}, armed ids {ids} in queue "
         f"{armed['slots'][:6]}, bit 2 poke read back "
         + ", ".join(f"id {t}: 0x{w:02x}->0x{b:02x}" for t, w, b in poke_reads))

    # 2 mapped
    unmapped = sorted({e.get("site") for e in wrows if e.get("site") not in SITE_BY_ADDR})
    gate("mapped", not unmapped,
         f"{len(wrows)} writer rows, unmapped pcs {[hex(u) for u in unmapped]}" if unmapped
         else f"{len(wrows)} writer rows, every pc in the nine static sites")

    # 3 fired
    fired_ids = sorted({e["tid"] for e in wrows if e["tid"] in ids})
    gate("fired", bool(wrows), f"writer rows on armed ids: {fired_ids or 'NONE'}")

    # 4 completion
    comp = (armed["pending"] > after["pending"] and armed["slots"][0] != after["slots"][0]
            and armed["minerals"] > after["minerals"] and bool(pos))
    gate("completion", comp,
         f"read back: pending {armed['pending']}->{after['pending']}, head "
         f"{armed['slots'][0]}->{after['slots'][0]}, storage {armed['minerals']}->"
         f"{after['minerals']}, POSAFF rows {len(pos)}")

    # 5 attributed
    flipped = [t for t in ids
               if not (census_before.get(t, 0) & 4) and (census_after.get(t, 0) & 4)]
    named = {e["tid"] for e in wrows}
    unattributed = [t for t in flipped if t not in named]
    cleared = [t for t in ids if (census_before.get(t, 0) & 4) and not (census_after.get(t, 0) & 4)]
    gate("attributed", (not wrows) or (not unattributed),
         f"armed ids that went 0->1: {flipped}; writer rows name {sorted(named)}; unattributed "
         f"{unattributed}; 1->0 {cleared}")

    # 6 direction
    bad_dir = []
    for t in flipped:
        rows = [e for e in wrows if e["tid"] == t and e["site"] in SITE_BY_ADDR]
        if rows and not any(SITE_BY_ADDR[e["site"]][4] for e in rows):
            bad_dir.append((t, [SITE_BY_TAG[e["tag"]][2] for e in rows]))
    for t in cleared:
        rows = [e for e in wrows if e["tid"] == t and e["site"] in SITE_BY_ADDR]
        if rows and not any(SITE_BY_ADDR[e["site"]][5] for e in rows):
            bad_dir.append((t, "cleared but no clearing site fired"))
    gate("direction", not bad_dir, f"transition-vs-site mismatches: {bad_dir or 'none'}")

    # 7 one-variable
    others = sorted(t for t in census_before
                    if bool(census_before[t] & 4) != bool(census_after.get(t, 0) & 4)
                    and t not in ids)
    unexplained = [t for t in others if t not in named]
    gate("onevar", not unexplained,
         f"records outside the armed set whose bit 2 changed: {others}; not named by a writer "
         f"row (confounded): {unexplained}")

    # 8 stability
    gate("stability", after["addr"] == armed["addr"] and after["round"] > armed["round"]
         and rc_ok,
         f"base addr 0x{armed['addr']:x} -> 0x{after['addr']:x}, round {armed['round']} -> "
         f"{after['round']}, boundaries rc={'all 0' if rc_ok else 'a non-zero rc'}")

    # 9 parse
    gate("parse", not bad_lines, f"{len(bad_lines)} unparsed log lines"
         + (f": {bad_lines[:3]}" if bad_lines else ""))

    # 10 clean
    gate("clean", tracer_after == "0", f"TracerPid after detach: {tracer_after}")

    ok = all(x[1] for x in g)
    find = []
    by_site = {}
    for e in wrows:
        by_site.setdefault((e["site"], e["tid"]), 0)
        by_site[(e["site"], e["tid"])] += 1
    for (site, tid), n in sorted(by_site.items()):
        s = SITE_BY_ADDR.get(site)
        if s is None:
            find.append(f"writer pc {site:#x} is NOT one of the nine static sites ({n}x on id {tid})")
            continue
        find.append(f"{s[1]} {s[2]} @ {site:#07x} ({s[3]}) fired {n}x on id {tid}")
    for e in pos[:4]:
        find.append(f"POSAFF id {e['id']} f30=0x{e['f30']:02x} edi {e['edi']} storage {e['storage']} "
                    f"-> markup {'OFF' if e['f30'] & 4 else 'ON'} at the visit")
    find.append("census: bit 2 set on " + str(sorted(t for t in census_after if census_after[t] & 4))
                + " after, " + str(sorted(t for t in census_before if census_before[t] & 4)) + " before")
    return ok, g, find


# ---------------------------------------------------------------- run
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-name", default="University Base")
    ap.add_argument("--ids", default="193,194")
    ap.add_argument("--boundaries", type=int, default=4)
    ap.add_argument("--poke-minerals", type=int, default=200)
    ap.add_argument("--no-poke-flags", dest="poke_flags", action="store_false",
                    help="leave type[+0x30] alone (default: clear bit 2 on each armed id so the "
                         "engine has to re-set it inside the window)")
    ap.set_defaults(poke_flags=True)
    ap.add_argument("--timeout", type=float, default=500.0)
    ap.add_argument("--tag", default="m74flag")
    a = ap.parse_args()
    ids = [int(x) for x in a.ids.split(",")]
    if len(ids) < 2:
        raise SystemExit("--ids needs two designed ids to discriminate")
    if any(i < 0x40 for i in ids):
        raise SystemExit("--ids must both be designed ids (>= 0x40)")

    if subprocess.run(["pgrep", "-x", "gdb"], capture_output=True, text=True).stdout.strip():
        raise SystemExit("a gdb is already running — stop it first")
    pid = game_pid()
    tracer = subprocess.run(["grep", "-m1", "TracerPid", "/proc/%d/status" % pid],
                            capture_output=True, text=True).stdout.split()[-1]
    if tracer != "0":
        raise SystemExit("TracerPid=%s != 0" % tracer)
    if subprocess.run(["sysctl", "-n", "kernel.yama.ptrace_scope"],
                      capture_output=True, text=True).stdout.strip() != "0":
        raise SystemExit("ptrace_scope != 0")

    poke_reads = []
    if a.poke_flags:
        for t in ids:
            addr = TYPE_ARR + t * TYPE_STRIDE + 0x30
            with open(f"/proc/{pid}/mem", "rb+", 0) as m:
                m.seek(addr)
                was = m.read(1)[0]
                m.seek(addr)
                m.write(bytes([was & ~0x04]))
                m.seek(addr)
                poke_reads.append((t, was, m.read(1)[0]))
        print("flag poke (type[+0x30] bit 2 cleared, read back): " + ", ".join(
              f"id {t}: 0x{was:02x} -> 0x{back:02x}" for t, was, back in poke_reads), flush=True)

    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        armed = base_row(m, a.base_name)
        census_before = flag_census(m)
    pos = {t: k for k, t in enumerate(armed["slots"]) if t in ids}
    if not pos or max(pos.values(), default=99) >= 6:
        raise SystemExit(f"arm gate: armed ids {ids} are not in the first six queue slots "
                         f"({armed['slots'][:6]}) — enqueue them first")
    flagged_before = sorted(t for t in census_before if census_before[t] & 4)
    print(f"static (read before attach): base {a.base_name!r} addr 0x{armed['addr']:x} owner "
          f"{armed['fac']} queue {armed['slots'][:6]} pending {armed['pending']} storage "
          f"{armed['minerals']} round {armed['round']}\n  records carrying +0x30 bit 2 before: "
          f"{flagged_before}", flush=True)

    def poke_storage(addr, value):
        with open(f"/proc/{pid}/mem", "rb+", 0) as m:
            m.seek(addr + 0x40)
            m.write(struct.pack("<i", value))
            m.seek(addr + 0x40)
            return struct.unpack("<i", m.read(4))[0]

    poke_storage(armed["addr"], a.poke_minerals)
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        armed = base_row(m, a.base_name)
    print(f"  storage poked to {a.poke_minerals}, read back {armed['minerals']}", flush=True)

    gpath = os.path.join(ROOT, "scratch", f"{a.tag}.gdb")
    lpath = os.path.join(EVID, f"{a.tag}.gdblog")
    os.makedirs(os.path.dirname(gpath), exist_ok=True)
    open(gpath, "w").write(gdb_script(armed["addr"], ids))
    log = open(lpath, "w")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath, "-p", str(pid)],
                         stdout=log, stderr=subprocess.STDOUT)
    time.sleep(3.0)
    head = open(lpath, "r", errors="replace").read()
    armed["armed_ok"] = "ARMED" in head
    if not armed["armed_ok"]:
        os.kill(g.pid, signal.SIGINT)
        time.sleep(1.0)
        raise SystemExit("gdb did not arm:\n" + head[-1500:])
    print(f"armed: head {armed['slots'][0]} pending {armed['pending']} storage "
          f"{armed['minerals']} (read back); 10 breakpoints attached", flush=True)

    t0 = time.time()
    rc_ok = True
    for k in range(a.boundaries):
        poke_storage(armed["addr"], a.poke_minerals)
        with open(f"/proc/{pid}/mem", "rb", 0) as m:
            row = base_row(m, a.base_name)
        print(f"  re-poke before boundary {k}: storage read back {row['minerals']} (head "
              f"{row['slots'][0]} pending {row['pending']})", flush=True)
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "smac_play.py"),
                            "--turns", "1", "--timeout", str(int(min(a.timeout, 220))),
                            "--no-escape", "3000", "--orders-per-turn", "1",
                            "--verbose", "--tag", f"{a.tag}_r{k}"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            rc_ok = False
        print(f"  boundary {k}: rc={r.returncode} t={time.time()-t0:.0f}s "
              f"{r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ''}", flush=True)

    try:
        os.kill(g.pid, signal.SIGINT)
    except ProcessLookupError:
        pass
    for _ in range(40):
        if not os.path.exists("/proc/%d" % g.pid):
            break
        time.sleep(0.5)
    subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
    log.close()

    tracer_after = subprocess.run(["grep", "-m1", "TracerPid", "/proc/%d/status" % pid],
                                  capture_output=True, text=True).stdout.split()[-1]
    with open(f"/proc/{pid}/mem", "rb", 0) as m:
        after = base_row(m, a.base_name)
        census_after = flag_census(m)
    text = open(lpath, "r", errors="replace").read()
    ev, bad = parse(text)
    with open(os.path.join(EVID, f"{a.tag}_seq.jsonl"), "w") as fh:
        for d in ev:
            fh.write(json.dumps(d) + "\n")

    print("--- ordered stream (armed records only) ---")
    for e in ev:
        print("  " + " ".join(f"{k}={v}" for k, v in e.items()))
    print(f"read back: head {armed['slots'][0]} -> {after['slots'][0]}  pending {armed['pending']} "
          f"-> {after['pending']}  queue {armed['slots'][:4]} -> {after['slots'][:4]}  storage "
          f"{armed['minerals']} -> {after['minerals']}  round {armed['round']} -> {after['round']}")
    for t in ids:
        print(f"  id {t}: +0x30 0x{census_before[t]:08x} -> 0x{census_after[t]:08x}")
    ok, gates, find = score(armed, census_before, census_after, ev, ids, poke_reads, after,
                            rc_ok, bad, tracer_after)
    print("--- gates ---")
    for name, good, detail in gates:
        print(f"  [{'PASS' if good else 'FAIL'}] {name}: {detail}")
    print("--- findings ---")
    for f in find:
        print("  " + f)
    print(f"log {os.path.relpath(lpath, ROOT)} ({len(ev)} events)")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
