package com.clauseguard.app.ui.screens

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

    // Bottom Sheet State
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    val scope = rememberCoroutineScope()

    // Sync bottom sheet visibility with selectedClause
    LaunchedEffect(selectedClause) {
        if (selectedClause != null) {
            scope.launch { sheetState.show() }
        }
    }

    Box(modifier = Modifier.fillMaxSize()) {
        // Background: Full Document
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(MaterialTheme.colorScheme.surface)
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
                        color = MaterialTheme.colorScheme.onSurface
                    )
                    IconButton(
                        onClick = onBack,
                        modifier = Modifier
                            .background(Color.Black.copy(alpha = 0.3f), CircleShape)
                    ) {
                        Icon(
                            imageVector = Icons.Rounded.Close,
                            contentDescription = "Close",
                            tint = MaterialTheme.colorScheme.onSurface
                        )
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                // Interactive Document
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(Color.White.copy(alpha = 0.03f), RoundedCornerShape(12.dp))
                        .padding(16.dp)
                        .verticalScroll(rememberScrollState())
                ) {
                    ClickableText(
                        text = annotatedText,
                        onClick = { offset ->
                            val annotations = annotatedText.getStringAnnotations("CLAUSE", offset, offset)
                            if (annotations.isNotEmpty()) {
                                val clauseText = annotations.first().item
                                selectedClause = report.clauses.find { it.clause_text == clauseText }
                            }
                        },
                        style = TextStyle(
                            fontSize = 14.sp,
                            lineHeight = 24.sp,
                            color = Color.White
                        )
                    )
                }
            }
        }

        // Negotiation Strategy Bottom Sheet
        if (selectedClause != null) {
            ModalBottomSheet(
                sheetState = sheetState,
                onDismissRequest = { selectedClause = null },
                containerColor = MaterialTheme.colorScheme.surfaceContainerHighest,
                shape = RoundedCornerShape(topStart = 24.dp, topEnd = 24.dp),
            ) {
                selectedClause?.let { clause ->
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(24.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        // Header
                        Text(
                            text = "Negotiation Strategy",
                            fontSize = 20.sp,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onSurface
                        )
                        Spacer(modifier = Modifier.height(16.dp))

                        // Original Clause (Highlighted Box)
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .background(
                                    brush = Brush.horizontalGradient(
                                        colors = listOf(
                                            MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.5f),
                                            MaterialTheme.colorScheme.secondaryContainer.copy(alpha = 0.5f)
                                        )
                                    ),
                                    shape = RoundedCornerShape(16.dp)
                                )
                                .padding(16.dp)
                        ) {
                            Column {
                                Text(
                                    text = "\"${clause.clause_text}\"",
                                    fontSize = 14.sp,
                                    color = MaterialTheme.colorScheme.onSurface,
                                    fontWeight = FontWeight.Medium,
                                    fontStyle = FontStyle.Italic
                                )
                                Spacer(modifier = Modifier.height(12.dp))
                                Text(
                                    text = "Risk: ${clause.risk_level.uppercase()}",
                                    fontSize = 12.sp,
                                    color = when (clause.risk_level.lowercase()) {
                                        "high", "critical" -> Color.Red
                                        "medium" -> Color(0xFFFF9F0A)
                                        else -> Color(0xFF32D74B)
                                    },
                                    fontWeight = FontWeight.Bold
                                )
                            }
                        }

                        Spacer(modifier = Modifier.height(24.dp))

                        // Explanation
                        Text(
                            text = "Why it's Risky",
                            fontSize = 16.sp,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onSurface
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = clause.explanation,
                            fontSize = 14.sp,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            lineHeight = 22.sp
                        )

                        Spacer(modifier = Modifier.height(24.dp))

                        // Negotiation Strategy (Purple Glass Box)
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .background(
                                    brush = Brush.horizontalGradient(
                                        colors = listOf(
                                            MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.4f),
                                            MaterialTheme.colorScheme.secondaryContainer.copy(alpha = 0.4f)
                                        )
                                    ),
                                    shape = RoundedCornerShape(16.dp)
                                )
                                .padding(20.dp)
                        ) {
                            Column {
                                Text(
                                    text = "How to Negotiate",
                                    fontSize = 16.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = MaterialTheme.colorScheme.onPrimaryContainer
                                )
                                Spacer(modifier = Modifier.height(12.dp))
                                Text(
                                    text = report.negotiation_script,
                                    fontSize = 14.sp,
                                    color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.9f),
                                    lineHeight = 22.sp
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
                "high", "critical" -> Color.Red.copy(alpha = 0.25f)
                "medium" -> Color(0xFFFF9F0A).copy(alpha = 0.25f)
                else -> Color(0xFF32D74B).copy(alpha = 0.25f)
            }

            withStyle(
                style = SpanStyle(
                    background = highlightColor,
                    textDecoration = TextDecoration.Underline,
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