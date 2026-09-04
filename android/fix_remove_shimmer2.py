with open('app/src/main/java/com/clauseguard/app/MainActivity.kt', 'r') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if "// ── Shimmer Placeholders ──" in line:
        skip = True
    if skip and "ScanningOverlay(isLoading = uiState is UiState.Loading)" in line:
        skip = False
        new_lines.append("        // ── Frosted-glass scanning overlay ──\n")
    if not skip:
        new_lines.append(line)

with open('app/src/main/java/com/clauseguard/app/MainActivity.kt', 'w') as f:
    f.writelines(new_lines)
