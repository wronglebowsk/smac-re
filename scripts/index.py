#!/usr/bin/env python3
"""Semantic index over two corpora: decompiled functions and session notes.

The index is derived data: `index/chunks.jsonl` (the text + a pointer back),
`index/vectors.f32` (one L2-normalised 768-float vector per chunk, row major) and
`index/meta.json`. Delete it and rebuild at any time; the sources are authoritative.

    python3 scripts/index.py build              # incremental (seconds)
    python3 scripts/index.py build --cold       # ignore cache, re-embed everything
    python3 scripts/index.py search "why does our base never convert minerals"
    python3 scripts/index.py status             # counts, staleness, endpoint health

Embedding server: http://192.168.1.213:8000/v1/embeddings (override with --endpoint
or EMBEDDING_URL). One sequential client on purpose — the server 500s on concurrent
requests ("Infer Request is busy"). Chunks are capped at 1500 chars because the model
truncates at 512 tokens; anything longer is silently cut.
"""

import argparse
import array
import hashlib
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "index")
CHUNKS = os.path.join(INDEX, "chunks.jsonl")
VECTORS = os.path.join(INDEX, "vectors.f32")
META = os.path.join(INDEX, "meta.json")
SUMMARIES = os.path.join(INDEX, "summaries.jsonl")
DEFAULT_ENDPOINT = os.environ.get("EMBEDDING_URL", "http://192.168.1.213:8000/v1/embeddings")
MODEL = "embeddinggemma-2"
DIM = 768
MAX_CHARS = 1500          # ~380 tokens, comfortably inside the model's 512-token window
BATCH = 32                # smaller batches keep padding down; the server 500s if parallel


# ---------------------------------------------------------------- sources

