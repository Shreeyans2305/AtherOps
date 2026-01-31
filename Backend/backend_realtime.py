# backend_realtime.py - Real-time signal processing with LangGraph
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
from datetime import datetime
import asyncio
import json
from collections import defaultdict, deque

# LangGraph imports
from langgraph.graph import StateGraph, END
from typing import TypedDict
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (replace with Redis in production)
class SignalStore:
    def __init__(self):
        self.signals = deque(maxlen=1000)  # Keep last 1000 signals
        self.patterns = defaultdict(list)  # Group by error type
        self.connected_dashboards = []  # WebSocket connections to dashboards
    
    def add_signal(self, signal):
        self.signals.append(signal)
        # Group similar errors
        key = f"{signal.get('type')}:{signal.get('message', '')[:50]}"
        self.patterns[key].append(signal)
        return signal
    
    def get_recent(self, limit=50):
        return list(self.signals)[-limit:]
    
    def get_pattern_count(self, pattern_key):
        return len(self.patterns.get(pattern_key, []))

store = SignalStore()

# LangGraph Agent (same as before but async-friendly)
llm = ChatOllama(model="llama3.2:3b", temperature=0.3)

class AgentState(TypedDict):
    pattern_key: str
    signals: List[Dict]
    analysis: str
    decision: str
    confidence: int

def analyze_pattern(pattern_key: str, signals: List[Dict]) -> Dict:
    """Analyzes a pattern using Llama"""
    if len(signals) < 2:
        return None
    
    merchant_ids = [s['merchant_id'] for s in signals]
    error_msg = signals[0].get('message', 'Unknown error')
    
    prompt = f"""Analyze this error pattern from a headless e-commerce platform:

ERROR: {error_msg}
AFFECTED MERCHANTS: {len(signals)} ({', '.join(set(merchant_ids))})
TIME WINDOW: Last 5 minutes

Provide:
ROOT_CAUSE: (merchant config / platform bug / external service / migration issue)
CONFIDENCE: (0-100)%
ACTION: (specific recommendation)
RISK: (low/medium/high)
REASONING: (brief explanation)

Be concise."""
    
    messages = [
        SystemMessage(content="You are analyzing e-commerce platform issues."),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    
    # Parse confidence from response
    confidence = 75  # Default
    if "CONFIDENCE:" in response.content:
        try:
            conf_line = [l for l in response.content.split('\n') if 'CONFIDENCE:' in l][0]
            confidence = int(''.join(filter(str.isdigit, conf_line)))
        except:
            pass
    
    # Determine decision
    if "RISK: low" in response.content.lower():
        decision = "auto_execute"
    elif "RISK: medium" in response.content.lower():
        decision = "needs_approval"
    else:
        decision = "escalate"
    
    return {
        "pattern_key": pattern_key,
        "affected_count": len(signals),
        "merchants": list(set(merchant_ids)),
        "analysis": response.content,
        "decision": decision,
        "confidence": confidence,
        "timestamp": datetime.now().isoformat()
    }

# Background task: Monitor for patterns
async def pattern_monitor():
    """Continuously monitors for patterns and triggers agent"""
    while True:
        await asyncio.sleep(10)  # Check every 10 seconds
        
        # Check each pattern
        for pattern_key, signals in store.patterns.items():
            # If we have 3+ occurrences in recent signals
            recent_signals = [s for s in signals if s in store.signals]
            
            if len(recent_signals) >= 3:
                print(f"\n🔍 PATTERN DETECTED: {pattern_key} ({len(recent_signals)} occurrences)")
                
                # Run analysis
                result = analyze_pattern(pattern_key, recent_signals)
                
                if result:
                    # Broadcast to all connected dashboards
                    await broadcast_alert(result)
                    
                    # Clear this pattern so we don't re-analyze immediately
                    store.patterns[pattern_key] = []

async def broadcast_alert(alert_data):
    """Send alert to all connected dashboard clients"""
    message = json.dumps({
        "type": "pattern_alert",
        "data": alert_data
    })
    
    disconnected = []
    for ws in store.connected_dashboards:
        try:
            await ws.send_text(message)
        except:
            disconnected.append(ws)
    
    # Remove disconnected clients
    for ws in disconnected:
        store.connected_dashboards.remove(ws)

# WebSocket endpoint for SDK (merchants send signals here)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("✅ SDK connected")
    
    try:
        while True:
            data = await websocket.receive_text()
            signal = json.loads(data)
            
            # Store signal
            store.add_signal(signal)
            
            print(f"📡 Signal: [{signal.get('merchant_id')}] {signal.get('type')} - {signal.get('message', '')[:50]}")
            
            # Broadcast to dashboards in real-time
            await broadcast_to_dashboards({
                "type": "new_signal",
                "data": signal
            })
            
    except WebSocketDisconnect:
        print("❌ SDK disconnected")

# WebSocket endpoint for dashboard (admins view signals here)
@app.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    await websocket.accept()
    store.connected_dashboards.append(websocket)
    print("✅ Dashboard connected")
    
    # Send recent signals on connect
    recent = store.get_recent(20)
    await websocket.send_text(json.dumps({
        "type": "initial_signals",
        "data": recent
    }))
    
    try:
        while True:
            # Keep connection alive (dashboard can send commands here)
            data = await websocket.receive_text()
            command = json.loads(data)
            
            if command.get("action") == "approve":
                # Handle approval
                await websocket.send_text(json.dumps({
                    "type": "approval_confirmed",
                    "data": {"message": "Action approved and executed"}
                }))
    
    except WebSocketDisconnect:
        store.connected_dashboards.remove(websocket)
        print("❌ Dashboard disconnected")

async def broadcast_to_dashboards(message):
    """Broadcast a message to all dashboards"""
    message_str = json.dumps(message)
    disconnected = []
    
    for ws in store.connected_dashboards:
        try:
            await ws.send_text(message_str)
        except:
            disconnected.append(ws)
    
    for ws in disconnected:
        store.connected_dashboards.remove(ws)

@app.get("/")
def root():
    return {
        "status": "Real-time Healing Agent Running",
        "signals_received": len(store.signals),
        "active_dashboards": len(store.connected_dashboards)
    }

@app.get("/stats")
def get_stats():
    """Get current statistics"""
    return {
        "total_signals": len(store.signals),
        "active_patterns": len(store.patterns),
        "connected_dashboards": len(store.connected_dashboards),
        "recent_signals": store.get_recent(10)
    }

# Start background monitor on startup
@app.on_event("startup")
async def startup():
    asyncio.create_task(pattern_monitor())
    print("🚀 Pattern monitor started")