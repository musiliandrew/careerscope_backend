import requests
import json
import base64

def test_webhook():
    url = "http://127.0.0.1:8000/api/applications/webhooks/pubsub/"
    
    # 1. Create the structured payload that parser.py would generate
    payload = {
        "user_id": 1, # Make sure this user exists in your local DB
        "company_name": "Google",
        "role_title": "Senior AI Engineer",
        "missing_skills": ["Kubernetes", "gRPC"],
        "event_type": "ApplicationRejectedPayload"
    }
    
    # 2. Encode to base64 to simulate GCP Pub/Sub structure
    payload_str = json.dumps(payload)
    data_encoded = base64.b64encode(payload_str.encode("utf-8")).decode("utf-8")
    
    # 3. Create the Pub/Sub Push format
    pubsub_msg = {
        "message": {
            "attributes": {
                "event_type": "ApplicationRejectedPayload"
            },
            "data": data_encoded,
            "messageId": "123456789"
        },
        "subscription": "projects/careerscope-local/subscriptions/careerscope.events.sub"
    }
    
    print(f"Sending mock Pub/Sub event to {url}...")
    try:
        response = requests.post(url, json=pubsub_msg)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except requests.exceptions.ConnectionError:
        print("Error: Django server is not running on port 8000.")

if __name__ == "__main__":
    test_webhook()
