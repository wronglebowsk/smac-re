#!/usr/bin/env python3
"""M348 -- which template CONSUMES the completion block's slot-1 / slot-2 text?

M346 established that the completion block of FUN_004ef6d0 (right after the
queue pop) writes two entries into a ten-slot text bank and reads them through
the `$`-token expander FUN_00625b20.  It left one question open: which template
consumes slots 1/2 (the item row and the base record)?

Measured here, all static (zero box time):

  BANK     0x999ff4 payload[10] / 0x999fcc owner[10] / 0x99a01c text[10][0x100].
           The two writers are FUN_006265a2 (index, LABEL-ID -> slot text) and
           FUN_00626634 (index, LITERAL string -> slot text); both bound k <= 9.
  POST     0x4f0f78 setter A(k=1, dword at 0x984d38+edi*48) and
           0x4f0f96 setter B(k=2, 0x927894+ebx*1436) -- the item label id and
           the base name string.
  KEY      the same block APPENDS "PRODUCEX" (0x68cfc4) + "Q" (0x68cfd0) or
           "G" (0x68cfd4) into 0x997120 and hands that key to FUN_0048f100
           @0x4f122a; the non-extended branch builds "PRODUCE"+Q/G.
  CONSUME  FUN_0048f100 sets slot 0 (the base name, [0x8f0d60]+0x13) and
           dispatches the key to the script-text table 0x997528.  The template
           is therefore a Script.txt record, NOT an .rdata string:
           #PRODUCEXQ / #PRODUCEXG bodies read `$ITEM1` (slot 1) and `$NUM1`;
           #PRODUCE2 / #PRODUCE3 read `$<M1:$FACTIONADJ2>` (slot 2).
  RETRACT  FUN_00636b1e -- M346's "drainer" -- is the multiplayer CREATE
           SESSION dialog: it draws "Session Name:", "Maximum Players:" and
           "Session Password (Optional):" (0x6998b0/c0/d4) into the widget and
           re-loops while strlen(slot 1) > 0x10 (session-name validation).

RIVALS that FAIL on the printed numbers:
  R1 "the template is an .rdata string"  -> 0 printable .rdata strings contain
     a `$<` token; the only token literal is the vocabulary `$LINK<`.
  R2 "slots 1/2 are an alert-private queue" -> 0x99a01c is read/pushed from
     dozens of functions across .text, and the named drainer is a net dialog.
  R3 "slot 2 feeds the same popup"       -> the #PRODUCEX* records contain no
     slot-2 token; slot 2 belongs to the #PRODUCE2/#PRODUCE3 family.

    python3 -u scripts/m348_slot_template.py      # table first, then gates
"""
import csv
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.join(ROOT, "terran.exe")
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")
SCRIPT = os.path.join(ROOT, "programs", "Script.txt")
INDEX = os.path.join(ROOT, "ghidra_out", "index.csv")
EVID = os.path.join(ROOT, "evidence", "m348_slot_template.txt")
IMAGE_BASE = 0x400000

OUT = []


def say(*a):
    line = " ".join(str(x) for x in a)
    print(line)
    OUT.append(line)


# --------------------------------------------------------------- inputs ---
binbuf = bytearray(open(BIN, "rb").read())

ins_re = re.compile(r"^\s*([0-9a-f]{6,8}):\t([0-9a-f ]+)\t\s*(\S+)\s*(.*)$")
INS = {}
ORDER = []
for line in open(TEXT, errors="replace"):
    m = ins_re.match(line.rstrip("\n"))
    if not m:
        continue
    a = int(m.group(1), 16)
    INS[a] = {"addr": a, "bytes": bytes.fromhex(m.group(2).replace(" ", "")),
              "mn": m.group(3), "ops": m.group(4).strip()}
    ORDER.append(a)
ORDER.sort()

SCRIPTS = {}
_cur = None
for raw in open(SCRIPT, errors="replace"):
    ln = raw.rstrip("\r\n")
    if ln.startswith("#"):
        key = ln[1:].split()[0] if len(ln) > 1 else ""
        if key and key.upper() == key and re.fullmatch(r"[A-Z0-9]+", key):
            _cur = key
            SCRIPTS.setdefault(_cur, [])
            continue
    if _cur:
        SCRIPTS[_cur].append(ln)

