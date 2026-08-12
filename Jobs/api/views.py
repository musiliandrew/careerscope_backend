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

        # Exclude non-job site navigation headers and junk titles
        junk_patterns = [
            'Careers', 'Jobs search', 'View Openings', 'Cookie Settings', 'Right to Work',
            'ATTACHMENTS (NO PAY)', 'ATTACHMENTS', 'Internal Applications', 'Late preparation',
            'Hiring', 'Founders', 'Work', 'Lecturers', 'Volunteers', 'Contractual opportunities',
            'Internships', 'Unpaid', 'Undergraduate Program', 'Graduate Trainee Program',
            'Management Trainee', 'SHARE YOUR RESUME/CV', 'Remote Hiring Guide', 'Hiring Tips',
            'Read our FAQ', 'FAQ', 'FAQs', 'Frequently Asked Questions', 'Jobs', 'Company overview',
            'About our company', 'About Us', 'What we do', 'Hiring process', 'How we hire', 'People',
            'Our Team', 'Accommodation', 'Accessibility', 'Legal', 'Privacy Policy', 'Terms of Service',
            'Contact us', 'Contact', 'Get in touch', 'Roles', 'Perks', 'Benefits', 'Overview', 'Home'
        ]
        for pattern in junk_patterns:
            qs = qs.exclude(title__iexact=pattern).exclude(title__istartswith=f"{pattern} |")

        company = self.request.query_params.get('company')
        if not company:
            qs = qs.exclude(company__tier__in=['faang_plus', 'african_tech'])
            
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
        if company:
            qs = qs.filter(Q(company__name__icontains=company) | Q(company__slug__icontains=company))
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
        else:
            # Strictly filter jobs to the last 7 days
            since = timezone.now() - timedelta(days=7)
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
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        if not user or not user.is_authenticated:
            return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        # Try fetching job safely (handling both UUID and string IDs)
        job = None
        try:
            job = Jobs.objects.filter(id=pk).first()
        except Exception:
            job = Jobs.objects.filter(Q(title__icontains=pk) | Q(slug__icontains=pk)).first()
        
        company_name = "Tech Employer"
        job_title = "Software Engineering Role"

        if job:
            job_title = job.title
            if job.company:
                company_name = job.company.name
            elif getattr(job, 'company_name', None):
                company_name = job.company_name

        # 1. Log Application in DB immediately
        app = Applications.objects.create(
            id=uuid.uuid4(),
            user=user,
            company_name=company_name,
            job_title=job_title,
            status='applied',
            applied_date=timezone.now().date(),
            source='careerscope_agent',
            notes='[Autonomous Agent] Dispatched via CareerScoper Autonomous Agent Workflow.',
            is_auto_applied=True
        )

        # 2. Async dispatch to email intelligence microservice if available
        import threading
        def async_agent_dispatch():
            email_system_url = getattr(settings, "EMAIL_INTELLIGENCE_URL", "http://127.0.0.1:8001")
            auto_apply_endpoint = f"{email_system_url}/webhook/agent/auto-apply"
            clean_domain = company_name.lower().replace(" ", "").replace(",", "").replace(".", "")
            recruiter_email = f"careers@{clean_domain}.com"
            agent_payload = {
                "job_title": job_title,
                "company_name": company_name,
                "recruiter_email": recruiter_email,
                "user_name": f"{user.first_name} {user.last_name}".strip() or user.username,
                "application_id": str(app.id)
            }
            try:
                requests.post(auto_apply_endpoint, json=agent_payload, timeout=5)
            except Exception as e:
                logger.warning(f"Async agent dispatch warning for {user.id}: {e}")

        threading.Thread(target=async_agent_dispatch).start()

        return Response({
            "status": "ok",
            "application_id": str(app.id),
            "job_title": job_title,
            "company_name": company_name,
            "message": f"Autonomous Agent applied to {job_title} at {company_name}!"
        }, status=status.HTTP_200_OK)
