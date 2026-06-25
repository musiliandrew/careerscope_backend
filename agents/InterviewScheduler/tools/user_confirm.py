import logging
from typing import List

from django.utils import timezone

from Applications.models import Applications, PendingInterviewConfirmation
from Oauth.models import Profile

logger = logging.getLogger(__name__)


def ask_user_for_confirmation(
    profile: Profile,
    application: Applications,
    email_thread_id: str,
    gmail_message_id: str,
    proposed_times: List[str],
    recruiter_email: str,
    company_name: str,
    role: str,
    stage: str,
) -> PendingInterviewConfirmation:
    """Create a PendingInterviewConfirmation and return it.

    UI / notification layer can surface this record to the user for approval
    based on the pending.id. This function does not block for user input; it
    only records the pending decision.
    """

    pending, created = PendingInterviewConfirmation.objects.get_or_create(
        application=application,
        defaults={
            "email_thread_id": email_thread_id,
            "gmail_message_id": gmail_message_id,
            "proposed_times": list(proposed_times or []),
            "recruiter_email": recruiter_email,
            "company_name": company_name[:200],
            "role": role[:200],
            "stage": stage[:50],
            "status": "pending",
        },
    )

    if not created:
        # Update times / recruiter if we already had a pending record
        pending.proposed_times = list(proposed_times or [])
        pending.recruiter_email = recruiter_email
        pending.company_name = company_name[:200]
        pending.role = role[:200]
        pending.stage = stage[:50]
        pending.status = "pending"
        pending.confirmed_at = None
        pending.save()

    logger.info(
        "InterviewScheduler.user_confirm: pending interview %s created/updated for profile %s, application %s",
        pending.id,
        profile.id,
        application.id,
    )

    return pending