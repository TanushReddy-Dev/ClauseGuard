package com.clauseguard.app.network

import com.clauseguard.app.BuildConfig
import com.clauseguard.app.models.AnalysisReport
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.RequestBody.Companion.toRequestBody
import retrofit2.Retrofit
import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part
import java.util.concurrent.TimeUnit

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
        .connectTimeout(180, TimeUnit.SECONDS)
        .readTimeout(180, TimeUnit.SECONDS)
        .writeTimeout(180, TimeUnit.SECONDS)
        .build()

    private val retrofit: Retrofit = Retrofit.Builder()
        .baseUrl("https://dna-conferences-erp-qld.trycloudflare.com/")
        .client(okHttp)
        .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
        .build()

    val api: ClauseGuardApi = retrofit.create(ClauseGuardApi::class.java)

    suspend fun analyzeContract(imageBytes: ByteArray, fileName: String): AnalysisReport {
        val requestBody = imageBytes.toRequestBody("application/octet-stream".toMediaType())
        val part = MultipartBody.Part.createFormData("file", fileName, requestBody)
        return api.analyzeContract(part)
    }
}
