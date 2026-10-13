# Learning journal

What the owner has met, practiced and demonstrated. A status moves only on
evidence from the owner's own work — never because something was explained.

**Statuses:** Introduced → Practiced → Independently implemented → Verified by
demonstration. Any topic can be marked *Needs revision*.

## Roadmap

In dependency order: each row needs the rows above it. Topics the owner does
hands-on are marked **hands-on**; the rest are taught as far as needed to
operate and debug the system.

| # | Topic | Depth | Needed for | Status |
|---|---|---|---|---|
| 1 | Linux processes: ports, signals, cgroups, memory | hands-on | Everything containerized | Introduced |
| 2 | Docker images, layers, build cache, registries | hands-on | Phase 1 | Practiced (images, layers, cache); registries Introduced |
| 3 | Docker networking and Compose | hands-on | Phase 1 | Introduced |
| 4 | How the demo services talk: HTTP, timeouts, health endpoints, config by environment | operate and debug | Phase 1 | Not started |
| 5 | Metrics, Prometheus, PromQL | hands-on | Phase 2 | Not started |
| 6 | OpenTelemetry: context propagation, OTLP, the Collector | hands-on | Phase 2 | Not started |
| 7 | Loki, Tempo, Grafana | hands-on | Phase 2 | Not started |
| 8 | Kubernetes lab track: pods, Deployments, Services, config, probes, storage, rollouts | hands-on | Starts with Phase 2; integrated at Phase 7 | Not started |
| 9 | Alert rules, Alertmanager, webhooks | hands-on | Phase 3 | Not started |
| 10 | Incident model: idempotency, state machines, job queues | operate and debug | Phase 3 | Not started |
| 11 | LLM tool calling, LangGraph, agent evaluation, prompt injection | operate and debug | Phase 4 | Not started |
| 12 | Anomaly detection, log clustering, MLflow | operate and debug | Phase 5 | Not started |
| 13 | CI/CD, registries, Terraform, cloud networking, DNS and TLS | hands-on | Phase 8 | Not started |
| 14 | Load testing and fault injection | hands-on | Phase 1 in small doses; Phase 9 in full | Not started |

## Entries

### 2026-10-11 — System architecture overview

- **Status:** Introduced
- **Why we needed it:** Phase 0; every later task is a piece of this picture.
- **Concepts explained:** The demo shop as a monitored target; pull-based
  metrics scraping versus pushed traces and logs; alert rule → Alertmanager →
  webhook → incident → investigation; read-only investigation tools.
- **Implementation references:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Problems encountered:** None yet.
- **What remains unclear:** Unknown until the owner explains the failure path
  back (task P0-5).
- **Related technologies:** Prometheus, Alertmanager, OpenTelemetry, LangGraph.
- **Recommended next exercise:** P0-5 — describe, without notes, what happens
  between a fault being injected and a finding appearing on the dashboard,
  naming who opens each connection.

### 2026-10-11 — Linux memory accounting, cgroups and the OOM killer

- **Status:** Introduced. The exercise is assigned and not yet done.
- **Why we needed it:** RAM is this project's tightest constraint, and "the
  container vanished with no error" is among the most common real incidents.
- **Concepts explained:** A container is an ordinary process in a cgroup;
  `--memory` writes a limit into that cgroup; exceeding it brings SIGKILL from
  the kernel, which a process cannot catch; `free` versus `available`;
  pressure stall information.
- **Important commands:** `free -h`, `cat /proc/pressure/memory`,
  `docker stats --no-stream`, `docker run --memory --memory-swap`,
  `docker inspect`, `journalctl -k`.
- **Practical exercises:** EXP-001 in [EXPERIMENTS.md](EXPERIMENTS.md).
- **Problems encountered:** None yet.
- **What remains unclear:** To be judged from the owner's evidence and answers.
- **Related technologies:** Compose memory limits (Phase 1); Kubernetes
  resource requests and limits, where the same event is reported as
  `OOMKilled` (lab track).
- **Recommended next exercise:** The stretch task in EXP-001: find a running
  container's cgroup directory and read `memory.max` and `memory.events`.

### 2026-10-12 — How a package install is wired: index, mirrors, partial upgrades

- **Status:** Practiced. The owner ran the full upgrade to completion on
  2026-10-12, on the third attempt (evidence: `/var/log/pacman.log`, in
  DBG-001) and restarted the machine afterwards. The diagnosis was the
  agent's.
- **Why we needed it:** Installing Buildx failed with 404 from every mirror
  ([DBG-001](INCIDENTS_AND_DEBUGGING.md)).
