# Engineering decisions

A running log. Major decisions get a full record under [adr/](adr/) and a
one-line entry here. D-005 to D-010 were made by the agent under the
delegation in D-002 and are open to the owner's review. Decisions are never rewritten; a new entry supersedes an
old one and says so.

| ID | Date | Decision | Status |
|---|---|---|---|
| D-001 | 2026-10-11 | The first usable version is one vertical slice across Phases 0–4 | Accepted |
| D-002 | 2026-10-11 | Owner does containers, tooling and connections; agent does application code | Accepted |
| D-003 | 2026-10-11 | Compose first, standalone Kubernetes lab from Phase 2 — [ADR-0001](adr/0001-compose-first-kubernetes-lab-track.md) | Accepted |
| D-004 | 2026-10-11 | One repository, phase branches merged into `main` on approval | Accepted |
| D-005 | 2026-10-11 | Shop is one package run as four processes — [ADR-0002](adr/0002-shop-one-package-four-processes.md) | Accepted |
| D-006 | 2026-10-11 | Python 3.14 with uv and a committed lockfile | Accepted |
| D-007 | 2026-10-11 | Shop schema comes from SQL files, not a migration tool | Accepted |
| D-008 | 2026-10-11 | Synchronous request handlers in the shop | Accepted |
| D-009 | 2026-10-11 | No default addresses; fail fast on missing configuration | Accepted |
| D-010 | 2026-10-11 | Stay on httpx for now despite the test-client deprecation warning | Accepted |

---

## D-001: First usable version is one vertical slice

- **Problem:** The full vision has ten phases. Without a narrow first target
  the project produces infrastructure and no product.
- **Context:** One developer, one laptop, no existing users.
- **Alternatives:** (a) build each layer fully before the next; (b) one thin
  slice through every layer up to investigation.
- **Trade-offs:** (a) gives polished layers but delays any end-to-end result
  for months. (b) gives a working, measurable product early, with every layer
  shallow at first.
- **Choice:** (b). "Inject a known fault into the demo shop; within minutes an
  incident exists with an investigation naming the faulty service and citing
  the metric queries and log lines that support it."
- **Reasoning:** An end-to-end path exposes integration problems that
  layer-by-layer work hides, and it is the only thing that can be evaluated
  against ground truth.
- **Consequences:** ML, remediation, Kubernetes integration, cloud, CI/CD and
  multi-tenancy all wait. Kubernetes practice continues separately (D-003).
- **Risks:** Shallow layers may need rework when deepened.
- **Revisit when:** The slice works and has baseline measurements.

## D-002: Ownership split

- **Problem:** The owner wants deep, hands-on skill with containers,
  observability tooling, Kubernetes and the connections between components,
  and does not want time spent writing application code.
- **Context:** The original plan had the owner writing most backend, agent and
  ML code. Amended by the owner on 2026-10-11.
- **Alternatives:** (a) owner writes application and infrastructure;
  (b) owner writes infrastructure only; (c) agent writes everything.
- **Trade-offs:** (a) is the broadest learning and the slowest. (b) focuses
  effort where the owner wants depth, at the cost of knowing the application
  code less well. (c) teaches nothing.
- **Choice:** (b). Details in [WORKING_AGREEMENT.md](WORKING_AGREEMENT.md).
- **Reasoning:** The owner's stated priority; operations skill comes from
  doing the operations.
- **Consequences:** The agent must document the application's interfaces —
  ports, endpoints, environment variables, failure behaviour — well enough
  that the owner can wire and debug it without reading every line.
- **Risks:** Debugging across the application boundary is harder when you did
  not write the application. The project map exists to offset that.
- **Revisit when:** Any phase gate; the owner can reclaim any task.

## D-004: One repository, phase branches

- **Problem:** Where code lives and how changes reach the main line.
- **Context:** One developer. CI and pull-request review arrive in Phase 8.
- **Alternatives:** (a) a repository per service; (b) one repository,
  everything committed to `main`; (c) one repository, phase work on branches.
- **Trade-offs:** (a) mirrors large organizations but multiplies setup for no
  gain here. (b) is simplest but leaves no checkpoint between approved and
  unapproved work. (c) costs one merge per phase topic.
- **Choice:** (c). `main` holds approved work; `phase-N/<topic>` branches
  carry work awaiting approval.
- **Reasoning:** The branch is the phase gate made concrete: unapproved work
  is visible but not merged.
- **Consequences:** Layout is `services/shop/`, `sentinelops/`, `docs/`.
- **Risks:** Long-lived branches drift. Branches stay small and merge quickly.
- **Revisit when:** CI is introduced in Phase 8.

## D-005: Shop is one package run as four processes

Full record: [ADR-0002](adr/0002-shop-one-package-four-processes.md).

## D-006: Python 3.14 with uv and a committed lockfile

