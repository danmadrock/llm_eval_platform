from models.experiment import Experiment
from repositories.base_repository import BaseRepository


class ExperimentRepository(BaseRepository[Experiment]):
    def __init__(self) -> None:
        super().__init__(Experiment)