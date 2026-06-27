from django.db import models
from django.db.models import QuerySet, ExpressionWrapper, F, DurationField
from django.utils import timezone
from datetime import timedelta
import uuid
from django.contrib.postgres.fields import ArrayField
from django.conf import settings


class JobCollectionLogs(models.Model):
    id = models.UUIDField(primary_key=True)
    source = models.ForeignKey('JobSources', models.DO_NOTHING)
    status = models.CharField(max_length=20, blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    duration_seconds = models.IntegerField(blank=True, null=True)
    jobs_requested = models.IntegerField(blank=True, null=True)
    jobs_received = models.IntegerField(blank=True, null=True)
    jobs_created = models.IntegerField(blank=True, null=True)
    jobs_updated = models.IntegerField(blank=True, null=True)
    jobs_skipped = models.IntegerField(blank=True, null=True)
    errors_count = models.IntegerField(blank=True, null=True)
    error_details = models.JSONField(blank=True, null=True)
    collection_params = models.JSONField(blank=True, null=True)
    api_response_meta = models.JSONField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'job_collection_logs'


class JobInterests(models.Model):
    id = models.UUIDField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.DO_NOTHING)
    job = models.ForeignKey('Jobs', models.DO_NOTHING)
    interest_type = models.CharField(max_length=20, blank=True, null=True)
    clicked_url = models.TextField(blank=True, null=True)
    converted_to_application = models.BooleanField(blank=True, null=True)
    conversion_reminder_sent = models.BooleanField(blank=True, null=True)
    reminder_sent_at = models.DateTimeField(blank=True, null=True)
    source_page = models.CharField(max_length=255, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'job_interests'
        unique_together = (('user', 'job', 'interest_type'),)


class JobMatchScores(models.Model):
    id = models.UUIDField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.DO_NOTHING)
    job = models.ForeignKey('Jobs', models.DO_NOTHING)
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    skill_match_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    location_match_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    salary_match_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    experience_match_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    match_reasons = models.TextField(blank=True, null=True)  # This field type is a guess.
    concerns = models.TextField(blank=True, null=True)  # This field type is a guess.
    calculated_at = models.DateTimeField(blank=True, null=True)
    ai_model_used = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'job_match_scores'
        unique_together = (('user', 'job'),)


class SystemConfig(models.Model):
    """Data-driven operational thresholds."""
    key = models.CharField(max_length=255, primary_key=True)
    value = models.JSONField()
    description = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'system_config'


class JobProviders(models.Model):
    """
    Canonical capability profile for ATS engines or Job Boards.
    e.g. Greenhouse, Lever, LinkedIn.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(unique=True, max_length=100)
    authentication_method = models.CharField(max_length=50, blank=True, null=True)
    pagination_strategy = models.CharField(max_length=50, blank=True, null=True)
    incremental_sync_strategy = models.CharField(max_length=50, blank=True, null=True)
    supports_etag = models.BooleanField(default=False)
    supports_last_modified = models.BooleanField(default=False)
    supports_webhooks = models.BooleanField(default=False)
    supports_cursor_pagination = models.BooleanField(default=False)
    max_page_size = models.IntegerField(default=100)
    request_timeout = models.IntegerField(default=30)
    retry_policy = models.JSONField(blank=True, null=True)
    rate_limit_rpm = models.IntegerField(default=60)
    max_concurrent_workers = models.IntegerField(default=5)
    cooldown_seconds = models.IntegerField(default=0)
    status_429_history = models.JSONField(default=list, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'job_providers'


class JobSources(models.Model):
    name = models.CharField(unique=True, max_length=50)
    provider = models.ForeignKey(JobProviders, on_delete=models.SET_NULL, null=True, blank=True, related_name='sources')
    base_url = models.TextField()
    is_active = models.BooleanField(blank=True, null=True)
    verification_interval = models.DurationField(blank=True, null=True)
    expiration_interval = models.DurationField(blank=True, null=True)
    last_collection_at = models.DateTimeField(blank=True, null=True)
    total_jobs_collected = models.BigIntegerField(blank=True, null=True)
    success_rate = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'job_sources'


class ScrapeMetadata(models.Model):
    """
    Operational metadata for incremental, adaptive scheduling.
    Strictly separated from the core JobSources domain model.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.OneToOneField(JobSources, on_delete=models.CASCADE, related_name='scrape_metadata')
    tier = models.CharField(max_length=20, default='warm')  # hot, warm, cold, archive
    priority = models.IntegerField(default=50)  # 0-100 business importance
    health_score = models.IntegerField(default=100)  # 0-100 computed operational health
    failure_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    average_latency = models.DurationField(blank=True, null=True)
    last_successful_scrape = models.DateTimeField(blank=True, null=True)
    last_job_id_seen = models.CharField(max_length=255, blank=True, null=True)
    etag = models.CharField(max_length=255, blank=True, null=True)
    jobs_found_last_run = models.IntegerField(default=0)
    average_update_frequency = models.DurationField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'scrape_metadata'


