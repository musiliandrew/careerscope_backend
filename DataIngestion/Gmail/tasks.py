import logging
from datetime import datetime
from typing import Any, Dict, List

from celery import shared_task
from django.db import models
from django.utils import timezone

from Applications.models import Applications, EmailTracking
from Oauth.models import Profile

from .services import fetch_job_application_emails

logger = logging.getLogger(__name__)


def _classify_email_fallback(subject: str, body: str) -> Dict[str, Any]:
    """Very simple keyword-based classifier used if the real classifier is unavailable."""

    text = f"{subject}\n{body}".lower()
    is_job_related = any(k in text for k in ["application", "applied", "interview", "job opportunity", "role"])
    return {
        "is_job_related": is_job_related,
        "company": None,
        "job_title": None,
        "email_type": "job_application" if is_job_related else "other",
        "confidence": 0.6 if is_job_related else 0.2,
    }


try:  # pragma: no cover - best-effort import
    from agents.Email.classifier import classify_email  # type: ignore
except Exception:  # pragma: no cover

    def classify_email(text: str) -> Dict[str, Any]:  # type: ignore[override]
        return _classify_email_fallback("", text)


@shared_task(name="DataIngestion.Gmail.tasks.sync_gmail_for_user")
def sync_gmail_for_user(profile_id: str) -> Dict[str, Any]:
    """Synchronize Gmail messages for a single Profile.

    This will:
    - Fetch recent candidate messages from Gmail.
    - Run the email classifier.
    - Store raw email metadata in EmailTracking.
    - Create Applications rows for probable job applications (source="gmail_auto").
    """

    try:
        profile = Profile.objects.select_related("user").get(id=profile_id)
    except Profile.DoesNotExist:
        logger.warning("sync_gmail_for_user: profile %s does not exist", profile_id)
        return {"profile_id": profile_id, "status": "missing_profile"}

    if not profile.gmail_sync_enabled or not profile.gmail_credentials:
        logger.info("Gmail sync disabled or no credentials for profile %s", profile_id)
        return {"profile_id": str(profile.id), "status": "disabled"}

    emails = fetch_job_application_emails(profile, since_days=14)
    created_apps = 0
    created_tracking = 0
    skipped_existing = 0

    for email in emails:
        gmail_id = email["gmail_id"]

        # Deduplicate by email_id (unique constraint on EmailTracking.email_id)
        if EmailTracking.objects.filter(email_id=gmail_id, user__isnull=False).exists():
            skipped_existing += 1
            continue

        subject = email.get("subject") or ""
        body = email.get("body") or ""
        classification = classify_email(f"{subject}\n{body}") or {}

        is_job_related = bool(classification.get("is_job_related"))
        if not is_job_related:
            # Still log the email for diagnostics but don't create an application.
            logger.debug("Email %s for profile %s not classified as job-related", gmail_id, profile.id)

        # Create EmailTracking row
        tracking = EmailTracking.objects.create(
            user=profile.user,
            application=None,
            email_id=gmail_id,
            thread_id=email.get("thread_id"),
            subject=subject[:500] if subject else None,
            sender=email.get("from", "")[:255] or None,
            sender_name=None,
            received_at=_parse_email_date_header(email.get("date_header")) or timezone.now(),
            body_text=(body or None),
            body_html=None,
            email_type=classification.get("email_type"),
            company_identified=classification.get("company"),
            job_title_identified=classification.get("job_title"),
            confidence_score=classification.get("confidence"),
            is_processed=True,
            processing_status="classified",
            processed_at=timezone.now(),
            error_message=None,
            application_created=False,
            event_created=False,
            user_notified=False,
            ai_model_used=classification.get("model"),
            extraction_data=classification or {},
            created_at=timezone.now(),
            updated_at=timezone.now(),
        )
        created_tracking += 1

        # If this is an interview invite, trigger the autonomous scheduler agent.
        if classification.get("is_interview_invite"):
            try:
                from agents.InterviewScheduler.agent import run_interview_scheduler

                run_interview_scheduler.delay(
                    str(profile.id),
                    {
                        "gmail_id": gmail_id,
                        "thread_id": email.get("thread_id"),
                        "subject": subject,
                        "body": body,
                        "from": email.get("from"),
                        "classification": classification,
                    },
                )
            except Exception as exc:
                logger.error(
                    "Gmail sync: failed to trigger InterviewScheduler for profile %s, gmail_id %s: %s",
                    profile.id,
                    gmail_id,
                    exc,
                )

        if not is_job_related:
            continue

        company = (classification.get("company") or email.get("from") or "").strip() or "Unknown Company"
        job_title = (classification.get("job_title") or classification.get("role") or "").strip() or "Unknown Role"

        # Avoid duplicate Applications per user/company/job_title on the same day
        user = tracking.user
        today = timezone.now().date()
        exists = Applications.objects.filter(
            user=user,
            company_name__iexact=company,
            job_title__iexact=job_title,
            applied_date=today,
        ).exists()
        if exists:
            skipped_existing += 1
            continue

        app = Applications.objects.create(
            user=user,
            job=None,
            job_interest=None,
            company_name=company[:255],
            job_title=job_title[:255],
            status="applied",
            applied_date=today,
            application_url=None,
            source="gmail_auto",
            salary_range=None,
            location=None,
            work_type=None,
            notes=f"Auto-imported from Gmail. Subject: {subject}",
            cover_letter=None,
            resume_version=None,
            interview_dates=None,
            interview_notes=None,
            next_action=None,
            next_action_date=None,
            follow_up_count=0,
            rejection_reason=None,
            feedback_received=None,
            offer_details=None,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            last_status_change=timezone.now(),
        )
        tracking.application = app
        tracking.application_created = True
        tracking.save(update_fields=["application", "application_created", "updated_at"])
        created_apps += 1

    profile.gmail_last_sync = timezone.now()
    profile.save(update_fields=["gmail_last_sync"])

    logger.info(
        "Gmail sync for profile %s completed: %s tracking, %s applications, %s skipped",
        profile.id,
        created_tracking,
        created_apps,
        skipped_existing,
    )

    return {
        "profile_id": str(profile.id),
        "created_tracking": created_tracking,
        "created_applications": created_apps,
        "skipped_existing": skipped_existing,
    }


