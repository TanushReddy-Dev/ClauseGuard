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
import com.clauseguard.app.ui.components.ErrorState
import com.clauseguard.app.ui.components.SplashScreen
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme(colorScheme = darkColorScheme()) {
                Surface(modifier = Modifier.fillMaxSize()) {
                    var showSplash by remember { mutableStateOf(true) }

                    // Crossfade handles the smooth fade-out of the splash screen
                    // and fade-in of the main capture view automatically
                    Crossfade(
                        targetState = showSplash,
                        animationSpec = tween(durationMillis = 600),
                        label = "splash_transition"
                    ) { isSplashScreen ->
                        if (isSplashScreen) {
                            SplashScreen(
                                onTimeout = { showSplash = false }
                            )
                        } else {
                            CaptureScreen()
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
    data class Success(val report: AnalysisReport) : UiState()
    data class Error(val message: String) : UiState()
}

// ── ViewModel: owns the network call, exposes state ──

class ContractViewModel : ViewModel() {
    var uiState by mutableStateOf<UiState>(UiState.Idle)
        private set

    fun sendContract(extractedText: String) {
        if (uiState is UiState.Loading) return
        uiState = UiState.Loading
        viewModelScope.launch {
            uiState = try {
                val report = NetworkClient.analyzeContract(text = extractedText)
                UiState.Success(report)
            } catch (e: Exception) {
                UiState.Error(e.message ?: "Analysis failed")
            }
        }
    }

    fun setError(message: String) {
        uiState = UiState.Error(message)
    }

    fun resetToIdle() {
        uiState = UiState.Idle
    }
}

@Composable
fun CaptureScreen(vm: ContractViewModel = viewModel()) {
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
            is UiState.Success -> ResultsOverlay((uiState as UiState.Success).report)
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

// ── Results: risk dial + clause cards ──

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ResultsOverlay(report: AnalysisReport) {
    val flaggedClauses = remember(report) {
        report.clauses.filter {
            val cat = it.classification.category.lowercase()
            cat != "other:unknown" && cat != "unknown"
        }
    }

    var showNegotiationSheet by remember { mutableStateOf(false) }

    Box(Modifier.fillMaxSize()) {
        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(bottom = 100.dp, top = 16.dp), // extra padding for the floating button
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            item {
                Text(
                    "Contract Risk Analysis",
                    fontSize = 22.sp,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.padding(16.dp),
                )
            }
            item {
                RiskDial(
                    score = (report.overall_risk_score * 10).toInt().coerceIn(0, 100),
                    modifier = Modifier.padding(vertical = 16.dp),
                )
            }
            item {
                Text(
                    report.summary,
                    fontSize = 14.sp,
                    color = Color.Gray,
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
                )
            }
            item {
                Text(
                    "Flagged Clauses",
                    fontSize = 18.sp,
                    fontWeight = FontWeight.SemiBold,
                    modifier = Modifier.padding(start = 16.dp, top = 24.dp, bottom = 8.dp),
                )
            }
            if (flaggedClauses.isEmpty()) {
                item { SafeStateCard() }
            } else {
                itemsIndexed(flaggedClauses) { index, clause ->
                    ClauseCard(clause = clause, index = index)
                }
            }
        }

        // Action button at the bottom
        if (report.negotiation_script.isNotBlank()) {
            Box(
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .fillMaxWidth()
                    .padding(16.dp)
            ) {
                Button(
                    onClick = { showNegotiationSheet = true },
                    modifier = Modifier.fillMaxWidth().height(56.dp),
                    shape = RoundedCornerShape(16.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = MaterialTheme.colorScheme.primaryContainer,
                        contentColor = MaterialTheme.colorScheme.onPrimaryContainer
                    )
                ) {
                    Text("View Negotiation Strategy", fontWeight = FontWeight.Bold)
                }
            }
        }
    }

    if (showNegotiationSheet) {
        val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
        ModalBottomSheet(
            onDismissRequest = { showNegotiationSheet = false },
            sheetState = sheetState,
            containerColor = MaterialTheme.colorScheme.surfaceVariant,
            shape = RoundedCornerShape(topStart = 24.dp, topEnd = 24.dp),
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 24.dp, vertical = 16.dp)
                    .padding(bottom = 32.dp)
            ) {
                Text(
                    "Negotiation Strategy",
                    fontSize = 20.sp,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(Modifier.height(16.dp))
                Text(
                    report.negotiation_script,
                    fontSize = 16.sp,
                    lineHeight = 24.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.9f)
                )
            }
        }
    }
}

// ── "All clear" empty state — frosted card with green checkmark ──

@Composable
private fun SafeStateCard() {
    var visible by remember { mutableStateOf(false) }
    LaunchedEffect(Unit) { visible = true }

    // Same MediumBouncy spring as clause cards for visual consistency
    val scale by animateFloatAsState(
        targetValue = if (visible) 1f else 0f,
        animationSpec = spring(
            dampingRatio = Spring.DampingRatioMediumBouncy,
            stiffness = Spring.StiffnessMedium,
        ),
        label = "safe-entrance",
    )

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp)
            .graphicsLayer { scaleX = scale; scaleY = scale; alpha = scale },
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF1B3726)),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Text("✓", fontSize = 48.sp, color = Color(0xFF4CAF50))
            Spacer(Modifier.height(12.dp))
            Text(
                "No high-risk clauses detected",
                fontWeight = FontWeight.Bold,
                fontSize = 18.sp,
                color = Color.White,
            )
            Spacer(Modifier.height(8.dp))
            Text(
                "This contract looks standard. No actionable risks were identified by the analysis.",
                fontSize = 14.sp,
                color = Color.White.copy(alpha = 0.7f),
                textAlign = TextAlign.Center,
            )
        }
    }
}

