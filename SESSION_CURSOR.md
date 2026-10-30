M112 STATIC PASS DONE (s171) — the 156-B tail is a fixed TRAILER, write-only by construction. 9 saves share their final 152 B exactly (only the last dword differs); immediate 156 (0x9c) is 13x in the EXE, NEVER in 0x58xxxx-0x59xxxx; not restored (0xbe27b0/0xbe27b4 unrelated, absent from 523 MB, row signature 6x at heap 0x34f0000). Not merged (PR #116).
BOX LOADED: terran.exe 1573718, 67/18, TracerPid 0, no driver/gdb.
next: one run — census an AUTOSAVE (trailer at a different offset) with the FILE* filter ($savefile 0x596850), predict sum = filesize - 156.
