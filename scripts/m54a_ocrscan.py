#!/usr/bin/env python3
"""M54a fixture survey: OCR every evidence PNG once, dump the features the
classifier cares about (base-word positions, TURN COMPLETE y, flatness counts).

Written because classify() must stop firing `base` on HUD message-pane text, and the
fix needs to be checked against BOTH kinds of screen. Output: evidence/m54a/ocrscan.json
(one record per png: n words, base-word hit coords, button centre, region colour counts,
classify() before the fix). ~7 s/png, so run it backgrounded.
"""
import glob, json, os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import smac_play as sp  # noqa: E402

OUT = os.path.join(ROOT, "evidence", "m54a", "ocrscan.json")
SCRATCH = "/tmp/m54a_scan"          # ocr() writes its 2x sibling NEXT TO the input, so
                                    # scanning straight out of evidence/ litters it with
                                    # _3x/_3x_3x derivatives (and then scans those too).


def scan(png):
    os.makedirs(SCRATCH, exist_ok=True)
    work = os.path.join(SCRATCH, os.path.basename(png))
    if not os.path.exists(work):
        shutil.copyfile(png, work)
    w = sp.ocr_fast(work)
    t = sp.text_of(w).lower()
    hits = {b: [[int(cx), int(cy)] for tt, cx, cy, _x, _h in w if b in tt.lower()]
            for b in sp.BASE_WORDS if b in t}
    btn = sp.find(w, ["complete"])
    rec = {
        "png": os.path.basename(png),
        "n": len(w),
        "basewords": hits,
        "complete": [round(btn[0]), round(btn[1])] if btn else None,
        "nc": sp.region_colors(png),
        "nt": sp.region_colors(png, sp.TEXTCOL),
        "classify_before": sp.classify(w, sp.region_colors(png), png),
        "text": t[:400],
    }
    return rec


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    pats = [p for p in sorted(glob.glob(os.path.join(ROOT, "evidence", "*.png")))
            if "_3x" not in p]
    pats += sorted(p for p in glob.glob(os.path.join(ROOT, "evidence", "m54a", "*.png"))
                   if "_3x" not in p)
    done = {}
    if os.path.exists(OUT):
        for r in json.load(open(OUT)):
            done[r["png"]] = r
    out = []
    for p in pats:
        k = os.path.basename(p)
        if k in done:
            out.append(done[k])
            continue
        try:
            rec = scan(p)
        except Exception as e:  # a bad png must not kill the survey
            rec = {"png": k, "error": repr(e)[:120]}
        out.append(rec)
        print(f"{k} n={rec.get('n')} cls={rec.get('classify_before')} "
              f"btn={rec.get('complete')} bw={list(rec.get('basewords', {}))}", flush=True)
        json.dump(out, open(OUT, "w"), indent=1)
    print("WROTE", OUT, len(out), "records", flush=True)


if __name__ == "__main__":
    main()
