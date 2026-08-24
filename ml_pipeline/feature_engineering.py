import numpy as np

def compute_fft_features(vibration_buffer):
    """
    Computes Fast Fourier Transform (FFT) features from high-frequency (50Hz) vibration data.
    Converts time-series signal to frequency domain to detect mechanical bearing wear & resonance.
    """
    buffer = np.array(vibration_buffer, dtype=float)
    if len(buffer) < 4:
        return {
            "fft_peak_freq": 12.5,
            "fft_spectral_energy": 0.05,
            "fft_spectral_entropy": 0.85,
            "rms_vibration": float(np.sqrt(np.mean(buffer**2))) if len(buffer) > 0 else 2.35
        }

    # Remove DC offset
    signal = buffer - np.mean(buffer)

    # Compute Fast Fourier Transform
    fft_vals = np.fft.rfft(signal)
    fft_mag = np.abs(fft_vals)
    freqs = np.fft.rfftfreq(len(buffer), d=1.0/50.0) # 50Hz sampling rate

    # Peak Frequency
    peak_idx = np.argmax(fft_mag)
    peak_freq = freqs[peak_idx] if peak_idx < len(freqs) else 15.0

    # Spectral Energy
    total_energy = np.sum(fft_mag ** 2) / (len(buffer) ** 2 + 1e-8)

    # Spectral Entropy
    prob = fft_mag / (np.sum(fft_mag) + 1e-8)
    entropy = -np.sum(prob * np.log2(prob + 1e-8))

    # RMS Vibration
    rms_vib = np.sqrt(np.mean(buffer ** 2))

    return {
        "fft_peak_freq": round(float(peak_freq), 2),
        "fft_spectral_energy": round(float(total_energy), 4),
        "fft_spectral_entropy": round(float(entropy), 3),
        "rms_vibration": round(float(rms_vib), 3)
    }

def extract_time_series_features(df, window_size=5):
    """
    Computes rolling mean and std features across sensor channels.
    """
    features = df[["temperature", "pressure", "rpm", "vibration"]].copy()

    # Rolling Means
    features["temp_rolling_mean"] = features["temperature"].rolling(window=window_size, min_periods=1).mean()
    features["press_rolling_mean"] = features["pressure"].rolling(window=window_size, min_periods=1).mean()
    features["rpm_rolling_mean"] = features["rpm"].rolling(window=window_size, min_periods=1).mean()
    features["vib_rolling_mean"] = features["vibration"].rolling(window=window_size, min_periods=1).mean()

    # Rolling Std Deviations
    features["temp_rolling_std"] = features["temperature"].rolling(window=window_size, min_periods=1).std().fillna(0.2)
    features["press_rolling_std"] = features["pressure"].rolling(window=window_size, min_periods=1).std().fillna(0.05)
    features["rpm_rolling_std"] = features["rpm"].rolling(window=window_size, min_periods=1).std().fillna(2.0)
    features["vib_rolling_std"] = features["vibration"].rolling(window=window_size, min_periods=1).std().fillna(0.1)

    return features

if __name__ == "__main__":
    test_vib = [2.1, 2.3, 2.5, 2.4, 2.8, 3.5, 4.2, 5.1, 6.0, 5.8]
    fft_res = compute_fft_features(test_vib)
    print("[OK] FFT Signal Feature Extraction test result:")
    print(fft_res)
