# ADR-0001: Docker Compose first, with a standalone Kubernetes lab track

- **Status:** Accepted
- **Date:** 2026-10-11
- **Decided by:** Owner, on the agent's recommendation

## Problem

Kubernetes is the owner's highest-priority learning goal, but the phase plan
places it at Phase 7. Meeting it for the first time after six phases of other
work compresses the most important topic into one block, and Phase 6
remediation would be written against Compose and then reworked.

## Context

- The development machine has 16 GB of RAM, with about 6 GiB available during
  normal desktop use. A kind cluster and the full Compose stack cannot run
  together.
- Kubernetes is easier to learn once container networking, health checks and
  metrics are familiar, because it builds on all three.
- Phase gates forbid building later-phase components early.

## Alternatives

| Option | For | Against |
|---|---|---|
| Kubernetes strictly at Phase 7 | Simple plan, full attention when it arrives | First contact comes late; no spaced practice; remediation reworked |
| Kubernetes from Phase 1, no Compose | Earliest exposure | Everything is debugged through an unfamiliar platform at once; heavier on RAM |
| **Compose for the product, plus a standalone kind lab track from Phase 2** | Months of spaced practice; Phase 7 becomes integration, not introduction | Some hours diverted from each phase; lab and stack run at different times |

## Decision

The product runs on Docker Compose through Phase 6. From Phase 2 the owner
works through a separate series of Kubernetes exercises on a local kind
cluster. The lab deploys practice workloads only; nothing in SentinelOps
depends on it, so no phase gate is crossed. SentinelOps moves onto Kubernetes
in Phase 7.

## Consequences

- Compose files stay the source of truth for how the stack runs until Phase 7.
- The lab needs its own exercise list and journal entries.
- The remediation executor in Phase 6 is written behind an interface so a
  Kubernetes implementation can be added without changing callers.

## Risks

- The lab track gets skipped under time pressure. It is tracked in
  PROGRESS.md like any other task.
- kind is installed from the Arch `extra` repository; whether `kind load`
  works with this machine's containerd image store is unverified.

## Revisit when

- The owner wants to move the product to Kubernetes earlier.
- RAM proves too tight even for the lab alone.