class JobProcessingState(models.Model):
    """
    Operational state tracking for the AI Enrichment Pipeline.
    Tracks the execution status of various capabilities for a specific job.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.OneToOneField('Jobs', on_delete=models.CASCADE, related_name='processing_state')
    
    # Example format: {"skill_extraction": {"status": "COMPLETED", "retries": 0, "last_updated": "2026-06-27T12:00:00Z"}}
    capability_statuses = models.JSONField(default=dict)
    
    # Global state (e.g. IN_PROGRESS, COMPLETED, FAILED)
    overall_status = models.CharField(max_length=20, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'job_processing_state'


class JobEnrichments(models.Model):
    """
    Stores versioned AI outputs separate from operational state.
    Provides a complete history and confidence score for every enrichment.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey('Jobs', on_delete=models.CASCADE, related_name='enrichments')
    capability_name = models.CharField(max_length=100)  # e.g. 'skill_extraction'
    
    # The actual extracted data
    result = models.JSONField()
    
    # Versioning & Traceability
    model_name = models.CharField(max_length=100, blank=True, null=True)  # e.g. 'gemini-1.5-pro'
    model_version = models.CharField(max_length=50, blank=True, null=True)
    prompt_version = models.CharField(max_length=50, blank=True, null=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=4, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'job_enrichments'
        # A job shouldn't have multiple current active enrichments of the exact same capability
        # unless we explicitly model active vs history. We'll rely on the most recent row or a status field.
        # But we want history, so no unique_together.
        indexes = [
            models.Index(fields=['job', 'capability_name', '-created_at']),
        ]
        

class JobQuerySet(QuerySet):
    def active(self):
        return self.filter(status='active')

    def fresh(self):
        return self.filter(status='active', is_fresh=True)

    def hot(self, days=7, min_applies=5):
        """
        Hot jobs: active jobs with high apply_count in recent days
        """
        recent = timezone.now() - timedelta(days=days)
        
        return self.active().filter(
            apply_count__gte=min_applies,
            posted_at__gte=recent
        ).order_by('-apply_count', '-view_count', '-posted_at')

    def with_apply_velocity(self):
        """
        Annotate jobs with applies per day (optional enhancement)
        """
        days_since_posted = ExpressionWrapper(
            timezone.now() - F('posted_at'),
            output_field=DurationField()
        )
        return self.annotate(
            days_active=(days_since_posted / timedelta(days=1)) + 1,  # avoid div by zero
            apply_velocity=F('apply_count') / F('days_active')
        )


class Jobs(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_id = models.CharField(max_length=255)
    source = models.ForeignKey(JobSources, models.DO_NOTHING)
    company = models.ForeignKey('Companies.Companies', models.DO_NOTHING)
    location = models.ForeignKey('Personalization.Locations', models.DO_NOTHING)
    title = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    description = models.TextField()
    requirements = models.TextField(blank=True, null=True)
    benefits = models.TextField(blank=True, null=True)
    work_type = models.CharField(max_length=20, blank=True, null=True)
    experience_level = models.CharField(max_length=20, blank=True, null=True)
    is_remote = models.BooleanField(blank=True, null=True)
    is_hybrid = models.BooleanField(blank=True, null=True)
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    salary_currency = models.CharField(max_length=3, blank=True, null=True)
    salary_period = models.CharField(max_length=20, blank=True, null=True)
    skills = ArrayField(models.CharField(max_length=100), blank=True, null=True, default=list)
    technologies = ArrayField(models.CharField(max_length=100), blank=True, null=True, default=list)
    categories = ArrayField(models.CharField(max_length=100), blank=True, null=True, default=list)
    external_url = models.TextField()
    job_hash = models.CharField(max_length=64, unique=True, blank=True, null=True)  # SHA-256 Hash for deduplication
    apply_url = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, null=True)
    posted_at = models.DateTimeField()
    source_updated_at = models.DateTimeField()
    ingested_at = models.DateTimeField(blank=True, null=True)
    last_verified_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    is_fresh = models.BooleanField(blank=True, null=True)
    freshness_score = models.IntegerField(blank=True, null=True)
    last_freshness_update = models.DateTimeField(blank=True, null=True)
    view_count = models.IntegerField(blank=True, null=True)
    apply_count = models.IntegerField(blank=True, null=True)
    quality_score = models.DecimalField(max_digits=3, decimal_places=1, blank=True, null=True)
    raw_data = models.JSONField(blank=True, null=True)
    parsed_metadata = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    objects = JobQuerySet.as_manager()

    def update_freshness_score(self):
        """Calculate and update the freshness score based on posted date"""
        if not self.posted_at:
            self.freshness_score = 0
            self.is_fresh = False
            return

        # Make posted_at timezone-aware if it's naive
        posted_at = self.posted_at
        if timezone.is_naive(posted_at):
            posted_at = timezone.make_aware(posted_at)

        now = timezone.now()
        age_hours = (now - posted_at).total_seconds() / 3600

        # Calculate freshness score (100 for brand new, 0 for old)
        if age_hours < 24:  # Less than 1 day
            self.freshness_score = 100
        elif age_hours < 48:  # 1-2 days
            self.freshness_score = 75
        elif age_hours < 72:  # 2-3 days
            self.freshness_score = 50
        elif age_hours < 168:  # Less than 1 week
            self.freshness_score = 25
        else:
            self.freshness_score = 0

        # Mark as fresh if less than 48 hours old
        self.is_fresh = age_hours < 48
        self.last_freshness_update = now

    class Meta:
        managed = True
        db_table = 'jobs'
        unique_together = (('external_id', 'source'),)