def _parse_email_date_header(value: str | None):
    if not value:
        return None
    # Try multiple RFC2822-compatible formats
    for fmt in [
        "%a, %d %b %Y %H:%M:%S %z",
        "%d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%d %b %Y %H:%M:%S %Z",
    ]:
        try:
            dt = datetime.strptime(value, fmt)
            return dt.astimezone(timezone.utc)
        except Exception:
            continue
    return None


@shared_task(name="DataIngestion.Gmail.tasks.sync_all_connected_accounts")
def sync_all_connected_accounts() -> Dict[str, Any]:
    """Master periodic task.

    Every 3 hours (scheduled via Celery Beat) this will scan for all Profiles
    that have Gmail and/or Calendar sync enabled and enqueue per-user tasks.
    """

    profiles = Profile.objects.filter(
        models.Q(gmail_sync_enabled=True, gmail_credentials__isnull=False)
        | models.Q(calendar_sync_enabled=True, calendar_credentials__isnull=False)
    )

    scheduled_gmail = 0
    scheduled_calendar = 0

    for profile in profiles:
        if profile.gmail_sync_enabled and profile.gmail_credentials:
            sync_gmail_for_user.delay(str(profile.id))
            scheduled_gmail += 1
        if profile.calendar_sync_enabled and profile.calendar_credentials:
            try:
                from DataIngestion.GoogleCalendar.tasks import sync_calendar_for_user

                sync_calendar_for_user.delay(str(profile.id))
                scheduled_calendar += 1
            except Exception as exc:  # pragma: no cover
                logger.error(
                    "Failed to enqueue calendar sync for profile %s: %s", profile.id, exc
                )

    logger.info(
        "sync_all_connected_accounts: scheduled %s gmail and %s calendar syncs",
        scheduled_gmail,
        scheduled_calendar,
    )

    return {
        "scheduled_gmail": scheduled_gmail,
        "scheduled_calendar": scheduled_calendar,
    }
