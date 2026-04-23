from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from src.preprocess import preprocess_data
import joblib
import os


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "model.pkl")


X_train, X_test, y_train, y_test = preprocess_data(training=True)

model = LinearRegression()

model.fit(X_train, y_train)

y_pred = model.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print("MAE:", mae)
print("R2 Score:", r2)

joblib.dump(model, MODEL_PATH)

print("Model trained and saved")