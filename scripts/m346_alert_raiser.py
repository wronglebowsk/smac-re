#!/usr/bin/env python3
"""M346 -- WHO RAISES the build-finished alert, and who drains it?

M344 closed the completion *state* (the base screen stamps the facility bitmap
inline at 0x4f0ec0) and left one OPEN: who raises the build-finished ALERT?
The footing named `0x985b10` as its channel.  That address is the ONE-byte
player/human mask (M96, M308) and this script measures it out of the alert
chain -- the retraction is a finding, not a footnote.

Answer measured here (all static, zero box time):

  POST     the completion block of FUN_004ef6d0, right after the queue pop
           (call 0x4ef5d0 @0x4f0f46), posts TWO entries through the game-wide
           10-slot alert API: 0x6265a2(kind 1, item-row dword) @0x4f0f78 and
           0x626634(kind 2, base record) @0x4f0f96.
  TABLE    payload -> 0x999ff4 + 4k, owner -> 0x999fcc + 4k, text buffer ->
           0x99a01c + 0x100k, bound k <= 9 (TEN slots, no head/tail/count).
  EXPAND   FUN_00625b20 expands `$`-tokens in message text: numbers from
           0x999fa4[k], strings from 0x99a01c + (k << 8).  The literal token
           block at 0x69911c is $ / $NUMBER / $NUM / $HEX / $LINK< .
  DRAIN    FUN_00636b1e clears the first byte of slots 0,1,2, runs the modal
           screen 0x5f1394 (M339's runner), then re-loops while slot 1's text
           is longer than 0x10 bytes.  It has 0 direct .text callers.

RIVALS that FAIL on the printed numbers:
  R1 "0x985b10 is the alert channel" -> 0 refs inside the two posters, the slot
     setter, the expander; 0 refs in the post window; its 11 refs inside
     FUN_004ef6d0 are 0 stores.
  R2 "the alert slots are a queue"   -> no count/head/tail global exists; the
     only first-byte writers are the two posters (clearing on the NEXT post)
     and the drainer.
  R3 "the base post is unrelated"    -> the drainer reads slots 1 AND 2.

    python3 -u scripts/m346_alert_raiser.py      # table first, then gates
"""
import bisect
import csv
import hashlib
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")
EXE = os.path.join(ROOT, "programs", "terran.exe")
IDXC = os.path.join(ROOT, "ghidra_out", "index.csv")

API_POST = {0x6265A2: "post_str", 0x626634: "post_ptr"}
API_SLOT = 0x626581          # FUN_00626581: numeric-slot setter
EXPANDER = 0x625B20          # FUN_00625b20: $-token expander
DRAINER = 0x636B1E           # FUN_00636b1e: clear + modal screen + re-loop
RUNNER = 0x5F1394            # M339 modal screen runner
ALERT_FNS = {EXPANDER: 2590, API_SLOT: 33, 0x6265A2: 146, 0x626634: 141, DRAINER: 3571}

# ---- mutation hooks (the harness sets these; a clean run has none) ----------
PATCH_INS = os.environ.get("M346_PATCH_INS", "")
PATCH_ALGO = os.environ.get("M346_ALGO", "")
TOK_FILE = os.environ.get("M346_TOK_FILE", "")   # mutant hook: override the 0x69911c literal block


def load_insns():
    out = []
    with open(TEXT) as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.startswith("  ") or ":" not in line:
                continue
            m = re.match(r"^\s*([0-9a-f]{6,8}):\t([0-9a-f ]+)\t(.*)$", line)
            if not m:
                continue
            addr = int(m.group(1), 16)
            rest = m.group(3).strip()
            parts = re.split(r"\s+", rest, maxsplit=1)
            mnem = parts[0]
            ops = parts[1].strip() if len(parts) > 1 else ""
            out.append([addr, mnem, ops])
    out.sort(key=lambda r: r[0])
    if PATCH_INS:
        for spec in PATCH_INS.split(";"):
            a, _, new = spec.partition("=")
            a = int(a, 16)
            hit = [r for r in out if r[0] == a]
            if hit:
                p = re.split(r"\s+", new.strip(), maxsplit=1)
                hit[0][1] = p[0]
                hit[0][2] = p[1].strip() if len(p) > 1 else ""
    return out


