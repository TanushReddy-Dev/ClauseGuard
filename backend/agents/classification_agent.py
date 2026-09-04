from __future__ import annotations

"""Classification Agent — batched taxonomy confirmation.

Receives ALL clauses together with their candidate taxonomy matches (produced
by the deterministic Phase 2 pipeline) and makes ONE LLM call to confirm or
reject each candidate, returning structured JSON with final category
assignments and confidence scores.
"""

import json
import logging
import re

from agent_router import PROVIDER_REGISTRY

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt design notes
# ---------------------------------------------------------------------------
# 1. Single batched call is intentional — it saves latency and cost compared
#    to N individual calls, and lets the model see cross-clause context (e.g.
#    if two clauses look similar it can resolve ambiguity by contrast).
# 2. The schema is prescribed precisely so the 8B model returns parseable JSON
#    on the first attempt.  The "best_match" / "confidence" / "reasoning"
#    triple per clause makes downstream risk-scoring straightforward.
# 3. The model is told to pick from candidates OR assign "other" with a short
#    label — this covers edge cases where the deterministic matcher missed.
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a legal-clause classification engine. You will receive a JSON object \
with a list of contract clauses and, for each clause, a set of candidate \
taxonomy categories produced by a keyword matcher. Your job is to confirm the \
single best category for each clause or reject all candidates and assign \
"other:<short_label>".

Instructions:
1. For each clause, review its text and the candidate categories.
2. Pick the single best-matching category from the candidates. If none fit, \
use "other:<your_short_label>" (e.g. "other:force_majeure").
3. Assign a confidence score from 0.0 to 1.0.
4. Provide a one-sentence reasoning string.

Return ONLY a JSON object with this exact schema — no markdown fences, no \
commentary:

{
  "classifications": [
    {
      "clause_index": 0,
      "best_match": "non-compete",
      "confidence": 0.93,
      "reasoning": "Clause explicitly restricts competitive employment."
    }
  ]
}

Rules:
- The "classifications" array MUST have exactly one entry per input clause, \
in the same order.
- "best_match" must be a string from the candidate list OR "other:<label>".
- "confidence" must be a float between 0.0 and 1.0.
- Do NOT add, remove, or reorder clauses.
"""


async def run_classification_agent(
    clauses: list[str],
    candidate_matches: list[list[dict]],
) -> list[dict]:
    """Confirm or reject taxonomy candidates for every clause in one LLM call.

    Parameters
    ----------
    clauses:
        Cleaned clause texts (output of extraction agent).
    candidate_matches:
        For each clause, a list of dicts like
        ``[{"category": "non-compete", "score": 0.85}, ...]`` produced by the
        deterministic keyword/embedding matcher in Phase 2.

    Returns
    -------
    A list of dicts (one per clause) each containing at minimum:
        ``{"best_match": str, "confidence": float, "reasoning": str}``
    """
    if not clauses:
        return []

    provider = PROVIDER_REGISTRY["classification"]

    # Build the user payload — one entry per clause with its candidate list
    payload = {
        "clauses": [
            {
                "index": idx,
                "text": text,
                "candidates": candidates,
            }
            for idx, (text, candidates) in enumerate(zip(clauses, candidate_matches))
        ]
    }

    raw_response = await provider.complete(
        system=_SYSTEM_PROMPT,
        user=json.dumps(payload, ensure_ascii=False),
        temperature=0.0,
        max_tokens=4096,
    )

    parsed = _parse_classifications(raw_response, expected_count=len(clauses))
    if parsed is not None:
        return parsed

    # Graceful degradation: fall back to the top deterministic candidate
    logger.warning(
        "Classification agent returned unparseable response; falling back to "
        "top deterministic candidates. Response preview: %.300s",
        raw_response,
    )
    return _fallback_classifications(candidate_matches)


# ---------------------------------------------------------------------------
# Response parsing helpers
# ---------------------------------------------------------------------------

def _parse_classifications(text: str, expected_count: int) -> list[dict] | None:
    """Extract the classifications array from the model response."""
    stripped = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    stripped = re.sub(r"```\s*$", "", stripped, flags=re.MULTILINE)
    stripped = stripped.strip()

    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return None

    # Accept either {"classifications": [...]} or a bare [...]
    if isinstance(parsed, dict):
        classifications = parsed.get("classifications")
    elif isinstance(parsed, list):
        classifications = parsed
    else:
        return None

    if not isinstance(classifications, list):
        return None

    # Validate minimum fields on each entry
    result: list[dict] = []
    for item in classifications:
        if not isinstance(item, dict):
            return None
        best_match = item.get("best_match") or item.get("category", "unknown")
        confidence = item.get("confidence", 0.5)
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.5
        confidence = max(0.0, min(1.0, confidence))

        result.append({
            "best_match": str(best_match),
            "confidence": confidence,
            "reasoning": str(item.get("reasoning", "")),
        })

    if len(result) != expected_count:
        logger.warning(
            "Classification agent returned %d items but expected %d.",
            len(result),
            expected_count,
        )
        # Still usable if the counts are off; downstream will align by index
        if not result:
            return None

    return result


def _fallback_classifications(candidate_matches: list[list[dict]]) -> list[dict]:
    """Pick the highest-scoring deterministic candidate per clause."""
    fallback: list[dict] = []
    for candidates in candidate_matches:
        if candidates:
            best = max(candidates, key=lambda c: c.get("score", 0.0))
            fallback.append({
                "best_match": best.get("category", "unknown"),
                "confidence": best.get("score", 0.5),
                "reasoning": "Fallback: top deterministic candidate used.",
            })
        else:
            fallback.append({
                "best_match": "unknown",
                "confidence": 0.0,
                "reasoning": "No candidates available.",
            })
    return fallback
