# memory/long_memory.py - Use timezone-aware datetimes
from typing import List, Dict
from datetime import datetime, timezone
import json

class LongTermMemory:
    """Stores historical incidents for pattern matching"""
    
    def __init__(self, storage_path="./incidents_history.json"):
        self.storage_path = storage_path
        self.incidents: List[Dict] = self._load_history()
    
    def _load_history(self) -> List[Dict]:
        """Load from disk"""
        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def _save_history(self):
        """Persist to disk"""
        with open(self.storage_path, 'w') as f:
            json.dump(self.incidents, f, indent=2, default=str)
    
    def store_incident(self, incident: Dict):
        """Store resolved incident for future reference"""
        incident["stored_at"] = datetime.now(timezone.utc).isoformat()
        self.incidents.append(incident)
        self._save_history()
    
    def find_similar_incidents(self, pattern_key: str, limit: int = 5) -> List[Dict]:
        """Find historical incidents with similar patterns"""
        # Simple keyword matching (in production, use embeddings)
        matches = []
        for incident in self.incidents:
            if pattern_key.lower() in incident.get("pattern_key", "").lower():
                matches.append(incident)
        return matches[-limit:]
    
    def get_resolution_strategies(self, pattern_key: str) -> List[str]:
        """Get what worked before for similar issues"""
        similar = self.find_similar_incidents(pattern_key)
        strategies = []
        for incident in similar:
            if "resolution" in incident:
                strategies.append(incident["resolution"])
        return strategies