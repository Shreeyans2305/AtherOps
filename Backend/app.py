# app.py - FastAPI backend
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agent_langgraph import HealingAgent
from fake_data import MOCK_SIGNALS
import asyncio
from concurrent.futures import ThreadPoolExecutor

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = HealingAgent()
executor = ThreadPoolExecutor(max_workers=1)

@app.get("/")
def root():
    return {"status": "Self-Healing Agent Running with LangGraph + Ollama"}

@app.get("/analyze")
async def run_analysis():
    """Trigger the agent workflow"""
    # Run in thread pool since LangGraph is synchronous
    loop = asyncio.get_event_loop()
    decisions = await loop.run_in_executor(executor, agent.run, MOCK_SIGNALS)
    
    return {"issues": decisions}

@app.post("/approve/{issue_id}")
def approve_action(issue_id: int):
    """Human approves an action"""
    return {
        "message": f"✅ Action {issue_id} approved! Email sent to merchants.",
        "action_taken": "sent_proactive_email",
        "timestamp": "2026-01-31T12:00:00"
    }

@app.get("/agent-status")
def get_status():
    """Shows the agent's current state"""
    return {
        "model": "llama3.2:3b (local)",
        "framework": "LangGraph",
        "status": "ready"
    }