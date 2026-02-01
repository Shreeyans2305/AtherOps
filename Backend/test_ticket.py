#!/usr/bin/env python3
"""
Test script for the ticket endpoint with email notification.
Run this after starting the server with: uvicorn main:app --host 0.0.0.0 --port 8000
"""
import requests
import json

# Test critical ticket
ticket_data = {
    "title": "CRITICAL: Payment Gateway Complete Failure",
    "description": "All payment transactions are failing with error code 503. Multiple merchants affected. Revenue loss is occurring. Immediate attention required.",
    "merchant_id": "store_demo_123",
    "merchant_email": "shreeyans.vichare@gmail.com",
    "priority": "critical",
    "category": "payment",
    "tags": ["critical", "payment", "urgent"]
}

print("=" * 60)
print("Testing Critical Ticket Submission")
print("=" * 60)

try:
    response = requests.post(
        "http://localhost:8000/api/tickets",
        json=ticket_data,
        timeout=30
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"\nResponse:")
    print(json.dumps(response.json(), indent=2))
    
except requests.exceptions.ConnectionError:
    print("\n❌ Could not connect to server. Make sure it's running:")
    print("   cd Backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000")
except Exception as e:
    print(f"\n❌ Error: {e}")
