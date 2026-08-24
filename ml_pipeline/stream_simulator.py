import os
import json
import time
import random
import numpy as np
from dataset_loader import load_cmapss_data

class SensorStreamSimulator:
    def __init__(self):
        try:
            self.cmapss_df = load_cmapss_data()
            self.total_rows = len(self.cmapss_df)
        except Exception as e:
            self.cmapss_df = None

        self.current_index = 0
        self.active_fault = "NONE"
        self.fault_active = False

        self.data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.machines_file = os.path.join(self.data_dir, "machines.json")

        if os.path.exists(self.machines_file):
            try:
                with open(self.machines_file, "r", encoding="utf-8") as f:
                    self.machines = json.load(f)
            except Exception:
                self.machines = self._get_default_machines()
        else:
            self.machines = self._get_default_machines()
            self.save_machines()

        if self.machines:
            self.selected_machine = self.machines[-1]
        else:
            self.selected_machine = {"id": "N/A", "name": "No Machine Available", "condition": "N/A", "type": "N/A"}

    def _get_default_machines(self):
        return []

    def save_machines(self):
        try:
            with open(self.machines_file, "w", encoding="utf-8") as f:
                json.dump(self.machines, f, indent=2)
        except Exception as e:
            print(f"[!] Error saving machines to {self.machines_file}: {e}")

    def set_fault(self, fault_type):
        if fault_type and fault_type.upper() != "NONE":
            self.active_fault = fault_type.upper()
            self.fault_active = True
        else:
            self.active_fault = "NONE"
            self.fault_active = False

    def select_machine(self, machine_id):
        for m in self.machines:
            if m["id"].lower() == str(machine_id).lower():
                self.selected_machine = m
                return m
        return self.selected_machine

    def _compute_machine_signature(self, machine):
        m_id = str(machine.get("id", ""))
        m_type = str(machine.get("type", "")).lower()
        m_cond = str(machine.get("condition", "Old Machine"))
        is_new = m_cond == "New Machine"

        # Unique hash seed per machine ID
        seed = sum(ord(c) for c in m_id) % 100

        # Base parameters per Machine Type
        if "pump" in m_type or "hydraulic" in m_type:
            base_temp = 50.0 + (seed % 8)
            base_press = 12.5 + (seed % 5) * 0.8
            base_rpm = 1200.0 + (seed % 10) * 20.0
            base_vib = 1.1 if is_new else 2.4
        elif "lathe" in m_type or "motor" in m_type:
            base_temp = 58.0 + (seed % 10)
            base_press = 4.2 + (seed % 4) * 0.5
            base_rpm = 1850.0 + (seed % 15) * 25.0
            base_vib = 0.9 if is_new else 2.2
        elif "turbine" in m_type or "engine" in m_type:
            base_temp = 75.0 + (seed % 12)
            base_press = 18.0 + (seed % 6) * 1.0
            base_rpm = 3200.0 + (seed % 20) * 30.0
            base_vib = 1.0 if is_new else 2.1
        elif "milling" in m_type or "cnc" in m_type:
            base_temp = 52.0 + (seed % 8)
            base_press = 6.2 + (seed % 4) * 0.4
            base_rpm = 1480.0 + (seed % 10) * 15.0
            base_vib = 1.0 if is_new else 2.3
        else:
            base_temp = 55.0 + (seed % 10)
            base_press = 7.0 + (seed % 5) * 0.5
            base_rpm = 1500.0 + (seed % 12) * 20.0
            base_vib = 1.1 if is_new else 2.4

        if is_new:
            base_temp = max(42.0, base_temp - 8.0)

        return round(base_temp, 1), round(base_press, 2), round(base_rpm, 1), round(base_vib, 2)

    def get_next_tick(self):
        t_str = time.strftime("%H:%M:%S")

        if not self.machines:
            return {
                "machine_id": "N/A",
                "machine_name": "No Machine Available",
                "machine_type": "N/A",
                "timestamp": "--:--:--",
                "temperature": 0.0,
                "pressure": 0.0,
                "rpm": 0.0,
                "vibration": 0.0,
                "vibration_buffer": [0.0] * 10,
                "fault_active": False,
                "fault_type": "NONE",
                "no_machine": True
            }

        temp_base, press_base, rpm_base, vib_base = self._compute_machine_signature(self.selected_machine)
        is_new = self.selected_machine.get("condition") == "New Machine"

        if self.cmapss_df is not None and not self.fault_active:
            row = self.cmapss_df.iloc[self.current_index]
            self.current_index = (self.current_index + 1) % self.total_rows

            temp = round(float(row["temperature"]) - 65.4 + temp_base, 1)
            pressure = round(float(row["pressure"]) - 6.21 + press_base, 2)
            rpm = round(float(row["rpm"]) - 1498.0 + rpm_base, 1)
            vibration = round(float(row["vibration"]) - 2.35 + vib_base, 2)
            if is_new:
                vibration = max(0.6, round(vibration * 0.5, 2))
                temp = max(40.0, round(temp * 0.85, 1))
        else:
            temp = round(temp_base + random.uniform(-0.5, 0.5), 1)
            pressure = round(press_base + random.uniform(-0.05, 0.05), 2)
            rpm = round(rpm_base + random.uniform(-5.0, 5.0), 1)
            vibration = round(vib_base + random.uniform(-0.1, 0.1), 2)

        if self.fault_active:
            if self.active_fault == "BEARING_WEAR":
                vibration = round(vibration + random.uniform(2.5, 4.0), 2)
                temp = round(temp + random.uniform(4.0, 8.0), 1)
            elif self.active_fault == "OVERHEATING":
                temp = round(temp + random.uniform(15.0, 25.0), 1)
            elif self.active_fault == "PRESSURE_DROP":
                pressure = round(max(1.0, pressure - random.uniform(3.0, 4.0)), 2)

        vib_buffer = [round(vibration + random.uniform(-0.05, 0.05), 2) for _ in range(50)]

        return {
            "machine_id": self.selected_machine["id"],
            "machine_name": self.selected_machine["name"],
            "machine_condition": self.selected_machine.get("condition", "Old Machine"),
            "machine_type": self.selected_machine.get("type", "CNC Mill"),
            "timestamp": t_str,
            "temperature": temp,
            "pressure": pressure,
            "rpm": rpm,
            "vibration": vibration,
            "vibration_buffer": vib_buffer,
            "fault_active": self.fault_active,
            "fault_type": self.active_fault
        }