# function spans from the Ghidra index (start, end, name)
SPANS = []
try:
    with open(INDEX) as f:
        for row in csv.DictReader(f):
            try:
                a = int(row["addr"], 16)
                sz = int(row["size_bytes"])
            except (KeyError, TypeError, ValueError):
                continue
            SPANS.append((a, a + sz, row["name"]))
    SPANS.sort()
except OSError:
    pass


def fn_of(addr):
    for a, b, n in SPANS:
        if a <= addr < b:
            return n
    return "?"


def b(va, n=1):
    off = va - IMAGE_BASE
    return bytes(binbuf[off:off + n])


def cstr(va, cap=64):
    off = va - IMAGE_BASE
    end = binbuf.find(b"\x00", off, off + cap)
    if end < 0:
        end = off + cap
    return bytes(binbuf[off:end]).decode("latin1")


def prev_push(a, lim=6):
    """Nearest push operand walking back from a call (a-1 is not an insn)."""
    p = a
    for _ in range(lim):
        p -= 1
        if p in INS and INS[p]["mn"] == "push":
            return INS[p]["ops"]
    return None


def ins(a):
    if a not in INS:
        raise SystemExit("M348: missing instruction at 0x%06x" % a)
    return INS[a]


def apply_patches():
    """Mutation hooks: byte patches in the image and instruction-line patches."""
    for spec in filter(None, os.environ.get("M348_PATCH_BIN", "").split(";")):
        va_s, val_s = spec.split("=", 1)
        va = int(va_s, 16)
        off = va - IMAGE_BASE
        if " " in val_s:
            raw = bytes.fromhex(val_s.replace(" ", ""))
            binbuf[off:off + len(raw)] = raw
        else:
            binbuf[off] = int(val_s, 16) if val_s.lower().startswith("0x") else int(val_s, 16)
    for spec in filter(None, os.environ.get("M348_PATCH_INS", "").split(";")):
        a_s, txt = spec.split("=", 1)
        a = int(a_s, 16)
        if a in INS:
            parts = txt.split(None, 1)
            INS[a]["mn"] = parts[0]
            INS[a]["ops"] = parts[1] if len(parts) > 1 else ""


apply_patches()


def script_body(key):
    body = os.environ.get("M348_SCRIPT_EDIT")
    lines = list(SCRIPTS.get(key, []))
    if body and body.startswith(key + ":"):
        lines = [body.split(":", 1)[1]]
    return lines


# ------------------------------------------------------------- measurements ---
say("M348 - which template consumes the completion block's slots 1/2")
say("input: terran.exe sha1 %s" % hashlib.sha1(bytes(binbuf)).hexdigest()[:16])

# 1. slot bank
say("")
say("TABLE 1 - the text bank (all inside .data: RVA 0x289000 + 0x316284)")
BANK_ROWS = [
    ("payload", 0x999FF4, "store [k*4+0x999ff4]"),
    ("owner", 0x999FCC, "store [k*4+0x999fcc]"),
    ("text", 0x99A01C, "byte clear [k<<8 + 0x99a01c]; stride 0x100"),
    ("numeric", 0x999FA4, "$NUMk / $HEXk read [k*4+0x999fa4]"),
]
for name, va, shape in BANK_ROWS:
    say("  %-8s 0x%06x  %s" % (name, va, shape))

# 2. the two setters
say("")
say("TABLE 2 - the two slot setters (bound k <= 9 in both)")
SETA, SETB = 0x6265A2, 0x626634
rows = [
    ("A bound cmp", ins(0x6265A8)["mn"] + " " + ins(0x6265A8)["ops"]),
    ("A bound jcc", ins(0x6265AC)["mn"] + " " + ins(0x6265AC)["ops"]),
    ("A payload", ins(0x6265D2)["mn"] + " " + ins(0x6265D2)["ops"]),
    ("A owner", ins(0x6265F6)["mn"] + " " + ins(0x6265F6)["ops"]),
    ("A text clear", ins(0x626603)["mn"] + " " + ins(0x626603)["ops"]),
    ("A label table", ins(0x62660E)["mn"] + " " + ins(0x62660E)["ops"]),
    ("A resolver", ins(0x626613)["mn"] + " " + ins(0x626613)["ops"]),
    ("B bound cmp", ins(0x626640)["mn"] + " " + ins(0x626640)["ops"]),
    ("B literal push", ins(0x6266A5)["mn"] + " " + ins(0x6266A5)["ops"]),
]
for k, v in rows:
    say("  %-14s %s" % (k, v))

