import uuid
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
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
        Private method to generate AI insights on status change.
        """
        try:
            from agents.AIService.StatusInsight import generate_status_insight
            
            # Get old status from the most recent history before this change (if any)
            # Since we just saved the history in perform_update, we can look at the second most recent or just pass the current 'status' before it was updated in memory? 
            # Actually perform_update calls this AFTER saving the new status to the instance but BEFORE saving the instance? 
            # Wait, perform_update does: instance.status = new_status (implicitly via serializer) -> save()
            # So we need to pass the *previous* status. 
            # In perform_update, we have `instance.status` which is the OLD status because serializer.save() hasn't been called yet?
            # No, serializer.save() is called at the end of perform_update.
            # Let's look at perform_update again.
            
            # In perform_update:
            # instance = serializer.instance (This is the object from DB, so it has OLD status)
            # new_status = serializer.validated_data.get('status')
            # So we have both.
            
            result = generate_status_insight(
                company=application.company_name,
                role=application.job_title,
                old_status=application.status, # This is still the old status on the instance
                new_status=new_status,
                notes=application.notes or ""
            )
            
            insight_text = result.get('insight', '')
            actions = result.get('action_items', [])
            
            formatted_note = f"\n\n[{timezone.now().strftime('%Y-%m-%d')}] AI Coach:\n{insight_text}\n"
            if actions:
                formatted_note += "Next Steps:\n" + "\n".join([f"- {action}" for action in actions])
            
            # We append to notes. 
            # Note: The instance is about to be saved by serializer.save(), so we should modify the validated_data 
            # OR modify the instance and let serializer save it.
            # Since serializer.save() updates the instance with validated_data, if we modify instance.notes directly, 
            # it might be overwritten if 'notes' is in validated_data.
            # Safer to update the instance AFTER the main save, or update validated_data.
            
            # Let's update the application object directly and save it again to be sure, 
            # or just append to the notes in memory if we are sure it persists.
            # Actually, the cleanest way in perform_update is to modify the serializer's validated_data if possible,
            # but here we are in a helper method.
            
            if application.notes:
                application.notes += formatted_note
            else:
                application.notes = formatted_note
                
            application.save(update_fields=['notes'])
            
        except Exception as e:
            print(f"Failed to generate AI insight: {e}")

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
