# ClauseGuard
> Exposing predatory contract clauses in seconds through edge-native OCR and hybrid AI deterministic scoring.

---

## The Problem & Solution

**The Problem:** Everyday consumers and gig workers sign away their rights because hiring a lawyer to review dense, opaque legal contracts is cost-prohibitive. As a result, people routinely fall victim to broad non-competes, aggressive IP assignments, and hidden binding arbitration traps.

**The Solution:** ClauseGuard serves as a legal expert in your pocket. By combining on-device OCR with a 6-stage hybrid LLM pipeline, the system instantly isolates high-risk clauses, calculates a deterministic risk score, and provides actionable negotiation scripts—all before you sign.

---

## System Architecture

```text
[ Physical Contract ]
         │
         ▼
┌───────────────────┐    1. Local edge OCR preserves privacy.
│  Android Client   │       Images never leave the device.
│    (CameraX)      │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐    2. Extracted text transmitted securely.
│  Google ML Kit    │       Only raw text strings are sent.
└─────────┬─────────┘
          │
  (Cloudflare Tunnel)    3. Zero-trust HTTPS bypasses restrictive subnets.
          │
          ▼
┌───────────────────┐    4. High-performance async endpoint handles
│  FastAPI Backend  │       incoming payload.
└─────────┬─────────┘
          │
     ┌────┴────┐
     ▼         ▼
┌────────┐ ┌────────┐    5. Hybrid Engine: LLM parses and classifies;
│  Qwen  │ │ Pandas │       Pandas enforces strict risk scoring rules
│  LLM   │ │ Engine │       to eliminate math hallucinations.
└────────┘ └────────┘
     │         │
     └────┬────┘
          ▼
[ JSON Risk Report  ]    6. Rendered natively with physics-based
          │                 3D flip cards and frosted glass UI.
          ▼
┌───────────────────┐
│  Jetpack Compose  │
└───────────────────┘
```

---

## Technology Stack

| Architectural Layer | Technologies Used |
| :--- | :--- |
| **Frontend** | Android, Kotlin, Jetpack Compose, CameraX, Material 3 |
| **Backend** | Python 3, FastAPI, Retrofit, Cloudflared (Tunnels) |
| **AI/ML Infrastructure** | Google ML Kit (Edge OCR), Featherless AI, Qwen LLM |
| **Data & Logic** | Pandas (Deterministic Rule Engine) |

---

## Frictionless Installation

### 1. Backend & AI Pipeline
```bash
# Clone the repository and setup Python environment
cd ClauseGuard/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure AI Routing (Featherless AI)
export FEATHERLESS_API_KEY="your_api_key_here"

# Spin up the FastAPI server
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. Network Tunneling
```bash
# Expose the local backend securely via Cloudflare
cloudflared tunnel --url http://localhost:8000
# Note the generated HTTPS URL (e.g., https://your-tunnel.trycloudflare.com)
```

### 3. Android Client
```bash
# Navigate to the Android project root
cd ../android

# Update the API endpoint in your build configuration
# Edit android/app/build.gradle.kts:
# buildConfigField("String", "BASE_URL", "\"https://your-tunnel.trycloudflare.com/\"")

# Clean and build the APK
./gradlew clean assembleDebug
```
*Note: Deploy to a physical Android device to test CameraX and ML Kit functionality.*

---

## Core Differentiators

* **Privacy-First Edge Processing:** Contract photos are processed entirely on-device using ML Kit OCR. Only raw extracted text strings transmit to the cloud, guaranteeing sensitive legal images are never stored or intercepted.
* **Hybrid Deterministic Scoring:** Generative AI is used strictly for natural language extraction and classification, feeding directly into a **Pandas-based deterministic rule engine**. This eliminates LLM hallucination in risk scoring, ensuring enterprise-grade consistency.
* **Zero-Cost OSS Routing:** Utilizing the open-source Qwen model served via Featherless AI allows the 6-stage agentic workflow to operate at zero API token cost, bypassing the massive financial overhead of proprietary cloud AI models.
