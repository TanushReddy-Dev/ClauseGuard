import os

path = "app/src/main/java/com/clauseguard/app/ui/screens/HomeScreen.kt"

with open(path, 'r') as f:
    text = f.read()

import_str = """
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
"""

text = text.replace("import androidx.compose.ui.draw.scale", "import androidx.compose.ui.draw.scale" + import_str)
text = text.replace("androidx.compose.ui.hapticfeedback.HapticFeedbackType", "HapticFeedbackType")
text = text.replace("androidx.compose.ui.draw.rotate", "rotate")

with open(path, 'w') as f:
    f.write(text)
