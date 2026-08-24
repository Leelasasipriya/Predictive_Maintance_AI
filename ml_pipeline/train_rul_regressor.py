import os
import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from dataset_loader import load_cmapss_data
from feature_engineering import extract_time_series_features

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
os.makedirs(MODEL_DIR, exist_ok=True)

def train_rul_regressor():
    print("[*] Training Supervised RUL Regressor on C-MAPSS dataset...")
    df = load_cmapss_data()

    X_features = extract_time_series_features(df)
    y_rul = df["RUL"].values

    # Fit Gradient Boosting Regressor (XGBoost / GBDT formulation)
    regressor = GradientBoostingRegressor(
        n_estimators=100,
        learning_rate=0.08,
        max_depth=5,
        random_state=42
    )
    regressor.fit(X_features, y_rul)

    # Save trained model & feature list
    rul_path = os.path.join(MODEL_DIR, "rul_regressor.pkl")
    feat_path = os.path.join(MODEL_DIR, "feature_names.pkl")

    joblib.dump(regressor, rul_path)
    joblib.dump(list(X_features.columns), feat_path)

    print(f"[OK] Supervised RUL Regressor trained & saved to '{rul_path}'.")
    return regressor, list(X_features.columns)

if __name__ == "__main__":
    train_rul_regressor()
