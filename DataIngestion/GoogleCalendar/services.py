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

CALENDAR_READONLY_SCOPE = "https://www.googleapis.com/auth/calendar.readonly"


def _build_credentials_from_profile(profile: Profile) -> Credentials | None:
    data = profile.calendar_credentials
    if not data:
        return None
    try:
        if isinstance(data, str):
            data = json.loads(data)
        creds = Credentials.from_authorized_user_info(data, scopes=[CALENDAR_READONLY_SCOPE])
        if not creds.scopes or CALENDAR_READONLY_SCOPE not in creds.scopes:
            creds = Credentials.from_authorized_user_info(
                {**data, "scopes": [CALENDAR_READONLY_SCOPE]},
                scopes=[CALENDAR_READONLY_SCOPE],
            )
        return creds
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to build Calendar credentials for profile %s: %s", profile.id, exc)
        return None


def get_calendar_service(profile: Profile):
    creds = _build_credentials_from_profile(profile)
    if not creds:
        return None

    try:
        if creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request

            creds.refresh(Request())
            try:
                profile.calendar_credentials = json.loads(creds.to_json())
                profile.save(update_fields=["calendar_credentials"])
            except Exception as exc:  # pragma: no cover
                logger.warning(
                    "Failed to persist refreshed Calendar credentials for %s: %s",
                    profile.id,
                    exc,
                )
    except Exception as exc:  # pragma: no cover
        logger.error("Error refreshing Calendar token for profile %s: %s", profile.id, exc)

    try:
        return build("calendar", "v3", credentials=creds)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to build Calendar service for profile %s: %s", profile.id, exc)
        return None


def fetch_upcoming_interviews(profile: Profile, days_ahead: int = 30) -> List[Dict[str, Any]]:
    """Fetch upcoming events that are likely interviews/meetings."""

    service = get_calendar_service(profile)
    if not service:
        return []

    now = timezone.now()
    time_min = now.isoformat()
    time_max = (now + timedelta(days=days_ahead)).isoformat()

    try:
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
                maxResults=100,
            )
            .execute()
        )
    except HttpError as exc:
        logger.error("Calendar API error for profile %s: %s", profile.id, exc)
        return []

    items = events_result.get("items", [])
    results: List[Dict[str, Any]] = []
    for ev in items:
        summary = ev.get("summary") or ""
        description = ev.get("description") or ""
        text = f"{summary}\n{description}".lower()
        # Heuristic filter for interviews/meetings
        if not any(k in text for k in ["interview", "screen", "recruiter", "hiring manager", "onsite"]):
            continue

        start = _parse_event_datetime(ev.get("start")) or now
        end = _parse_event_datetime(ev.get("end")) or (start + timedelta(hours=1))

        results.append(
            {
                "google_id": ev.get("id"),
                "summary": summary,
                "description": description,
                "location": ev.get("location"),
                "start": start,
                "end": end,
                "html_link": ev.get("htmlLink"),
            }
        )

    return results


def _parse_event_datetime(obj: Dict[str, Any] | None):
    if not obj:
        return None
    value = obj.get("dateTime") or obj.get("date")
    if not value:
        return None
    try:
        # google returns ISO 8601
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if timezone.is_naive(dt):
            return timezone.make_aware(dt, timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:  # pragma: no cover
        return None