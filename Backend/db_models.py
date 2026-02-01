"""
Database models for AtherOps with organization-based multi-tenancy.
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Organization(Base):
    """
    Organization model - synced with Clerk organizations.
    """
    __tablename__ = "organizations"
    
    id = Column(String, primary_key=True)  # Clerk organization ID
    name = Column(String, nullable=False)
    slug = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="organization")
    events = relationship("Event", back_populates="organization")


class User(Base):
    """
    User model - synced with Clerk users.
    """
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)  # Clerk user ID
    email = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    organization_id = Column(String, ForeignKey("organizations.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_sign_in = Column(DateTime)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")


class Event(Base):
    """
    Event model - stores all incoming events with organization isolation.
    """
    __tablename__ = "events"
    
    id = Column(String, primary_key=True)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    merchant_id = Column(String, index=True)
    event_type = Column(String, nullable=False, index=True)
    severity = Column(String)
    message = Column(Text)
    event_metadata = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="events")


class Observation(Base):
    """
    Observation model - patterns detected by the Observer agent.
    """
    __tablename__ = "observations"
    
    id = Column(String, primary_key=True)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    observation_type = Column(String)
    pattern = Column(String)
    confidence = Column(Integer)  # 0-100
    event_count = Column(Integer)
    observation_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Hypothesis(Base):
    """
    Hypothesis model - root cause analysis by the Reasoner agent.
    """
    __tablename__ = "hypotheses"
    
    id = Column(String, primary_key=True)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    observation_id = Column(String, ForeignKey("observations.id"))
    hypothesis = Column(Text)
    confidence = Column(Integer)  # 0-100
    evidence = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class ActionPlan(Base):
    """
    Action Plan model - remediation plans by the Decision agent.
    """
    __tablename__ = "action_plans"
    
    id = Column(String, primary_key=True)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    hypothesis_id = Column(String, ForeignKey("hypotheses.id"))
    action_type = Column(String)
    description = Column(Text)
    risk_level = Column(String)  # low, medium, high
    confidence = Column(Integer)  # 0-100
    status = Column(String, default="pending")  # pending, executing, completed, failed
    result = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    executed_at = Column(DateTime)


class Ticket(Base):
    """
    Ticket model - support tickets with organization isolation.
    """
    __tablename__ = "tickets"
    
    id = Column(String, primary_key=True)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    merchant_id = Column(String)
    title = Column(String, nullable=False)
    description = Column(Text)
    priority = Column(String, default="medium")  # low, medium, high, critical
    status = Column(String, default="open")  # open, in_progress, resolved, closed
    category = Column(String)
    tags = Column(JSON)
    reporter_email = Column(String)
    ticket_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime)
