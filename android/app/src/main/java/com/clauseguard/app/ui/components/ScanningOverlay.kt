package com.clauseguard.app.ui.components

import android.graphics.RenderEffect
import android.graphics.Shader
import android.os.Build
import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asComposeRenderEffect
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

@Composable
fun ScanningOverlay(isLoading: Boolean) {
    val blurRadius = remember { Animatable(0f) }

    LaunchedEffect(isLoading) {
        blurRadius.animateTo(
            targetValue = if (isLoading) 20f else 0f,
            animationSpec = tween(durationMillis = 600)
        )
    }

    // Only draw the overlay if the blur radius is actively greater than 0
    if (blurRadius.value > 0.01f || isLoading) {
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center,
        ) {
            // Background Layer: Isolated from the text to prevent blur bleed.
            // State read (`blurRadius.value`) is deferred to the graphicsLayer draw phase,
            // entirely eliminating recomposition thrashing during the animation.
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .graphicsLayer {
                        val radius = blurRadius.value
                        if (radius > 0f && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                            renderEffect = RenderEffect
                                .createBlurEffect(radius, radius, Shader.TileMode.DECAL)
                                .asComposeRenderEffect()
                        }
                    }
                    .background(Color.Black.copy(alpha = 0.3f))
            )

            // Foreground Layer: Text remains crisp and unblurred.
            Text(
                text = "Analyzing contract…",
                color = Color.White,
                fontSize = 20.sp,
                fontWeight = FontWeight.Medium
            )
        }
    }
}