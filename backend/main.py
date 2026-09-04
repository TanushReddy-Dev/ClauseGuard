from fastapi import FastAPI, File, UploadFile

from schemas import AnalysisReport, ClauseClassification, ClauseRiskScore, RiskLevel

app = FastAPI(title="ClauseGuard API")


@app.post("/analyze-contract", response_model=AnalysisReport)
async def analyze_contract(file: UploadFile = File(...)):
    _ = await file.read()  # consume upload; real OCR + analysis in later phase

    return AnalysisReport(
        clauses=[
            ClauseRiskScore(
                clause_text="Contractor agrees to a 24-month non-compete within a 100-mile radius.",
                classification=ClauseClassification(category="non-compete", confidence=0.95),
                risk_level=RiskLevel.HIGH,
                risk_score=8.5,
                explanation="Non-compete is unusually broad in both duration and geography for gig work.",
            ),
            ClauseRiskScore(
                clause_text="All intellectual property created during the engagement belongs to the Company.",
                classification=ClauseClassification(category="IP assignment", confidence=0.92),
                risk_level=RiskLevel.MEDIUM,
                risk_score=6.0,
                explanation="Full IP assignment is standard but may cover personal projects if not scoped.",
            ),
        ],
        overall_risk_score=7.25,
        overall_risk_level=RiskLevel.HIGH,
        negotiation_script=(
            "I'd like to discuss two clauses before signing. First, the non-compete — "
            "a 24-month, 100-mile restriction feels disproportionate for gig-based work. "
            "Could we narrow it to 6 months and direct competitors only? Second, the IP clause — "
            "can we add a carve-out for work unrelated to company projects?"
        ),
        summary=(
            "This contract contains a high-risk non-compete and a moderately risky "
            "IP assignment clause. Both are negotiable and commonly revised."
        ),
    )
