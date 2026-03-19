# LLM Evaluation Platform — API Specification

> **Status note (2026-03):** This document is a target-state design specification. The Python service modules in this repository are currently scaffolds (mostly empty files), so treat this as implementation intent rather than current behavior.

## Overview

This document defines the HTTP API for the **LLM Evaluation Platform**.

The API allows clients to:

- manage datasets
- manage prompts
- manage model configurations
- create experiments
- run evaluations
- monitor evaluation runs
- retrieve evaluation results

The API follows a **RESTful design** and is implemented using **FastAPI**.

All endpoints return **JSON responses**.

---

# Base URL

Example base URL:

```
http://localhost:8000/api/v1
```

Versioning allows future API evolution.

---

# Authentication (Future)

Authentication is not required for the MVP.

Future versions may support:

- API keys
- OAuth
- role-based access control

---

# Core Resources

The API manages the following resources:

- datasets
- dataset versions
- prompts
- prompt versions
- model configs
- experiments
- runs
- evaluation results
- metrics

---

# Response Format

All responses follow a consistent structure.

Success response:

```
{
  "data": {...}
}
```

List response:

```
{
  "data": [...],
  "pagination": {
    "limit": 50,
    "offset": 0,
    "total": 120
  }
}
```

Error response:

```
{
  "error": {
    "code": "resource_not_found",
    "message": "Dataset not found"
  }
}
```

---

# Datasets API

## Create Dataset

Creates a logical dataset container.

```
POST /datasets
```

Request:

```
{
  "name": "customer_support_qa",
  "description": "Customer support evaluation dataset",
  "task_type": "qa"
}
```

Response:

```
{
  "data": {
    "id": "dataset_id",
    "name": "customer_support_qa",
    "created_at": "..."
  }
}
```

---

## List Datasets

```
GET /datasets
```

Query parameters:

```
limit
offset
```

---

## Get Dataset

```
GET /datasets/{dataset_id}
```

---

# Dataset Versions API

## Create Dataset Version

Uploads a dataset file.

```
POST /datasets/{dataset_id}/versions
```

Request:

```
multipart/form-data
file: dataset.jsonl
```

Response:

```
{
  "data": {
    "id": "dataset_version_id",
    "dataset_id": "...",
    "version": 1,
    "example_count": 1200
  }
}
```

---

## List Dataset Versions

```
GET /datasets/{dataset_id}/versions
```

---

# Prompts API

## Create Prompt

```
POST /prompts
```

Request:

```
{
  "name": "support_prompt",
  "description": "Customer support prompt"
}
```

---

## Create Prompt Version

```
POST /prompts/{prompt_id}/versions
```

Request:

```
{
  "template": "You are a helpful assistant.\n\nQuestion: {question}\nAnswer:"
}
```

---

## List Prompts

```
GET /prompts
```

---

# Model Config API

## Create Model Configuration

```
POST /models
```

Request:

```
{
  "provider": "openai",
  "model_name": "gpt-4o",
  "parameters": {
    "temperature": 0,
    "max_tokens": 512
  }
}
```

---

## List Models

```
GET /models
```

---

# Experiments API

Experiments group evaluation runs.

## Create Experiment

```
POST /experiments
```

Request:

```
{
  "name": "support_prompt_experiments",
  "description": "Prompt optimization experiments"
}
```

---

## List Experiments

```
GET /experiments
```

---

## Get Experiment

```
GET /experiments/{experiment_id}
```

---

# Runs API

Runs represent evaluation executions.

---

## Create Run

```
POST /runs
```

Request:

```
{
  "experiment_id": "...",
  "dataset_version_id": "...",
  "prompt_version_id": "...",
  "model_config_id": "...",
  "metrics": [
    "exact_match",
    "semantic_similarity"
  ]
}
```

Response:

```
{
  "data": {
    "run_id": "...",
    "status": "created"
  }
}
```

---

## Get Run

```
GET /runs/{run_id}
```

Response:

```
{
  "data": {
    "run_id": "...",
    "status": "running",
    "progress": 0.42,
    "created_at": "...",
    "started_at": "...",
    "completed_at": null
  }
}
```

---

## List Runs

```
GET /runs
```

Query parameters:

```
experiment_id
status
limit
offset
```

---

## Cancel Run

```
POST /runs/{run_id}/cancel
```

---

# Run Metrics API

Aggregated metrics for a run.

```
GET /runs/{run_id}/metrics
```

Response:

```
{
  "data": {
    "exact_match": 0.81,
    "semantic_similarity": 0.92,
    "latency_ms_avg": 740,
    "cost_total_usd": 12.40
  }
}
```

---

# Evaluation Results API

Per-example results.

```
GET /runs/{run_id}/results
```

Query parameters:

```
limit
offset
```

Example response:

```
{
  "data": [
    {
      "example_index": 42,
      "model_output": "...",
      "scores": {
        "exact_match": 1,
        "semantic_similarity": 0.94
      },
      "latency_ms": 720
    }
  ]
}
```

---

# Metrics API

Lists supported evaluation metrics.

```
GET /metrics
```

Response:

```
{
  "data": [
    "exact_match",
    "semantic_similarity",
    "llm_judge",
    "latency",
    "cost"
  ]
}
```

---

# Pagination

Endpoints returning lists support pagination.

Parameters:

```
limit
offset
```

Example:

```
GET /runs?limit=50&offset=0
```

---

# Filtering

Common filtering options:

```
experiment_id
status
dataset_id
model
```

---

# Rate Limiting (Future)

Future versions may enforce rate limits.

Example:

```
100 requests / minute
```

---

# Future Extensions

The API can be extended to support:

- human evaluation annotations
- experiment comparison endpoints
- dataset browsing
- RAG evaluation endpoints
- prompt optimization workflows

---

# Summary

The API provides a simple and extensible interface for managing evaluation workflows.

Key characteristics:

- RESTful resource design
- asynchronous evaluation runs
- reproducible configurations
- scalable result retrieval
- minimal complexity for MVP