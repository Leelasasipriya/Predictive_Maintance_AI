import os
import sys
import asyncio
import json
import re
import urllib.parse
import urllib.request
import base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "ml_pipeline"))

# pyrefly: ignore [missing-import]
from inference_engine import RealTimeInferenceEngine
# pyrefly: ignore [missing-import]
from stream_simulator import SensorStreamSimulator
# pyrefly: ignore [missing-import]
from report_generator import generate_csv_report, generate_pdf_report

app = FastAPI(title="Predictive Maintenance AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

inference_engine = RealTimeInferenceEngine()
stream_simulator = SensorStreamSimulator()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()
rolling_history = []

# Data Models
class NewMachineRequest(BaseModel):
    machine_id: str
    machine_name: str
    condition: str  # "New Machine" or "Old Machine"
    type: str = "CNC Mill"

class EditMachineRequest(BaseModel):
    old_id: str
    machine_id: str
    machine_name: str
    condition: str
    type: str

class SettingsRequest(BaseModel):
    admin_name: str
    admin_number: str
    admin_email: str
    company_name: str
    block_name: str
    theme: str = "light"
    role: str = "Admin"

# Global Admin Settings State with File Persistence
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "settings.json")

def load_admin_settings():
    defaults = {
        "admin_name": "Admin User",
        "admin_number": "+1 (555) 019-2834",
        "admin_email": "admin@factory.ai",
        "company_name": "Siemens Industrial Park",
        "block_name": "Block B-07",
        "theme": "light",
        "role": "Admin"
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                defaults.update(saved)
        except Exception:
            pass
    return defaults

def save_admin_settings():
    try:
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(admin_settings, f, indent=2)
    except Exception as e:
        print(f"[!] Error saving settings to {SETTINGS_FILE}: {e}")

admin_settings = load_admin_settings()

class MaintenanceRequest(BaseModel):
    machine_id: str
    action: str
    technician: str = "Admin Technician"
    time: str = ""

MAINTENANCE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "maintenance_history.json")

