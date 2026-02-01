"""
Helper functions for syncing Clerk users and organizations with local database.
"""
from sqlalchemy.orm import Session
from db_models import User, Organization
from datetime import datetime


def sync_user_to_db(db: Session, user_data: dict) -> User:
    """
    Sync a Clerk user to the local database.
    Creates or updates the user record.
    """
    user_id = user_data.get("user_id")
    
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    
    if user:
        # Update existing user
        user.email = user_data.get("email", user.email)
        user.organization_id = user_data.get("org_id")
        user.last_sign_in = datetime.utcnow()
        user.updated_at = datetime.utcnow()
    else:
        # Create new user
        user = User(
            id=user_id,
            email=user_data.get("email"),
            organization_id=user_data.get("org_id"),
            last_sign_in=datetime.utcnow()
        )
        db.add(user)
    
    db.commit()
    db.refresh(user)
    return user


def sync_organization_to_db(db: Session, org_id: str, org_name: str = None) -> Organization:
    """
    Sync a Clerk organization to the local database.
    Creates or updates the organization record.
    """
    # Check if organization exists
    org = db.query(Organization).filter(Organization.id == org_id).first()
    
    if org:
        # Update existing organization
        if org_name:
            org.name = org_name
            org.updated_at = datetime.utcnow()
    else:
        # Create new organization
        org = Organization(
            id=org_id,
            name=org_name or f"Organization {org_id[:8]}",
            slug=org_id
        )
        db.add(org)
    
    db.commit()
    db.refresh(org)
    return org


def get_or_create_user_and_org(db: Session, user_data: dict) -> tuple[User, Organization]:
    """
    Get or create both user and organization from Clerk data.
    Returns (user, organization) tuple.
    """
    org_id = user_data.get("org_id")
    
    # Sync organization first if present
    org = None
    if org_id:
        org = sync_organization_to_db(db, org_id)
    
    # Sync user
    user = sync_user_to_db(db, user_data)
    
    return user, org
