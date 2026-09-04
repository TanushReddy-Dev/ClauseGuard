import os

path = "app/src/main/java/com/clauseguard/app/ui/screens/HomeScreen.kt"

with open(path, 'r') as f:
    text = f.read()

# Add haptics and rotation to the FAB
text = text.replace(
"""            // Main FAB
            FloatingActionButton(
                onClick = { isFabExpanded = !isFabExpanded },
                containerColor = Color(0xFF5E5CE6),
                contentColor = Color.White,
                shape = CircleShape,
                modifier = Modifier.size(56.dp)
            ) {
                Icon(
                    imageVector = if (isFabExpanded) Icons.Rounded.Close else Icons.Rounded.Add,
                    contentDescription = "New Scan",
                    modifier = Modifier.size(24.dp)
                )
            }""",
"""            // Main FAB
            val haptics = LocalHapticFeedback.current
            val fabRotation by animateFloatAsState(
                targetValue = if (isFabExpanded) 45f else 0f,
                animationSpec = spring(dampingRatio = 0.8f, stiffness = 400f),
                label = "fab_rotation"
            )
            FloatingActionButton(
                onClick = {
                    haptics.performHapticFeedback(androidx.compose.ui.hapticfeedback.HapticFeedbackType.TextHandleMove)
                    isFabExpanded = !isFabExpanded
                },
                containerColor = Color(0xFF5E5CE6),
                contentColor = Color.White,
                shape = CircleShape,
                modifier = Modifier.size(56.dp)
            ) {
                Icon(
                    imageVector = Icons.Rounded.Add,
                    contentDescription = "New Scan",
                    modifier = Modifier.size(24.dp).androidx.compose.ui.draw.rotate(fabRotation)
                )
            }"""
)

# Fix the spring in AnimatedVisibility
text = text.replace(
"""                    animationSpec = spring(
                        dampingRatio = Spring.DampingRatioMediumBouncy,
                        stiffness = Spring.StiffnessMedium
                    )""",
"""                    animationSpec = spring(
                        dampingRatio = 0.8f,
                        stiffness = 400f
                    )"""
)

with open(path, 'w') as f:
    f.write(text)
