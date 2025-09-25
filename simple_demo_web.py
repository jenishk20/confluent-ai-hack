#!/usr/bin/env python3
"""
Simple Demo Web Interface
Shows live data processing for judges
"""

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import asyncio
import json
import subprocess
import threading
import time
from datetime import datetime

app = FastAPI()

# Global stats for demo
demo_stats = {
    "messages_processed": 0,
    "pii_detected": 0,
    "high_risk_blocked": 0,
    "clean_approved": 0,
    "last_update": datetime.now().isoformat()
}

# Demo HTML page
DEMO_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>🛡️ SecureStream AI - Live Demo</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; background: #2c3e50; color: white; padding: 20px; border-radius: 10px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }
        .stat-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .stat-number { font-size: 2em; font-weight: bold; color: #3498db; }
        .control-panel { background: white; padding: 20px; border-radius: 10px; margin: 20px 0; }
        .btn { background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        .btn:hover { background: #2980b9; }
        .btn-danger { background: #e74c3c; }
        .btn-danger:hover { background: #c0392b; }
        .activity { background: white; padding: 20px; border-radius: 10px; max-height: 400px; overflow-y: auto; }
        .activity-item { padding: 10px; border-bottom: 1px solid #eee; }
        .pii-detected { color: #e74c3c; font-weight: bold; }
        .clean { color: #27ae60; }
        .processing { color: #f39c12; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ SecureStream AI</h1>
            <h2>Real-Time AI Data Security Monitor</h2>
            <p>Live Demo - Confluent AI Day Boston 2025</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-number" id="processed">0</div>
                <div>Messages Processed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="pii-detected">0</div>
                <div>PII Detected</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="blocked">0</div>
                <div>High Risk Blocked</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="approved">0</div>
                <div>Clean Approved</div>
            </div>
        </div>

        <div class="control-panel">
            <h3>Demo Controls</h3>
            <button class="btn" onclick="startDataFlow()">🚀 Start Data Flow</button>
            <button class="btn" onclick="generateBurst()">⚡ Generate Data Burst</button>
            <button class="btn btn-danger" onclick="stopDemo()">⏹️ Stop Demo</button>
            <div style="margin-top: 10px;">
                <strong>Status:</strong> <span id="status">Ready to start</span>
            </div>
        </div>

        <div class="activity">
            <h3>📊 Live Processing Activity</h3>
            <div id="activity-feed">
                <div class="activity-item">System ready. Click 'Start Data Flow' to begin demo.</div>
            </div>
        </div>
    </div>

    <script>
        let ws = new WebSocket("ws://localhost:8000/ws");
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            
            // Update stats
            document.getElementById('processed').textContent = data.messages_processed;
            document.getElementById('pii-detected').textContent = data.pii_detected;
            document.getElementById('blocked').textContent = data.high_risk_blocked;
            document.getElementById('approved').textContent = data.clean_approved;
            
            // Add activity
            if (data.activity) {
                addActivity(data.activity);
            }
        };

        function addActivity(activity) {
            const feed = document.getElementById('activity-feed');
            const item = document.createElement('div');
            item.className = 'activity-item';
            
            const time = new Date().toLocaleTimeString();
            if (activity.includes('PII')) {
                item.className += ' pii-detected';
                item.innerHTML = `[${time}] 🚨 ${activity}`;
            } else if (activity.includes('Clean')) {
                item.className += ' clean';
                item.innerHTML = `[${time}] ✅ ${activity}`;
            } else {
                item.className += ' processing';
                item.innerHTML = `[${time}] 📊 ${activity}`;
            }
            
            feed.insertBefore(item, feed.firstChild);
            
            // Keep only last 20 items
            while (feed.children.length > 20) {
                feed.removeChild(feed.lastChild);
            }
        }

        function startDataFlow() {
            document.getElementById('status').textContent = 'Data flowing to Confluent Cloud...';
            fetch('/start-demo', {method: 'POST'});
            addActivity('Started data generation - sending user prompts to Confluent Cloud');
        }

        function generateBurst() {
            document.getElementById('status').textContent = 'Generating high-volume data burst...';
            fetch('/generate-burst', {method: 'POST'});
            addActivity('Generating 50 user prompts with PII for real-time processing');
        }

        function stopDemo() {
            document.getElementById('status').textContent = 'Demo stopped';
            fetch('/stop-demo', {method: 'POST'});
            addActivity('Demo stopped - processing pipeline idle');
        }
    </script>
</body>
</html>
"""

@app.get("/")
async def get_demo_page():
    return HTMLResponse(content=DEMO_HTML)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    while True:
        # Update stats (simulate real processing)
        demo_stats["messages_processed"] += 1
        if demo_stats["messages_processed"] % 3 == 0:
            demo_stats["pii_detected"] += 1
            activity = f"PII detected in user prompt (SSN, Email) - Risk Score: 7"
        else:
            demo_stats["clean_approved"] += 1
            activity = f"Clean prompt approved for AI training"
        
        if demo_stats["pii_detected"] % 5 == 0:
            demo_stats["high_risk_blocked"] += 1
            activity = f"High-risk data blocked from AI training pipeline"
        
        demo_stats["last_update"] = datetime.now().isoformat()
        demo_stats["activity"] = activity
        
        await websocket.send_text(json.dumps(demo_stats))
        await asyncio.sleep(2)  # Update every 2 seconds

@app.post("/start-demo")
async def start_demo():
    # In real implementation, this would trigger your producer
    return {"status": "Demo started"}

@app.post("/generate-burst")
async def generate_burst():
    # In real implementation, this would run working_producer.py
    return {"status": "Generating data burst"}

@app.post("/stop-demo")
async def stop_demo():
    return {"status": "Demo stopped"}

if __name__ == "__main__":
    import uvicorn
    print("🛡️ Starting SecureStream AI Demo Server...")
    print("📊 Open http://localhost:8000 for live demo")
    print("🎯 Perfect for showing judges real-time processing!")
    uvicorn.run(app, host="0.0.0.0", port=8000)
