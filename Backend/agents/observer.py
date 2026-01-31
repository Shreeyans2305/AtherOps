# agents/observer.py - Use timezone-aware datetimes
from models.schemas import UnifiedEvent, Observation, Severity
from memory.working_memory import WorkingMemory
from collections import defaultdict
from datetime import datetime, timezone
import uuid
from typing import List, Dict

class ObserverAgent:
    """Monitors signals and detects patterns"""
    
    def __init__(self, working_memory: WorkingMemory):
        self.memory = working_memory
    
    def observe(self) -> List[Observation]:
        """
        Analyze recent events and produce observations
        Returns: List of detected patterns
        """
        recent_events = self.memory.get_recent_events(minutes=10)
        
        if len(recent_events) < 2:
            return []
        
        # Group events by pattern
        patterns = self._cluster_events(recent_events)
        
        # Convert to observations
        observations = []
        for pattern_key, events in patterns.items():
            if len(events) >= 2:  # Threshold for "pattern"
                obs = self._create_observation(pattern_key, events)
                observations.append(obs)
                self.memory.add_observation(obs)
        
        return observations
    
    def _cluster_events(self, events: List[UnifiedEvent]) -> Dict[str, List[UnifiedEvent]]:
        """Cluster similar events"""
        clusters = defaultdict(list)
        
        for event in events:
            # Create pattern key from event characteristics
            pattern_key = f"{event.event_type}:{event.message[:50]}"
            clusters[pattern_key].append(event)
        
        return clusters
    
    def _create_observation(self, pattern_key: str, events: List[UnifiedEvent]) -> Observation:
        """Create structured observation from events"""
        merchants = list(set([e.merchant_id for e in events]))
        
        # Determine severity (use highest from events)
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        max_severity = max(events, key=lambda e: severity_order.get(e.severity, 0))
        
        description = self._generate_description(pattern_key, events)
        
        # Ensure all timestamps are timezone-aware
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
    
    def _generate_description(self, pattern_key: str, events: List[UnifiedEvent]) -> str:
        """Generate human-readable description"""
        event_type = events[0].event_type
        merchant_count = len(set(e.merchant_id for e in events))
        
        # Check for migration stage correlation
        stages = [e.migration_stage for e in events if e.migration_stage]
        stage_info = ""
        if stages and len(set(stages)) == 1:
            stage_info = f" (all in migration stage {stages[0]})"
        
        return (
            f"Spike in {event_type} affecting {merchant_count} merchant(s){stage_info}. "
            f"Pattern: {events[0].message[:100]}"
        )
    
    def _calculate_confidence(self, events: List[UnifiedEvent]) -> float:
        """Calculate confidence score based on event characteristics"""
        # More events = higher confidence
        event_score = min(len(events) / 10, 0.5)
        
        # Same migration stage = higher confidence
        stages = [e.migration_stage for e in events if e.migration_stage]
        stage_score = 0.3 if stages and len(set(stages)) == 1 else 0
        
        # Time clustering = higher confidence
        time_range = (max(e.timestamp for e in events) - min(e.timestamp for e in events)).total_seconds()
        time_score = 0.2 if time_range < 300 else 0.1  # Within 5 minutes
        
        return min(event_score + stage_score + time_score, 1.0)