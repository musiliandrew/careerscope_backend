from datetime import timedelta

from django.utils import timezone
from django.db.models import Q
from django.db import DatabaseError
from django.db.utils import OperationalError
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from Jobs.models import JobInterests, Jobs
from Personalization.utils import notify_personalization_service
from Personalization.models import UserBehaviorEvent
from .serializers import (
    JobInterestSerializer,
    TrackInterestSerializer,
    ConvertInterestSerializer,
    ConversionReminderSerializer,
)


class InterestsListPagination(generics.ListAPIView):
    pass


class InterestsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = JobInterestSerializer

    def get_queryset(self):
        qs = JobInterests.objects.filter(user=self.request.user).order_by("-created_at")
        converted = self.request.query_params.get("converted")
        days = self.request.query_params.get("days")
        limit = self.request.query_params.get("limit")

        if converted in ["true", "1", "false", "0"]:
            is_conv = converted in ["true", "1"]
            qs = qs.filter(converted_to_application=is_conv)
        if days and days.isdigit():
            since = timezone.now() - timedelta(days=int(days))
            qs = qs.filter(created_at__gte=since)
        if limit and limit.isdigit():
            qs = qs[: int(limit)]
        return qs


class TrackInterestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TrackInterestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job_id = serializer.validated_data["job_id"]
        interest_type = serializer.validated_data.get("interest_type", "external_click")
        clicked_url = serializer.validated_data.get("clicked_url")
        source_page = serializer.validated_data.get("source_page")

        job = Jobs.objects.get(id=job_id)

        # Upsert by (user, job, interest_type)
        ji, created = JobInterests.objects.update_or_create(
            user=request.user,
            job=job,
            interest_type=interest_type,
            defaults={
                "clicked_url": clicked_url,
                "source_page": source_page,
                "updated_at": timezone.now(),
            },
        )
        # Ensure created_at if missing
        if not ji.created_at:
            ji.created_at = timezone.now()
            ji.save(update_fields=["created_at", "updated_at"])

        event_type = UserBehaviorEvent.EventType.JOB_CLICK
        if interest_type in {"save", "saved", "bookmark"}:
            event_type = UserBehaviorEvent.EventType.JOB_SAVE
        elif interest_type in {"apply", "applied"}:
            event_type = UserBehaviorEvent.EventType.JOB_APPLY

        notify_personalization_service(
            event_type=event_type,
            object_type="job",
            object_id=str(job.id)
        )

        return Response({"success": True, "interest_id": str(ji.id)}, status=status.HTTP_200_OK)


class ConvertInterestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ConvertInterestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        interest_id = serializer.validated_data["interest_id"]
        # additional_data = serializer.validated_data.get("additional_data", {})

        try:
            ji = JobInterests.objects.get(id=interest_id, user=request.user)
        except JobInterests.DoesNotExist:
            return Response({"success": False, "error": "Interest not found"}, status=status.HTTP_404_NOT_FOUND)

        ji.converted_to_application = True
        ji.updated_at = timezone.now()
        ji.save(update_fields=["converted_to_application", "updated_at"])

        notify_personalization_service(
            event_type=UserBehaviorEvent.EventType.JOB_APPLY,
            object_type="job",
            object_id=str(ji.job_id)
        )

        # Placeholder for application creation integration
        application_id = None

        return Response({"success": True, "application_id": application_id}, status=status.HTTP_200_OK)


class ConversionRemindersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        days = request.query_params.get("days") or "7"
        try:
            days_int = int(days)
        except ValueError:
            days_int = 7

        since = timezone.now() - timedelta(days=days_int)
        try:
            qs = (
                JobInterests.objects
                .filter(user=request.user, converted_to_application=False)
                .filter(created_at__gte=since)
                .select_related("job", "job__company")
                .order_by("-created_at")
            )

            reminders = []
            now = timezone.now()
            for ji in qs:
                job = ji.job
                company_name = getattr(job.company, "name", None)
                days_ago = max(0, (now - (ji.created_at or now)).days)
                reminders.append({
                    "interest_id": str(ji.id),
                    "job_title": job.title,
                    "company_name": company_name,
                    "clicked_url": ji.clicked_url or "",
                    "days_ago": days_ago,
                    "created_at": ji.created_at or now,
                })

            ser = ConversionReminderSerializer(reminders, many=True)
            return Response({"success": True, "reminders": ser.data}, status=status.HTTP_200_OK)
        except (OperationalError, DatabaseError):
            # On transient DB failures, fail soft with empty reminders
            return Response({"success": True, "reminders": []}, status=status.HTTP_200_OK)
