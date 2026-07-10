from datetime import timedelta

from django.utils import timezone
from django.db.models import Q
from rest_framework import generics, filters
from rest_framework.permissions import AllowAny

from Jobs.models import Jobs
from .serializers import JobListSerializer


class JobsListPagination(filters.BaseFilterBackend):
    pass


from rest_framework.pagination import PageNumberPagination


class Pagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class JobsListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = JobListSerializer
    pagination_class = Pagination

    def get_queryset(self):
        qs = Jobs.objects.filter(status='active').select_related('company', 'location', 'source').order_by('-posted_at')
        q = self.request.query_params.get('q')
        role = self.request.query_params.get('role')  # ds|ai|ml|swe
        tech = self.request.query_params.get('tech')  # comma list
        location = self.request.query_params.get('location')
        work_type = self.request.query_params.get('work_type')
        source = self.request.query_params.get('source')
        is_remote = self.request.query_params.get('is_remote')
        days = self.request.query_params.get('days')

        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(company__name__icontains=q))
        if role in ['ds','ai','ml','swe']:
            # coarse filter against title/description
            from Jobs.filters import ROLE_KEYWORDS
            any_terms = ROLE_KEYWORDS.get(role, [])
            filt = Q()
            for t in any_terms:
                filt |= Q(title__icontains=t) | Q(description__icontains=t)
            if any_terms:
                qs = qs.filter(filt)
        if tech:
            # intersects skills array (icontains fallback)
            toks = [t.strip().lower() for t in tech.split(',') if t.strip()]
            for t in toks:
                qs = qs.filter(skills__icontains=[t])
        if location:
            qs = qs.filter(Q(location__city__icontains=location) | Q(location__country__icontains=location))
        if work_type:
            qs = qs.filter(work_type__iexact=work_type)
        if source:
            qs = qs.filter(source__name__iexact=source)
        if is_remote in ['true','1']:
            qs = qs.filter(Q(location__is_remote=True) | Q(work_type__iexact='remote'))
        if days and days.isdigit():
            since = timezone.now() - timedelta(days=int(days))
            qs = qs.filter(posted_at__gte=since)
        return qs

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from Oauth.permissions import RequiresPremiumTier
import requests
import uuid
import logging
from django.conf import settings
from Applications.models import Applications

logger = logging.getLogger(__name__)

class JobAgentApplyView(APIView):
    permission_classes = [IsAuthenticated, RequiresPremiumTier]

    def post(self, request, pk):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        try:
            job = Jobs.objects.get(id=pk)
        except Jobs.DoesNotExist:
            return Response({"detail": "Job not found"}, status=status.HTTP_404_NOT_FOUND)
            
        company = job.company
        
        # Try to extract recruiter email from job metadata
        recruiter_email = None
        if job.parsed_metadata and isinstance(job.parsed_metadata, dict):
            recruiter_email = job.parsed_metadata.get('recruiter_email') or job.parsed_metadata.get('contact_email')
            
        if not recruiter_email:
            # Fallback to company domain
            domain = company.website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0] if company.website else f"{company.slug}.com"
            recruiter_email = f"careers@{domain}"

        agent_payload = {
            "job_title": job.title,
            "company_name": company.name,
            "recruiter_email": recruiter_email,
            "user_name": f"{user.first_name} {user.last_name}".strip() or user.username,
            "cv_summary": "Auto-generated CV summary from profile.",
            "cv_file_path": None # Mock for now
        }
        
        email_system_url = getattr(settings, "EMAIL_INTELLIGENCE_URL", "http://127.0.0.1:8001")
        auto_apply_endpoint = f"{email_system_url}/webhook/agent/auto-apply"
        
        try:
            agent_response = requests.post(auto_apply_endpoint, json=agent_payload, timeout=30)
            if agent_response.status_code == 200:
                # Log Application
                Applications.objects.create(
                    id=uuid.uuid4(),
                    user=user,
                    company_name=company.name,
                    job_title=job.title,
                    status='applied',
                    applied_date=timezone.now().date(),
                    source='careerscope',
                    notes='Manually triggered Agent Apply.',
                    is_auto_applied=True
                )
                return Response({"status": "ok", "message": "Agent applied successfully."})
            else:
                return Response({"detail": "Agent apply failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Failed to manually agent-apply for {user.id}: {e}")
            return Response({"detail": "Agent apply request failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
