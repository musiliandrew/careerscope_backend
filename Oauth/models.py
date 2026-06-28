from django.db import models
from django.conf import settings
from uuid import uuid4


class Profile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    portfolio = models.URLField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=20, blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    github_url = models.URLField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    avatar_id = models.CharField(max_length=100, blank=True, null=True)
    resume_url = models.CharField(max_length=255, blank=True, null=True)
    resume_data = models.JSONField(blank=True, null=True)

    # Gmail / Calendar sync configuration
    gmail_credentials = models.JSONField(blank=True, null=True)
    gmail_sync_enabled = models.BooleanField(default=False)
    gmail_last_sync = models.DateTimeField(blank=True, null=True)
    calendar_credentials = models.JSONField(blank=True, null=True)
    calendar_sync_enabled = models.BooleanField(default=False)
    calendar_last_sync = models.DateTimeField(blank=True, null=True)

    # OAuth and account metadata migrated from the old Oauth.Users table.
    google_id = models.CharField(max_length=255, blank=True, null=True)
    github_id = models.CharField(max_length=255, blank=True, null=True)
    email_verified = models.BooleanField(blank=True, null=True)
    email_verification_token = models.TextField(blank=True, null=True)
    last_login_at = models.DateTimeField(blank=True, null=True)
    subscription_tier = models.CharField(max_length=50, blank=True, null=True, default="free")
    subscription_status = models.CharField(max_length=50, blank=True, null=True, default="active")
    bio = models.TextField(blank=True, null=True)


class JobPreferences(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    profile = models.ForeignKey(
        to=Profile, on_delete=models.CASCADE, related_name="preferences"
    )
    target_role = models.TextField(blank=True, null=True)
    preferred_work_type = models.TextField(blank=True, null=True)
    preferred_locations = models.TextField(blank=True, null=True)
    target_salary_min = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    target_salary_max = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    available_from = models.DateTimeField(blank=True, null=True)
    notice_period = models.CharField(max_length=20, blank=True, null=True)
    company_types = models.TextField(blank=True, null=True)


class CareerGoals(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    profile = models.ForeignKey(
        to=Profile, on_delete=models.CASCADE, related_name="career_goals"
    )
    looking_for = models.TextField(blank=True, null=True)
    deal_breakers = models.TextField(blank=True, null=True)
    nice_to_haves = models.TextField(blank=True, null=True)


class EducationBackground(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    institution = models.CharField(max_length=100)
    joined = models.DateField(blank=True, null=True)
    done = models.BooleanField(default=True)
    completed = models.DateField(blank=True, null=True)
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="education_background"
    )
    certification = models.CharField(max_length=50, blank=True, null=True)
    field_of_learning = models.CharField(max_length=100, blank=True, null=True)

class Evidence(models.Model):
    class EvidenceType(models.TextChoices):
        RESUME_BULLET = "resume_bullet", "Resume Bullet"
        GITHUB_REPO = "github_repo", "GitHub Repository"
        PORTFOLIO_PROJECT = "portfolio_project", "Portfolio Project"
        WORK_EXPERIENCE = "work_experience", "Work Experience"
        CERTIFICATION = "certification", "Certification"
        ASSESSMENT = "assessment", "Assessment"
        RECOMMENDATION = "recommendation", "Recommendation"
        INTERVIEW_FEEDBACK = "interview_feedback", "Interview Feedback"
        APPLICATION_OUTCOME = "application_outcome", "Application Outcome"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid4)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="evidence")
    evidence_type = models.CharField(max_length=50, choices=EvidenceType.choices)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = "evidence"


