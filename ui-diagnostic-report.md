# UI Diagnostic Report

### 1. Blur Bleed (Text Ghosting)
* **File:** `ScanningOverlay.kt`
* **Anti-pattern:** `Modifier.blur()` is applied directly to the parent `Box` containing the `Text` composable.
* **Explanation:** When `Modifier.blur()` is applied to a layout container, it blurs the container *and all of its children*. This causes the "Analyzing contract…" text to blur into an illegible smudge as the animation progresses. To fix this, the blur must be applied to an empty sibling `Box` that sits behind the text, or applied via a `graphicsLayer` rendering effect specifically on the background element.

### 2. Recomposition Thrashing (Animation Stutter)
* **File:** `ScanningOverlay.kt`
* **Anti-pattern:** State read of `blurRadius.value` occurs directly in the composition phase.
* **Explanation:** Because `blurRadius.value.dp` is read inside the `Modifier.blur()` call directly in the composition tree, Jetpack Compose is forced to invalidate and recompose the entire `Box` on every single frame of the 600ms animation. This causes heavy CPU thrashing and frame drops. High-frequency animation state should be read inside the drawing phase (e.g., inside a `graphicsLayer { ... }` block) to bypass the recomposition phase entirely.

### 3. Transparency Overlap & Z-Index Bleed
* **File:** `ClauseCard.kt`
* **Anti-pattern:** Switching view states mid-flip without strict layer opacity.
* **Explanation:** During the `rotationY` flip animation, the UI swaps between the front and back column exactly when `rotation <= 90f`. Because the internal `Box` lacks a strict, opaque `Modifier.background()`, the hardware layer can momentarily blend or ghost the text rendering from the back face through the front face during the frame transition. 

### 4. 3D Perspective Distortion
* **File:** `ClauseCard.kt`
* **Anti-pattern:** Improper `cameraDistance` scaling (Currently mitigated but critical).
* **Explanation:** The `graphicsLayer` correctly implements `cameraDistance = 12f * density`. If this property were ever omitted or set too low, the default camera distance would cause extreme perspective distortion during the Y-axis rotation. The edges of the card would artificially stretch towards the viewer, clipping out of bounds and causing severe visual artifacts during the tap interaction.