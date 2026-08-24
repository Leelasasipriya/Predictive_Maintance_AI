import os
import pandas as pd
import numpy as np

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "train_FD001.txt")

SENSOR_COLUMNS = [f"sensor_{i}" for i in range(1, 22)]
COLUMN_NAMES = ["unit_id", "time_cycle", "op_setting_1", "op_setting_2", "op_setting_3"] + SENSOR_COLUMNS

def load_cmapss_data(filepath=None):
    """
    Loads and preprocesses the NASA C-MAPSS engine dataset.
    Calculates ground-truth Remaining Useful Life (RUL) per unit cycle.
    """
    if filepath is None:
        filepath = DATA_PATH

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"C-MAPSS dataset not found at {filepath}")

    # Read space-delimited text file
    df = pd.read_csv(filepath, sep=r"\s+", header=None, names=COLUMN_NAMES)

    # Compute maximum cycle reached by each engine unit
    max_cycles = df.groupby("unit_id")["time_cycle"].max().reset_index()
    max_cycles.rename(columns={"time_cycle": "max_cycle"}, inplace=True)

    df = pd.merge(df, max_cycles, on="unit_id")
    df["RUL"] = df["max_cycle"] - df["time_cycle"]

    # Map key physical sensors for industrial IoT dashboard
    # Map raw sensors to realistic physical ranges
    df["temperature"] = round(45.0 + (df["sensor_2"] - 600.0) * 0.8 + np.random.normal(0, 0.2, len(df)), 2)
    df["temperature"] = df["temperature"].clip(35.0, 95.0)

    df["pressure"] = round(6.0 + (df["sensor_4"] - 1400.0) * 0.02 + np.random.normal(0, 0.05, len(df)), 2)
    df["pressure"] = df["pressure"].clip(2.5, 12.0)

    df["rpm"] = round(1450.0 + (df["sensor_7"] - 500.0) * 0.5 + np.random.normal(0, 3.0, len(df)), 1)
    df["rpm"] = df["rpm"].clip(900.0, 2200.0)

    df["vibration"] = round(1.8 + (df["sensor_11"] - 47.0) * 0.6 + np.random.normal(0, 0.1, len(df)), 2)
    df["vibration"] = df["vibration"].clip(0.4, 8.5)

    return df

if __name__ == "__main__":
    data = load_cmapss_data()
    print(f"[OK] C-MAPSS dataset loaded successfully with {len(data)} rows and {data['unit_id'].nunique()} engine units.")
    print("Sample dataset head:")
    print(data[["unit_id", "time_cycle", "temperature", "pressure", "rpm", "vibration", "RUL"]].head())
