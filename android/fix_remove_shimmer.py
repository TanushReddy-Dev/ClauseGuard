import re

with open('app/src/main/java/com/clauseguard/app/MainActivity.kt', 'r') as f:
    text = f.read()

# Match the old shimmer block exactly as it appears in the current file
shimmer_block = r"""        // ── Shimmer Placeholders ──
        if \(uiState is UiState\.Loading\) \{
            LazyColumn\(
                modifier = Modifier\.fillMaxSize\(\),
                contentPadding = PaddingValues\(top = 100\.dp\),
                horizontalAlignment = Alignment\.CenterHorizontally,
                userScrollEnabled = false
            \) \{
                items\(4\) \{
                    Box\(
                        modifier = Modifier
                            \.fillMaxWidth\(\)
                            \.padding\(horizontal = 16\.dp, vertical = 8\.dp\)
                            \.height\(100\.dp\)
                            \.clip\(RoundedCornerShape\(16\.dp\)\)
                            \.shimmerEffect\(\)
                    \)
                \}
            \}
        \}

"""

# Alternatively, just use string replace for safety
exact_str = """        // ── Shimmer Placeholders ──
        if (uiState is UiState.Loading) {
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                contentPadding = PaddingValues(top = 100.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                userScrollEnabled = false
            ) {
                items(4) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 16.dp, vertical = 8.dp)
                            .height(100.dp)
                            .clip(RoundedCornerShape(16.dp))
                            .shimmerEffect()
                    )
                }
            }
        }

"""

text = text.replace(exact_str, "")

with open('app/src/main/java/com/clauseguard/app/MainActivity.kt', 'w') as f:
    f.write(text)