# 3. completion block window
POP, POST1, POST2, END = 0x4F0F46, 0x4F0F78, 0x4F0F96, 0x4F0F9B
window = [a for a in ORDER if POP <= a <= END]
posts = []
for a in window:
    i = INS[a]
    if i["mn"] == "call" and i["ops"] in ("0x6265a2", "0x626634"):
        pushes = []
        p = a
        while p > POP and len(pushes) < 4:
            p -= 1
            if p not in INS:
                continue
            if INS[p]["mn"] == "push":
                pushes.append(INS[p]["ops"])
        posts.append((a, i["ops"], list(pushes)))
say("")
say("TABLE 3 - completion window 0x%06x..0x%06x (%d insns)" % (POP, END, len(window)))
for a, tgt, pushes in posts:
    say("  call 0x%06x @0x%06x arg1..arg4 %s" % (int(tgt, 16), a, pushes))

# 4. the two argument computations
def seq(lo, hi):
    return [ins(a) for a in ORDER if lo <= a <= hi]


item = seq(0x4F0F65, 0x4F0F6F)
item_factor = 1
for i in item:
    m = re.fullmatch(r"(\w+),\[(\w+)\+\2\*2\]", i["ops"])
    if i["mn"] == "lea" and m:
        item_factor *= 3
    elif i["mn"] == "shl":
        item_factor *= 1 << int(i["ops"].split(",")[1], 16)
item_base = None
for i in item:
    m = re.search(r"\[ecx\+0x([0-9a-f]+)\]", i["ops"])
    if m:
        item_base = int(m.group(1), 16)

base = seq(0x4F0F7D, 0x4F0F8C)
base_factor = 1
for i in base:
    if i["mn"] == "lea" and i["ops"] == "eax,[ebx+ebx*4]":
        base_factor *= 5
    elif i["mn"] == "lea" and i["ops"] == "eax,[eax+eax*8]":
        base_factor *= 9
    elif i["mn"] == "shl" and i["ops"] == "eax,0x3":
        base_factor *= 8
    elif i["mn"] == "sub" and i["ops"] == "eax,ebx":
        base_factor -= 1
base_stride = None
for i in base:
    m = re.search(r"\[eax\*4\+0x([0-9a-f]+)\]", i["ops"])
    if m:
        base_stride = (int(m.group(1), 16), base_factor * 4)
say("")
say("TABLE 4 - argument computation")
say("  item: edi*%d + 0x%06x  (record first dword -> label id)" % (item_factor, item_base))
say("  base: ebx*%d + 0x%06x  (record pointer -> literal text)" % (base_stride[1], base_stride[0]))

# 5. key assembly literals
say("")
say("TABLE 5 - the popup key the block assembles in 0x997120")
KEYROWS = [(0x68CF8C, "PROJECT"), (0x68CF94, "FAC"), (0x68CFB0, "voices\\fac"),
           (0x68CFBC, ".mp3"), (0x68CFC4, "PRODUCEX"), (0x68CFD0, "Q"),
           (0x68CFD4, "G"), (0x68CFE8, "PRODUCE"), (0x68CFD8, "facblt_sm.pcx")]
for va, want in KEYROWS:
    say("  0x%06x %-16r" % (va, cstr(va, 32)))
key_appenders = [a for a in ORDER if 0x4F0F40 <= a <= 0x4F1360
                 and INS[a]["mn"] == "call" and INS[a]["ops"] == "0x64b9e0"]
say("  strcat(0x64b9e0) sites in block: %s" % ["%06x" % a for a in key_appenders])

