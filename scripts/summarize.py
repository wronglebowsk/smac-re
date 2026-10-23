#!/usr/bin/env python3
"""Label every indexed function with a one-sentence description from the local 125B.

This is the expensive, one-time enrichment pass (`docs/SEARCH.md`). Output is
`index/summaries.jsonl`, one row per function, keyed by a hash of the decompiled body, so a
rerun only touches functions that actually changed.

    python3 scripts/summarize.py --dry-run      # how much work is left
    python3 scripts/summarize.py                # run until done (resumable)
    python3 scripts/summarize.py --limit 50     # smoke test

The model is a reasoning model: without `enable_thinking: false` it spends the whole token
budget thinking and returns an empty string (300 tokens, no answer). With it off, ~18 tokens
and <1 s per function.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from index import ROOT, SUMMARIES, body_hash, iter_functions  # noqa: E402

LLM = os.environ.get("SUMMARY_URL", "http://192.168.1.12:8080/v1/chat/completions")
MODEL = os.environ.get("SUMMARY_MODEL", "qwen125b")
MAX_BODY = 8000
PROMPT = ("Label this decompiled C function for a code-search index. Reply with ONE plain-English "
          "sentence, max 25 words, no preamble, no code, no quotes. Say what it does and, if "
          "apparent, which game concept it touches (bases, units, minerals, energy, terraform, "
          "diplomacy, UI).\n\n```c\n{body}\n```")


def load_done():
    done = {}
    if os.path.isfile(SUMMARIES):
        for line in open(SUMMARIES, encoding="utf-8"):
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            done[row["addr"]] = row.get("hash")
    return done


def valid(text):
    if not text:
        return False
    t = text.strip().strip('"').strip("`")
    words = t.split()
    if not (3 <= len(words) <= 45):
        return False
    if "```" in t or t.startswith(("Function FUN_", "I cannot", "I'm sorry", "Unable")):
        return False
    return True


def label(body, retries=1):
    payload = {"model": MODEL,
               "messages": [{"role": "user", "content": PROMPT.format(body=body[:MAX_BODY])}],
               "max_tokens": 120, "temperature": 0, "top_p": 1,
               "chat_template_kwargs": {"enable_thinking": False}}
    for attempt in range(retries + 1):
        req = urllib.request.Request(LLM, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                body_json = json.loads(r.read())
            text = (body_json["choices"][0]["message"].get("content") or "").strip()
            if valid(text):
                return re.sub(r"\s+", " ", text)
        except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
            if attempt == retries:
                raise SystemExit(f"LLM endpoint failed: {exc}")
            time.sleep(3)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--min-bytes", type=int, default=0, help="skip functions smaller than this")
    ap.add_argument("--include-all", action="store_true", help="include boilerplate functions")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    todo = []
    done = load_done()
    for f in iter_functions(args.include_all):
        if f["size"] < args.min_bytes:
            continue
        if done.get(f["addr"]) == body_hash(f["body"]):
            continue
        todo.append(f)
    print(f"{len(todo)} functions to label ({len(done)} already cached), "
          f"est {len(todo) * 1.35 / 3600:.2f} h", flush=True)
    if args.dry_run or not todo:
        return 0

    os.makedirs(os.path.dirname(SUMMARIES), exist_ok=True)
    t0 = time.time()
    written = failed = 0
    with open(SUMMARIES, "a", encoding="utf-8") as out:
        for i, f in enumerate(todo, 1):
            if args.limit and written >= args.limit:
                break
            summary = label(f["body"])
            if not summary:
                failed += 1
            else:
                out.write(json.dumps({"addr": f["addr"], "hash": body_hash(f["body"]),
                                      "summary": summary, "model": MODEL,
                                      "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
                                     ensure_ascii=False) + "\n")
                out.flush()
                written += 1
            if i % 25 == 0:
                rate = i / max(1e-9, time.time() - t0)
                eta = (len(todo) - i) / rate / 60 if rate else 0
                print(f"  {i}/{len(todo)}  {rate:.2f} fn/s  eta {eta:.0f} min  "
                      f"failed {failed}", flush=True)
    dt = time.time() - t0
    print(f"done: {written} written, {failed} failed, {dt / 60:.1f} min "
          f"({written / dt:.2f} fn/s) -> {os.path.relpath(SUMMARIES, ROOT)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
