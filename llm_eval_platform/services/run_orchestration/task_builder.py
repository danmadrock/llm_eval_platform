from __future__ import annotations

from typing import Any

from llm_eval_platform.models.run import Run
from llm_eval_platform.storage.dataset_storage import DatasetStorage
from llm_eval_platform.tasks.evaluation_task import EvaluationTask


class TaskBuilder:
    def __init__(self, dataset_storage: DatasetStorage | None = None) -> None:
        self.dataset_storage = dataset_storage or DatasetStorage()

    def build_tasks(self, run: Run) -> list[EvaluationTask]:
        examples = self.dataset_storage.load_examples(run.dataset_version.object_uri)
        metric_names = self.resolve_metrics(run.parameters)
        tasks: list[EvaluationTask] = []
        for index, record in enumerate(examples):
            input_payload, expected_output = self._split_record(record)
            tasks.append(
                EvaluationTask(
                    run_id=run.id,
                    example_index=index,
                    input_payload=input_payload,
                    expected_output=expected_output,
                    prompt_template=run.prompt_version.template,
                    model_provider=run.model_config.provider,
                    model_name=run.model_config.model_name,
                    model_parameters=run.model_config.parameters,
                    metrics=metric_names,
                )
            )
        return tasks

    @staticmethod
    def _split_record(record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None]:
        if "input" in record:
            input_payload = dict(record["input"])
        else:
            input_payload = {
                key: value
                for key, value in record.items()
                if key not in {"expected_output", "reference", "answer", "target"}
            }
        if "expected_output" in record:
            expected_output = record["expected_output"]
        elif "reference" in record:
            expected_output = record["reference"]
        elif "answer" in record:
            expected_output = {"answer": record["answer"]}
        elif "target" in record:
            expected_output = {"answer": record["target"]}
        else:
            expected_output = None
        return input_payload, expected_output

    @staticmethod
    def resolve_metrics(parameters: dict[str, Any]) -> list[str]:
        configured = parameters.get("metrics") if isinstance(parameters, dict) else None
        if not configured:
            return ["exact_match", "semantic_similarity", "latency", "cost"]

        metric_names = [str(metric) for metric in configured]
        if "llm_judge_experimental" in metric_names and "llm_judge" not in metric_names:
            metric_names.append("llm_judge")
        return metric_names