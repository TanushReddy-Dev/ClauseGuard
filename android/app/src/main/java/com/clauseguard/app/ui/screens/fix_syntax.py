import re

def fix_syntax(path):
    with open(path, 'r') as f:
        text = f.read()

    bad_modifier = """        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 8.dp)
            ,
                ambientColor = Color.Transparent,
                shape = RoundedCornerShape(24.dp)
            )
            .background("""

    good_modifier = """        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 8.dp)
            .background("""

    text = text.replace(bad_modifier, good_modifier)
    
    with open(path, 'w') as f:
        f.write(text)

fix_syntax('/c/Users/Tanus/ClauseGuard/android/app/src/main/java/com/clauseguard/app/ui/screens/HomeScreen.kt')
