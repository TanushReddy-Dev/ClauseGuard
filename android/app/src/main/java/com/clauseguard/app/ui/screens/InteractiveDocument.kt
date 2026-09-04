package com.clauseguard.app.ui.screens

import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.ClickableText
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Close
import androidx.compose.material.icons.rounded.Share
import androidx.compose.foundation.layout.wrapContentHeight
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.Text
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.clauseguard.app.models.AnalysisReport
import com.clauseguard.app.models.ClauseRiskScore
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun InteractiveDocumentScreen(
    report: AnalysisReport,
    rawText: String,
    onBack: () -> Unit
) {
    var selectedClause by mutableStateOf<ClauseRiskScore?>(null)
    val annotatedText = remember(report, rawText) {
        buildAnnotatedStringFromClauses(rawText, report.clauses)
    }

    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    val scope = rememberCoroutineScope()
    val haptics = LocalHapticFeedback.current
    val clipboardManager = LocalClipboardManager.current
    val context = LocalContext.current

    LaunchedEffect(selectedClause) {
        if (selectedClause != null) {
            scope.launch { sheetState.show() }
        }
    }

    Box(modifier = Modifier.fillMaxSize()) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color(0xFF050507))
                .padding(top = 24.dp)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(16.dp),
                verticalArrangement = Arrangement.Top
            ) {
                // Header
                Row(
                    modifier = Modifier.fillMaxWidth(),
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
                        onClick = onBack,
                        modifier = Modifier
                            .background(Color.White.copy(alpha = 0.1f), CircleShape)
                    ) {
                        Icon(
                            imageVector = Icons.Rounded.Close,
                            contentDescription = "Close",
                            tint = Color.White
                        )
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                // Interactive Document Area
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(Color.White.copy(alpha = 0.05f), RoundedCornerShape(24.dp))
                        .padding(16.dp)
                        .verticalScroll(rememberScrollState())
                ) {
                    ClickableText(
                        text = annotatedText,
                        onClick = { offset ->
                            val annotations = annotatedText.getStringAnnotations("CLAUSE", offset, offset)
                            if (annotations.isNotEmpty()) {
                                haptics.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                                val clauseText = annotations.first().item
                                selectedClause = report.clauses.find { it.clause_text == clauseText }
                            }
                        },
                        style = TextStyle(
                            fontSize = 15.sp,
                            lineHeight = 26.sp,
                            color = Color.White.copy(alpha = 0.9f)
                        )
                    )
                }
            }
        }

        // Modal Bottom Sheet
        if (selectedClause != null) {
            ModalBottomSheet(
                sheetState = sheetState,
                onDismissRequest = { selectedClause = null },
                containerColor = Color(0xFF1C1C1E),
                shape = RoundedCornerShape(topStart = 32.dp, topEnd = 32.dp),
            ) {
                selectedClause?.let { clause ->
                    // Wrapping the entire content in a scrollable column that wraps content height
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .wrapContentHeight()
                            .padding(horizontal = 24.dp)
                            .padding(bottom = 48.dp)
                            .verticalScroll(rememberScrollState()),
                        verticalArrangement = Arrangement.spacedBy(16.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        // Header with Copy Button
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = "Analysis & Strategy",
                                fontSize = 20.sp,
                                fontWeight = FontWeight.Bold,
                                color = Color.White
                            )
                            IconButton(
                                onClick = {
                                    haptics.performHapticFeedback(HapticFeedbackType.LongPress)
                                    // Copy both the explanation and the global strategy
                                    clipboardManager.setText(
                                        AnnotatedString("Analysis: \${clause.explanation}\n\nStrategy: \${report.negotiation_script}")
                                    )
                                    Toast.makeText(context, "Strategy copied!", Toast.LENGTH_SHORT).show()
                                },
                                modifier = Modifier
                                    .background(Color.White.copy(alpha = 0.1f), CircleShape)
                            ) {
                                Icon(
                                    imageVector = Icons.Rounded.Share,
                                    contentDescription = "Copy",
                                    tint = Color.White,
                                    modifier = Modifier.size(20.dp)
                                )
                            }
                        }

                        // Original Clause (Highlighted Box)
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .wrapContentHeight()
                                .background(Color.White.copy(alpha = 0.05f), RoundedCornerShape(16.dp))
                                .padding(16.dp)
                        ) {
                            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                                Text(
                                    text = "\"${clause.clause_text}\"",
                                    fontSize = 15.sp,
                                    color = Color.White,
                                    fontWeight = FontWeight.Medium,
                                    fontStyle = FontStyle.Italic,
                                    lineHeight = 24.sp
                                )
                                Text(
                                    text = "Risk: ${clause.risk_level.uppercase()}",
                                    fontSize = 13.sp,
                                    color = when (clause.risk_level.lowercase()) {
                                        "high", "critical" -> Color(0xFFFF3B30)
                                        "medium" -> Color(0xFFFF9F0A)
                                        else -> Color(0xFF32D74B)
                                    },
                                    fontWeight = FontWeight.Bold
                                )
                            }
                        }

                        // Explanation
                        Column(
                            modifier = Modifier.fillMaxWidth(),
                            verticalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Text(
                                text = "Why it's Risky",
                                fontSize = 16.sp,
                                fontWeight = FontWeight.Bold,
                                color = Color.White
                            )
                            Text(
                                text = clause.explanation,
                                fontSize = 15.sp,
                                color = Color.White.copy(alpha = 0.8f),
                                lineHeight = 24.sp
                            )
                        }

                        // Negotiation Strategy
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .wrapContentHeight()
                                .background(Color(0xFF5E5CE6).copy(alpha = 0.15f), RoundedCornerShape(16.dp))
                                .padding(20.dp)
                        ) {
                            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                                Text(
                                    text = "Negotiation Strategy",
                                    fontSize = 16.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = Color(0xFFA191FF)
                                )
                                Text(
                                    // Displaying the global negotiation script
                                    text = report.negotiation_script,
                                    fontSize = 15.sp,
                                    color = Color.White.copy(alpha = 0.9f),
                                    lineHeight = 24.sp
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

private fun buildAnnotatedStringFromClauses(
    text: String,
    clauses: List<ClauseRiskScore>
): AnnotatedString {
    return buildAnnotatedString {
        val sortedClauses = clauses
            .map { it.clause_text }
            .distinct()
            .mapNotNull { clauseText ->
                val start = text.indexOf(clauseText)
                if (start != -1) {
                    val end = start + clauseText.length
                    val clause = clauses
                        .filter { it.clause_text == clauseText }
                        .maxByOrNull { it.risk_score }
                    if (clause != null) Triple(start, end, clause) else null
                } else {
                    null
                }
            }
            .sortedBy { it.first }

        var currentPos = 0
        for ((start, end, clause) in sortedClauses) {
            if (start > currentPos) {
                append(text.substring(currentPos, start))
            }

            val highlightColor = when (clause.risk_level.lowercase()) {
                "high", "critical" -> Color(0xFFFF3B30).copy(alpha = 0.3f)
                "medium" -> Color(0xFFFF9F0A).copy(alpha = 0.3f)
                else -> Color(0xFF32D74B).copy(alpha = 0.3f)
            }

            withStyle(
                style = SpanStyle(
                    background = highlightColor,
                    color = Color.White
                )
            ) {
                addStringAnnotation("CLAUSE", clause.clause_text, start, end)
                append(clause.clause_text)
            }
            currentPos = end
        }

        if (currentPos < text.length) {
            append(text.substring(currentPos))
        }
    }
}