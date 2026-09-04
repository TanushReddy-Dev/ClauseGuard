from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, system: str, user: str, **kwargs) -> str:
        ...


# Register provider classes here as they are implemented.
# Key: short name (e.g. "groq", "gemini"), Value: LLMProvider subclass.
PROVIDER_REGISTRY: dict[str, type[LLMProvider]] = {}
