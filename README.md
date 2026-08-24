# Real-Time Predictive Maintenance & Anomaly Detection for Industrial IoT

An enterprise-grade, real-world Industry 4.0 Predictive Maintenance System that processes high-frequency (50Hz) multi-sensor telemetry streams (Vibration, Temperature, Pressure, RPM), executes FFT frequency signal processing, runs dual ML models for unsupervised anomaly detection and supervised Remaining Useful Life (RUL) estimation in sub-50ms latency, and visualizes live health metrics on an interactive monitoring dashboard.

---

## 🌟 Key System Features

- **Multi-Sensor 50Hz Telemetry Streaming**: Real-time continuous monitoring of motor speed (RPM), fluid pressure (bar), thermal conditions (°C), and mechanical vibration (mm/s).
- **Fast Fourier Transform (FFT) Signal Processing**: Converts time-domain vibration streams into frequency-domain metrics (*Peak Frequency, Spectral Energy, Spectral Entropy, RMS Vibration*) to catch early bearing wear and resonance.
- **Dual Machine Learning Architecture**:
  - **Unsupervised Anomaly Detector (`IsolationForest`)**: Trained on normal operational baselines to detect baseline deviations without needing historical failure labels.
  - **Supervised RUL Regressor (`GradientBoostingRegressor` / XGBoost)**: Trained on NASA C-MAPSS run-to-failure cycles to predict remaining operational lifespan (Hours/Days).
- **Low-Latency Async Backend**: Built with **FastAPI** & **WebSockets** for persistent bi-directional telemetry streaming with **<50ms inference latency**.
- **Interactive Control Dashboard**:
  - **Dashboard Tab**: Machine Health Score %, Live Anomaly Score, RUL, Failure Risk %, and Maintenance History.
  - **Industrial Machine Inventory**: Add/Edit/Delete assets with custom condition (*New/Old Machine*) and machine type.
  - **Alerts Center**: 2-column layout (Current Active Alerts & Alerts History) synchronized with machine inventory.
  - **Sensor Analytics**: 5 parameter cards with normal expected ranges and a single line chart with 10-unit Y-axis grid.
  - **Reports Center**: Automated Daily, Weekly, Monthly PDF/CSV report exports & email sharing modal.
  - **Maintenance Center**: Machine condition overview, editable SMS message textarea, and Fast2SMS mobile dispatch.
  - **General Settings**: Admin profile, password eye toggle, Light/Dark theme switcher, and session authentication lock.

---

## 🏗️ System Architecture

```
[ Multi-Sensor IoT Telemetry ]  <-- (Vibration, Temp, Pressure, RPM at 50Hz)
              │
              ▼
[ Async WebSocket Gateway ]     <-- (FastAPI Stream Broker)
              │
              ▼
[ Feature Engineering Pipeline ] <-- (Sliding Window, FFT Frequencies, Rolling Metrics)
              │
    ┌─────────┴─────────┐
    ▼                   ▼
[ Unsupervised Model ] [ Supervised Model ]
(Anomaly Detector)     (RUL Regressor)
    │                   │
    └─────────┬─────────┘
              ▼
[ Dual-Model Inference Engine ] <-- (Sub-50ms Low Latency Execution)
              │
              ▼
[ Interactive Monitoring Dashboard ] (HTML5 / CSS3 / Vanilla JS / Chart.js)
```

---

## 🛠️ Tech Stack

| Domain | Technologies Used |
| :--- | :--- |
| **Languages** | Python 3.11+, JavaScript (ES6+), HTML5, CSS3 |
| **Machine Learning** | Scikit-Learn (IsolationForest, GradientBoosting), Joblib, NumPy, Pandas |
| **Signal Processing** | Fast Fourier Transform (`np.fft`), Sliding Window Rolling Aggregations |
| **Backend Framework** | FastAPI, WebSockets (`asyncio`), Uvicorn, Pydantic |
| **Frontend** | Vanilla JS (ES6+ SPA), Chart.js (v4.4), Custom CSS Grid/Flexbox |
| **Integrations** | Fast2SMS REST API, Dynamic PDF/CSV Exporter |
| **Dataset** | NASA C-MAPSS Turbofan Engine Degradation Dataset (`train_FD001.txt`) |

---

## 📁 Repository Folder Structure

```
Predictive_Maintance_AI/
├── .gitignore               # Ignored files (pycache, venvs, IDE configs)
├── requirements.txt         # Python package dependencies
├── README.md                # System documentation
├── app.py                   # System Launcher Script
├── backend/
│   ├── inference_engine.py  # Dual ML Model (<50ms) Engine
│   ├── main.py              # FastAPI REST & WebSocket Backend
│   └── report_generator.py  # PDF/CSV Report Exporter
├── ml_pipeline/
│   ├── dataset_loader.py    # NASA C-MAPSS Data Loader
│   ├── feature_engineering.py # 50Hz FFT & Sliding Window Signal Processing
│   ├── stream_simulator.py  # Live Sensor Telemetry & Fault Simulator
│   ├── train_anomaly_detector.py # Unsupervised Model Trainer
│   └── train_rul_regressor.py   # Supervised XGBoost RUL Trainer
├── models/
│   ├── anomaly_detector.pkl # Saved Unsupervised Anomaly Model
│   ├── feature_names.pkl    # Model Feature Vector List
│   ├── rul_regressor.pkl    # Saved Supervised RUL Model
│   └── scaler.pkl           # StandardScaler Object
├── data/
│   └── train_FD001.txt      # NASA C-MAPSS Engine Dataset
└── frontend/
    ├── app.js               # Single Page App JS & WebSocket Engine
    ├── index.html           # Predictive Maintenance AI Dashboard UI
    └── style.css            # Dark Mode Industrial CSS Design System
```

---

## 🚀 Getting Started

### 1. Prerequisites
Ensure you have **Python 3.11+** installed on your system.

### 2. Installation
Clone the repository and install the dependencies:
```bash
git clone https://github.com/your-username/Predictive_Maintance_AI.git
cd Predictive_Maintance_AI
pip install -r requirements.txt
```

### 3. Launching the Application
Run the launcher script:
```bash
python app.py
```

Open your browser and navigate to:
- **Interactive Web Dashboard**: `http://127.0.0.1:8000/`
- **Live Telemetry Stream**: `ws://127.0.0.1:8000/ws/telemetry`

---

## 📊 Dataset Reference

This project utilizes the **NASA C-MAPSS (Commercial Aircraft Engine Supplier) Dataset** (`train_FD001.txt`), simulating turbofan engine degradation under different operational conditions until run-to-failure. Ground-truth Remaining Useful Life (RUL) is calculated per engine cycle to train supervised regression models.

---

## 🔒 License & Author

Developed for **Real-Time Predictive Maintenance & Industrial IoT Anomaly Detection**.  
© 2026 Predictive Maintenance AI. All Rights Reserved.
