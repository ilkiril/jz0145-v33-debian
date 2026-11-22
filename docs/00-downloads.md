# Downloads (pinned)

Sizes are given so you can tell a truncated download from a good one. All of these
change over time — if a size differs, check the release notes before flashing.

## 1. Debian image (the one this guide was verified with)

`Mio-sha512/OpenStick-Builder`, release asset `openstick-debian.zip`
(CPR build, kernel `6.12.1-cpr`):

```
https://github.com/Mio-sha512/OpenStick-Builder/releases
```

Expected contents of the zip (sizes in bytes):

| file | size | note |
|---|---|---|
| `sbl1.mbn` | 258 568 | secondary bootloader |
| `rpm.mbn` | 154 804 | resource/power manager |
| `tz.mbn` | 605 312 | trust zone |
| `hyp.mbn` | 10 424 | hypervisor |
| `aboot.mbn` | 262 464 | = lk2nd on this build |
| `boot.bin` | 32 129 492 | **ext4 image**, kernel + dtbs + extlinux |
| `rootfs.bin` | 726 417 272 | Debian 13 rootfs |
| `gpt_both0.bin` | 34 304 | **template — must be rebuilt**, see 02 |

`unzip -l` first. If `sbl1.mbn` is missing from your extraction, the flash stops after
the GPT and the board stays in EDL — that has happened and cost an hour.

## 2. EDL loader

`prog_emmc_firehose_8916.mbn`, shipped inside:

```
https://github.com/OpenStick/OpenStick/releases/download/v1/base.zip
```

`pip install edl pyusb pyserial` provides the `edl` command.

## 3. Your own factory backup

There is no download for this. Dump it before flashing anything:

```
edl rl backup_dir --memory=eMMC     # or edl wf backup.bin for a full dump
md5sum backup.bin
```

It is the only source for `modem` and `persist` — without them there is no WiFi and no
modem afterwards (see 04).

## Verify before you flash

```
edl printgpt                      # table readable?
python3 scripts/rebuild_gpt.py --src gpt_both0.bin --disk <sectors> --dry-run
```

`--disk` must equal what `printgpt` reports as the disk size. For the JZ0145_V33 that is
7733248 sectors; anything else is a different variant and every offset in these docs is
wrong for it.
