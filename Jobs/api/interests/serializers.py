from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta

from Jobs.models import JobInterests, Jobs


class JobSummarySerializer(serializers.ModelSerializer):
    company = serializers.CharField(source="company.name", read_only=True)
    location = serializers.SerializerMethodField()

    class Meta:
        model = Jobs
        fields = [
            "id",
            "title",
            "company",
            "external_url",
        ]

    def get_location(self, obj: Jobs):
        try:
            city = getattr(obj.location, "city", None)
            country = getattr(obj.location, "country", None)
            if city and country:
                return f"{city}, {country}"
            return city or country or "Remote"
        except Exception:
            return None


class JobInterestSerializer(serializers.ModelSerializer):
    job = JobSummarySerializer(read_only=True)
    days_ago = serializers.SerializerMethodField()

    class Meta:
        model = JobInterests
        fields = [
            "id",
            "job",
            "interest_type",
            "clicked_url",
            "converted_to_application",
            "conversion_reminder_sent",
            "created_at",
            "days_ago",
        ]

    def get_days_ago(self, obj: JobInterests):
        try:
            if obj.created_at:
                delta = timezone.now() - obj.created_at
                return max(0, delta.days)
            return 0
        except Exception:
            return 0


class TrackInterestSerializer(serializers.Serializer):
    job_id = serializers.UUIDField()
    interest_type = serializers.ChoiceField(choices=["view", "external_click", "save", "share"], default="external_click")
    clicked_url = serializers.URLField(required=False, allow_blank=True)
    source_page = serializers.CharField(required=False, allow_blank=True)

    def validate_job_id(self, value):
        if not Jobs.objects.filter(id=value).exists():
            raise serializers.ValidationError("Job not found")
        return value


class ConvertInterestSerializer(serializers.Serializer):
    interest_id = serializers.UUIDField()
    additional_data = serializers.JSONField(required=False)

    def validate_interest_id(self, value):
        if not JobInterests.objects.filter(id=value).exists():
            raise serializers.ValidationError("Interest not found")
        return value


class ConversionReminderSerializer(serializers.Serializer):
    interest_id = serializers.UUIDField()
    job_title = serializers.CharField()
    company_name = serializers.CharField()
    clicked_url = serializers.CharField(allow_blank=True, required=False)
    days_ago = serializers.IntegerField()
    created_at = serializers.DateTimeField()
