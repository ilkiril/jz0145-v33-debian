# 04 — WiFi and modem firmware

## The symptom

```
remoteproc1: Direct firmware load for wcnss.mdt failed with error -2
remoteproc0: Direct firmware load for mba.mbn failed with error -2
```

`/lib/firmware` contains only `msm-firmware-loader/`. No `wlan0`, no `wwan0`,
NetworkManager sees no WiFi device at all.

## Where the firmware actually lives

Not in the rootfs. `msm-firmware-loader.service` mounts the device's own Android
partitions into the firmware search path:

```
/lib/firmware/msm-firmware-loader/mnt/modem
/lib/firmware/msm-firmware-loader/mnt/persist
```

and symlinks `target/<soc>/**` to `mnt/<part>/image/**`.

After a GPT change, `modem` and `persist` are typically empty — everything that was
there before the new table was written is gone. That is not a missing package; the
data has to come back.

## Restore from the factory backup

If you dumped the whole disk before flashing (`wf backup.bin`), cut the two partitions
out and write them back:

```python
S = 512
ranges = {                      # JZ0145_V33 factory layout
    "modem":   (131072,  131072),   # start sector, sector count
    "persist": (2067552, 65536),
}
```

```sh
edl w modem   fw_modem.img
edl w persist fw_persist.img
```

`modem` begins with `eb3c904d 53444f53…` — a Qualcomm firmware container, not a
filesystem. `persist` is ext4 (superblock at offset 1024).

After a power cycle:

```
wcn36xx: firmware WLAN version 'WCN v2.0 RadioPhy vUnknown with 19.2MHz XO'
wcn36xx: firmware API 1.5.1.2, 41 stations, 2 bssids
```

and `wlan0` appears with a MAC from `persist`. `wwan0` also comes up (BAM-DMUX), but
stays `DOWN` until a SIM is inserted.

## Joining a network

```
ip link set wlan0 nomaster          # it may be enslaved to the AP bridge br0
ip addr flush dev br0; ip link set br0 down    # br0 shares 192.168.100.1 with usb0
nmcli device wifi connect 'YourSSID' password 'secret' ifname wlan0
```

`nmcli device wifi list` on this driver sometimes shows only 4 networks. `iw dev wlan0
scan` is reliable — use it when the expected SSID seems to be missing.

If `nmcli` hangs, it is usually retrying a wrong PSK: interrupt with Ctrl-C, the
driver reloads and `wlan0` comes back after ~10 s.

## Known-good result

```
wlan0  UP  192.168.178.141/24
ssh    active
```

Boot to login prompt: ~51 s with `maxcpus=1`.