- **Problem:** Which interpreter and how dependencies are installed.
- **Context:** Arch's system Python is externally managed, so nothing may be
  installed into it with pip. uv 0.12.17 was already present.
- **Alternatives:** (a) pip and venv with a requirements file; (b) Poetry;
  (c) uv with `pyproject.toml` and `uv.lock`.
- **Trade-offs:** (a) has no lockfile by default. (b) is another tool to
  install. (c) resolves and installs fast, pins every transitive version, and
  can install a pinned interpreter by itself.
- **Choice:** (c), on Python 3.14.
- **Reasoning:** A lockfile makes a container build install exactly what the
  tests ran against. 3.14 is the system interpreter and matches a
  `python:3.14-slim` image already on the machine. All six runtime
  dependencies resolved and installed on 3.14 on 2026-10-11.
- **Consequences:** Image builds install from `uv.lock`.
- **Risks:** A later dependency (LangGraph, PyTorch, MLflow) may lag on 3.14.
  That is checked when each is introduced; SentinelOps is a separate project
  and can pin a different version.
- **Revisit when:** A needed library does not support 3.14.

## D-007: Shop schema comes from SQL files, not a migration tool

- **Problem:** How the shop's tables and seed rows get created.
- **Context:** The shop's schema is three small tables that are not expected
  to evolve. Alembic is in the stack for the SentinelOps backend, whose schema
  will.
- **Alternatives:** (a) Alembic migrations; (b) the services create their own
  tables at startup; (c) plain SQL files run once against an empty database.
- **Trade-offs:** (a) is the right tool for an evolving schema and overhead
  for a fixed one. (b) hides schema changes inside application startup and
  races when several instances start together. (c) is explicit and visible,
  but offers no path for changing a database that already has data.
- **Choice:** (c), in `services/shop/db/init/`.
- **Reasoning:** Simplest thing that works for a fixed schema, and it keeps
  database initialisation a deliberate operational step rather than a side
  effect.
- **Consequences:** The test suite rebuilds its tables from the same files,
  so a model that drifts from the schema fails a test. Readiness checks that
  each service's table exists.
- **Risks:** Changing the schema later means recreating the database.
- **Revisit when:** The shop's schema needs to change with data in place.

## D-008: Synchronous request handlers in the shop

- **Problem:** Sync or async handlers, database driver and HTTP client.
- **Alternatives:** (a) async throughout; (b) synchronous handlers run on
  FastAPI's thread pool, with synchronous SQLAlchemy and httpx.
- **Trade-offs:** (a) handles more concurrent connections per process and is
  harder to reason about and to debug. (b) is easy to follow and blocks one
  thread per in-flight request.
- **Choice:** (b).
- **Reasoning:** The shop exists to be monitored and broken, not to be fast.
  Thread-per-request also makes resource exhaustion (threads, pooled
  connections) straightforward to provoke and to see, which Phase 9 wants.
- **Consequences:** Throughput is bounded by the thread pool and the
  connection pool.
- **Risks:** None for a demo target.
- **Revisit when:** Load testing needs more than this model can deliver.

## D-009: No default addresses; fail fast on missing configuration

- **Problem:** What a service does when it has not been told where its
  dependencies are.
- **Alternatives:** (a) default to `localhost` addresses; (b) require every
  address and exit at startup naming what is missing.
- **Trade-offs:** (a) is convenient on one machine and fails confusingly
  everywhere else, at request time. (b) fails immediately and specifically.
- **Choice:** (b).
- **Reasoning:** Inside a container `localhost` is the container itself, so a
  localhost default is wrong in exactly the environments that matter. An exit
  at startup with the variable's name is the easiest failure to diagnose.
- **Consequences:** Every deployment must set every address explicitly.
- **Risks:** None identified.
- **Revisit when:** Never expected.

## D-010: Stay on httpx for now

- **Problem:** Starlette's test client warns that using `httpx` is deprecated
  in favour of `httpx2`, a successor package first published in May 2026.
- **Alternatives:** (a) move the application and tests to `httpx2`; (b) add
  `httpx2` for tests only; (c) stay on `httpx` and leave the warning visible.
- **Trade-offs:** (a) follows the framework's direction but adopts a young
  library before confirming that tracing instrumentation exists for it. (b)
  leaves two HTTP client libraries in one project. (c) keeps one known
  library and one deprecation warning in the test output.
- **Choice:** (c).
- **Reasoning:** Phase 2 needs the HTTP client instrumented so trace context
  crosses service boundaries. That choice should be made once, with the
  instrumentation options checked, not as a side effect of silencing a
  warning.
- **Consequences:** The test run prints one `StarletteDeprecationWarning`.
- **Risks:** A future Starlette release may drop `httpx` support in the test
  client.
- **Revisit when:** Phase 2 tracing is designed, or the test client stops
  working with `httpx`.
