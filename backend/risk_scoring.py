"""
risk_scoring.py
Deterministic risk-scoring and analytics engine for contract clauses.
Uses Pandas for DataFrame-driven aggregation, groupby analytics, and
normalized scoring.  No LLM calls — pure arithmetic and Pandas operations.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Severity-level weight mapping
# ---------------------------------------------------------------------------

SEVERITY_WEIGHTS: dict[str, int] = {
    "low": 1,
    "medium": 3,
    "high": 5,
}


# ---------------------------------------------------------------------------
# Per-clause risk score
# ---------------------------------------------------------------------------


def compute_risk_score(
    similarity_score: float,
    severity_weight: float,
    category_frequency: float,
) -> float:
    """Compute a single clause's risk score on a 0-10 scale.

    # Formula rationale: similarity_score acts as a confidence gate (how well
    # the clause matches a known risky pattern), severity_weight captures the
    # inherent danger of the matched category, and category_frequency boosts
    # the score when multiple clauses in the same contract share the same
    # risk category — because repeated risky language signals intentional
    # one-sidedness rather than boilerplate.  The weights (0.45, 0.35, 0.20)
    # prioritise match confidence and inherent severity while still rewarding
    # pattern repetition.

    Formula:
        raw = (0.45 × similarity_score + 0.35 × severity_weight
               + 0.20 × category_frequency) × 10
        score = clamp(raw, 0, 10)

    Parameters
    ----------
    similarity_score:
        Cosine similarity between the clause and its best taxonomy match,
        expected in [0, 1].
    severity_weight:
        The severity_weight column from the matched taxonomy row,
        expected in [0, 1].
    category_frequency:
        Ratio of clauses in this contract that share the same risk category,
        expected in [0, 1].  For a single-clause contract this is 1.0;
        for 2 out of 5 clauses sharing a category it is 0.4.

    Returns
    -------
    float in [0.0, 10.0].
    """
    raw = (
        0.45 * _clamp01(similarity_score)
        + 0.35 * _clamp01(severity_weight)
        + 0.20 * _clamp01(category_frequency)
    ) * 10.0

    return round(_clamp(raw, 0.0, 10.0), 2)


# ---------------------------------------------------------------------------
# Overall contract risk score (list-based)
# ---------------------------------------------------------------------------


def compute_overall_risk(clause_scores: list[float]) -> float:
    """Aggregate per-clause risk scores into a single 0-100 overall score.

    The aggregation uses a **power-mean with exponent 2** (quadratic mean /
    RMS) so that a few high-risk clauses dominate more than a simple average
    would allow, reflecting the reality that one very dangerous clause can
    make an otherwise fair contract exploitative.

    Formula:
        overall = sqrt( mean( score_i² ) ) × 10

    The ×10 maps the per-clause 0-10 range into a 0-100 overall range.

    An empty list returns 0.0.

    Parameters
    ----------
    clause_scores:
        List of per-clause risk scores, each in [0, 10].

    Returns
    -------
    float in [0.0, 100.0].
    """
    if not clause_scores:
        return 0.0

    n = len(clause_scores)
    sum_of_squares = sum(s ** 2 for s in clause_scores)
    rms = math.sqrt(sum_of_squares / n)

    # Scale from 0-10 per-clause range to 0-100 overall range
    overall = rms * 10.0

    return round(_clamp(overall, 0.0, 100.0), 2)


# ---------------------------------------------------------------------------
# Pandas-driven risk analytics engine
# ---------------------------------------------------------------------------


def build_clause_dataframe(clauses: list[dict[str, Any]]) -> pd.DataFrame:
    """Convert a list of clause dictionaries into a scored Pandas DataFrame.

    Each input dict is expected to contain at minimum:
        - clause_text (str): the raw clause text
        - category (str): risk category label (e.g. "non_compete_overreach")
        - risk_level (str): one of "low", "medium", "high"

    Optional keys consumed if present:
        - similarity_score (float): cosine similarity from taxonomy matching
        - severity_weight (float): from taxonomy CSV

    The function adds computed columns:
        - severity_weight_num (int): numerical weight derived from risk_level
        - weighted_risk (float): severity_weight_num × similarity_score
        - category_frequency (float): proportion of clauses sharing this category
        - risk_score (float): per-clause score from compute_risk_score()

    Parameters
    ----------
    clauses:
        List of clause dictionaries from the classification pipeline.

    Returns
    -------
    pd.DataFrame with all original columns plus computed risk metrics.
    Empty input returns an empty DataFrame with the expected schema.
    """
    if not clauses:
        return pd.DataFrame(columns=[
            "clause_text", "category", "risk_level",
            "similarity_score", "severity_weight",
            "severity_weight_num", "weighted_risk",
            "category_frequency", "risk_score",
        ])

    df = pd.DataFrame(clauses)

    # Ensure required columns exist with safe defaults
    if "similarity_score" not in df.columns:
        df["similarity_score"] = 0.0
    if "severity_weight" not in df.columns:
        df["severity_weight"] = 0.0
    if "risk_level" not in df.columns:
        df["risk_level"] = "low"

    # Fill any NaN values in numeric columns
    df["similarity_score"] = pd.to_numeric(
        df["similarity_score"], errors="coerce"
    ).fillna(0.0)
    df["severity_weight"] = pd.to_numeric(
        df["severity_weight"], errors="coerce"
    ).fillna(0.0)

    # Map risk_level strings to numerical severity weights: LOW=1, MEDIUM=3, HIGH=5
    df["severity_weight_num"] = (
        df["risk_level"]
        .astype(str)
        .str.lower()
        .map(SEVERITY_WEIGHTS)
        .fillna(SEVERITY_WEIGHTS["low"])
        .astype(int)
    )

    # Weighted risk = severity numerical weight × similarity confidence
    df["weighted_risk"] = df["severity_weight_num"] * df["similarity_score"]

    # Category frequency: proportion of clauses sharing each category
    category_counts = df["category"].value_counts(normalize=True)
    df["category_frequency"] = df["category"].map(category_counts).fillna(0.0)

    # Compute per-clause risk score using the weighted formula
    df["risk_score"] = df.apply(
        lambda row: compute_risk_score(
            similarity_score=float(row["similarity_score"]),
            severity_weight=float(row["severity_weight"]),
            category_frequency=float(row["category_frequency"]),
        ),
        axis=1,
    )

    return df


def aggregate_risk_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Group clauses by risk category and compute aggregate risk metrics.

    For each category, computes:
        - clause_count: number of clauses in the category
        - total_weighted_risk: sum of weighted_risk values
        - mean_risk_score: average per-clause risk score
        - max_risk_score: highest per-clause risk score
        - severity_weight_sum: total numerical severity weight

    Parameters
    ----------
    df:
        DataFrame produced by build_clause_dataframe().

    Returns
    -------
    pd.DataFrame grouped by category with aggregated metrics,
    sorted by total_weighted_risk descending.
    Empty input returns an empty DataFrame with the expected schema.
    """
    if df.empty:
        return pd.DataFrame(columns=[
            "category", "clause_count", "total_weighted_risk",
            "mean_risk_score", "max_risk_score", "severity_weight_sum",
        ])

    aggregated = (
        df.groupby("category", as_index=False)
        .agg(
            clause_count=("clause_text", "count"),
            total_weighted_risk=("weighted_risk", "sum"),
            mean_risk_score=("risk_score", "mean"),
            max_risk_score=("risk_score", "max"),
            severity_weight_sum=("severity_weight_num", "sum"),
        )
        .reset_index(drop=True)
        .sort_values("total_weighted_risk", ascending=False)
        .reset_index(drop=True)
    )

    return aggregated


