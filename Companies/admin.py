from django.contrib import admin
from .models import Companies, CompanyNews, CompanyMonitoringJobs

@admin.register(Companies)
class CompaniesAdmin(admin.ModelAdmin):
    list_display = ("name", "tier", "website", "is_actively_hiring")
    search_fields = ("name", "website", "industry", "location")
    list_filter = ("tier", "is_actively_hiring", "industry")
    prepopulated_fields = {"slug": ("name",)}
    fields = (
        "name",
        "slug",
        "tier",
        "website",
        "industry",
        "company_size",
        "location",
        "founded_year",
        "is_actively_hiring",
    )


@admin.register(CompanyNews)
class CompanyNewsAdmin(admin.ModelAdmin):
    list_display = ("company", "title", "source", "published_date", "url")
    search_fields = ("title", "url", "source")
    list_filter = ("source", "published_date")


@admin.register(CompanyMonitoringJobs)
class CompanyMonitoringJobsAdmin(admin.ModelAdmin):
    list_display = (
        "company",
        "job_type",
        "status",
        "started_at",
        "completed_at",
        "items_processed",
        "errors_count",
    )
    search_fields = ("company__name", "job_type", "status")
    list_filter = ("job_type", "status")
