# FitGuard AI — Neural Health Intelligence System

> **"Predict Today. Prevent Tomorrow."**

FitGuard AI is a high-performance, medical-grade predictive platform designed to revolutionize preventive healthcare. By fusing real-time biometric data with advanced neural intelligence and LLM-driven medical personalization, the system identifies early health risk markers and generates tailored physiological and nutritional protocols.

![Design Aesthetic](https://img.shields.io/badge/Aesthetic-Cyberpunk_HUD-00ffc8?style=for-the-badge)
![Status](https://img.shields.io/badge/System-Active-00ffc8?style=for-the-badge)

---

## ⚡ Core Intelligence Modules

### 01. Biometric Fusion
Real-time integration of physiological data streams, including heart rate, blood pressure trends, age, height, weight, physical activity, sleep, and smoking habits.

### 02. Neural Risk Prediction
Proprietary machine learning models trained to predict blood pressure trends, risk levels, and output structured cardiovascular and lifestyle recommendations.

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
- **Machine Learning**: Scikit-learn based predictive models for health risk assessment.
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
2. Start the development server using Uvicorn (pointing to `src` directory):
   ```bash
   python -m uvicorn server:app --app-dir src --reload
   ```

### Frontend Setup
1. Navigate to the frontend directory and install dependencies:
   ```bash
   cd frontend
   npm install
   ```
2. Start the development server:
   ```bash
   npm run dev
   ```

---

## 🔒 Security & Privacy
FitGuard AI implements a **Privacy First** protocol. All biometric data transmission is encrypted, passwords are hashed using bcrypt, and user-associated endpoints are secured using JSON Web Tokens (JWT) to ensure strict data isolation.

---

© 2026 FitGuard AI · Global Health Intelligence System
