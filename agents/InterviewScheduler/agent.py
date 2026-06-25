import logging
from typing import Any, Dict

from celery import shared_task

from Applications.models import Applications
from Oauth.models import Profile

from .tools.google_calendar import find_free_slots, create_interview_event
from .tools.email_reply import send_reply_to_recruiter
from .tools.user_confirm import ask_user_for_confirmation

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert interview scheduling assistant.
You NEVER confirm a time without explicit user approval.
Always propose 2–3 times from the user's actual calendar.
Only create the event after the user says explicit approval words like "yes", "confirm", "book it".
Then send a polite reply to the recruiter.
Update the job application stage accordingly.
"""


@shared_task(name="agents.InterviewScheduler.run_interview_scheduler")
def run_interview_scheduler(profile_id: str, email_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Entry point called from Gmail ingestion when an interview invite is detected.

    `email_payload` should contain at least:
    - gmail_id
    - thread_id
    - subject
    - body
    - classification dict with company, role, stage, is_interview_invite, proposed_times (optional)
    """

    logger.info("InterviewScheduler: received interview email for profile=%s", profile_id)

    try:
        profile = Profile.objects.select_related("user").get(id=profile_id)
    except Profile.DoesNotExist:
        logger.warning("InterviewScheduler: profile %s does not exist", profile_id)
        return {"status": "missing_profile"}

    classification = email_payload.get("classification") or {}

    company = classification.get("company") or email_payload.get("from") or "Unknown Company"
    role = classification.get("role") or classification.get("job_title") or "Unknown Role"
    stage = classification.get("stage") or "interview"

    # Try to find an Applications row that matches this company & role
    application = (
        Applications.objects.filter(
            user__email=profile.user.email,
            company_name__icontains=company,
            job_title__icontains=role,
        )
        .order_by("-applied_date")
        .first()
    )

    if not application:
        logger.warning(
            "InterviewScheduler: no matching application for profile=%s company=%r role=%r",
            profile.id,
            company,
            role,
        )
        return {"status": "no_matching_application"}

    # Candidate time suggestions: 2–3 slots
    suggested = classification.get("proposed_times") or []
    if not suggested:
        all_slots = find_free_slots(profile, days=7, duration_minutes=60)
        suggested = all_slots[:3]

    pending = ask_user_for_confirmation(
        profile=profile,
        application=application,
        email_thread_id=email_payload.get("thread_id") or "",
        gmail_message_id=email_payload.get("gmail_id") or "",
        proposed_times=suggested,
        recruiter_email=classification.get("recruiter_email") or "",
        company_name=company,
        role=role,
        stage=stage,
    )

    # At this point, UI should surface `pending.id` to the user for approval.
    # Separate API/view will:
    # - mark pending.status = "confirmed"
    # - choose a specific time
    # - call `finalize_interview_booking` below.

    return {
        "status": "pending_user_confirmation",
        "pending_id": pending.id,
        "suggested_times": pending.proposed_times,
    }


@shared_task(name="agents.InterviewScheduler.finalize_interview_booking")
def finalize_interview_booking(
    pending_id: int,
    chosen_time: str,
    user_response: str,
) -> Dict[str, Any]:
    """Finalize the interview booking after the user has approved a time.

    - Create calendar event
    - Send reply email
    - Update application stage
    - Mark PendingInterviewConfirmation as confirmed
    """

    from Applications.models import PendingInterviewConfirmation

    try:
        pending = PendingInterviewConfirmation.objects.select_related("application").get(id=pending_id)
    except PendingInterviewConfirmation.DoesNotExist:
        logger.warning("InterviewScheduler.finalize: pending %s does not exist", pending_id)
        return {"status": "missing_pending"}

    profile = Profile.objects.select_related("user").get(user=pending.application.user.user)  # type: ignore[arg-type]

    event_title = f"Interview - {pending.company_name} - {pending.role}"
    event_link = create_interview_event(
        profile=profile,
        start_time=chosen_time,
        title=event_title,
        recruiter_email=pending.recruiter_email,
    )

    if not event_link:
        logger.error("InterviewScheduler.finalize: failed to create calendar event for pending %s", pending.id)
        return {"status": "calendar_error"}

    # Send reply email
    body = (
        f"Hi,\n\nThanks for the invitation. I'd like to confirm the interview at {chosen_time}.\n"
        f"Looking forward to speaking with you.\n\nBest,\n{profile.full_name or profile.user.get_username()}"
    )
    send_reply_to_recruiter(profile, thread_id=pending.email_thread_id, message=body)

    # Update application stage
    app = pending.application
    app.status = "interview"
    app.interview_notes = (app.interview_notes or "") + f"\nScheduled via agent at {chosen_time}"
    app.last_status_change = timezone.now()
    app.save(update_fields=["status", "interview_notes", "last_status_change"])

    pending.status = "confirmed"
    pending.user_response = user_response
    pending.confirmed_at = timezone.now()
    pending.save(update_fields=["status", "user_response", "confirmed_at"])

    return {"status": "booked", "event_link": event_link}