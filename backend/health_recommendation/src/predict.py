import joblib
import logging
import os

try:
    from preprocess import preprocess_data
except ModuleNotFoundError:
    from src.preprocess import preprocess_data

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "models", "scaler.pkl")

_model = None


def _ensure_models():
    global _model
    if _model is not None:
        return

    if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
        logger.warning("ML model files not found — training model automatically...")
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        try:
            import train  # noqa: F401 — trains and saves model on import
        except ModuleNotFoundError:
            import src.train  # noqa: F401

    _model = joblib.load(MODEL_PATH)


def predict_bp(input_data: dict):
    _ensure_models()
    processed = preprocess_data(input_data, training=False)
    prediction = _model.predict(processed)
    return float(prediction[0])