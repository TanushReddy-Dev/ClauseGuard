with open('app/src/main/java/com/clauseguard/app/ui/screens/HomeScreen.kt', 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.strip() in ['import rotate', 'import HapticFeedbackType']:
        continue
    if "import androidx.compose.ui.draw.scale" in line:
        new_lines.append(line)
        new_lines.append("import androidx.compose.ui.draw.rotate\n")
        new_lines.append("import androidx.compose.ui.hapticfeedback.HapticFeedbackType\n")
        continue
    new_lines.append(line)

with open('app/src/main/java/com/clauseguard/app/ui/screens/HomeScreen.kt', 'w') as f:
    f.writelines(new_lines)
