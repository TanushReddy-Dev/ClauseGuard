import re

def fix_file(path):
    with open(path, 'r') as f:
        text = f.read()

    # Fix HomeScreen syntax
    bad = r"""\.padding\(vertical = 8\.dp\)
            ,
                ambientColor = Color\.Transparent,
                shape = RoundedCornerShape\(24\.dp\)
            \)
            \.background"""
    good = """.padding(vertical = 8.dp)
            .background"""
    text = re.sub(bad, good, text)

    with open(path, 'w') as f:
        f.write(text)

fix_file('app/src/main/java/com/clauseguard/app/ui/screens/HomeScreen.kt')
