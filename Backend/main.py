# main.py - FastAPI application with all integrations
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
import asyncio
import json

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from agents.orchestrator import AgentOrchestrator
from ingestion.receivers import EventReceiver
from services.ticket_service import ticket_service, Ticket, TicketPriority
from models.schemas import UnifiedEvent, EventType, Severity
from datetime import datetime, timezone
import uuid

# Database and Authentication
from database import get_db, init_db
from auth import get_current_user, get_optional_user, require_organization
import db_models



# Pydantic model for ticket creation request
class TicketCreateRequest(BaseModel):
    title: str
    description: str
    merchant_id: str
    merchant_email: Optional[str] = None
    priority: str = "medium"  # low, medium, high, critical
    category: Optional[str] = None
    tags: List[str] = []
    reporter_email: Optional[str] = None
    metadata: dict = {}

# Create orchestrator
orchestrator = AgentOrchestrator()
event_queue = asyncio.Queue()
event_receiver = EventReceiver(event_queue)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database and start background tasks
    print("🗄️  Initializing database...")
    init_db()
    print("✅ Database initialized")
    
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

# WebSocket: Dashboard receives updates here (requires authentication)
@app.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket, token: Optional[str] = Query(None)):
    await websocket.accept()
    
    # Verify authentication
    user = None
    if token:
        try:
            from auth import verify_clerk_token
            user = verify_clerk_token(token)
            print(f"✅ Dashboard connected - User: {user.get('email')}, Org: {user.get('org_id')}")
        except Exception as e:
            print(f"❌ Dashboard authentication failed: {e}")
            await websocket.close(code=1008, reason="Authentication required")
            return
    else:
        print("⚠️  Dashboard connected without authentication (development mode)")
    
    orchestrator.dashboard_connections.append(websocket)
    
    try:
        # Send current state (filtered by organization if authenticated)
        try:
            await websocket.send_text(json.dumps({
                "type": "initial_state",
                "observations": [obs.dict() for obs in orchestrator.working_memory.get_active_observations()],
                "hypotheses": list(orchestrator.working_memory.hypotheses.values()),
                "plans": list(orchestrator.working_memory.action_plans.values()),
                "user": user
            }, default=str))
        except (WebSocketDisconnect, RuntimeError, Exception) as e:
            print(f"⚠️ Failed to send initial state (client disconnected?): {e}")
            if websocket in orchestrator.dashboard_connections:
                orchestrator.dashboard_connections.remove(websocket)
            return
    
        while True:
            try:
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
            except (WebSocketDisconnect, RuntimeError):
                raise  # Re-raise to be caught by outer block
            except Exception as e:
                print(f"❌ Error processing dashboard command: {e}")
                # Don't break loop for minor processing errors
                continue
    
    except WebSocketDisconnect:
        if websocket in orchestrator.dashboard_connections:
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

@app.get("/api/recent-events")
def get_recent_events(hours: int = 24):
    """Get recent events from the last N hours with timestamps"""
    from datetime import timedelta
    
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    recent_events = [
        {
            **event.dict(),
            "timestamp": event.timestamp.isoformat()
        }
        for event in orchestrator.working_memory.events
        if event.timestamp >= cutoff_time
    ]
    
    # Sort by timestamp descending (newest first)
    recent_events.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return {
        "events": recent_events,
        "count": len(recent_events),
        "time_range_hours": hours
    }

@app.get("/api/agent-activity")
def get_agent_activity():
    """Get current agent pipeline status and activity"""
    return {
        "observers": {
            "active_observations": len(orchestrator.working_memory.get_active_observations()),
            "total_observations": len(orchestrator.working_memory.observations)
        },
        "reasoner": {
            "hypotheses_generated": len(orchestrator.working_memory.hypotheses)
        },
        "decision": {
            "action_plans": len(orchestrator.working_memory.action_plans),
            "pending_approval": len([
                p for p in orchestrator.working_memory.action_plans.values()
                if p.requires_approval
            ])
        },
        "executor": {
            "total_plans": len(orchestrator.working_memory.action_plans)
        },
        "recent_activity": {
            "events_last_hour": len([
                e for e in orchestrator.working_memory.events
                if (datetime.now(timezone.utc) - e.timestamp).total_seconds() < 3600
            ])
        }
    }

@app.post("/webhook/failure")
async def receive_webhook_failure(payload: dict):
    """Receive webhook delivery failures"""
    await event_receiver.receive_webhook_event(payload)
    return {"status": "received"}


# ============================================================================
# TICKET ENDPOINTS - Scalable ticket processing system
# ============================================================================

