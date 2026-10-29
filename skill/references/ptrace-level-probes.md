# Probes at the ptrace / syscall layer (when a watchpoint is the wrong instrument)

Use when a value changes but NO ring-3 store can be found, or when you must know **where a syscall put
its bytes**. gdb hardware watchpoints cannot see a kernel write: Linux installs a user DR breakpoint with
the exclude-kernel bit, and `copy_to_user` inside `read()`/`pread()` raises no debug exception. So a
silent census is consistent with "the destination of a file read IS the watched region" — and only a
syscall-layer probe can prove it.

## One tracer per task
strace and gdb cannot both attach to the same process (`ptrace_attach` -> EBUSY). Decide which layer the
question lives at BEFORE arming: strace-only for "which syscall touched these bytes", gdb-only for
"which instruction stored". Two straces can coexist as long as they trace different processes (e.g. the
guest plus `wineserver`).

## strace: raw args give you the POINTER
`-a 0` still prints a content preview; **`-e raw=<set>` prints the raw hex arguments, which for
`read`/`pread64` is the buffer ADDRESS** — that is the whole trick for "did the loader read straight into
this global?". Combine two `-e` qualifiers:

```bash
strace -f -qq -ttt -O 256 -s 32 -o <log> -p <pid> \
  -e trace=read,pread64,pwrite64,pwritev,mmap,mmap2,munmap,mprotect,mremap,process_vm_writev,process_vm_readv,open,openat,close,lseek64,_llseek \
  -e raw=read,pread64,pwrite64,pwritev,mmap,mmap2,munmap,mprotect,mremap,process_vm_writev
```

Line format with `-f -ttt`: `PID TIMESTAMP name(args) = ret` — parse the pid FIRST, then the timestamp.
At detach a syscall still in flight prints an entry-only line (`name(` with no `) = ret`): count those
separately as `unfinished`, do not treat them as unparsed noise and do not fail a gate on one or two of
them. Skip `--- SIG... ---` and `+++ exited ... +++`.
`open`/`openat` stay decoded so the fd -> path map can be built from their return value; keep that map
per traced pid AND a merged fallback, because `-f` attributes a thread's open to its LWP id while the fd
belongs to the process.

**Wine guests are fine:** strace auto-detects the ia32 personality (`System call usage summary for 32 bit
mode`) and decodes Wine's syscalls. Budget the noise: an idle HUD is ~25k syscalls/s, most of them X11
socket `read`/`write` — keep the trace set narrow (drop plain `write` from the guest trace when you only
need `pwrite64`), and write the RAW logs to `scratch/`, committing only a filtered extract to
`evidence/` (a full-load trace is tens of MB and the gate FAILs at 30 MB).
`perf trace` prints pointers by default too, but it needs `kernel.perf_event_paranoid` low enough to read
`/sys/kernel/tracing/events/raw_syscalls/`; on a `paranoid=2` box it dies with a permissions error —
strace is the tool to reach for (or run perf under sudo).

## Was the page written, or remapped? (no tracer at all)
`echo 4 > /proc/<pid>/clear_refs` clears the **soft-dirty** bits (the kernel write-protects the PTEs
afterwards, so a LATER write — including a kernel `copy_to_user`) sets them again. Read
`/proc/<pid>/pagemap` for the pages covering the region: one 8-byte word per page, present = bit 63,
soft-dirty = bit 55, PFN = bits 0-54.

- soft-dirty SET after the window => the pages were WRITTEN in place.
- `/proc/<pid>/maps` for the region byte-identical (same start/end/perm/offset/dev/inode) AND no
  `mmap`/`mremap`/`munmap`/`mprotect` event covering it => nothing remapped them.
- PFNs may read as **0** for a same-uid reader on some hosts (only the flag bits survive); verify that on
  your own box before gating on PFN equality, and gate on soft-dirty + maps identity instead.

## Candidate table for "who wrote these bytes with no store in my window"
Print the predictions from the baseline BEFORE the run (the shape rule) — the candidates must disagree on
different observables, and each observable gets its own gate:

| candidate | read-buffer leg | maps / soft-dirty leg | other-writer leg | sentinel leg |
|---|---|---|---|---|
| kernel write (a syscall destination IS the region) | a read/pread64 whose range covers the poked offsets, on the data fd | maps identical, soft-dirty SET | none | replaced |
| ring-3 store (DR missed it: post-arm thread) | NO covering read | maps identical, soft-dirty SET | none | replaced |
| MAP_FIXED remap / mremap | any | an mmap/mremap covering it, or maps CHANGE | — | replaced |
| out-of-process write | — | maps identical, soft-dirty SET | `process_vm_writev` with that remote pid, or a `pwrite64`/`write` on a `/proc/<pid>/mem` fd | replaced |
| nothing wrote | — | soft-dirty CLEAR | — | SURVIVES |

Poke **distinct** sentinels (one value per offset) at addresses that SPAN the whole region — one per
stride-slot — so the read-back says which part came back, and gate coverage against the observed read
ranges, not just on "a read happened". A destination often lives at a STRUCTURE ANCHOR below the field you
watch (see `code-atlas.md`: the record block is anchor+0x50C), so classify reads by RANGE OVERLAP with the
watched region, not by "buffer address is inside it" — a read that starts below the window can land
squarely on the watched dwords.

## Reuse the box state you already have
Reaching the quiescent pre-load screen costs ~140 s after a relaunch. When a run crashed BEFORE it poked
anything, the box is still parked at that screen with its process-start data built — re-run with the
harness's `--no-relaunch` flag instead of paying the relaunch again; build that flag into every harness
that starts from a fresh process, and print the screen class plus the baseline values it found, so the
reused state is verified rather than assumed.

## The .SAV chain (static, from the Ghidra export)

`FUN_00598340` is the magic/version dispatcher. The .SAV chain: `FUN_00597ee0` opens the file, `_strcmp`s the
256-byte header against the `TERRAN` magic, then calls **`FUN_00596850`** (the body loader), which reads whole
global regions **in place** through the fread-shaped wrapper `FUN_0064cc00(dest, size, count, handle)` — e.g.
`FUN_0064cc00(&DAT_00927590, 0x2ce0 /*11488 = 8×1436*/, 1, handle)`, the per-faction structure array whose
record block sits at anchor+0x50C = 0x927a9c (count at +0, TYPE +4, KEY +0x24, VAL +0x44 relative to the count).
When `DAT_00926a14 != 0` the sibling `FUN_00596540` runs instead: it mallocs a scratch buffer, reads into it, and
stores into the destination in ring 3 (byte-order fixup) — the two paths differ in whether a hardware watchpoint
can see the write at all. LIVE (M106, m106r7 PASS 15/15): the in-place path is what runs — `read(0x5,
0x927c84, 0x2000) = 0x2000` inside the fd-run that carries the save to EOF, and a DR breakpoint CANNOT see a
kernel `copy_to_user` write (Linux installs the user DR breakpoint with the exclude-kernel bit).
