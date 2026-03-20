from models.model_config import ModelConfig
from repositories.base_repository import BaseRepository


class ModelRepository(BaseRepository[ModelConfig]):
    def __init__(self) -> None:
        super().__init__(ModelConfig)