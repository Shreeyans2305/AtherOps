# ingestion/normalizer.py - Use timezone-aware datetimes
from models.schemas import UnifiedEvent, EventType, Severity
from datetime import datetime, timezone
import uuid

class EventNormalizer:
    """Converts raw signals into unified event schema"""
    
    def normalize_sdk_event(self, raw_event: dict) -> UnifiedEvent:
        """Normalize SDK telemetry"""
        # Parse timestamp and ensure it's timezone-aware
        timestamp_str = raw_event.get("timestamp")
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            # If naive, add UTC timezone
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
        except:
            # Fallback to current time
            timestamp = datetime.now(timezone.utc)
        
        # Get event type, fallback to API_ERROR if unknown
        event_type_raw = raw_event.get("type", "api_error")
        try:
            event_type = EventType(event_type_raw)
        except ValueError:
            print(f"⚠️  Unknown event type '{event_type_raw}', using api_error")
            event_type = EventType.API_ERROR
        
        return UnifiedEvent(
            event_id=str(uuid.uuid4()),
            merchant_id=raw_event.get("merchant_id"),
            timestamp=timestamp,
            event_type=event_type,
            severity=Severity(raw_event.get("severity", "medium")),
            message=raw_event.get("message", ""),
            metadata={
                "url": raw_event.get("url"),
                "status": raw_event.get("status"),
                "duration": raw_event.get("duration"),
                "stack": raw_event.get("stack"),
            },
            source="sdk",
            migration_stage=raw_event.get("migration_stage")
        )
    
    def normalize_webhook_failure(self, raw_event: dict) -> UnifiedEvent:
        """Normalize webhook delivery failures"""
        return UnifiedEvent(
            event_id=str(uuid.uuid4()),
            merchant_id=raw_event.get("merchant_id"),
            timestamp=datetime.now(timezone.utc),  # Changed to timezone-aware
            event_type=EventType.WEBHOOK_FAILURE,
            severity=Severity.HIGH,
            message=f"Webhook delivery failed: {raw_event.get('webhook_type')}",
            metadata={
                "webhook_type": raw_event.get("webhook_type"),
                "retry_count": raw_event.get("retry_count"),
                "error_code": raw_event.get("error_code"),
            },
            source="webhook",
            migration_stage=raw_event.get("migration_stage")
        )
    
    def normalize_log_entry(self, raw_log: dict) -> UnifiedEvent:
        """Normalize application logs"""
        severity_map = {
            "ERROR": Severity.HIGH,
            "WARN": Severity.MEDIUM,
            "INFO": Severity.LOW,
        }
        
        timestamp_str = raw_log.get("timestamp")
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
        except:
            timestamp = datetime.now(timezone.utc)
        
        return UnifiedEvent(
            event_id=str(uuid.uuid4()),
            merchant_id=raw_log.get("merchant_id", "platform"),
            timestamp=timestamp,
            event_type=EventType.API_ERROR,
            severity=severity_map.get(raw_log.get("level"), Severity.MEDIUM),
            message=raw_log.get("message"),
            metadata={
                "logger": raw_log.get("logger"),
                "trace_id": raw_log.get("trace_id"),
            },
            source="log"
        )