# 6. display call and slot 0
disp = [a for a in ORDER if 0x4F0F40 <= a <= 0x4F1360
        and INS[a]["mn"] == "call" and INS[a]["ops"] == "0x48f100"]
slot0 = [a for a in ORDER if 0x48F100 <= a < 0x48F100 + 1299
         and INS[a]["mn"] == "call" and INS[a]["ops"] == "0x626634"]
say("")
say("TABLE 6 - the consumer entry point")
say("  block display call 0x48f100 sites: %s" % ["%06x" % a for a in disp])
say("  FUN_0048f100 slot-0 setter calls: %s" % ["%06x" % a for a in slot0])
say("  FUN_0048f100 slot-0 source: %s ; %s" % (
    ins(0x48F203)["mn"] + " " + ins(0x48F203)["ops"],
    ins(0x48F209)["mn"] + " " + ins(0x48F209)["ops"]))

# 7. Script.txt records
say("")
say("TABLE 7 - the Script.txt records reachable from the block's keys")
SLOT_TOKEN = re.compile(r"\$[A-Z]*?(\d)")

def tokens(lines):
    return sorted(set(SLOT_TOKEN.findall(" ".join(lines))))

for key in ("PRODUCEXQ", "PRODUCEXG", "PRODUCEQ", "PRODUCEG", "PRODUCE2", "PRODUCE3"):
    body = script_body(key)
    text = " ".join(x.strip() for x in body if x.strip() and not x.startswith(";"))
    say("  #%-10s slots=%s  %r" % (key, tokens(body), text[:74]))

# 8. no .rdata template
say("")
say("TABLE 8 - is the template an .rdata string?")
RD_LO, RD_HI = 0x271000, 0x286B53   # .rdata RVA span from the PE header
hits = []
i = RD_LO
while i < RD_HI:
    j = i
    while j < RD_HI and 32 <= binbuf[j] < 127:
        j += 1
    if j - i >= 6:
        s = bytes(binbuf[i:j]).decode("latin1")
        if "$" in s:
            hits.append((IMAGE_BASE + i, s))
    i = max(j + 1, i + 1)
say("  printable .rdata strings containing '$': %d %s" % (len(hits), [("%06x" % a) for a, _ in hits]))
say("  of those containing '$<': %d" % sum(1 for _, s in hits if "$<" in s))

# 9. reader census
say("")
say("TABLE 9 - who reads the text bank 0x99a01c")
readers = [a for a in ORDER if "0x99a01c" in INS[a]["ops"]]
rfns = {}
for a in readers:
    rfns.setdefault(fn_of(a), []).append(a)
pairs = []
for a in ORDER:
    i = INS[a]
    if i["mn"] != "shl" or not re.fullmatch(r"(e[a-d]x|e[sd]i|e[b]p),0x8", i["ops"]):
        continue
    reg = i["ops"].split(",")[0]
    nxt = a + len(i["bytes"])
    if nxt in INS and INS[nxt]["mn"] == "add" and INS[nxt]["ops"] == reg + ",0x99a01c":
        pairs.append(a)
say("  0x99a01c referencing insns: %d in %d functions" % (len(readers), len(rfns)))
say("  funcs: %s" % sorted(rfns)[:12])
say("  same-register shl REG,8 / add REG,0x99a01c pairs: %d %s"
    % (len(pairs), ["%06x" % a for a in pairs]))

# 10. the retraction: 0x636b1e is the Create Session dialog
say("")
say("TABLE 10 - M346's 'drainer' FUN_00636b1e re-read")
DR = 0x636B1E
dlg = [a for a in ORDER if DR <= a < DR + 3571
       and INS[a]["mn"] == "push" and INS[a]["ops"] in ("0x6998b0", "0x6998c0", "0x6998d4")]
for a in dlg:
    say("  push 0x%s @0x%06x  -> %r" % (INS[a]["ops"][2:], a, cstr(int(INS[a]["ops"], 16), 40)))
say("  slot1 length test: %s ; %s" % (
    ins(0x637358)["mn"] + " " + ins(0x637358)["ops"],
    ins(0x63735B)["mn"] + " " + ins(0x63735B)["ops"]))
say("  re-loop target: %s" % (ins(0x63735D)["mn"] + " " + ins(0x63735D)["ops"]))

