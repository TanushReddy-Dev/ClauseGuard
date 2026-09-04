# ClauseGuard ⚖️🛡️

*Empowering workers and consumers by exposing predatory contract clauses in seconds.*

---

## 🛑 The Problem & 💡 The Solution

**The Problem:** Legal contracts are intentionally dense, opaque, and heavily skewed in favor of the drafter. For gig workers, freelancers, and everyday consumers, hiring a lawyer to review standard agreements is cost-prohibitive. Consequently, people routinely sign away their rights—falling victim to broad non-competes, aggressive IP assignments, and hidden arbitration mandates.

**The Solution:** ClauseGuard puts a legal expert in your pocket. Using edge-native OCR and an advanced 6-stage LLM pipeline, ClauseGuard instantly scans physical documents, isolates high-risk clauses, calculates a deterministic risk score, and arms you with a tailored negotiation strategy—all before you pick up a pen.

---

## 🏗️ System Architecture

ClauseGuard uses a hybrid architecture combining secure on-device processing with a powerful, deterministic AI backend.

```text
  [Physical Contract] 
          │
          ▼
┌───────────────────┐      1. Local edge OCR preserves privacy.
│  Android Client   │         Images never leave the device.
│    (CameraX)      │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐      2. Raw text is securely transmitted
│  Google ML Kit    │         over HTTPS to our infrastructure.
│ (On-Device OCR)   │
└─────────┬─────────┘
          │
          ▼
    [Raw Text String]
          │
 ══(Cloudflare Tunnel)══   3. Secure tunnel bypasses local network blocks.
          │
          ▼
┌───────────────────┐      4. 6-stage agentic pipeline extracts and
│ FastAPI Backend   │         classifies legal language.
└─────────┬─────────┘
          │
     ┌────┴────┐
     ▼         ▼
┌────────┐ ┌────────┐      5. Hybrid Engine:
│  Qwen  │ │ Pandas │         The LLM provides natural language extraction
│  LLM   │ │ Engine │         and negotiation scripts. Pandas enforces strict,
└────────┘ └────────┘         deterministic risk scoring rules for consistency.
     │         │
     └────┬────┘
          ▼
 [Analysis Report JSON]    6. Data flows back to the client.
          │
          ▼
┌───────────────────┐      7. Premium Native UX:
│ Jetpack Compose   │         Physics-based 3D card flips, frosted glass overlays,
│  UI / Animations  │         and animated risk dials render the results.
└───────────────────┘
```

---

## 🛠️ Tech Stack Breakdown

### Frontend (Native Android)
*   **Kotlin & Jetpack Compose:** Fully declarative, state-driven UI.
*   **CameraX:** Full-bleed, lifecycle-aware hardware camera integration.
*   **Google ML Kit:** On-device Text Recognition (OCR) without network latency.
*   **Animations:** Apple-inspired, Emil Kowalski-style physics-based spring animations (`animateFloatAsState`, `Spring.DampingRatioMediumBouncy`) and 3D graphics layer transforms.
*   **Retrofit & kotlinx.serialization:** Robust, type-safe network layer.

### Backend (API & Data)
*   **Python 3 & FastAPI:** High-performance, asynchronous REST API.
*   **Pandas:** Deterministic rule engine ensuring risk scores are calculated via strict heuristics rather than unpredictable LLM hallucinations.
*   **Cloudflare Tunnels (`cloudflared`):** Exposes the local backend to the public internet securely, bypassing hackathon/local Wi-Fi subnet restrictions.

### AI & Inference
*   **Featherless AI:** Serverless, zero-cost AI model routing infrastructure.
*   **Qwen LLM:** Highly capable open-source large language model responsible for the 6-stage agentic workflow (extracting clauses, categorizing risk types, and generating the negotiation script).

---

## 🚀 Setup & Installation

### 1. Backend Setup
Navigate to the backend directory, set up your Python environment, and start the FastAPI server:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Export your Featherless AI key
export FEATHERLESS_API_KEY="your_api_key_here"

# Start the FastAPI server
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. Cloudflare Tunnel
In a new terminal, expose your local port 8000 using Cloudflare:
```bash
cloudflared tunnel --url http://localhost:8000
```
*Note the generated `.trycloudflare.com` HTTPS URL.*

### 3. Android Setup
1. Open the `/android` folder in **Android Studio**.
2. Open `app/build.gradle.kts`.
3. Locate the `BASE_URL` build config field and replace it with your active Cloudflare tunnel URL:
   ```kotlin
   buildConfigField("String", "BASE_URL", "\"https://your-tunnel-url.trycloudflare.com/\"")
   ```
4. Sync Gradle.
5. Build and run on a **physical Android device** (CameraX and ML Kit require real hardware to function correctly).

---

## 🌟 Key Differentiators

*   **Privacy First (Edge OCR):** We respect user privacy. Contract photos are processed entirely on-device using ML Kit. Only the raw extracted text strings are transmitted to the backend, meaning no sensitive images are ever stored on a server.
*   **Deterministic + Generative Hybrid:** LLMs are great at parsing text but terrible at math and consistency. ClauseGuard uses the LLM purely for text extraction and classification, routing the output into a **Pandas-based deterministic engine** that calculates the final risk score. You get the intelligence of generative AI with the reliability of standard software.
*   **Premium, Tactile UI:** The app rejects cross-platform UI jank. Built entirely in native Jetpack Compose, the interface utilizes frosted glass blurring, spring-physics 3D flip cards, and smoothly animated Canvas dials to make reviewing dense legal text engaging and digestible.
*   **Zero-Cost OSS Routing:** By utilizing the open-source Qwen model served via Featherless AI, the operational pipeline remains incredibly cost-effective compared to proprietary, locked-in alternatives.