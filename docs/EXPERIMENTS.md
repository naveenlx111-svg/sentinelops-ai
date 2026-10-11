# Experiments

Measured results only. An experiment that has not been executed is marked
**NOT RUN**; incomplete or uncertain results say so.

| ID | Date | Title | Status |
|---|---|---|---|
| EXP-001 | 2026-10-11 | Memory baseline and container OOM behaviour | **NOT RUN** — assigned to the owner |
| EXP-002 | 2026-10-11 | Memory footprint of the shop as local processes | Run once; indicative only |

---

## EXP-001: Memory baseline and container OOM behaviour

- **Status:** **NOT RUN.** Parts A–C are assigned to the owner. The only data
  below is a snapshot the agent took while inspecting the machine.
- **Date assigned:** 2026-10-11
- **Objective:** (1) Establish how much memory is really available for this
  project during normal desktop use. (2) Observe what a container looks like
  when the kernel kills it for exceeding its memory limit.
- **Hypothesis:** A container limited to 64 MiB with no swap that writes
  200 MiB is killed by the kernel: it exits with a signal-derived exit code,
  prints nothing, and Docker and the kernel log each record the kill. With a
  512 MiB limit the same command succeeds.
- **Environment:** Arch Linux, kernel 7.2.6-arch2-1, KDE Plasma on Wayland,
  cgroup v2 with the systemd cgroup driver.
- **Hardware:** Intel Core i7-13700HX (24 threads), 15 GiB RAM, 16 GB swap
  file plus 4 GB zram, NVIDIA RTX 5060 Laptop GPU with 8 GB VRAM.
- **Code revision:** None; the experiment uses no project code.
- **Dependencies:** Docker Engine 29.8.1; image `python:3.14-slim`, already
  present locally.
- **Workload:** One Python process allocating and writing 200 MiB.

### Test setup and commands

Part A — baseline, with normal applications left open:

```bash
free -h
cat /proc/pressure/memory
docker stats --no-stream
```

Part B — trigger:

```bash
docker run --name oom-lab --memory=64m --memory-swap=64m python:3.14-slim \
  python -c "data = b'x' * (200 * 1024 * 1024); print('survived')"
echo "exit code: $?"
```

Part C — find three independent pieces of evidence that the kernel killed the
process. Starting points: `docker inspect oom-lab`, `journalctl -k --since "5
minutes ago"`, `docker logs oom-lab`.

Control — repeat Part B as `oom-lab-2` with both limits at `512m`.

Cleanup — `docker rm oom-lab oom-lab-2`.

### Metrics to collect

`available` memory, memory pressure averages, per-container memory, the exit
code of each run, and the three pieces of evidence.

### Agent snapshot (2026-10-11, taken during environment inspection)

Not part of the experiment proper, recorded because it is real data:

| Measure | Value |
|---|---|
| Memory total / used / available | 15 GiB / 9.3 GiB / 6.0 GiB |
| zram swap | 3.7 GB of 4 GB used |
| Swap file | 269 MB of 16 GB used |
| Memory pressure, `some` avg10 / avg60 / avg300 | 0.00 / 0.00 / 0.02 |
| Largest processes by resident memory | `baloo_file` 1.3 GB; Chrome several processes of 0.3–1.0 GB; `plasmashell` 0.6 GB |
| Running containers (another project) | 3 containers, about 280 MiB total |

Reading: the machine was not stalling on memory at that moment, but had about
6 GiB of headroom with the desktop in normal use.

### Results

**NOT RUN.**

### Observations, failures, interpretation

None yet.

### Limitations

One machine, one moment. The baseline depends on which applications are open.

### Next actions

The owner runs Parts A–C and the control and sends the outputs. The agent
records them here unedited and reviews the interpretation.

### Raw artifacts

None yet.

---

## EXP-002: Memory footprint of the shop as local processes

- **Status:** Run once by the agent. Indicative only.
- **Date:** 2026-10-11
- **Objective:** Get a first real number for how much memory the shop needs,
  to inform the memory limits set when it is containerized.
- **Hypothesis:** None stated in advance; this was a measurement taken during
  end-to-end verification.
- **Environment:** Arch Linux, kernel 7.2.6-arch2-1. The four services ran as
  ordinary host processes, not in containers. PostgreSQL ran in a container.
- **Hardware:** As EXP-001.
- **Code revision:** Branch `phase-1/shop-services`, the working tree shortly
  before the commit that adds this record. The readiness check was changed
  after the measurement to query each service's table; the figures were not
  re-measured.
- **Dependencies:** Python 3.14.7, FastAPI 0.143.0, Starlette 1.7.0,
  uvicorn 0.54.0, SQLAlchemy 2.1.4, psycopg 3.3.6, httpx 0.28.1,
  pydantic 2.14.0; image `postgres:18-alpine`.
- **Workload:** One pass of `scripts/smoke.sh`: eight HTTP requests through
  the gateway, plus a handful of health and readiness requests. No sustained
  load.

### Test setup and commands

Each service was started with
`uvicorn shop.<service>.app:create_app --factory --host 127.0.0.1 --port <port>`,
one worker each. After the smoke test, resident memory was read with
`ps -o rss= -p <pid>`, and the PostgreSQL container with
`docker stats --no-stream`.

### Results

| Process | Resident memory |
|---|---|
| gateway | 67 MiB |
| users | 92 MiB |
| catalog | 93 MiB |
| checkout | 99 MiB |
| PostgreSQL (container, limited to 256 MiB) | 35 MiB |
| **Total** | **about 386 MiB** |

### Observations

- The three services that load SQLAlchemy and the PostgreSQL driver use about
  25–32 MiB more than the gateway, which loads neither.
- All 8 smoke checks passed during the run.

### Interpretation

Nearly idle, the whole shop fits in roughly 0.4 GiB. Against about 6 GiB
available (EXP-001 snapshot) the shop is not what will strain this machine;
the observability stack is the part to measure next.

### Limitations

- A single run with almost no traffic. Memory under load is unknown.
- Resident memory counts pages shared between the four processes once per
  process, so the total overstates what they use together.
- Host processes, not containers. Whether running in containers changes
  these figures was not measured.

### Next actions

Repeat inside containers once the owner has built them, and again under load
in Phase 9.

### Raw artifacts

None kept; the figures above were read from the terminal during the run.
