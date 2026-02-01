#!/usr/bin/env python3
"""
Test script for merchant communication (non-critical) ticket.
This tests that even non-critical merchant emails are actually sent.
"""
import requests
import json

# Test medium priority ticket (merchant config issue)
ticket_data = {
    "title": "API Key Configuration Error",
    "description": "The API key appears to be incorrectly configured. Please check your settings.",
    "merchant_id": "store_demo_123",
    "merchant_email": "shreeyans.vichare@gmail.com",
    "priority": "medium",
    "category": "integration",
    "tags": ["config", "api-key"]
}

print("=" * 60)
print("Testing Medium Priority Merchant Communication")
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
