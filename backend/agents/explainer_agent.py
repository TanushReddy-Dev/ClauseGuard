from __future__ import annotations

"""Explainer Agent — plain-language report & negotiation script.

Takes the full set of risk-scored, flagged clauses and the overall risk score
and produces a human-friendly summary plus a ready-to-use negotiation script.
This is the only agent that uses a larger model (70B) because the output must
be persuasive, nuanced, and well-structured prose — not structured data.
"""

import json
import logging
import re

from agent_router import PROVIDER_REGISTRY

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt design notes
# ---------------------------------------------------------------------------
# 1. The model is given the persona of a senior contract-review advisor so it
#    produces appropriately authoritative but accessible language.
# 2. The negotiation script is explicitly framed as first-person dialogue the
#    user can copy-paste into an email or say in a meeting — this dramatically
#    increases actionability versus a generic "you could try asking for X".
# 3. Temperature is 0.4: high enough for natural prose, low enough to avoid
#    fabricating clause content.
# 4. The output schema is minimal (summary + negotiation_script) so parsing
#    is reliable even from a 70B model that occasionally adds preamble.
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a senior contract-review advisor writing for a non-lawyer audience. \
You will receive a JSON object containing:
- "flagged_clauses": a list of clauses that have been risk-scored, each with \
  clause_text, category, risk_level, risk_score, and explanation.
- "overall_risk_score": a float from 0 to 10 representing aggregate risk.

Produce a JSON object with exactly two keys:

{
  "summary": "<one-paragraph plain-language summary of the contract's risk \
profile, highlighting the most concerning clauses and why>",
  "negotiation_script": "<a ready-to-use, first-person script the user can \
say or email to the other party to push back on the riskiest clauses. Be \
specific: reference clause language, propose concrete alternatives, and \
maintain a professional-but-firm tone.>"
}

Rules:
- Write for a non-lawyer. Avoid jargon; explain terms when necessary.
- The summary should be 3-6 sentences.
- The negotiation script should cover every HIGH or CRITICAL clause and \
optionally mention MEDIUM ones.
- Do NOT invent clauses that were not provided.
- Return ONLY the JSON object — no markdown fences, no commentary.
"""


async def run_explainer_agent(
    flagged_clauses: list[dict],
    overall_risk: float,
) -> dict:
    """Generate a plain-language summary and negotiation script.

    Parameters
    ----------
    flagged_clauses:
        List of dicts, each with keys: clause_text, category, risk_level,
        risk_score, explanation.
    overall_risk:
        Aggregate risk score (0–10).

    Returns
    -------
    ``{"summary": str, "negotiation_script": str}``
    """
    if not flagged_clauses:
        return {
            "summary": "No clauses were flagged for risk in this contract.",
            "negotiation_script": "No negotiation points identified.",
        }

    provider = PROVIDER_REGISTRY["explainer"]

    user_payload = json.dumps(
        {
            "flagged_clauses": flagged_clauses,
            "overall_risk_score": round(overall_risk, 2),
        },
        ensure_ascii=False,
    )

    raw_response = await provider.complete(
        system=_SYSTEM_PROMPT,
        user=user_payload,
        temperature=0.4,
        max_tokens=8192,
    )

    parsed = _parse_explainer_response(raw_response)
    if parsed is not None:
        return parsed

    # Graceful fallback — return the raw text as summary so the user at least
    # sees *something* useful.
    logger.warning(
        "Explainer agent returned unparseable JSON; wrapping raw text. "
        "Response preview: %.300s",
        raw_response,
    )
    return {
        "summary": raw_response[:2000],
        "negotiation_script": "Unable to generate a structured negotiation script. "
        "Please review the summary above.",
    }


def _parse_explainer_response(text: str) -> dict | None:
    """Extract the summary / negotiation_script dict from model output."""
    stripped = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    stripped = re.sub(r"```\s*$", "", stripped, flags=re.MULTILINE)
    stripped = stripped.strip()

    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return None

    if not isinstance(parsed, dict):
        return None

    summary = parsed.get("summary")
    script = parsed.get("negotiation_script")

    if not isinstance(summary, str) or not isinstance(script, str):
        return None

    return {
        "summary": summary.strip(),
        "negotiation_script": script.strip(),
    }
