from __future__ import annotations

"""Full analysis pipeline — chains deterministic phases with LLM agent calls.

Pipeline stages:
  0. Cache check — return instantly on cache hit (SHA-256 of normalised text).
  1. Segmentation (deterministic) — split raw OCR text into clause-level chunks.
  2. Extraction Agent (LLM) — clean OCR noise from each clause.
  3. Candidate matching (deterministic) — keyword/heuristic taxonomy matching.
  4. Classification Agent (LLM, batched) — confirm/reject taxonomy candidates.
  5. Risk scoring (deterministic) — rule-based risk scores per clause.
  6. Explainer Agent (LLM) — plain-language summary + negotiation script.
  7. Cache save — persist the result for future instant retrieval.
"""

import asyncio
import logging
import re

from schemas import (
    AnalysisReport,
    ClauseClassification,
    ClauseRiskScore,
    RiskLevel,
)
from agents.extraction_agent import run_extraction_agent
from agents import classification_agent
from agents.explainer_agent import run_explainer_agent
from cache_layer import compute_hash, get_cached_response, save_to_cache

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Taxonomy used by the deterministic candidate matcher (Phase 2)
# ---------------------------------------------------------------------------
TAXONOMY_KEYWORDS: dict[str, list[str]] = {
    "non-compete": [
        "non-compete", "noncompete", "not compete", "competitive activity",
        "restraint of trade", "covenant not to compete",
    ],
    "non-solicitation": [
        "non-solicitation", "nonsolicitation", "not solicit", "soliciting",
        "recruit employees",
    ],
    "IP assignment": [
        "intellectual property", "IP assignment", "work product",
        "inventions", "copyright assignment", "all rights",
    ],
    "confidentiality": [
        "confidential", "nondisclosure", "non-disclosure", "NDA",
        "proprietary information", "trade secret",
    ],
    "termination": [
        "termination", "terminate", "at-will", "notice period",
        "upon termination", "severance",
    ],
    "liability": [
        "liability", "indemnif", "hold harmless", "limitation of liability",
        "damages", "consequential",
    ],
    "payment": [
        "payment", "compensation", "invoice", "net 30", "net 60",
        "late fee", "billing",
    ],
    "governing-law": [
        "governing law", "jurisdiction", "venue", "dispute resolution",
        "arbitration", "mediation",
    ],
}

# Risk weights per category — higher weight = inherently riskier clause type
_CATEGORY_RISK_WEIGHTS: dict[str, float] = {
    "non-compete": 8.0,
    "non-solicitation": 6.0,
    "IP assignment": 7.0,
    "confidentiality": 4.0,
    "termination": 5.5,
    "liability": 7.5,
    "payment": 3.0,
    "governing-law": 3.5,
}

# High-signal risk phrases that bump the score
_RISK_PHRASES: list[tuple[re.Pattern[str], float]] = [
    (re.compile(r"\b(24|36|48)\s*-?\s*month", re.I), 2.0),
    (re.compile(r"\b100[- ]?mile", re.I), 1.5),
    (re.compile(r"\ball\b.*\bintellectual property\b", re.I), 1.5),
    (re.compile(r"\birrevocab", re.I), 2.0),
    (re.compile(r"\bperpetual\b", re.I), 2.0),
    (re.compile(r"\bunlimited\s+liabilit", re.I), 2.5),
    (re.compile(r"\bsole\s+discretion\b", re.I), 1.0),
    (re.compile(r"\bwithout\s+cause\b", re.I), 1.5),
    (re.compile(r"\bno\s+notice\b", re.I), 1.5),
    (re.compile(r"\bwaive\b", re.I), 1.0),
    (re.compile(r"\bforegoing\s+rights?\b", re.I), 1.0),
]


# ===================================================================
# Stage 1 — Deterministic clause segmentation
# ===================================================================