async def process_ticket_through_pipeline(ticket: Ticket):
    """
    Process a ticket through the agent pipeline immediately.
    Tickets are direct incidents that don't need pattern detection.
    We process them through Reason → Decide → Execute directly.
    """
    from models.schemas import Observation, Hypothesis, ActionPlan
    
    print(f"\n{'='*60}")
    print(f"🎫 PROCESSING TICKET DIRECTLY: {ticket.ticket_id}")
    print(f"{'='*60}")
    
    # Map ticket priority to severity
    priority_to_severity = {
        "low": Severity.LOW,
        "medium": Severity.MEDIUM,
        "high": Severity.HIGH,
        "critical": Severity.CRITICAL,
    }
    
    severity = priority_to_severity.get(ticket.priority, Severity.MEDIUM)
    
    # Create a UnifiedEvent from the ticket
    event = UnifiedEvent(
        event_id=str(uuid.uuid4()),
        merchant_id=ticket.merchant_id,
        timestamp=datetime.now(timezone.utc),
        event_type=EventType.TICKET,  # Use specific type for correct frontend classification
        severity=severity,
        message=f"[TICKET] {ticket.title}: {ticket.description}",
        metadata={
            "ticket_id": ticket.ticket_id,
            "source": "ticket",
            "category": ticket.category,
            "tags": ticket.tags,
            "merchant_email": ticket.merchant_email,
            "reporter_email": ticket.reporter_email,
            "original_metadata": ticket.metadata,
        },
        source="ticket",
    )
    
    # Add to working memory for tracking
    orchestrator.working_memory.add_event(event)
    
    # Broadcast event for live chart updates
    await orchestrator._broadcast_to_dashboard({
        "type": "new_event",
        "event": event.dict()
    })

    # Create observation manually since we're bypassing observer
    obs = Observation(
        observation_id=str(uuid.uuid4()),
        pattern_key=f"ticket:{event.message}",
        description=f"User reported issue: {event.message}",
        affected_merchants=[event.merchant_id],
        event_count=1,
        first_seen=event.timestamp,
        last_seen=event.timestamp,
        severity=event.severity,
        events=[event],
        confidence=1.0  # Tickets are high confidence
    )
    
    orchestrator.working_memory.add_observation(obs)
    print(f"   📋 Created observation from ticket")
    
    # Broadcast to dashboard
    await orchestrator._broadcast_to_dashboard({
        "type": "new_ticket_incident",
        "observation": obs.dict(),
        "ticket": ticket.dict() # Use ticket.dict() as ticket_data is not defined
    })
    
    # STEP 2: Run through Reasoner
    print(f"\n🧠 REASONER: Analyzing ticket...")
    hypothesis = orchestrator.reasoner.reason(obs)
    print(f"   Root cause: {hypothesis.root_cause} ({int(hypothesis.confidence*100)}% confident)")
    
    # STEP 3: Run through Decision Agent
    print(f"\n⚖️  DECISION: Planning action...")
    plan = orchestrator.decision.decide(hypothesis)
    print(f"   Action: {plan.action_type} (priority: {plan.priority}, risk: {plan.risk_level})")
    
    # Inject merchant email into action details if available
    if ticket.merchant_email and plan.action_type == "merchant_communication":
        plan.action_details["merchant_emails"] = {ticket.merchant_id: ticket.merchant_email}
    
    # Broadcast to dashboard
    await orchestrator._broadcast_to_dashboard({
        "type": "new_ticket_incident",
        "ticket": ticket.dict(),
        "observation": obs.dict(),
        "hypothesis": hypothesis.dict(),
        "plan": plan.dict()
    })
    
    # STEP 4: Execute (based on approval requirements)
    if not plan.requires_approval:
        print(f"\n✅ EXECUTOR: Auto-executing...")
        result = await orchestrator.executor.execute(plan, approved=True)
        print(f"   Status: {result.status}")
        print(f"   Result: {result.result_details}")
        
        # Store successful resolution
        if result.status == "success":
            orchestrator._store_resolved_incident(obs, hypothesis, plan, result)
            
        await orchestrator._broadcast_to_dashboard({
            "type": "ticket_execution_result",
            "ticket_id": ticket.ticket_id,
            "result": result.dict()
        })
    else:
        print(f"\n⏳ EXECUTOR: Awaiting human approval (risk: {plan.risk_level})...")
    
    print(f"\n{'='*60}")
    print(f"✅ TICKET PROCESSING COMPLETE")
    print(f"{'='*60}\n")
    
    return event


# Register the callback when the module loads
ticket_service.on_ticket_created(process_ticket_through_pipeline)


@app.post("/api/tickets")
async def create_ticket(request: TicketCreateRequest):
    """
    Create a new ticket and process it through the agent pipeline.
    
    This endpoint is designed to be scalable:
    - Currently accepts tickets from the frontend
    - Can be extended to accept webhooks from Jira, Zendesk, etc.
    - The ticket_service handles the abstraction
    """
    ticket = await ticket_service.create_ticket(request.dict())
    
    return {
        "status": "success",
        "ticket_id": ticket.ticket_id,
        "message": "Ticket created and processing through the healing pipeline",
        "ticket": ticket.dict()
    }


@app.get("/api/tickets")
async def get_all_tickets():
    """Get all tickets in the system"""
    tickets = await ticket_service.get_all_tickets()
    return {
        "tickets": [t.dict() for t in tickets],
        "count": len(tickets)
    }


@app.get("/api/tickets/{ticket_id}")
async def get_ticket(ticket_id: str):
    """Get a specific ticket by ID"""
    ticket = await ticket_service.get_ticket(ticket_id)
    if not ticket:
        return {"error": "Ticket not found"}, 404
    return {"ticket": ticket.dict()}


@app.patch("/api/tickets/{ticket_id}/status")
async def update_ticket_status(ticket_id: str, status: str):
    """Update a ticket's status"""
    from services.ticket_service import TicketStatus
    
    try:
        ticket_status = TicketStatus(status)
    except ValueError:
        return {"error": f"Invalid status: {status}"}, 400
    
    success = await ticket_service.update_status(ticket_id, ticket_status)
    if not success:
        return {"error": "Ticket not found or update failed"}, 404
    
    return {"status": "updated", "new_status": status}