import uuid

from django.db import models
from django.conf import settings

class LearningPathSteps(models.Model):
    id = models.UUIDField(primary_key=True)
    learning_path = models.ForeignKey('LearningPaths', models.DO_NOTHING)
    step_order = models.IntegerField()
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    resource_type = models.CharField(max_length=50, blank=True, null=True)
    resource_url = models.TextField(blank=True, null=True)
    estimated_hours = models.IntegerField(blank=True, null=True)
    is_completed = models.BooleanField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'learning_path_steps'


class LearningPaths(models.Model):
    id = models.UUIDField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.DO_NOTHING)
    target_job = models.ForeignKey('Jobs.Jobs', models.DO_NOTHING, blank=True, null=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    target_role = models.CharField(max_length=255, blank=True, null=True)
    estimated_hours = models.IntegerField(blank=True, null=True)
    difficulty_level = models.CharField(max_length=20, blank=True, null=True)
    completion_percentage = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'learning_paths'


class SkillGapAnalyses(models.Model):
    id = models.UUIDField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.DO_NOTHING)
    job = models.ForeignKey('Jobs.Jobs', models.DO_NOTHING, blank=True, null=True)
    match_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    missing_skills = models.TextField(blank=True, null=True)
    matching_skills = models.TextField(blank=True, null=True)
    nice_to_have_skills = models.TextField(blank=True, null=True)
    analysis_text = models.TextField(blank=True, null=True)
    recommendations = models.TextField(blank=True, null=True)
    estimated_time_to_ready = models.CharField(max_length=50, blank=True, null=True)
    analyzed_at = models.DateTimeField(blank=True, null=True)
    ai_model_used = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'skill_gap_analyses'


class UserCompanyFollows(models.Model):
    id = models.UUIDField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.DO_NOTHING)
    company = models.ForeignKey('Companies.Companies', models.DO_NOTHING)
    followed_at = models.DateTimeField(blank=True, null=True)
    notification_preference = models.CharField(max_length=20, blank=True, null=True)
    match_score = models.IntegerField(blank=True, null=True)
    last_interaction = models.DateTimeField(blank=True, null=True)
    interaction_count = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'user_company_follows'
        unique_together = (('user', 'company'),)

class Locations(models.Model):
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100)
    country_code = models.CharField(max_length=2)
    coordinates = models.JSONField(blank=True, null=True)
    is_remote = models.BooleanField(blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    total_jobs = models.IntegerField(blank=True, null=True)
    active_jobs = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'locations'
        unique_together = (('city', 'state', 'country'),)


class UserMemory(models.Model):
    class MemoryType(models.TextChoices):
        PROFILE_FACT = "profile_fact", "Profile fact"
        CAREER_GOAL = "career_goal", "Career goal"
        SKILL = "skill", "Skill"
        LEARNING_INTEREST = "learning_interest", "Learning interest"
        PREFERENCE = "preference", "Preference"
        NEGATIVE_PREFERENCE = "negative_preference", "Negative preference"
        BEHAVIORAL_SIGNAL = "behavioral_signal", "Behavioral signal"
        TRAIT = "trait", "Trait"
        PERSONA_SUMMARY = "persona_summary", "Persona summary"
        APPLICATION_SIGNAL = "application_signal", "Application signal"
        COMPANY_INTEREST = "company_interest", "Company interest"
        CONVERSATION = "conversation", "Conversation"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memories")
    memory_type = models.CharField(max_length=40, choices=MemoryType.choices)
    text = models.TextField()
    source = models.CharField(max_length=80, blank=True, null=True)
    source_object_type = models.CharField(max_length=100, blank=True, null=True)
    source_object_id = models.CharField(max_length=100, blank=True, null=True)
    confidence = models.DecimalField(max_digits=4, decimal_places=3, default=1)
    importance = models.DecimalField(max_digits=4, decimal_places=3, default=0.5)
    is_core = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(blank=True, null=True)
    valid_until = models.DateTimeField(blank=True, null=True)
    last_reinforced_at = models.DateTimeField(blank=True, null=True)
    qdrant_point_id = models.CharField(max_length=100, blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = "user_memories"
        indexes = [
            models.Index(fields=["user", "memory_type", "is_active"]),
            models.Index(fields=["source", "source_object_type", "source_object_id"]),
            models.Index(fields=["qdrant_point_id"]),
        ]

    def __str__(self):
        return f"{self.user_id}:{self.memory_type}:{self.text[:80]}"


class UserBehaviorEvent(models.Model):
    class EventType(models.TextChoices):
        JOB_VIEW = "job_view", "Job view"
        JOB_CLICK = "job_click", "Job click"
        JOB_SAVE = "job_save", "Job save"
        JOB_APPLY = "job_apply", "Job apply"
        JOB_DISMISS = "job_dismiss", "Job dismiss"
        COMPANY_FOLLOW = "company_follow", "Company follow"
        COMPANY_UNFOLLOW = "company_unfollow", "Company unfollow"
        SEARCH = "search", "Search"
        LEARNING_STEP_STARTED = "learning_step_started", "Learning step started"
        LEARNING_STEP_COMPLETED = "learning_step_completed", "Learning step completed"
        RECOMMENDATION_ACCEPTED = "recommendation_accepted", "Recommendation accepted"
        RECOMMENDATION_REJECTED = "recommendation_rejected", "Recommendation rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="behavior_events")
    event_type = models.CharField(max_length=50, choices=EventType.choices)
    object_type = models.CharField(max_length=80, blank=True, null=True)
    object_id = models.CharField(max_length=100, blank=True, null=True)
    event_value = models.DecimalField(max_digits=8, decimal_places=3, blank=True, null=True)
    context = models.JSONField(blank=True, null=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = "user_behavior_events"
        indexes = [
            models.Index(fields=["user", "event_type", "created_at"]),
            models.Index(fields=["object_type", "object_id"]),
        ]


class UserTrait(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="traits")
    trait_key = models.CharField(max_length=100)
    trait_value = models.CharField(max_length=255)
    confidence = models.DecimalField(max_digits=4, decimal_places=3, default=0.5)
    evidence_count = models.PositiveIntegerField(default=1)
    last_evidence_at = models.DateTimeField(blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = "user_traits"
        unique_together = (("user", "trait_key", "trait_value"),)
        indexes = [
            models.Index(fields=["user", "trait_key"]),
        ]
