import re

with open('app/src/main/java/com/clauseguard/app/ui/screens/ResultsScreen.kt', 'r') as f:
    text = f.read()

# Add Toast context to ResultsScreen
text = text.replace(
"""fun ResultsScreen(
    report: AnalysisReport,
    onBack: () -> Unit
) {
    val haptics = LocalHapticFeedback.current""",
"""fun ResultsScreen(
    report: AnalysisReport,
    onBack: () -> Unit
) {
    val context = LocalContext.current
    val haptics = LocalHapticFeedback.current"""
)

# Add Toast to button
text = text.replace(
"""                Button(
                    onClick = {
                        haptics.performHapticFeedback(HapticFeedbackType.LongPress)
                        clipboardManager.setText(buildAnnotatedString { append(report.negotiation_script) })
                        showStrategySheet = false
                    },""",
"""                Button(
                    onClick = {
                        haptics.performHapticFeedback(HapticFeedbackType.LongPress)
                        clipboardManager.setText(buildAnnotatedString { append(report.negotiation_script) })
                        android.widget.Toast.makeText(context, "Strategy copied to clipboard!", android.widget.Toast.LENGTH_SHORT).show()
                        showStrategySheet = false
                    },"""
)

with open('app/src/main/java/com/clauseguard/app/ui/screens/ResultsScreen.kt', 'w') as f:
    f.write(text)
