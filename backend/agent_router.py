from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load .env from the backend directory so FEATHERLESS_API_KEY is available
# even when the process is launched from a different working directory.
load_dotenv(Path(__file__).resolve().parent / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env.example")  # fallback defaults

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, system: str, user: str, **kwargs) -> str:
        ...


class FeatherlessProvider(LLMProvider):
    """Concrete LLM provider backed by Featherless.ai's OpenAI-compatible API.

    Each instance is bound to a specific model so the registry can map logical
    agent roles (extraction, classification, explainer) to different model sizes.
    """

    def __init__(self, model: str, *, temperature: float = 0.2, max_tokens: int = 4096) -> None:
        api_key = os.environ.get("FEATHERLESS_API_KEY")
        if not api_key:
            raise RuntimeError(
                "FEATHERLESS_API_KEY environment variable is not set. "
                "Export it before starting the server."
            )

        self._client = AsyncOpenAI(
            base_url="https://api.featherless.ai/v1",
            api_key=api_key,
            timeout=10.0,  # fast timeout to trigger fallbacks before Demo Guard
        )
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    @property
    def model(self) -> str:
        return self._model

    async def complete(self, system: str, user: str, **kwargs) -> str:
        """Send a chat completion request and return the assistant's text.

        Raises on empty/malformed responses so callers can handle retries at a
        higher level rather than silently propagating garbage.
        """
        temperature = kwargs.get("temperature", self._temperature)
        max_tokens = kwargs.get("max_tokens", self._max_tokens)

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if not response.choices:
            raise ValueError(
                f"Featherless API returned zero choices for model {self._model!r}. "
                f"Response id: {getattr(response, 'id', 'unknown')}"
            )

        content = response.choices[0].message.content
        if content is None:
            raise ValueError(
                f"Featherless API returned a choice with null content for model {self._model!r}."
            )

        return content.strip()


class FallbackProvider(LLMProvider):
    """Wraps a primary provider with an ordered chain of fallback providers.

    On any exception from the primary (timeout, rate limit, 5xx, malformed
    response), the next provider in the chain is tried.  If every provider in
    the chain fails, the final exception is re-raised so the caller's own
    graceful-degradation logic (e.g. returning raw clauses) still activates.

    This gives the pipeline zero-downtime resilience during live demos:
    - Primary model is unavailable → fallback lightweight model responds
    - All models down → agent-level fallbacks return deterministic results
    """

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

        # All providers exhausted — re-raise the last exception so agent-level
        # graceful degradation (e.g. returning raw clauses) still triggers.
        raise last_exc  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Shared AsyncOpenAI client — reused across all FeatherlessProvider instances
# to benefit from connection pooling.
# ---------------------------------------------------------------------------

def _make_provider(model: str, **kwargs) -> FeatherlessProvider:
    """Convenience factory that creates a FeatherlessProvider."""
    return FeatherlessProvider(model=model, **kwargs)


# ---------------------------------------------------------------------------
# Provider registry — maps logical agent roles to FallbackProvider chains.
#
# Fallback strategy per role:
#   • extraction    — Qwen2.5-7B (primary) → Qwen2.5-3B (fast fallback)
#   • classification — Qwen2.5-7B (primary) → Qwen2.5-3B (fast fallback)
#   • explainer     — Qwen2.5-32B (primary) → Qwen2.5-7B (lighter fallback)
#
# The lightweight fallback models sacrifice some quality but keep the pipeline
# running when the primary model hits rate limits or latency spikes.
# ---------------------------------------------------------------------------
PROVIDER_REGISTRY: dict[str, LLMProvider] = {
    "extraction": FallbackProvider([
        _make_provider(
            "Qwen/Qwen2.5-7B-Instruct",
            temperature=0.1,   # low temperature for faithful OCR cleanup
            max_tokens=8192,   # Increased for larger PDFs
        ),
        _make_provider(
            "Qwen/Qwen2.5-32B-Instruct", # Step up to larger context handling
            temperature=0.1,
            max_tokens=8192,
        ),
        _make_provider(
            "Qwen/Qwen2.5-3B-Instruct",
            temperature=0.1,
            max_tokens=4096,
        ),
    ]),
    "classification": FallbackProvider([
        _make_provider(
            "Qwen/Qwen2.5-7B-Instruct",
            temperature=0.0,   # deterministic classification
            max_tokens=8192,
        ),
        _make_provider(
            "Qwen/Qwen2.5-32B-Instruct",
            temperature=0.0,
            max_tokens=8192,
        ),
        _make_provider(
            "Qwen/Qwen2.5-3B-Instruct",
            temperature=0.0,
            max_tokens=4096,
        ),
    ]),
    "explainer": FallbackProvider([
        _make_provider(
            "Qwen/Qwen2.5-72B-Instruct", # Largest model for massive context analysis
            temperature=0.4,
            max_tokens=8192,
        ),
        _make_provider(
            "Qwen/Qwen2.5-32B-Instruct",
            temperature=0.4,   # slightly creative for natural language output
            max_tokens=16384,   # explainer produces longer narrative text
        ),
        _make_provider(
            "Qwen/Qwen2.5-7B-Instruct",
            temperature=0.4,
            max_tokens=8192,
        ),
    ]),
}
