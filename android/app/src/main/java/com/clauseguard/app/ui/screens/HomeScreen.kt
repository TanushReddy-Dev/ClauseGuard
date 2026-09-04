package com.clauseguard.app.ui.screens

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.Spring
import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.rounded.Warning
import androidx.compose.ui.draw.clip
import androidx.compose.foundation.border
import androidx.compose.ui.draw.shadow
import androidx.compose.animation.core.spring
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Add
import androidx.compose.material.icons.rounded.Close
import androidx.compose.material.icons.rounded.Create
import androidx.compose.material.icons.rounded.Delete
import androidx.compose.material.icons.rounded.Lock
import androidx.compose.material.icons.rounded.Search
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExtendedFloatingActionButton
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.SwipeToDismissBox
import androidx.compose.material3.SwipeToDismissBoxValue
import androidx.compose.material3.Text
import androidx.compose.material3.rememberSwipeToDismissBoxState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.scale
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
import com.clauseguard.app.data.AppDatabase
import com.clauseguard.app.data.ContractEntity
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    onNavigateToScan: () -> Unit,
    onUploadDocument: (Uri) -> Unit,
    onNavigateToResult: (String, String) -> Unit
) {
    val context = LocalContext.current
    val db = AppDatabase.getDatabase(context)
    val dao = db.contractDao()
    val scope = rememberCoroutineScope()
    val haptics = LocalHapticFeedback.current

    val contracts by dao.getAllContracts().collectAsState(initial = emptyList())
    var isFabExpanded by remember { mutableStateOf(false) }

    val filePickerLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.OpenDocument()
    ) { uri: Uri? ->
        isFabExpanded = false
        if (uri != null) {
            onUploadDocument(uri)
        }
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF050507)) // Deep black background
    ) {
        Column(modifier = Modifier.fillMaxSize()) {
            // Header
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 24.dp, vertical = 32.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Box(
                    modifier = Modifier
                        .size(44.dp)
                        .background(Color(0xFF5E5CE6), CircleShape), // Solid color
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = Icons.Rounded.Lock,
                        contentDescription = "Vault Icon",
                        tint = Color.White,
                        modifier = Modifier.size(24.dp)
                    )
                }
                Spacer(modifier = Modifier.width(16.dp))
                Text(
                    text = "Secure Vault",
                    fontSize = 28.sp,
                    fontWeight = FontWeight.ExtraBold,
                    color = Color.White
                )
            }

            // Empty State or List
            if (contracts.isEmpty()) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Box(
                            modifier = Modifier
                                .size(80.dp)
                                .background(Color(0xFF5E5CE6), CircleShape), // Solid color
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(Icons.Rounded.Warning, contentDescription = null, tint = Color.White, modifier = Modifier.size(32.dp))
                        }
                        Spacer(Modifier.height(16.dp))
                        Text(
                            text = "Your Vault is Empty",
                            fontSize = 20.sp,
                            fontWeight = FontWeight.Bold,
                            color = Color.White
                        )
                        Spacer(Modifier.height(8.dp))
                        Text(
                            text = "Scan or upload your first contract to begin the risk analysis.",
                            color = Color.White.copy(alpha = 0.5f),
                            textAlign = TextAlign.Center,
                            lineHeight = 24.sp
                        )
                    }
                }
            } else {
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(bottom = 120.dp, start = 16.dp, end = 16.dp)
                ) {
                    items(items = contracts, key = { it.id }) { contract ->
                        val dismissState = rememberSwipeToDismissBoxState(
                            confirmValueChange = { state ->
                                if (state == SwipeToDismissBoxValue.EndToStart) {
                                    scope.launch { dao.deleteContractById(contract.id) }
                                    true
                                } else false
                            }
                        )

                        SwipeToDismissBox(
                            state = dismissState,
                            backgroundContent = {
                                val color by animateColorAsState(
                                    if (dismissState.targetValue == SwipeToDismissBoxValue.EndToStart) Color(0xFFFF3B30) else Color.Transparent,
                                    label = "delete_color"
                                )
                                val scale by animateFloatAsState(
                                    if (dismissState.targetValue == SwipeToDismissBoxValue.EndToStart) 1f else 0.8f, // Emil: Snappy transition to 1f, not 1.2f
                                    label = "delete_scale"
                                )
                                Box(
                                    modifier = Modifier
                                        .fillMaxSize()
                                        .padding(vertical = 8.dp)
                                        .background(color, RoundedCornerShape(16.dp))
                                        .padding(end = 24.dp),
                                    contentAlignment = Alignment.CenterEnd
                                ) {
                                    Icon(
                                        imageVector = Icons.Rounded.Delete,
                                        contentDescription = "Delete",
                                        tint = Color.White,
                                        modifier = Modifier.scale(scale)
                                    )
                                }
                            },
                            content = {
                                VaultCard(
                                    contract = contract,
                                    onClick = {
                                        haptics.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                                        onNavigateToResult(contract.summaryJson, contract.rawText)
                                    }
                                )
                            },
                            enableDismissFromStartToEnd = false
                        )
                    }
                }
            }
        }

        // FAB Group
        Column(
            modifier = Modifier
                .align(Alignment.BottomEnd)
                .padding(bottom = 32.dp, end = 24.dp),
            horizontalAlignment = Alignment.End
        ) {
            // Expanded Actions
            AnimatedVisibility(
                visible = isFabExpanded,
                enter = fadeIn() + slideInVertically(
                    initialOffsetY = { 50 },
                    animationSpec = spring(
                        dampingRatio = 0.8f, // Emil: Apple style low bounce
                        stiffness = 400f
                    )
                ),
                exit = fadeOut() + slideOutVertically(targetOffsetY = { 50 })
            ) {
                Column(
                    horizontalAlignment = Alignment.End,
                    modifier = Modifier.padding(bottom = 16.dp)
                ) {
                    ExtendedFloatingActionButton(
                        onClick = {
                            isFabExpanded = false
                            filePickerLauncher.launch(
                                arrayOf(
                                    "application/pdf",
                                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                )
                            )
                        },
                        containerColor = Color.White.copy(alpha = 0.08f),
                        contentColor = Color.White,
                        icon = { Icon(Icons.Rounded.Search, "Upload File") },
                        text = { Text("Upload File", fontWeight = FontWeight.SemiBold) },
                        modifier = Modifier.padding(bottom = 12.dp)
                    )

                    ExtendedFloatingActionButton(
                        onClick = {
                            isFabExpanded = false
                            onNavigateToScan()
                        },
                        containerColor = Color.White.copy(alpha = 0.08f),
                        contentColor = Color.White,
                        icon = { Icon(Icons.Rounded.Create, "Scan Contract") },
                        text = { Text("Scan Document", fontWeight = FontWeight.SemiBold) }
                    )
                }
            }

            // Main FAB
            val fabRotation by animateFloatAsState(
                targetValue = if (isFabExpanded) 45f else 0f,
                animationSpec = spring(dampingRatio = 0.8f, stiffness = 400f),
                label = "fab_rotation"
            )
            FloatingActionButton(
                onClick = {
                    haptics.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                    isFabExpanded = !isFabExpanded
                },
                containerColor = Color(0xFF5E5CE6),
                contentColor = Color.White,
                shape = CircleShape,
                modifier = Modifier.size(56.dp)
            ) {
                Icon(
                    imageVector = Icons.Rounded.Add,
                    contentDescription = "New Scan",
                    modifier = Modifier.size(24.dp).rotate(fabRotation)
                )
            }
        }
    }
}

