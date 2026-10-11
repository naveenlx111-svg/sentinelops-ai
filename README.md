# SentinelOps AI

An AI-assisted Site Reliability Engineering platform: it watches a running
system, turns alerts into durable incident records, and investigates each
incident to produce ranked root-cause hypotheses backed by telemetry a human
can re-check.

This is also a learning project. See
[docs/WORKING_AGREEMENT.md](docs/WORKING_AGREEMENT.md) for how the work is
split and why.

## Problem

When a system of several services fails, an engineer has to correlate
metrics, logs, traces, recent deployments and past incidents by hand. That is
slow, repetitive and hardest at exactly the moment it matters. SentinelOps
does the correlation and shows its evidence.

## Status

**Phase 1 — building the application to monitor.** The demo shop's code is
written and verified as local processes; containerizing it is the current
work. The live task list is [docs/PROGRESS.md](docs/PROGRESS.md).

### Implemented

- **Demo shop application** (`services/shop/`): gateway, users, catalog and
  checkout services over one PostgreSQL database, with explicit failure
  handling between services, liveness and readiness endpoints, JSON logs, a
  test suite and an end-to-end smoke script.

Not implemented: containers, observability, alerting, incidents,
investigation. Nothing of SentinelOps itself exists yet.

### Planned

| Phase | Capability |
|---|---|
| 1 | Containerizing the demo shop (its code is implemented) |
| 2 | Metrics, logs and traces flowing into Prometheus, Loki, Tempo and Grafana |
| 3 | Alerts become deduplicated incidents with a lifecycle and timeline |
| 4 | An incident launches an AI investigation with evidence-backed findings |
| 5 | Anomaly detection, log clustering, incident classification |
| 6 | Approved, audited remediation runbooks |
| 7 | Kubernetes deployment (a standalone practice track starts at Phase 2) |
| 8 | CI/CD and a cloud staging environment |
| 9 | Fault injection with measured detection and diagnosis |
| 10 | Hardening and pilot users |

The first usable version is Phases 0–4: inject a known fault, and within
minutes an incident exists with an investigation naming the faulty service
and citing the queries that support it.

## Architecture

One demo application emits telemetry; Prometheus, Loki and Tempo store it;
Alertmanager turns firing rules into webhooks; the SentinelOps backend turns
webhooks into incidents and runs investigations that query the telemetry
stores read-only. Diagrams and the full request path are in
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Technology stack

| Area | Choices |
|---|---|
| Backend | Python, FastAPI, Pydantic, SQLAlchemy, PostgreSQL, Redis |
| Agents | LangGraph, LLM tool calling with structured outputs |
| ML | NumPy, pandas, scikit-learn, MLflow; PyTorch only when justified |
| Observability | OpenTelemetry, Prometheus, Alertmanager, Grafana, Loki, Tempo |
| Infrastructure | Docker, Docker Compose, Kubernetes (kind locally), Terraform, GitHub Actions |
| Frontend | React, TypeScript, Tailwind CSS |
| Testing | pytest, Playwright, k6 |

Each tool is adopted in the phase that needs it, not before.

## Prerequisites

- Linux with Docker Engine, plus the Compose and Buildx plugins
- [uv](https://docs.astral.sh/uv/) for Python environments
- git

Development happens on Arch Linux with 16 GB of RAM, so the full stack is
never assumed to run at once.

## Quickstart

There is no one-command start yet; that arrives with the container stack.
Until then the shop runs as four processes, as described under Development.

## Development

All commands run from `services/shop/`.

```bash
uv sync                      # create .venv and install the locked dependencies
uv run ruff format .         # format
uv run ruff check .          # lint
```

Start one service (each needs its environment variables; the full list is the
connection contract in [docs/PROJECT_MAP.md](docs/PROJECT_MAP.md)):

```bash
DATABASE_URL='postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE' \
  uv run uvicorn shop.users.app:create_app --factory --port 8001
```

The database must already contain the tables from `db/init/`.

## Testing

```bash
uv run pytest                # tests that need no database; the rest are skipped

TEST_DATABASE_URL='postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE' \
  uv run pytest              # everything; drops and recreates the shop tables
```

Point `TEST_DATABASE_URL` only at a database you can afford to wipe.

```bash
scripts/smoke.sh http://localhost:8000    # end-to-end, against a running gateway
```

Last verified 2026-10-11: 32 tests passed against PostgreSQL 18, and the
smoke test passed 8 of 8 against four running processes.

## Repository conventions

- **Layout:** `services/shop/` for the demo application, `docs/` for
  everything here, and `sentinelops/` for the platform once it exists.
- **Branches:** `main` holds approved work. Phase work happens on
  `phase-N/<topic>` and merges at the owner's approval.
- **Commits:** a short type prefix — `feat:`, `fix:`, `docs:`, `test:`,
  `infra:`, `chore:` — then what changed and why.
- **Docs change with the code they describe**, in the same commit.

## Documentation

| Document | Purpose |
|---|---|
| [WORKING_AGREEMENT](docs/WORKING_AGREEMENT.md) | Roles, task labels, phases, rules |
| [ARCHITECTURE](docs/ARCHITECTURE.md) | Components, connections, diagrams, risks |
| [PROJECT_MAP](docs/PROJECT_MAP.md) | Where everything is; the connection contract between services |
| [PROGRESS](docs/PROGRESS.md) | Current phase, tasks, blockers, next steps |
| [ENGINEERING_DECISIONS](docs/ENGINEERING_DECISIONS.md) | Decision log; major ones in [adr/](docs/adr/) |
| [LEARNING_JOURNAL](docs/LEARNING_JOURNAL.md) | What has been introduced, practiced and demonstrated |
| [EXPERIMENTS](docs/EXPERIMENTS.md) | Experiments and measured results |
| [CHANGELOG](docs/CHANGELOG.md) | Meaningful changes by date |

More documents are added when they have real content: an operations guide
with the first running stack, a debugging log with the first real failure,
and one technology guide per tool as it is introduced.

## Known limitations

- The shop is not containerized and has only been run on one machine.
- The shop has no authentication, no retries and no idempotent orders; the
  full list is in [docs/PROJECT_MAP.md](docs/PROJECT_MAP.md).
- Everything beyond the shop is a proposal until it is built and verified.