# ------------------------------------------------------------------ GATES ---
GATES = []
FAILS = []


def gate(gid, name, cond, detail):
    ok = bool(cond)
    GATES.append((gid, name, ok, detail))
    if not ok:
        FAILS.append(gid)


def norm(ops):
    return ops.replace(" ", "").lower()


# G1 bank addresses live in .data and the setters bound k <= 9
gate("G1", "bank arrays 0x999ff4/0x999fcc/0x99a01c inside .data; text stride 0x100; bound 9",
     all(0x689000 <= va < 0x689000 + 0x316284 for _, va, _ in BANK_ROWS)
     and ins(0x6265A8)["ops"] == "DWORD PTR [ebp+0x8],0x9"
     and ins(0x6265AC)["mn"] == "jle"
     and "DWORD PTR [ebp+0x8]" in ins(0x6265FD)["ops"]
     and "shl" in ins(0x626600)["mn"] and ins(0x626600)["ops"] == "edx,0x8",
     "bound cmp 0x9 + jle; text index edx<<8")

# G2 setter A shape: payload, owner, clear, return 3 above 9
gate("G2", "setter A stores payload/owner and clears slot text",
     ins(0x6265D2)["mn"] == "mov" and "0x999ff4" in ins(0x6265D2)["ops"]
     and ins(0x6265F6)["mn"] == "mov" and "0x999fcc" in ins(0x6265F6)["ops"]
     and ins(0x626603)["mn"] == "mov" and ins(0x626603)["ops"].endswith(",0x0")
     and ins(0x6265AE)["ops"] == "eax,0x3",
     "stores + byte clear + return 3")

# G3 label setter vs literal setter
gate("G3", "setter A resolves a LABEL ID through table 0x997b28; setter B copies a literal",
     ins(0x62660E)["ops"] == "ecx,0x997b28"
     and ins(0x626613)["ops"] == "0x61482f"
     and not any(INS[a]["ops"] == "0x61482f" for a in ORDER if SETB <= a < SETB + 141)
     and ins(0x6266A5)["mn"] == "push" and ins(0x6266A5)["ops"] == "eax",
     "0x997b28 + call 0x61482f only in A")

# G4 exactly two posts, kinds 1 then 2, inside the pop..re-read window
gate("G4", "two posts in the completion window, kind 1 then kind 2",
     len(posts) == 2
     and posts[0][1] == "0x6265a2" and posts[0][2][0] == "0x1"
     and posts[1][1] == "0x626634" and posts[1][2][0] == "0x2"
     and ins(POP)["ops"] == "0x4ef5d0",
     "%d posts; pop 0x4ef5d0" % len(posts))

# G5 item argument = edi*48 + 0x984d38
gate("G5", "slot-1 argument = dword at 0x984d38 + edi*48",
     item_factor == 48 and item_base == 0x984D38 and ins(0x4F0F6F)["mn"] == "mov",
     "factor %d base 0x%06x" % (item_factor, item_base or 0))

# G6 base argument = ebx*1436 + 0x927894
gate("G6", "slot-2 argument = 0x927894 + ebx*1436",
     base_stride == (0x927894, 1436) and base_factor == 359,
     "stride %s factor %d" % (base_stride[1], base_factor))

# G7 key literals and appends
gate("G7", "key = PRODUCEX + Q|G (PRODUCE fallback) appended in 0x997120; voice name PROJECT|FAC + idx",
     cstr(0x68CFC4) == "PRODUCEX" and cstr(0x68CFE8) == "PRODUCE"
     and cstr(0x68CFD0) == "Q" and cstr(0x68CFD4) == "G"
     and cstr(0x68CF8C) == "PROJECT" and cstr(0x68CF94) == "FAC"
     and cstr(0x68CFB0) == "voices\\fac" and cstr(0x68CFBC) == ".mp3"
     and len(key_appenders) >= 4,
     "%d strcat sites" % len(key_appenders))

