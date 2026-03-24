from __future__ import annotations

from collections import UserDict
from typing import Any


class SafeFormatDict(UserDict[str, Any]):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


class PromptRenderer:
    def render(self, template: str, variables: dict[str, Any]) -> str:
        return template.format_map(SafeFormatDict(variables))