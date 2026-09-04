import re

def declutter(path):
    with open(path, 'r') as f:
        text = f.read()

    # Remove Deep Mesh Gradient definitions
    text = re.sub(r'val backgroundBrush = Brush\.verticalGradient\([\s\S]*?\)\s*', '', text)
    
    # Replace background(backgroundBrush) with pure black
    text = text.replace('.background(backgroundBrush)', '.background(Color(0xFF000000))')
    
    # Replace linear gradients with solid subtle color
    text = re.sub(r'brush\s*=\s*Brush\.linearGradient\([^)]+\)', 'color = Color(0xFF2C2C2E)', text)
    text = re.sub(r'brush\s*=\s*Brush\.verticalGradient\([^)]+\)', 'color = Color(0xFF1C1C1E)', text)
    text = re.sub(r'brush\s*=\s*Brush\.horizontalGradient\([^)]+\)', 'color = Color(0xFF1C1C1E)', text)

    # Simplify shadows and borders to feel more Apple-like (flat/subtle)
    text = re.sub(r'\.shadow\(\s*elevation = 16\.dp,\s*spotColor = Color\([^)]+\)\.copy\(alpha = 0\.5f\),\s*ambientColor = Color\.Transparent\s*\)', '', text)
    text = re.sub(r'\.shadow\(\s*elevation = 32\.dp,\s*spotColor = Color\.Black\.copy\(alpha = 0\.4f\),\s*ambientColor = Color\.Transparent,\s*shape = RoundedCornerShape\(24\.dp\)\s*\)', '', text)

    # Change 0xFF5E5CE6 (bright purple) to an iOS system-like Blue or subtle Gray where appropriate
    text = text.replace('Color(0xFF5E5CE6)', 'Color(0xFF0A84FF)')

    with open(path, 'w') as f:
        f.write(text)

declutter('app/src/main/java/com/clauseguard/app/ui/screens/HomeScreen.kt')
declutter('app/src/main/java/com/clauseguard/app/ui/screens/ResultsScreen.kt')
