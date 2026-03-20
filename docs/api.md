# LLM Evaluation Platform — API Specification

> **Status note (2026-03-19):** Phase 1 is now implemented in this repository for the core metadata domain. The endpoints below describe the current API surface for datasets, prompts, model configs, experiments, runs, and evaluation results.

## Overview

The API exposes reproducible metadata workflows for the evaluation platform. It is implemented with **FastAPI** and follows a consistent envelope format for all CRUD endpoints.

Base URL

```
/api/v1
```

## Response Format

Success response:

```
{
  "data": {"id": "..."}
}
```

List response:

```json
{
  "data": [],
  "pagination": {
    "limit": 50,
    "offset": 0,
    "total": 1
  }
}
```

Error response:

```json
{
  "error": {
    "code": "resource_not_found",
    "message": "Dataset not found."
  }
}
```

## Implemented Core Endpoints

### Datasets

- `POST /datasets`
- `GET /datasets`
- `GET /datasets/{dataset_id}`
- `PATCH /datasets/{dataset_id}`
- `DELETE /datasets/{dataset_id}`
- `POST /datasets/{dataset_id}/versions`
- `GET /datasets/{dataset_id}/versions`

Dataset versions are immutable and auto-increment from `1` per dataset.

### Prompts

- `POST /prompts`
- `GET /prompts`
- `GET /prompts/{prompt_id}`
- `PATCH /prompts/{prompt_id}`
- `DELETE /prompts/{prompt_id}`
- `POST /prompts/{prompt_id}/versions`
- `GET /prompts/{prompt_id}/versions`

Prompt versions are immutable and auto-increment from `1` per prompt.

### Model Configs

- `POST /models`
- `GET /models`
- `GET /models/{model_config_id}`
- `PATCH /models/{model_config_id}`
- `DELETE /models/{model_config_id}`

### Experiments

- `POST /experiments`
- `GET /experiments`
- `GET /experiments/{experiment_id}`
- `PATCH /experiments/{experiment_id}`
- `DELETE /experiments/{experiment_id}`

### Runs

- `POST /runs`
- `GET /runs`
- `GET /runs/{run_id}`
- `PATCH /runs/{run_id}`
- `DELETE /runs/{run_id}`

Run creation validates references to the selected experiment, dataset version, prompt version, and model configuration.

### Evaluation Results

- `POST /results`
- `GET /results`
- `GET /results/{result_id}`
- `PATCH /results/{result_id}`
- `DELETE /results/{result_id}`

`GET /results` supports optional filtering by `run_id`.

## Migration Reproducibility
Schema management is handled by Alembic. The Phase 1 initial migration creates all implemented tables and supports a full `upgrade -> downgrade -> upgrade` cycle, which is exercised by automated tests.