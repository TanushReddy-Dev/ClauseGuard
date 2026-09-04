from __future__ import annotations

"""Extraction Agent — OCR noise cleanup.

Receives raw segmented clauses (potentially noisy from OCR) and returns
cleaned, faithful versions.  The prompt is deliberately strict: the model
must NOT paraphrase, summarise, or infer meaning — only fix character-level
OCR artefacts (ligature splits, misread glyphs, stray whitespace, etc.).
"""

import json
import logging
import re

from agent_router import PROVIDER_REGISTRY

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt design notes
# ---------------------------------------------------------------------------
# 1. Role anchoring ("You are an OCR post-processor") prevents the model from
#    drifting into summarisation or legal-interpretation mode.
# 2. Explicit negative instructions ("Do NOT paraphrase …") reduce hallucinated
#    rewrites — critical because downstream agents rely on textual fidelity.
# 3. JSON output envelope (list of strings) is trivial for 8B-Instruct to
#    produce reliably and easy to parse with a regex fallback.
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are an OCR post-processing specialist. You will receive a JSON array of \
raw text clauses extracted from a scanned legal contract. Each clause may \
contain OCR noise: misread characters, broken ligatures, stray symbols, \
irregular whitespace, or missing punctuation.

Your task:
1. Fix obvious OCR errors (e.g. "rn" → "m", "l" → "I" where contextually \
appropriate, "0" ↔ "O", run-together words, etc.).
2. Normalise whitespace (collapse multiple spaces, fix line-break artefacts).
3. Restore missing or garbled punctuation only when unambiguous.

Rules you MUST follow:
- Do NOT paraphrase, reword, summarise, or add meaning.
- Do NOT remove or merge separate clauses.
- Preserve the original clause order.
- Return ONLY a JSON array of cleaned strings — no commentary, no markdown \
fences, no keys.

Example input:  ["The Contr actor sha ll not cornpete …"]
Example output: ["The Contractor shall not compete …"]
"""


async def run_extraction_agent(raw_clauses: list[str]) -> list[str]:
    """Clean OCR noise from *raw_clauses* via the extraction LLM.

    Returns a list of cleaned clause strings in the same order.  If the LLM
    response cannot be parsed, the original clauses are returned unchanged so
    the pipeline degrades gracefully rather than crashing.
    """
    if not raw_clauses:
        return []

    provider = PROVIDER_REGISTRY["extraction"]

    user_payload = json.dumps(raw_clauses, ensure_ascii=False)

    raw_response = await provider.complete(
        system=_SYSTEM_PROMPT,
        user=user_payload,
        temperature=0.1,
        max_tokens=4096,
    )

    # --- Parse response -------------------------------------------------------
    # Primary path: the model returns valid JSON.
    # Fallback: strip markdown fences and try again, then give up gracefully.
    cleaned = _parse_clauses(raw_response, expected_count=len(raw_clauses))
    if cleaned is not None:
        return cleaned

    logger.warning(
        "Extraction agent returned unparseable response; falling back to raw clauses. "
        "Response preview: %.300s",
        raw_response,
    )
    return raw_clauses


def _parse_clauses(text: str, expected_count: int) -> list[str] | None:
    """Try to extract a JSON list of strings from the model output."""
    # Strip markdown code fences if present
    stripped = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    stripped = re.sub(r"```\s*$", "", stripped, flags=re.MULTILINE)
    stripped = stripped.strip()

    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return None

    if not isinstance(parsed, list):
        return None

    # Coerce every element to a string (model might return numbers for short clauses)
    result = [str(item).strip() for item in parsed]

    # Warn but don't fail if count differs — partial cleanup is better than none
    if len(result) != expected_count:
        logger.warning(
            "Extraction agent returned %d clauses but expected %d; using returned set.",
            len(result),
            expected_count,
        )

    return result
