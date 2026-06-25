import json
import logging
from datetime import datetime, timedelta
from typing import List

from django.utils import timezone

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from Oauth.models import Profile

logger = logging.getLogger(__name__)

CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar.events"


def get_calendar_service(profile: Profile):
    """Build a Google Calendar service from Profile.calendar_credentials.

    Assumes the user granted calendar.events scope during OAuth.
    """

    data = profile.calendar_credentials
    if not data:
        return None

    try:
        if isinstance(data, str):
            data = json.loads(data)
        creds = Credentials.from_authorized_user_info(data, scopes=[CALENDAR_SCOPE])
    except Exception as exc:  # defensive
        logger.error("InterviewScheduler.calendar: failed to build creds for profile %s: %s", profile.id, exc)
        return None

    # Refresh if needed and persist
    try:
        if creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request

            creds.refresh(Request())
            try:
                profile.calendar_credentials = json.loads(creds.to_json())
                profile.save(update_fields=["calendar_credentials"])
            except Exception as exc:
                logger.warning(
                    "InterviewScheduler.calendar: failed to persist refreshed creds for %s: %s",
                    profile.id,
                    exc,
                )
    except Exception as exc:
        logger.error("InterviewScheduler.calendar: error refreshing token for %s: %s", profile.id, exc)

    try:
        return build("calendar", "v3", credentials=creds)
    except Exception as exc:
        logger.error("InterviewScheduler.calendar: failed to build service for %s: %s", profile.id, exc)
        return None


def find_free_slots(profile: Profile, days: int = 7, duration_minutes: int = 60) -> List[str]:
    """Return a naive list of candidate times (ISO strings) over the next N days.

    This implementation is simple: it proposes 9am–5pm local hours, spaced by
    `duration_minutes`, without doing a full free/busy check. It's enough to
    demonstrate the flow and can be upgraded later.
    """

    now = timezone.now()
    suggestions: List[str] = []

    start_day = now
    end_day = now + timedelta(days=days)

    current = start_day.replace(minute=0, second=0, microsecond=0)
    while current < end_day and len(suggestions) < 10:
        # Working hours heuristic: 9–17 local time
        if 9 <= current.hour < 17:
            suggestions.append(current.isoformat())
        current += timedelta(minutes=duration_minutes)

    return suggestions


def create_interview_event(profile: Profile, start_time: str, title: str, recruiter_email: str | None = None) -> str | None:
    """Create a calendar event and optionally invite the recruiter.

    Returns an HTML link to the event on success, or None on failure.
    """

    service = get_calendar_service(profile)
    if not service:
        return None

    try:
        start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        if timezone.is_naive(start_dt):
            start_dt = timezone.make_aware(start_dt, timezone.utc)
    except Exception:
        logger.warning("InterviewScheduler.calendar: invalid start_time %r", start_time)
        return None

    end_dt = start_dt + timedelta(hours=1)

    event = {
        "summary": title,
        "start": {"dateTime": start_dt.isoformat()},
        "end": {"dateTime": end_dt.isoformat()},
    }

    if recruiter_email:
        event["attendees"] = [{"email": recruiter_email}]

    try:
        created = (
            service.events()
            .insert(calendarId="primary", body=event, sendUpdates="all")
            .execute()
        )
        return created.get("htmlLink")
    except HttpError as exc:
        logger.error(
            "InterviewScheduler.calendar: failed to create event for profile %s: %s",
            profile.id,
            exc,
        )
        return None