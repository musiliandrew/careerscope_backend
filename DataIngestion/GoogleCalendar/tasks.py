import logging
from typing import Any, Dict

from celery import shared_task
from django.utils import timezone

from Events.models import Event
from Oauth.models import Profile

from .services import fetch_upcoming_interviews

logger = logging.getLogger(__name__)


@shared_task(name="DataIngestion.GoogleCalendar.tasks.sync_calendar_for_user")
def sync_calendar_for_user(profile_id: str) -> Dict[str, Any]:
    """Synchronize Google Calendar interview-like events into Events table."""

    try:
        profile = Profile.objects.select_related("user").get(id=profile_id)
    except Profile.DoesNotExist:
        logger.warning("sync_calendar_for_user: profile %s does not exist", profile_id)
        return {"profile_id": profile_id, "status": "missing_profile"}

    if not profile.calendar_sync_enabled or not profile.calendar_credentials:
        logger.info("Calendar sync disabled or no credentials for profile %s", profile_id)
        return {"profile_id": str(profile.id), "status": "disabled"}

    events = fetch_upcoming_interviews(profile)
    created = 0
    skipped = 0

    for ev in events:
        google_id = ev.get("google_id")
        summary = ev.get("summary") or "Interview"
        start = ev.get("start") or timezone.now()
        end = ev.get("end")

        # Avoid duplicates by (source, title, start_date)
        exists = Event.objects.filter(
            source="google_calendar",
            title__iexact=summary,
            start_date=start,
        ).exists()
        if exists:
            skipped += 1
            continue

        Event.objects.create(
            title=summary[:300],
            description=ev.get("description"),
            start_date=start,
            end_date=end,
            location=(ev.get("location") or "")[:255] or None,
            event_type="interview",
            category="interview",
            tech_focus=[],
            organizer=None,
            sponsors=[],
            prize_money=None,
            attendee_count=None,
            registration_deadline=None,
            external_url=ev.get("html_link"),
            image_url=None,
            is_virtual=None,
            is_hybrid=None,
            target_audience=[],
            requirements=[],
            status="upcoming",
            source="google_calendar",
            match_score=None,
            tags=[],
            created_at=timezone.now(),
            updated_at=timezone.now(),
        )
        created += 1

    profile.calendar_last_sync = timezone.now()
    profile.save(update_fields=["calendar_last_sync"])

    logger.info(
        "Calendar sync for profile %s completed: %s created, %s skipped",
        profile.id,
        created,
        skipped,
    )

    return {"profile_id": str(profile.id), "created": created, "skipped": skipped}