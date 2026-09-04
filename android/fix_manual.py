with open('app/src/main/java/com/clauseguard/app/ui/screens/HomeScreen.kt', 'r') as f:
    home = f.read()

home = home.replace(
"""    // Deep Mesh Gradient Background
    val backgroundBrush = Brush.verticalGradient(
        colors = listOf(
            Color(0xFF0A0A1A),
            Color(0xFF2D1B4E),
            Color(0xFF050507)
        )
    )

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(backgroundBrush)
    )""",
"""    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF050507))
    )"""
)

home = home.replace(
"""                        .background(
                            brush = Brush.linearGradient(
                                colors = listOf(Color(0xFF5E5CE6), Color(0xFF0A84FF))
                            ),
                            shape = CircleShape
                        )""",
"""                        .background(Color(0xFF5E5CE6), CircleShape)"""
)

with open('app/src/main/java/com/clauseguard/app/ui/screens/HomeScreen.kt', 'w') as f:
    f.write(home)


with open('app/src/main/java/com/clauseguard/app/ui/screens/ResultsScreen.kt', 'r') as f:
    res = f.read()

res = res.replace(
"""    // Deep Mesh Gradient Background
    val backgroundBrush = Brush.verticalGradient(
        colors = listOf(
            Color(0xFF0A0A1A), // Midnight Blue
            Color(0xFF2D1B4E), // Subtle Neon Purple
            Color(0xFF050507)  // Pure Black
        )
    )

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(backgroundBrush)
    )""",
"""    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF050507))
    )"""
)

res = res.replace(
"""                            .background(
                                brush = Brush.linearGradient(
                                    colors = listOf(Color(0xFF5E5CE6), Color(0xFF0A84FF))
                                ),
                                shape = CircleShape
                            )""",
"""                            .background(Color(0xFF5E5CE6), CircleShape)"""
)

res = res.replace(
"""                        .background(
                            brush = Brush.verticalGradient(
                                colors = listOf(Color(0xFFA191FF).copy(alpha = 0.15f), Color.Transparent)
                            ),
                            shape = RoundedCornerShape(16.dp)
                        )""",
"""                        .background(Color(0xFF5E5CE6).copy(alpha = 0.1f), RoundedCornerShape(16.dp))"""
)

with open('app/src/main/java/com/clauseguard/app/ui/screens/ResultsScreen.kt', 'w') as f:
    f.write(res)
