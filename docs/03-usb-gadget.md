# 03 — USB gadget (RNDIS + serial console)

## Why not the shipped script

`msm8916-usb-gadget.sh` from the images aborts immediately:

```
OTG role control not available
```

Mainline on MSM8916 runs the controller in **peripheral-only** mode; there is no OTG
role switch to poke. The script also insists on a `br0` bridge that conflicts with the
NetworkingManager AP profile, and it uses the classic

```sh
[ -d "$G" ] && { echo "exists"; }
```

trap: under `set -e` a false test returns 1, the compound command returns 1, and the
script exits silently. That is why the log ends after one line.

## The working version

`scripts/usb-gadget.sh` in this repo. Key points:

- `modprobe libcomposite` — **requires matching module versions** (see 02)
- gadget `g1`, VID:PID `0x1d6b:0x0104` (Linux Foundation / Multifunction)
- functions: `rndis.usb0` + `acm.GS0`
- UDC: whatever is first in `/sys/class/udc` (here `ci_hdrc.0`)
- brings `usb0` up with `192.168.100.1/24`

Result on the host side (Windows):

- `Serielles USB-Gerät (COMx)` → `getty@ttyGS0`, 115200, login shell
- `RNDIS` network device → needs the *Remote NDIS Compatible Device* driver; on
  Windows 11 use *Update driver → search automatically*

## Debugging checklist

```
ls /sys/class/udc                      # must not be empty
lsmod | grep -E 'libcomposite|u_ether' # both must be present
mount | grep configfs
mkdir /sys/kernel/config/usb_gadget/t && rmdir /sys/kernel/config/usb_gadget/t
```

If `mkdir` returns `Operation not permitted` while `libcomposite` claims to be loaded,
the module is a different build than the running kernel. That was the actual cause of
several hours of "the gadget service failed" on this board.

Log the script's output to `/boot/…` (a plain ext4 partition that survives) — the
serial console is useless once the gadget breaks the console itself.
