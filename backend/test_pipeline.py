"""End-to-end test for the ClauseGuard analysis pipeline.

Feeds sample contract text containing a wage-withholding clause and an
arbitration clause through run_full_pipeline and prints the resulting
AnalysisReport as formatted JSON.
"""
from __future__ import annotations

import asyncio
import json
import sys

from pipeline import run_full_pipeline

# ---------------------------------------------------------------------------
# Sample contract text — two realistic clauses likely to appear in gig/
# freelance agreements.  Includes minor OCR-style noise to exercise the
# extraction agent (e.g. "ternns" instead of "terms").
# ---------------------------------------------------------------------------
SAMPLE_CONTRACT = """
INDEPENDENT CONTRACTOR AGREEMENT

4.1 Wage Withholding and Payment Terms
The Company reserves the right to withhold up to 20% of any payment due to the
Contractor as a security deposit against potential damages, defective
deliverables, or breach of contract ternns. Withheld amounts shall be released
no earlier than 90 days following project completion, at the Company's sole
discretion. The Contractor waives all rights to interest on withheld funds.

5.2 Mandatory Binding Arbitration
Any dispute, claim, or controversy arising out of or relating to this Agreement
shall be resolved exclusively through binding arbitration administered by the
American Arbitration Association under its Commercial Arbitration Rules. The
arbitration shall take place in New York, New York. The Contractor irrevocably
waives the right to trial by jury and the right to participate in any class
action or collective proceeding. Each party shall bear its own costs and
attorneys' fees regardless of the outcome.
"""


async def main() -> None:
    print("=" * 72)
    print("ClauseGuard Pipeline — End-to-End Test")
    print("=" * 72)
    print()
    print("Input contract length:", len(SAMPLE_CONTRACT), "chars")
    print("Running full pipeline (3 LLM calls via Featherless.ai)...")
    print()

    try:
        report = await run_full_pipeline(SAMPLE_CONTRACT)
    except Exception as exc:
        print(f"PIPELINE FAILED: {exc}", file=sys.stderr)
        sys.exit(1)

    # Serialize the Pydantic model to formatted JSON
    report_json = report.model_dump_json(indent=2) if hasattr(report, "model_dump_json") else json.dumps(report.dict(), indent=2, default=str)

    print("Pipeline completed successfully!")
    print()
    print("-" * 72)
    print("AnalysisReport JSON:")
    print("-" * 72)
    print(report_json)
    print()

    # Quick sanity checks
    assert len(report.clauses) > 0, "Expected at least one scored clause"
    assert report.overall_risk_score >= 0.0, "Risk score should be non-negative"
    assert report.summary, "Summary should not be empty"
    assert report.negotiation_script, "Negotiation script should not be empty"

    print("=" * 72)
    print(f"ALL CHECKS PASSED — {len(report.clauses)} clauses scored, "
          f"overall risk: {report.overall_risk_score} ({report.overall_risk_level.value})")
    print("=" * 72)


if __name__ == "__main__":
    asyncio.run(main())
