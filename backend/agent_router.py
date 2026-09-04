import logging
import os
import asyncio
from abc import ABC, abstractmethod
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load .env
load_dotenv(Path(__file__).resolve().parent / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env.example")  # fallback defaults

logger = logging.getLogger(__name__)

# Configure Groq
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    raise RuntimeError(
        "GROQ_API_KEY environment variable is not set. "
        "Export it before starting the server."
    )

class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, system: str, user: str, **kwargs) -> str:
        ...

class GroqProvider(LLMProvider):
    """Concrete LLM provider backed by Groq's ultra-fast API."""

    def __init__(self, model: str, *, temperature: float = 0.2, max_tokens: int = 8192) -> None:
        self._model_name = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        
        self._client = AsyncOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=api_key,
            timeout=15.0,  # Strict timeout
        )

    @property
    def model(self) -> str:
        return self._model_name

    async def complete(self, system: str, user: str, **kwargs) -> str:
        temperature = kwargs.get("temperature", self._temperature)
        max_tokens = kwargs.get("max_tokens", self._max_tokens)

        try:
            # Wrap the generation call in wait_for to prevent built-in retry sleep
            response = await asyncio.wait_for(
                self._client.chat.completions.create(
                    model=self._model_name,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                ),
                timeout=15.0
            )
            
            if not response.choices:
                raise ValueError(f"Groq API returned zero choices for model {self._model_name!r}.")
                
            content = response.choices[0].message.content
            if content is None:
                raise ValueError(f"Groq API returned a choice with null content for model {self._model_name!r}.")
                
            return content.strip()
            
        except Exception as e:
            logger.error(f"Groq generation failed for {self._model_name}: {e}")
            raise


class FallbackProvider(LLMProvider):
    """Wraps a primary provider with an ordered chain of fallback providers."""

    def __init__(self, providers: list[LLMProvider]) -> None:
        if not providers:
            raise ValueError("FallbackProvider requires at least one provider.")
        self._providers = providers

    @property
    def model(self) -> str:
        first = self._providers[0]
        return getattr(first, "model", "unknown")

    async def complete(self, system: str, user: str, **kwargs) -> str:
        last_exc: BaseException | None = None

        for idx, provider in enumerate(self._providers):
            model_name = getattr(provider, "model", f"provider-{idx}")
            try:
                result = await provider.complete(system, user, **kwargs)
                if idx > 0:
                    logger.info(
                        "Fallback succeeded on attempt %d/%d (model: %s).",
                        idx + 1,
                        len(self._providers),
                        model_name,
                    )
                return result
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "Provider %d/%d (%s) failed: %s. %s",
                    idx + 1,
                    len(self._providers),
                    model_name,
                    exc,
                    "Trying next fallback…" if idx < len(self._providers) - 1 else "No more fallbacks.",
                )

        raise last_exc  # type: ignore[misc]


def _make_provider(model: str, **kwargs) -> GroqProvider:
    """Convenience factory that creates a GroqProvider."""
    return GroqProvider(model=model, **kwargs)


# ---------------------------------------------------------------------------
# Provider registry — using Groq for ultra-fast, lightweight processing
# ---------------------------------------------------------------------------
PROVIDER_REGISTRY: dict[str, LLMProvider] = {
    "extraction": FallbackProvider([
        _make_provider(
            "openai/gpt-oss-20b",
            temperature=0.1,
            max_tokens=8192,
        ),
        _make_provider(
            "allam-2-7b",
            temperature=0.1,
            max_tokens=8192,
        ),
    ]),
    "classification": FallbackProvider([
        _make_provider(
            "openai/gpt-oss-20b",
            temperature=0.0,
            max_tokens=8192,
        ),
        _make_provider(
            "allam-2-7b",
            temperature=0.0,
            max_tokens=8192,
        ),
    ]),
    "explainer": FallbackProvider([
        _make_provider(
            "openai/gpt-oss-120b",
            temperature=0.4,   
            max_tokens=8192,   
        ),
        _make_provider(
            "openai/gpt-oss-20b",
            temperature=0.4,   
            max_tokens=8192,   
        ),
    ]),
}