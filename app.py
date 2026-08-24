import os
import sys
import uvicorn

# Ensure python path points to backend and ml_pipeline
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))
sys.path.append(os.path.join(os.path.dirname(__file__), "ml_pipeline"))

def prepare_models():
    model_dir = os.path.join(os.path.dirname(__file__), "models")
    anomaly_path = os.path.join(model_dir, "anomaly_detector.pkl")
    rul_path = os.path.join(model_dir, "rul_regressor.pkl")

    if not (os.path.exists(anomaly_path) and os.path.exists(rul_path)):
        print("[*] Pre-trained models missing. Initiating automated ML model training on NASA C-MAPSS dataset...")
        # pyrefly: ignore [missing-import]
        from train_anomaly_detector import train_anomaly_detector
        # pyrefly: ignore [missing-import]
        from train_rul_regressor import train_rul_regressor

        train_anomaly_detector()
        train_rul_regressor()
    else:
        print("[OK] Pre-trained ML Models verified in 'models/'.")

if __name__ == "__main__":
    print("=" * 70)
    print(" INDUSTRIAL IoT PREDICTIVE MAINTENANCE & ANOMALY DETECTION SYSTEM ")
    print("=" * 70)

    prepare_models()

    print("\n[+] Starting FastAPI Async Backend on http://127.0.0.1:8000...")
    print("    [+] Live Telemetry Stream: ws://127.0.0.1:8000/ws/telemetry")
    print("    [+] Interactive Dashboard: http://127.0.0.1:8000/\n")
    print("=" * 70)

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
