from llm_eval_platform.models.model_config import ModelConfig
from llm_eval_platform.repositories.base_repository import BaseRepository


class ModelRepository(BaseRepository[ModelConfig]):
    def __init__(self) -> None:
        super().__init__(ModelConfig)