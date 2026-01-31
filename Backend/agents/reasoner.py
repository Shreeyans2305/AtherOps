# agents/reasoner.py - Diagnoses root causes using LLM
from models.schemas import Observation, Hypothesis
from memory.working_memory import WorkingMemory
from memory.long_memory import LongTermMemory
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
import uuid
from typing import List, Dict

class ReasonerAgent:
    """Analyzes observations and forms hypotheses"""
    
    def __init__(self, working_memory: WorkingMemory, long_memory: LongTermMemory):
        self.working_memory = working_memory
        self.long_memory = long_memory
        self.llm = ChatOllama(model="llama3.1:8b", temperature=0.2)
    
    def reason(self, observation: Observation) -> Hypothesis:
        """
        Analyze observation and produce hypothesis
        """
        # Get historical context
        similar_incidents = self.long_memory.find_similar_incidents(
            observation.pattern_key
        )
        
        # Build context for LLM
        context = self._build_reasoning_context(observation, similar_incidents)
        
        # Call LLM
        diagnosis = self._diagnose_with_llm(context)
        
        # Create hypothesis
        hypothesis = self._create_hypothesis(observation, diagnosis, similar_incidents)
        
        # Store in memory
        self.working_memory.add_hypothesis(hypothesis)
        
        return hypothesis
    
    def _build_reasoning_context(self, obs: Observation, similar: List[Dict]) -> str:
        """Build context string for LLM"""
        context = f"""OBSERVATION:
Pattern: {obs.pattern_key}
Description: {obs.description}
Affected merchants: {len(obs.affected_merchants)} ({', '.join(obs.affected_merchants[:5])})
Event count: {obs.event_count}
Severity: {obs.severity}

SAMPLE EVENTS:
"""
        for i, event in enumerate(obs.events[:3], 1):
            context += f"{i}. [{event.event_type}] {event.message}\n"
            context += f"   Merchant: {event.merchant_id}, Stage: {event.migration_stage}\n"
        
        if similar:
            context += "\n\nHISTORICAL SIMILAR INCIDENTS:\n"
            for i, incident in enumerate(similar, 1):
                context += f"{i}. {incident.get('pattern_key', 'Unknown')}\n"
                context += f"   Resolution: {incident.get('resolution', 'Not recorded')}\n"
        
        return context
    
    def _diagnose_with_llm(self, context: str) -> Dict:
        """Use LLM to analyze root cause"""
        prompt = f"""{context}

As a technical support AI analyzing a headless e-commerce migration, diagnose this issue.

Provide:
1. ROOT_CAUSE: (merchant config / platform bug / external service / API version mismatch / documentation gap)
2. CONFIDENCE: (0-100)%
3. EVIDENCE: List specific indicators from the data
4. RECOMMENDED_DOCS: What documentation might help
5. DIAGNOSIS: 2-3 sentence explanation

Format your response clearly with these headers."""

        messages = [
            SystemMessage(content="You are a technical diagnostic AI for e-commerce platforms."),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        return self._parse_llm_response(response.content)
    
    def _parse_llm_response(self, content: str) -> Dict:
        """Parse structured response from LLM"""
        result = {
            "root_cause": "unknown",
            "confidence": 0.5,
            "evidence": [],
            "diagnosis": content,
            "docs": []
        }
        
        lines = content.split('\n')
        for line in lines:
            if "ROOT_CAUSE:" in line:
                result["root_cause"] = line.split("ROOT_CAUSE:")[1].strip()
            elif "CONFIDENCE:" in line:
                try:
                    conf_str = ''.join(filter(str.isdigit, line))
                    result["confidence"] = int(conf_str) / 100
                except:
                    pass
            elif "EVIDENCE:" in line:
                # Collect evidence from following lines
                idx = lines.index(line)
                evidence = []
                for i in range(idx + 1, min(idx + 5, len(lines))):
                    if lines[i].strip().startswith('-') or lines[i].strip().startswith('•'):
                        evidence.append(lines[i].strip())
                result["evidence"] = evidence
        
        return result
    
    def _create_hypothesis(self, obs: Observation, diagnosis: Dict, similar: List[Dict]) -> Hypothesis:
        """Create hypothesis from diagnosis"""
        return Hypothesis(
            hypothesis_id=str(uuid.uuid4()),
            observation_id=obs.observation_id,
            root_cause=diagnosis["root_cause"],
            evidence=diagnosis.get("evidence", [obs.description]),
            confidence=diagnosis["confidence"],
            diagnosis=diagnosis["diagnosis"],
            related_docs=diagnosis.get("docs", []),
            historical_matches=[inc.get("pattern_key", "") for inc in similar]
        )