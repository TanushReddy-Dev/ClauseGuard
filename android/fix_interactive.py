import re

def fix_file(path):
    with open(path, 'r') as f:
        text = f.read()

    # Fix imports
    text = text.replace("import androidx.compose.material.icons.rounded.ContentCopy", "import androidx.compose.material.icons.rounded.Share\nimport androidx.compose.foundation.layout.wrapContentHeight")
    
    # Replace ContentCopy icon
    text = text.replace("Icons.Rounded.ContentCopy", "Icons.Rounded.Share")

    with open(path, 'w') as f:
        f.write(text)

fix_file('/c/Users/Tanus/ClauseGuard/android/app/src/main/java/com/clauseguard/app/ui/screens/InteractiveDocument.kt')
