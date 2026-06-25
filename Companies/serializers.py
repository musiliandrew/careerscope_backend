from rest_framework import serializers
from .models import Companies, CompanyNews, TechTrend, MarketInsights, IndustryTrends
from Jobs.models import Jobs
import os
import re
from urllib.parse import urlparse


class CompanySerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()

    def get_logo_url(self, obj):
        # If model has a dedicated logo_url already validated, use it
        if obj.logo_url and "logo.dev" not in obj.logo_url:
            return obj.logo_url
        
        # 1. Resolve Domain
        domain = ""
        if obj.website:
            try:
                d = urlparse(obj.website).netloc
                if d: domain = d.replace("www.", "")
            except: pass
        
        if not domain:
            name_clean = re.sub(r'[^a-zA-Z0-9]', '', obj.name.lower().replace("research", "").replace("inc", "").replace("ltd", ""))
            domain = f"{name_clean}.com"
            
        token = os.getenv("LOGO_DEV_API_KEY", "sk_LI5k5ASSSTC6y9NDWm6Fsg")
        # logo.dev usually prefers 'pk_' keys for client-side images, but we'll try the provided one
        return f"https://img.logo.dev/{domain}?token={token}"

    class Meta:
        model = Companies
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "website",
            "logo_url",
            "industry",
            "company_size",
            "tier",
            "location",
            "founded_year",
            "careers_page_url",
            "tech_stack",
            "benefits",
            "valuation",
            "employee_count",
            "rating",
            "review_count",
            "is_actively_hiring",
            "avg_salary_min",
            "avg_salary_max",
            "active_jobs_count",
            "jobs_last_30_days",
            "created_at",
            "updated_at",
            "data_freshness_score",
        ]


class CompanyJobListSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    location_name = serializers.CharField(source="location.city", read_only=True)

    class Meta:
        model = Jobs
        fields = [
            "id",
            "title",
            "company",
            "company_name",
            "location",
            "location_name",
            "posted_at",
            "last_verified_at",
            "freshness_score",
            "is_fresh",
            "external_url",
            "apply_url",
            "work_type",
            "experience_level",
            "is_remote",
            "is_hybrid",
        ]


class CompanyListSerializer(serializers.ModelSerializer):
    formatted_salary_range = serializers.ReadOnlyField()
    logo_url = serializers.SerializerMethodField()

    def get_logo_url(self, obj):
        if obj.logo_url and "logo.dev" not in obj.logo_url:
            return obj.logo_url
        
        domain = ""
        if obj.website:
            try:
                d = urlparse(obj.website).netloc
                if d: domain = d.replace("www.", "")
            except: pass
            
        if not domain:
            name_clean = re.sub(r'[^a-zA-Z0-9]', '', obj.name.lower().replace("research", "").replace("inc", "").replace("ltd", ""))
            domain = f"{name_clean}.com"
            
        token = os.getenv("LOGO_DEV_API_KEY", "sk_LI5k5ASSSTC6y9NDWm6Fsg")
        return f"https://img.logo.dev/{domain}?token={token}"
    class Meta:
        model = Companies
        fields = [
            "id",
            "name",
            "slug",
            "logo_url",
            "industry",
            "company_size",
            "tier",
            "location",
            "is_actively_hiring",
            "active_jobs_count",
            "jobs_last_30_days",
            "formatted_salary_range",
        ]


class CompanyNewsSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    publishedAt = serializers.DateTimeField(source="published_date")
    sentimentScore = serializers.DecimalField(source="sentiment_score", max_digits=3, decimal_places=2, required=False)

    class Meta:
        model = CompanyNews
        fields = [
            "id",
            "company",
            "company_name",
            "title",
            "url",
            "source",
            "publishedAt",
            "news_type",
            "relevance",
            "summary",
            "sentimentScore",
            "keywords",
            "scraped_at",
            "is_featured",
            "view_count",
        ]

class TechTrendSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechTrend
        fields = '__all__'

class IndustryTrendSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndustryTrends
        fields = '__all__'

class MarketInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketInsights
        fields = '__all__'
