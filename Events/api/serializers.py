from rest_framework import serializers
from Events.models import Event


class EventSerializer(serializers.ModelSerializer):
    startDate = serializers.DateTimeField(source='start_date')
    endDate = serializers.DateTimeField(source='end_date', allow_null=True)
    eventType = serializers.CharField(source='event_type', allow_null=True)
    techFocus = serializers.ListField(source='tech_focus')
    prizeMoney = serializers.CharField(source='prize_money', allow_null=True)
    registrationDeadline = serializers.DateTimeField(source='registration_deadline', allow_null=True)
    externalUrl = serializers.CharField(source='external_url', allow_null=True)
    imageUrl = serializers.CharField(source='image_url', allow_null=True)
    isVirtual = serializers.BooleanField(source='is_virtual', allow_null=True)
    isHybrid = serializers.BooleanField(source='is_hybrid', allow_null=True)
    matchScore = serializers.IntegerField(source='match_score', allow_null=True)

    class Meta:
        model = Event
        fields = [
            'id',
            'title',
            'description',
            'startDate',
            'endDate',
            'location',
            'eventType',
            'category',
            'techFocus',
            'organizer',
            'sponsors',
            'prizeMoney',
            'attendeeCount',
            'registrationDeadline',
            'externalUrl',
            'imageUrl',
            'isVirtual',
            'isHybrid',
            'targetAudience',
            'requirements',
            'status',
            'source',
            'matchScore',
            'tags',
        ]
