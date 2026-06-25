import base64
import logging
from email.mime.text import MIMEText

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from Oauth.models import Profile

logger = logging.getLogger(__name__)

GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.send"


def _get_gmail_service(profile: Profile):
    data = profile.gmail_credentials
    if not data:
        return None
    try:
        if isinstance(data, str):
            import json

            data = json.loads(data)
        creds = Credentials.from_authorized_user_info(data, scopes=[GMAIL_SCOPE])
    except Exception as exc:
        logger.error("InterviewScheduler.gmail: failed to build creds for %s: %s", profile.id, exc)
        return None

    try:
        return build("gmail", "v1", credentials=creds)
    except Exception as exc:
        logger.error("InterviewScheduler.gmail: failed to build service for %s: %s", profile.id, exc)
        return None


def _encode_message(msg: MIMEText) -> dict:
    import base64 as b64

    raw = b64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    return {"raw": raw}


def send_reply_to_recruiter(profile: Profile, thread_id: str, message: str) -> bool:
    """Send a plain-text reply in an existing Gmail thread.

    This assumes the Gmail account used for sync is also the sender address.
    """

    service = _get_gmail_service(profile)
    if not service:
        return False

    try:
        msg = MIMEText(message)
        msg["Subject"] = "Re: Interview availability"
        msg["To"] = ""  # Gmail infers from thread; recruiter is already on thread

        body = _encode_message(msg)
        body["threadId"] = thread_id

        service.users().messages().send(userId="me", body=body).execute()
        return True
    except Exception as exc:
        logger.error(
            "InterviewScheduler.gmail: failed to send reply for profile %s, thread %s: %s",
            profile.id,
            thread_id,
            exc,
        )
        return False