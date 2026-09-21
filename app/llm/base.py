from abc import ABC, abstractmethod
from typing import TypeVar
from pydantic import BaseModel
from app.models import Usage

T = TypeVar("T", bound=BaseModel)


class ProviderError(RuntimeError):
    """Sanitized provider failure, safe to persist/display."""


class LLMProvider(ABC):
    def __init__(self):
        self.usage: list[Usage] = []
        self.on_usage = None

    def record(self, usage):
        self.usage.append(usage)
        if self.on_usage:
            self.on_usage(usage)

    @abstractmethod
    def generate_structured(self, agent: str, system_prompt: str, input_data: dict,
                            response_schema: type[T]) -> T:
        """Return a validated model or raise; never silently use mock output."""
