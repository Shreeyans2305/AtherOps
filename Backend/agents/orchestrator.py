# agents/orchestrator.py - Coordinates the agent pipeline with enhanced broadcasting
from agents.observer_hybrid import HybridObserverAgent
from agents.reasoner import ReasonerAgent
from agents.decision import DecisionAgent
from agents.executor import ExecutorAgent
from memory.working_memory import WorkingMemory
from memory.long_memory import LongTermMemory
from datetime import datetime
import asyncio

class AgentOrchestrator:
    """Coordinates the multi-agent pipeline with detailed broadcasting"""
    
    def __init__(self):
        self.working_memory = WorkingMemory()
        self.long_memory = LongTermMemory()
        
        self.observer = HybridObserverAgent(self.working_memory)
        self.reasoner = ReasonerAgent(self.working_memory, self.long_memory)
        self.decision = DecisionAgent(self.working_memory, self.long_memory)
        self.executor = ExecutorAgent()
        
        self.dashboard_connections = []  # WebSocket connections
    
    async def run_pipeline(self):
        """
        Main agent loop: Observe → Reason → Decide → Execute
        Runs continuously in background with detailed broadcasting
        """
        while True:
            try:
                print("\n" + "="*60)
                print("🔄 RUNNING AGENT PIPELINE")
                print("="*60)
                
                # STEP 1: Observer detects patterns
                print("\n👁️  OBSERVER: Analyzing recent events...")
                await self._broadcast_to_dashboard({
                    "type": "agent_step",
                    "agent": "observer",
                    "status": "running",
                    "timestamp": datetime.now().isoformat()
                })
                
                observations = self.observer.observe()
                
                if not observations:
                    print("   No significant patterns detected")
                    await self._broadcast_to_dashboard({
                        "type": "agent_step",
                        "agent": "observer",
                        "status": "completed",
                        "result": "no_patterns",
                        "timestamp": datetime.now().isoformat()
                    })
                    await asyncio.sleep(30)
                    continue
                
                print(f"   ✅ Detected {len(observations)} pattern(s)")
                
                # Broadcast observations created
                for obs in observations:
                    await self._broadcast_to_dashboard({
                        "type": "observation_created",
                        "observation": obs.dict(),
                        "timestamp": datetime.now().isoformat()
                    })
                
                await self._broadcast_to_dashboard({
                    "type": "agent_step",
                    "agent": "observer",
                    "status": "completed",
                    "result": f"{len(observations)} patterns detected",
                    "observations_count": len(observations),
                    "timestamp": datetime.now().isoformat()
                })
                
                # STEP 2: Reasoner diagnoses each observation
                for obs in observations:
                    print(f"\n🧠 REASONER: Analyzing '{obs.pattern_key}'...")
                    await self._broadcast_to_dashboard({
                        "type": "agent_step",
                        "agent": "reasoner",
                        "status": "running",
                        "observation_id": obs.observation_id,
                        "pattern_key": obs.pattern_key,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    hypothesis = self.reasoner.reason(obs)
                    print(f"   Root cause: {hypothesis.root_cause} ({int(hypothesis.confidence*100)}% confident)")
                    
                    # Broadcast hypothesis generated
                    await self._broadcast_to_dashboard({
                        "type": "hypothesis_generated",
                        "hypothesis": hypothesis.dict(),
                        "observation_id": obs.observation_id,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    await self._broadcast_to_dashboard({
                        "type": "agent_step",
                        "agent": "reasoner",
                        "status": "completed",
                        "result": hypothesis.root_cause,
                        "confidence": hypothesis.confidence,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # STEP 3: Decision agent plans action
                    print(f"\n⚖️  DECISION: Planning action...")
                    await self._broadcast_to_dashboard({
                        "type": "agent_step",
                        "agent": "decision",
                        "status": "running",
                        "hypothesis_id": hypothesis.hypothesis_id,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    plan = self.decision.decide(hypothesis)
                    print(f"   Action: {plan.action_type} (priority: {plan.priority}, risk: {plan.risk_level})")
                    
                    # Broadcast action plan created
                    await self._broadcast_to_dashboard({
                        "type": "action_planned",
                        "plan": plan.dict(),
                        "hypothesis_id": hypothesis.hypothesis_id,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    await self._broadcast_to_dashboard({
                        "type": "agent_step",
                        "agent": "decision",
                        "status": "completed",
                        "result": plan.action_type,
                        "priority": plan.priority,
                        "risk_level": plan.risk_level,
                        "requires_approval": plan.requires_approval,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Broadcast complete incident (for backward compatibility)
                    await self._broadcast_to_dashboard({
                        "type": "new_incident",
                        "observation": obs.dict(),
                        "hypothesis": hypothesis.dict(),
                        "plan": plan.dict()
                    })
                    
                    # STEP 4: Executor runs action (if auto-approved)
                    if not plan.requires_approval:
                        print(f"\n✅ EXECUTOR: Auto-executing...")
                        await self._broadcast_to_dashboard({
                            "type": "agent_step",
                            "agent": "executor",
                            "status": "running",
                            "plan_id": plan.plan_id,
                            "action_type": plan.action_type,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        result = await self.executor.execute(plan, approved=True)
                        print(f"   Status: {result.status}")
                        
                        # Broadcast execution result with email info
                        await self._broadcast_to_dashboard({
                            "type": "action_executed",
                            "result": result.dict(),
                            "plan_id": plan.plan_id,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        # Check if email was sent and broadcast separately
                        if result.result_details:
                            email_sent = result.result_details.get("email_sent") or result.result_details.get("emails_sent", 0) > 0
                            if email_sent:
                                await self._broadcast_to_dashboard({
                                    "type": "email_sent",
                                    "plan_id": plan.plan_id,
                                    "action_type": plan.action_type,
                                    "recipients": result.result_details.get("recipients", []),
                                    "subject": result.result_details.get("subject", ""),
                                    "email_result": result.result_details.get("email_result"),
                                    "timestamp": datetime.now().isoformat()
                                })
                        
                        await self._broadcast_to_dashboard({
                            "type": "agent_step",
                            "agent": "executor",
                            "status": "completed",
                            "result": result.status,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        # Store successful resolution
                        if result.status == "success":
                            self._store_resolved_incident(obs, hypothesis, plan, result)
                    else:
                        print(f"\n⏳ EXECUTOR: Awaiting human approval...")
                        await self._broadcast_to_dashboard({
                            "type": "agent_step",
                            "agent": "executor",
                            "status": "pending_approval",
                            "plan_id": plan.plan_id,
                            "timestamp": datetime.now().isoformat()
                        })
                
                print("\n" + "="*60)
                print("✅ PIPELINE CYCLE COMPLETE")
                print("="*60)
                
            except Exception as e:
                print(f"❌ Pipeline error: {e}")
                await self._broadcast_to_dashboard({
                    "type": "pipeline_error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            
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