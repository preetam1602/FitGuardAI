import pandas as pd
import joblib
import os
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "heart.csv")
SCALER_PATH = os.path.join(BASE_DIR, "models", "scaler.pkl")
    

def create_health_features(df):
    """
    Convert heart dataset → health style features
    """

    np.random.seed(42)

    height = np.random.normal(170, 10, len(df))  # Average height with some variation
    weight = np.random.normal(70, 12, len(df))  # Average weight with some variation

    bmi = weight / ((height / 100) ** 2) 

    sleep = np.random.normal(7, 1, len(df))

    physical = np.where(df["exang"] == 1, 0, 1)
    smoking = df["fbs"]

    gender = df["sex"]
    heart_rate = df["thalach"]

    bp_category = pd.cut(
        df["trestbps"],
        bins=[0, 120, 140, 200],
        labels=[0, 1, 2]
    )

    new_df = pd.DataFrame({
        "age": df["age"],
        "gender": gender,
        "height": height,
        "weight": weight,
        "bmi": bmi,
        "bloodPressure": bp_category.astype(int),
        "heartRate": heart_rate,
        "physicalActivity": physical,
        "sleepHours": sleep,
        "smokingHabit": smoking,
        "target": df["trestbps"]
    })

    return new_df


def preprocess_data(data=None, training=True):

    if training:

        df = pd.read_csv(DATA_PATH)

        df = create_health_features(df)

        X = df.drop("target", axis=1)
        y = df["target"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        scaler = StandardScaler()

        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        joblib.dump(scaler, SCALER_PATH)

        return X_train_scaled, X_test_scaled, y_train, y_test

    else:
        scaler = joblib.load(SCALER_PATH)

        # Convert string values to numeric
        if isinstance(data.get("smokingHabit"), str):
            data["smokingHabit"] = 1 if data["smokingHabit"].lower() == "yes" else 0
        
        if isinstance(data.get("physicalActivity"), str):
            activity_map = {
                "sedentary": 0,
                "light": 1,
                "moderate": 2,
                "active": 3,
                "very-active": 4
            }
            data["physicalActivity"] = activity_map.get(data["physicalActivity"].lower(), 2)
        
        if isinstance(data.get("bloodPressure"), str):
            # Convert "120/80" format to systolic value for categorization
            try:
                systolic = int(data["bloodPressure"].split("/")[0])
                if systolic < 120:
                    data["bloodPressure"] = 0
                elif systolic < 140:
                    data["bloodPressure"] = 1
                else:
                    data["bloodPressure"] = 2
            except:
                data["bloodPressure"] = 1  # Default to elevated

        # Convert gender to numeric
        if isinstance(data.get("gender"), str):
            data["gender"] = 1 if data["gender"].lower() == "male" else 0

        # Ensure columns are in the correct order
        column_order = ["age", "gender", "height", "weight", "bmi", 
                       "bloodPressure", "heartRate", "physicalActivity", 
                       "sleepHours", "smokingHabit"]
        
        # Create DataFrame with data and reorder columns
        df = pd.DataFrame([data])
        df = df[column_order]

        scaled = scaler.transform(df)

        return scaled