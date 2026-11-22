#!/usr/bin/env python3
"""Rebuild the GPT of an OpenStick image so it is valid for the real eMMC.

The GPT shipped in the release zips is a template: AlternateLBA points at ~0.17 GB,
LastUsableLBA is small, and the `rootfs` entry is 0 sectors long. Written unchanged to
a 0x760000-sector disk, every cold boot falls back into EDL and the board looks dead.

Usage
-----
    python rebuild_gpt.py --src gpt_both0.bin --disk 7733248 \\
        --out-main gpt_main.bin --out-backup gpt_backup.bin

    # make rootfs start right after `boot` and run to the end of the disk
    python rebuild_gpt.py --src gpt_both0.bin --disk 7733248 \\
        --rootfs-after boot --uuid a7ab80e8-e9d1-e8cd-f157-93f69b1d141e \\
        --out-main gpt_main.bin --out-backup gpt_backup.bin

    # drop partitions you do not need (system, userdata, ...)
    python rebuild_gpt.py ... --drop system,userdata,cache,recovery

Reads either `gpt_both0.bin` (main + backup) or `gpt_main0.bin`. Writes a 34-sector
main image (LBA 0..33) and a 33-sector backup image (entries + header) which belong at
sector 0 and sector DISK-1 respectively.
"""
import argparse
import struct
import uuid
import zlib

HDR = 512          # GPT header lives at LBA 1
ENTRIES = 1024     # partition entry array at LBA 2


def read_template(path):
    data = bytearray(open(path, "rb").read())
    if data[HDR:HDR + 8] != b"EFI PART":
        raise SystemExit(f"{path}: no GPT signature at offset 512")
    n = struct.unpack_from("<I", data, HDR + 80)[0]
    esz = struct.unpack_from("<I", data, HDR + 84)[0]
    if not (0 < n <= 256 and 128 <= esz <= 4096):
        raise SystemExit(f"{path}: implausible entry count/size ({n}/{esz})")
    return data, n, esz


def entries(data, n, esz):
    out = []
    for i in range(n):
        off = ENTRIES + i * esz
        e = data[off:off + esz]
        if e[:16] == b"\x00" * 16:
            continue
        first, last = struct.unpack_from("<QQ", e, 32)
        name = e[56:128].decode("utf-16-le").rstrip("\x00")
        out.append({"idx": i, "off": off, "first": first, "last": last, "name": name})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--disk", type=int, required=True, help="total sectors, e.g. 7733248")
    ap.add_argument("--out-main", default="gpt_main.bin")
    ap.add_argument("--out-backup", default="gpt_backup.bin")
    ap.add_argument("--rootfs-after", default=None,
                    help="name of the partition the rootfs should follow, e.g. boot")
    ap.add_argument("--rootfs-size", type=int, default=None,
                    help="fixed rootfs size in sectors (default: to end of disk)")
    ap.add_argument("--uuid", default=None,
                    help="PARTUUID the kernel command line expects")
    ap.add_argument("--drop", default="", help="comma separated names to remove")
    ap.add_argument("--dry-run", action="store_true", help="print the result, write nothing")
    a = ap.parse_args()

    data, n, esz = read_template(a.src)
    parts = entries(data, n, esz)
    print(f"template: {a.src}  entries={len(parts)}  disk={a.disk} sectors")

    drop = {x.strip() for x in a.drop.split(",") if x.strip()}
    for p in parts:
        if p["name"] in drop:
            data[p["off"]:p["off"] + esz] = b"\x00" * esz   # zero the type GUID
            print(f"  dropped: {p['name']}")

    last_usable = a.disk - 34
    boot = next((p for p in parts if p["name"] == a.rootfs_after), None) if a.rootfs_after else None
    rootfs = next((p for p in parts if p["name"] == "rootfs"), None)
    if rootfs is None:
        raise SystemExit("template has no partition named 'rootfs'")

    start = (boot["last"] + 1) if boot else rootfs["first"]
    end = start + a.rootfs_size - 1 if a.rootfs_size else last_usable
    struct.pack_into("<QQ", data, rootfs["off"] + 32, start, end)
    print(f"  rootfs: {start} .. {end}  ({(end - start + 1) * 512 / 2**30:.2f} GiB)")

    if a.uuid:
        data[rootfs["off"] + 16:rootfs["off"] + 32] = uuid.UUID(a.uuid).bytes_le
        print(f"  rootfs PARTUUID: {a.uuid}")

    if a.dry_run:
        print("\ndry run - nothing written")
        return

    arr = bytes(data[ENTRIES:ENTRIES + n * esz])
    struct.pack_into("<Q", data, HDR + 24, 1)                 # MyLBA
    struct.pack_into("<Q", data, HDR + 32, a.disk - 1)        # AlternateLBA
    struct.pack_into("<Q", data, HDR + 48, last_usable)       # LastUsableLBA
    struct.pack_into("<I", data, HDR + 88, zlib.crc32(arr) & 0xFFFFFFFF)
    struct.pack_into("<I", data, HDR + 16, 0)
    struct.pack_into("<I", data, HDR + 16, zlib.crc32(bytes(data[HDR:HDR + 92])) & 0xFFFFFFFF)
    open(a.out_main, "wb").write(data[:34 * 512])
    print(f"wrote {a.out_main} (34 sectors, goes to sector 0)")

    bak = bytearray(33 * 512)
    bak[:len(arr)] = arr
    hdr = bytearray(data[HDR:HDR + 92])
    struct.pack_into("<Q", hdr, 24, a.disk - 1)
    struct.pack_into("<Q", hdr, 32, 1)
    struct.pack_into("<Q", hdr, 72, a.disk - 33)
    struct.pack_into("<I", hdr, 16, 0)
    struct.pack_into("<I", hdr, 16, zlib.crc32(bytes(hdr)) & 0xFFFFFFFF)
    bak[32 * 512:32 * 512 + 92] = hdr
    open(a.out_backup, "wb").write(bak)
    print(f"wrote {a.out_backup} (33 sectors, goes to sector {a.disk - 1})")

    print("\nflash:")
    print("  edl w gpt_main   %s" % a.out_main)
    print("  edl w gpt_backup %s" % a.out_backup)
    print("  edl printgpt     # rootfs must NOT show 0 sectors")


if __name__ == "__main__":
    main()
