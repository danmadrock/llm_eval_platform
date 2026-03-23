from llm_eval_platform.models.experiment import Experiment
from llm_eval_platform.repositories.base_repository import BaseRepository


class ExperimentRepository(BaseRepository[Experiment]):
    def __init__(self) -> None:
        super().__init__(Experiment)