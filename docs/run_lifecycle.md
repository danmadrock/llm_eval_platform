# LLM Evaluation Platform — Run Lifecycle

## Overview

This document defines the lifecycle of **evaluation runs** within the LLM Evaluation Platform.

A **run** represents a single execution of an evaluation configuration:

- dataset version
- prompt version
- model configuration
- metric set

Runs are executed asynchronously using distributed workers and task queues.

The run lifecycle ensures:

- reproducibility
- reliable distributed execution
- fault tolerance
- observability

---

# Run Definition

A run is created when a user requests evaluation of a specific configuration.

Example run configuration:

```
dataset_version = support_qa_v1
prompt_version = support_prompt_v3
model = gpt-4
metrics = [exact_match, semantic_similarity]
```

Each run is uniquely identified by a `run_id`.

---

# Run State Machine

Runs move through a series of states.

```
created → queued → running → completed
                     ↓
                    failed
```

## created

Run has been registered but not yet scheduled.

## queued

Evaluation tasks have been scheduled and placed in the task queue.

## running

Workers are actively processing evaluation tasks.

## completed

All evaluation tasks finished successfully.

## failed

Run failed due to a fatal error.

---

# Run Execution Phases

Run execution occurs in several phases.

```
Run Creation
     │
     ▼
Dataset Preparation
     │
     ▼
Task Generation
     │
     ▼
Task Scheduling
     │
     ▼
Worker Execution
     │
     ▼
Result Aggregation
     │
     ▼
Run Completion
```

---

# Phase 1 — Run Creation

The run is created through the API.

The system records:

- dataset_version_id
- prompt_version_id
- model_config_id
- metric_set
- example_count

Initial state:

```
status = created
```

---

# Phase 2 — Dataset Preparation

The orchestrator retrieves dataset metadata.

Steps:

1. fetch dataset version metadata
2. determine example count
3. validate dataset availability
4. validate prompt configuration

If validation fails, the run transitions to:

```
status = failed
```

---

# Phase 3 — Task Generation

The dataset is partitioned into evaluation tasks.

Each dataset example becomes one task.

Example task:

```
{
  run_id: "...",
  example_index: 42,
  input: {...},
  expected_output: "...",
}
```

Tasks are generated in memory and pushed to the task queue.

---

# Phase 4 — Task Scheduling

Evaluation tasks are placed into the task queue.

Queue responsibilities:

- load balancing across workers
- reliable task delivery
- retry scheduling

Redis is used as the queue backend.

The run state transitions to:

```
status = queued
```

---

# Phase 5 — Worker Execution

Workers consume tasks from the queue.

For each task:

```
worker → evaluation_engine.execute(task)
```

Evaluation steps:

1. render prompt
2. call model through model gateway
3. compute metrics
4. collect metadata
5. return structured result

Results are written to the database.

---

# Phase 6 — Result Aggregation

The orchestrator periodically aggregates results.

Aggregated metrics include:

- mean metric scores
- latency distribution
- total cost
- success rate

These metrics are stored in `run_metrics`.

---

# Phase 7 — Run Completion

The run is marked complete when:

```
processed_examples == total_examples
```

Run state:

```
status = completed
```

Completion metadata:

```
completed_at
duration
aggregate metrics
```

---

# Failure Handling

Failures may occur during evaluation.

Examples:

- model API failure
- network timeout
- invalid response
- metric execution failure

Failures are handled at two levels.

---

## Task-Level Failures

Individual task failures are retried.

Retry strategy:

```
max_retries = configurable
retry_backoff = exponential
```

Failed tasks after retries are recorded as failed results.

---

## Run-Level Failures

Run-level failures occur when:

- dataset cannot be loaded
- model configuration invalid
- system infrastructure failure

The run transitions to:

```
status = failed
```

---

# Idempotent Execution

Tasks must be idempotent.

If a worker crashes, the task can be safely re-executed.

This prevents duplicate or inconsistent results.

Task identity:

```
(run_id, example_index)
```

Duplicate results overwrite previous attempts.

---

# Progress Tracking

Run progress is tracked using:

```
completed_examples
total_examples
```

Progress metric:

```
progress = completed_examples / total_examples
```

This enables real-time monitoring of evaluation runs.

---

# Observability

The system tracks several operational signals.

## Run Metrics

- run duration
- evaluation throughput
- failure rate

## Worker Metrics

- tasks processed
- average inference latency
- retry rate

## Model Metrics

- token usage
- cost
- response latency

These metrics allow system monitoring and debugging.

---

# Cancellation

Users may cancel running evaluations.

Cancellation steps:

1. mark run as `cancelled`
2. stop scheduling new tasks
3. workers skip remaining tasks

This prevents unnecessary compute usage.

---

# Partial Results

Runs may complete with partial results if some tasks fail.

Example:

```
success_rate = 98%
```

Aggregated metrics should include success rates.

---

# Large Run Handling

Large evaluation runs may contain tens of thousands of tasks.

Strategies for large runs:

- dataset streaming
- distributed worker pools
- task batching
- result partitioning

This ensures the system scales with dataset size.

---

# Deterministic Reproduction

Each run stores all configuration required for reproduction.

Reproducible fields:

- dataset_version_id
- prompt_version_id
- model_config_id
- metric definitions

This ensures historical runs can be reproduced.

---

# Future Extensions

Future improvements may include:

- distributed orchestrators
- priority scheduling
- run comparison pipelines
- automated regression detection
- experiment pipelines

---

# Summary

The run lifecycle defines how evaluation runs are executed and managed.

Key characteristics:

- deterministic execution
- distributed worker processing
- reliable task retries
- scalable evaluation architecture
- reproducible experiments

The run lifecycle ensures evaluation experiments remain reliable and scalable as the system grows.