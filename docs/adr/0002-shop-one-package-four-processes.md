# ADR-0002: The demo shop is one package run as four processes

- **Status:** Accepted
- **Date:** 2026-10-11
- **Decided by:** Agent, under the delegation in D-002; open to the owner's
  review

## Problem

The demo shop needs several services that talk over a network, fail
independently and can be traced across hops. How should their code and
packaging be organised?

## Context

- The owner's learning focus is containers, networking and operations, not
  application code (D-002).
- The development machine is short on RAM and disk: 86% of the disk was in
  use on 2026-10-11.
- The four services share the same framework and most of their dependencies.

## Alternatives

| Option | For | Against |
|---|---|---|
| Four projects, four dependency sets, four images | Closest to independently released microservices | Four lockfiles and four near-identical build files; a shared library becomes a build-context problem; four times the image storage |
| **One package, one lockfile, started four ways** | One build to understand deeply; small disk footprint; still four processes with four network identities and four failure modes | Services cannot pin different dependency versions or be released separately |
| One process serving every route | Simplest | Nothing to connect, trace or fail independently; defeats the purpose |

## Decision

One Python package, `shop`, with a sub-package per service and a `common`
sub-package. Each service is started as its own process with
`uvicorn shop.<service>.app:create_app --factory` and configured only through
environment variables.

## Consequences

- One image can serve all four services, selected by the start command. The
  same pattern is used by tools this project adopts later, which run one
  binary in different roles.
- Table ownership and "talk through the API, not the database" are
  conventions enforced by review, not by separate credentials.
- Splitting a service into its own project later is a contained change: move
  its sub-package and copy what it uses from `common`.

## Risks

- Shared code tempts services into sharing more than plumbing. `common` holds
  only configuration, database, HTTP-client and health helpers.

## Revisit when

- A service needs a dependency that conflicts with another's.
- Building a separate image per service becomes a learning goal in itself.
