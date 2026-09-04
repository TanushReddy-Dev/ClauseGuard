package com.clauseguard.app.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.clauseguard.app.ui.screens.ScanningOverlay
import com.clauseguard.app.ui.screens.RiskDial
import com.clauseguard.app.ui.components.ClauseCard

/**
 * The final screen that displays analysis results.
 *
 * Layout flow:
 *   • ScanningOverlay — frosted-glass blur animating while the network call is in flight.
 *   • LazyColumn of ClauseCard — each flagged clause with spring entrance + 3D flip.
 *   • RiskDial — animated arc showing the overall risk score.
 *
 * State is driven by a simple UiState sealed class (loaded inline) that the caller
 * can replace with a ViewModel / hilt‑scoped holder as the app matures.
 */
@Composable
fun ResultsScreen(uiState: UiState) {
    Box(modifier = Modifier.fillMaxSize()) {
        when (uiState) {
            is UiState.Idle -> {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text(
                        text = "Capture a contract to begin",
                        color = MaterialTheme.colorScheme.onSurface,
                        fontWeight = FontWeight.Medium
                    )
                }
            }

            is UiState.Loading -> {
                ScanningOverlay(isLoading = true)
            }

            is UiState.Error -> {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text(
                        text = "Error: ${uiState.message}",
                        color = MaterialTheme.colorScheme.error,
                        fontWeight = FontWeight.Medium
                    )
                }
            }

            is UiState.Success -> {
                // Background paper texture so the frosted glass reads well.
                val bg = MaterialTheme.colorScheme.surface

                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(bg),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center,
                ) {
                    // Top banner — title + risk dial.
                    Spacer(modifier = Modifier.height(16.dp))
                    RiskDial(score = uiState.result.overallRisk)
                    Spacer(modifier = Modifier.height(24.dp))

                    // Clause list.
                    Text(
                        text = "Flagged Clauses",
                        fontSize = 20.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = MaterialTheme.colorScheme.onSurface,
                    )
                    Spacer(modifier = Modifier.height(8.dp))

                    LazyColumn(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 16.dp),
                        contentPadding = PaddingValues(vertical = 8.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                    ) {
                        itemsIndexed(uiState.result.clauses) { index, clause ->
                            ClauseCard(clause = clause, index = index)
                        }
                    }

                    Spacer(modifier = Modifier.height(32.dp))
                }
            }
        }
    }
}

/** Sealed UI state for the results screen. */
@Immutable
sealed class UiState

@Immutable
object UiStateIdle : UiState()

@Immutable
object UiStateLoading : UiState()

@Immutable
data class UiStateSuccess(
    val result: AnalysisResult
) : UiState()

@Immutable
data class UiStateError(
    val message: String
) : UiState()

/** Holds the overall risk score and the list of flagged clauses. */
@Immutable
data class AnalysisResult(
    val overallRisk: Int,
    val clauses: List<ClauseCardData>
)

/** Minimal data class for a flagged clause — keeps Compose composition healthy. */
@Immutable
data class ClauseCardData(
    val title: String,
    val excerpt: String,
    val riskScore: Int,
    val citation: String
)