def segment_clauses(raw_text: str) -> list[str]:
    """Split raw OCR text into individual clause strings.

    Strategy: split on numbered headings (e.g. "1.", "1.1", "(a)") or double
    newlines, then drop fragments shorter than 20 characters (likely headers
    or artefacts).
    """
    if not raw_text.strip():
        return []

    # Split on common clause-boundary patterns
    parts = re.split(
        r"(?:\n\s*\n)"                       # double newline
        r"|(?=\n\s*\d+\.\d*\s)"              # numbered heading "1." or "1.1"
        r"|(?=\n\s*\([a-z]\)\s)",             # lettered sub-clause "(a)"
        raw_text,
    )

    clauses: list[str] = []
    for part in parts:
        cleaned = part.strip()
        # Drop very short fragments (likely headers, page numbers, etc.)
        if len(cleaned) >= 20:
            clauses.append(cleaned)

    # If splitting produced nothing useful, treat the whole text as one clause
    if not clauses and len(raw_text.strip()) >= 20:
        clauses = [raw_text.strip()]

    return clauses


# ===================================================================
# Stage 3 — Deterministic candidate matching
# ===================================================================

def match_candidates(clauses: list[str]) -> list[list[dict]]:
    """For each clause, return ranked candidate taxonomy matches.

    Uses simple keyword occurrence counting normalised by the number of
    keywords in each category.  Returns up to 3 candidates per clause.
    """
    results: list[list[dict]] = []
    for clause in clauses:
        lower = clause.lower()
        scores: list[tuple[str, float]] = []
        for category, keywords in TAXONOMY_KEYWORDS.items():
            hits = sum(1 for kw in keywords if kw.lower() in lower)
            if hits > 0:
                score = round(hits / len(keywords), 3)
                scores.append((category, score))
        # Sort descending by score, take top 3
        scores.sort(key=lambda x: x[1], reverse=True)
        candidates = [
            {"category": cat, "score": sc}
            for cat, sc in scores[:3]
        ]
        # Always provide at least one candidate so the classification agent
        # has something to evaluate
        if not candidates:
            candidates = [{"category": "unknown", "score": 0.0}]
        results.append(candidates)
    return results


# ===================================================================
# Stage 5 — Deterministic risk scoring
# ===================================================================

def score_risk(
    clause_text: str,
    category: str,
    confidence: float,
) -> tuple[float, RiskLevel]:
    """Compute a 0-10 risk score and corresponding risk level.

    Combines a base weight for the category with additive bonuses for high-risk
    phrases found in the text, scaled by classification confidence.
    """
    base = _CATEGORY_RISK_WEIGHTS.get(category, 5.0)

    # Additive phrase bonuses
    bonus = 0.0
    for pattern, weight in _RISK_PHRASES:
        if pattern.search(clause_text):
            bonus += weight

    raw_score = (base + bonus) * confidence
    # Clamp to [0, 10]
    score = round(min(10.0, max(0.0, raw_score)), 2)

    if score >= 8.5:
        level = RiskLevel.CRITICAL
    elif score >= 6.5:
        level = RiskLevel.HIGH
    elif score >= 4.0:
        level = RiskLevel.MEDIUM
    else:
        level = RiskLevel.LOW

    return score, level


# ===================================================================
# Full pipeline orchestration
# ===================================================================

