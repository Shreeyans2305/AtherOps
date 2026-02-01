# models/schemas.py - Unified event schema and data models
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Literal
from datetime import datetime
from enum import Enum

class EventType(str, Enum):
    API_ERROR = "api_error"
    CHECKOUT_FAILURE = "checkout_failure"
    WEBHOOK_FAILURE = "webhook_failure"
    PERFORMANCE = "performance"
    CONFIG_ERROR = "config_error"
    PAYMENT_FAILURE = "payment_failure"
    JAVASCRIPT_ERROR = "javascript_error"
    PROMISE_REJECTION = "promise_rejection"
    XHR_ERROR = "xhr_error"
    CHECKOUT_EVENT = "checkout_event"
    API_CALL = "api_call"
    TICKET = "ticket"  # Added to explicitely better tracking

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

# Unified Event Schema (all signals normalized to this)
class UnifiedEvent(BaseModel):
    event_id: str
    merchant_id: str
    timestamp: datetime
    event_type: EventType
    severity: Severity
    message: str
    metadata: Dict = Field(default_factory=dict)
    source: str  # "sdk", "webhook", "log", "api"
    migration_stage: Optional[int] = None
    
    class Config:
        use_enum_values = True

# Observer Output
class Observation(BaseModel):
    observation_id: str
    pattern_key: str
    description: str
    affected_merchants: List[str]
    event_count: int
    first_seen: datetime
    last_seen: datetime
    severity: Severity
    events: List[UnifiedEvent]
    confidence: float = 0.0

# Reasoner Output
class Hypothesis(BaseModel):
    hypothesis_id: str
    observation_id: str
    root_cause: str
    evidence: List[str]
    confidence: float  # 0-1
    diagnosis: str
    related_docs: List[str] = Field(default_factory=list)
    historical_matches: List[str] = Field(default_factory=list)

# Decision Output
class ActionPlan(BaseModel):
    plan_id: str
    hypothesis_id: str
    action_type: Literal[
        "support_guidance",
        "engineering_escalation", 
        "merchant_communication",
        "temporary_mitigation",
        "documentation_update"
    ]
    priority: Literal["low", "medium", "high", "critical"]
    risk_level: Literal["low", "medium", "high"]
    requires_approval: bool
    action_details: Dict
    estimated_impact: str

# Executor Output
class ExecutionResult(BaseModel):
    execution_id: str
    plan_id: str
    status: Literal["success", "failed", "pending_approval", "skipped"]
    executed_at: Optional[datetime] = None
    result_details: Dict = Field(default_factory=dict)
    error: Optional[str] = None