class Insight(models.Model):
    class InsightType(models.TextChoices):
        STRENGTH = "strength", "Strength"
        WEAKNESS = "weakness", "Weakness"
        OPPORTUNITY = "opportunity", "Opportunity"
        RISK = "risk", "Risk"
        RECOMMENDATION = "recommendation", "Recommendation"
        OBSTACLE = "obstacle", "Obstacle"

    id = models.UUIDField(primary_key=True, default=uuid4)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="insights")
    insight_type = models.CharField(max_length=50, choices=InsightType.choices)
    description = models.TextField()
    source = models.CharField(max_length=255, blank=True, null=True)
    severity = models.CharField(max_length=50, blank=True, null=True)
    confidence = models.DecimalField(max_digits=4, decimal_places=3, default=0.5)
    affected_companies = models.JSONField(blank=True, null=True, default=list)
    affected_roles = models.JSONField(blank=True, null=True, default=list)
    recommended_actions = models.JSONField(blank=True, null=True, default=list)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = "insights"



class UserSkills(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, null=True, blank=True, related_name="skills"
    )
    skill_name = models.CharField(max_length=100)
    skill_category = models.CharField(max_length=50, blank=True, null=True)
    proficiency_level = models.CharField(max_length=20, blank=True, null=True)
    proficiency_score = models.IntegerField(blank=True, null=True)  # 0-100 scale
    confidence_score = models.DecimalField(max_digits=4, decimal_places=3, blank=True, null=True)
    years_of_experience = models.DecimalField(max_digits=3, decimal_places=1, blank=True, null=True)
    is_verified = models.BooleanField(blank=True, null=True)
    verified_by = models.CharField(max_length=100, blank=True, null=True)
    verification_source = models.CharField(max_length=255, blank=True, null=True)
    last_verified_at = models.DateTimeField(blank=True, null=True)
    evidence = models.ManyToManyField(Evidence, related_name="skills_supported", blank=True)
    added_date = models.DateField(blank=True, null=True)
    last_used_date = models.DateField(blank=True, null=True)
    want_to_learn = models.BooleanField(default=False, blank=True)
    metadata = models.JSONField(blank=True, null=True, default=dict)

    class Meta:
        managed = True
        db_table = "user_skills"
        unique_together = (("profile", "skill_name"),)


class SkillProgress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    user_skill = models.ForeignKey(UserSkills, on_delete=models.CASCADE, related_name="progress_history")
    previous_proficiency = models.IntegerField(blank=True, null=True)
    new_proficiency = models.IntegerField()
    reason = models.TextField(blank=True, null=True)
    evidence = models.ForeignKey(Evidence, on_delete=models.SET_NULL, blank=True, null=True, related_name="skill_progress_events")
    metadata = models.JSONField(blank=True, null=True, default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = "skill_progress"



class WorkExperience(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="experiences"
    )
    title = models.CharField(max_length=100)
    company = models.CharField(max_length=100)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    skills_demonstrated = models.ManyToManyField(UserSkills, related_name="work_experiences", blank=True)
    technologies_used = models.TextField(blank=True, null=True)
    achievements = models.TextField(blank=True, null=True)
    business_impact = models.TextField(blank=True, null=True)
    evidence = models.ManyToManyField(Evidence, related_name="work_experiences_supported", blank=True)
    metadata = models.JSONField(blank=True, null=True, default=dict)


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="projects"
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    tools = models.CharField(max_length=255, blank=True, null=True)
    skills_demonstrated = models.ManyToManyField(UserSkills, related_name="projects_demonstrated", blank=True)
    outcomes = models.TextField(blank=True, null=True)
    measurable_impact = models.TextField(blank=True, null=True)
    evidence = models.ManyToManyField(Evidence, related_name="projects_supported", blank=True)
    link = models.URLField(blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True, default=dict)


class DecisionLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="decision_history")
    decision_type = models.CharField(max_length=150)
    inputs = models.JSONField(default=dict)
    conclusion = models.JSONField(default=dict)
    reasoning_process = models.TextField(blank=True, null=True)
    confidence = models.DecimalField(max_digits=4, decimal_places=3, default=0.0)
    evidence_referenced = models.ManyToManyField(Evidence, related_name="decisions_supported", blank=True)
    strategy_used = models.CharField(max_length=50, blank=True, null=True)
    model_version = models.CharField(max_length=100, blank=True, null=True)
    twin_version_id = models.CharField(max_length=100, blank=True, null=True) # E.g., snapshot hash
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = "decision_logs"
