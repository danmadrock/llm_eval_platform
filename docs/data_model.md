# LLM Evaluation Platform — Data Model

> **Status note (2026-03):** This document is a target-state design specification. The Python service modules in this repository are currently scaffolds (mostly empty files), so treat this as implementation intent rather than current behavior.

## Overview

This document defines the **database architecture and entity model** for the LLM Evaluation Platform.

The data model is designed to support:
- reproducible evaluation experiments
- scalable evaluation execution
- efficient result storage and querying
- extensibility for future evaluation tasks

The platform uses **PostgreSQL** as the primary metadata and results database. Large artifacts (datasets, logs, raw outputs) are stored in **object storage**.

---

# Design Principles

## 1. Reproducibility

Every evaluation run must be reproducible. This ensures historical experiments can be re-run.

A run records:
- dataset version
- prompt version
- model configuration
- evaluation metrics

---

## 2. Immutable Versions

Datasets and prompts are **versioned**. Versions are immutable once created. This guarantees that evaluation results remain consistent.

---

## 3. Separation of Metadata and Artifacts

Metadata is stored in PostgreSQL. Large artifacts are stored in object storage.

Examples of artifacts:
- dataset files
- raw model responses
- evaluation logs

---

## 4. Efficient Result Storage

Evaluation results are stored per dataset example. Aggregated metrics are also stored per run.

This allows:
- detailed debugging
- error analysis
- metric recomputation

---

# Entity Model

The platform contains the following core entities:
```
Dataset
  └ DatasetVersion
        └ EvaluationExample

Prompt
  └ PromptVersion

ModelConfig

Experiment
  └ Run
        └ EvaluationResult

Metric
RunMetric
```

---

# ER Diagram

```
Dataset
  │
  └── DatasetVersion
         │
         └── EvaluationExample

Prompt
  │
  └── PromptVersion

ModelConfig

Experiment
  │
  └── Run
        │
        ├── EvaluationResult
        │
        └── RunMetric

Metric
```

---

# Table Schema

## datasets

Stores logical datasets.
```
datasets
---------
id (uuid, pk)
name (text)
description (text)
task_type (text)
created_at (timestamp)
```

---

## dataset_versions

Stores immutable versions of datasets. Dataset content is stored in object storage.
```
dataset_versions
----------------
id (uuid, pk)
dataset_id (uuid, fk)
version (int)
object_uri (text)
example_count (int)
created_at (timestamp)
```

Example `object_uri`:
```
s3://datasets/support_qa/v1.jsonl
```

---

## evaluation_examples (optional)

For small datasets we may store examples in DB. Large datasets remain in object storage.
```
evaluation_examples
-------------------
id (uuid, pk)
dataset_version_id (uuid, fk)
input (jsonb)
expected_output (jsonb)
metadata (jsonb)
```

---

## prompts

Logical prompt definitions.
```
prompts
-------
id (uuid, pk)
name (text)
description (text)
created_at (timestamp)
```

---

## prompt_versions

Immutable prompt versions.
```
prompt_versions
---------------
id (uuid, pk)
prompt_id (uuid, fk)
version (int)
template (text)
created_at (timestamp)
```

Example template:
```
You are a helpful assistant.

Question: {question}

Answer:
```

---

## model_configs

Stores model configuration used in runs.
```
model_configs
-------------
id (uuid, pk)
provider (text)
model_name (text)
parameters (jsonb)
created_at (timestamp)
```

Example parameters:
```
{
  "temperature": 0,
  "max_tokens": 512
}
```

---

## experiments

Logical grouping of runs.

Example:

```
"prompt-optimization-support-agent"
```

```
experiments
-----------
id (uuid, pk)
name (text)
description (text)
created_at (timestamp)
```

---

## runs

Represents a concrete evaluation execution.

