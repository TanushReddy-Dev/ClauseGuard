from schemas import AnalysisReport, ClauseRiskScore, ClauseClassification, RiskLevel

def get_demo_fallback_report() -> AnalysisReport:
    """Return a pre-baked high-risk sample contract JSON payload for demo safeguard."""
    return AnalysisReport(
        clauses=[
            ClauseRiskScore(
                clause_text="The Contractor agrees not to engage in any competitive activity with the Company or its affiliates for a period of 24 months following the termination of this Agreement, within a 100-mile radius of any Company office.",
                classification=ClauseClassification(
                    category="non-compete",
                    confidence=0.95,
                ),
                risk_level=RiskLevel.CRITICAL,
                risk_score=9.5,
                explanation="A 24-month, 100-mile non-compete is unusually broad and highly restrictive for a freelance agreement."
            ),
            ClauseRiskScore(
                clause_text="All intellectual property, inventions, and work product created by the Contractor during the engagement shall be the sole and exclusive property of the Company in perpetuity.",
                classification=ClauseClassification(
                    category="IP assignment",
                    confidence=0.92,
                ),
                risk_level=RiskLevel.HIGH,
                risk_score=7.0,
                explanation="Full IP assignment is standard but covers all work product in perpetuity, which may include unrelated personal projects."
            )
        ],
        overall_risk_score=8.25,
        overall_risk_level=RiskLevel.HIGH,
        negotiation_script="Dear [Party], I have reviewed the contract and have concerns regarding the non-compete clause. A 24-month restriction within a 100-mile radius is quite broad for an independent contractor role. I propose reducing the duration to 6 months and limiting the restriction to direct competitors. Additionally, regarding the IP assignment, I would like to clarify that it only applies to work created specifically for the Company and not to my personal projects. I look forward to discussing these points. Best regards, [Your Name]",
        summary="This contract presents a high risk primarily due to a highly restrictive 24-month non-compete clause. Additionally, the broad IP assignment clause could potentially claim ownership over your personal, unrelated projects."
    )
