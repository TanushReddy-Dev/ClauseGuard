import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
import json
import asyncio

from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Load .env
load_dotenv(Path(__file__).resolve().parent / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env.example")  # fallback defaults

logger = logging.getLogger(__name__)

# Configure Gemini
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY environment variable is not set. "
        "Export it before starting the server."
    )
genai.configure(api_key=api_key)


class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, system: str, user: str, **kwargs) -> str:
        ...


class GeminiProvider(LLMProvider):
    """Concrete LLM provider backed by Google's Gemini API."""

    def __init__(self, model: str, *, temperature: float = 0.2, max_tokens: int = 8192) -> None:
        self._model_name = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        
        # Configure model parameters and disable safety filters since legal
        # documents often trigger false positives for violence/harassment.
        self._model = genai.GenerativeModel(
            model_name=model,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )

    @property
    def model(self) -> str:
        return self._model_name

    async def complete(self, system: str, user: str, **kwargs) -> str:
        """Send a chat completion request and return the assistant's text."""
        temperature = kwargs.get("temperature", self._temperature)
        max_tokens = kwargs.get("max_tokens", self._max_tokens)
        
        # Gemini handles system instructions natively via generation_config
        config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        
        # Combine system and user prompt for older Gemini models, or use system_instruction 
        # if using the newer API. We'll use a combined prompt approach to be safe across versions.
        combined_prompt = f"System Instructions:\n{system}\n\nUser Input:\n{user}"

        try:
            # We use generate_content_async for async execution
            # Prevent internal SDK retry sleep (on 429s) from hanging the backend
            response = await asyncio.wait_for(
                self._model.generate_content_async(
                    combined_prompt,
                    generation_config=config
                ),
                timeout=10.0
            )
            
            if not response.text:
                raise ValueError(f"Gemini API returned an empty response for model {self._model_name!r}.")
                
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
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


def _make_provider(model: str, **kwargs) -> GeminiProvider:
    """Convenience factory that creates a GeminiProvider."""
    return GeminiProvider(model=model, **kwargs)


# ---------------------------------------------------------------------------
# Provider registry — using Gemini 1.5 Flash for ultra-fast, lightweight 
# processing across all agents, with 1.5 Flash-8B as a fallback.
# ---------------------------------------------------------------------------
PROVIDER_REGISTRY: dict[str, LLMProvider] = {
    "extraction": FallbackProvider([
        _make_provider(
            "models/gemini-3.5-flash-lite",
            temperature=0.1,   
            max_tokens=8192,   
        ),
        _make_provider(
            "models/gemini-3.6-flash",
            temperature=0.1,
            max_tokens=4096,
        ),
    ]),
    "classification": FallbackProvider([
        _make_provider(
            "models/gemini-3.5-flash-lite",
            temperature=0.0,   
            max_tokens=8192,
        ),
        _make_provider(
            "models/gemini-3.6-flash",
            temperature=0.0,
            max_tokens=4096,
        ),
    ]),
    "explainer": FallbackProvider([
        _make_provider(
            "models/gemini-3.5-flash-lite",
            temperature=0.4,   
            max_tokens=8192,   
        ),
        _make_provider(
            "models/gemini-3.6-flash",
            temperature=0.4,
            max_tokens=8192,
        ),
    ]),
}
