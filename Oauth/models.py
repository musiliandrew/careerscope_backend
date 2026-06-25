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


class UserSkills(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, null=True, blank=True, related_name="skills"
    )
    skill_name = models.CharField(max_length=100)
    skill_category = models.CharField(max_length=50, blank=True, null=True)
    proficiency_level = models.CharField(max_length=20, blank=True, null=True)
    years_of_experience = models.DecimalField(
        max_digits=3, decimal_places=1, blank=True, null=True
    )
    is_verified = models.BooleanField(blank=True, null=True)
    verified_by = models.CharField(max_length=100, blank=True, null=True)
    added_date = models.DateField(blank=True, null=True)
    last_used_date = models.DateField(blank=True, null=True)
    want_to_learn = models.BooleanField(default=False, blank=True)

    class Meta:
        managed = True
        db_table = "user_skills"
        unique_together = (("profile", "skill_name"),)


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


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="projects"
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    tools = models.CharField(max_length=255, blank=True, null=True)
    link = models.URLField(blank=True, null=True)

