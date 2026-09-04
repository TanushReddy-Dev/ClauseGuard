package com.clauseguard.app.ui.screens

import androidx.compose.animation.animateContentSize
import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Close
import androidx.compose.material.icons.rounded.KeyboardArrowDown
import androidx.compose.material.icons.rounded.Warning
import androidx.compose.material.icons.rounded.Share
import androidx.compose.material.icons.rounded.Info
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.clauseguard.app.models.AnalysisReport
import com.clauseguard.app.models.ClauseRiskScore

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ResultsScreen(
    report: AnalysisReport,
    onBack: () -> Unit
) {
    val haptics = LocalHapticFeedback.current
    val flaggedClauses = remember(report) {
        report.clauses.filter {
            val cat = it.classification.category.lowercase()
            cat != "other:unknown" && cat != "unknown"
        }
    }

    var showStrategySheet by remember { mutableStateOf(false) }
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF050507)) // Solid black background instead of gradient
    ) {
        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(top = 16.dp, bottom = 120.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            item {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp, vertical = 8.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "Contract Analysis",
                        fontSize = 22.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )
                    IconButton(
                        onClick = {
                            haptics.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                            onBack()
                        },
                        modifier = Modifier
                            .background(Color.White.copy(alpha = 0.1f), CircleShape)
                            .border(1.dp, Color.White.copy(alpha = 0.12f), CircleShape)
                    ) {
                        Icon(
                            imageVector = Icons.Rounded.Close,
                            contentDescription = "Close",
                            tint = Color.White
                        )
                    }
                }
            }

            item {
                RiskDial(
                    score = (report.overall_risk_score * 10).toInt().coerceIn(0, 100),
                    modifier = Modifier.padding(vertical = 16.dp)
                )
            }

            item {
                Text(
                    text = "Flagged Clauses",
                    fontSize = 18.sp,
                    fontWeight = FontWeight.SemiBold,
                    color = Color.White,
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(start = 24.dp, top = 24.dp, bottom = 16.dp)
                )
            }

            if (flaggedClauses.isEmpty()) {
                item { SafeStateCard() }
            } else {
                items(flaggedClauses) { clause ->
                    ClauseCard(clause = clause, globalNegotiationScript = report.negotiation_script)
                }
            }
        }

        // Global Negotiation Strategy Button
        if (report.negotiation_script.isNotBlank()) {
            Box(
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .fillMaxWidth()
                    .padding(16.dp)
                    .padding(bottom = 16.dp)
            ) {
                Button(
                    onClick = {
                        haptics.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                        showStrategySheet = true
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(56.dp)
                        ,
                    shape = RoundedCornerShape(16.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color(0xFF0A84FF),
                        contentColor = Color.White
                    )
                ) {
                    Icon(imageVector = Icons.Rounded.Info, contentDescription = null, modifier = Modifier.size(20.dp))
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("View Master Strategy", fontWeight = FontWeight.Bold, fontSize = 16.sp)
                }
            }
        }
    }

    if (showStrategySheet) {
        val clipboardManager = LocalClipboardManager.current
        ModalBottomSheet(
            onDismissRequest = { showStrategySheet = false },
            sheetState = sheetState,
            containerColor = Color(0xFF1C1C1E),
            shape = RoundedCornerShape(topStart = 32.dp, topEnd = 32.dp),
            dragHandle = {
                Box(
                    modifier = Modifier
                        .padding(vertical = 12.dp)
                        .width(48.dp)
                        .height(6.dp)
                        .background(Color.White.copy(alpha = 0.2f), CircleShape)
                )
            }
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 24.dp)
                    .padding(bottom = 48.dp)
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        modifier = Modifier
                            .size(48.dp)
                            .background(Color(0xFF0A84FF), CircleShape), // Solid color
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(imageVector = Icons.Rounded.Info, contentDescription = null, tint = Color.White)
                    }
                    Spacer(modifier = Modifier.width(16.dp))
                    Column {
                        Text(
                            text = "Master Negotiation",
                            fontSize = 22.sp,
                            fontWeight = FontWeight.ExtraBold,
                            color = Color.White
                        )
                        Text(
                            text = "Generated by ClauseGuard AI",
                            fontSize = 13.sp,
                            color = Color.White.copy(alpha = 0.5f)
                        )
                    }
                }

                Spacer(Modifier.height(32.dp))

                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(Color.White.copy(alpha = 0.05f), RoundedCornerShape(24.dp))
                        .border(1.dp, Color.White.copy(alpha = 0.12f), RoundedCornerShape(24.dp))
                        .padding(24.dp)
                ) {
                    Text(
                        text = report.negotiation_script,
                        fontSize = 15.sp,
                        lineHeight = 26.sp,
                        color = Color.White.copy(alpha = 0.85f),
                        fontStyle = FontStyle.Italic
                    )
                }

                Spacer(Modifier.height(32.dp))

                Button(
                    onClick = {
                        haptics.performHapticFeedback(HapticFeedbackType.LongPress)
                        clipboardManager.setText(buildAnnotatedString { append(report.negotiation_script) })
                        showStrategySheet = false
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(56.dp),
                    shape = RoundedCornerShape(16.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color.White.copy(alpha = 0.1f),
                        contentColor = Color.White
                    )
                ) {
                    Icon(imageVector = Icons.Rounded.Share, contentDescription = null, modifier = Modifier.size(20.dp))
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Copy to Clipboard", fontWeight = FontWeight.Bold, fontSize = 16.sp)
                }
            }
        }
    }
}

