import requests
import logging
import threading
import os

logger = logging.getLogger(__name__)

PERSONALIZATION_WEBHOOK_URL = os.getenv("PERSONALIZATION_WEBHOOK_URL", "http://localhost:8001/webhooks")

def _send_webhook(endpoint: str, payload: dict):
    url = f"{PERSONALIZATION_WEBHOOK_URL}/{endpoint}"
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        logger.error(f"Failed to send personalization webhook to {url}: {e}")

def notify_personalization_service(event_type: str, object_type: str, object_id: str):
    """
    Fire-and-forget webhook to the personalization engine.
    """
    payload = {
        "event_type": event_type,
        "object_type": object_type,
        "object_id": str(object_id)
    }
    # Run in a background thread so it doesn't block the Django response
    threading.Thread(target=_send_webhook, args=("profile_updated", payload)).start()
