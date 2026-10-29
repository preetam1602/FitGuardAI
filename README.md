# FitGuard AI — Neural Health Intelligence System

> **"Predict Today. Prevent Tomorrow."**

FitGuard AI is a high-performance, medical-grade predictive platform designed to revolutionize preventive healthcare. By fusing real-time biometric data with advanced neural intelligence and LLM-driven medical personalization, the system identifies early health risk markers and generates tailored physiological and nutritional protocols.

![Design Aesthetic](https://img.shields.io/badge/Aesthetic-Cyberpunk_HUD-00ffc8?style=for-the-badge)
![Status](https://img.shields.io/badge/System-Active-00ffc8?style=for-the-badge)

---

## ⚡ Core Intelligence Modules

### 01. Biometric Fusion
Real-time integration of physiological data streams, including heart rate, blood pressure trends, age, height, weight, physical activity, sleep, and smoking habits.

### 02. Cardiovascular Risk Engine
10-year heart disease risk from the validated Framingham equation (D'Agostino 2008), a "heart age", blood pressure staging per the 2017 ACC/AHA guideline, and a breakdown of how much each modifiable factor (smoking, BP, BMI) adds to the user's risk. Deterministic and citable, with no trained model. See `backend/health_recommendation/README.md`.

### 03. AI Diet Blueprint (Groq)
Generates highly customized dietary guidelines, macronutrient targets, full meal plans, supplements, foods to avoid, and weekly habit tips powered by Groq Llama 3.3.

### 04. JWT Authentication
Secure JSON Web Token (JWT) system using `HS256` encryption to restrict access to user profile history and diet blueprints.

---

## 🎨 Design Philosophy: Cyberpunk HUD

The platform utilizes a **Cyberpunk Health HUD** aesthetic, designed to evoke the feeling of a professional medical terminal.

- **Palette**: Deep Space Background (`#030b0f`) with high-contrast Cyan Pulse highlights (`#00ffc8`).
- **Typography**: 
    - **Orbitron**: Used for headers and critical data readouts.
    - **DM Mono**: Used for clinical labels and technical descriptions.
- **Visual Effects**: 
    - **Scanlines & Grids**: Global CRT-style overlays for an immersive terminal experience.
    - **Glassmorphism**: Translucent panels with backdrop blurring for a premium, multi-layered feel.
    - **Heartbeat Animations**: Real-time pulsing indicators for system status and biometric data.

---

## 🛠 Technology Stack

### Frontend
- **React 18** + **Vite**: Blazing-fast interface with optimized production builds.
- **Vanilla CSS Variables & CSS Modules**: Custom design system for the Cyberpunk theme.
- **React Router**: Navigation between diagnostics.

### Backend
- **FastAPI**: Asynchronous Python framework for high-concurrency data processing.
- **PostgreSQL (`asyncpg`)**: High-performance asynchronous database storage replacing MongoDB.
- **Groq API**: LLM pipeline for dietary optimization.
- **Risk Engine**: Framingham CVD risk equation + ACC/AHA BP staging (pure Python, unit-tested).
- **JWT Auth**: PyJWT & bcrypt for cryptography.

---

## 🚀 System Initialization

### Prerequisites
- Node.js (v18+)
- Python (3.9+)
- PostgreSQL Database

### Configuration
Create a `.env` file inside the `backend/` directory:
```env
DATABASE_URL=postgresql://<username>:<password>@localhost:5432/<database_name>
GROQ_API_KEY=your_groq_api_key_here
SECRET_KEY=your_jwt_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
PORT=3001
DEBUG=false
FRONTEND_URL=http://localhost:5173/
```

### Backend Setup
1. Navigate to the backend directory and install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
2. Copy the example env file and configure your database + API keys:
   ```bash
   cp .env.example .env   # Windows: copy .env.example .env
   ```
3. Start the development server on **port 3001** (must match the Vite proxy in `frontend/vite.config.js`):
   ```bash
   python -m uvicorn server:app --app-dir src --reload --port 3001
   ```
   Or on Windows:
   ```powershell
   .\start.ps1
   ```
   > **Note:** Run the risk engine tests with `python -m pytest tests` from `backend/`.

### Frontend Setup
1. Navigate to the frontend directory and install dependencies:
   ```bash
   cd frontend
   npm install
   ```
2. (Optional) Copy `frontend/.env.example` to `.env` if you need a custom API URL for production builds.
3. Start the development server:
   ```bash
   npm run dev
   ```
   The frontend runs on **http://localhost:5173** and proxies `/api/*` requests to the backend at **http://localhost:3001**.

---

## 🔒 Security & Privacy
FitGuard AI implements a **Privacy First** protocol. All biometric data transmission is encrypted, passwords are hashed using bcrypt, and user-associated endpoints are secured using JSON Web Tokens (JWT) to ensure strict data isolation.

---

© 2026 FitGuard AI · Global Health Intelligence System

---

## 📚 Self-RAG Diet Pipeline

Diet blueprints are grounded in the documents placed in the git-ignored `data/` folder (e.g. `DGI_2024.pdf`, ICMR-NIN Dietary Guidelines for Indians). Code lives in `backend/src/rag/`. It adapts [Self-RAG](https://arxiv.org/abs/2310.11511) with prompted critics, keeping only the parts that don't hurt latency.

| Stage | What runs | Cost |
|---|---|---|
| **Retrieve** | Profile → ~9 focused queries. Dense (`bge-small-en-v1.5`) + BM25, fused with **RRF**. Round-robin pick so each concern is covered. | ~0.7–1 s |
| **Rerank** (conditional) | Cross-encoder (`ms-marco-MiniLM-L-6-v2`) **only** for queries where dense and BM25 disagree on the top hit; max 6 pairs / 1 s budget. | 0–0.5 s |
| **IsRel** | Reranker score if reranked, else dense score — no LLM call. | ~0 |
| **Generate** | Groq `GROQ_MODEL` (default `openai/gpt-oss-120b`) with cited `[n]` excerpts. If rate-limited, falls back to `GROQ_FALLBACK_MODEL` immediately instead of waiting. | ~3.5 s |
| **IsSup + IsUse** | One batched critic call on `CRITIC_MODEL` (`openai/gpt-oss-20b`, separate rate-limit bucket), 5 s timeout, no retries — on failure the blueprint is returned unverified. | ~0.8 s |
| **Correct** | Regenerate once with critic feedback **only** if unsupported (`no`) or usefulness < 3. | rare |

Skipped on purpose: the *Retrieve* critic (a diet plan always needs evidence) and beam search (multiplies generation calls).

The blueprint keeps its original fields and adds `guideline_notes`, `sources` (page refs, scores), `rag_grounded` and `self_rag` (critic verdict, regenerations, model used, per-stage `timings_ms`).

```bash
cd backend/src
python -m rag.ingest          # build index (auto-built at server startup if missing; --force to rebuild)
```

Endpoints: `POST /api/diet/recommend` (health data → prediction + grounded blueprint, no account needed; limited to 3 per hour per IP), `GET /api/rag/status`. `/api/health-assessment` uses the same pipeline.

Toggles (env): `RAG_RERANK`, `SELF_RAG_CRITIC`, `SELF_RAG_MAX_RETRIES`, `CRITIC_TIMEOUT_S`, `RAG_RERANK_MAX_PAIRS`, `RAG_RERANK_BUDGET_MS`.

> Groq's free tier allows ~8k tokens/min per model and one blueprint uses ~5k, so expect ~1 blueprint/minute before requests start waiting on the quota.
