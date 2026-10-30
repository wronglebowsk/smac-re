M112 STATIC PASS DONE (s171) — the 156-B tail is a fixed TRAILER (last 152 B identical across all 9 saves, only the final dword differs; offset varies with file size). Its reader is UNNAMED: the loader's 152-B leg (0x597716) lands at 0x92bf58 = [9999,9999,0,0,2100,2600], not the trailer; the 156 B is absent from 523 MB of mem; rows 6x at heap 0x34f0000. Not merged (PR #116).
BOX LOADED: terran.exe 1573718, 67/18, TracerPid 0, no driver/gdb.
next: one run — census an AUTOSAVE (trailer at a different offset) with the FILE* filter ($savefile 0x596850), predict sum = filesize - 156.
