# memory/working_memory.py - Use timezone-aware datetimes
from collections import defaultdict, deque
from models.schemas import UnifiedEvent, Observation, Hypothesis, ActionPlan
from typing import Dict, List
from datetime import datetime, timedelta, timezone

class WorkingMemory:
    """Stores current incident state (last 1 hour)"""
    
    def __init__(self, retention_minutes=60):
        self.events: deque = deque(maxlen=1000)
        self.observations: Dict[str, Observation] = {}
        self.hypotheses: Dict[str, Hypothesis] = {}
        self.action_plans: Dict[str, ActionPlan] = {}
        self.processed_event_ids: set = set()  # Track which events have been processed into observations
        self.retention_minutes = retention_minutes
    
    def add_event(self, event: UnifiedEvent):
        """Add event and cleanup old ones"""
        self.events.append(event)
        self._cleanup_old_events()
    
    def _cleanup_old_events(self):
        """Remove events older than retention period"""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=self.retention_minutes)
        while self.events and self.events[0].timestamp < cutoff:
            self.events.popleft()
    
    def get_recent_events(self, minutes: int = 10) -> List[UnifiedEvent]:
        """Get unprocessed events from last N minutes"""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        return [e for e in self.events if e.timestamp > cutoff and e.event_id not in self.processed_event_ids]
    
    def add_observation(self, obs: Observation):
        self.observations[obs.observation_id] = obs
        # Mark all events in this observation as processed
        for event in obs.events:
            self.processed_event_ids.add(event.event_id)
    
    def add_hypothesis(self, hyp: Hypothesis):
        self.hypotheses[hyp.hypothesis_id] = hyp
    
    def add_action_plan(self, plan: ActionPlan):
        self.action_plans[plan.plan_id] = plan
    
    def get_observation(self, obs_id: str) -> Observation:
        return self.observations.get(obs_id)
    
    def get_active_observations(self) -> List[Observation]:
        """Get observations from last 30 minutes"""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
        return [
            obs for obs in self.observations.values()
            if obs.last_seen > cutoff
        ]