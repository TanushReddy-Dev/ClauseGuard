package com.clauseguard.app.network

import com.clauseguard.app.models.AnalysisReport
import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.RequestBody.Companion.toRequestBody
import retrofit2.Retrofit
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part
import java.util.concurrent.TimeUnit

sealed class Result<out T> {
    data class Success<out T>(val data: T) : Result<T>()
    object Loading : Result<Nothing>()
    data class Error(val message: String) : Result<Nothing>()
}

interface ClauseGuardApi {
    @Multipart
    @POST("analyze-contract")
    suspend fun analyzeContract(
        @Part file: MultipartBody.Part,
    ): AnalysisReport
}

object NetworkClient {
    private val json = Json { ignoreUnknownKeys = true }

    private val okHttp = OkHttpClient.Builder()
        .connectTimeout(60, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .writeTimeout(60, TimeUnit.SECONDS)
        .build()

    private val retrofit: Retrofit = Retrofit.Builder()
        .baseUrl("https://clauseguard-api-29de.onrender.com/")
        .client(okHttp)
        .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
        .build()

    val api: ClauseGuardApi = retrofit.create(ClauseGuardApi::class.java)

    suspend fun analyzeContract(imageBytes: ByteArray, fileName: String): AnalysisReport {
        val requestBody = imageBytes.toRequestBody("application/octet-stream".toMediaType())
        val part = MultipartBody.Part.createFormData("file", fileName, requestBody)
        return api.analyzeContract(part)
    }

    suspend fun analyzeContractSafe(imageBytes: ByteArray, fileName: String): Result<AnalysisReport> {
        return try {
            val report = analyzeContract(imageBytes, fileName)
            Result.Success(report)
        } catch (e: Exception) {
            Result.Error(e.localizedMessage ?: "A network timeout or error occurred. Please try again.")
        }
    }
}