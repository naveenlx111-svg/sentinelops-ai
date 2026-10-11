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
| 2 | Docker images, layers, build cache, registries | hands-on | Phase 1 | Not started |
| 3 | Docker networking and Compose | hands-on | Phase 1 | Not started |
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
