import json
import base64
import logging
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
import base64
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from Personalization.models import UserCompanyFollows, Notification
from Companies.models import Companies
from Applications.models import Applications
from Jobs.models import Jobs
from Oauth.models import JobPreferences

logger = logging.getLogger(__name__)

class PubSubJobConsumerView(APIView):
    """
    Webhook endpoint to consume Pub/Sub Push events.
    Listens for 'raw-jobs' topic events (specifically 'job_created').
    Generates notifications for users following the company.
    """
    permission_classes = [AllowAny] # In production, verify Google Pub/Sub tokens

    def post(self, request, *args, **kwargs):
        envelope = request.data
        if not envelope or "message" not in envelope:
            return Response({"error": "Bad request"}, status=status.HTTP_400_BAD_REQUEST)

        message = envelope.get("message", {})
        data_encoded = message.get("data")
        
        if not data_encoded:
            return Response({"status": "no data"}, status=status.HTTP_200_OK)

        try:
            data_json = base64.b64decode(data_encoded).decode('utf-8')
            payload = json.loads(data_json)
            
            # The Data Ingestion System outbox payload wraps the event
            # We expect outbox_events format: id, topic, event_type, payload
            # Actually, flush_outbox.py publishes the exact payload from the DB.
            # So payload is {"job_id": "...", "title": "...", "company_id": "..."}
            
            job_id = payload.get("job_id")
            company_id = payload.get("company_id")
            title = payload.get("title", "New Job")
            
            if not company_id or not job_id:
                logger.warning("Received job event without company_id or job_id")
                return Response({"status": "missing fields"}, status=status.HTTP_200_OK)
                
            try:
                company = Companies.objects.get(id=company_id)
            except Companies.DoesNotExist:
                logger.error(f"Company {company_id} not found for job event")
                return Response({"status": "company not found"}, status=status.HTTP_200_OK)

            # Find followers
            follows = UserCompanyFollows.objects.filter(company_id=company_id)
            
            notifications = []
            for follow in follows:
                user = follow.user
                notifications.append(Notification(
                    user=user,
                    title=f"New Job at {company.name}",
                    message=f"{company.name} just posted a new role: {title}",
                    notification_type="job_alert",
                    reference_id=job_id
                ))
                
                # Auto-Apply Logic
                decision_engine_url = getattr(settings, "DECISION_ENGINE_URL", "http://127.0.0.1:8002")
                evaluate_endpoint = f"{decision_engine_url}/api/v1/reasoning/evaluate_match"
                
                eval_payload = {
                    "user_id": str(user.id),
                    "job_snapshot": {
                        "job_id": job_id,
                        "title": title,
                        "description": "Scraped job description placeholder"
                    }
                }
                
                try:
                    response = requests.post(evaluate_endpoint, json=eval_payload, timeout=10)
                    if response.status_code == 200:
                        eval_result = response.json()
                        overall_readiness = eval_result.get("overall_readiness", 0.0)
                        
                        # Fetch User Preferences
                        prefs = JobPreferences.objects.filter(profile__user=user).first()
                        if prefs and prefs.auto_apply_enabled and overall_readiness >= prefs.auto_apply_threshold:
                            logger.info(f"High match score {overall_readiness} for {user.id}. Triggering Auto-Apply.")
                            
                            # Trigger Auto-Apply Agent
                            email_system_url = getattr(settings, "EMAIL_INTELLIGENCE_URL", "http://127.0.0.1:8001")
                            auto_apply_endpoint = f"{email_system_url}/webhook/agent/auto-apply"
                            
                            # Try to extract recruiter email from job metadata
                            recruiter_email = None
                            try:
                                job_obj = Jobs.objects.get(id=job_id)
                                if job_obj.parsed_metadata and isinstance(job_obj.parsed_metadata, dict):
                                    recruiter_email = job_obj.parsed_metadata.get('recruiter_email') or job_obj.parsed_metadata.get('contact_email')
                            except Exception:
                                pass
                                
                            if not recruiter_email:
                                # Fallback to company domain
                                domain = company.website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0] if company.website else f"{company.slug}.com"
                                recruiter_email = f"careers@{domain}"

                            agent_payload = {
                                "job_title": title,
                                "company_name": company.name,
                                "recruiter_email": recruiter_email,
                                "user_name": f"{user.first_name} {user.last_name}".strip() or user.username,
                                "cv_summary": "Auto-generated CV summary from profile.",
                                "cv_file_path": None # Mock for now
                            }
                            
                            agent_response = requests.post(auto_apply_endpoint, json=agent_payload, timeout=20)
                            if agent_response.status_code == 200:
                                # Log Application
                                import uuid
                                from django.utils import timezone
                                Applications.objects.create(
                                    id=uuid.uuid4(),
                                    user=user,
                                    company_name=company.name,
                                    job_title=title,
                                    status='applied',
                                    applied_date=timezone.now().date(),
                                    source='careerscope',
                                    notes='Auto-applied by CareerScoper Agent.',
                                    is_auto_applied=True
                                )
                                
                                notifications.append(Notification(
                                    user=user,
                                    title=f"Auto-Applied: {title} at {company.name}",
                                    message=f"We found an {overall_readiness}% match and applied on your behalf!",
                                    notification_type="system",
                                    reference_id=job_id
                                ))
                except Exception as eval_e:
                    logger.error(f"Failed to auto-apply for {user.id}: {eval_e}")
                
            if notifications:
                Notification.objects.bulk_create(notifications)
                logger.info(f"Created {len(notifications)} notifications for new job {job_id}")

            return Response({"status": "processed"}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error processing pubsub message: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PubSubApplicationEventConsumerView(APIView):
    """
    Webhook endpoint to consume Application Events (like Rejections) from Pub/Sub.
    Triggers the Decision Engine to analyze the rejection and creates a proactive study guide notification.
    """
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        envelope = request.data
        if not envelope or "message" not in envelope:
            return Response({"error": "Bad request"}, status=status.HTTP_400_BAD_REQUEST)
            
        message = envelope.get("message", {})
        data_encoded = message.get("data")
        attributes = message.get("attributes", {})
        
        # We only care about ApplicationRejectedPayload for this specific loop
        event_type = attributes.get("event_type", "")
        if event_type != "ApplicationRejectedPayload" and "ApplicationRejectedPayload" not in str(data_encoded):
            return Response({"status": "ignored"}, status=status.HTTP_200_OK)
            
        if not data_encoded:
            return Response({"status": "no data"}, status=status.HTTP_200_OK)
            
        try:
            data_json = base64.b64decode(data_encoded).decode('utf-8')
            payload = json.loads(data_json)
            
            user_id = payload.get("user_id")
            company_name = payload.get("company_name", "Unknown Company")
            role_title = payload.get("role_title", "Unknown Role")
            missing_skills = payload.get("missing_skills", [])
            extracted_feedback = payload.get("extracted_feedback", "")
            
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                logger.error(f"User {user_id} not found for rejection event")
                return Response({"status": "user not found"}, status=status.HTTP_200_OK)
                
            # Call Decision Engine
            decision_engine_url = getattr(settings, "DECISION_ENGINE_URL", "http://127.0.0.1:8002")
            analyze_endpoint = f"{decision_engine_url}/api/v1/reasoning/analyze_rejection"
            
            reasoning_payload = {
                "user_id": user_id,
                "company_name": company_name,
                "role_title": role_title,
                "missing_skills": missing_skills,
                "extracted_feedback": extracted_feedback
            }
            
            try:
                response = requests.post(analyze_endpoint, json=reasoning_payload, timeout=10)
                response.raise_for_status()
                study_guide = response.json()
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to call Decision Engine: {e}")
                study_guide = {
                    "encouraging_message": "We saw the update. Let's pivot and focus on fundamentals.",
                    "core_weaknesses": missing_skills,
                    "action_plan": ["Review core requirements", "Keep applying!"]
                }
                
            # Create the proactive notification
            message_body = study_guide.get("encouraging_message", "")
            if study_guide.get("action_plan"):
                message_body += f"\n\nNext Steps: {', '.join(study_guide['action_plan'][:2])}"
                
            Notification.objects.create(
                user=user,
                title=f"Action Plan: {company_name} Rejection",
                message=message_body[:255], # Truncate if too long
                notification_type="system"
            )
            
            logger.info(f"Created study guide notification for user {user_id} regarding {company_name}")
            return Response({"status": "processed"}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error processing application event: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
