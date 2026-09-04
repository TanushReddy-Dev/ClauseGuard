package com.clauseguard.app.ui.components

import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.clauseguard.app.models.ClauseRiskScore

@Composable
fun ClauseCard(clause: ClauseRiskScore, index: Int) {
    var visible by remember { mutableStateOf(false) }
    var flipped by remember { mutableStateOf(false) }
    val haptic = LocalHapticFeedback.current

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

    val riskColor = when {
        riskPercent >= 70 -> Color.Red
        riskPercent >= 40 -> Color(0xFFFF9800)
        else -> Color(0xFF4CAF50)
    }

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp)
            .graphicsLayer {
                // State reads deferred to the graphicsLayer draw phase
                scaleX = scale
                scaleY = scale
                alpha = scale
                rotationY = rotation

                // Strictly lock 3D perspective to prevent distortion/clipping
                cameraDistance = 12f * density
            }
            .clickable {
                haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                flipped = !flipped
            },
        shape = RoundedCornerShape(16.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                // Apply strict opaque background to the Box to prevent transparency bleed
                .background(MaterialTheme.colorScheme.surface)
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
                        color = riskColor,
                    )
                }
            } else {
                Column(Modifier.graphicsLayer { rotationY = 180f }) {
                    Text(
                        "Risk Score: $riskPercent/100",
                        fontWeight = FontWeight.Bold,
                        fontSize = 18.sp,
                        color = riskColor,
                    )
                    Spacer(Modifier.height(8.dp))
                    Text(clause.explanation, fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }
    }
}