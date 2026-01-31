# main.py - FastAPI application with all integrations
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import json

from agents.orchestrator import AgentOrchestrator
from ingestion.receivers import EventReceiver

# Create orchestrator
orchestrator = AgentOrchestrator()
event_queue = asyncio.Queue()
event_receiver = EventReceiver(event_queue)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start background tasks
    pipeline_task = asyncio.create_task(orchestrator.run_pipeline())
    ingestion_task = asyncio.create_task(process_event_queue())
    
    print("🚀 Agent pipeline started")
    print("🚀 Event ingestion started")
    
    yield
    
    # Shutdown
    pipeline_task.cancel()
    ingestion_task.cancel()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

async def process_event_queue():
    """Process events from queue and add to memory"""
    while True:
        event = await event_queue.get()
        orchestrator.working_memory.add_event(event)
        
        # Broadcast to dashboards
        await orchestrator._broadcast_to_dashboard({
            "type": "new_event",
            "event": event.dict()
        })

# WebSocket: SDK sends signals here
@app.websocket("/ws/sdk")
async def sdk_websocket(websocket: WebSocket):
    await websocket.accept()
    print("✅ SDK connected")
    
    try:
        while True:
            await event_receiver.receive_sdk_event(websocket)
    except WebSocketDisconnect:
        print("❌ SDK disconnected")

# WebSocket: Dashboard receives updates here
@app.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    await websocket.accept()
    orchestrator.dashboard_connections.append(websocket)
    print("✅ Dashboard connected")
    
    # Send current state
    await websocket.send_text(json.dumps({
        "type": "initial_state",
        "observations": [obs.dict() for obs in orchestrator.working_memory.get_active_observations()],
        "hypotheses": list(orchestrator.working_memory.hypotheses.values()),
        "plans": list(orchestrator.working_memory.action_plans.values())
    }, default=str))
    
    try:
        while True:
            data = await websocket.receive_text()
            command = json.loads(data)
            
            # Handle approval
            if command.get("action") == "approve":
                plan_id = command.get("plan_id")
                plan = orchestrator.working_memory.action_plans.get(plan_id)
                if plan:
                    result = await orchestrator.executor.execute(plan, approved=True)
                    await websocket.send_text(json.dumps({
                        "type": "execution_result",
                        "result": result.dict()
                    }, default=str))
    
    except WebSocketDisconnect:
        orchestrator.dashboard_connections.remove(websocket)
        print("❌ Dashboard disconnected")

@app.get("/")
def root():
    return {
        "status": "Multi-Agent Healing System Running",
        "agents": ["observer", "reasoner", "decision", "executor"],
        "events_in_memory": len(orchestrator.working_memory.events),
        "active_observations": len(orchestrator.working_memory.get_active_observations())
    }

@app.get("/stats")
def get_stats():
    return {
        "total_events": len(orchestrator.working_memory.events),
        "active_observations": len(orchestrator.working_memory.observations),
        "hypotheses": len(orchestrator.working_memory.hypotheses),
        "action_plans": len(orchestrator.working_memory.action_plans),
        "historical_incidents": len(orchestrator.long_memory.incidents)
    }

@app.post("/webhook/failure")
async def receive_webhook_failure(payload: dict):
    """Receive webhook delivery failures"""
    await event_receiver.receive_webhook_event(payload)
    return {"status": "received"}