import os

path = "app/src/main/java/com/clauseguard/app/ui/screens/HomeScreen.kt"

with open(path, 'r') as f:
    text = f.read()

import_str = """
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
"""

# Actually put them at the top of the file
text = text.replace("package com.clauseguard.app.ui.screens", "package com.clauseguard.app.ui.screens\n" + import_str)

with open(path, 'w') as f:
    f.write(text)
