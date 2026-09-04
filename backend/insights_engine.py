"""
insights_engine.py
Macro-insights aggregation module that analyses a user's historical contract
reports to surface recurring vulnerability patterns and risk trends.

Uses Pandas for DataFrame construction, groupby aggregation, and index
resetting.  No LLM calls — pure deterministic analytics.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Human-readable labels for predatory categories
_CATEGORY_LABELS: dict[str, str] = {
    "unilateral_termination": "Unilateral Termination",
    "wage_withholding": "Wage Withholding / Deduction",
    "non_compete_overreach": "Non-Compete Overreach",
    "forced_arbitration": "Forced Arbitration",
    "ip_assignment": "IP Assignment",
    "liability_indemnification": "Liability / Indemnification",
    "jurisdiction_abuse": "Jurisdiction Abuse",
    "non-compete": "Non-Compete",
    "confidentiality": "Confidentiality",
}

# Number of top predatory categories to surface in insights
_TOP_K_CATEGORIES = 3


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _flatten_reports_to_clauses(
    historical_reports: list[dict[str, Any]],
) -> pd.DataFrame:
    """Flatten a list of AnalysisReport JSONs into a single clause-level DataFrame.

    Each row represents one clause from one contract. The contract index
    (report_index) is preserved so we can count distinct contracts per category.

    Expected structure of each report dict (matching AnalysisReport schema):
        {
            "clauses": [
                {
                    "clause_text": "...",
                    "classification": {"category": "...", "confidence": 0.95},
                    "risk_level": "high",
                    "risk_score": 8.5,
                    "explanation": "..."
                },
                ...
            ],
            "overall_risk_score": 7.25,
            "overall_risk_level": "high",
            ...
        }

    Returns an empty DataFrame with the expected schema if input is empty or
    contains no clauses.
    """
    rows: list[dict[str, Any]] = []

    for report_idx, report in enumerate(historical_reports):
        clauses = report.get("clauses", [])
        overall_score = report.get("overall_risk_score", 0.0)
        overall_level = report.get("overall_risk_level", "low")

        for clause in clauses:
            # Support both nested classification dict and flat category key
            classification = clause.get("classification", {})
            if isinstance(classification, dict):
                category = classification.get("category", "unknown")
                confidence = classification.get("confidence", 0.0)
            else:
                category = clause.get("category", "unknown")
                confidence = clause.get("confidence", 0.0)

            rows.append(
                {
                    "report_index": report_idx,
                    "clause_text": clause.get("clause_text", ""),
                    "category": str(category).lower().strip(),
                    "confidence": float(confidence),
                    "risk_level": str(
                        clause.get("risk_level", "low")
                    ).lower().strip(),
                    "risk_score": float(clause.get("risk_score", 0.0)),
                    "explanation": clause.get("explanation", ""),
                    "contract_overall_score": float(overall_score),
                    "contract_overall_level": str(overall_level).lower().strip(),
                }
            )

    if not rows:
        return pd.DataFrame(
            columns=[
                "report_index",
                "clause_text",
                "category",
                "confidence",
                "risk_level",
                "risk_score",
                "explanation",
                "contract_overall_score",
                "contract_overall_level",
            ]
        )

    return pd.DataFrame(rows)


def _compute_category_frequency_pct(
    df: pd.DataFrame, total_contracts: int
) -> pd.DataFrame:
    """Compute per-category stats: how many contracts contain each category,
    expressed as a percentage of the user's total analysed contracts.

    Returns a DataFrame with columns:
        - category
        - contracts_affected (int): distinct contracts containing this category
        - frequency_pct (float): percentage of contracts affected (0-100)
        - total_flags (int): total clause occurrences across all contracts
        - mean_risk_score (float): average risk score for this category
        - max_risk_score (float): highest risk score seen for this category
        - mean_confidence (float): average classification confidence
    """
    if df.empty or total_contracts == 0:
        return pd.DataFrame(
            columns=[
                "category",
                "contracts_affected",
                "frequency_pct",
                "total_flags",
                "mean_risk_score",
                "max_risk_score",
                "mean_confidence",
            ]
        )

    agg = (
        df.groupby("category", as_index=False)
        .agg(
            contracts_affected=("report_index", "nunique"),
            total_flags=("clause_text", "count"),
            mean_risk_score=("risk_score", "mean"),
            max_risk_score=("risk_score", "max"),
            mean_confidence=("confidence", "mean"),
        )
        .reset_index(drop=True)
    )

    agg["frequency_pct"] = round(
        (agg["contracts_affected"] / total_contracts) * 100.0, 1
    )

    # Round float columns for clean output
    agg["mean_risk_score"] = agg["mean_risk_score"].round(2)
    agg["max_risk_score"] = agg["max_risk_score"].round(2)
    agg["mean_confidence"] = agg["mean_confidence"].round(2)

    # Sort by frequency descending, then by mean_risk_score descending
    agg = (
        agg.sort_values(
            ["frequency_pct", "mean_risk_score"], ascending=[False, False]
        )
        .reset_index(drop=True)
    )

    return agg


def _format_category_label(category: str) -> str:
    """Return a human-readable label for a category slug."""
    return _CATEGORY_LABELS.get(
        category, category.replace("_", " ").title()
    )


def _build_trend_narrative(
    category: str, frequency_pct: float, mean_risk: float
) -> str:
    """Generate a plain-language trend sentence for a category."""
    label = _format_category_label(category)

    if frequency_pct >= 75.0:
        frequency_word = "nearly all"
    elif frequency_pct >= 50.0:
        frequency_word = "the majority"
    elif frequency_pct >= 25.0:
        frequency_word = "a significant portion"
    else:
        frequency_word = "some"

    if mean_risk >= 7.0:
        severity_phrase = "with consistently high risk scores"
    elif mean_risk >= 4.0:
        severity_phrase = "with moderate risk scores"
    else:
        severity_phrase = "though typically at lower risk levels"

    return (
        f'"{label}" appears in {frequency_pct:.0f}% of your contracts '
        f"({frequency_word}), {severity_phrase} (avg {mean_risk:.1f}/10)."
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_user_insights(
    historical_reports: list[dict[str, Any]],
) -> dict[str, Any]:
    """Analyse a user's historical contract reports and return macro-level
    risk insights.

    Converts a list of past AnalysisReport JSON dicts into a Pandas DataFrame,
    performs groupby aggregations with proper index resetting, and identifies
    the top 3 most frequently flagged predatory categories.

    Parameters
    ----------
    historical_reports:
        List of AnalysisReport-shaped dicts.  Each must have a ``clauses``
        list (matching the ClauseRiskScore schema) and an
        ``overall_risk_score`` float.

    Returns
    -------
    dict with keys:
        - contracts_analysed (int): total number of reports processed
        - total_clauses_flagged (int): total clause-level flags across all reports
        - average_contract_risk (float): mean overall_risk_score across contracts
        - risk_trend (str): "improving" / "stable" / "worsening" based on the
          first-half vs second-half average of contract scores
        - top_predatory_categories (list[dict]): top 3 categories by frequency,
          each with category, label, frequency_pct, contracts_affected,
          total_flags, mean_risk_score, max_risk_score, narrative
        - all_category_stats (list[dict]): full breakdown for every category
        - highest_single_risk (dict | None): the single clause with the
          highest risk_score across all reports
    """
    if not historical_reports:
        return {
            "contracts_analysed": 0,
            "total_clauses_flagged": 0,
            "average_contract_risk": 0.0,
            "risk_trend": "stable",
            "top_predatory_categories": [],
            "all_category_stats": [],
            "highest_single_risk": None,
        }

    total_contracts = len(historical_reports)

    # Flatten all reports into a single clause-level DataFrame
    df = _flatten_reports_to_clauses(historical_reports)

    if df.empty:
        return {
            "contracts_analysed": total_contracts,
            "total_clauses_flagged": 0,
            "average_contract_risk": 0.0,
            "risk_trend": "stable",
            "top_predatory_categories": [],
            "all_category_stats": [],
            "highest_single_risk": None,
        }

    # ------------------------------------------------------------------
    # Contract-level aggregation
    # ------------------------------------------------------------------

    contract_scores = (
        df.groupby("report_index", as_index=False)
        .agg(overall_score=("contract_overall_score", "first"))
        .reset_index(drop=True)
    )

    avg_contract_risk = round(float(contract_scores["overall_score"].mean()), 2)

    # Risk trend: compare first half vs second half of contract history
    midpoint = max(1, total_contracts // 2)
    first_half_scores = contract_scores.loc[
        contract_scores["report_index"] < midpoint, "overall_score"
    ]
    second_half_scores = contract_scores.loc[
        contract_scores["report_index"] >= midpoint, "overall_score"
    ]

    first_mean = float(first_half_scores.mean()) if len(first_half_scores) > 0 else 0.0
    second_mean = (
        float(second_half_scores.mean()) if len(second_half_scores) > 0 else 0.0
    )

    trend_delta = second_mean - first_mean
    if trend_delta > 0.5:
        risk_trend = "worsening"
    elif trend_delta < -0.5:
        risk_trend = "improving"
    else:
        risk_trend = "stable"

    # ------------------------------------------------------------------
    # Category-level aggregation (groupby + reset_index)
    # ------------------------------------------------------------------

    category_stats = _compute_category_frequency_pct(df, total_contracts)

    # Build top-K predatory categories with narratives
    top_categories: list[dict[str, Any]] = []
    for _, row in category_stats.head(_TOP_K_CATEGORIES).iterrows():
        cat = str(row["category"])
        freq = float(row["frequency_pct"])
        mean_risk = float(row["mean_risk_score"])

        top_categories.append(
            {
                "category": cat,
                "label": _format_category_label(cat),
                "frequency_pct": freq,
                "contracts_affected": int(row["contracts_affected"]),
                "total_flags": int(row["total_flags"]),
                "mean_risk_score": mean_risk,
                "max_risk_score": float(row["max_risk_score"]),
                "narrative": _build_trend_narrative(cat, freq, mean_risk),
            }
        )

    # Full category stats as list of dicts
    all_stats = category_stats.to_dict(orient="records")

    # ------------------------------------------------------------------
    # Highest single risk clause across all history
    # ------------------------------------------------------------------

    highest_idx = df["risk_score"].idxmax()
    highest_row = df.loc[highest_idx]
    highest_single_risk = {
        "clause_text": str(highest_row["clause_text"]),
        "category": str(highest_row["category"]),
        "risk_level": str(highest_row["risk_level"]),
        "risk_score": float(highest_row["risk_score"]),
        "from_contract_index": int(highest_row["report_index"]),
    }

    return {
        "contracts_analysed": total_contracts,
        "total_clauses_flagged": len(df),
        "average_contract_risk": avg_contract_risk,
        "risk_trend": risk_trend,
        "top_predatory_categories": top_categories,
        "all_category_stats": all_stats,
        "highest_single_risk": highest_single_risk,
    }
