# Evidence: the three failure modes, verbatim

## 1. Old kernel (6.12.1-msm8916, 2022 vintage) — dies at ~0.9 s

```
[750] Updating device tree: done
[900] booting linux @ 0x80000000, ramdisk @ 0x82000000, tags/device tree @ 0x81e00000
[910] Jumping to kernel via monitor
[    0.000000] Linux version 5.15.0-handsomekernel+ (guo@guo-Server) #17 SMP PREEMPT
...
evm: HMAC attrs: 0x1
Unable to handle kernel paging request at virtual address fffffe0000078a10
Mem abort info:
  ESR = 0x0000000096000044
  EC = 0x25: DABT (current EL), IL = 32 bits
  SET = 0, FnV = 0
  EA = 0, S1PTW = 0
  FSC = 0x04: level 0 translation fault
Call trace:
 __pagevec_lru_add
```

Result: silent reset, board looks dead, no LED, back in nothing (not even EDL).
With the CPR build and 4 cores the panic moves to the scheduler:

```
Attempted to kill the idle task
```

Same kernel with `maxcpus=1` boots to a login prompt in ~51 s.

## 2. Module version mismatch — gadget silently fails

```
+ mkdir -p /sys/kernel/config/usb_gadget/g1
mkdir: cannot create directory '/sys/kernel/config/usb_gadget/g1': Operation not permitted
```

`libcomposite` reports as loaded, `mount | grep configfs` is fine, but the module was
built for another kernel (`/lib/modules/6.12.1-msm8916` vs running `6.12.1-cpr`).
Every configfs write fails, no USB device appears on the host, and the console stays
on UART only.

## 3. Firmware partitions wiped by the new GPT

```
remoteproc1: Direct firmware load for wcnss.mdt failed with error -2
remoteproc1: powering up a204000.remoteproc
remoteproc1: request_firmware failed: -2
remoteproc0: Direct firmware load for mba.mbn failed with error -2
remoteproc0: Boot failed: -2
qcom-venus 1d00000.video-codec: Direct firmware load for qcom/venus-1.8/venus.mbn failed with error -2
```

`/lib/firmware` contains only `msm-firmware-loader/`; `mnt/modem` and `mnt/persist`
are empty because the partitions were overwritten. Restoring both from the factory
backup yields:

```
qcom-wcnss-pil a204000.remoteproc: timed out on wait
qcom_wcnss_ctrl ...: WCNSS Version 1.5 1.2
wcn36xx: mac address: 02:00:96:d0:24:c6
wcn36xx: firmware WLAN version 'WCN v2.0 RadioPhy vUnknown with 19.2MHz XO'
wcn36xx: firmware API 1.5.1.2, 41 stations, 2 bssids
```

and `wlan0` + `wwan0` exist.
