from __future__ import annotations

"""Classification Agent — single-clause taxonomy confirmation.

Receives one clause with its candidate taxonomy matches and confirms or
rejects the candidate, returning structured JSON.
"""

import json
import logging
import re

from agent_router import PROVIDER_REGISTRY

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a legal-clause classification engine. You will receive a JSON object \
with a contract clause and a set of candidate taxonomy categories produced \
by a keyword matcher. Your job is to confirm the single best category for \
the clause or reject all candidates and assign "other:<short_label>".

Instructions:
1. Review the clause text and the candidate categories.
2. Pick the single best-matching category from the candidates. If none fit, \
use "other:<your_short_label>" (e.g. "other:force_majeure").
3. Assign a confidence score from 0.0 to 1.0.
4. Provide a one-sentence reasoning string.

Return ONLY a JSON object with this exact schema — no markdown fences, no commentary:

{
  "best_match": "non-compete",
  "confidence": 0.93,
  "reasoning": "Clause explicitly restricts competitive employment."
}

Rules:
- "best_match" must be a string from the candidate list OR "other:<label>".
- "confidence" must be a float between 0.0 and 1.0.
"""

async def analyze(clause: str, candidates: list[dict]) -> dict:
    """Analyze a single clause."""
    provider = PROVIDER_REGISTRY["classification"]
    
    payload = {
        "text": clause,
        "candidates": candidates
    }
    
    try:
        raw_response = await provider.complete(
            system=_SYSTEM_PROMPT,
            user=json.dumps(payload, ensure_ascii=False),
            temperature=0.0,
            max_tokens=1024,
        )
        
        stripped = re.sub(r"^```(?:json)?\s*", "", raw_response, flags=re.MULTILINE)
        stripped = re.sub(r"```\s*$", "", stripped, flags=re.MULTILINE)
        stripped = stripped.strip()
        
        parsed = json.loads(stripped)
        
        best_match = parsed.get("best_match") or parsed.get("category", "unknown")
        confidence = float(parsed.get("confidence", 0.5))
        reasoning = str(parsed.get("reasoning", ""))
        
        return {
            "best_match": str(best_match),
            "confidence": max(0.0, min(1.0, confidence)),
            "reasoning": reasoning
        }
    except Exception as exc:
        logger.warning("Classification failed for clause: %s. Using fallback. Error: %s", clause[:30], exc)
        if candidates:
            best = max(candidates, key=lambda c: c.get("score", 0.0))
            return {
                "best_match": best.get("category", "unknown"),
                "confidence": best.get("score", 0.5),
                "reasoning": "Fallback: top deterministic candidate used."
            }
        return {
            "best_match": "unknown",
            "confidence": 0.0,
            "reasoning": "No candidates available."
        }
