from __future__ import annotations

"""File-based response cache for the ClauseGuard analysis pipeline.

Provides SHA-256-based deduplication of contract analyses.  When the same
contract text (after normalisation) is submitted twice the cached result is
returned instantly — no LLM calls, no latency.

The cache is stored as individual JSON files under a configurable directory
(default: ``backend/.cache/``).  Each file is named ``<sha256_hex>.json``.
Using one-file-per-entry avoids locking issues on concurrent writes and makes
manual inspection / pruning trivial.
"""

import hashlib
import string
import json
import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# Default cache directory lives alongside the backend source.
# Override via the CLAUSEGUARD_CACHE_DIR environment variable.
_CACHE_DIR = Path(
    os.environ.get(
        "CLAUSEGUARD_CACHE_DIR",
        str(Path(__file__).resolve().parent / ".cache"),
    )
)


def _ensure_cache_dir() -> Path:
    """Create the cache directory if it doesn't exist."""
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return _CACHE_DIR




def compute_hash(raw_text: str) -> str:
    """Return the SHA-256 hex digest of the *normalised* contract text."""
    normalised = normalize_text(raw_text)
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()


def _cache_path(text_hash: str) -> Path:
    """Return the filesystem path for a given hash."""
    return _ensure_cache_dir() / f"{text_hash}.json"


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def get_cached_response(text_hash: str) -> dict | None:
    """Look up a cached AnalysisReport by its text hash.

    Returns the report dict on cache hit, or ``None`` on miss / corrupt file.
    """
    path = _cache_path(text_hash)
    if not path.is_file():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            logger.warning("Cache file %s contains non-dict data; treating as miss.", path)
            return None
        logger.info("Cache HIT for hash %s…%s", text_hash[:8], text_hash[-4:])
        return data
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to read cache file %s: %s", path, exc)
        return None


def save_to_cache(text_hash: str, report_dict: dict) -> None:
    """Persist an AnalysisReport dict to the file cache.

    Writes atomically (write-to-temp then rename) to avoid serving a
    half-written file on concurrent reads.
    """
    path = _cache_path(text_hash)
    tmp_path = path.with_suffix(".tmp")

    try:
        tmp_path.write_text(
            json.dumps(report_dict, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp_path.replace(path)  # atomic on POSIX
        logger.info("Cache SAVE for hash %s…%s", text_hash[:8], text_hash[-4:])
    except OSError as exc:
        logger.error("Failed to write cache file %s: %s", path, exc)
        # Non-fatal — the pipeline result is still returned to the caller.
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


def list_cached_hashes() -> list[str]:
    """Return all cached text hashes (for diagnostics / prewarm verification)."""
    cache_dir = _ensure_cache_dir()
    return sorted(
        p.stem
        for p in cache_dir.glob("*.json")
        if len(p.stem) == 64  # SHA-256 hex length
    )
import string

def normalize_text(raw_text: str) -> str:
    """Normalize contract text for consistent hashing.

    Strips leading/trailing whitespace, collapses runs of whitespace to a
    single space, removes punctuation, and lowercases.  This means trivially
    reformatted or slightly noisy OCR copies of the same contract hit the
    same cache entry.
    """
    text = raw_text.strip()
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text)
    return text.strip()
