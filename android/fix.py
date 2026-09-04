import re

with open('/c/Users/Tanus/ClauseGuard/android/app/src/main/java/com/clauseguard/app/ui/screens/ResultsScreen.kt', 'r') as f:
    text = f.read()

# Remove the summary item
text = re.sub(r'item\s*\{\s*Text\(\s*text\s*=\s*report\.summary[\s\S]*?modifier\s*=\s*Modifier\.padding\(horizontal\s*=\s*24\.dp\,\s*vertical\s*=\s*8\.dp\)\s*\)\s*\}', '', text)

with open('/c/Users/Tanus/ClauseGuard/android/app/src/main/java/com/clauseguard/app/ui/screens/ResultsScreen.kt', 'w') as f:
    f.write(text)
