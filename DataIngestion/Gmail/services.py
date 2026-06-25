import base64
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from django.utils import timezone

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from Oauth.models import Profile

logger = logging.getLogger(__name__)

GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"


def _build_credentials_from_profile(profile: Profile) -> Credentials | None:
    """Reconstruct Google Credentials from stored profile JSON.

    The JSON is stored in Profile.gmail_credentials and is expected to be either
    a dict or a JSON string compatible with google.oauth2.credentials.Credentials.
    """

    data = profile.gmail_credentials
    if not data:
        return None

    try:
        if isinstance(data, str):
            data = json.loads(data)
        # from_authorized_user_info expects a mapping with token/refresh_token, etc.
        creds = Credentials.from_authorized_user_info(data, scopes=[GMAIL_READONLY_SCOPE])
        # Ensure scope includes read-only if missing
        if not creds.scopes or GMAIL_READONLY_SCOPE not in creds.scopes:
            creds = Credentials.from_authorized_user_info(
                {**data, "scopes": [GMAIL_READONLY_SCOPE]}, scopes=[GMAIL_READONLY_SCOPE]
            )
        return creds
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to build Gmail credentials for profile %s: %s", profile.id, exc)
        return None


def get_gmail_service(profile: Profile):
    """Return a Gmail API client for the given profile or None if not configured."""

    creds = _build_credentials_from_profile(profile)
    if not creds:
        return None

    # Refresh tokens if needed; google-auth handles refresh when used, but we
    # can proactively persist refreshed tokens.
    try:
        if creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request

            creds.refresh(Request())
            # Persist updated credentials back to profile
            try:
                profile.gmail_credentials = json.loads(creds.to_json())
                profile.save(update_fields=["gmail_credentials"])
            except Exception as exc:  # pragma: no cover
                logger.warning("Failed to persist refreshed Gmail credentials for %s: %s", profile.id, exc)
    except Exception as exc:  # pragma: no cover
        logger.error("Error refreshing Gmail token for profile %s: %s", profile.id, exc)

    try:
        return build("gmail", "v1", credentials=creds)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to build Gmail service for profile %s: %s", profile.id, exc)
        return None


def fetch_job_application_emails(profile: Profile, since_days: int = 14) -> List[Dict[str, Any]]:
    """Fetch potentially job-related emails for the given profile.

    This does not classify emails; it only pulls messages matching a broad query
    and extracts basic metadata and a text body snippet.
    """

    service = get_gmail_service(profile)
    if not service:
        return []

    # Gmail uses YYYY/MM/DD in query syntax
    since = (timezone.now() - timedelta(days=since_days)).strftime("%Y/%m/%d")
    # Broad query for job-application-related emails
    query = (
        f"after:{since} "
        "(subject:application OR subject:applied OR subject:resume "
        "OR subject:'thank you for applying' OR 'job application' OR 'interview')"
    )

    try:
        response = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=100)
            .execute()
        )
    except HttpError as exc:
        logger.error("Gmail API error for profile %s while listing messages: %s", profile.id, exc)
        return []

    messages = response.get("messages", [])
    if not messages:
        return []

    results: List[Dict[str, Any]] = []

    for msg in messages:
        msg_id = msg.get("id")
        if not msg_id:
            continue
        try:
            msg_data = (
                service.users()
                .messages()
                .get(userId="me", id=msg_id, format="full")
                .execute()
            )
        except HttpError as exc:
            logger.warning("Gmail API error fetching message %s for profile %s: %s", msg_id, profile.id, exc)
            continue

        payload = msg_data.get("payload", {})
        headers = {h["name"]: h["value"] for h in payload.get("headers", [])}
        subject = headers.get("Subject", "")
        from_ = headers.get("From", "")
        date_header = headers.get("Date", "")

        body = _extract_plaintext_from_payload(payload)

        results.append(
            {
                "gmail_id": msg_id,
                "thread_id": msg_data.get("threadId"),
                "subject": subject,
                "from": from_,
                "date_header": date_header,
                "snippet": msg_data.get("snippet", ""),
                "body": body[:5000] if body else "",
            }
        )

    return results


def _extract_plaintext_from_payload(payload: Dict[str, Any]) -> str:
    """Extract a best-effort plaintext body from a Gmail message payload."""

    try:
        if "parts" in payload:
            # Walk parts recursively looking for text/plain
            texts: List[str] = []
            stack = [payload]
            while stack:
                part = stack.pop()
                for child in part.get("parts", []) or []:
                    stack.append(child)
                mime_type = part.get("mimeType")
                if mime_type == "text/plain":
                    data = (part.get("body") or {}).get("data")
                    if data:
                        texts.append(_decode_base64(data))
            return "\n".join(t for t in texts if t)

        # No parts → single body
        data = (payload.get("body") or {}).get("data")
        if data:
            return _decode_base64(data)
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to extract plaintext from Gmail payload: %s", exc)

    return ""


def _decode_base64(data: str) -> str:
    try:
        return base64.urlsafe_b64decode(data.encode("utf-8")).decode("utf-8", errors="ignore")
    except Exception:  # pragma: no cover
        return ""