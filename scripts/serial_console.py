#!/usr/bin/env python3
"""Drive a dongle's USB serial console from the host (no PuTTY needed).

    python serial_console.py COM13 "ip -br a" "ls /sys/class/udc"

Every argument is executed in order and the output printed. Close PuTTY first, the
port is exclusive.
"""
import sys
import time

import serial


def read_all(s, wait=1.5):
    end = time.time() + wait
    buf = b""
    while time.time() < end:
        chunk = s.read(4096)
        if chunk:
            buf += chunk
    return buf.decode("utf-8", "replace")


def main():
    port = sys.argv[1] if len(sys.argv) > 1 else "COM13"
    s = serial.Serial(port, 115200, timeout=1)
    time.sleep(0.3)
    s.read(65536)
    s.write(b"\r")
    time.sleep(0.5)
    s.read(65536)
    for cmd in sys.argv[2:]:
        print(f"\n$ {cmd}")
        s.write(cmd.encode() + b"\r")
        print(read_all(s, 2.5))
    s.close()


if __name__ == "__main__":
    main()
