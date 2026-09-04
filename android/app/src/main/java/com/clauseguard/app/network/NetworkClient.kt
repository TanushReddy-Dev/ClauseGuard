package com.clauseguard.app.network

import com.clauseguard.app.models.AnalysisReport
import com.clauseguard.app.models.ClauseInput
import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.http.POST
import java.util.concurrent.TimeUnit

sealed class Result<out T> {
    data class Success<out T>(val data: T) : Result<T>()
    object Loading : Result<Nothing>()
    data class Error(val message: String) : Result<Nothing>()
}

interface ClauseGuardApi {
    @POST("analyze-contract")
    suspend fun analyzeContract(
        @retrofit2.http.Body input: ClauseInput,
    ): AnalysisReport
}

object NetworkClient {
    private val json = Json { ignoreUnknownKeys = true }

    private val okHttp = OkHttpClient.Builder()
        .connectTimeout(0, TimeUnit.SECONDS)
        .readTimeout(0, TimeUnit.SECONDS)
        .writeTimeout(0, TimeUnit.SECONDS)
        .build()

    private val retrofit: Retrofit = Retrofit.Builder()
        .baseUrl("https://ice-copyrighted-clinical-univ.trycloudflare.com/")
        .client(okHttp)
        .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
        .build()

    val api: ClauseGuardApi = retrofit.create(ClauseGuardApi::class.java)

    suspend fun analyzeContract(text: String): AnalysisReport {
        return api.analyzeContract(ClauseInput(text = text))
    }

    suspend fun analyzeContractSafe(text: String): Result<AnalysisReport> {
        return try {
            val report = analyzeContract(text)
            Result.Success(report)
        } catch (e: Exception) {
            Result.Error(e.localizedMessage ?: "A network timeout or error occurred. Please try again.")
        }
    }
}