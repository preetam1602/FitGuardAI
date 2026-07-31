<div align="center">

# FitGuard AI
### Neural Health Intelligence Platform

**Predict Today. Prevent Tomorrow.**

[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-Async-009688?logo=fastapi&logoColor=white)](#)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-asyncpg-4169E1?logo=postgresql&logoColor=white)](#)
[![Groq](https://img.shields.io/badge/LLM-Groq%20Llama%203.3-F55036)](#)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](#)

</div>

---

## Overview

**FitGuard AI** is a predictive health-analytics platform that fuses real-time biometric data with machine learning and large language models to surface early cardiovascular and lifestyle risk indicators, and to generate personalized, evidence-informed nutrition and habit protocols.

The system is built for developers and health-tech teams who need a production-grade reference architecture combining a modern async backend, an ML inference layer, and LLM-driven personalization — wrapped in a distinctive, high-contrast "medical terminal" interface.

> **Disclaimer:** FitGuard AI is a technology demonstration and decision-support tool. It is **not** a certified medical device and does not provide medical diagnoses. Outputs should not replace professional clinical judgment. Always consult a licensed healthcare provider before making health decisions.

---

## Core Intelligence Modules

| Module | Description |
|---|---|
| **01 · Biometric Fusion** | Real-time ingestion and normalization of physiological signals — heart rate, blood pressure trends, age, height, weight, activity level, sleep, and smoking status. |
| **02 · Neural Risk Prediction** | Scikit-learn models trained to project blood pressure trajectories and output structured, tiered cardiovascular and lifestyle risk assessments. |
| **03 · AI Diet Blueprint** | Groq-hosted Llama 3.3 generates individualized macronutrient targets, structured meal plans, supplement guidance, foods to avoid, and weekly habit-formation tips. |
| **04 · Secure Access Layer** | JWT (HS256) authentication with bcrypt password hashing, enforcing strict per-user data isolation across profile history and diet blueprint endpoints. |

---

## Design Philosophy — Cyberpunk Health HUD

The interface is designed to evoke a professional diagnostic terminal: precise, high-signal, and immersive.

- **Palette** — Deep-space background (`#030b0f`) paired with high-contrast cyan-pulse accents (`#00ffc8`) for critical readouts and status indicators.
- **Typography** — *Orbitron* for headers and primary data readouts; *DM Mono* for clinical labels and technical annotations.
- **Visual System**
  - CRT-style scanline and grid overlays for terminal-grade immersion
  - Glassmorphic panels with backdrop blur for a layered, premium feel
  - Real-time heartbeat-pulse animations tied to system and biometric status

---

## Technology Stack

**Frontend**
- React 18 + Vite — optimized dev experience and production builds
- CSS Modules with a custom CSS-variable design system
- React Router — navigation across diagnostic views

**Backend**
- FastAPI — asynchronous Python framework for high-concurrency workloads
- PostgreSQL via `asyncpg` — high-performance async data layer
- Groq API — LLM inference pipeline for dietary personalization
- Scikit-learn — trained models for health risk assessment
- PyJWT + bcrypt — authentication and credential security

---

## Getting Started

### Prerequisites

| Requirement | Version |
|---|---|
| Node.js | ≥ 18 |
| Python | ≥ 3.9 |
| PostgreSQL | Any recent stable release |

### Environment Configuration

Create a `.env` file inside `backend/`:

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

> Never commit `.env` files. Rotate `SECRET_KEY` and `GROQ_API_KEY` for each environment (dev / staging / production).

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn server:app --app-dir src --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`, and the API at `http://localhost:3001`.

---

## Security & Privacy

FitGuard AI follows a **privacy-first** design posture:

- All biometric data in transit is encrypted
- Passwords are hashed with **bcrypt** — never stored in plaintext
- All user-associated endpoints require a valid **JWT**, enforcing strict data isolation between accounts
- Diet blueprints and risk history are scoped exclusively to the authenticated user

---

## Roadmap

- [ ] Wearable device integrations (Apple Health, Fitbit, Garmin)
- [ ] Longitudinal risk trend visualization
- [ ] Multi-language diet blueprint generation
- [ ] Clinician-facing dashboard and export (PDF/HL7)
- [ ] Role-based access control for care-team accounts

---

## Contributing

Contributions are welcome. Please open an issue to discuss significant changes before submitting a pull request, and ensure new features include appropriate tests and documentation updates.

## License

Distributed under the MIT License. See `LICENSE` for details.

---

<div align="center">

**© 2026 FitGuard AI · Global Health Intelligence System**

</div>
