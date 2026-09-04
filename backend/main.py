from __future__ import annotations

import logging
import io

import pypdf
import docx
from fastapi import FastAPI, File, HTTPException, UploadFile
import openai

from schemas import AnalysisReport
from pipeline import run_full_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

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
    except openai.APITimeoutError:
        logger.exception("Upstream LLM provider timed out for file: %s", file.filename)
        raise HTTPException(
            status_code=503,
            detail="The analysis engine timed out while processing your contract. Please try again later.",
        )
    except openai.RateLimitError:
        logger.exception("Upstream LLM provider rate limit exceeded for file: %s", file.filename)
        raise HTTPException(
            status_code=503,
            detail="The analysis engine is currently experiencing high traffic. Please try again in a few minutes.",
        )
    except (openai.APIStatusError, openai.APIConnectionError):
        logger.exception("Upstream LLM provider returned an API error for file: %s", file.filename)
        raise HTTPException(
            status_code=503,
            detail="The analysis engine is temporarily unavailable. Please try again later.",
        )
    except Exception:
        logger.exception("Pipeline failed unexpectedly for file: %s", file.filename)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during contract analysis. Please try again.",
        )

    return report


@app.post("/analyze-file", response_model=AnalysisReport)
async def analyze_file(file: UploadFile = File(...)):
    """Analyse an uploaded contract document (PDF or DOCX).

    Extracts text from the file and feeds it through the full six-stage analysis pipeline.
    """
    raw_bytes = await file.read()

    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    
    filename = file.filename or ""
    filename_lower = filename.lower()

    raw_text = ""

    if filename_lower.endswith(".pdf") or file.content_type == "application/pdf":
        try:
            reader = pypdf.PdfReader(io.BytesIO(raw_bytes))
            raw_text = "\n\n".join([page.extract_text() or "" for page in reader.pages])
        except Exception as exc:
            logger.exception("Failed to open PDF file: %s", filename)
            raise HTTPException(status_code=415, detail="The uploaded file is not a valid PDF or is corrupted.")
            
    elif filename_lower.endswith(".docx") or file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        try:
            doc = docx.Document(io.BytesIO(raw_bytes))
            extracted_text = []
            for para in doc.paragraphs:
                if para.text.strip():
                    extracted_text.append(para.text)
            raw_text = "\n\n".join(extracted_text)
        except Exception as exc:
            logger.exception("Failed to open DOCX file: %s", filename)
            raise HTTPException(status_code=415, detail="The uploaded file is not a valid DOCX or is corrupted.")
            
    else:
        raise HTTPException(status_code=415, detail="Unsupported file format. Please upload a .pdf or .docx file.")

    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="Uploaded file contains no readable text. It might be a scanned image without OCR.")

    try:
        report = await run_full_pipeline(raw_text)
    except openai.APITimeoutError:
        logger.exception("Upstream LLM provider timed out for file: %s", filename)
        raise HTTPException(
            status_code=503,
            detail="The analysis engine timed out while processing your contract. Please try again later.",
        )
    except openai.RateLimitError:
        logger.exception("Upstream LLM provider rate limit exceeded for file: %s", filename)
        raise HTTPException(
            status_code=503,
            detail="The analysis engine is currently experiencing high traffic. Please try again in a few minutes.",
        )
    except (openai.APIStatusError, openai.APIConnectionError):
        logger.exception("Upstream LLM provider returned an API error for file: %s", filename)
        raise HTTPException(
            status_code=503,
            detail="The analysis engine is temporarily unavailable. Please try again later.",
        )
    except Exception:
        logger.exception("Pipeline failed unexpectedly for file: %s", filename)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during contract analysis. Please try again.",
        )

    return report

if __name__ == "__main__":
    import os
    import uvicorn
    
    # Render dynamically assigns a PORT environment variable.
    # We default to 8000 for local development.
    port = int(os.environ.get("PORT", 8000))
    
    # Bind to 0.0.0.0 to expose the server to the outside world
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
