from flask import Flask, render_template_string
import json
import os

app = Flask(__name__)

# Mock data for the dashboard demo
# In production, this would read from C:\Users\kyle\miso_data\audit_logs.json
LOGS = [
    {"timestamp": "2026-02-26 19:45:01", "user": "kyle", "stem": "PASS", "legal": "PASS", "corp": "PASS", "verdict": "200 OK"},
    {"timestamp": "2026-02-26 19:48:22", "user": "guest", "stem": "PASS", "legal": "FAIL", "corp": "PENDING", "verdict": "403 REJECTED"},
    {"timestamp": "2026-02-26 19:55:10", "user": "kyle", "stem": "FAIL", "legal": "N/A", "corp": "N/A", "verdict": "403 REJECTED (Entropy)"}
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>MISO Sovereign Dashboard</title>
    <style>
        body { background: #0e1117; color: #ffffff; font-family: 'Segoe UI', sans-serif; padding: 20px; }
        .audit-card { background: #1a1c23; border-left: 5px solid #4caf50; padding: 15px; margin-bottom: 10px; border-radius: 4px; }
        .fail { border-left-color: #f44336; }
        .status { font-weight: bold; margin-right: 15px; }
        .header { border-bottom: 1px solid #333; margin-bottom: 20px; padding-bottom: 10px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ MISO Sovereign Dashboard</h1>
        <p>Master Node: 127.0.0.1 | Mirror: 10.200.20.158</p>
    </div>
    {% for log in logs %}
    <div class="audit-card {{ 'fail' if '403' in log.verdict else '' }}">
        <strong>{{ log.timestamp }}</strong> | User: {{ log.user }} <br>
        <span class="status">STEM: {{ log.stem }}</span>
        <span class="status">LEGAL: {{ log.legal }}</span>
        <span class="status">CORP: {{ log.corp }}</span>
        <h3 style="margin: 10px 0 0 0;">{{ log.verdict }}</h3>
    </div>
    {% endfor %}
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(HTML_TEMPLATE, logs=LOGS)

if __name__ == '__main__':
    print("[🌐] DASHBOARD LIVE AT http://127.0.0.1:5000")
    app.run(port=5000)
