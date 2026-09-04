package com.clauseguard.app.models

import kotlinx.serialization.Serializable

@Serializable
data class ClauseInput(
    val text: String,
    val page: Int? = null
)

@Serializable
data class ClauseClassification(
    val category: String,
    val confidence: Double,
)

@Serializable
data class ClauseRiskScore(
    val clause_text: String,
    val classification: ClauseClassification,
    val risk_level: String,
    val risk_score: Double,
    val explanation: String,
)

@Serializable
data class AnalysisReport(
    val clauses: List<ClauseRiskScore>,
    val overall_risk_score: Double,
    val overall_risk_level: String,
    val negotiation_script: String,
    val summary: String,
)