def load_maintenance_history():
    if os.path.exists(MAINTENANCE_FILE):
        try:
            with open(MAINTENANCE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return [
        {
            "id": "maint-101",
            "machine_id": "MCH-045",
            "action": "Routine bearing race alignment & sensor lubrication",
            "technician": "Admin Technician",
            "time": "2026-08-24 10:30:00",
            "status": "Completed"
        }
    ]

def save_maintenance_history(history_list):
    try:
        os.makedirs(os.path.dirname(MAINTENANCE_FILE), exist_ok=True)
        with open(MAINTENANCE_FILE, "w", encoding="utf-8") as f:
            json.dump(history_list, f, indent=2)
    except Exception as e:
        print(f"[!] Error saving maintenance history to {MAINTENANCE_FILE}: {e}")

maintenance_history = load_maintenance_history()

@app.get("/")
async def get_dashboard():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"})
    return HTMLResponse("<h2>Predictive Maintenance AI backend running.</h2>")

@app.get("/style.css")
async def get_css():
    return FileResponse(os.path.join(FRONTEND_DIR, "style.css"), headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"})

@app.get("/app.js")
async def get_js():
    return FileResponse(os.path.join(FRONTEND_DIR, "app.js"), headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"})



# Machines API
@app.get("/api/machines")
async def get_machines():
    return {
        "active_machine": stream_simulator.selected_machine,
        "machines": stream_simulator.machines
    }

@app.post("/api/machines/add")
async def add_machine(req: NewMachineRequest):
    for m in stream_simulator.machines:
        if m["id"].lower() == req.machine_id.lower():
            raise HTTPException(status_code=400, detail="Machine ID already exists")

    new_m = {
        "id": req.machine_id.upper(),
        "name": req.machine_name,
        "condition": req.condition,
        "type": req.type or "CNC Mill"
    }
    stream_simulator.machines.append(new_m)
    if stream_simulator.selected_machine.get("id") == "N/A" or len(stream_simulator.machines) == 1:
        stream_simulator.selected_machine = new_m
    stream_simulator.save_machines()
    return {"status": "success", "machine": new_m, "machines": stream_simulator.machines}

@app.post("/api/machines/edit")
async def edit_machine(req: EditMachineRequest):
    target = None
    for m in stream_simulator.machines:
        if m["id"].lower() == req.old_id.lower():
            target = m
            break

    if not target:
        raise HTTPException(status_code=404, detail="Machine not found")

    target["id"] = req.machine_id.upper()
    target["name"] = req.machine_name
    target["condition"] = req.condition
    target["type"] = req.type

    if stream_simulator.selected_machine["id"].lower() == req.old_id.lower():
        stream_simulator.selected_machine = target

    stream_simulator.save_machines()
    return {"status": "success", "machine": target, "machines": stream_simulator.machines}

@app.delete("/api/machines/{machine_id}")
async def delete_machine(machine_id: str):
    found = None
    for m in stream_simulator.machines:
        if m["id"].lower() == machine_id.lower():
            found = m
            break

    if not found:
        raise HTTPException(status_code=404, detail="Machine ID not found")

    stream_simulator.machines.remove(found)
    if stream_simulator.selected_machine["id"].lower() == machine_id.lower():
        if len(stream_simulator.machines) > 0:
            stream_simulator.selected_machine = stream_simulator.machines[0]
        else:
            stream_simulator.selected_machine = {"id": "N/A", "name": "No Machine Available", "condition": "N/A", "type": "N/A"}

    stream_simulator.save_machines()
    return {"status": "success", "deleted_id": machine_id, "machines": stream_simulator.machines}

@app.post("/api/select-machine")
async def select_machine(req: dict):
    m_id = req.get("machine_id")
    selected = stream_simulator.select_machine(m_id)
    return {"status": "success", "selected_machine": selected}
# Admin Settings API
@app.get("/api/settings")
async def get_settings():
    global admin_settings
    admin_settings = load_admin_settings()
    return admin_settings

@app.post("/api/settings")
async def update_settings(req: SettingsRequest):
    admin_settings.update(req.dict())
    save_admin_settings()
    return {"status": "success", "settings": admin_settings}

# Maintenance History API
@app.get("/api/maintenance-history")
async def get_maintenance_history():
    return {"status": "success", "history": maintenance_history}

@app.post("/api/maintenance-history")
async def add_maintenance_history(req: MaintenanceRequest):
    import time
    record = {
        "id": f"maint-{int(time.time() * 1000)}",
        "machine_id": req.machine_id.upper(),
        "action": req.action,
        "technician": req.technician or "Admin Technician",
        "time": req.time or time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Completed"
    }
    maintenance_history.insert(0, record)
    save_maintenance_history(maintenance_history)
    return {"status": "success", "record": record, "history": maintenance_history}

@app.delete("/api/maintenance-history/{record_id}")
async def delete_maintenance_history(record_id: str):
    global maintenance_history
    maintenance_history = [m for m in maintenance_history if m.get("id") != record_id]
    save_maintenance_history(maintenance_history)
    return {"status": "success", "deleted_id": record_id, "history": maintenance_history}

# Export Report Endpoint
@app.get("/api/export-report")
async def export_report(machine_id: str = "MCH-07", format: str = "csv", report_type: str = "daily"):
    if format.lower() == "pdf":
        html = generate_pdf_report(machine_id, report_type)
        return Response(content=html, media_type="text/html", headers={"Content-Disposition": f"attachment; filename=maintenance_report_{machine_id}.html"})
    else:
        csv_data = generate_csv_report(machine_id, report_type)
        return Response(content=csv_data, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=maintenance_report_{machine_id}.csv"})

# WebSocket Telemetry
@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            raw_sample = stream_simulator.get_next_tick()
            processed_payload = inference_engine.process_telemetry(raw_sample, rolling_history)

            # Pass exact Machine Type to payload
            processed_payload["machine_type"] = raw_sample.get("machine_type", "CNC Mill")

            rolling_history.append(processed_payload)
            if len(rolling_history) > 30:
                rolling_history.pop(0)

            await websocket.send_json(processed_payload)
            await asyncio.sleep(0.25)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
