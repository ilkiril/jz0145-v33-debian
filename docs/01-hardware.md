# 01 — Hardware

## Board

| | |
|---|---|
| Model | JZ0145_V33, sold as UFI001C / M5311-class 4G dongle |
| SoC | Qualcomm MSM8916, 4× Cortex-A53 @ 1.0–1.2 GHz |
| RAM | 512 MB |
| eMMC | 004GE0, 3.69 GiB usable, **7 733 248 sectors (0x760000)** |
| Partitions on disk | 14 (`mmcblk0p1` … `mmcblk0p14`) |
| Windows name at boot | `MSM8916` / `OpenStick` |
| VID:PID EDL | `05C6:9008` |
| VID:PID fastboot (lk2nd) | `18D1:D00D` |

The board is close to the **UZ801 v3** but boots a different DTB and has a different
factory partition layout. Do not paste a UZ801 GPT onto it.

## eMMC geometry (factory)

```
DISK         7733248 sectors
LAST_USABLE  7733214
BACKUP GPT   7733215
```

Factory partition starts (sector):

```
modem     131072   (131072 sectors, 64 MB)   <- WCNSS + modem firmware
sbl1      262144   (ROM-fixed, do not move)
rpm       263168
tz        264192
hyp       266240
aboot     264192   (as laid out by the factory GPT)
boot      396384
persist  2067552   (65536 sectors, 32 MB, ext4)
```

`aboot` **must** end up where the ROM looks for it. On the OpenStick template GPT it
lands at 524288 and the boot ROM then finds nothing — which looks exactly like a
bricked board.

## UART

- `ttyMSM0`, **115200 8N1**
- Pins: RX = 26, TX = 32 (logic level **1.8 V** on this revision)
- Reading with a 3.3 V adapter (Bus Pirate, CH340) is fine.
- **Never drive TX** into the SoC from a 3.3 V adapter without a level shifter — you
  can kill the pin.

Practical detail: the console is also exported over the USB gadget as ACM
(`Serielles USB-Gerät`, `getty@ttyGS0`). Once the gadget works you no longer need
probes; open the COM port at 115200 and log in.

## LEDs

GPIO 6 / 7 / 8, driven by software. A board that is booting, hung, or in EDL is
**dark** — an unlit LED is not evidence of a dead device.
