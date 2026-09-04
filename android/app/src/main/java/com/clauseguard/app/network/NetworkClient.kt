package com.clauseguard.app.network

import com.clauseguard.app.BuildConfig
import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.engine.okhttp.OkHttp
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.request.forms.formData
import io.ktor.client.request.forms.submitFormWithBinaryData
import io.ktor.http.Headers
import io.ktor.http.HttpHeaders
import io.ktor.serialization.kotlinx.json.json
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

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

object NetworkClient {
    private val client = HttpClient(OkHttp) {
        install(ContentNegotiation) {
            json(Json { ignoreUnknownKeys = true })
        }
    }

    suspend fun analyzeContract(imageBytes: ByteArray, fileName: String): AnalysisReport {
        return client.submitFormWithBinaryData(
            url = "${BuildConfig.BASE_URL}/analyze-contract",
            formData = formData {
                append("file", imageBytes, Headers.build {
                    append(HttpHeaders.ContentDisposition, "filename=\"$fileName\"")
                    append(HttpHeaders.ContentType, "image/jpeg")
                })
            },
        ).body()
    }
}