async def run_full_pipeline(raw_ocr_text: str) -> AnalysisReport:
    """Execute the complete clause-analysis pipeline.

    Stage 0 checks the file cache — on a hit the result is returned instantly
    with zero LLM calls.  Stages 1, 3, 5 are deterministic (pure Python).
    Stages 2, 4, 6 are LLM-backed agents via Featherless.ai.
    Stage 7 saves the result to cache for future instant retrieval.
    """
    # --- Stage 0: Cache lookup ---
    text_hash = compute_hash(raw_ocr_text)
    cached = get_cached_response(text_hash)
    if cached is not None:
        logger.info("[CACHE HIT] Returning cached result for hash %s…%s", text_hash[:8], text_hash[-4:])
        return AnalysisReport(**cached)
    
    logger.info("[CACHE MISS] Running analysis pipeline for hash %s…%s", text_hash[:8], text_hash[-4:])

    # --- Stage 1: Segmentation (deterministic) ---
    raw_clauses = segment_clauses(raw_ocr_text)
    if not raw_clauses:
        empty_report = AnalysisReport(
            clauses=[],
            overall_risk_score=0.0,
            overall_risk_level=RiskLevel.LOW,
            negotiation_script="No clauses detected in the provided document.",
            summary="The document appears to be empty or unreadable.",
        )
        # Cache even empty results to avoid re-processing blank documents
        _save_report(text_hash, empty_report)
        return empty_report

    logger.info("Stage 1 complete: segmented %d clauses.", len(raw_clauses))

    # --- Stage 2: Extraction Agent (LLM — OCR cleanup) ---
    cleaned_clauses = await run_extraction_agent(raw_clauses)
    logger.info("Stage 2 complete: extraction agent cleaned %d clauses.", len(cleaned_clauses))

    # --- Stage 3: Candidate matching (deterministic) ---
    candidates = match_candidates(cleaned_clauses)
    logger.info("Stage 3 complete: candidate matching done.")


    # --- Stage 4: Classification Agent (LLM — concurrent confirmation) ---
    sem = asyncio.Semaphore(3)  # Strictly limit to 3 concurrent API calls

    async def bounded_analyze(clause, cands):
        async with sem:
            return await classification_agent.analyze(clause, cands)

    tasks = [bounded_analyze(clause, cands) for clause, cands in zip(cleaned_clauses, candidates)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    classifications = []
    for res in results:
        if isinstance(res, Exception):
            logger.error("Classification task failed: %s", res)
            classifications.append({"best_match": "unknown", "confidence": 0.0, "reasoning": "Task failed"})
        else:
            classifications.append(res)
            
    logger.info("Stage 4 complete: classification agent confirmed %d clauses.", len(classifications))

    # --- Stage 5: Risk scoring (deterministic) ---
    scored_clauses: list[ClauseRiskScore] = []
    for idx, clause_text in enumerate(cleaned_clauses):
        # Safely access classification result (handle count mismatches)
        if idx < len(classifications):
            cls = classifications[idx]
        else:
            cls = {"best_match": "unknown", "confidence": 0.5, "reasoning": ""}

        category = cls["best_match"]
        confidence = cls["confidence"]
        reasoning = cls.get("reasoning", "")

        risk_score, risk_level = score_risk(clause_text, category, confidence)

        scored_clauses.append(
            ClauseRiskScore(
                clause_text=clause_text,
                classification=ClauseClassification(
                    category=category,
                    confidence=confidence,
                ),
                risk_level=risk_level,
                risk_score=risk_score,
                explanation=reasoning,
            )
        )

    # Compute overall risk as a weighted average (weight = individual score)
    if scored_clauses:
        total_weight = sum(c.risk_score for c in scored_clauses)
        if total_weight > 0:
            overall_risk = sum(c.risk_score ** 2 for c in scored_clauses) / total_weight
        else:
            overall_risk = 0.0
        overall_risk = round(min(10.0, max(0.0, overall_risk)), 2)
    else:
        overall_risk = 0.0

    if overall_risk >= 8.5:
        overall_level = RiskLevel.CRITICAL
    elif overall_risk >= 6.5:
        overall_level = RiskLevel.HIGH
    elif overall_risk >= 4.0:
        overall_level = RiskLevel.MEDIUM
    else:
        overall_level = RiskLevel.LOW

    logger.info("Stage 5 complete: overall_risk=%.2f (%s).", overall_risk, overall_level.value)

    # --- Stage 6: Explainer Agent (LLM — summary + negotiation script) ---
    flagged_for_explainer = [
        {
            "clause_text": c.clause_text,
            "category": c.classification.category,
            "risk_level": c.risk_level.value,
            "risk_score": c.risk_score,
            "explanation": c.explanation,
        }
        for c in scored_clauses
    ]

    explainer_result = await run_explainer_agent(flagged_for_explainer, overall_risk)
    logger.info("Stage 6 complete: explainer agent produced summary.")

    report = AnalysisReport(
        clauses=scored_clauses,
        overall_risk_score=overall_risk,
        overall_risk_level=overall_level,
        negotiation_script=explainer_result["negotiation_script"],
        summary=explainer_result["summary"],
    )

    # --- Stage 7: Cache save ---
    _save_report(text_hash, report)

    return report


def _save_report(text_hash: str, report: AnalysisReport) -> None:
    """Serialize and cache an AnalysisReport.  Non-fatal on error."""
    try:
        report_dict = report.model_dump() if hasattr(report, "model_dump") else report.dict()
        save_to_cache(text_hash, report_dict)
    except Exception as exc:
        logger.error("Failed to cache report for hash %s: %s", text_hash[:8], exc)
