# agents/orchestrator.py - Coordinates the agent pipeline
from agents.observer import ObserverAgent
from agents.reasoner import ReasonerAgent
from agents.decision import DecisionAgent
from agents.executor import ExecutorAgent
from memory.working_memory import WorkingMemory
from memory.long_memory import LongTermMemory
import asyncio

class AgentOrchestrator:
    """Coordinates the multi-agent pipeline"""
    
    def __init__(self):
        self.working_memory = WorkingMemory()
        self.long_memory = LongTermMemory()
        
        self.observer = ObserverAgent(self.working_memory)
        self.reasoner = ReasonerAgent(self.working_memory, self.long_memory)
        self.decision = DecisionAgent(self.working_memory)
        self.executor = ExecutorAgent()
        
        self.dashboard_connections = []  # WebSocket connections
    
    async def run_pipeline(self):
        """
        Main agent loop: Observe → Reason → Decide → Execute
        Runs continuously in background
        """
        while True:
            try:
                print("\n" + "="*60)
                print("🔄 RUNNING AGENT PIPELINE")
                print("="*60)
                
                # STEP 1: Observer detects patterns
                print("\n👁️  OBSERVER: Analyzing recent events...")
                observations = self.observer.observe()
                
                if not observations:
                    print("   No significant patterns detected")
                    await asyncio.sleep(30)
                    continue
                
                print(f"   ✅ Detected {len(observations)} pattern(s)")
                
                # STEP 2: Reasoner diagnoses each observation
                for obs in observations:
                    print(f"\n🧠 REASONER: Analyzing '{obs.pattern_key}'...")
                    hypothesis = self.reasoner.reason(obs)
                    print(f"   Root cause: {hypothesis.root_cause} ({int(hypothesis.confidence*100)}% confident)")
                    
                    # STEP 3: Decision agent plans action
                    print(f"\n⚖️  DECISION: Planning action...")
                    plan = self.decision.decide(hypothesis)
                    print(f"   Action: {plan.action_type} (priority: {plan.priority}, risk: {plan.risk_level})")
                    
                    # Broadcast to dashboard
                    await self._broadcast_to_dashboard({
                        "type": "new_incident",
                        "observation": obs.dict(),
                        "hypothesis": hypothesis.dict(),
                        "plan": plan.dict()
                    })
                    
                    # STEP 4: Executor runs action (if auto-approved)
                    if not plan.requires_approval:
                        print(f"\n✅ EXECUTOR: Auto-executing...")
                        result = await self.executor.execute(plan, approved=True)
                        print(f"   Status: {result.status}")
                        
                        # Store successful resolution
                        if result.status == "success":
                            self._store_resolved_incident(obs, hypothesis, plan, result)
                    else:
                        print(f"\n⏳ EXECUTOR: Awaiting human approval...")
                
                print("\n" + "="*60)
                print("✅ PIPELINE CYCLE COMPLETE")
                print("="*60)
                
            except Exception as e:
                print(f"❌ Pipeline error: {e}")
            
            # Wait before next cycle
            await asyncio.sleep(30)
    
    def _store_resolved_incident(self, obs, hyp, plan, result):
        """Store successful resolution in long-term memory"""
        incident = {
            "pattern_key": obs.pattern_key,
            "root_cause": hyp.root_cause,
            "action_taken": plan.action_type,
            "resolution": plan.action_details.get("subject", plan.action_type),
            "confidence": hyp.confidence,
            "affected_merchants": len(obs.affected_merchants),
            "execution_result": result.dict()
        }
        self.long_memory.store_incident(incident)
    
    async def _broadcast_to_dashboard(self, message):
        """Send update to all connected dashboards"""
        import json
        message_str = json.dumps(message, default=str)
        
        disconnected = []
        for ws in self.dashboard_connections:
            try:
                await ws.send_text(message_str)
            except:
                disconnected.append(ws)
        
        for ws in disconnected:
            self.dashboard_connections.remove(ws)