package com.clauseguard.app.ui.components

import android.graphics.RenderEffect
import android.graphics.Shader
import android.os.Build
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons

import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asComposeRenderEffect
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.delay

@Composable
fun ScanningOverlay(isLoading: Boolean) {
    val blurRadius = remember { Animatable(0f) }
    val overlayAlpha = remember { Animatable(0f) }

    // Emil: Staggering the blur and the alpha. Blur happens first to separate the background, then the content fades in.
    LaunchedEffect(isLoading) {
        if (isLoading) {
            // Enter transition
            blurRadius.animateTo(
                targetValue = 20f,
                animationSpec = tween(durationMillis = 400, easing = FastOutSlowInEasing)
            )
            overlayAlpha.animateTo(
                targetValue = 1f,
                animationSpec = tween(durationMillis = 300, easing = LinearOutSlowInEasing)
            )
        } else {
            // Exit transition: fade out content, then un-blur
            overlayAlpha.animateTo(
                targetValue = 0f,
                animationSpec = tween(durationMillis = 200, easing = FastOutLinearInEasing)
            )
            blurRadius.animateTo(
                targetValue = 0f,
                animationSpec = tween(durationMillis = 300, easing = FastOutLinearInEasing)
            )
        }
    }

    if (blurRadius.value > 0.01f || isLoading) {
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center,
        ) {
            // Deep blur backdrop
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
                    .background(Color.Black.copy(alpha = 0.4f)) // Darken the blurred content
            )

            // Central "Analyzing" Card - Apple inspired frosted glass modal
            Box(
                modifier = Modifier
                    .graphicsLayer {
                        // Emil: Never animate from scale 0. Start at 0.95.
                        val scale = 0.95f + (0.05f * overlayAlpha.value)
                        scaleX = scale
                        scaleY = scale
                        alpha = overlayAlpha.value
                    }
                    .clip(RoundedCornerShape(32.dp))
                    .background(Color(0xFF1C1C1E).copy(alpha = 0.8f))
                    .border(1.dp, Color.White.copy(alpha = 0.1f), RoundedCornerShape(32.dp))
                    .padding(horizontal = 40.dp, vertical = 32.dp),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    
                    // Pulsing Icon Ring
                    val infiniteTransition = rememberInfiniteTransition(label = "pulse")
                    val pulseScale by infiniteTransition.animateFloat(
                        initialValue = 0.9f,
                        targetValue = 1.1f,
                        animationSpec = infiniteRepeatable(
                            animation = tween(1000, easing = FastOutSlowInEasing),
                            repeatMode = RepeatMode.Reverse
                        ),
                        label = "pulse_scale"
                    )
                    
                    val pulseAlpha by infiniteTransition.animateFloat(
                        initialValue = 0.8f,
                        targetValue = 0.2f,
                        animationSpec = infiniteRepeatable(
                            animation = tween(1000, easing = FastOutSlowInEasing),
                            repeatMode = RepeatMode.Reverse
                        ),
                        label = "pulse_alpha"
                    )

                    Box(contentAlignment = Alignment.Center) {
                        // Outer glowing pulse
                        Box(
                            modifier = Modifier
                                .size(64.dp)
                                .scale(pulseScale)
                                .alpha(pulseAlpha)
                                .background(Color(0xFF5E5CE6).copy(alpha = 0.3f), CircleShape)
                        )
                        // Inner solid circle with Spinner
                        Box(
                            modifier = Modifier
                                .size(56.dp)
                                .background(Color(0xFF5E5CE6), CircleShape),
                            contentAlignment = Alignment.Center
                        ) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(24.dp),
                                color = Color.White,
                                strokeWidth = 2.5.dp
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(24.dp))

                    Text(
                        text = "Analyzing Contract",
                        color = Color.White,
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "Running multi-agent AI pipeline...",
                        color = Color.White.copy(alpha = 0.5f),
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Medium
                    )
                }
            }
        }
    }
}
