# agents/observer_hybrid.py - Updated with system prompt
from models.schemas import UnifiedEvent, Observation, Severity
from memory.working_memory import WorkingMemory
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from agents.prompts.observer_prompts import (
    OBSERVER_SYSTEM_PROMPT,
    OBSERVER_CLASSIFICATION_TEMPLATE
)
from collections import defaultdict
from datetime import datetime, timezone
from typing import List, Dict, Tuple
import uuid
import json

class HybridObserverAgent:
    """
    Combines fast rule-based clustering with LLM validation
    Now with detailed system prompts for higher accuracy
    """
    
    def __init__(self, working_memory: WorkingMemory):
        self.memory = working_memory
        self.llm = ChatOllama(
            model="llama3.1:8b",
            temperature=0.1,  # Low for consistency
            num_predict=512   # Limit tokens for faster response
        )
        
        # Known patterns from heuristics
        self.known_patterns = {
            "503": "service_unavailable",
            "timeout": "timeout_error",
            "webhook": "webhook_failure",
            "payment": "payment_issue",
            "auth": "authentication_error",
            "404": "not_found",
            "500": "internal_error",
        }
    
    def observe(self) -> List[Observation]:
        """Hybrid observation: heuristics + LLM when needed"""
        recent_events = self.memory.get_recent_events(minutes=10)
        
        if len(recent_events) < 2:
            return []
        
        print(f"   Analyzing {len(recent_events)} events (hybrid approach)...")
        
        # Step 1: Fast heuristic clustering
        heuristic_clusters, uncertain_events = self._fast_cluster(recent_events)
        print(f"   🚀 Fast clustering: {len(heuristic_clusters)} patterns, {len(uncertain_events)} uncertain")
        
        # Step 2: Use LLM only for uncertain events
        if uncertain_events:
            print(f"   🧠 Using LLM for {len(uncertain_events)} uncertain events...")
            llm_clusters = self._llm_cluster(uncertain_events)
            # Merge
            for pattern, events in llm_clusters.items():
                if pattern in heuristic_clusters:
                    heuristic_clusters[pattern].extend(events)
                else:
                    heuristic_clusters[pattern] = events
        
        # Step 3: Create observations
        observations = []
        for pattern_key, events in heuristic_clusters.items():
            if len(events) >= 2:
                obs = self._create_observation(pattern_key, events)
                observations.append(obs)
                self.memory.add_observation(obs)
                print(f"   ✅ Pattern: '{pattern_key}' ({len(events)} events)")
        
        return observations
    
    def _fast_cluster(self, events: List[UnifiedEvent]) -> Tuple[Dict, List]:
        """Fast heuristic-based clustering"""
        clusters = defaultdict(list)
        uncertain = []
        
        for event in events:
            pattern = self._apply_heuristics(event)
            
            if pattern:
                clusters[pattern].append(event)
            else:
                uncertain.append(event)
        
        return dict(clusters), uncertain
    
    def _apply_heuristics(self, event: UnifiedEvent) -> str:
        """Apply fast pattern matching rules"""
        message = event.message.lower()
        event_type = event.event_type
        
        # Rule 1: HTTP error codes
        if "503" in message or "service unavailable" in message:
            return "service_unavailable"
        if "500" in message or "internal server error" in message:
            return "internal_server_error"
        if "404" in message or "not found" in message:
            return "resource_not_found"
        if "401" in message or "403" in message or "unauthorized" in message:
            return "authentication_error"
        if "429" in message or "rate limit" in message:
            return "rate_limit_exceeded"
        
        # Rule 2: Timeout patterns
        if "timeout" in message or "timed out" in message:
            if "payment" in message or "gateway" in message:
                return "payment_gateway_timeout"
            elif "webhook" in message:
                return "webhook_timeout"
            else:
                return "api_timeout"
        
        # Rule 3: Event type patterns
        if event_type == "webhook_failure":
            return "webhook_delivery_failure"
        if event_type == "payment_failure":
            if "declined" in message or "insufficient" in message:
                return "payment_declined"
            else:
                return "payment_processing_error"
        
        # Rule 4: Migration-specific
        if "missing" in message and "field" in message:
            return "missing_required_field"
        if "api version" in message or "deprecated" in message:
            return "api_version_mismatch"
        
        # Rule 5: Exact message match
        if len(message) > 20:
            return f"exact_match:{message[:50]}"
        
        # Uncertain - needs LLM
        return None
    
    def _llm_cluster(self, events: List[UnifiedEvent]) -> Dict[str, List[UnifiedEvent]]:
        """Use LLM with detailed system prompt to cluster uncertain events"""
        if not events:
            return {}
        
        # Build event summaries
        summaries = []
        for i, event in enumerate(events):
            summaries.append({
                "index": i,
                "type": event.event_type,
                "message": event.message[:200],
                "merchant": event.merchant_id,
                "migration_stage": event.migration_stage,
                "severity": event.severity
            })
        
        # Calculate time window
        timestamps = [e.timestamp for e in events]
        time_window = f"{min(timestamps).strftime('%H:%M:%S')} - {max(timestamps).strftime('%H:%M:%S')}"
        
        merchants = set(e.merchant_id for e in events)
        
        # Use template with context
        user_prompt = OBSERVER_CLASSIFICATION_TEMPLATE.format(
            events_json=json.dumps(summaries, indent=2),
            event_count=len(events),
            time_window=time_window,
            merchant_count=len(merchants)
        )
        
        try:
            messages = [
                SystemMessage(content=OBSERVER_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            text = response.content
            
            # Extract JSON
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            result = json.loads(text.strip())
            
            # Group events by pattern
            clusters = defaultdict(list)
            for classification in result.get("classifications", []):
                idx = classification["index"]
                pattern = classification["pattern"]
                if idx < len(events):
                    clusters[pattern].append(events[idx])
            
            return dict(clusters)
            
        except Exception as e:
            print(f"   ⚠️  LLM clustering failed: {e}")
            # Fallback
            return {f"unknown_{i}": [event] for i, event in enumerate(events)}
    
    def _create_observation(self, pattern_key: str, events: List[UnifiedEvent]) -> Observation:
        """Create observation from clustered events"""
        merchants = list(set([e.merchant_id for e in events]))
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        max_severity = max(events, key=lambda e: severity_order.get(e.severity, 0))
        
        # Generate description
        merchant_count = len(merchants)
        pattern_readable = pattern_key.replace("_", " ").title()
        
        stages = [e.migration_stage for e in events if e.migration_stage]
        stage_info = f" (migration stage {stages[0]})" if stages and len(set(stages)) == 1 else ""
        
        description = (
            f"{pattern_readable}: {merchant_count} merchant(s) affected{stage_info}. "
            f"Total occurrences: {len(events)}. "
            f"Sample: {events[0].message[:100]}"
        )
        
        timestamps = [e.timestamp for e in events]
        
        return Observation(
            observation_id=str(uuid.uuid4()),
            pattern_key=pattern_key,
            description=description,
            affected_merchants=merchants,
            event_count=len(events),
            first_seen=min(timestamps),
            last_seen=max(timestamps),
            severity=max_severity.severity,
            events=events,
            confidence=self._calculate_confidence(events)
        )
    
    def _calculate_confidence(self, events: List[UnifiedEvent]) -> float:
        """Calculate pattern confidence"""
        event_score = min(len(events) / 10, 0.4)
        
        stages = [e.migration_stage for e in events if e.migration_stage]
        stage_score = 0.3 if stages and len(set(stages)) == 1 else 0.1
        
        merchants = set(e.merchant_id for e in events)
        merchant_score = 0.2 if len(merchants) >= 3 else 0.1
        
        time_range = (max(e.timestamp for e in events) - min(e.timestamp for e in events)).total_seconds()
        time_score = 0.2 if time_range < 300 else 0.05
        
        return min(event_score + stage_score + merchant_score + time_score, 1.0)