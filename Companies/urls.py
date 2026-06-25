from django.urls import path
from .views import (
    CompaniesListView,
    CompanyDetailView,
    CompanyNewsListView,
    CompanyJobsListView,
    CompaniesFeedView,
    CompanyFollowView,
    TechTrendsView,
    RefreshTrendsView,
    GlobalCompanyNewsView,
    MarketInsightsView,
)

urlpatterns = [
    path("feed/", CompaniesFeedView.as_view(), name="companies_feed"),
    path("", CompaniesListView.as_view(), name="companies_list"),
    path("<uuid:id>/", CompanyDetailView.as_view(), name="company_detail"),
    path("<uuid:company_id>/news/", CompanyNewsListView.as_view(), name="company_news"),
    path("<uuid:company_id>/jobs/", CompanyJobsListView.as_view(), name="company_jobs"),
    path("<uuid:company_id>/follow/", CompanyFollowView.as_view(), name="company_follow"),
    path("tech-trends/", TechTrendsView.as_view(), name="tech_trends"),
    path("trends/refresh/", RefreshTrendsView.as_view(), name="refresh_trends"),
    path("news/all/", GlobalCompanyNewsView.as_view(), name="global_company_news"),
    path("market-insights/", MarketInsightsView.as_view(), name="market_insights"),
]
