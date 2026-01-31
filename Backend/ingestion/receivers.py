# ingestion/receivers.py - Receive events from various sources
from fastapi import WebSocket
from models.schemas import UnifiedEvent
from ingestion.normalizer import EventNormalizer
import json

class EventReceiver:
    def __init__(self, event_queue):
        self.normalizer = EventNormalizer()
        self.event_queue = event_queue  # Async queue
    
    async def receive_sdk_event(self, websocket: WebSocket):
        """Receive from SDK WebSocket"""
        data = await websocket.receive_text()
        raw_event = json.loads(data)
        
        # Normalize to unified schema
        event = self.normalizer.normalize_sdk_event(raw_event)
        
        # Push to processing queue
        await self.event_queue.put(event)
        
        return event
    
    async def receive_webhook_event(self, payload: dict):
        """Receive webhook failures"""
        event = self.normalizer.normalize_webhook_failure(payload)
        await self.event_queue.put(event)
        return event
    
    async def receive_log_event(self, log_entry: dict):
        """Receive from log streaming"""
        event = self.normalizer.normalize_log_entry(log_entry)
        await self.event_queue.put(event)
        return event