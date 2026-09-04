package com.clauseguard.app

import android.Manifest
import android.content.Context
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.ImageProxy
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.animation.Crossfade
import androidx.compose.animation.core.tween
import com.clauseguard.app.ui.components.ScanningOverlay
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.material3.ButtonDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.blur
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
import com.clauseguard.app.ui.components.shimmerEffect
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.compose.viewModel
import com.clauseguard.app.models.AnalysisReport
import com.clauseguard.app.models.ClauseRiskScore
import com.clauseguard.app.network.NetworkClient
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import com.clauseguard.app.ui.components.ClauseCard
import androidx.compose.material.icons.rounded.Close
import com.clauseguard.app.ui.components.ErrorState
import com.clauseguard.app.ui.components.SplashScreen
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.clauseguard.app.data.AppDatabase
import com.clauseguard.app.data.ContractEntity
import com.clauseguard.app.ui.screens.HomeScreen
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import kotlinx.coroutines.launch

import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import java.io.File

import java.io.FileOutputStream
import android.net.Uri

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val dao = AppDatabase.getDatabase(applicationContext).contractDao()
        val viewModel = ContractViewModel(dao)

        setContent {
            MaterialTheme(colorScheme = darkColorScheme()) {
                Surface(modifier = Modifier.fillMaxSize()) {
                    var showSplash by remember { mutableStateOf(true) }

                    Crossfade(
                        targetState = showSplash,
                        animationSpec = tween(durationMillis = 600),
                        label = "splash_transition"
                    ) { isSplashScreen ->
                        if (isSplashScreen) {
                            SplashScreen(onTimeout = { showSplash = false })
                        } else {
                            val navController = rememberNavController()
                            NavHost(navController = navController, startDestination = "home") {
                                composable("home") {
                                    HomeScreen(
                                        onNavigateToScan = {
                                            viewModel.resetToIdle()
                                            navController.navigate("capture")
                                        },
                                        onUploadDocument = { uri ->
                                            viewModel.resetToIdle()
                                            viewModel.uploadDocument(uri, applicationContext)
                                            navController.navigate("capture")
                                        },
                                        onNavigateToResult = { summaryJson, rawText ->
                                            try {
                                                val report = Json.decodeFromString<AnalysisReport>(summaryJson)
                                                viewModel.setCachedReport(report, rawText)
                                                navController.navigate("capture")
                                            } catch (e: Exception) {
                                                e.printStackTrace()
                                            }
                                        }
                                    )
                                }
                                composable("capture") {
                                    CaptureScreen(
                                        vm = viewModel,
                                        onBack = { navController.popBackStack() }
                                    )
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

// ── UI state ──

sealed class UiState {
    object Idle : UiState()
    object Loading : UiState()
    data class Success(val report: AnalysisReport, val rawText: String) : UiState()
    data class Error(val message: String) : UiState()
}

// ── ViewModel: owns the network call, exposes state ──

class ContractViewModel(private val dao: com.clauseguard.app.data.ContractDao? = null) : ViewModel() {
    var uiState by mutableStateOf<UiState>(UiState.Idle)
        private set

    fun sendContract(extractedText: String) {
        if (uiState is UiState.Loading) return
        uiState = UiState.Loading
        viewModelScope.launch {
            uiState = try {
                val report = NetworkClient.analyzeContract(text = extractedText)

                // Persist the result to Room DB
                dao?.insertContract(
                    ContractEntity(
                        title = report.summary.take(30).trim() + "...",
                        riskScore = (report.overall_risk_score * 10).toInt().coerceIn(0, 100),
                        rawText = extractedText,
                        summaryJson = Json.encodeToString(report)
                    )
                )

                UiState.Success(report, extractedText)
            } catch (e: Exception) {
                UiState.Error(e.message ?: "Analysis failed")
            }
        }
    }

    fun uploadDocument(uri: Uri, context: android.content.Context) {
        if (uiState is UiState.Loading) return
        uiState = UiState.Loading
        viewModelScope.launch {
            try {
                // Copy the selected document to a temporary file
                val contentResolver = context.contentResolver
                val mimeType = contentResolver.getType(uri) ?: "application/octet-stream"
                val extension = if (mimeType.contains("pdf")) ".pdf" else ".docx"
                val tempFile = File.createTempFile("upload_", extension, context.cacheDir)

                contentResolver.openInputStream(uri)?.use { inputStream ->
                    FileOutputStream(tempFile).use { outputStream ->
                        inputStream.copyTo(outputStream)
                    }
                }

                // Create MultipartBody
                val requestBody = tempFile.asRequestBody(mimeType.toMediaTypeOrNull())
                val multipart = MultipartBody.Part.createFormData("file", tempFile.name, requestBody)

                // Upload
                val report = NetworkClient.api.analyzeFile(multipart)

                // Persist the result to Room DB
                dao?.insertContract(
                    ContractEntity(
                        title = report.summary.take(30).trim() + "...",
                        riskScore = (report.overall_risk_score * 10).toInt().coerceIn(0, 100),
                        rawText = "Document File Upload",
                        summaryJson = Json.encodeToString(report)
                    )
                )

                uiState = UiState.Success(report, "Document File Upload")
            } catch (e: Exception) {
                uiState = UiState.Error(e.message ?: "Upload failed")
            }
        }
    }

    fun setCachedReport(report: AnalysisReport, rawText: String) {
        uiState = UiState.Success(report, rawText)
    }

    fun setError(message: String) {
        uiState = UiState.Error(message)
    }

    fun resetToIdle() {
        uiState = UiState.Idle
    }
}

@Composable
fun CaptureScreen(vm: ContractViewModel = viewModel(), onBack: () -> Unit = {}) {
    val uiState = vm.uiState

    Box(Modifier.fillMaxSize()) {
        // Only show Capture UI when idle to avoid overlapping the success screen
        if (uiState is UiState.Idle) {
            com.clauseguard.app.ui.screens.CameraCaptureScreen(
                onDocumentCaptured = { bytes, _ ->
                    // Decode bytes to Bitmap for ML Kit Text Recognition
                    val bitmap = android.graphics.BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
                    if (bitmap != null) {
                        val image = InputImage.fromBitmap(bitmap, 0)
                        val recognizer = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)

                        recognizer.process(image)
                            .addOnSuccessListener { visionText ->
                                val recognizedText = visionText.text
                                android.util.Log.d("ClauseGuard", "OCR Success: Extracted \${recognizedText.length} chars")
                                vm.sendContract(recognizedText)
                            }
                            .addOnFailureListener { e ->
                                android.util.Log.e("ClauseGuard", "OCR Failed", e)
                                vm.setError("OCR extraction failed: \${e.localizedMessage}")
                            }
                    } else {
                        vm.setError("Failed to decode scanned image")
                    }
                },
                onError = { err -> vm.setError(err) }
            )
        }

        // ── Shimmer Placeholders ──
        if (uiState is UiState.Loading) {
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                contentPadding = PaddingValues(top = 100.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                userScrollEnabled = false
            ) {
                items(4) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 16.dp, vertical = 8.dp)
                            .height(100.dp)
                            .clip(RoundedCornerShape(16.dp))
                            .shimmerEffect()
                    )
                }
            }
        }

        // ── Frosted-glass scanning overlay ──
        ScanningOverlay(isLoading = uiState is UiState.Loading)

        // ── Results overlay ──
        val haptic = LocalHapticFeedback.current
        LaunchedEffect(uiState) {
            if (uiState is UiState.Success) {
                haptic.performHapticFeedback(HapticFeedbackType.LongPress)
            }
        }

        when (uiState) {
            is UiState.Success -> {
                val successState = uiState as UiState.Success
                com.clauseguard.app.ui.screens.ResultsScreen(
                    report = successState.report,
                    onBack = onBack
                )
            }
            is UiState.Error -> {
                ErrorState(
                    message = (uiState as UiState.Error).message,
                    onRetry = {
                        // Reset to idle so the user can scan again
                        vm.resetToIdle()
                    }
                )
            }
            else -> {}
        }
    }
}

// ── Frosted-glass overlay: Animatable drives blur 0→20dp over 600ms ──

@Composable
private fun ScanningOverlay(isLoading: Boolean) {
    val blurRadius = remember { Animatable(0f) }

    LaunchedEffect(isLoading) {
        blurRadius.animateTo(
            targetValue = if (isLoading) 20f else 0f,
            animationSpec = tween(durationMillis = 600),
        )
    }

    if (blurRadius.value > 0.01f) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .blur(blurRadius.value.dp)
                .background(Color.Black.copy(alpha = 0.3f)),
            contentAlignment = Alignment.Center,
        ) {
            Text("Analyzing contract…", color = Color.White, fontSize = 20.sp, fontWeight = FontWeight.Medium)
        }
    }
}