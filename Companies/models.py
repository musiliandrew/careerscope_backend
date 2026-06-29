from django.db import models
import uuid
from django.contrib.postgres.fields import ArrayField

class Companies(models.Model):
    # Company size choices
    SIZE_CHOICES = [
        ('1-10', '1-10 employees'),
        ('11-50', '11-50 employees'),
        ('51-200', '51-200 employees'),
        ('201-500', '201-500 employees'),
        ('501-1000', '501-1000 employees'),
        ('1001-5000', '1001-5000 employees'),
        ('5000+', '5000+ employees'),
    ]

    # Company tier choices
    TIER_CHOICES = [
        ('faang_plus', 'FAANG+'),
        ('ai_unicorn', 'AI Unicorn'),
        ('unicorn', 'Unicorn'),
        ('african_tech', 'African Tech'),
        ('enterprise', 'Enterprise'),
        ('startup', 'Startup'),
        ('scale_up', 'Scale-up'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.CharField(unique=True, max_length=255)
    description = models.TextField(blank=True, null=True)
    website = models.TextField(blank=True, null=True)
    logo_url = models.TextField(blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    company_size = models.CharField(max_length=50, blank=True, null=True)
    tier = models.CharField(max_length=50, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    founded_year = models.IntegerField(blank=True, null=True)
    careers_page_url = models.TextField(blank=True, null=True)
    tech_stack = ArrayField(models.CharField(max_length=100), blank=True, null=True, default=list)
    benefits = ArrayField(models.CharField(max_length=200), blank=True, null=True, default=list)
    valuation = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    employee_count = models.IntegerField(blank=True, null=True)
    rating = models.DecimalField(max_digits=2, decimal_places=1, blank=True, null=True)
    review_count = models.IntegerField(blank=True, null=True)
    is_actively_hiring = models.BooleanField(blank=True, null=True)
    avg_salary_min = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    avg_salary_max = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_monitored = models.BooleanField(blank=True, null=True)
    last_job_scrape = models.DateTimeField(blank=True, null=True)
    last_news_check = models.DateTimeField(blank=True, null=True)
    total_jobs_posted = models.IntegerField(blank=True, null=True)
    active_jobs_count = models.IntegerField(blank=True, null=True)
    jobs_last_30_days = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    data_freshness_score = models.IntegerField(blank=True, null=True)

    @property
    def formatted_salary_range(self):
        """Format salary range as a string"""
        if self.avg_salary_min and self.avg_salary_max:
            return f"${self.avg_salary_min:,.0f} - ${self.avg_salary_max:,.0f}"
        elif self.avg_salary_min:
            return f"${self.avg_salary_min:,.0f}+"
        elif self.avg_salary_max:
            return f"Up to ${self.avg_salary_max:,.0f}"
        return "Not specified"

    @property
    def match_score_for_user(self):
        """Calculate match score for user (placeholder)"""
        # TODO: Implement actual matching logic based on user profile
        return 0

    class Meta:
        managed = True
        db_table = 'companies'


class CompanyMonitoringJobs(models.Model):
    id = models.UUIDField(primary_key=True)
    company = models.ForeignKey(Companies, models.DO_NOTHING, blank=True, null=True)
    job_type = models.CharField(max_length=30, blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    duration_seconds = models.IntegerField(blank=True, null=True)
    items_processed = models.IntegerField(blank=True, null=True)
    items_created = models.IntegerField(blank=True, null=True)
    items_updated = models.IntegerField(blank=True, null=True)
    errors_count = models.IntegerField(blank=True, null=True)
    parameters = models.JSONField(blank=True, null=True)
    results = models.JSONField(blank=True, null=True)
    error_details = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'company_monitoring_jobs'


class CompanyNews(models.Model):
    id = models.UUIDField(primary_key=True)
    company = models.ForeignKey(Companies, models.DO_NOTHING)
    title = models.CharField(max_length=500)
    url = models.TextField()
    source = models.CharField(max_length=100, blank=True, null=True)
    published_date = models.DateTimeField()
    news_type = models.CharField(max_length=20, blank=True, null=True)
    relevance = models.CharField(max_length=20, blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    sentiment_score = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    keywords = models.TextField(blank=True, null=True)  # This field type is a guess.
    scraped_at = models.DateTimeField(blank=True, null=True)
    is_featured = models.BooleanField(blank=True, null=True)
    view_count = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'company_news'

class IndustryTrends(models.Model):
    id = models.UUIDField(primary_key=True)
    industry = models.CharField(max_length=100)
    trend_type = models.CharField(max_length=20, blank=True, null=True)
    metric_name = models.CharField(max_length=200)
    current_value = models.DecimalField(max_digits=15, decimal_places=2)
    previous_value = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    change_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    period_start = models.DateField()
    period_end = models.DateField()
    calculation_date = models.DateTimeField(blank=True, null=True)
    data_source = models.CharField(max_length=100, blank=True, null=True)
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'industry_trends'
        unique_together = (('industry', 'trend_type', 'metric_name', 'period_end'),)

class MarketInsights(models.Model):
    id = models.UUIDField(primary_key=True)
    insight_type = models.CharField(max_length=30, blank=True, null=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    metric_value = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    metric_unit = models.CharField(max_length=50, blank=True, null=True)
    trend_data = models.JSONField(blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    time_period = models.CharField(max_length=100, blank=True, null=True)
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    data_sources = models.TextField(blank=True, null=True)  # This field type is a guess.
    calculation_date = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'market_insights'


class TechTrend(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50) # e.g., Language, Framework, Cloud, AI-Tool
    popularity_score = models.FloatField(default=0) # 0-100
    growth_percentage = models.FloatField(default=0) 
    demand_rank = models.IntegerField(default=0) # Rank based on job postings
    social_volume = models.IntegerField(default=0) # Mentions in news/social
    sentiment_score = models.FloatField(default=0.5) # 0 to 1
    last_updated = models.DateTimeField(auto_now=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = 'tech_trends'

class TechTrendNews(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tech = models.ForeignKey(TechTrend, on_delete=models.CASCADE, related_name='news')
    title = models.CharField(max_length=500)
    url = models.TextField()
    source = models.CharField(max_length=100)
    published_at = models.DateTimeField()
    snippet = models.TextField(blank=True, null=True)
    sentiment = models.FloatField(default=0.5)

    class Meta:
        managed = True
        db_table = 'tech_trend_news'

# ============================================
# DYNAMIC COMPANY INTELLIGENCE MODELS
# ============================================

class CompanySource(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Companies, on_delete=models.CASCADE, related_name='sources')
    url = models.TextField(unique=True)
    source_type = models.CharField(max_length=50) # e.g., 'engineering_blog', 'careers', 'github', 'news'
    is_active = models.BooleanField(default=True)
    last_crawled_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'company_sources'

class CompanyDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Companies, on_delete=models.CASCADE, related_name='documents')
    source = models.ForeignKey(CompanySource, on_delete=models.SET_NULL, null=True, blank=True)
    source_url = models.TextField()
    content_raw = models.TextField()
    content_markdown = models.TextField(blank=True, null=True)
    crawl_timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'company_documents'

class CompanyKnowledge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Companies, on_delete=models.CASCADE, related_name='knowledge')
    document = models.ForeignKey(CompanyDocument, on_delete=models.SET_NULL, null=True, blank=True)
    fact_type = models.CharField(max_length=100) # e.g., 'technology_used', 'culture_principle', 'benefit'
    content = models.TextField() # Structured fact
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2) # 0.00 to 1.00
    model_version = models.CharField(max_length=100) # e.g., 'gemini-1.5-pro'
    evidence_reference = models.TextField(blank=True, null=True) # Direct quote or pointer
    extracted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'company_knowledge'

class CompanyObservation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Companies, on_delete=models.CASCADE, related_name='observations')
    observation_type = models.CharField(max_length=100) # e.g., 'hiring_velocity', 'tech_adoption'
    value = models.JSONField() # Flexible payload for time-series data
    observed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'company_observations'