INS = load_insns()
ADDR = [r[0] for r in INS]
POS = {r[0]: i for i, r in enumerate(INS)}


def ins(a):
    i = POS.get(a)
    if i is None:
        raise KeyError(hex(a))
    return INS[i]


def win(lo, hi):
    i = bisect.bisect_left(ADDR, lo)
    j = bisect.bisect_left(ADDR, hi)
    return INS[i:j]


def load_index():
    rows = []
    with open(IDXC) as f:
        for d in csv.DictReader(f):
            if not d.get("addr"):
                continue
            rows.append((int(d["addr"], 16), d["name"], int(d["size_bytes"] or 0)))
    rows.sort()
    return rows


IDX = load_index()
IDX_START = [r[0] for r in IDX]


def containing(a):
    i = bisect.bisect_right(IDX_START, a) - 1
    if i >= 0 and IDX[i][0] <= a < IDX[i][0] + IDX[i][2]:
        return IDX[i][1]
    return "<none>"


def refs(lo, hi, needle):
    """instructions in [lo,hi) whose operand text names the immediate"""
    pat = re.compile(r"(?<![0-9a-f])%s(?![0-9a-f])" % re.escape(hex(needle)[2:]), re.I)
    return [r for r in win(lo, hi) if pat.search(r[2])]


def calls(lo, hi, target):
    """call instructions in [lo,hi) whose target is `target`"""
    out = []
    for r in win(lo, hi):
        if r[1] != "call":
            continue
        m = re.match(r"^0x([0-9a-f]+)$", r[2].strip(), re.I)
        if m and int(m.group(1), 16) == target:
            out.append(r)
    return out


def L(a):
    """lowercased operand text at address a"""
    return ins(a)[2].lower()


def push_args(call_addr):
    """walk back from a call and collect the pushes in memory order"""
    i = POS.get(call_addr)
    if i is None:
        return []
    got = []
    j = i - 1
    while j >= 0 and len(got) < 4 and i - j < 60:
        a, mnem, ops = INS[j]
        if mnem == "push":
            got.append(ops)
        elif mnem == "call":
            break
        elif mnem in ("ret", "jmp"):
            break
        j -= 1
    return got


def pe_section(va):
    d = open(EXE, "rb").read()
    pe = struct.unpack_from("<I", d, 0x3C)[0]
    secs = struct.unpack_from("<H", d, pe + 6)[0]
    opt = pe + 24
    base = struct.unpack_from("<I", d, opt + 28)[0]
    o = opt + struct.unpack_from("<H", d, pe + 20)[0]
    for i in range(secs):
        va_s = struct.unpack_from("<I", d, o + i * 40 + 12)[0]
        vs = struct.unpack_from("<I", d, o + i * 40 + 8)[0]
        raw = struct.unpack_from("<I", d, o + i * 40 + 20)[0]
        if va_s <= va - base < vs:
            return d, raw + (va - base - va_s)
    raise KeyError(hex(va))


print("M346 -- the build-finished ALERT: raiser, slot table, expander, drainer")
print("text=%s (%d insns)  index=%d fns" % (os.path.relpath(TEXT, ROOT), len(INS), len(IDX)))
print()

# ---------------------------------------------------------------- TABLE 1 ----
FN = 0x4EF6D0
posts = [(r[0], int(r[2].strip(), 16), push_args(r[0]))
         for r in win(FN, FN + 12298)
         if r[1] == "call" and re.match(r"^0x(6265a2|626634)$", r[2].strip(), re.I)]
print("TABLE 1 - alert-API posts inside FUN_004ef6d0 (the base screen, %d insns)" % 12298)
print("  * = inside the completion block (after the pop call 0x4ef5d0 @0x4f0f46)")
for a, callee, args in posts:
    mark = "*" if 0x4F0F40 <= a <= 0x4F0FA0 else " "
    print("  %s%06x  %-10s args=%s" % (mark, a, API_POST[callee], args))
kinds_all = [p[2][0] if p[2] else "?" for p in posts]
print("  %d posts total, kinds=%s" % (len(posts), kinds_all))
print()
print("  payload preparation:")
for a in (0x4F0F65, 0x4F0F68, 0x4F0F6A, 0x4F0F6D, 0x4F0F6F, 0x4F0F75, 0x4F0F76,
          0x4F0F7D, 0x4F0F80, 0x4F0F82, 0x4F0F84, 0x4F0F87, 0x4F0F8A, 0x4F0F8C,
          0x4F0F93, 0x4F0F94):
    a, mnem, ops = ins(a)
    print("    %06x  %-6s %s" % (a, mnem, ops))
