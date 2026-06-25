from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Profile,
    EducationBackground,
    UserSkills,
    WorkExperience,
    Project,
    JobPreferences,
    CareerGoals,
)
from .backblaze import blaze_client

User = get_user_model()


class RegSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email", "password"]


class LoginSerializer(Serializer):
    username = serializers.CharField(max_length=100)
    password = serializers.CharField(max_length=100)


class ExchangeSerializer(Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(required=False, allow_blank=True)


# Profile patching serializers


class ProfileSerializer1(ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "full_name",
            "portfolio",
            "bio",
            "phone_number",
            "country",
            "linkedin_url",
            "github_url",
            "location",
        ]


class AvatarImageSerializer(serializers.Serializer):
    image = serializers.FileField()


class EducationSerializer(ModelSerializer):
    class Meta:
        model = EducationBackground
        fields = [
            "institution",
            "joined",
            "completed",
            "certification",
            "field_of_learning",
        ]


class SkillSerializer(ModelSerializer):
    class Meta:
        model = UserSkills
        fields = [
            "skill_name",
            "skill_category",
            "years_of_experience",
            "proficiency_level",
            "want_to_learn",
        ]


class PreferenceSerializer(ModelSerializer):
    class Meta:
        model = JobPreferences
        fields = [
            "target_role",
            "preferred_work_type",
            "preferred_locations",
            "target_salary_min",
            "target_salary_max",
            "available_from",
            "notice_period",
            "company_types",
        ]


class CareerGoalSerializer(ModelSerializer):
    class Meta:
        model = CareerGoals
        fields = ["looking_for", "deal_breakers", "nice_to_haves"]


class WorkExperienceSerializer(ModelSerializer):
    class Meta:
        model = WorkExperience
        fields = "__all__"


class ProjectSerializer(ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"


class FullProfileSerializer(ModelSerializer):
    education_background = EducationSerializer(many=True, allow_null=True)
    skills = SkillSerializer(many=True, allow_null=True)
    preferences = PreferenceSerializer(many=True, read_only=True)
    experiences = WorkExperienceSerializer(many=True, allow_null=True)
    career_goals = CareerGoalSerializer(many=True, read_only=True)

    class Meta:
        model = Profile
        fields = [
            "full_name",
            "portfolio",
            "bio",
            "avatar_id",
            "phone_number",
            "country",
            "linkedin_url",
            "github_url",
            "location",
            "google_id",
            "github_id",
            "email_verified",
            "last_login_at",
            "subscription_tier",
            "subscription_status",
            "preferences",
            "education_background",
            "skills",
            "experiences",
            "career_goals",
            "resume_data",
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["avatar_url"] = (
            blaze_client.get_url(representation["avatar_id"])
            if representation["avatar_id"]
            else ""
        )
        representation["email"] = instance.user.email
        del representation["avatar_id"]

        # Add integrations status
        representation["integrations"] = {
            "email": {
                "connected": instance.gmail_sync_enabled,
                "email": instance.user.email if instance.gmail_sync_enabled else "",
            },
            "linkedin": {
                "imported": bool(instance.linkedin_url),
                "lastSync": instance.gmail_last_sync.isoformat() if instance.gmail_last_sync else "",
            },
            "github": {
                "imported": bool(instance.github_url),
                "projects": 0,
                "topLanguages": [],
            },
            "calendar": {
                "connected": instance.calendar_sync_enabled,
            }
        }
        return representation

    def update(self, instance, validated_data):
        education = validated_data.pop("education_background", [])
        skills = validated_data.pop("skills", [])

        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        instance.education_background.all().delete()
        for item in education:
            EducationBackground.objects.create(profile=instance, **item)

        instance.skills.all().delete()
        for skill in skills:
            UserSkills.objects.create(profile=instance, **skill)

        return instance
