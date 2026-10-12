# Incidents and debugging

Real failures met while building or operating this project, and how each was
diagnosed. An entry records what was observed, not what was guessed; a fix
that has not been applied is marked **NOT RUN**.

| ID | Date | Title | Status |
|---|---|---|---|
| DBG-001 | 2026-10-12 | `pacman -S` fails with 404 from every mirror | Closed 2026-10-12, verified after reboot |

---

## DBG-001: `pacman -S` fails with 404 from every mirror

- **Date:** 2026-10-12
- **Where:** the development machine, during task P0-2b (install Buildx and
  the packaged Compose plugin).
- **Status:** Closed. Fixed by the owner on 2026-10-12 and verified after
  the reboot the same day.

### Symptom

```text
$ sudo pacman -S docker-buildx docker-compose
Packages (2) docker-buildx-0.37.1-1  docker-compose-5.5.1-1
...
error: failed retrieving file 'docker-buildx-0.37.1-1-x86_64.pkg.tar.zst'
       from geo.mirror.pkgbuild.com : The requested URL returned error: 404
       (the same from about twenty other mirrors; one timed out instead)
error: failed to commit transaction (failed to retrieve some files)
Errors occurred, no packages were upgraded.
```

`docker buildx version` then answered `unknown command: docker buildx`.

### Impact

- Buildx is still not installed, so the shop image cannot be built yet.
- The hand-installed Compose plugin had already been moved to
  `~/docker-compose.manual-backup` by the next command in the same pasted
  block, so `docker compose` is unavailable as well until the fix is applied
  or the file is moved back.
- Running containers were not affected. Nothing was installed or upgraded:
  pacman downloads every file before it changes anything.

### How a package install is connected

```mermaid
flowchart LR
    pacman -->|"1. read name and version"| lists[("/var/lib/pacman/sync/*.db<br/>local copy of the repository index")]
    pacman -->|"2. HTTPS GET name-version-arch.pkg.tar.zst"| mirror["Mirror<br/>from /etc/pacman.d/mirrorlist, tried in order"]
    pacman -->|"3. verify signature, then install"| root[("Installed system")]
```

The file name in step 2 is built from the version in step 1. A mirror keeps
only the current build of each package. If the local index is older than the
mirror, pacman asks for a file that has since been replaced, and every mirror
correctly answers 404. Pacman's only retry is the next mirror in the list.

### Checks and what they showed

| Check | Result |
|---|---|
| Age of the local index: `ls -l /var/lib/pacman/sync/` | `extra.db` dated 2026-09-23, 19 days old |
| Version the local index names: `pacman -Si docker-buildx` | 0.37.1-1 |
| Does a mirror have that file? `curl -I <mirror>/extra/os/x86_64/docker-buildx-0.37.1-1-x86_64.pkg.tar.zst` | HTTP 404 |
| What the mirror has now (directory listing) | `docker-buildx-0.38.0-1`, `docker-compose-5.6.0-1` |
| Last index refresh: `/var/log/pacman.log` | 2026-09-23, by a `pacman -Sy --needed <packages>` with no upgrade |
| Pending upgrades, computed against a private copy of a fresh index | 561 packages, about 2.3 GiB to download, including `linux` 7.2.6 → 7.2.9, `nvidia-open`, `systemd`, `glibc`, `docker` 29.8.1 → 29.9.0 |

### Root cause

The local package index was 19 days old. It named package builds that the
mirrors had already replaced.

`docker-compose-5.5.1-1` did download, from one mirror that had not yet
dropped the old file. That was luck, not a different cause.

### Contributing factor

The agent's instructions for P0-2b gave `pacman -S` without first checking
how old the package index was, and put the `mv` of the working Compose plugin
in the same block as an install it depended on. A pasted block does not stop
at the first failure, so the working plugin was moved even though its
replacement never arrived.

### Fix

Refresh the index and upgrade the whole system in one transaction, adding the
two new packages, then reboot because the kernel and the NVIDIA driver are
among the upgrades:

```bash
sudo pacman -Syu docker-buildx docker-compose
```

Refreshing the index without upgrading (`pacman -Sy <package>`) is the
tempting shortcut and the wrong one. Arch has no stable release: a package is
built against the libraries that are current on the day it is built. A new
package on top of 19-day-old libraries is a partial upgrade, which Arch does
not support.

Checked before recommending this, on 2026-10-12:

- Arch news since the last full upgrade: one item (2026-09-22, mkinitcpio 42
  and TPM2 unlocking of LUKS devices). It does not apply to how this machine
  is set up.
