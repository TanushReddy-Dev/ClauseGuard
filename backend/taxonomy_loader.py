"""
taxonomy_loader.py
Loads the clause taxonomy CSV at module-import time and precomputes TF-IDF
vectors for fast in-memory similarity matching.  No external vector database
is required — all computation uses pandas + scikit-learn.
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

_CSV_PATH = os.environ.get(
    "CLAUSE_TAXONOMY_CSV",
    str(Path(__file__).resolve().parent / "data" / "clause_taxonomy.csv"),
)

# ---------------------------------------------------------------------------
# Load CSV and precompute TF-IDF at import time (once per process)
# ---------------------------------------------------------------------------

_taxonomy_df: pd.DataFrame = pd.read_csv(_CSV_PATH)

# Validate expected columns
_REQUIRED_COLUMNS = {"clause_text", "category", "severity_weight", "source_citation"}
_missing = _REQUIRED_COLUMNS - set(_taxonomy_df.columns)
if _missing:
    raise ValueError(
        f"Taxonomy CSV is missing required columns: {_missing}. "
        f"Found: {list(_taxonomy_df.columns)}"
    )

# Build TF-IDF matrix over the taxonomy clause texts
_vectorizer = TfidfVectorizer(
    lowercase=True,
    stop_words="english",
    ngram_range=(1, 2),
    max_features=10_000,
    sublinear_tf=True,
)

_taxonomy_tfidf_matrix = _vectorizer.fit_transform(
    _taxonomy_df["clause_text"].astype(str)
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_taxonomy_dataframe() -> pd.DataFrame:
    """Return a copy of the loaded taxonomy DataFrame."""
    return _taxonomy_df.copy()


def find_candidate_matches(clause_text: str, top_k: int = 3) -> list[dict]:
    """Return the *top_k* most similar taxonomy rows for a given clause.

    Each returned dict contains:
        - clause_text:      the matching taxonomy clause
        - category:         risk category label
        - severity_weight:  float in [0, 1]
        - source_citation:  legal reference
        - similarity_score: cosine similarity in [0, 1]

    Parameters
    ----------
    clause_text:
        Raw text of a single contract clause to match.
    top_k:
        Number of top matches to return (default 3).

    Returns
    -------
    list[dict] sorted by descending similarity score.
    """
    if not clause_text or not clause_text.strip():
        return []

    # Transform the query clause into the same TF-IDF space
    query_vector = _vectorizer.transform([clause_text])

    # Compute cosine similarity against every taxonomy entry
    similarities: np.ndarray = cosine_similarity(
        query_vector, _taxonomy_tfidf_matrix
    ).flatten()

    # Clamp top_k to the number of available taxonomy rows
    top_k = min(top_k, len(_taxonomy_df))

    # Get indices of the top-k highest similarity scores
    top_indices = similarities.argsort()[::-1][:top_k]

    results: list[dict] = []
    for idx in top_indices:
        row = _taxonomy_df.iloc[idx]
        results.append(
            {
                "clause_text": str(row["clause_text"]),
                "category": str(row["category"]),
                "severity_weight": float(row["severity_weight"]),
                "source_citation": str(row["source_citation"]),
                "similarity_score": round(float(similarities[idx]), 4),
            }
        )

    return results
