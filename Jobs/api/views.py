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
        qs = Jobs.objects.filter(status='active').order_by('-posted_at')
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
            from DataIngestion.Jobs.filters import ROLE_KEYWORDS
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
