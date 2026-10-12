# Progress

The operational source of truth. Updated at the end of every working session.

## Now

- **Phase:** 0 closing, 1 started
- **Last updated:** 2026-10-12
- **Milestone:** a containerized shop that passes the smoke test
- **State:** the shop's application code is written and verified as local
  processes on branch `phase-1/shop-services`. It is not on `main` and not
  containerized. The next work is the owner's.

The owner said "start" on 2026-10-11 and delegated all application code
(D-002). The agent took that as the go-ahead to write the shop, because the
owner's container work needs an application to build. It sits on a branch so
that `main` holds only what has been explicitly approved.

## Blockers

| Blocker | Owner | Unblocks |
|---|---|---|
| `docker buildx` is not installed. The first install attempt failed on a stale package index ([DBG-001](INCIDENTS_AND_DEBUGGING.md)); the fix is a full system upgrade and a reboot | Owner | Building the shop image |
| `docker compose` is unavailable until the same fix, because the hand-installed plugin was moved aside before its replacement arrived | Owner | Running the stack; the owner's other project's Compose commands |

## Phase 0 tasks

| ID | Task | Label | Status |
|---|---|---|---|
| P0-1 | Memory baseline and the container OOM lab ([EXP-001](EXPERIMENTS.md)) | ME — OPERATIONS | **Open** |
| P0-2a | Rename branch to `main` | AGENT IMPLEMENTATION | Done |
| P0-2b | Install `docker-buildx`; replace the hand-installed Compose binary with the packaged one | ME — OPERATIONS | **Open** — two attempts on 2026-10-12: the first failed on a stale package index, the second was cut short by a restart before anything was installed ([DBG-001](INCIDENTS_AND_DEBUGGING.md)) |
| P0-3 | Working agreement in the repository | AGENT IMPLEMENTATION | Done |
| P0-4 | First usable version defined (D-001) | PAIR PROGRAMMING | Done — approved 2026-10-11 |
| P0-5 | Owner explains the seven-step failure path back in their own words | ME — MANUAL | **Open** |
| P0-6 | Decisions recorded (D-001 to D-004, ADR-0001) | AGENT IMPLEMENTATION | Done |
| P0-7 | Initial documents | AGENT IMPLEMENTATION | Done — owner review pending |
| P0-8 | Risk register (in [ARCHITECTURE.md](ARCHITECTURE.md)) | AGENT IMPLEMENTATION | Done — owner review pending |
| P0-9 | Repository conventions (in the [README](../README.md)) | AGENT IMPLEMENTATION | Done |
| P0-10 | Create the GitHub repository and connect it as `origin` | ME — OPERATIONS | Done — 2026-10-12: the owner created the repository and registered the SSH key; `main` and `phase-1/shop-services` are pushed |
| P0-11 | Phase 0 gate review | AGENT REVIEW | Waiting on the open tasks |

## Phase 1 tasks

| ID | Task | Label | Depends on | Status |
|---|---|---|---|---|
| P1-1 | Shop services, schema, tests, smoke script | AGENT IMPLEMENTATION | — | Done on the branch; owner approval to merge pending |
| P1-2 | Lesson: images, layers, build cache; then write the shop's Dockerfile and build the image | ME — OPERATIONS | P0-2b | Next |
| P1-3 | Lesson: container networking and Compose; then write the Compose file for PostgreSQL and the four services | ME — OPERATIONS | P1-2 | Not started |
| P1-4 | Initialise the database inside the stack from `db/init/` | ME — OPERATIONS | P1-3 | Not started |
| P1-5 | Health checks, start-up ordering and memory limits in Compose | ME — OPERATIONS | P1-3 | Not started |
| P1-6 | Run `scripts/smoke.sh` against the composed stack; review of the result | ME — OPERATIONS, then AGENT REVIEW | P1-4 | Not started |
| P1-7 | Debugging exercises on the running stack | ME — OPERATIONS | P1-6 | Not started |
| P1-8 | Technology guides for Docker images and Docker networking, written alongside the lessons | AGENT IMPLEMENTATION | P1-2, P1-3 | Not started |
| P1-9 | Fault scripts that record ground truth | AGENT IMPLEMENTATION | P1-6 | Not started |
| P1-10 | Operations guide with the procedures the owner has verified | AGENT IMPLEMENTATION | P1-6 | Not started |
| P1-11 | Phase 1 gate review | AGENT REVIEW | all | Not started |

## Verified deliverables

| Deliverable | Evidence |
|---|---|
| Approved architecture and plan | Owner approval on 2026-10-11; [ARCHITECTURE.md](ARCHITECTURE.md), D-001 |
| Shop application code | 2026-10-11: 32 tests passed against PostgreSQL 18; smoke test 8 of 8 through the gateway with four real processes; failure behaviour in [PROJECT_MAP.md](PROJECT_MAP.md) |

## Pending tests

- The shop has not been run in containers. Everything about container
  networking, image contents and start-up order is unverified.
- Timeout behaviour (504) is covered by unit tests only; it has not been
  observed with a really slow service.

## Next priorities

1. Owner: P0-2b first — the full system upgrade and reboot from DBG-001.
   Then P0-1 (OOM lab).
2. Owner: say whether `phase-1/shop-services` may merge into `main`.
3. Agent, then owner: P1-2, the Dockerfile lesson and build.

## Links

- Decisions: [ENGINEERING_DECISIONS.md](ENGINEERING_DECISIONS.md)
- Learning status: [LEARNING_JOURNAL.md](LEARNING_JOURNAL.md)
- What the application expects from its environment: [PROJECT_MAP.md](PROJECT_MAP.md)
