import re

def declutter2(path):
    with open(path, 'r') as f:
        text = f.read()

    # Remove shadows entirely for the true clean, flat look requested
    text = re.sub(r'\.shadow\([^)]+\)\s*', '', text)
    
    with open(path, 'w') as f:
        f.write(text)

declutter2('app/src/main/java/com/clauseguard/app/ui/screens/HomeScreen.kt')
declutter2('app/src/main/java/com/clauseguard/app/ui/screens/ResultsScreen.kt')
