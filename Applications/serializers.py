from rest_framework import serializers
from .models import Applications, ApplicationEvents, ApplicationStatusHistory, PendingInterviewConfirmation

class ApplicationEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationEvents
        fields = '__all__'

class ApplicationStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationStatusHistory
        fields = '__all__'

class PendingInterviewConfirmationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PendingInterviewConfirmation
        fields = '__all__'

class ApplicationSerializer(serializers.ModelSerializer):
    events = ApplicationEventSerializer(many=True, read_only=True, source='applicationevents_set')
    status_history = ApplicationStatusHistorySerializer(many=True, read_only=True, source='applicationstatushistory_set')
    pending_confirmation = PendingInterviewConfirmationSerializer(read_only=True, source='pendinginterviewconfirmation')
    days_since_applied = serializers.IntegerField(read_only=True)

    class Meta:
        model = Applications
        fields = [
            'id', 'company_name', 'job_title', 'status', 'applied_date', 
            'application_url', 'source', 'salary_range', 'location', 
            'work_type', 'notes', 'cover_letter', 'resume_version', 
            'next_action', 'next_action_date', 'last_status_change',
            'days_since_applied', 'events', 'status_history', 'pending_confirmation',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_status_change']

    def create(self, validated_data):
        # Automatically associate with the current user
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
            
        return super().create(validated_data)
