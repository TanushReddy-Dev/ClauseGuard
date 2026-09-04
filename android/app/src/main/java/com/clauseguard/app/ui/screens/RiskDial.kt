package com.clauseguard.app.ui.screens

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/**
 * A risk-score dial drawn via Canvas.drawArc.
 *
 * The arc sweeps 240° (from 150° start angle) to represent 0–100% risk.
 * The sweep angle is animated from 0 → target using animateFloatAsState with a
 * 1200ms tween for a smooth ease-out into the final position.
 *
 * Usage: place in ResultsScreen with the computed overallRisk score (0–100).
 */
@Composable
fun RiskDial(
    score: Int,
    modifier: Modifier = Modifier,
) {
    // Clamp to valid range and ensure we always have a target.
    val clampedScore = score.coerceIn(0, 100)

    // The arc is 240° total; sweepTarget maps 0–100 → 0–240 degrees.
    val sweepTarget = (clampedScore / 100f) * 240f

    // Start the animation once on first composition so the arc animates in.
    var animationTriggered by remember { mutableStateOf(false) }
    LaunchedEffect(Unit) { animationTriggered = true }

    val animatedSweep by animateFloatAsState(
        targetValue = if (animationTriggered) sweepTarget else 0f,
        animationSpec = tween(durationMillis = 1200),
        label = "risk-dial",
    )

    // Color mapping consistent with the ClauseCard risk thresholds.
    val arcColor = when {
        clampedScore >= 70 -> Color.Red
        clampedScore >= 40 -> Color(0xFFFF9800)
        else -> Color(0xFF4CAF50)
    }

    Box(
        modifier = modifier
            .size(200.dp)
            .padding(vertical = 16.dp),
        contentAlignment = Alignment.Center,
    ) {
        Canvas(modifier = Modifier.size(180.dp)) {
            val stroke = Stroke(width = 16.dp.toPx(), cap = StrokeCap.Round)
            val arcSize = Size(size.width, size.height)
            val topLeft = Offset.Zero

            // Background track — a light gray ring so the animated arc stands out.
            drawArc(
                color = Color.LightGray.copy(alpha = 0.3f),
                startAngle = 150f,
                sweepAngle = 240f,
                useCenter = false,
                topLeft = topLeft,
                size = arcSize,
                style = stroke,
            )

            // Foreground animated arc — sweeps from the start angle according to the risk score.
            drawArc(
                color = arcColor,
                startAngle = 150f,
                sweepAngle = animatedSweep,
                useCenter = false,
                topLeft = topLeft,
                size = arcSize,
                style = stroke,
            )
        }

        // Center numeric label (e.g. "73").
        Text(
            text = "$clampedScore",
            fontSize = 40.sp,
            fontWeight = FontWeight.Bold,
            color = arcColor,
            alignment = Alignment.Center,
        )
    }
}