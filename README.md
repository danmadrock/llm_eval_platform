# LLM Evaluation Platform

A production-oriented platform concept for evaluating Large Language Models (LLMs), prompts, and AI pipelines.


## Current Repository Status

This repository currently contains:

- a comprehensive **system design and architecture documentation set**;
- implemented Phase 1 CRUD APIs for core metadata;
- an implemented Phase 2 vertical slice proving asynchronous evaluation from run orchestration through persisted results;

The platform is now in an **early vertical-slice implementation stage**.


## Vision

Build an inspiring, production-grade evaluation platform where teams can:

- run reproducible evaluations across prompts, models, and datasets;
- compare quality, latency, and cost trade-offs;
- detect regressions before shipping LLM changes;
- evolve toward automated, continuous evaluation in CI/CD;

---

## Documentation Map

Core design docs:

- `docs/architecture.md` - system architecture and principles;
- `docs/data_model.md` - entities and relational model;
- `docs/evaluation_engine.md` - evaluation execution internals;
- `docs/run_lifecycle.md` — run state machine and orchestration;
- `docs/api.md` — target API specification;

Planning and execution docs (added for implementation readiness):

- `docs/repository_assessment.md` — gap analysis of current repo vs target platform
- `docs/implementation_plan.md` — structured phased build plan with milestones
- `docs/development.md` — engineering process, standards, and Definition of Done
- `docs/templates/experiment_design_template.md` — reusable experiment brief template
- `docs/templates/metric_spec_template.md` — reusable metric design template

---

## Proposed Build Sequence

1. Platform foundation (configuration, app bootstrap, DB session handling)
2. Core domain model + migrations
3. API endpoints + validation
4. Orchestration and worker loop
5. Evaluation engine and model gateway
6. Metrics + aggregation + observability
7. Testing, benchmarking, and release hardening

For detailed work breakdown, see `docs/implementation_plan.md`.

---

## Running (when implementation is in place)

Target runtime stack:

- API: FastAPI
- DB: PostgreSQL
- Queue: Redis/RQ
- Workers: Python worker processes
- Storage: S3-compatible object storage

Planned start command:

```bash
docker compose up --build
```

---

## Licence

Apache 2.0