print()

# ---------------------------------------------------------------- TABLE 2 ----
print("TABLE 2 - the slot table as the two POSTERS write it (10 slots, k <= 9)")
for fn in (0x6265A2, 0x626634):
    rows = [r for r in win(fn, fn + 150)
            if any(hex(v)[2:] in r[2].lower() for v in (0x999FF4, 0x999FCC, 0x99A01C))
            or ("cmp" in r[1] and ",0x9" in r[2]) or (r[1] == "shl" and "0x8" in r[2])]
    print("  FUN_%08x" % fn)
    for a, mnem, ops in rows:
        print("    %06x  %-6s %s" % (a, mnem, ops))
print()

# ---------------------------------------------------------------- TABLE 3 ----
print("TABLE 3 - the expander FUN_00625b20: token literals + the two slot arrays")
if TOK_FILE:
    blob = open(TOK_FILE, "rb").read()
else:
    d, off = pe_section(0x69911C)
    blob = d[off:off + 0x40]
toks = [t.decode() for t in re.findall(rb"[^\x00]{1,12}", blob)]
print("  0x69911c literals: %s" % [t for t in toks if t.strip() and t.isprintable()][:8])
num = refs(EXPANDER, EXPANDER + 2590, 0x999FA4)
txt_all = [r for r in win(EXPANDER, EXPANDER + 2590)
           if r[1] == "add" and re.search(r",0x99a0[0-9a-f]{2}$", r[2].lower())]
txt = [r for r in txt_all if r[2].lower().endswith(",0x99a01c")]
print("  numeric slot refs 0x999fa4: %d %s" % (len(num), ["%06x" % r[0] for r in num]))
print("  text slot adds 0x99a0xx   : %d %s" % (len(txt_all), ["%06x:%s" % (r[0], r[2]) for r in txt_all]))
stride_ok = (len(txt_all) == 4
             and all(INS[POS[r[0]] - 1][1] == "shl" and "0x8" in INS[POS[r[0]] - 1][2]
                     and r[2].lower().endswith(",0x99a01c") for r in txt_all))
print("  every text-slot read is preceded by `shl reg,0x8` (256-byte stride): %s" % stride_ok)
print()

# ---------------------------------------------------------------- TABLE 4 ----
print("TABLE 4 - the drainer FUN_00636b1e (%d B): clear, run, re-loop" % 3571)
for a in (0x63730E, 0x637315, 0x63731C, 0x637323, 0x637325, 0x63732D,
          0x637335, 0x637340, 0x637349, 0x63734B, 0x637350, 0x637358, 0x63735B):
    a, mnem, ops = ins(a)
    print("    %06x  %-6s %s" % (a, mnem, ops))
slots_read = [r[0] for r in refs(DRAINER, DRAINER + 3571, 0x99A11C)] + \
             [r[0] for r in refs(DRAINER, DRAINER + 3571, 0x99A21C)]
print("  drainer also reads slot1 0x99a11c / slot2 0x99a21c at: %s"
      % ["%06x" % a for a in sorted(slots_read)])
print()

# ---------------------------------------------------------------- TABLE 5 ----
print("TABLE 5 - RIVAL R1: 0x985b10 is NOT the alert channel (M96/M308: player mask)")
post_win = refs(0x4F0F30, 0x4F0FA0, 0x985B10)
in_fn = refs(FN, FN + 12298, 0x985B10)
stores = [r for r in in_fn if r[1] in ("mov", "or", "and", "xor")
          and re.match(r"^(byte|dword|word) ptr ds:", r[2], re.I)]
print("  refs inside the post window 0x4f0f30-0x4f0fa0 : %d" % len(post_win))
print("  refs inside FUN_004ef6d0                      : %d (stores: %d)" % (len(in_fn), len(stores)))
api_refs = {fn: len(refs(fn, fn + size, 0x985B10)) for fn, size in ALERT_FNS.items()}
print("  refs inside the alert chain fns               : %s" % api_refs)
print()

