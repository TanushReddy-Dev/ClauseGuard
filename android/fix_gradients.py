import re

def remove_gradients(path):
    with open(path, 'r') as f:
        text = f.read()

    # Remove the backgroundBrush entirely
    text = re.sub(r'val backgroundBrush = Brush\.verticalGradient\([^)]+\)', '', text)
    # Replace background(backgroundBrush) with background(MaterialTheme.colorScheme.surface) or Color(0xFF050507)
    text = text.replace('.background(backgroundBrush)', '.background(Color(0xFF050507))')
    text = text.replace('.background(backgroundBrush)', '.background(Color(0xFF050507))')
    
    # Replace the Brush.linearGradient with solid purple
    text = re.sub(r'brush = Brush\.linearGradient\([^)]+\)', 'color = Color(0xFF5E5CE6)', text)
    text = re.sub(r'brush = Brush\.verticalGradient\([^)]+\)', 'color = Color(0xFF5E5CE6).copy(alpha = 0.1f)', text)
    text = re.sub(r'brush = Brush\.horizontalGradient\([^)]+\)', 'color = Color(0xFF5E5CE6).copy(alpha = 0.1f)', text)

    with open(path, 'w') as f:
        f.write(text)

remove_gradients('app/src/main/java/com/clauseguard/app/ui/screens/HomeScreen.kt')
remove_gradients('app/src/main/java/com/clauseguard/app/ui/screens/ResultsScreen.kt')
