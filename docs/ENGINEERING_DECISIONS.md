# Engineering decisions

A running log. Major decisions get a full record under [adr/](adr/) and a
one-line entry here. Decisions are never rewritten; a new entry supersedes an
old one and says so.

| ID | Date | Decision | Status |
|---|---|---|---|
| D-001 | 2026-10-11 | The first usable version is one vertical slice across Phases 0–4 | Accepted |
| D-002 | 2026-10-11 | Owner does containers, tooling and connections; agent does application code | Accepted |
| D-003 | 2026-10-11 | Compose first, standalone Kubernetes lab from Phase 2 — [ADR-0001](adr/0001-compose-first-kubernetes-lab-track.md) | Accepted |
| D-004 | 2026-10-11 | One repository, phase branches merged into `main` on approval | Accepted |

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
