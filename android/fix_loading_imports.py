with open('app/src/main/java/com/clauseguard/app/ui/components/ScanningOverlay.kt', 'r') as f:
    text = f.read()

text = text.replace("import androidx.compose.material.icons.rounded.AutoAwesome", "")

with open('app/src/main/java/com/clauseguard/app/ui/components/ScanningOverlay.kt', 'w') as f:
    f.write(text)