- Free space: 83 GiB on `/`, 774 MiB on `/boot`.
- The other project's three containers have restart policy `unless-stopped`
  and the Docker service is enabled at boot, so they should return after the
  reboot. To be verified.

### Second attempt, 2026-10-12 — did not complete

The owner ran the fix. `/var/log/pacman.log` and the system journal show:

| Time | Event |
|---|---|
| 10:13:50 | `pacman -Syu docker-buildx docker-compose github-cli`; package index refreshed |
| 10:13:53 | "starting full system upgrade" |
| 10:15:55 | The machine begins a normal shutdown |
| 10:16:24 | The machine is running again |

No package was downloaded, installed or upgraded in those two minutes: the
log has no `installed` or `upgraded` line for the day, the package cache holds
nothing new, and no lock file was left behind. The machine restarted before
the transaction had done any work. The log does not say whether the prompt
was answered.

State afterwards, checked at 10:31: Buildx and Compose still absent, kernel
still 7.2.6, Docker 29.8.1, the other project's three containers back up on
their own after the restart. The system is consistent, but the package index
is now newer than the installed packages, so nothing should be installed with
a plain `pacman -S` until the full upgrade has run.

How to tell the upgrade has finished: pacman prints a numbered
`(n/N) upgrading ...` line for every package, then
`:: Running post-transaction hooks...`, and only then returns the shell
prompt. The reboot comes after that.

### Third attempt, 2026-10-12 — completed

The owner ran the same command again at 10:34:47 and let it finish.
`/var/log/pacman.log` records the transaction starting at 11:31:23 and
completing at 11:31:41, with 561 packages upgraded and 8 installed, among
them `docker-buildx 0.38.0-1`, `docker-compose 5.6.0-1` and
`github-cli 2.102.0-1`. The initramfs build for kernel 7.2.9 reported
"Initcpio image generation successful" and "Unified kernel image generation
successful". One warning: directory permissions differ on `/boot/`
(filesystem 700, package 755), which changes nothing.

### Verification

Checked by the agent at 17:47 on 2026-10-12. The machine had not been
restarted since 10:16, before the upgrade.

| Check | Result |
|---|---|
| `docker buildx version` | 0.38.0 |
| `docker compose version` | 5.6.0 |
| Plugin files in use, from `docker info` | both under `/usr/lib/docker/cli-plugins/`; no user-level plugin left to shadow them |
| `pacman -Qu` | nothing pending |
| Failed systemd units | none |
| The other project's containers | three, up 8 hours, undisturbed by the upgrade |

Three things show the upgrade is installed but not yet running, which is
what an upgrade without a reboot looks like:

| Check | On disk | Running |
|---|---|---|
| Kernel: `pacman -Q linux` against `uname -r` | 7.2.9 | 7.2.6, whose module directory no longer exists |
| Docker: client against server in `docker version` | 29.9.0 | 29.8.1 |
| NVIDIA: library against loaded module | 615.78 | 615.71.09 |

`nvidia-smi` fails with `Failed to initialize NVML: Driver/library version
mismatch`, as predicted before the upgrade. A kernel module built for 7.2.9
at version 615.78.08 is present on disk and will load at the next boot.

### After the reboot

The owner restarted the machine at 17:52. Checked by the agent at 17:53:

| Check | Result |
|---|---|
| `uname -r` | 7.2.9-arch1-1, matching the installed package |
| `docker version` | client 29.9.0, server 29.9.0 |
| `docker buildx version`, `docker compose version` | 0.38.0, 5.6.0 |
| `nvidia-smi` | driver 615.78.08, matching the loaded module |
| `docker ps` | the other project's three containers came back on their own |
| A throwaway container from an image already on disk | ran and exited cleanly |
| `pacman -Qu` | nothing pending |

### Side effect of the upgrade — open, not diagnosed

Since the upgrade to systemd 262, four TPM measurement units fail at boot
(`systemd-tpm2-setup-early`, `systemd-pcrproduct` and two
`systemd-pcrlogin@` instances) with
`Failed to initialize NvPCR index: No such file or directory`, and
`systemctl is-system-running` reports `degraded`. They did not fail on the
two boots before the upgrade. Nothing in this project depends on them and
Docker and the GPU are unaffected. The cause has not been investigated.

### Prevention

- On Arch, install with `-Syu <package>`, or run `-Syu` first. Never `-Sy`
  followed later by `-S`.
- In instructions, a step that removes something working goes after the
  check that its replacement works, not in the same block.