def normalize_overall_score(df: pd.DataFrame) -> float:
    """Compute a normalized 0-100 overall risk score from a clause DataFrame.

    # Normalization rationale: the raw sum of weighted_risk values is unbounded
    # (it grows with clause count), so we divide by the theoretical maximum
    # (all clauses at HIGH severity × perfect similarity) to produce a ratio,
    # then scale to 0-100.  This ensures comparability across contracts of
    # different lengths.

    Formula:
        max_possible = num_clauses × max_severity_weight (5) × 1.0
        normalized   = (sum(weighted_risk) / max_possible) × 100
        score        = clamp(normalized, 0, 100)

    Parameters
    ----------
    df:
        DataFrame produced by build_clause_dataframe().

    Returns
    -------
    float in [0.0, 100.0].  Returns 0.0 for empty DataFrames.
    """
    if df.empty:
        return 0.0

    total_weighted = float(df["weighted_risk"].sum())
    max_severity = max(SEVERITY_WEIGHTS.values())  # 5
    max_possible = len(df) * max_severity * 1.0  # perfect similarity = 1.0

    if max_possible == 0.0:
        return 0.0

    normalized = (total_weighted / max_possible) * 100.0
    return round(_clamp(normalized, 0.0, 100.0), 2)


def compute_risk_metrics(clauses: list[dict[str, Any]]) -> dict[str, Any]:
    """End-to-end risk analytics: build DataFrame, aggregate, normalize, and
    return a structured metrics dictionary ready for API response injection.

    Parameters
    ----------
    clauses:
        List of clause dictionaries from the classification pipeline.
        Each dict should contain: clause_text, category, risk_level,
        and optionally similarity_score and severity_weight.

    Returns
    -------
    dict with keys:
        - overall_risk_score (float): normalized 0-100 score
        - overall_risk_level (str): "low" / "medium" / "high"
        - clause_count (int): total number of clauses analysed
        - category_breakdown (list[dict]): per-category aggregated metrics
        - per_clause_scores (list[dict]): each clause with its computed risk_score
        - highest_risk_clause (dict | None): the single riskiest clause
    """
    df = build_clause_dataframe(clauses)

    if df.empty:
        return {
            "overall_risk_score": 0.0,
            "overall_risk_level": "low",
            "clause_count": 0,
            "category_breakdown": [],
            "per_clause_scores": [],
            "highest_risk_clause": None,
        }

    # Aggregate by category
    category_agg = aggregate_risk_by_category(df)

    # Normalized overall score (0-100)
    overall_score = normalize_overall_score(df)

    # Derive overall risk level from the normalized score
    if overall_score >= 60.0:
        overall_level = "high"
    elif overall_score >= 30.0:
        overall_level = "medium"
    else:
        overall_level = "low"

    # Per-clause score summaries
    per_clause = df[["clause_text", "category", "risk_level", "risk_score"]].to_dict(
        orient="records"
    )

    # Identify the single highest-risk clause
    highest_idx = df["risk_score"].idxmax()
    highest_row = df.loc[highest_idx]
    highest_risk_clause = {
        "clause_text": str(highest_row["clause_text"]),
        "category": str(highest_row["category"]),
        "risk_level": str(highest_row["risk_level"]),
        "risk_score": float(highest_row["risk_score"]),
    }

    return {
        "overall_risk_score": overall_score,
        "overall_risk_level": overall_level,
        "clause_count": len(df),
        "category_breakdown": category_agg.to_dict(orient="records"),
        "per_clause_scores": per_clause,
        "highest_risk_clause": highest_risk_clause,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _clamp(value: float, lo: float, hi: float) -> float:
    """Clamp *value* to the interval [lo, hi]."""
    return max(lo, min(hi, value))


def _clamp01(value: float) -> float:
    """Clamp *value* to [0, 1]."""
    return _clamp(value, 0.0, 1.0)
