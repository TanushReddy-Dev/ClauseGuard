with open('/c/Users/Tanus/ClauseGuard/android/app/src/main/java/com/clauseguard/app/ui/screens/ResultsScreen.kt', 'r') as f:
    text = f.read()

import_str = """
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.rounded.ContentCopy
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.text.buildAnnotatedString
"""

text = text.replace("import androidx.compose.material.icons.rounded.Info", "import androidx.compose.material.icons.rounded.Info\n" + import_str)

with open('/c/Users/Tanus/ClauseGuard/android/app/src/main/java/com/clauseguard/app/ui/screens/ResultsScreen.kt', 'w') as f:
    f.write(text)