```
runs
----
id (uuid, pk)
experiment_id (uuid, fk)
dataset_version_id (uuid, fk)
prompt_version_id (uuid, fk)
model_config_id (uuid, fk)

status (text)
example_count (int)

started_at (timestamp)
completed_at (timestamp)

created_at (timestamp)
```

Run status values:
```
created
queued
running
completed
failed
```

---

## metrics

Defines evaluation metrics.

```
metrics
-------
id (uuid, pk)
name (text)
description (text)
metric_type (text)
created_at (timestamp)
```

Examples:
- exact_match
- semantic_similarity
- llm_judge
- latency
- cost

---

## run_metrics

Stores aggregated metric values for a run.

```
run_metrics
-----------
id (uuid, pk)
run_id (uuid, fk)
metric_id (uuid, fk)

value (float)
computed_at (timestamp)
```

Example:

```
accuracy = 0.84
```

---

## evaluation_results

Stores evaluation results for individual examples.

```
evaluation_results
------------------
id (uuid, pk)

run_id (uuid, fk)
example_index (int)

input (jsonb)
expected_output (jsonb)
model_output (jsonb)

scores (jsonb)

latency_ms (int)
token_usage (jsonb)
cost_usd (numeric)

created_at (timestamp)
```

Example `scores`:

```
{
  "exact_match": 1,
  "semantic_similarity": 0.92
}
```

---

# Relationships

Key relationships:
```
dataset → dataset_versions (1:N)

prompt → prompt_versions (1:N)

experiment → runs (1:N)

run → evaluation_results (1:N)

run → run_metrics (1:N)
```

Each run references:
```
dataset_version
prompt_version
model_config
```

This guarantees reproducibility.

---

# Indexing Strategy

Indexes are required for fast querying.

### runs

```
INDEX runs_experiment_idx
(experiment_id)
```

```
INDEX runs_status_idx
(status)
```

---

### evaluation_results
```
INDEX results_run_idx
(run_id)
```

```
INDEX results_example_idx
(run_id, example_index)
```

---

### run_metrics

```
INDEX run_metrics_run_idx
(run_id)
```

---

### dataset_versions

```
INDEX dataset_versions_dataset_idx
(dataset_id)
```

---

# Run Result Structure

Each evaluation example produces a structured result.

Example result:

```
{
  "run_id": "...",
  "example_index": 42,
  "input": {"question": "Who wrote Hamlet?"},
  "expected_output": "William Shakespeare",
  "model_output": "Hamlet was written by William Shakespeare.",
  "scores": {
      "exact_match": 0,
      "semantic_similarity": 0.95
  },
  "latency_ms": 740,
  "token_usage": {
      "prompt_tokens": 34,
      "completion_tokens": 16
  },
  "cost_usd": 0.0021
}
```

---

# Scalability Considerations

The system is designed to scale to large evaluation workloads.

## Horizontal worker scaling

Evaluation tasks are independent. Workers can process tasks in parallel.

---

## Result partitioning

Large result tables can grow quickly.

Recommended strategies:
- partition `evaluation_results` by `run_id`
- archive old runs

---

## Large dataset handling

Datasets are stored in object storage. Workers stream dataset files during evaluation. This prevents database bloat.

---

# Storage Strategy

## PostgreSQL

Stores:
- metadata
- run definitions
- evaluation results
- aggregated metrics

---

## Object Storage

Stores:
- dataset files
- raw model responses
- run artifacts
- logs

---

# Future Extensions

The schema supports future extensions such as:
- human evaluation annotations
- RAG retrieval metrics
- judge reasoning storage
- experiment tagging
- dataset lineage tracking

---

# Summary

This data model provides a scalable and reproducible foundation for the LLM Evaluation Platform.

Key characteristics:
- versioned datasets and prompts
- experiment and run tracking
- per-example evaluation results
- aggregated metric storage
- scalable artifact storage
- efficient indexing for analysis

The schema is intentionally minimal while remaining extensible for advanced evaluation workflows.