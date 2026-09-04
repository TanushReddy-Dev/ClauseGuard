# ClauseGuard

Exposing predatory contract clauses in seconds through edge-native scanning and Groq-powered multi-agent AI.

## The Problem & The Solution

**The Problem:** Everyday consumers and gig workers sign away their rights because hiring a lawyer to review dense, opaque legal contracts is cost-prohibitive. As a result, people routinely fall victim to broad non-competes, aggressive IP assignments, and hidden binding arbitration traps.

**The Solution:** ClauseGuard serves as a legal expert in your pocket. By combining on-device ML Kit document scanning with an ultra-fast, Groq-accelerated LLM pipeline, the system instantly isolates high-risk clauses, calculates a risk score, and provides actionable negotiation scripts—all safely persisted in a local on-device vault.

## System Architecture

```text
[ Physical Contract / PDF / DOCX ]
                │
                ▼
  ┌───────────────────┐    1. Ingestion: ML Kit Document Scanner provides edge 
  │  Android Client   │       detection & OCR. Users can also natively upload
  │ (Jetpack Compose) │       PDF and DOCX files.
  └─────────┬─────────┘
                │
         (Cloudflare Tunnel)   2. Zero-trust HTTPS tunnel bypasses restrictive subnets.
                │
                ▼
  ┌───────────────────┐    3. Asyncio API: High-performance backend intercepts
  │  FastAPI Backend  │       the payload and checks the Local Cache Layer to
  │  & Caching Layer  │       bypass LLM processing for known contracts.
  └─────────┬─────────┘
                │
           ┌────┴────┐
           ▼         ▼
  ┌────────┐ ┌────────┐    4. Hybrid Engine: Groq LPUs execute a multi-agent
  │  Groq  │ │ Pandas │       chain in parallel for zero-latency extraction, 
  │  LPUs  │ │ Engine │       while Pandas enforces strict risk scoring math.
  └────────┘ └────────┠────────┘
                │         │
                └────┬────┘
                      ▼
  [ JSON Risk Report ]    5. Delivery: Rendered natively with physics-based
                │                 3D flip cards and frosted glass UI.
                ▼
  ┌───────────────────┐    6. Secure Vault: Analysis is saved to an on-device
  │ Room DB (Android) │       Room Database, guaranteeing absolute data 
  └───────────────────┝       sovereignty with zero cloud storage dependency.
                    │
```

## Technology Stack

| Architectural Layer | Technologies Used |
| :--- | :--- |
| **Frontend** | Android, Kotlin, Jetpack Compose, Material 3 |
| **Local Storage** | Room Database, Kotlin Coroutines (Flow) |
| **Backend** | Python 3, FastAPI, Asyncio, Cloudflared (Tunnels) |
| **AI/ML Infrastructure** | Google ML Kit (Edge Document Scanner), Groq LPUs |
| **Data & Logic** | Pandas (Deterministic Rule Engine), Intelligent Caching |

## Frictionless Installation

### 1. Backend & AI Pipeline

```bash
# Clone the repository and setup Python environment
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure AI Routing (Groq API)
export GROQ_API_KEY="your_groq_api_key_here"

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
cd android

# Update the API endpoint in your build configuration
# Edit android/app/build.gradle.kts:
# buildConfigField("String", "BASE_URL", "\"https://your-tunnel.trycloudflare.com/\"")

# Clean and build the APK
./gradlew clean assembleDebug
```

*Note: Deploy to a physical Android device to test the ML Kit Document Scanner and Haptics functionality.*

## Core Differentiators

* **Absolute Data Sovereignty:** Contract photos are processed entirely on-device using ML Kit, and all highly sensitive contract analyses are persisted strictly on the device using a native Room Database. Zero cloud storage lock-in.
* **Ultra-Low Latency Inference:** By replacing standard API bottlenecks with Groq LPUs and implementing Asyncio parallelism, the backend executes its complex multi-agent workflow in a fraction of a second. A local caching layer instantly serves identical requests to completely bypass API round-trips.
* **Hybrid Deterministic Scoring:** Generative AI handles natural language extraction, feeding directly into a Pandas-based deterministic rule engine. This eliminates LLM hallucination in risk scoring, ensuring enterprise-grade math and consistency.
* **Premium Tactile UX:** A fully native Compose interface rejects cross-platform jank, featuring 60fps physics-based 3D flip cards, frosted glass overlays, and dynamic haptic feedback.