def named_rows():
    """NAMED.md rows: addr -> (proposed name, evidence text). The only human-written
    semantics we have for a function, so when present it dominates a mechanical summary."""
    path = os.path.join(ROOT, "NAMED.md")
    rows = {}
    if not os.path.isfile(path):
        return rows
    for line in open(path, encoding="utf-8"):
        if not line.startswith("| `0x"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        rows[cells[0].strip("`").lower()] = (cells[1].strip("`"), "|".join(cells[3:]).strip())
    return rows


def iter_functions(include_all=False):
    """Yield informative functions (or all of them) with their decompiled body.

    A function with no name, no strings, no data references and fewer than six callees is
    boilerplate: its text is `FUN_004b8e30 ... calls FUN_004b8e30`, which embeds to noise and
    dilutes every query. Those are skipped unless include_all is set.
    """
    named = named_rows()
    shard_dir = os.path.join(ROOT, "ghidra_out")
    for path in sorted(os.path.join(shard_dir, f) for f in os.listdir(shard_dir)
                       if f.startswith("shard_") and f.endswith(".c")):
        text = open(path, encoding="utf-8", errors="replace").read()
        parts = re.split(r"(?m)^// ==== (\S+) @ (0x[0-9a-f]+) size=(\d+)", text)
        for i in range(1, len(parts), 4):
            name, addr, size, body = parts[i], parts[i + 1], parts[i + 2], parts[i + 3]
            strings = re.findall(r"\bs_[A-Za-z0-9_]{3,}", body)[:8]
            datas = re.findall(r"\b(?:PTR_)?(?:DAT|UNK)_[0-9a-f]{4,}", body)[:5]
            callees = sorted(set(re.findall(r"\b(FUN_[0-9a-f]{6,})\s*\(", body)))[:10]
            if not include_all and not (addr.lower() in named or strings or datas or len(callees) >= 6):
                continue
            yield {"name": name, "addr": addr, "size": int(size), "body": body,
                   "strings": strings, "datas": datas, "callees": callees,
                   "named": named.get(addr.lower()), "path": os.path.relpath(path, ROOT)}


def load_summaries():
    """addr -> {hash, summary} from the LLM labelling pass (scripts/summarize.py)."""
    out = {}
    if os.path.isfile(SUMMARIES):
        for line in open(SUMMARIES, encoding="utf-8"):
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            out[row["addr"]] = row
    return out


def body_hash(body):
    return hashlib.sha1(body.strip().encode("utf-8")).hexdigest()[:12]


def fn_chunks(include_all=False):
    """One chunk per function. A validated LLM one-liner, when present, replaces the
    mechanical signature — that sentence is what makes semantic search work here."""
    summaries = {} if os.environ.get("INDEX_NO_SUMMARIES") else load_summaries()
    out = []
    for f in iter_functions(include_all):
        s = summaries.get(f["addr"])
        has_summary = bool(s and s.get("hash") == body_hash(f["body"]))
        bits = [f"Function {f['name']} at {f['addr']}, {f['size']} bytes."]
        # A NAMED row is human-written and identifier-rich: it leads, because mean pooling
        # dilutes exact names when a prose summary sits in front of them (measured).
        if f["named"]:
            bits.append(f"Known as {f['named'][0]}. {f['named'][1][:300]}")
        if has_summary and not f["named"]:
            bits.append("Does: " + s["summary"])
        else:
            sig = f["body"].strip().splitlines()[0][:120] if f["body"].strip() else ""
            if sig:
                bits.append(sig)
        if f["strings"]:
            bits.append("References strings: " + ", ".join(f["strings"]) + ".")
        if f["datas"]:
            bits.append("Touches data: " + ", ".join(f["datas"]) + ".")
        if f["callees"]:
            bits.append("Calls: " + ", ".join(f["callees"]) + ".")
        out.append({"id": f"fn:{f['addr']}", "kind": "function", "addr": f["addr"],
                    "path": f["path"], "text": " ".join(b for b in bits if b)[:MAX_CHARS]})
    return out


def note_chunks():
    """One chunk per session section, hot file first, then the rotated archives."""
    files = [os.path.join(ROOT, "SESSION_NOTES.md")]
    archive = os.path.join(ROOT, "docs", "sessions")
    if os.path.isdir(archive):
        files += [os.path.join(archive, f) for f in sorted(os.listdir(archive)) if f.endswith(".md")]
    out = []
    for path in files:
        if not os.path.isfile(path):
            continue
        lines = open(path, encoding="utf-8").read().splitlines()
        starts = [i for i, l in enumerate(lines) if l.startswith("## Session")]
        for n, s in enumerate(starts):
            e = starts[n + 1] if n + 1 < len(starts) else len(lines)
            body = "\n".join(lines[s:e]).strip()
            head = lines[s].removeprefix("## ").strip()
            out.append({"id": "note:%s:%d" % (os.path.basename(path), s + 1),
                        "kind": "note", "path": os.path.relpath(path, ROOT),
                        "line": s + 1, "text": (head + ". " + body[len(lines[s]):]).strip()[:MAX_CHARS]})
    return out


def all_chunks(include_all=False):
    return fn_chunks(include_all) + note_chunks()


def digest(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------- embedding

def embed(texts, endpoint, retries=3):
    """Sequential batches. Returns a list of normalised float tuples."""
    vectors = []
    for start in range(0, len(texts), BATCH):
        batch = texts[start:start + BATCH]
        payload = json.dumps({"input": batch, "model": MODEL}).encode()
        for attempt in range(retries):
            req = urllib.request.Request(endpoint, data=payload,
                                         headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=300) as r:
                    body = json.loads(r.read())
                break
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
                if attempt == retries - 1:
                    raise SystemExit(
                        f"embedding endpoint unavailable ({exc}).\n"
                        f"  start it: ssh paul@192.168.1.213 'systemctl --user start embeddinggemma-production'\n"
                        f"  or skip the index: the merge still stands, only search is degraded.")
                time.sleep(2 ** attempt)
        data = sorted(body["data"], key=lambda d: d["index"])
        for row in data:
            v = row["embedding"]
            n = math.sqrt(sum(x * x for x in v)) or 1.0
            vectors.append(tuple(x / n for x in v))
    return vectors


# ---------------------------------------------------------------- build

def load_existing():
    cache = {}
    if not (os.path.isfile(CHUNKS) and os.path.isfile(VECTORS) and os.path.isfile(META)):
        return cache
    try:
        meta = json.load(open(META, encoding="utf-8"))
        if meta.get("dim") != DIM or meta.get("model") != MODEL:
            return cache
        raw = array.array("f")
        with open(VECTORS, "rb") as fh:
            raw.fromfile(fh, os.path.getsize(VECTORS) // 4)
        rows = [json.loads(l) for l in open(CHUNKS, encoding="utf-8") if l.strip()]
        if len(rows) * DIM != len(raw):
            return cache
        for i, row in enumerate(rows):
            cache[row["id"]] = (row["hash"], raw[i * DIM:(i + 1) * DIM].tobytes())
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    return cache


def cmd_build(args):
    os.makedirs(INDEX, exist_ok=True)
    chunks = all_chunks(args.all)
    for c in chunks:
        c["hash"] = digest(c["text"])
    cache = {} if args.cold else load_existing()

    fresh = [c for c in chunks if c["hash"] != cache.get(c["id"], (None,))[0]]
    print(f"{len(chunks)} chunks ({len(chunks) - len(fresh)} cached, {len(fresh)} to embed)")
    t0 = time.perf_counter()
    if fresh:
        vectors = embed([c["text"] for c in fresh], args.endpoint)
        for c, v in zip(fresh, vectors):
            cache[c["id"]] = (c["hash"], array.array("f", v).tobytes())
        print(f"embedded {len(fresh)} chunks in {time.perf_counter() - t0:.1f} s")

    with open(CHUNKS, "w", encoding="utf-8") as fh:
        for c in chunks:
            fh.write(json.dumps(c, ensure_ascii=False) + "\n")
    with open(VECTORS, "wb") as fh:
        for c in chunks:
            fh.write(cache[c["id"]][1])
    meta = {"model": MODEL, "dim": DIM, "count": len(chunks),
            "functions": sum(1 for c in chunks if c["kind"] == "function"),
            "notes": sum(1 for c in chunks if c["kind"] == "note"),
            "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "sources": source_fingerprint()}
    json.dump(meta, open(META, "w", encoding="utf-8"), indent=1)
    print(f"index: {len(chunks)} chunks, {os.path.getsize(VECTORS) / 1e6:.1f} MB vectors "
          f"-> {os.path.relpath(INDEX, ROOT)}/")
    return 0


def source_fingerprint():
    """Cheap staleness check: newest mtime + size of the source corpora."""
    latest = 0
    total = 0
    for path in [os.path.join(ROOT, "SESSION_NOTES.md")] + \
                [os.path.join(ROOT, "ghidra_out", f) for f in os.listdir(os.path.join(ROOT, "ghidra_out"))
                 if f.startswith("shard_") and f.endswith(".c")]:
        if os.path.isfile(path):
            st = os.stat(path)
            latest = max(latest, st.st_mtime)
            total += st.st_size
    return {"newest_mtime": int(latest), "bytes": total}


def cmd_status(_args):
    if not os.path.isfile(META):
        print("no index yet — run: python3 scripts/index.py build")
        return 1
    meta = json.load(open(META, encoding="utf-8"))
    print(f"{meta['count']} chunks ({meta['functions']} functions, {meta['notes']} notes), "
          f"{meta['dim']}-d, built {meta['built_at']}")
    print(f"size: {os.path.getsize(VECTORS) / 1e6:.1f} MB")
    now = source_fingerprint()
    if now != meta["sources"]:
        print("STALE — sources changed since the build; run `index.py build`")
    else:
        print("up to date with the listed sources")
    return 0


# ---------------------------------------------------------------- search

def cmd_search(args):
    if not os.path.isfile(META):
        raise SystemExit("no index yet — run: python3 scripts/index.py build")
    raw = array.array("f")
    with open(VECTORS, "rb") as fh:
        raw.fromfile(fh, os.path.getsize(VECTORS) // 4)
    rows = [json.loads(l) for l in open(CHUNKS, encoding="utf-8") if l.strip()]
    q = embed([args.query], args.endpoint)[0]
    scored = []
    for i, row in enumerate(rows):
        if args.kind and row["kind"] != args.kind:
            continue
        off = i * DIM
        s = 0.0
        for j in range(DIM):
            s += raw[off + j] * q[j]
        scored.append((s, row))
    scored.sort(key=lambda t: -t[0])
    top = scored[:args.k]
    if args.json:
        print(json.dumps([{"score": round(s, 4), **r} for s, r in top], indent=1))
        return 0
    for s, r in top:
        where = r["addr"] if r["kind"] == "function" else f"{r['path']}:{r['line']}"
        print(f"{s:.3f}  {r['kind']:8}  {where:38}  {r['text'][:110]}")
    print(f"\n{len(scored)} candidates scanned; a hit is a lead, not evidence — cite the file:line.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--cold", action="store_true")
    b.add_argument("--all", action="store_true", help="include boilerplate functions (10,284 chunks)")
    b.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    b.set_defaults(fn=cmd_build)
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("-k", type=int, default=8)
    s.add_argument("--kind", choices=["function", "note"])
    s.add_argument("--json", action="store_true")
    s.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    s.set_defaults(fn=cmd_search)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
