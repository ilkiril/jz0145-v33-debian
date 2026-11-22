# 05 — Replicating this from scratch

Target: someone with the same dongle gets from "unknown device" to `ssh user@<ip>` in
about two hours, including the backup, **without guessing**.

The recipe is only reproducible if you make the same *observations* at the same points.
That is what the checkpoints are for.

## Bill of materials

| Item | Note |
|---|---|
| JZ0145_V33 / UFI001C dongle | this guide is board-specific |
| USB **data** cable | charge-only cables are the classic 30-minute detour |
| PC with Windows or Linux | EDL tooling + ~5 GB free disk for the backup |
| 4 GB free space | full-disk backup, ~40 min at 1.3 MB/s |
| *(optional)* USB-UART adapter | 3.3 V is fine for **reading** only |
| *(optional)* 1.8 V level shifter | only if you want to *send* on UART |

No soldering, no case opening, no test points are required for this recipe.

## Budget

- Backup: 40 min (do not skip; without it there is no way back)
- Flash: 10 min
- First boot + fixing gadget/firmware: 45–60 min
- Total: ~2 h with the backup, ~1 h without

## Checkpoints — stop at the first red one

**K0 — Device is alive.**
`edl printgpt` returns a table. If not: hold BOT while plugging, wait 5 s, release.
Red: no response on a known-good port and a WinUSB binding → wrong cable/port.

**K1 — Geometry recorded.**
Write down `DISK`, `LAST_USABLE`, and every partition start you see.
Red flag: `DISK` is not 7733248 → this is a different variant, all offsets differ.

**K2 — Full backup exists and is verified.**
```
edl rl backup_dir --memory=eMMC            # or wf full dump
md5sum backup.bin                          # write the hash down
```
Red: backup < 3.9 GB → truncated, start over. **Never flash without K2.**

**K3 — GPT valid, or not.**
Parse the table from the image *before* flashing:
`AlternateLBA` must equal `DISK-1`, `LastUsableLBA` = `DISK-34`, and `rootfs` must be
larger than 0 sectors. Most release images fail this. Rebuild, then flash.

**K4 — Kernel and rootfs from the same build.**
```
ls rootfs/lib/modules/                 # e.g. 6.12.1-cpr
```
Must match the kernel version printed at boot. Red: mismatch → the USB gadget will
fail later with `Operation not permitted`, hours after the real mistake.

**K5 — Boot reaches a prompt.**
Serial: `Reached target getty.target` in ≤ 90 s. With 4 cores it panics instead —
add `maxcpus=1`. Red: silent reset → wrong DTB or wrong aboot offset.

**K6 — USB gadget enumerates on the host.**
Host sees a COM port (ACM). Red: `ls /sys/class/udc` empty, or `mkdir` on configfs
returns EPERM (see K4).

**K7 — Network hardware present.**
`ls /sys/class/net` shows `wlan0` (and `wwan0`). Red: only `lo usb0 br0` → the
`modem`/`persist` partitions are empty, restore from the K2 backup.

**K8 — Reachable over the network.**
`ssh user@<ip>` answers. Done.

## What must NOT be copied blindly

- **GPT and offsets** are per-variant. Different eMMC size → different sectors.
- **PARTUUID** in the kernel command line must match the GPT you write.
- **DTB name** differs (`msm8916-jz01-45-v33.dtb` here, `…-uz801v3.dtb` in the release).
- **`maxcpus=1`** is board-specific; try 4 cores again after everything else works and
  keep the working command line in `/boot`.
- **Firmware** comes from *your* device's backup. Someone else's `modem.img` carries
  their calibration data.

## Reproducibility rules that saved hours

1. **One variable per flash.** GPT, bootloader, kernel, rootfs, firmware — not all at
   once. Otherwise a failure tells you nothing.
2. **Log everything to a partition that survives** (`/boot/gadget.log`), not to the
   console that the failing component might be breaking.
3. **Same USB port, same binding.** WinUSB bindings are per port; switching ports
   silently swaps the driver underneath you.
4. **Never `edl reset` on this board.** Power cycle, 10 s. And `edl reset` fails anyway
   with `Sector size in XML 4096 does not match disk sector size 512`.
5. **Screenshots are not evidence.** Paste the text.

## If you have a second stick

The whole recipe becomes a 15-minute script, because K0–K4 are already known:
backup it, rebuild its GPT with its own geometry, flash the same build, restore its own
`modem`/`persist`, done. Keep the backup of every unit — the calibration data is
unique per device and cannot be regenerated.
