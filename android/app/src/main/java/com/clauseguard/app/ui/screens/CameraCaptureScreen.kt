package com.clauseguard.app.ui.screens

import android.app.Activity
import android.content.Context
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.IntentSenderRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Search
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.google.mlkit.vision.documentscanner.GmsDocumentScanner
import com.google.mlkit.vision.documentscanner.GmsDocumentScannerOptions
import com.google.mlkit.vision.documentscanner.GmsDocumentScannerOptions.RESULT_FORMAT_JPEG
import com.google.mlkit.vision.documentscanner.GmsDocumentScannerOptions.RESULT_FORMAT_PDF
import com.google.mlkit.vision.documentscanner.GmsDocumentScannerOptions.SCANNER_MODE_FULL
import com.google.mlkit.vision.documentscanner.GmsDocumentScanning
import com.google.mlkit.vision.documentscanner.GmsDocumentScanningResult

@Composable
fun CameraCaptureScreen(
    onDocumentCaptured: (ByteArray, String) -> Unit,
    onError: (String) -> Unit
) {
    val context = LocalContext.current

    // Configure the ML Kit Document Scanner:
    // SCANNER_MODE_FULL — provides edge detection, perspective correction, and crop UI
    // setGalleryImportAllowed — lets users pick existing photos from their gallery
    // setResultFormats — returns both a cropped JPEG (for OCR) and a PDF (for archival)
    // setPageLimit — max 10 pages per scan session
    val scannerOptions = GmsDocumentScannerOptions.Builder()
        .setScannerMode(SCANNER_MODE_FULL)
        .setGalleryImportAllowed(true)
        .setResultFormats(RESULT_FORMAT_PDF, RESULT_FORMAT_JPEG)
        .setPageLimit(10)
        .build()

    val scanner: GmsDocumentScanner = GmsDocumentScanning.getClient(scannerOptions)

    // Activity result launcher that receives the scanner's IntentSender result
    val scannerLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.StartIntentSenderForResult()
    ) { activityResult ->
        if (activityResult.resultCode == Activity.RESULT_OK) {
            val scanResult = GmsDocumentScanningResult.fromActivityResultIntent(activityResult.data)
            if (scanResult != null) {
                // Extract the first JPEG page for OCR processing
                val pages = scanResult.pages
                if (pages != null && pages.isNotEmpty()) {
                    val firstPageUri = pages[0].imageUri
                    val bytes = readBytesFromUri(context, firstPageUri)
                    if (bytes != null) {
                        onDocumentCaptured(bytes, "scanned_contract.jpg")
                    } else {
                        onError("Failed to read scanned image")
                    }
                } else {
                    onError("No pages captured")
                }
            } else {
                onError("Scanner returned no result")
            }
        }
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF050507)),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
            modifier = Modifier.padding(32.dp)
        ) {
            Icon(
                imageVector = Icons.Rounded.Search,
                contentDescription = "Document Scanner",
                tint = Color.White.copy(alpha = 0.6f),
                modifier = Modifier.size(80.dp)
            )

            Spacer(modifier = Modifier.height(24.dp))

            Text(
                text = "Scan Your Contract",
                color = Color.White,
                fontSize = 24.sp,
                fontWeight = FontWeight.Bold
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = "Position the document in the frame.\nEdge detection and perspective correction are automatic.",
                color = Color.Gray,
                fontSize = 14.sp,
                textAlign = TextAlign.Center,
                lineHeight = 20.sp
            )

            Spacer(modifier = Modifier.height(40.dp))

            Button(
                onClick = {
                    // Launch the native ML Kit Document Scanner UI
                    val activity = context as? Activity
                    if (activity != null) {
                        scanner.getStartScanIntent(activity)
                            .addOnSuccessListener { intentSender ->
                                scannerLauncher.launch(
                                    IntentSenderRequest.Builder(intentSender).build()
                                )
                            }
                            .addOnFailureListener { e ->
                                onError(e.message ?: "Failed to start scanner")
                            }
                    } else {
                        onError("Activity context required")
                    }
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp),
                shape = RoundedCornerShape(16.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer,
                    contentColor = MaterialTheme.colorScheme.onPrimaryContainer
                )
            ) {
                Text("Open Scanner", fontWeight = FontWeight.Bold, fontSize = 16.sp)
            }
        }
    }
}

private fun readBytesFromUri(context: Context, uri: android.net.Uri): ByteArray? {
    return try {
        context.contentResolver.openInputStream(uri)?.use { it.readBytes() }
    } catch (e: Exception) {
        null
    }
}