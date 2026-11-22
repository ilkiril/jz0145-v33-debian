# Where to post this (and in which order)

Post **evidence, not a success story**. Maintainers close "it works!" issues; they
cannot ignore a reproducible failure with a log.

## 1. Mio-sha512/OpenStick-Builder — the build we used

Best place for the CPR/`maxcpus=1` finding, because it is *their* kernel.

> **JZ0145_V33 (UFI001C): CPR build boots with `maxcpus=1`, panics with 4 cores**
>
> Board: JZ0145_V33 / UFI001C, MSM8916, 512 MB, eMMC 0x760000 sectors.
> Using the `cpr` release (kernel 6.12.1-cpr) with the shipped rootfs.
>
> With the default command line the kernel panics ~0.9 s after `Jumping to kernel`:
>
> ```
> Attempted to kill the idle task
> Unable to handle kernel paging request at virtual address ...
> ESR = 0x96000044  EC = 0x25: DABT
> ```
>
> Adding `maxcpus=1` boots reliably to a login prompt in ~51 s (systemd 257.9,
> Debian 13, arm64). The DTB must be `msm8916-jz01-45-v33.dtb`; the asset ships
> `msm8916-yiming-uz801v3.dtb`.
>
> Two related observations, both reproducible:
> 1. `gpt_both0.bin` in the release is a template — `AlternateLBA` ~0.17 GB and
>    `rootfs` with 0 sectors. Written raw to a 0x760000-sector disk the board falls
>    back into EDL on every cold boot.
> 2. If rootfs and kernel come from different builds, `libcomposite` loads but every
>    configfs write returns `Operation not permitted`, so the gadget silently fails.
>
> Logs attached. Full recipe: <repo URL>

## 2. OpenStick/OpenStick — the firmware partition trap

> **After a GPT change `modem`/`persist` are empty → no WiFi, no modem**
>
> `msm-firmware-loader` mounts the device's own `modem` and `persist` partitions into
> `/lib/firmware/msm-firmware-loader/mnt/*`. If you rewrite the partition table, those
> partitions come back empty and the kernel reports
> `Direct firmware load for wcnss.mdt / mba.mbn failed with error -2`.
>
> It is *not* a missing package: restore the two partitions from a full-disk backup
> (JZ0145_V33: modem @131072 +131072 sectors, persist @2067552 +65536) and `wcn36xx`
> loads normally. Worth a line in the README — it is the single most confusing symptom
> after flashing, because Debian boots fine and just has no network hardware.

## 3. postmarketOS wiki

The mainline MSM8916 device page for UZ801-style dongles. Add a short "JZ0145_V33"
variant section: different DTB, `maxcpus=1`, different factory offsets.

## 4. Reddit / forums

`r/postmarketOS`, XDA, 4pda (RU). Link the repo, do not re-paste the whole text.

---

## Before you publish

- [ ] No WiFi PSK, no hostnames, no IPs of your home network in the repo or logs
- [ ] `captures/` contains logs, not screenshots of logs
- [ ] Say clearly what is **not** tested (SIM/4G, 4 cores, suspend)
- [ ] MIT licence file present, so people can actually reuse the scripts