// ── Clause card: spring entrance + tap-to-flip 3D ──

@Composable
private fun ClauseCard(clause: ClauseRiskScore, index: Int) {
    var visible by remember { mutableStateOf(false) }
    var flipped by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) { visible = true }

    val scale by animateFloatAsState(
        targetValue = if (visible) 1f else 0f,
        animationSpec = spring(
            dampingRatio = Spring.DampingRatioMediumBouncy,
            stiffness = Spring.StiffnessMedium,
        ),
        label = "entrance",
    )

    val rotation by animateFloatAsState(
        targetValue = if (flipped) 180f else 0f,
        animationSpec = spring(
            dampingRatio = Spring.DampingRatioLowBouncy,
            stiffness = Spring.StiffnessMediumLow,
        ),
        label = "flip",
    )

    val isFrontVisible = rotation <= 90f
    val riskPercent = (clause.risk_score * 10).toInt().coerceIn(0, 100)

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp)
            .graphicsLayer {
                scaleX = scale
                scaleY = scale
                alpha = scale
                rotationY = rotation
                cameraDistance = 12f * density
            }
            .clickable { flipped = !flipped },
        shape = RoundedCornerShape(16.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp),
            contentAlignment = Alignment.CenterStart,
        ) {
            if (isFrontVisible) {
                Column {
                    Text(clause.classification.category, fontWeight = FontWeight.Bold, fontSize = 16.sp)
                    Spacer(Modifier.height(8.dp))
                    Text(clause.clause_text, fontSize = 14.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Spacer(Modifier.height(6.dp))
                    Text(
                        clause.risk_level.uppercase(),
                        fontSize = 12.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = riskColor(riskPercent),
                    )
                }
            } else {
                Column(Modifier.graphicsLayer { rotationY = 180f }) {
                    Text(
                        "Risk Score: $riskPercent/100",
                        fontWeight = FontWeight.Bold,
                        fontSize = 18.sp,
                        color = riskColor(riskPercent),
                    )
                    Spacer(Modifier.height(8.dp))
                    Text(clause.explanation, fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }
    }
}

// ── Risk dial: Canvas arc animated 0→score over 1200ms ──

@Composable
private fun RiskDial(score: Int, modifier: Modifier = Modifier) {
    var triggered by remember { mutableStateOf(false) }
    LaunchedEffect(Unit) { triggered = true }

    val sweepTarget = (score / 100f) * 240f

    val animatedSweep by animateFloatAsState(
        targetValue = if (triggered) sweepTarget else 0f,
        animationSpec = tween(durationMillis = 1200),
        label = "dial",
    )

    val color = riskColor(score)

    Box(modifier = modifier.size(200.dp), contentAlignment = Alignment.Center) {
        Canvas(Modifier.size(180.dp)) {
            val stroke = Stroke(width = 16.dp.toPx(), cap = StrokeCap.Round)
            val arcSize = Size(size.width, size.height)

            drawArc(
                color = Color.LightGray.copy(alpha = 0.3f),
                startAngle = 150f,
                sweepAngle = 240f,
                useCenter = false,
                topLeft = Offset.Zero,
                size = arcSize,
                style = stroke,
            )
            drawArc(
                color = color,
                startAngle = 150f,
                sweepAngle = animatedSweep,
                useCenter = false,
                topLeft = Offset.Zero,
                size = arcSize,
                style = stroke,
            )
        }
        Text("$score", fontSize = 40.sp, fontWeight = FontWeight.Bold, color = color)
    }
}

private fun riskColor(score: Int): Color = when {
    score >= 70 -> Color.Red
    score >= 40 -> Color(0xFFFF9800)
    else -> Color(0xFF4CAF50)
}