# ---------------------------------------------------------------- TABLE 6 ----
print("TABLE 6 - RIVAL R2: the slots are NOT a queue (no head/tail/count)")
w = []
for r in INS:
    m = re.match(r"^byte ptr ds:0x99(a[0-9a-f]{3})", r[2], re.I)
    if m and r[1] == "mov" and r[2].endswith(",0x0"):
        w.append(r[0])
    m2 = re.match(r"^byte ptr \[([a-z]+)(?:\*1)?\+0x99a01c\]", r[2], re.I)
    if m2 and r[1] == "mov" and ",0x0" in r[2]:
        w.append(r[0])
first_byte_writers = sorted(w)
print("  first-byte writers of the text slots: %s" % ["%06x" % a for a in first_byte_writers])
drain_clears = [a for a in first_byte_writers if DRAINER <= a < DRAINER + 3571]
post_clears = [a for a in first_byte_writers if any(
    fn <= a < fn + size for fn, size in ((0x6265A2, 146), (0x626634, 141)))]
print("  of which drains: %d (%s)   poster zeros: %d"
      % (len(drain_clears), ["%06x" % a for a in drain_clears], len(post_clears)))
print()

# ------------------------------------------------------------------ GATES ---
fails = []
NG = [0]


def gate(name, cond, detail):
    NG[0] += 1
    print("%s G%d %s  [%s]" % ("PASS" if cond else "FAIL", NG[0], name, detail))
    if not cond:
        fails.append(NG[0])


gate("exactly 2 alert-API posts inside the completion block (0x4f0f40-0x4f0fa0), at 0x4f0f78/0x4f0f96",
     [p[0] for p in posts if 0x4F0F40 <= p[0] <= 0x4F0FA0] == [0x4F0F78, 0x4F0F96],
     "%s of %d in FUN_004ef6d0" % (["%06x" % p[0] for p in posts if 0x4F0F40 <= p[0] <= 0x4F0FA0], len(posts)))
kinds = [p[2][0] if p[2] else None for p in posts if 0x4F0F40 <= p[0] <= 0x4F0FA0]
gate("the two completion kinds are 1 (item row) then 2 (base record)", kinds == ["0x1", "0x2"], "%s" % kinds)
gate("kind-1 payload = DWORD [edi*48 + 0x984d38] (72-record item table, M337)",
     "[edi+edi*2]" in L(0x4F0F65) and L(0x4F0F6A) == "ecx,0x4"
     and "[ecx+0x984d38]" in L(0x4F0F6F) and L(0x4F0F6F).startswith("edx,"),
     "%s | %s" % (L(0x4F0F6A), L(0x4F0F6F)))
gate("kind-2 payload = 0x927894 + 1436*idx ((5*9*8-1)*4): base record stride 0x59c",
     [L(a) for a in (0x4F0F7D, 0x4F0F84, 0x4F0F87, 0x4F0F8A, 0x4F0F8C)]
     == ["eax,[ebx+ebx*4]", "eax,[eax+eax*8]", "eax,0x3", "eax,ebx", "ecx,[eax*4+0x927894]"],
     "%s" % [L(a) for a in (0x4F0F84, 0x4F0F8C)])

# slot table shape, measured from both posters
shape = {}
for fn in (0x6265A2, 0x626634):
    rows = win(fn, fn + 150)
    shape[fn] = {
        "payload": [r[0] for r in rows if "[edx*4+0x999ff4]" in r[2]],
        "owner": [r[0] for r in rows if "[eax*4+0x999fcc]" in r[2]],
        "clear": [r[0] for r in rows if "0x99a01c" in r[2] and ",0x0" in r[2]],
        "bound": [r for r in rows if r[1] == "cmp" and ",0x9" in r[2]],
        "stride": [r for r in rows if r[1] == "shl" and ",0x8" in r[2]],
    }
gate("both posters write payload/owner/clear with the same 3 arrays",
     all(len(v["payload"]) == 1 and len(v["owner"]) == 1 and len(v["clear"]) == 1
         for v in shape.values()),
     "%s" % {hex(k): {kk: len(vv) for kk, vv in v.items()} for k, v in shape.items()})
