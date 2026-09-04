from __future__ import annotations

import logging

from fastapi import FastAPI, File, HTTPException, UploadFile

from schemas import AnalysisReport
from pipeline import run_full_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(title="ClauseGuard API")


@app.post("/analyze-contract", response_model=AnalysisReport)
async def analyze_contract(file: UploadFile = File(...)):
    """Analyse an uploaded contract document.

    Accepts any text-based file (PDF text layer, .txt, .docx extraction).
    The content is decoded as UTF-8 and fed through the full six-stage
    analysis pipeline (3 deterministic + 3 LLM-backed agents).
    """
    raw_bytes = await file.read()

    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Decode raw bytes — handle common encodings gracefully
    try:
        raw_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            raw_text = raw_bytes.decode("latin-1")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Unable to decode the uploaded file. Please upload a UTF-8 or Latin-1 text file.",
            )

    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="Uploaded file contains no readable text.")

    try:
        report = await run_full_pipeline(raw_text)
    except Exception:
        logging.getLogger(__name__).exception("Pipeline failed for file: %s", file.filename)
        raise HTTPException(
            status_code=502,
            detail="Contract analysis failed due to an upstream service error. Please try again.",
        )

    return report
