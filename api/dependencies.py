from services.datasets.dataset_service import DatasetService
from services.datasets.dataset_version_service import DatasetVersionService
from services.evaluation_result_service import EvaluationResultService
from services.experiments.experiment_service import ExperimentService
from services.model_config_service import ModelConfigService
from services.prompts.prompt_service import PromptService
from services.prompts.prompt_version_service import PromptVersionService
from services.runs.run_service import RunService


def get_dataset_service() -> DatasetService:
    return DatasetService()


def get_dataset_version_service() -> DatasetVersionService:
    return DatasetVersionService()


def get_prompt_service() -> PromptService:
    return PromptService()


def get_prompt_version_service() -> PromptVersionService:
    return PromptVersionService()


def get_model_config_service() -> ModelConfigService:
    return ModelConfigService()


def get_experiment_service() -> ExperimentService:
    return ExperimentService()


def get_run_service() -> RunService:
    return RunService()


def get_evaluation_result_service() -> EvaluationResultService:
    return EvaluationResultService()