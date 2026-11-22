#!/bin/sh
# USB gadget for MSM8916 dongles in peripheral-only mode: RNDIS + serial console.
# Install as /usr/local/sbin/usb-gadget-simple.sh and start from a systemd unit
# after libcomposite is available. Logs to /boot/gadget.log so the output survives
# a broken console.
set -eu

LOG=/boot/gadget.log
G=/sys/kernel/config/usb_gadget/g1

log() { echo "[gadget] $*" | tee -a "$LOG"; }

modprobe libcomposite
mountpoint -q /sys/kernel/config || mount -t configfs none /sys/kernel/config
[ -d /sys/kernel/config/usb_gadget ] || { log "configfs missing"; exit 1; }

# Idempotent: never use `[ -d "$G" ] && {...}` under set -e.
if [ -d "$G" ]; then
    log "gadget already present, rebinding"
else
    mkdir -p "$G"
fi

mkdir -p "$G/strings/0x409" "$G/configs/c.1/strings/0x409"

echo 0x1d6b > "$G/idVendor"
echo 0x0104 > "$G/idProduct"
echo 0x0100 > "$G/bcdDevice"
echo 0x0200 > "$G/bcdUSB"
echo 0123456789 > "$G/strings/0x409/serialnumber"
echo "MSM8916"     > "$G/strings/0x409/manufacturer"
echo "OpenStick"   > "$G/strings/0x409/product"
echo "rndis+acm"   > "$G/configs/c.1/strings/0x409/configuration"

mkdir -p "$G/functions/rndis.usb0" "$G/functions/acm.GS0"
echo 02:11:22:33:44:55 > "$G/functions/rndis.usb0/host_addr"
echo 02:11:22:33:44:66 > "$G/functions/rndis.usb0/dev_addr"

ln -sf "$G/functions/rndis.usb0" "$G/configs/c.1/rndis.usb0"
ln -sf "$G/functions/acm.GS0"    "$G/configs/c.1/acm.GS0"

UDC=$(ls /sys/class/udc | head -1)
[ -n "$UDC" ] || { log "no UDC"; exit 1; }

echo "$UDC" > "$G/UDC"
log "bound to $UDC"
sleep 1

# Host side: RNDIS network 192.168.100.1/24, ACM console on getty@ttyGS0
ip link set usb0 up || true
ip addr replace 192.168.100.1/24 dev usb0 || true
systemctl start getty@ttyGS0.service || true

log "done"