@Composable
private fun ClauseCard(clause: ClauseRiskScore, globalNegotiationScript: String) {
    val haptics = LocalHapticFeedback.current
    var expanded by remember { mutableStateOf(false) }

    val riskColor = when (clause.risk_level.lowercase()) {
        "high", "critical" -> Color(0xFFFF3B30)
        "medium" -> Color(0xFFFF9F0A)
        else -> Color(0xFF32D74B)
    }

    val arrowRotation by animateFloatAsState(
        targetValue = if (expanded) 180f else 0f,
        animationSpec = spring(
            dampingRatio = 0.8f, // Emil: Apple style low bounce
            stiffness = 400f
        ),
        label = "arrow_rotation"
    )

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp)
            .background(
                color = Color.White.copy(alpha = 0.06f),
                shape = RoundedCornerShape(24.dp)
            )
            .border(
                width = 1.dp,
                color = Color.White.copy(alpha = 0.12f),
                shape = RoundedCornerShape(24.dp)
            )
            .clip(RoundedCornerShape(24.dp))
            .animateContentSize(
                animationSpec = spring(
                    dampingRatio = 0.8f, // Emil: Apple style low bounce
                    stiffness = 400f
                )
            )
            .clickable {
                haptics.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                expanded = !expanded
            }
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = clause.classification.category,
                    fontWeight = FontWeight.Bold,
                    fontSize = 16.sp,
                    color = Color.White
                )
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier
                        .background(riskColor.copy(alpha = 0.15f), RoundedCornerShape(50))
                        .border(1.dp, riskColor.copy(alpha = 0.3f), RoundedCornerShape(50))
                        .padding(horizontal = 12.dp, vertical = 6.dp)
                ) {
                    Icon(
                        imageVector = Icons.Rounded.Warning,
                        contentDescription = "Risk",
                        tint = riskColor,
                        modifier = Modifier.size(14.dp)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = clause.risk_level.uppercase(),
                        color = Color.White,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.SemiBold
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            Text(
                text = "\"${clause.clause_text}\"",
                fontSize = 14.sp,
                color = Color.White.copy(alpha = 0.85f),
                fontStyle = FontStyle.Italic,
                lineHeight = 22.sp,
                modifier = Modifier
                    .background(Color.Black.copy(alpha = 0.3f), RoundedCornerShape(12.dp))
                    .padding(14.dp)
            )

            Spacer(modifier = Modifier.height(16.dp))

            Text(
                text = "Analysis",
                fontSize = 13.sp,
                fontWeight = FontWeight.Bold,
                color = riskColor.copy(alpha = 0.9f)
            )
            Spacer(modifier = Modifier.height(6.dp))
            Text(
                text = clause.explanation,
                fontSize = 15.sp,
                color = Color.White,
                lineHeight = 22.sp
            )

            Spacer(modifier = Modifier.height(16.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = if (expanded) "Hide Strategy" else "View Strategy",
                    fontSize = 14.sp,
                    fontWeight = FontWeight.SemiBold,
                    color = Color(0xFFA191FF)
                )
                Spacer(modifier = Modifier.width(6.dp))
                Icon(
                    imageVector = Icons.Rounded.KeyboardArrowDown,
                    contentDescription = "Toggle Strategy",
                    tint = Color(0xFFA191FF),
                    modifier = Modifier
                        .size(20.dp)
                        .rotate(arrowRotation)
                )
            }

            if (expanded) {
                Spacer(modifier = Modifier.height(16.dp))
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(Color(0xFFA191FF).copy(alpha = 0.1f), RoundedCornerShape(16.dp)) // Solid color
                        .border(1.dp, Color(0xFFA191FF).copy(alpha = 0.2f), RoundedCornerShape(16.dp))
                        .padding(16.dp)
                ) {
                    Column {
                        Text(
                            text = "Negotiation Strategy",
                            fontSize = 14.sp,
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFFA191FF)
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = globalNegotiationScript,
                            fontSize = 14.sp,
                            color = Color.White.copy(alpha = 0.9f),
                            lineHeight = 22.sp
                        )
                    }
                }
            }
        }
    }
}

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

    val color = when {
        score >= 70 -> Color(0xFFFF3B30)
        score >= 40 -> Color(0xFFFF9F0A)
        else -> Color(0xFF32D74B)
    }

    Box(modifier = modifier.size(200.dp), contentAlignment = Alignment.Center) {
        Canvas(Modifier.size(180.dp)) {
            val stroke = Stroke(width = 16.dp.toPx(), cap = StrokeCap.Round)
            val arcSize = Size(size.width, size.height)

            drawArc(
                color = Color.White.copy(alpha = 0.05f),
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
        Text("$score", fontSize = 48.sp, fontWeight = FontWeight.ExtraBold, color = color)
    }
}

@Composable
private fun SafeStateCard() {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp)
            .background(Color(0xFF32D74B).copy(alpha = 0.1f), RoundedCornerShape(24.dp))
            .border(1.dp, Color(0xFF32D74B).copy(alpha = 0.3f), RoundedCornerShape(24.dp))
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Text("✓", fontSize = 48.sp, color = Color(0xFF32D74B))
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