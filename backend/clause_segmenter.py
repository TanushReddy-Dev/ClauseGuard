"""
clause_segmenter.py
Splits raw contract text (e.g. from OCR) into clause-level units.

Strategy (applied in order of priority):
1. Numbered-clause patterns  — "1.", "1)", "Section 1", "Article I", "(a)", etc.
2. Paragraph-break heuristics — double newlines separating substantive blocks.
3. Sentence-based fallback    — split on sentence-ending punctuation when
   neither numbering nor paragraph breaks yield multiple segments.
"""

from __future__ import annotations

import re


# ---------------------------------------------------------------------------
# Compiled regex patterns
# ---------------------------------------------------------------------------

# Matches common numbered/lettered clause openers at the start of a line:
#   "1."  "1)"  "(1)"  "(a)"  "a."  "a)"
#   "Section 1"  "SECTION 1.2"  "Article I"  "ARTICLE IV"
#   "Clause 3"   "CLAUSE 3.1"
_NUMBERED_CLAUSE_RE = re.compile(
    r"""
    (?:^|\n)                        # beginning of text or newline
    \s*                             # optional leading whitespace
    (?:
        (?:Section|SECTION|Article|ARTICLE|Clause|CLAUSE)\s+  # keyword prefix
        (?:[IVXLC]+|\d+(?:\.\d+)*)  # Roman numeral or decimal numbering
    |
        \(?\s*                      # optional opening paren
        (?:\d{1,3}(?:\.\d{1,3})*|[a-zA-Z])  # "1", "1.2", "a", "B"
        \s*[.)]\s*                  # closing delimiter: "." or ")"
    )
    """,
    re.VERBOSE,
)

# A "paragraph break" is two or more consecutive newlines (possibly with
# whitespace in between), which is the most common visual separator in OCR'd
# contract text.
_PARAGRAPH_BREAK_RE = re.compile(r"\n\s*\n")

# Sentence-ending punctuation followed by whitespace or end-of-string.
# Handles common abbreviations by requiring the preceding token to be
# at least two characters (avoids splitting on "e.g." or "U.S.").
_SENTENCE_END_RE = re.compile(
    r"(?<=[a-zA-Z]{2}[.!?])\s+(?=[A-Z])"
)

# Minimum character length for a segment to be considered a real clause
# (filters out stray headings, page numbers, etc.).
_MIN_CLAUSE_LENGTH = 20


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _clean(text: str) -> str:
    """Normalize whitespace within a clause while preserving single newlines."""
    text = text.strip()
    # Collapse runs of spaces/tabs (but not newlines) into one space
    text = re.sub(r"[^\S\n]+", " ", text)
    # Collapse 3+ newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def _is_valid_clause(segment: str) -> bool:
    """Return True if the segment is long enough to be a meaningful clause."""
    return len(segment.strip()) >= _MIN_CLAUSE_LENGTH


def _split_by_numbered_clauses(text: str) -> list[str]:
    """Split text on numbered-clause openers and return the segments."""
    # Find all match positions
    matches = list(_NUMBERED_CLAUSE_RE.finditer(text))
    if len(matches) < 2:
        # A single match (or none) means numbered splitting is not useful
        return []

    segments: list[str] = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        segment = text[start:end]
        segments.append(_clean(segment))

    return [s for s in segments if _is_valid_clause(s)]


def _split_by_paragraphs(text: str) -> list[str]:
    """Split text on double-newline paragraph breaks."""
    parts = _PARAGRAPH_BREAK_RE.split(text)
    return [_clean(p) for p in parts if _is_valid_clause(p)]


def _split_by_sentences(text: str) -> list[str]:
    """Fallback: split text on sentence boundaries."""
    parts = _SENTENCE_END_RE.split(text)
    # Re-join very short fragments (< _MIN_CLAUSE_LENGTH) with the next segment
    merged: list[str] = []
    buffer = ""
    for part in parts:
        candidate = (buffer + " " + part).strip() if buffer else part.strip()
        if len(candidate) < _MIN_CLAUSE_LENGTH:
            buffer = candidate
        else:
            merged.append(_clean(candidate))
            buffer = ""
    # Flush remaining buffer
    if buffer and _is_valid_clause(buffer):
        merged.append(_clean(buffer))
    elif buffer and merged:
        # Append short trailing fragment to the last clause
        merged[-1] = _clean(merged[-1] + " " + buffer)

    return merged


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def segment_into_clauses(raw_text: str) -> list[str]:
    """Split raw contract text into clause-level units.

    The function tries three strategies in priority order:
    1. **Numbered clauses** — splits on patterns like "1.", "Section 2",
       "Article III", "(a)", etc.
    2. **Paragraph breaks** — splits on double-newline boundaries.
    3. **Sentence fallback** — splits on sentence-ending punctuation when
       neither of the above yields multiple segments.

    Parameters
    ----------
    raw_text:
        The full text of a contract (typically from OCR output).

    Returns
    -------
    list[str]  — ordered list of clause strings, each stripped and normalized.
    An empty input returns an empty list.
    """
    if not raw_text or not raw_text.strip():
        return []

    text = raw_text.strip()

    # Strategy 1: numbered clauses
    clauses = _split_by_numbered_clauses(text)
    if len(clauses) >= 2:
        return clauses

    # Strategy 2: paragraph breaks
    clauses = _split_by_paragraphs(text)
    if len(clauses) >= 2:
        return clauses

    # Strategy 3: sentence-based fallback
    clauses = _split_by_sentences(text)
    if clauses:
        return clauses

    # Last resort: return the whole text as a single clause if it's long enough
    if _is_valid_clause(text):
        return [_clean(text)]

    return []
