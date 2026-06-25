from rest_framework import generics, filters
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Q, Case, When, Value, IntegerField
from django.utils import timezone
from django.db import DatabaseError
from django.db.utils import OperationalError

from .models import Companies, CompanyNews, CompanyMonitoringJobs, TechTrend, MarketInsights, IndustryTrends
from Personalization.models import UserCompanyFollows
from .serializers import (
    CompanySerializer,
    CompanyListSerializer,
    CompanyNewsSerializer,
    CompanyJobListSerializer,
    TechTrendSerializer,
    MarketInsightSerializer,
    IndustryTrendSerializer,
)
from Intelligence.Trends.analyzer import synthesize_tech_commentary, analyze_tech_trends
from Jobs.models import Jobs


class CompaniesListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CompanyListSerializer
    def get_queryset(self):
        # Prioritize Tiers: FAANG+ > AI Unicorn > Unicorn > African Tech > others
        qs = Companies.objects.annotate(
            tier_priority=Case(
                When(tier='faang_plus', then=Value(1)),
                When(tier='ai_unicorn', then=Value(2)),
                When(tier='unicorn', then=Value(3)),
                When(tier='african_tech', then=Value(4)),
                default=Value(10),
                output_field=IntegerField(),
            )
        ).order_by('tier_priority', '-updated_at')
        
        tier = self.request.query_params.get('tier')
        industry = self.request.query_params.get('industry')
        hiring = self.request.query_params.get('hiring')
        if tier:
            qs = qs.filter(tier=tier)
        if industry:
            qs = qs.filter(industry=industry)
        if hiring in ['true', '1']:
            qs = qs.filter(is_actively_hiring=True)
        return qs


class CompanyDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = CompanySerializer
    queryset = Companies.objects.all()
    lookup_field = 'id'


class CompanyNewsListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CompanyNewsSerializer

    def get_queryset(self):
        company_id = self.kwargs.get('company_id')
        return CompanyNews.objects.filter(company_id=company_id).order_by('-published_date', '-scraped_at')


class CompanyJobsListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CompanyJobListSerializer
    class Pagination(PageNumberPagination):
        page_size = 20
        page_size_query_param = 'page_size'
        max_page_size = 100
    pagination_class = Pagination

    def get_queryset(self):
        company_id = self.kwargs.get('company_id')
        qs = Jobs.objects.filter(company_id=company_id).order_by('-posted_at')
        fresh = self.request.query_params.get('fresh')
        days = self.request.query_params.get('days')
        q = self.request.query_params.get('q')
        if fresh in ['true', '1']:
            qs = qs.filter(is_fresh=True)
        if days and days.isdigit():
            from django.utils import timezone
            from datetime import timedelta
            since = timezone.now() - timedelta(days=int(days))
            qs = qs.filter(posted_at__gte=since)
        if q:
            qs = qs.filter(title__icontains=q)
        return qs


class CompaniesFeedPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class CompaniesFeedView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    pagination_class = CompaniesFeedPagination

    def get(self, request, *args, **kwargs):
        # 1. Prioritize Tiers for the main feed
        qs = Companies.objects.annotate(
            tier_priority=Case(
                When(tier='faang_plus', then=Value(1)),
                When(tier='ai_unicorn', then=Value(2)),
                When(tier='unicorn', then=Value(3)),
                When(tier='african_tech', then=Value(4)),
                default=Value(10),
                output_field=IntegerField(),
            )
        ).order_by('tier_priority', '-updated_at')

        q = request.query_params.get('q')
        industry = request.query_params.get('industry')
        is_hiring = request.query_params.get('is_hiring')
        following_only = request.query_params.get('following') in ['true', '1']

        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(industry__icontains=q))
        if industry:
            qs = qs.filter(industry__iexact=industry)
        if is_hiring in ['true', '1']:
            qs = qs.filter(is_actively_hiring=True)

        req_user = getattr(request, 'user', None)
        api_user = req_user if req_user and getattr(req_user, 'is_authenticated', False) else None

        if following_only:
            if not api_user:
                # No auth -> no follows
                qs = qs.none()
            else:
                followed_ids = UserCompanyFollows.objects.filter(user=api_user).values_list('company_id', flat=True)
                qs = qs.filter(id__in=followed_ids)

        page = self.paginate_queryset(qs)
        companies_list = page if page is not None else qs

        # Precompute stats
        now = timezone.now()
        hiring_count = Companies.objects.filter(is_actively_hiring=True).count()
        total_open_roles = Jobs.objects.filter(status='active').count()
        monitored_count = Companies.objects.filter(companymonitoringjobs__isnull=False).distinct().count()
        following_count = None
        if api_user:
            following_count = UserCompanyFollows.objects.filter(user=api_user).count()

        # Facets
        industries = list(Companies.objects.exclude(industry__isnull=True).exclude(industry='').values_list('industry', flat=True).distinct())

        serializer = CompanyListSerializer(companies_list, many=True, context={'request': request})
        companies_data = serializer.data

        for i, company_data in enumerate(companies_data):
            c = companies_list[i]
            # recent news (up to 3)
            news_qs = CompanyNews.objects.filter(company_id=c.id).order_by('-published_date', '-scraped_at')[:3]
            recent_news = [
                {
                    "title": n.title,
                    "url": n.url,
                    "source": getattr(n, 'source', None),
                    "date": getattr(n, 'published_date', None),
                }
                for n in news_qs
            ]

            # recent jobs (up to 3)
            jobs_qs = Jobs.objects.filter(company_id=c.id, status='active').order_by('-posted_at')[:3]
            job_openings = [
                {
                    "title": j.title,
                    "location": getattr(j.location, 'city', None),
                    "type": j.work_type,
                    "salary": (f"${int(j.salary_min):,} - ${int(j.salary_max):,}" if j.salary_min and j.salary_max else None),
                    "url": j.apply_url or j.external_url,
                    "postedDate": j.posted_at,
                }
                for j in jobs_qs
            ]

            # Match frontend CamelCase expectations
            company_data["logoUrl"] = company_data.get("logo_url")
            company_data["techStack"] = getattr(c, 'tech_stack', []) or []
            company_data["isFollowing"] = UserCompanyFollows.objects.filter(user=api_user, company_id=c.id).exists() if api_user else False
            company_data["openRoles"] = Jobs.objects.filter(company_id=c.id, status='active').count()
            company_data["isHiring"] = company_data.get("is_actively_hiring", False)
            company_data["monitoringActive"] = CompanyMonitoringJobs.objects.filter(company_id=c.id).exists()
            company_data["matchScore"] = 45 

            company_data["recentNews"] = recent_news
            company_data["jobOpenings"] = job_openings
            company_data["careerPage"] = getattr(c, 'careers_page_url', None)
            company_data["avgSalary"] = company_data.get("formatted_salary_range")

        payload = {
            "companies": companies_data,
            "total": qs.count(),
            "industries": industries,
            "tiers": ["FAANG+", "AI Unicorn", "Unicorn", "African Tech", "Startup", "Enterprise"],
            "stats": {
                "followingCount": following_count or 0,
                "hiringCount": hiring_count,
                "monitoredCount": monitored_count,
                "totalOpenRoles": total_open_roles,
                "averageRating": 4.2,
            },
            "pagination": None,
            "timestamp": now,
        }

        if page is not None:
            return self.get_paginated_response(payload)
        return Response(payload)


class CompanyFollowView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        company_id = self.kwargs.get('company_id')
        try:
            company = Companies.objects.get(id=company_id)
        except Companies.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        api_user = request.user
        obj, created = UserCompanyFollows.objects.get_or_create(user=api_user, company=company)
        count = UserCompanyFollows.objects.filter(user=api_user).count()
        return Response({"followed": True, "created": created, "followingCount": count}, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        company_id = self.kwargs.get('company_id')
        try:
            company = Companies.objects.get(id=company_id)
        except Companies.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        api_user = request.user
        UserCompanyFollows.objects.filter(user=api_user, company=company).delete()
        count = UserCompanyFollows.objects.filter(user=api_user).count()
        return Response({"followed": False, "followingCount": count}, status=status.HTTP_200_OK)

class GlobalCompanyNewsView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CompanyNewsSerializer
    queryset = CompanyNews.objects.all().order_by('-published_date', '-scraped_at')
    
    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(summary__icontains=q))
        return qs
class TechTrendsView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        # Optional: Trigger refresh if stale (e.g., more than 6 hours)
        # For this demo, we'll just return what's in DB
        trends = TechTrend.objects.filter(is_active=True).order_by('-popularity_score')
        
        # Categorize
        categories = {}
        for t in trends:
            cat = t.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(TechTrendSerializer(t).data)

        # Get top movers
        movers = trends.order_by('-growth_percentage')[:5]

        return Response({
            "categories": categories,
            "top_movers": TechTrendSerializer(movers, many=True).data,
            "commentary": synthesize_tech_commentary(),
            "timestamp": timezone.now()
        })

class RefreshTrendsView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    def post(self, request):
        count = analyze_tech_trends()
        return Response({"status": "success", "processed": count})

class MarketInsightsView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    
    def get(self, request, *args, **kwargs):
        # 1. Fetch Latest Insights
        insights = MarketInsights.objects.all().order_by('-calculation_date')[:10]
        
        # 2. Fetch High-Level Industry Trends
        trends = IndustryTrends.objects.all().order_by('-calculation_date')
        
        # 3. Group trends if needed or just return raw
        # Let's say we group by industry
        industry_trends = {}
        for t in trends:
            if t.industry not in industry_trends:
                industry_trends[t.industry] = []
            industry_trends[t.industry].append(IndustryTrendSerializer(t).data)
            
        return Response({
            "insights": MarketInsightSerializer(insights, many=True).data,
            "industry_trends": industry_trends,
            "timestamp": timezone.now()
        })
