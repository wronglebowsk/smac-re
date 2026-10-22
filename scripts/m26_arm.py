#!/usr/bin/env python3
"""M26: generate evidence/m26_live.gdb armed on the LIVE selected record.

Reads DAT_0091b5bc (selected unit index) from /proc/<pid>/mem, then writes a
gdb script with 3 hardware watchpoints on that record (+16 order-dword, +20 dx,
+28 dy) plus auto-continue entry breakpoints on the whole order path:
  0x476580 MAPH | 0x4d3f70 ACT | 0x4d6fb0 ORDERGIVER | 0x512450 KEYSEL
  0x512b40 KEYROUTE | 0x529090 SOLOWRAP | 0x585720 EXEC | 0x502c40 STEP
  0x4cffa0 ATTACK | 0x4cdc70 BOMB | 0x5ab355 SETTER
Prints the ready-to-run gdb command line.
"""
import struct
import subprocess

GDB = """set pagination off
set confirm off
watch *(int *){b16}
commands
printf "WP_ORDER pc=%#x\\n", $pc
continue
end
watch *(int *){b20}
commands
printf "WP_DX pc=%#x\\n", $pc
continue
end
watch *(int *){b28}
commands
printf "WP_DY pc=%#x\\n", $pc
continue
end
break *0x476580
commands
printf "MAPH p1=%#x p2=%#x p3=%#x sel=%d b5b8=%d b5c4=%d b5e8=%d\\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc), *(int *)0x91b5bc, *(int *)0x91b5b8, *(int *)0x91b5c4, *(int *)0x91b5e8
continue
end
break *0x4d3f70
commands
printf "ACT x=%d y=%d flag=%d sel=%d\\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc), *(int *)0x91b5bc
continue
end
break *0x4d6fb0
commands
printf "ORDERGIVER unit=%d p2=%#x p3=%#x\\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end
break *0x512450
commands
printf "KEYSEL a1=%#x a2=%#x\\n", *(int *)($esp+4), *(int *)($esp+8)
continue
end
break *0x512b40
commands
printf "KEYROUTE a1=%#x\\n", *(int *)($esp+4)
continue
end
break *0x529090
commands
printf "SOLOWRAP idx=%d dir=%#x mode=%#x\\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end
break *0x585720
commands
printf "EXEC idx=%d p2=%#x p3=%#x order=%d\\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc), *(unsigned char*)(0x933278 + 52**(int*)($esp+4) + 17)
continue
end
break *0x502c40
commands
printf "STEP idx=%d dir=%d parity=%d\\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+12)
continue
end
break *0x4cffa0
commands
printf "ATTACK idx=%d x=%d y=%d\\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end
break *0x4cdc70
commands
printf "BOMB idx=%d mode=%#x x=%d y=%d\\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc), *(int *)($esp+0x10)
continue
end
break *0x5ab355
commands
printf "SETTER idx=%d newx=%d\\n", ($esi/52), $bx
continue
end
continue
"""


def main():
    pid = int(subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True,
                             text=True).stdout.split()[0])
    f = open(f"/proc/{pid}/mem", "rb", 0)
    f.seek(0x91B5BC)
    sel = struct.unpack("<I", f.read(4))[0]
    base = 0x933278 + sel * 52
    script = GDB.format(b16=hex(base + 16), b20=hex(base + 20), b28=hex(base + 28))
    open("/home/n100/reverse/smac/evidence/m26_live.gdb", "w").write(script)
    print(f"sel={sel} base={hex(base)}")
    print("gdb -batch -nx -x evidence/m26_live.gdb -p " + str(pid))


if __name__ == "__main__":
    main()