- **Concepts explained:** pacman reads a local copy of the repository index,
  builds a file name from it and fetches that file from a mirror; mirrors keep
  only the current build; a stale index therefore produces 404s; why `-Sy`
  without `-u` is a partial upgrade; a transaction downloads everything before
  changing anything; why a kernel upgrade needs a reboot before new kernel
  modules can load.
- **Important commands:** `pacman -Syu`, `pacman -Si`, `pacman -Q`,
  `/var/log/pacman.log`, `ls -l /var/lib/pacman/sync/`.
- **Problems encountered:** DBG-001.
- **What remains unclear:** To be judged once the owner has run the fix and
  explained the 404 in their own words.
- **Related technologies:** The same shape returns with container images: a
  tag is a name in an index, a registry holds the content, and a stale or
  moved tag gives "manifest unknown". Topic 2 in the roadmap.
- **Recommended next exercise:** After the upgrade, find in
  `/var/log/pacman.log` the line where `docker-buildx` was installed and the
  line where `linux` was upgraded.

### 2026-10-12 — Docker images, layers and the build cache

- **Status:** Practiced. On 2026-10-12 and 2026-10-13 the owner wrote
  `services/shop/Dockerfile` and `.dockerignore` and built the image from
  VS Code, one instruction at a time. The agent named each instruction and
  checked each result, so this is guided practice, not independent work.
- **Why we needed it:** Phase 1; the shop has to become an image before it
  can run in Compose or Kubernetes.
- **Concepts explained:** image = layers + config + manifest; tag versus
  digest; which instructions create layers; why a deleted file still occupies
  the image; how the cache decides to reuse a step and why instruction order
  sets rebuild time; the build context; who dials whom during a build.
- **Important commands:** `docker build`, `docker history`,
  `docker image inspect`, `docker image ls`, `docker run --rm`,
  `docker image rm`, `docker builder prune`, `docker buildx du`.
- **Implementation references:**
  [TECHNOLOGY_GUIDES/docker-images.md](TECHNOLOGY_GUIDES/docker-images.md)
- **Practical exercises:** Part 1, read `python:3.14-slim`. Part 2, write
  `services/shop/Dockerfile` to requirements R1–R8 and run the seven checks.
  Both done; results are in the guide.
- **Problems encountered:** A build tagged `sentinelops/shops:dev` by
  mistake, which made `docker run` ask Docker Hub for a repository that does
  not exist; fixed by retagging. The inspect output has no `User` key for an
  image that runs as root, which the agent's instructions had not allowed
  for.
- **What remains unclear:** Three things, from what was observed. Images
  and containers were mixed up at the start of part 1. In the cache
  experiment the owner ran the builds but did not read which steps were
  cached; the agent read that from the build logs and explained it. The
  knowledge check has not been answered, so the status stops at Practiced.
- **Related technologies:** Compose builds and runs these images (topic 3);
  kind and Kubernetes pull them by tag or digest (topic 8); registries and
  the pipeline push them (topic 13).
- **Recommended next exercise:** Repeat check 6 alone: change one source
  line, rebuild, and say from the terminal output which steps ran and why.
  Then the guide's five knowledge-check questions.

### 2026-10-13 — Docker networking and Compose

- **Status:** Introduced. The exercise is assigned and not yet done.
- **Why we needed it:** The image runs one program. The shop is four
  services and a database that have to find each other.
- **Concepts explained:** one network namespace per container, so
  `localhost` is the container itself; a bridge network as a virtual switch;
  name lookups by service name on a network you create; publishing a port
  and what the address on the left side controls; Compose as a client of
  the Docker Engine that makes reality match a file; volumes; keeping a
  password out of a committed file with `.env`.
- **Important commands:** `docker compose config`, `up -d`, `ps`, `logs`,
  `exec`, `down`; `docker network ls`, `docker network inspect`;
  `ss -ltn`.
- **Implementation references:**
  [TECHNOLOGY_GUIDES/docker-networking-and-compose.md](TECHNOLOGY_GUIDES/docker-networking-and-compose.md)
- **Practical exercises:** Write `compose.yaml` to requirements C1–C7 and
  run the nine checks.
- **Problems encountered:** None yet.
- **What remains unclear:** To be judged from the owner's Compose file, the
  check results and the knowledge-check answers.
- **Related technologies:** Kubernetes Services and cluster DNS do the same
  job as Compose service names (topic 8); Prometheus will reach its scrape
  targets by these names (topic 5).
- **Recommended next exercise:** Check 4 in the guide: resolve one service's
  name from inside another container and find that address in
  `docker network inspect`.
