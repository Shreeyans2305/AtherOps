# services/ticket_service.py - Scalable ticket processing system
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Literal
from datetime import datetime, timezone
from enum import Enum
import uuid


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketSource(str, Enum):
    FRONTEND = "frontend"
    JIRA = "jira"
    ZENDESK = "zendesk"
    SLACK = "slack"
    EMAIL = "email"
    API = "api"


class Ticket(BaseModel):
    """Unified ticket model - works with any ticketing system"""
    ticket_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    external_id: Optional[str] = None  # e.g., Jira ticket ID (PROJ-123)
    source: TicketSource = TicketSource.FRONTEND
    
    # Core fields
    title: str
    description: str
    merchant_id: str
    merchant_email: Optional[str] = None
    
    # Classification
    priority: TicketPriority = TicketPriority.MEDIUM
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    # Status tracking
    status: TicketStatus = TicketStatus.OPEN
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    
    # Additional context
    metadata: Dict = Field(default_factory=dict)
    attachments: List[str] = Field(default_factory=list)
    
    # Assignee info
    assigned_to: Optional[str] = None
    reporter_email: Optional[str] = None
    
    class Config:
        use_enum_values = True


class TicketProvider(ABC):
    """
    Abstract base class for ticket providers.
    Implement this to integrate with Jira, Zendesk, etc.
    """
    
    @abstractmethod
    async def fetch_ticket(self, external_id: str) -> Optional[Ticket]:
        """Fetch a ticket from the external system"""
        pass
    
    @abstractmethod
    async def sync_tickets(self, since: Optional[datetime] = None) -> List[Ticket]:
        """Sync tickets from the external system"""
        pass
    
    @abstractmethod
    async def update_ticket_status(self, external_id: str, status: TicketStatus) -> bool:
        """Update ticket status in the external system"""
        pass
    
    @abstractmethod
    async def add_comment(self, external_id: str, comment: str) -> bool:
        """Add a comment to the ticket in the external system"""
        pass


class JiraTicketProvider(TicketProvider):
    """
    Jira ticket provider - implement when ready to integrate with Jira.
    This is a placeholder for future implementation.
    """
    
    def __init__(self, base_url: str, api_token: str, project_key: str):
        self.base_url = base_url
        self.api_token = api_token
        self.project_key = project_key
    
    async def fetch_ticket(self, external_id: str) -> Optional[Ticket]:
        """
        Fetch a Jira ticket and convert to unified Ticket format.
        
        TODO: Implement with Jira API
        Example:
            response = requests.get(
                f"{self.base_url}/rest/api/3/issue/{external_id}",
                headers={"Authorization": f"Bearer {self.api_token}"}
            )
            data = response.json()
            return self._convert_jira_to_ticket(data)
        """
        raise NotImplementedError("Jira integration not yet implemented")
    
    async def sync_tickets(self, since: Optional[datetime] = None) -> List[Ticket]:
        """Sync tickets from Jira using JQL"""
        raise NotImplementedError("Jira integration not yet implemented")
    
    async def update_ticket_status(self, external_id: str, status: TicketStatus) -> bool:
        """Update Jira ticket status"""
        raise NotImplementedError("Jira integration not yet implemented")
    
    async def add_comment(self, external_id: str, comment: str) -> bool:
        """Add comment to Jira ticket"""
        raise NotImplementedError("Jira integration not yet implemented")
    
    def _convert_jira_to_ticket(self, jira_data: dict) -> Ticket:
        """Convert Jira issue format to unified Ticket"""
        # Map Jira priority to our priority
        priority_map = {
            "Highest": TicketPriority.CRITICAL,
            "High": TicketPriority.HIGH,
            "Medium": TicketPriority.MEDIUM,
            "Low": TicketPriority.LOW,
            "Lowest": TicketPriority.LOW,
        }
        
        fields = jira_data.get("fields", {})
        
        return Ticket(
            ticket_id=str(uuid.uuid4()),
            external_id=jira_data.get("key"),
            source=TicketSource.JIRA,
            title=fields.get("summary", ""),
            description=fields.get("description", ""),
            merchant_id=fields.get("customfield_merchant_id", "unknown"),
            priority=priority_map.get(
                fields.get("priority", {}).get("name", "Medium"),
                TicketPriority.MEDIUM
            ),
            status=TicketStatus.OPEN,
            metadata={"jira_data": jira_data}
        )


