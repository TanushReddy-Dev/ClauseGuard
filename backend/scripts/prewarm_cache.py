#!/usr/bin/env python3
"""Pre-warm the ClauseGuard response cache with demo contracts.

Run this script before a live demo to populate the file cache so that the
first request for each demo contract returns instantly (zero LLM latency).

Usage:
    cd backend
    python scripts/prewarm_cache.py

The script calls run_full_pipeline for each demo contract.  On completion
each result is cached under its SHA-256 hash.  Subsequent API calls with
the same (normalised) contract text will return the cached result.
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys
import os

# Ensure the backend package root is on sys.path when running as a script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cache_layer import compute_hash, list_cached_hashes
from pipeline import run_full_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("prewarm")

# ---------------------------------------------------------------------------
# Demo contracts — realistic sample text covering common risky clauses.
# ---------------------------------------------------------------------------

DEMO_CONTRACTS: list[dict[str, str]] = [
    {
        "name": "Freelance Software Development Agreement",
        "text": """
FREELANCE SOFTWARE DEVELOPMENT AGREEMENT

1. Scope of Work
The Contractor shall design, develop, and deliver a web-based dashboard
application according to the specifications outlined in Exhibit A.

2. Payment Terms
The Company shall pay the Contractor a flat fee of $15,000, payable in three
installments. The Company reserves the right to withhold up to 25% of each
payment as a quality assurance hold until final acceptance. Withheld amounts
shall be released at the Company's sole discretion no earlier than 60 days
after project completion. Late payments by the Company shall not accrue
interest.

3. Intellectual Property Assignment
All intellectual property, inventions, and work product created by the
Contractor during the engagement — including source code, documentation,
designs, and algorithms — shall be the sole and exclusive property of the
Company in perpetuity. The Contractor irrevocably assigns all rights, title,
and interest in such work to the Company worldwide.

4. Non-Compete
The Contractor agrees not to engage in any competitive activity with the
Company or its affiliates for a period of 24 months following the termination
of this Agreement, within a 100-mile radius of any Company office.

5. Termination
The Company may terminate this Agreement at any time, without cause, by
providing 5 days written notice. Upon termination, the Contractor shall
deliver all completed and in-progress work. No additional compensation shall
be owed for incomplete milestones.
""",
    },
    {
        "name": "Gig Worker Services Agreement",
        "text": """
GIG WORKER SERVICES AGREEMENT

Section 1 — Engagement
The Worker is engaged as an independent contractor to provide delivery
services on behalf of the Platform. This agreement does not create an
employment relationship.

Section 2 — Compensation and Withholding
The Platform shall compensate the Worker on a per-delivery basis at rates
published in the Worker app. The Platform reserves the right to withhold
payment for any delivery that receives a customer complaint until
investigation is complete, at the Platform's sole discretion. Investigation
periods may extend up to 90 days. The Worker waives any claim to interest
on withheld funds.

Section 3 — Mandatory Arbitration
Any dispute arising out of or relating to this Agreement shall be resolved
exclusively through binding arbitration under the rules of the American
Arbitration Association. The arbitration shall take place in San Francisco,
California. The Worker irrevocably waives the right to trial by jury and the
right to participate in any class action, collective action, or
representative proceeding. Each party shall bear its own legal costs.

Section 4 — Liability Limitation
The Platform's total liability to the Worker under this Agreement shall not
exceed the total compensation paid to the Worker in the 30 days preceding
the claim. The Platform shall not be liable for any indirect, incidental,
consequential, or punitive damages under any circumstances.

Section 5 — Confidentiality
The Worker agrees to keep confidential all proprietary information, trade
secrets, routing algorithms, customer data, and pricing models disclosed
during the engagement. This obligation survives termination of the Agreement
in perpetuity.
""",
    },
    {
        "name": "Marketing Consultant Agreement",
        "text": """
MARKETING CONSULTANT RETAINER AGREEMENT

Article I — Services
The Consultant shall provide strategic marketing advisory services including
brand positioning, campaign planning, and performance analytics as directed
by the Company's Chief Marketing Officer.

Article II — Compensation
The Company shall pay the Consultant a monthly retainer of $5,000, due on
the first business day of each month. The Company may offset any amounts
owed against future invoices for any reason, including dissatisfaction with
deliverables, at its sole discretion. The Consultant shall not be entitled
to any bonus, equity, or benefits.

Article III — Non-Solicitation
For a period of 36 months following termination of this Agreement, the
Consultant shall not directly or indirectly solicit, recruit, or hire any
employee, contractor, or client of the Company. The Consultant shall not
interfere with any business relationship between the Company and its
customers or vendors.

Article IV — Governing Law and Dispute Resolution
This Agreement shall be governed by the laws of the State of Delaware.
Any dispute shall be submitted to binding arbitration in Wilmington,
Delaware. The prevailing party shall be entitled to recover reasonable
attorneys' fees. The Consultant waives all rights to a jury trial.

Article V — Indemnification
The Consultant shall indemnify and hold harmless the Company, its officers,
directors, and employees from any and all claims, damages, losses, and
expenses (including attorneys' fees) arising from the Consultant's
performance or breach of this Agreement. This indemnification obligation
is unlimited in scope and duration.
""",
    },
]


async def prewarm() -> None:
    """Run all demo contracts through the pipeline and cache the results."""
    total = len(DEMO_CONTRACTS)
    logger.info("Starting cache prewarm with %d demo contracts…", total)

    existing_hashes = set(list_cached_hashes())
    skipped = 0
    processed = 0

    for idx, contract in enumerate(DEMO_CONTRACTS, 1):
        name = contract["name"]
        text = contract["text"]
        text_hash = compute_hash(text)

        if text_hash in existing_hashes:
            logger.info(
                "[%d/%d] SKIP (already cached): %s [%s…%s]",
                idx, total, name, text_hash[:8], text_hash[-4:],
            )
            skipped += 1
            continue

        logger.info("[%d/%d] Processing: %s …", idx, total, name)

        try:
            report = await run_full_pipeline(text)
            processed += 1
            logger.info(
                "[%d/%d] DONE: %s — %d clauses, risk %.1f (%s)",
                idx, total, name,
                len(report.clauses),
                report.overall_risk_score,
                report.overall_risk_level.value,
            )
        except Exception as exc:
            logger.error("[%d/%d] FAILED: %s — %s", idx, total, name, exc)

    logger.info(
        "Prewarm complete: %d processed, %d skipped (already cached), %d total.",
        processed, skipped, total,
    )


if __name__ == "__main__":
    asyncio.run(prewarm())
