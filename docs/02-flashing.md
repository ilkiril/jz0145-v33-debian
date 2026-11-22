# 02 — Flashing

## Prerequisites

```
pip install edl pyusb pyserial
```

Loader: `prog_emmc_firehose_8916.mbn` (matches the OpenStick releases).

**Windows:** Zadig must bind **WinUSB** to `05C6:9008`. The binding is per USB port —
use one port for the whole session, otherwise `edl` fails with
`USBError(32, 'Pipe error')` or segfaults.

## Enter EDL

Hold **BOT**, plug USB, wait ~5 s, release. `edl printgpt` should answer. Note that
`edl reset` does **not** work on this board (`Sector size in XML 4096 does not match
disk sector size 512`) — you always need a physical power cycle: unplug, wait 10 s,
replug.

## Flash order

```
edl w gpt_main   gpt_main.bin            # sector 0
edl w gpt_backup gpt_backup.bin          # sector 7733215
edl w sbl1       sbl1.mbn
edl w rpm        rpm.mbn
edl w tz         tz.mbn
edl w hyp        hyp.mbn
edl w aboot      aboot.mbn               # = lk2nd, or the CPR image's aboot
edl w boot       boot.raw                # ext4 image: vmlinuz + dtbs + extlinux
edl w rootfs     rootfs.raw
```

`boot` is *not* a boot.img: the CPR build ships an **ext4 filesystem image**
containing `vmlinuz`, `dtbs/qcom/*` and `extlinux/extlinux.conf`. Mount it, edit the
config, write it back — no repacking tools needed.

## GPT: the part everyone gets wrong

The `gpt_both0.bin` inside the release zips is a template:

- `AlternateLBA` points at ~0.17 GB
- `LastUsableLBA` is small
- the `rootfs` entry has **0 sectors**

Written unchanged, the table is invalid for a 7 733 248-sector disk and the board drops
into EDL on every cold boot. Rebuild it:

```python
DISK        = 7733248
LAST_USABLE = DISK - 34          # 7733214
BACKUP_LBA  = DISK - 1           # 7733215
# rootfs entry: first_lba = boot_last + 1, last_lba = LAST_USABLE
# then recompute header CRC32 and the entries-array CRC32
```

Keep this PARTUUID in the kernel command line or the kernel waits forever for a root
device:

```
root=PARTUUID=a7ab80e8-e9d1-e8cd-f157-93f69b1d141e
```

## Boot args (extlinux.conf)

```
append root=PARTUUID=a7ab80e8-e9d1-e8cd-f157-93f69b1d141e rootfstype=ext4 \
       rootwait rw console=ttyMSM0,115200 maxcpus=1
fdt /dtbs/qcom/msm8916-jz01-45-v33.dtb
```

`maxcpus=1` is mandatory on this revision: with 4 cores the CPR kernel panics in the
CPU hotplug/idle path (`Attempted to kill the idle task`), with 1 core it is stable.
Cost: roughly three quarters of the CPU are idle.

## Verify a flash before power-cycling

```
edl printgpt          # rootfs must show a real size, not 0 sectors
edl r rootfs check.img 0 16
```

Then unplug — not `edl reset`.
