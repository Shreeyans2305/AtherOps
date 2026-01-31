# agents/decision.py - Plans appropriate actions
from models.schemas import Hypothesis, ActionPlan
from memory.working_memory import WorkingMemory
import uuid
from typing import Dict
class DecisionAgent:
    """Determines appropriate actions based on hypothesis"""
    
    def __init__(self, working_memory: WorkingMemory):
        self.memory = working_memory
    
    def decide(self, hypothesis: Hypothesis) -> ActionPlan:
        """
        Create action plan based on hypothesis
        """
        action_type = self._determine_action_type(hypothesis)
        priority = self._calculate_priority(hypothesis)
        risk_level = self._assess_risk(hypothesis)
        requires_approval = self._needs_approval(risk_level, action_type)
        
        action_details = self._build_action_details(hypothesis, action_type)
        impact = self._estimate_impact(hypothesis)
        
        plan = ActionPlan(
            plan_id=str(uuid.uuid4()),
            hypothesis_id=hypothesis.hypothesis_id,
            action_type=action_type,
            priority=priority,
            risk_level=risk_level,
            requires_approval=requires_approval,
            action_details=action_details,
            estimated_impact=impact
        )
        
        self.memory.add_action_plan(plan)
        return plan
    
    def _determine_action_type(self, hyp: Hypothesis) -> str:
        """Decide what type of action to take"""
        root_cause = hyp.root_cause.lower()
        
        if "merchant config" in root_cause or "documentation gap" in root_cause:
            return "merchant_communication"
        elif "platform bug" in root_cause or "api version" in root_cause:
            return "engineering_escalation"
        elif "external service" in root_cause:
            return "support_guidance"
        elif hyp.confidence < 0.6:
            return "support_guidance"
        else:
            return "temporary_mitigation"
    
    def _calculate_priority(self, hyp: Hypothesis) -> str:
        """Calculate priority based on severity and merchant count"""
        obs = self.memory.get_observation(hyp.observation_id)
        
        if not obs:
            return "medium"
        
        if obs.severity.value == "critical":
            return "critical"
        elif obs.severity.value == "high" and len(obs.affected_merchants) >= 5:
            return "high"
        elif len(obs.affected_merchants) >= 10:
            return "high"
        elif obs.severity.value == "medium":
            return "medium"
        else:
            return "low"
    
    def _assess_risk(self, hyp: Hypothesis) -> str:
        """Assess risk of taking action"""
        if hyp.confidence < 0.5:
            return "high"
        elif "platform bug" in hyp.root_cause.lower():
            return "high"
        elif "merchant config" in hyp.root_cause.lower():
            return "low"
        else:
            return "medium"
    
    def _needs_approval(self, risk_level: str, action_type: str) -> bool:
        """Determine if human approval is needed"""
        if risk_level == "high":
            return True
        if action_type == "engineering_escalation":
            return True
        if action_type == "merchant_communication":
            return False  # Safe to auto-send
        return False
    
    def _build_action_details(self, hyp: Hypothesis, action_type: str) -> Dict:
        """Build specific action details"""
        obs = self.memory.get_observation(hyp.observation_id)
        
        if action_type == "merchant_communication":
            return {
                "subject": f"Action Required: {obs.pattern_key}",
                "body": f"""We've detected an issue affecting your store:

{hyp.diagnosis}

Recommended steps:
1. Check your configuration for: {hyp.root_cause}
2. Review documentation: {', '.join(hyp.related_docs[:2])}
3. Contact support if issue persists

Affected merchants: {len(obs.affected_merchants)}
""",
                "recipients": obs.affected_merchants
            }
        
        elif action_type == "engineering_escalation":
            return {
                "title": f"[AUTO] Platform Issue: {obs.pattern_key}",
                "description": hyp.diagnosis,
                "affected_count": len(obs.affected_merchants),
                "severity": obs.severity.value,
                "evidence": hyp.evidence
            }
        
        elif action_type == "support_guidance":
            return {
                "guidance": f"Create support article: {hyp.root_cause}",
                "talking_points": hyp.evidence
            }
        
        else:
            return {"description": hyp.diagnosis}
    
    def _estimate_impact(self, hyp: Hypothesis) -> str:
        """Estimate impact of taking action"""
        obs = self.memory.get_observation(hyp.observation_id)
        merchant_count = len(obs.affected_merchants)
        
        return f"Will notify/help {merchant_count} affected merchant(s). Confidence: {int(hyp.confidence * 100)}%"