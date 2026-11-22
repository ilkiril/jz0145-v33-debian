# JZ0145_V33 / UFI001C — Debian 13 on a Qualcomm MSM8916 4G dongle

Working, reproducible recipe for getting **Debian 13 (trixie) with SSH** onto the
JZ0145_V33 4G dongle (sold as *UFI001C*, *M5311*-class hardware, MSM8916, eMMC 3.94 GB).

The board is nearly identical to the **UZ801 v3** that most guides target, but three
things differ and each of them looks like a dead device if you don't know it.

Status: **boots, WiFi works, SSH works.** Modem (`wwan0`) enumerates; no SIM tested yet.

---

## TL;DR — the five things that cost the most time

| Symptom | Real cause | Fix |
|---|---|---|
| Board appears dead after flashing, always back in EDL | GPT from the release zips is a **template** (`AlternateLBA` → 0.17 GB, `rootfs` = 0 sectors). Written raw it is invalid, so every cold boot falls into EDL | Recompute `LastUsable`, backup LBA and both CRCs for the real geometry (0x760000 sectors, backup @ 7733215) |
| Kernel dies ~0.9 s after `Jumping to kernel` | `.98`/2022 kernel panics in `cpr_driver_init` on this rev | Use the **CPR build** + `maxcpus=1` |
| Debian boots over serial, but no USB device appears | rootfs modules are `6.12.1-<other>`, kernel is `6.12.1-cpr` → `libcomposite` can't load | rootfs and kernel from the **same build** |
| No `wlan0`, no `wwan0`, `wcnss.mdt` / `mba.mbn` error -2 | GPT change wiped the Android `modem` and `persist` partitions the firmware loader needs | Restore both from your factory backup by offset |
| `edl` segfaults / device not found | Zadig binds WinUSB per **USB port**; another port = libusb-win32 again | Rebind, or use the same port for everything |

Full detail in [`docs/`](docs).

---

## What worked

1. **Image**: CPR build of [OpenStick-Builder](https://github.com/Mio-sha512/OpenStick-Builder)
   (release asset with `cpr` in the name) — kernel `6.12.1-cpr`, Debian 13 rootfs.
2. **Boot args**: add `maxcpus=1` to `extlinux.conf`. Without it the kernel panics
   (`Attempted to kill the idle task`).
3. **DTB**: `msm8916-jz01-45-v33.dtb` (the release ships `msm8916-yiming-uz801v3.dtb`).
4. **GPT**: rebuilt on the factory geometry so `aboot` sits where the ROM looks for it.
5. **USB gadget**: hand-written configfs script (RNDIS + ACM). The shipped
   `msm8916-usb-gadget.sh` aborts with *"OTG role control not available"*.
6. **Firmware**: `modem` + `persist` restored from the factory backup.
7. **Login**: `user` / `1`, root locked → `sudo -i`.

---

## Layout

```
docs/00-downloads.md    pinned sources, expected file sizes
docs/01-hardware.md     board, eMMC geometry, partition offsets, UART levels
docs/02-flashing.md     EDL flash order, GPT rebuild, boot args
docs/03-usb-gadget.md   configfs gadget (RNDIS + ACM console)
docs/04-firmware.md     restoring modem/persist for WiFi + modem
docs/05-replication.md  checklist to rebuild the whole thing (K0–K8)
scripts/                rebuild_gpt.py, usb-gadget.sh, serial_console.py
captures/               boot logs and error output as evidence
```

## Evidence

`captures/` contains the raw serial output for the failure modes above — the kernel
Oops, the configfs `Operation not permitted`, the `wcnss.mdt` error. Screenshots of a
terminal are worthless in a bug report; plain logs are not.

## Known limitations (measured, not guessed)

- **Only one CPU.** `maxcpus=1` is required; with four cores the CPR kernel panics in
  the idle/hotplug path. The other three A53s stay idle.
- **No WiFi monitor mode.** `wcn36xx` has no monitor interface — no packet capture of
  foreign traffic, no wardriving.
- **No USB host.** The controller runs peripheral-only; no hub, no storage, no printer.
- **No GPIO, no camera.** UART, LEDs and the SIM slot are the only exposed hardware.
- **LTE registration may be refused by the operator.** On this unit two different SIMs
  on the same network (Vodafone DE) both end in
  `registration-denied / roaming: on / limited`, while the same SIM registers fine in a
  phone; signal is −89 dBm and the home PLMN matches the SIM. EFS was wiped and
  rebuilt, firmware is `MPSS.DPM.2.0.c12`. Remaining suspect is a network-side device
  (IMEI/EIR) block — check with the operator before assuming a config problem.
- Booting takes ~51 s, RAM is 376 MiB usable, eMMC 3.43 GiB.

## License

MIT. Take it, fork it, correct it.

<img width="1386" height="467" alt="image" src="https://github.com/user-attachments/assets/787077b0-1fc8-420f-8b15-cb5c3fa56063" />
