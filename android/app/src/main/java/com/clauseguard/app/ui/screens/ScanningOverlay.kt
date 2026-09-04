package com.clauseguard.app.ui.screens

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.blur
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/**
 * Frosted-glass overlay that animates blur radius from 0 to 20dp while a network
 * call is in flight. Driven by an Animatable<Float> so the blur can be driven by
 * real Compose animation APIs (no static images).
 *
 * Usage: place inside ResultsScreen behind the content, passing the loading state
 * from the ViewModel / state holder.
 */
@Composable
fun ScanningOverlay(isLoading: Boolean) {
    // Animatable drives blur radius from 0→20dp over a 600ms tween.
    val blurRadius = remember { Animatable(0f) }

    LaunchedEffect(isLoading) {
        blurRadius.animateTo(
            targetValue = if (isLoading) 20f else 0f,
            animationSpec = tween(durationMillis = 600)
        )
    }

    // Only render the overlay when the blur radius is > 0 so we don't add an
    // unnecessary layer during the idle state.
    if (blurRadius.value > 0.01f) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .blur(blurRadius.value.dp)
                .background(Color.Black.copy(alpha = 0.3f)),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = "Analyzing contract…",
                color = Color.White,
                fontSize = 20.sp,
                fontWeight = FontWeight.Medium
            )
        }
    }
}