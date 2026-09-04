with open('/c/Users/Tanus/ClauseGuard/android/app/src/main/java/com/clauseguard/app/MainActivity.kt', 'r') as f:
    lines = f.readlines()
with open('/c/Users/Tanus/ClauseGuard/android/app/src/main/java/com/clauseguard/app/MainActivity.kt', 'w') as f:
    for line in lines:
        if line.strip() == "// ── Results: risk dial + clause cards ──":
            break
        f.write(line)
