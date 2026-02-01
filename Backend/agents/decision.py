# agents/decision.py - Hybrid approach with conditional LLM
from models.schemas import Hypothesis, ActionPlan, Severity
from memory.working_memory import WorkingMemory
from memory.long_memory import LongTermMemory
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from agents.prompts.decision_prompts import (
    DECISION_SYSTEM_PROMPT,
    DECISION_PLANNING_TEMPLATE
)
import uuid
import json

class DecisionAgent:
    """
    Determines appropriate actions based on hypothesis
    Uses HYBRID approach: rule-based for clear cases, LLM for complex ones
    """
    
    def __init__(self, working_memory: WorkingMemory, long_memory: LongTermMemory):
        self.memory = working_memory
        self.long_memory = long_memory
        self.llm = ChatOllama(
            model="llama3.1:8b",
            temperature=0.3,  # Balanced for creativity + consistency
            num_predict=1024
        )
        
        # Simple decision rules for common cases
        self.decision_rules = self._build_decision_rules()
    
    def decide(self, hypothesis: Hypothesis) -> ActionPlan:
        """
        Create action plan - uses rules first, LLM for complex cases
        """
        obs = self.memory.get_observation(hypothesis.observation_id)
        
        # Try rule-based decision first
        simple_decision = self._try_rule_based_decision(hypothesis, obs)
        
        if simple_decision:
            print(f"   📋 Rule-based decision: {simple_decision['action_type']}")
            return self._create_action_plan(hypothesis, simple_decision)
        
        # Complex case - use LLM
        print(f"   🧠 Complex case - using LLM for decision...")
        llm_decision = self._llm_decide(hypothesis, obs)
        return self._create_action_plan(hypothesis, llm_decision)
    
    def _build_decision_rules(self) -> dict:
        """Build simple decision tree for common patterns"""
        return {
            # Rule: Merchant config errors → communicate
            "merchant_config": {
                "action_type": "merchant_communication",
                "priority": "medium",
                "risk_level": "low",
                "requires_approval": False
            },
            # Rule: Platform bugs → escalate
            "platform_bug": {
                "action_type": "engineering_escalation",
                "priority": "high",
                "risk_level": "high",
                "requires_approval": True
            },
            # Rule: External service issues → support guidance
            "external_service": {
                "action_type": "support_guidance",
                "priority": "medium",
                "risk_level": "low",
                "requires_approval": False
            },
            # Rule: Documentation gaps → update docs
            "documentation_gap": {
                "action_type": "documentation_update",
                "priority": "low",
                "risk_level": "low",
                "requires_approval": False
            }
        }
    
    def _try_rule_based_decision(self, hyp: Hypothesis, obs) -> dict:
        """
        Try to make decision using simple rules
        Returns None if case is too complex for rules
        """
        root_cause = hyp.root_cause.lower()
        confidence = hyp.confidence
        merchant_count = len(obs.affected_merchants) if obs else 0
        
        # Rule 1: Low confidence → need more data
        if confidence < 0.5:
            return {
                "action_type": "support_guidance",
                "priority": "low",
                "risk_level": "low",
                "requires_approval": False,
                "reasoning": "Low confidence - gather more data before acting"
            }
        
        # Rule 2: Single merchant + merchant config → communicate
        if merchant_count == 1 and "merchant" in root_cause and "config" in root_cause:
            return {
                "action_type": "merchant_communication",
                "priority": "low",
                "risk_level": "low",
                "requires_approval": False,
                "reasoning": "Single merchant config issue - direct communication"
            }
        
        # Rule 3: High confidence platform bug → escalate
        if confidence > 0.8 and "platform" in root_cause and "bug" in root_cause:
            priority = "critical" if merchant_count >= 10 else "high"
            return {
                "action_type": "engineering_escalation",
                "priority": priority,
                "risk_level": "high",
                "requires_approval": True,
                "reasoning": "High confidence platform bug affecting multiple merchants"
            }
        
        # Rule 4: External service + multiple merchants → support guidance
        if "external" in root_cause and merchant_count >= 3:
            return {
                "action_type": "support_guidance",
                "priority": "medium",
                "risk_level": "low",
                "requires_approval": False,
                "reasoning": "External service issue - provide support guidance"
            }
        
        # Rule 5: Documentation gap → update docs
        if "documentation" in root_cause or "doc" in root_cause:
            return {
                "action_type": "documentation_update",
                "priority": "low",
                "risk_level": "low",
                "requires_approval": False,
                "reasoning": "Documentation needs updating"
            }
        
        # Rule 6: API version mismatch + migration → merchant communication
        if "api version" in root_cause or "mismatch" in root_cause:
            return {
                "action_type": "merchant_communication",
                "priority": "high",
                "risk_level": "low",
                "requires_approval": False,
                "reasoning": "API version mismatch - merchants need to update"
            }
        
        # Rule 7: Ticket-based critical issues (from support tickets)
        # Check observation pattern for ticket source
        pattern_key = obs.pattern_key.lower() if obs else ""
        if "ticket_" in pattern_key:
            # This is from a support ticket - extract priority from pattern
            if "critical" in pattern_key:
                return {
                    "action_type": "engineering_escalation",
                    "priority": "critical",
                    "risk_level": "high",
                    "requires_approval": False,  # Critical tickets auto-execute
                    "reasoning": "Critical support ticket - immediate escalation required"
                }
            elif "high" in pattern_key:
                return {
                    "action_type": "engineering_escalation",
                    "priority": "high",
                    "risk_level": "high",
                    "requires_approval": False,
                    "reasoning": "High priority support ticket - escalation required"
                }
            elif "payment" in pattern_key:
                # Payment issues are always high priority
                return {
                    "action_type": "engineering_escalation",
                    "priority": "high",
                    "risk_level": "high",
                    "requires_approval": False,
                    "reasoning": "Payment-related ticket - immediate attention required"
                }
            elif "medium" in pattern_key:
                # Medium priority tickets → merchant communication
                return {
                    "action_type": "merchant_communication",
                    "priority": "medium",
                    "risk_level": "low",
                    "requires_approval": False,
                    "reasoning": "Medium priority support ticket - merchant communication"
                }
            elif "low" in pattern_key:
                # Low priority tickets → support guidance
                return {
                    "action_type": "support_guidance",
                    "priority": "low",
                    "risk_level": "low",
                    "requires_approval": False,
                    "reasoning": "Low priority support ticket - support guidance"
                }
            else:
                # Default for any other ticket - merchant communication
                return {
                    "action_type": "merchant_communication",
                    "priority": "medium",
                    "risk_level": "low",
                    "requires_approval": False,
                    "reasoning": "Support ticket - merchant communication"
                }
        
        # Rule 8: Critical severity from observation
        if obs and obs.severity in ["critical", Severity.CRITICAL]:
            return {
                "action_type": "engineering_escalation",
                "priority": "critical",
                "risk_level": "high",
                "requires_approval": False,
                "reasoning": "Critical severity issue - immediate escalation"
            }
        
        # Complex case - no clear rule matches
        return None
    
    def _llm_decide(self, hyp: Hypothesis, obs) -> dict:
        """Use LLM for complex decision-making"""
        
        # Get historical resolutions
        similar = self.long_memory.find_similar_incidents(obs.pattern_key)
        historical_text = "None"
        if similar:
            resolutions = []
            for inc in similar[:2]:
                resolutions.append(f"- {inc.get('action_taken', 'Unknown')}: {inc.get('resolution', 'N/A')}")
            historical_text = "\n".join(resolutions)
        
        # Build context
        evidence_text = "\n".join(f"- {e}" for e in hyp.evidence[:3])
        
        user_prompt = DECISION_PLANNING_TEMPLATE.format(
            root_cause=hyp.root_cause,
            confidence=int(hyp.confidence * 100),
            diagnosis=hyp.diagnosis,
            evidence=evidence_text,
            pattern_key=obs.pattern_key,
            merchant_count=len(obs.affected_merchants),
            severity=obs.severity,
            event_count=obs.event_count,
            historical_resolutions=historical_text
        )
        
        try:
            messages = [
                SystemMessage(content=DECISION_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            # Parse JSON
            text = response.content
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            decision = json.loads(text.strip())
            return decision
        
        except Exception as e:
            print(f"   ⚠️  LLM decision failed: {e}")
            # Fallback to conservative decision
            return {
                "action_type": "support_guidance",
                "priority": "medium",
                "risk_level": "medium",
                "requires_approval": True,
                "reasoning": "LLM decision failed - defaulting to safe option"
            }
    
    def _create_action_plan(self, hyp: Hypothesis, decision: dict) -> ActionPlan:
        """Create ActionPlan from decision dict"""
        obs = self.memory.get_observation(hyp.observation_id)
        
        # Build action details based on type
        action_details = self._build_action_details(
            decision["action_type"],
            hyp,
            obs
        )
        
        # Calculate impact
        impact = decision.get(
            "estimated_impact",
            f"Will address issue for {len(obs.affected_merchants)} merchant(s)"
        )
        
        plan = ActionPlan(
            plan_id=str(uuid.uuid4()),
            hypothesis_id=hyp.hypothesis_id,
            action_type=decision["action_type"],
            priority=decision["priority"],
            risk_level=decision["risk_level"],
            requires_approval=decision["requires_approval"],
            action_details=action_details,
            estimated_impact=impact
        )
        
        self.memory.add_action_plan(plan)
        return plan
    
    def _build_action_details(self, action_type: str, hyp: Hypothesis, obs) -> dict:
        """Build specific action details"""
        if action_type == "merchant_communication":
            # Extract merchant emails from events metadata
            merchant_emails = {}
            for event in obs.events:
                merchant_id = event.merchant_id
                # Check event metadata for merchant email
                if event.metadata:
                    email = event.metadata.get("merchant_email")
                    if email and merchant_id:
                        merchant_emails[merchant_id] = email
            
            return {
                "subject": f"Action Required: {obs.pattern_key.replace('_', ' ').title()}",
                "body": f"""We've detected an issue affecting your store:

{hyp.diagnosis}

Recommended steps:
{self._format_evidence_as_steps(hyp.evidence)}

If you need assistance, please contact support with reference: {obs.observation_id}

Affected merchants: {len(obs.affected_merchants)}
""",
                "recipients": obs.affected_merchants,
                "merchant_emails": merchant_emails  # Include actual email addresses
            }
        
        elif action_type == "engineering_escalation":
            return {
                "title": f"[AUTO-ESCALATION] {obs.pattern_key}",
                "description": hyp.diagnosis,
                "affected_count": len(obs.affected_merchants),
                "severity": obs.severity,
                "evidence": hyp.evidence,
                "confidence": int(hyp.confidence * 100)
            }
        
        elif action_type == "support_guidance":
            return {
                "guidance": f"Pattern: {obs.pattern_key}",
                "talking_points": hyp.evidence,
                "resolution": hyp.diagnosis
            }
        
        elif action_type == "documentation_update":
            return {
                "section": obs.pattern_key.replace("_", " ").title(),
                "content": hyp.diagnosis,
                "related_docs": hyp.related_docs
            }
        
        else:
            return {"description": hyp.diagnosis}
    
    def _format_evidence_as_steps(self, evidence: list) -> str:
        """Format evidence as actionable steps"""
        if not evidence:
            return "Please check your configuration"
        
        steps = []
        for i, item in enumerate(evidence[:3], 1):
            steps.append(f"{i}. {item}")
        
        return "\n".join(steps)