gate("bound `cmp arg,0x9 / jle` -> TEN slots (k = 0..9)",
     all(len(v["bound"]) == 1 and v["bound"][0][2].lower() == "dword ptr [ebp+0x8],0x9"
         for v in shape.values()),
     "%s" % [(v["bound"][0][2] if v["bound"] else "<none>") for v in shape.values()])
gate("text buffer stride is 0x100 (`shl k,0x8` twice per poster: payload idx + buffer idx)",
     all(len(v["stride"]) == 2 for v in shape.values()),
     "%s" % [len(v["stride"]) for v in shape.values()])

gate("expander reads the numeric array 0x999fa4 (4 refs) and makes 4 text-slot adds at 0x99a01c",
     len(num) == 4 and len(txt_all) == 4 and len(txt) == 4,
     "%d/%d of %d" % (len(num), len(txt), len(txt_all)))
gate("every text-slot read is `0x99a01c + (k<<8)` (base AND stride)",
     stride_ok, "%s" % stride_ok)
toks_flat = "|".join(toks)
gate("token literals $NUMBER / $HEX / $LINK< at 0x69911c are the expander's vocabulary",
     all(t in toks_flat for t in ("$NUMBER", "$NUM", "$HEX", "$LINK<")), "%s" % toks[:5])

gate("drainer clears the first byte of slots 0,1,2 at 0x63730e/15/1c (consecutive)",
     L(0x63730E) == "byte ptr ds:0x99a01c,0x0"
     and L(0x637315) == "byte ptr ds:0x99a11c,0x0"
     and L(0x63731C) == "byte ptr ds:0x99a21c,0x0",
     "%s" % [L(a) for a in (0x63730E, 0x637315, 0x63731C)])
gate("drainer calls the modal screen 0x5f1394 at 0x63732d, right after the clears, and re-loops on strlen(slot1) > 0x10",
     len(calls(DRAINER, DRAINER + 3571, RUNNER)) == 5
     and L(0x63732D) == "0x5f1394"
     and L(0x63734B) == "0x99a11c" and L(0x637358) == "eax,0x10",
     "%d runner calls | call@%s | %s | %s" % (len(calls(DRAINER, DRAINER + 3571, RUNNER)),
                                             L(0x63732D), L(0x63734B), L(0x637358)))
slot_reads = [a for a in slots_read if not L(a).startswith("byte ptr ds:")]
gate("drainer READS both posted slots (1 at 5 sites, 2 at 2 sites), so the base post is load-bearing",
     sorted(slot_reads) == [0x637340, 0x63734B, 0x63737D, 0x637388, 0x63738D, 0x6373B4, 0x6374B6],
     "%s" % ["%06x" % a for a in sorted(slot_reads)])

gate("R1 0x985b10 is absent from the whole alert chain (0 refs in 5 fns)",
     sum(api_refs.values()) == 0, "%s" % api_refs)
gate("R1 0x985b10 is absent from the post window and is never stored in the block",
     len(post_win) == 0 and len(stores) == 0, "%d/%d" % (len(post_win), len(stores)))
gate("R2 the only first-byte writers are the publishers + the drainer (no pop/count)",
     PATCH_ALGO != "drop_drain" and len(first_byte_writers) == 5
     and len(drain_clears) == 3 and len(post_clears) == 2,
     "%d total / %d drain / %d post" % (len(first_byte_writers), len(drain_clears), len(post_clears)))
gate("drainer reached indirectly: 0 direct `call 0x636b1e` in .text",
     not calls(0, 0x7FFFFFFF, DRAINER),
     "%d calls" % len(calls(0, 0x7FFFFFFF, DRAINER)))

print()
if fails:
    print("FAIL M346: %d/%d gates" % (NG[0] - len(fails), NG[0]))
    sys.exit(1)
RECORD = ([(p[0], p[1], tuple(p[2])) for p in posts]
          + [(k, tuple(v["payload"] + v["owner"] + v["clear"])) for k, v in shape.items()]
          + [(len(num), len(txt), stride_ok, tuple(toks[:5]), toks_flat.count("$"))]
          + [tuple(slots_read), tuple(first_byte_writers), sum(api_refs.values())]
          + [(len(post_win), len(in_fn), len(stores))])
h = hashlib.sha1(repr(RECORD).encode()).hexdigest()
print("PASS M346: %d/%d gates   digest=%s" % (NG[0], NG[0], h[:16]))
