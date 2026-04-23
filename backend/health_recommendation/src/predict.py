import joblib
import os

try:
    from preprocess import preprocess_data
except ModuleNotFoundError:
    from src.preprocess import preprocess_data

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "model.pkl")

model = joblib.load(MODEL_PATH)


def predict_bp(input_data: dict):

    processed = preprocess_data(input_data, training=False)

    prediction = model.predict(processed)

    return float(prediction[0])