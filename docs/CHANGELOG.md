# Changelog

Meaningful changes, newest first. Git history has the detail.

## 2026-10-12

### Added

- Debugging log, opened with DBG-001: a package install that failed with
  404 from every mirror because the local package index was stale.
- The repository is on GitHub: `main` and `phase-1/shop-services` pushed.

## 2026-10-11

### Added

- Demo shop application in `services/shop/`: gateway, users, catalog and
  checkout services, the database schema and seed data, a test suite and an
  end-to-end smoke script. Runs as local processes; not yet containerized.
- Project map with the connection contract between the services.
- Decisions D-005 to D-010 and ADR-0002.
- Experiment EXP-002: memory footprint of the shop processes.
- Phase 0 documentation set: working agreement, architecture, decision log,
  progress tracker, learning journal, experiments.
