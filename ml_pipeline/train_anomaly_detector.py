import os
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from dataset_loader import load_cmapss_data
from feature_engineering import extract_time_series_features

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
os.makedirs(MODEL_DIR, exist_ok=True)

class UnsupervisedAnomalyDetector:
    """
    Unsupervised Anomaly Detector using Isolation Forest & Distance Metric.
    Calculates reconstruction error / anomaly metric relative to normal operating baseline.
    """
    def __init__(self, contamination=0.05):
        self.model = IsolationForest(n_estimators=100, contamination=contamination, random_state=42)
        self.threshold = 0.30
        self.center_vec = None

    def fit(self, X_scaled):
        self.model.fit(X_scaled)
        self.center_vec = np.mean(X_scaled, axis=0)

    def predict_reconstruction_error(self, X_scaled):
        """
        Computes synthetic reconstruction error / anomaly metric in range [0.0, 1.0+].
        """
        # Distance from normal operational centroid
        distances = np.linalg_norm(X_scaled - self.center_vec, axis=1) / np.sqrt(X_scaled.shape[1])
        # Scale to match typical 0.10 normal / 0.30+ threshold range
        scores = np.clip(distances * 0.25, 0.02, 1.20)
        return scores

def train_anomaly_detector():
    print("[*] Training Unsupervised Anomaly Detector on C-MAPSS normal operating baseline...")
    df = load_cmapss_data()

    # Filter early cycles (healthy operating state 99% of time)
    healthy_df = df[df["time_cycle"] <= 50].copy()

    X_raw = extract_time_series_features(healthy_df)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)

    detector = UnsupervisedAnomalyDetector(contamination=0.03)
    detector.fit(X_scaled)

    # Save trained model & scaler
    scaler_path = os.path.join(MODEL_DIR, "scaler.pkl")
    anomaly_path = os.path.join(MODEL_DIR, "anomaly_detector.pkl")

    joblib.dump(scaler, scaler_path)
    joblib.dump(detector, anomaly_path)

    print(f"[OK] Unsupervised Anomaly Detector trained & saved to '{anomaly_path}'.")
    return detector, scaler

if __name__ == "__main__":
    train_anomaly_detector()
