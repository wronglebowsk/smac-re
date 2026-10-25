#!/usr/bin/env python3
"""M54g probe v2: key the colonist BUILD-BASE order (`b`, FUN_004d1280) — staged.

Session lesson: OCR is ~15 s/poll on this box and the HUD sometimes classifies `unknown`,
so a pane-servicing loop built on OCR spams keys. This probe is MEMORY-FIRST: it polls
+17 / the base array / the record at 100 ms, and OCRs only when memory says something
changed (or at stage end). Stages isolate the cause:

  stage 0  read state; optionally clear +17 on the target (one var)
  stage 1  poke SEL_G only, NO key -> does selection alone open a pane? (memory + 1 OCR)
  stage 2  press `b` -> poll memory 8 s; if the base array changed: NEWBASE accepted
           itself; else OCR once and service the pane with ONE key
  stage 3  with --poke-type: the same test on a type-0 (Colony Pod, class 8) record

Oracle = /proc/pid/mem. One keypress per stage. Never answers a quit-prompt.
"""
import argparse, json, os, struct, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as P

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(ROOT, "evidence", "m54g")
os.makedirs(EVID, exist_ok=True)
BASE_ARR, BASE_SZ, BASE_COUNT_G = 0x95DA10, 304, 0x985AF4
J = lambda o: o.hex() if isinstance(o, bytes) else str(o)


def bases(f):
    n = struct.unpack("<I", P.rd(f, BASE_COUNT_G, 4))[0]
    d = P.rd(f, BASE_ARR, n * BASE_SZ)
    return [dict(idx=i, x=struct.unpack("<h", d[i*BASE_SZ:i*BASE_SZ+2])[0],
                 y=struct.unpack("<h", d[i*BASE_SZ+2:i*BASE_SZ+4])[0],
                 faction=d[i*BASE_SZ+4]) for i in range(n)]


def ours(f):
    return sum(1 for b in bases(f) if b["faction"] == 3)


def ocr_once(tag):
    png = P.freeze(tag)
    w = P.ocr_fast(png)
    k = P.classify(w, P.region_colors(png), png)
    return png, k, P.text_of(w)[:160]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unit", type=int, required=True)
    ap.add_argument("--poke-type", type=int, default=None)
    ap.add_argument("--clear-order", action="store_true")
    ap.add_argument("--key", default="b")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()
    jpath = args.json or os.path.join(EVID, f"probe_{args.unit}.json")

    pid, f = P.mem()
    out = {"pid": pid, "unit": args.unit, "key": args.key, "poke_type": args.poke_type,
           "stages": []}
    R = lambda: P.unit_rec(f, args.unit)
    O = lambda: struct.unpack("<i", P.rd(f, P.SEL_G, 4))[0]

    r0 = R()
    out["stages"].append(dict(stage=0, rec=r0, bases_ours=ours(f), sel=O()))
    print(f"S0 rec{args.unit} x{r0['x']} y{r0['y']} type{r0['type']} order{r0['order']} "
          f"mp{r0['mpused']} sel={O()} bases_ours={ours(f)}", flush=True)

    if args.clear_order and r0["order"] != 0:
        P.wr(f, P.UNIT_ARR + args.unit * 52 + 17, b"\x00")
        print("S0b cleared +17 ->", P.rd(f, P.UNIT_ARR + args.unit * 52 + 17, 1)[0], flush=True)

    if args.poke_type is not None:
        P.wr(f, P.UNIT_ARR + args.unit * 52 + 10, struct.pack("<H", args.poke_type))
        back = struct.unpack("<H", P.rd(f, P.UNIT_ARR + args.unit * 52 + 10, 2))[0]
        out["stages"].append(dict(stage="poke10", readback=back))
        print(f"S0c poked +10 -> {args.poke_type}, read back {back}", flush=True)

    # stage 1: selection only
    P.focus()
    P.wr(f, P.SEL_G, struct.pack("<i", args.unit))
    time.sleep(1.2)
    png, k, txt = ocr_once("sel")
    out["stages"].append(dict(stage=1, sel=O(), kind=k, text=txt))
    print(f"S1 sel={O()} kind={k} :: {txt[:90]}", flush=True)
    pane_open = k not in ("hud", None)
    if pane_open:
        os.system(f"cp {png} {EVID}/s1_{k}.png")

    # stage 2: the key
    b0 = ours(f)
    P.sh(f'xdotool key --clearmodifiers "{args.key}"')
    print(f"S2 pressed {args.key}", flush=True)
    t0, changed = time.time(), None
    while time.time() - t0 < 8:
        ob = P.rd(f, P.UNIT_ARR + args.unit * 52 + 17, 1)[0]
        nb = ours(f)
        if nb != b0:
            changed = f"bases_ours {b0}->{nb} at +17={ob} t={time.time()-t0:.2f}"
            break
        if ob != 0:
            changed = f"+17={ob:#x} t={time.time()-t0:.2f}"
            break
        time.sleep(0.1)
    sel_now = O()
    png2, k2, txt2 = ocr_once("key")
    out["stages"].append(dict(stage=2, changed=changed, bases_ours=ours(f), order=P.rd(
        f, P.UNIT_ARR + args.unit * 52 + 17, 1)[0], sel=sel_now, kind=k2, text=txt2))
    print(f"S2 memory: {changed} | sel now {sel_now} | kind {k2} :: {txt2[:90]}", flush=True)
    if k2 not in ("hud", "unknown", None):
        os.system(f"cp {png2} {EVID}/s2_{k2}.png")
        if k2 == "quit-prompt":
            print("S2 quit-prompt NOT answered", flush=True)
        elif k2 == "base":
            P.key("Escape"); time.sleep(1.0)
            png3, k3, txt3 = ocr_once("esc")
            out["stages"].append(dict(stage="esc", kind=k3, text=txt3))
            print(f"S3 after Escape kind={k3} :: {txt3[:90]}", flush=True)
        else:
            P.key("Return"); time.sleep(1.2)
            png3, k3, txt3 = ocr_once("ret")
            out["stages"].append(dict(stage="ret", kind=k3, text=txt3))
            print(f"S3 after Return kind={k3} :: {txt3[:90]}", flush=True)
            if k3 == "base":
                P.key("Escape"); time.sleep(1.0)
                print("S3 base screen closed with Escape", flush=True)

    r1 = R()
    out["stages"].append(dict(stage=9, rec=r1, bases_ours=ours(f), base_list=bases(f)))
    print(f"S9 rec{args.unit} x{r1['x']} y{r1['y']} type{r1['type']} order{r1['order']} "
          f"bases_ours={ours(f)}", flush=True)
    for b in bases(f):
        if b["faction"] == 3:
            print("OUR BASE:", b, flush=True)
    with open(jpath, "w") as fh:
        json.dump(out, fh, indent=1, default=J)
    print("wrote", jpath)


if __name__ == "__main__":
    main()