# G8 block hands the key to 0x48f100; 0x48f100 sets slot 0
gate("G8", "display call 0x48f100 gets 0x997120; it sets slot 0 = [0x8f0d60]+0x13",
     disp and any(prev_push(a) == "0x997120" for a in disp)
     and slot0 and ins(0x48F203)["ops"] == "edx,DWORD PTR ds:0x8f0d60"
     and ins(0x48F209)["mn"] == "add" and ins(0x48F209)["ops"] == "edx,0x13",
     "display calls %s; slot0 setter %s" % (["%06x" % a for a in disp],
                                            ["%06x" % a for a in slot0]))

# G9 Script records consume slot 1 (PRODUCEX*) and slot 2 (PRODUCE2/3)
xq = " ".join(script_body("PRODUCEXQ"))
xq_slots = set(SLOT_TOKEN.findall(xq))
p2 = " ".join(script_body("PRODUCE2"))
gate("G9", "#PRODUCEXQ reads slot 1 ($ITEM1/$NUM1); #PRODUCE2 reads slot 2",
     "$ITEM1" in xq and "$NUM1" in xq and ("2" not in xq_slots)
     and "$FACTIONADJ2" in p2,
     "XQ slots %s; P2 has FACTIONADJ2=%s" % (sorted(xq_slots), "$FACTIONADJ2" in p2))

# G10 no .rdata template: zero '$<' strings
gate("G10", "no .rdata string carries a $< token; only the vocabulary $LINK<",
     sum(1 for _, s in hits if "$<" in s) == 0
     and all(a == 0x673330 for a, _ in hits),
     "%d '$' strings, %d '$<' " % (len(hits), sum(1 for _, s in hits if "$<" in s)))

# G11 expander is the only structured reader; bank is global
gate("G11", "exactly 7 sites build 0x99a01c+(k<<8): 4 in FUN_00625b20, 2 in the setters, 1 in the modal screen",
     pairs == [0x5F12EE, 0x625DA9, 0x625F08, 0x6261B0, 0x62637C, 0x62661C, 0x6266A9]
     and fn_of(0x5F12EE).startswith("FUN_005f")
     and len(rfns) > 10,
     "%d pairs; %d functions read 0x99a01c; 0x5f12ee in %s" % (
         len(pairs), len(rfns), fn_of(0x5F12EE)))

# G12 retraction: 0x636b1e is the Create Session dialog
gate("G12", "FUN_00636b1e pushes the three session-field labels and loops on strlen(slot1)>0x10",
     {int(INS[a]["ops"], 16) for a in dlg} == {0x6998B0, 0x6998C0, 0x6998D4}
     and cstr(0x6998B0) == "Session Name:" and cstr(0x6998C0) == "Maximum Players:"
     and cstr(0x6998D4) == "Session Password (Optional):"
     and ins(0x637358)["ops"] == "eax,0x10" and ins(0x63735D)["mn"] == "jmp"
     and ins(0x63735D)["ops"] == "0x63724e",
     "labels %s; cmp 0x10 -> jmp 0x63724e" % ["%06x" % a for a in dlg])

say("")
npass = sum(1 for g in GATES if g[2])
for gid, name, ok, detail in GATES:
    say("  %-4s %-4s %s  [%s]" % (gid, "PASS" if ok else "FAIL", name, detail))
say("")
say("R1 RIVAL .rdata template   -> %s" % ("REFUTED" if GATES[9][2] else "survives"))
say("R2 RIVAL alert-private bank-> %s" % ("REFUTED" if (GATES[10][2] and GATES[11][2]) else "survives"))
say("R3 RIVAL slot2 same popup  -> %s" % ("REFUTED" if GATES[8][2] else "survives"))
say("")
digest = hashlib.sha256("\n".join(OUT).encode()).hexdigest()
say("RESULT %s: %d/%d gates  digest %s" % (
    "PASS" if not FAILS else "FAIL", npass, len(GATES), digest[:16]))
# a mutated run must never overwrite the acceptance evidence
if not any(os.environ.get(k) for k in ("M348_PATCH_BIN", "M348_PATCH_INS", "M348_SCRIPT_EDIT")):
    os.makedirs(os.path.dirname(EVID), exist_ok=True)
    with open(EVID, "w") as f:
        f.write("\n".join(OUT) + "\n")
sys.exit(0 if not FAILS else 1)
