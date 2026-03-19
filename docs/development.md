# Development Guide

## Purpose

This guide defines how to implement the platform from its architecture docs into a maintainable production codebase.

## Engineering Principles

- **Correctness over speed:** evaluation results must be trustworthy.
- **Reproducibility by default:** all runs must be replayable.
- **Observability first:** no silent failures in async workflows.
- **Incremental delivery:** merge vertical slices that are usable end-to-end.
- **Simple abstractions:** avoid premature complexity.

## Definition of Done (DoD)

A feature is done only when all are true:

1. Domain model and API contract are documented.
2. Migrations are created and reversible.
3. Unit tests pass for logic and validation.
4. Integration tests pass for DB/API boundaries.
5. Logs and metrics are emitted for key execution paths.
6. Failure modes are handled and surfaced.
7. Documentation is updated.

## Suggested Branching and PR Workflow

- Branch naming: `feat/<area>-<short-description>` or `fix/<area>-<short-description>`
- Keep PRs small enough for focused review.
- Each PR should include:
  - problem statement
  - implementation summary
  - risk and rollback notes
  - test evidence

## Testing Strategy

### Test Pyramid

- **Unit tests (majority):** metrics, prompt rendering, status transitions, repositories.
- **Integration tests:** API + DB, worker + queue, storage adapters.
- **End-to-end smoke tests:** run creation through result retrieval.

### Minimum CI Gates

- lint (`ruff`, `black --check`)
- type checks (`mypy` on core/service layers)
- tests (`pytest -q`)
- migration check (`alembic upgrade head` in ephemeral DB)

## Reliability and Operations Checklist

- Idempotent task execution for worker retries.
- Dead-letter strategy for poison tasks.
- Timeouts and retries on provider calls.
- Structured logging with correlation IDs (`run_id`, `task_id`).
- Metrics for throughput, failure rate, latency, and queue depth.

## Security Checklist

- Keep provider/API keys in environment or secret manager.
- Validate and size-limit dataset uploads.
- Sanitize and redact sensitive inputs from logs.
- Enforce authn/authz before multi-tenant rollout.

## Documentation Discipline

When behavior changes, update the relevant docs in the same PR:

- API behavior → `docs/api.md`
- run states/orchestration → `docs/run_lifecycle.md`
- engine behavior/metrics → `docs/evaluation_engine.md`
- schema changes → `docs/data_model.md`