# fake_data.py - Simulates merchant problems
MOCK_SIGNALS = [
    {
        "id": 1,
        "merchant_id": "store_123",
        "type": "api_error",
        "message": "Payment gateway timeout - error code 503",
        "timestamp": "2026-01-31T10:30:00",
        "severity": "high"
    },
    {
        "id": 2,
        "merchant_id": "store_456",
        "type": "checkout_failure",
        "message": "Webhook not receiving order confirmations",
        "timestamp": "2026-01-31T10:35:00",
        "severity": "medium"
    },
    {
        "id": 3,
        "merchant_id": "store_123",
        "type": "api_error",
        "message": "Payment gateway timeout - error code 503",
        "timestamp": "2026-01-31T10:40:00",
        "severity": "high"
    },
    {
        "id": 4,
        "merchant_id": "store_789",
        "type": "api_error",
        "message": "Payment gateway timeout - error code 503",
        "timestamp": "2026-01-31T10:42:00",
        "severity": "high"
    },
    {
        "id": 5,
        "merchant_id": "store_999",
        "type": "config_error",
        "message": "Missing API key in headless configuration",
        "timestamp": "2026-01-31T11:00:00",
        "severity": "medium"
    },
]