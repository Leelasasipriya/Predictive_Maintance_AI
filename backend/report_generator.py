import io
import csv
from datetime import datetime

def generate_csv_report(machine_id, report_type="daily", range_type=None):
    """
    Generates a structured CSV report for machine telemetry and health metrics.
    """
    if range_type is not None:
        report_type = range_type

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["REPORT_TYPE", report_type.upper()])
    writer.writerow(["GENERATED_AT", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow(["MACHINE_ID", machine_id])
    writer.writerow([])
    writer.writerow(["Timestamp", "Temperature (°C)", "Pressure (bar)", "RPM", "Vibration (mm/s)", "Health Score (%)", "Anomaly Score", "RUL (Hours)", "Status"])

    # Sample report entries
    now = datetime.now()
    for i in range(24):
        t_str = (now).strftime("%H:%M:%S")
        writer.writerow([
            t_str,
            round(65.4 + (i % 3) * 0.4, 2),
            round(6.21 + (i % 2) * 0.05, 2),
            round(1498.0 + (i % 4) * 2.0, 1),
            round(2.35 + (i % 3) * 0.1, 2),
            95 if i < 18 else 78,
            0.14 if i < 18 else 0.42,
            round(182.0 - i * 0.5, 1),
            "HEALTHY" if i < 18 else "WARNING"
        ])

    return output.getvalue()

def generate_pdf_report(machine_id, report_type="daily", range_type=None):
    """
    Generates an HTML/PDF formatted report representation.
    """
    if range_type is not None:
        report_type = range_type
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Predictive Maintenance Report - {machine_id}</title>
        <style>
            body {{ font-family: Arial, sans-serif; background: #0f172a; color: #f8fafc; padding: 30px; }}
            h1 {{ color: #38bdf8; border-bottom: 2px solid #334155; padding-bottom: 10px; }}
            .metric-card {{ background: #1e293b; padding: 15px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #334155; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ padding: 10px; border: 1px solid #334155; text-align: left; }}
            th {{ background: #0284c7; color: white; }}
        </style>
    </head>
    <body>
        <h1>Industrial IoT Predictive Maintenance Report</h1>
        <div class="metric-card">
            <p><strong>Report Type:</strong> {report_type.upper()} Performance Audit</p>
            <p><strong>Target Machine:</strong> {machine_id} (CNC Milling Machine - 07)</p>
            <p><strong>Generated Date:</strong> {datetime.now().strftime('%B %d, %Y - %H:%M:%S')}</p>
            <p><strong>Overall Machine Health:</strong> 95% (Excellent)</p>
            <p><strong>Predicted Remaining Useful Life (RUL):</strong> 182 Hours (≈ 7.5 Days)</p>
        </div>
        <h2>Diagnostic Sensor Summary</h2>
        <table>
            <tr><th>Sensor Parameter</th><th>Operational Average</th><th>Threshold Range</th><th>Status</th></tr>
            <tr><td>Temperature (°C)</td><td>65.4 °C</td><td>40 - 80 °C</td><td>Normal</td></tr>
            <tr><td>Pressure (bar)</td><td>6.21 bar</td><td>3 - 10 bar</td><td>Normal</td></tr>
            <tr><td>Motor Speed (RPM)</td><td>1498 RPM</td><td>1000 - 2000 RPM</td><td>Normal</td></tr>
            <tr><td>Vibration (mm/s)</td><td>2.35 mm/s</td><td>0 - 4 mm/s</td><td>Optimal Baseline</td></tr>
        </table>
    </body>
    </html>
    """
    return html_content
