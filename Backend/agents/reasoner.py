# agents/reasoner.py - Updated with detailed system prompt
from models.schemas import Observation, Hypothesis
from memory.working_memory import WorkingMemory
from memory.long_memory import LongTermMemory
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from agents.prompts.reasoner_prompts import (
    REASONER_SYSTEM_PROMPT,
    REASONER_DIAGNOSIS_TEMPLATE
)
import uuid
import json
from typing import List, Dict

class ReasonerAgent:
    """Analyzes observations and forms hypotheses - now with detailed system prompts"""
    
    def __init__(self, working_memory: WorkingMemory, long_memory: LongTermMemory):
        self.working_memory = working_memory
        self.long_memory = long_memory
        self.llm = ChatOllama(
            model="llama3.1:8b",
            temperature=0.2,  # Slightly higher for nuanced reasoning
            num_predict=1024   # More tokens for detailed diagnosis
        )
    
    def reason(self, observation: Observation) -> Hypothesis:
        """Analyze observation and produce hypothesis"""
        
        # Fast path for tickets - they already have clear descriptions
        if observation.pattern_key.startswith("ticket_"):
            return self._fast_reason_ticket(observation)
        
        # Get historical context
        similar_incidents = self.long_memory.find_similar_incidents(
            observation.pattern_key
        )
        
        # Build rich context for LLM
        context = self._build_reasoning_context(observation, similar_incidents)
        
        # Call LLM with system prompt
        diagnosis = self._diagnose_with_llm(context)
        
        # Create hypothesis
        hypothesis = self._create_hypothesis(observation, diagnosis, similar_incidents)
        
        # Store in memory
        self.working_memory.add_hypothesis(hypothesis)
        
        return hypothesis
    
    def _fast_reason_ticket(self, observation: Observation) -> Hypothesis:
        """
        Fast reasoning path for support tickets.
        Tickets already contain user-provided descriptions, so we can skip the LLM.
        """
        # Extract info from ticket events
        event = observation.events[0] if observation.events else None
        
        # Determine root cause from ticket metadata
        category = observation.pattern_key.split("_")[1] if "_" in observation.pattern_key else "general"
        
        root_cause_map = {
            "payment": "Payment Processing Issue",
            "checkout": "Checkout Flow Error", 
            "integration": "API Integration Issue",
            "performance": "Performance Degradation",
            "general": "General Issue Reported",
        }
        
        root_cause = root_cause_map.get(category, "Issue Reported by Merchant")
        
        # Build diagnosis from ticket description
        description = observation.description
        if event and event.message:
            # Extract description from ticket message
            description = event.message.replace("[TICKET] ", "")
        
        hypothesis = Hypothesis(
            hypothesis_id=str(uuid.uuid4()),
            observation_id=observation.observation_id,
            root_cause=root_cause,
            evidence=[
                f"Reported by merchant: {observation.affected_merchants[0] if observation.affected_merchants else 'Unknown'}",
                f"Category: {category}",
                f"Issue: {description[:200]}"
            ],
            confidence=0.90,  # Tickets are explicit reports, high confidence
            diagnosis=description,
            related_docs=[],
            historical_matches=[]
        )
        
        self.working_memory.add_hypothesis(hypothesis)
        return hypothesis
    
    def _build_reasoning_context(self, obs: Observation, similar: List[Dict]) -> Dict:
        """Build structured context for the reasoner"""
        
        # Sample events for evidence
        sample_events = []
        for i, event in enumerate(obs.events[:3], 1):
            sample_events.append(
                f"{i}. [{event.event_type}] {event.message}\n"
                f"   Merchant: {event.merchant_id}, Migration Stage: {event.migration_stage}, "
                f"   Severity: {event.severity}"
            )
        
        # Historical context
        historical_text = "None - this is a novel pattern"
        if similar:
            historical_items = []
            for inc in similar[:3]:
                historical_items.append(
                    f"- Pattern: {inc.get('pattern_key', 'Unknown')}\n"
                    f"  Resolution: {inc.get('resolution', 'Not recorded')}\n"
                    f"  Root Cause: {inc.get('root_cause', 'Unknown')}"
                )
            historical_text = "\n".join(historical_items)
        
        # Merchant context
        merchant_stages = {}
        for event in obs.events:
            if event.migration_stage:
                merchant_stages[event.merchant_id] = event.migration_stage
        
        merchant_context = "All in same migration stage" if len(set(merchant_stages.values())) == 1 else "Across multiple migration stages"
        if merchant_stages:
            merchant_context += f" (Stage {list(merchant_stages.values())[0]})" if len(set(merchant_stages.values())) == 1 else f" (Stages: {set(merchant_stages.values())})"
        
        return {
            "pattern_key": obs.pattern_key,
            "description": obs.description,
            "merchant_count": len(obs.affected_merchants),
            "merchant_list": ", ".join(obs.affected_merchants[:5]) + ("..." if len(obs.affected_merchants) > 5 else ""),
            "event_count": obs.event_count,
            "severity": obs.severity,
            "sample_events": "\n".join(sample_events),
            "historical_context": historical_text,
            "merchant_context": merchant_context
        }
    
    def _diagnose_with_llm(self, context: Dict) -> Dict:
        """Use LLM with detailed system prompt to diagnose"""
        
        # Format user prompt using template
        user_prompt = REASONER_DIAGNOSIS_TEMPLATE.format(**context)
        
        messages = [
            SystemMessage(content=REASONER_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            return self._parse_diagnosis(response.content)
        
        except Exception as e:
            print(f"   ⚠️  LLM diagnosis failed: {e}")
            # Fallback diagnosis
            return {
                "root_cause": "unknown",
                "confidence": 0.3,
                "evidence": [context["description"]],
                "diagnosis": f"Unable to diagnose. Pattern: {context['pattern_key']}",
                "docs": []
            }
    
    def _parse_diagnosis(self, content: str) -> Dict:
        """Parse structured diagnosis from LLM response"""
        result = {
            "root_cause": "unknown",
            "confidence": 0.5,
            "evidence": [],
            "diagnosis": content,
            "docs": []
        }
        
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            line_stripped = line.strip()
            
            if line_stripped.startswith("ROOT_CAUSE:"):
                result["root_cause"] = line_stripped.split("ROOT_CAUSE:")[1].strip().lower()
            
            elif line_stripped.startswith("CONFIDENCE:"):
                try:
                    conf_str = ''.join(filter(str.isdigit, line_stripped))
                    if conf_str:
                        result["confidence"] = int(conf_str) / 100
                except:
                    pass
            
            elif line_stripped == "EVIDENCE:":
                current_section = "evidence"
            
            elif line_stripped == "RECOMMENDED_DOCS:":
                current_section = "docs"
            
            elif line_stripped.startswith("DIAGNOSIS:"):
                current_section = "diagnosis"
                result["diagnosis"] = line_stripped.split("DIAGNOSIS:")[1].strip()
            
            elif current_section == "evidence" and line_stripped.startswith("-"):
                result["evidence"].append(line_stripped[1:].strip())
            
            elif current_section == "docs" and line_stripped.startswith("-"):
                result["docs"].append(line_stripped[1:].strip())
            
            elif current_section == "diagnosis" and line_stripped and not line_stripped.startswith(("ROOT", "CONFIDENCE", "EVIDENCE", "RECOMMENDED")):
                result["diagnosis"] += " " + line_stripped
        
        return result
    
    def _create_hypothesis(self, obs: Observation, diagnosis: Dict, similar: List[Dict]) -> Hypothesis:
        """Create hypothesis from diagnosis"""
        return Hypothesis(
            hypothesis_id=str(uuid.uuid4()),
            observation_id=obs.observation_id,
            root_cause=diagnosis["root_cause"],
            evidence=diagnosis.get("evidence", [obs.description]),
            confidence=diagnosis["confidence"],
            diagnosis=diagnosis["diagnosis"].strip(),
            related_docs=diagnosis.get("docs", []),
            historical_matches=[inc.get("pattern_key", "") for inc in similar]
        )