@Composable
private fun VaultCard(contract: ContractEntity, onClick: () -> Unit) {
    val formatter = SimpleDateFormat("MMM dd, yyyy", Locale.getDefault())
    val dateString = formatter.format(Date(contract.date))

    val riskColor = when {
        contract.riskScore >= 70 -> Color(0xFFFF3B30)
        contract.riskScore >= 40 -> Color(0xFFFF9F0A)
        else -> Color(0xFF32D74B)
    }

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 8.dp)
            .shadow(
                elevation = 32.dp, // Emil: Softer, deeper shadows
                spotColor = Color.Black.copy(alpha = 0.4f),
                ambientColor = Color.Transparent,
                shape = RoundedCornerShape(24.dp)
            )
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
            .clickable { onClick() }
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = contract.title.ifBlank { "Untitled Contract" },
                    fontSize = 18.sp,
                    fontWeight = FontWeight.SemiBold,
                    color = Color.White
                )
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text = dateString,
                    fontSize = 14.sp,
                    color = Color.White.copy(alpha = 0.5f)
                )
            }
            Box(
                modifier = Modifier
                    .size(52.dp)
                    .background(riskColor.copy(alpha = 0.15f), RoundedCornerShape(50))
                    .border(1.dp, riskColor.copy(alpha = 0.3f), RoundedCornerShape(50)),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = contract.riskScore.toString(),
                    color = Color.White,
                    fontWeight = FontWeight.Bold,
                    fontSize = 18.sp
                )
            }
        }
    }
}