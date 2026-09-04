with open('app/src/main/java/com/clauseguard/app/MainActivity.kt', 'r') as f:
    text = f.read()

old_shimmer = """        // ── Shimmer Placeholders ──
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
        }"""

new_shimmer = """        // ── Shimmer Placeholders (Emil Kowalski Staggered Entrance) ──
        if (uiState is UiState.Loading) {
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                contentPadding = PaddingValues(top = 100.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                userScrollEnabled = false
            ) {
                items(4) { index ->
                    var isVisible by remember { mutableStateOf(false) }
                    
                    LaunchedEffect(Unit) {
                        // Stagger delay: 80ms between items
                        kotlinx.coroutines.delay(index * 80L)
                        isVisible = true
                    }
                    
                    // Emil: Scale entrance starts from 0.95, not 0
                    val scale by animateFloatAsState(
                        targetValue = if (isVisible) 1f else 0.95f,
                        animationSpec = spring(dampingRatio = 0.8f, stiffness = 400f),
                        label = "shimmer_scale"
                    )
                    
                    val alpha by animateFloatAsState(
                        targetValue = if (isVisible) 1f else 0f,
                        animationSpec = tween(300),
                        label = "shimmer_alpha"
                    )

                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 16.dp, vertical = 8.dp)
                            .height(110.dp)
                            .graphicsLayer {
                                scaleX = scale
                                scaleY = scale
                                this.alpha = alpha
                            }
                            .clip(RoundedCornerShape(24.dp))
                            .background(Color.White.copy(alpha = 0.03f)) // Subtler base
                            .border(1.dp, Color.White.copy(alpha = 0.08f), RoundedCornerShape(24.dp))
                            .shimmerEffect()
                    )
                }
            }
        }"""

text = text.replace(old_shimmer, new_shimmer)

with open('app/src/main/java/com/clauseguard/app/MainActivity.kt', 'w') as f:
    f.write(text)
