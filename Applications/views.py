import uuid
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from .models import Applications, ApplicationStatusHistory, ApplicationEvents
from .serializers import ApplicationSerializer, ApplicationEventSerializer
from agents.AIService import AIManager # Assuming this exists or we will use a placeholder

class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Applications.objects.filter(user=self.request.user).order_by('-applied_date')

    def perform_create(self, serializer):
        # The serializer.create method handles the user association
        serializer.save()

    def perform_update(self, serializer):
        # Check if status is changing
        instance = serializer.instance
        new_status = serializer.validated_data.get('status')
        
        if new_status and new_status != instance.status:
            # Log status change
            ApplicationStatusHistory.objects.create(
                id=uuid.uuid4(),
                application=instance,
                old_status=instance.status,
                new_status=new_status,
                changed_by_user=True,
                created_at=timezone.now()
            )
            instance.last_status_change = timezone.now()
            
            # Trigger AI Insight generation (Async or Sync)
            # For now, we'll do a simple synchronous call or placeholder
            # ideally this should be a celery task
            self._generate_ai_status_insight(instance, new_status)

        serializer.save()

    def _generate_ai_status_insight(self, application, new_status):
        """
        Private method to fire the async webhook for AI insight generation.
        """
        import threading
        import requests
        import os

        def fire_webhook():
            # Use 127.0.0.1 for local internal webhook triggers
            url = f"{os.getenv('BACKEND_URL', 'http://127.0.0.1:8000')}/api/applications/webhooks/status_insight/"
            if not url.endswith('/'):
                url += '/'
            payload = {
                "application_id": str(application.id),
                "user_id": str(self.request.user.id),
                "old_status": application.status,
                "new_status": new_status,
            }
            try:
                requests.post(url, json=payload, timeout=5)
            except Exception as e:
                print(f"Webhook trigger failed: {e}")

        threading.Thread(target=fire_webhook).start()

    @action(detail=True, methods=['post'])
    def add_event(self, request, pk=None):
        application = self.get_object()
        serializer = ApplicationEventSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(id=uuid.uuid4(), application=application, created_at=timezone.now())
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def generate_insight(self, request, pk=None):
        """
        Manual trigger for AI insight
        """
        application = self.get_object()
        self._generate_ai_status_insight(application, application.status)
        return Response({"status": "Insight generated", "notes": application.notes})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def status_insight_webhook(request):
    """
    Webhook handler for generating AI insights asynchronously.
    """
    app_id = request.data.get('application_id')
    user_id = request.data.get('user_id')
    old_status = request.data.get('old_status')
    new_status = request.data.get('new_status')
    
    if not all([app_id, user_id, new_status]):
        return Response({"error": "Missing parameters"}, status=400)
        
    application = Applications.objects.filter(id=app_id).first()
    if not application:
        return Response({"error": "Application not found"}, status=404)
        
    # Get user profile for rich context
    from Oauth.models import Profile
    profile = Profile.objects.filter(user_id=user_id).first()
    
    tech_skills = []
    learning_skills = []
    if profile:
        tech_skills = list(profile.skills.filter(want_to_learn=False).values_list('skill_name', flat=True))
        learning_skills = list(profile.skills.filter(want_to_learn=True).values_list('skill_name', flat=True))
        
    # Count recent rejections
    fourteen_days_ago = timezone.now() - timezone.timedelta(days=14)
    recent_rejections = Applications.objects.filter(
        user_id=user_id, 
        status='rejected', 
        last_status_change__gte=fourteen_days_ago
    ).count()
    
    try:
        from agents.AIService.StatusInsight import generate_status_insight
        result = generate_status_insight(
            company=application.company_name,
            role=application.job_title,
            old_status=old_status or "",
            new_status=new_status,
            notes=application.notes or "",
            tech_skills=tech_skills,
            learning_skills=learning_skills,
            recent_rejections=recent_rejections
        )
        
        insight_text = result.get('insight', '')
        actions = result.get('action_items', [])
        suggested_skill = result.get('suggested_skill_to_learn', '').strip()
        
        # Auto-update profile with missing skill
        if suggested_skill and profile:
            from Oauth.models import UserSkills
            from Personalization.utils import notify_personalization_service
            
            skill_exists = UserSkills.objects.filter(profile=profile, skill_name__iexact=suggested_skill).exists()
            if not skill_exists:
                new_skill = UserSkills.objects.create(
                    profile=profile,
                    skill_name=suggested_skill,
                    skill_category="AI Suggested",
                    want_to_learn=True
                )
                notify_personalization_service("skill_updated", "UserSkills", new_skill.id)
                actions.append(f"Added '{suggested_skill}' to your Learning Goals to adjust your future job matches.")
        
        formatted_note = f"\n\n[{timezone.now().strftime('%Y-%m-%d')}] AI Coach:\n{insight_text}\n"
        if actions:
            formatted_note += "Next Steps:\n" + "\n".join([f"- {action}" for action in actions])
            
        if application.notes:
            application.notes += formatted_note
        else:
            application.notes = formatted_note
            
        application.save(update_fields=['notes'])
        return Response({"status": "Success"})
    except Exception as e:
        print(f"Failed to generate AI insight: {e}")
        return Response({"error": str(e)}, status=500)
