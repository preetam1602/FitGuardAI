# FitGuard AI

Simple health app.
- Frontend: React + Vite
- Backend: FastAPI
- ML model: in `backend/health_recommendation`

## 1) Start Backend
Open a terminal:

```powershell
cd "backend/src"
$env:MONGO_URI="your_mongodb_connection_string"
$env:DEBUG="true"
python -m uvicorn server:app --reload --host 0.0.0.0 --port 3001
```

If it starts, backend runs at:
- http://localhost:3001
- API docs: http://localhost:3001/docs

## 2) Start Frontend
Open a second terminal:

```powershell
cd "frontend"
npm install
npm run dev
```

Frontend usually runs at:
- http://localhost:5173

Open the frontend link in your browser.

## 3) Common Errors
### `Error loading ASGI app. Could not import module "app"`
Use this instead:

```powershell
cd "backend/src"
python -m uvicorn server:app --reload --host 0.0.0.0 --port 3001
```

### `npm run dev` fails
Run:

```powershell
cd "frontend"
npm install
npm run dev
```

### Mongo error / backend exits
Set valid `MONGO_URI` before running backend.

## 4) Project Structure
- `backend/src/server.py` -> FastAPI app
- `frontend/` -> UI
- `backend/health_recommendation/` -> ML code and data
