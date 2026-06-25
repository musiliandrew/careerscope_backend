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


class JobSources(models.Model):
    name = models.CharField(unique=True, max_length=50)
    base_url = models.TextField()
    is_active = models.BooleanField(blank=True, null=True)
    rate_limit_per_minute = models.IntegerField(blank=True, null=True)
    last_collection_at = models.DateTimeField(blank=True, null=True)
    total_jobs_collected = models.BigIntegerField(blank=True, null=True)
    success_rate = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'job_sources'
        

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