class FrontendTicketProvider(TicketProvider):
    """
    Provider for tickets submitted directly from the frontend.
    These are stored locally and processed immediately.
    """
    
    def __init__(self):
        self.tickets: Dict[str, Ticket] = {}
    
    def create_ticket(self, ticket: Ticket) -> Ticket:
        """Create a new ticket from frontend submission"""
        ticket.source = TicketSource.FRONTEND
        ticket.created_at = datetime.now(timezone.utc)
        self.tickets[ticket.ticket_id] = ticket
        return ticket
    
    async def fetch_ticket(self, external_id: str) -> Optional[Ticket]:
        """Fetch a ticket by ID"""
        return self.tickets.get(external_id)
    
    async def sync_tickets(self, since: Optional[datetime] = None) -> List[Ticket]:
        """Get all tickets (optionally since a certain date)"""
        tickets = list(self.tickets.values())
        if since:
            tickets = [t for t in tickets if t.created_at >= since]
        return tickets
    
    async def update_ticket_status(self, external_id: str, status: TicketStatus) -> bool:
        """Update ticket status"""
        if external_id in self.tickets:
            self.tickets[external_id].status = status
            self.tickets[external_id].updated_at = datetime.now(timezone.utc)
            return True
        return False
    
    async def add_comment(self, external_id: str, comment: str) -> bool:
        """Add a comment to the ticket metadata"""
        if external_id in self.tickets:
            ticket = self.tickets[external_id]
            if "comments" not in ticket.metadata:
                ticket.metadata["comments"] = []
            ticket.metadata["comments"].append({
                "text": comment,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            return True
        return False


class TicketService:
    """
    Main ticket service - handles ticket processing and routing.
    Supports multiple providers for scalability.
    """
    
    def __init__(self):
        self.providers: Dict[TicketSource, TicketProvider] = {}
        self.frontend_provider = FrontendTicketProvider()
        self.providers[TicketSource.FRONTEND] = self.frontend_provider
        
        # Callbacks for ticket processing
        self._on_ticket_created_callbacks = []
    
    def register_provider(self, source: TicketSource, provider: TicketProvider):
        """Register a ticket provider (e.g., Jira, Zendesk)"""
        self.providers[source] = provider
        print(f"✅ Registered ticket provider: {source}")
    
    def on_ticket_created(self, callback):
        """Register a callback for when tickets are created"""
        self._on_ticket_created_callbacks.append(callback)
    
    async def create_ticket(self, ticket_data: dict) -> Ticket:
        """
        Create a ticket from raw data.
        This is the main entry point for ticket creation.
        """
        ticket = Ticket(
            title=ticket_data.get("title", "Untitled Issue"),
            description=ticket_data.get("description", ""),
            merchant_id=ticket_data.get("merchant_id", "unknown"),
            merchant_email=ticket_data.get("merchant_email"),
            priority=TicketPriority(ticket_data.get("priority", "medium")),
            category=ticket_data.get("category"),
            tags=ticket_data.get("tags", []),
            metadata=ticket_data.get("metadata", {}),
            reporter_email=ticket_data.get("reporter_email"),
        )
        
        # Store in frontend provider
        self.frontend_provider.create_ticket(ticket)
        
        print(f"🎫 New ticket created: {ticket.ticket_id}")
        print(f"   Title: {ticket.title}")
        print(f"   Priority: {ticket.priority}")
        print(f"   Merchant: {ticket.merchant_id}")
        
        # Trigger callbacks
        for callback in self._on_ticket_created_callbacks:
            await callback(ticket)
        
        return ticket
    
    async def get_ticket(self, ticket_id: str, source: TicketSource = TicketSource.FRONTEND) -> Optional[Ticket]:
        """Get a ticket by ID from the appropriate provider"""
        provider = self.providers.get(source)
        if provider:
            return await provider.fetch_ticket(ticket_id)
        return None
    
    async def get_all_tickets(self, source: Optional[TicketSource] = None) -> List[Ticket]:
        """Get all tickets, optionally filtered by source"""
        all_tickets = []
        
        if source:
            provider = self.providers.get(source)
            if provider:
                all_tickets = await provider.sync_tickets()
        else:
            for provider in self.providers.values():
                tickets = await provider.sync_tickets()
                all_tickets.extend(tickets)
        
        return all_tickets
    
    async def update_status(self, ticket_id: str, status: TicketStatus, 
                           source: TicketSource = TicketSource.FRONTEND) -> bool:
        """Update ticket status"""
        provider = self.providers.get(source)
        if provider:
            return await provider.update_ticket_status(ticket_id, status)
        return False


# Global ticket service instance
ticket_service = TicketService()
