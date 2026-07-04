import json
import os
import logging
from typing import Optional

try:
    from google.cloud import tasks_v2
except ImportError:
    tasks_v2 = None

logger = logging.getLogger(__name__)

def enqueue_task(endpoint: str, payload: dict, service_url: Optional[str] = None) -> bool:
    """
    Enqueues an HTTP POST task to Google Cloud Tasks.
    
    endpoint: The relative path to hit (e.g. '/worker/consume')
    payload: A dictionary containing the JSON payload for the POST request
    service_url: The base URL of the microservice (e.g. data-ingestion-system URL).
                 Defaults to DATA_INGESTION_SERVICE_URL.
    """
    project = os.getenv("GCP_PROJECT")
    location = os.getenv("GCP_LOCATION")
    queue = os.getenv("GCP_QUEUE_NAME")
    
    if not service_url:
        service_url = os.getenv("DATA_INGESTION_SERVICE_URL", "http://127.0.0.1:8001")

    if not all([project, location, queue]):
        logger.warning(
            "Cloud Tasks env vars missing (GCP_PROJECT, GCP_LOCATION, GCP_QUEUE_NAME). "
            f"Falling back to direct HTTP request (or mock) for endpoint: {endpoint}"
        )
        
        # When running locally without GCP setup, we could dispatch the request directly via requests
        # but to avoid blocking the main thread, we just log it as a mock enqueue
        logger.info(f"[MOCK ENQUEUE] Endpoint: {service_url}{endpoint} | Payload: {payload}")
        return True

    if tasks_v2 is None:
        logger.error("google-cloud-tasks is not installed.")
        return False

    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(project, location, queue)

    url = f"{service_url.rstrip('/')}{endpoint}"
    
    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": url,
            "headers": {"Content-type": "application/json"},
            "body": json.dumps(payload).encode(),
        }
    }

    try:
        response = client.create_task(request={"parent": parent, "task": task})
        logger.debug(f"Created task {response.name}")
        return True
    except Exception as e:
        logger.error(f"Failed to create task in GCP: {e}")
        return False
