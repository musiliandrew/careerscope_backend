"""
digital_twin.py - The Canonical Digital Twin Builder

This module serves as the single source of truth for constructing a user's professional identity.
It aggregates data from multiple models (Profile, Skills, Projects, Experience, Evidence, Insights)
and computes a derived Career Snapshot.
"""
from typing import Dict, Any, List
from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from Oauth.models import (
    Profile, UserSkills, WorkExperience, Project, 
    JobPreferences, CareerGoals, EducationBackground, 
    Evidence, Insight, SkillProgress
)
from Personalization.models import UserMemory, UserBehaviorEvent

User = get_user_model()

class DigitalTwinBuilder:
    
    @classmethod
    def build(cls, user_id: str) -> Dict[str, Any]:
        """
        Builds and returns the canonical Career Digital Twin for a user.
        This contains both raw structured data and derived analytical state.
        """
        profile = Profile.objects.prefetch_related(
            Prefetch('skills', queryset=UserSkills.objects.prefetch_related('evidence', 'progress_history')),
            Prefetch('experiences', queryset=WorkExperience.objects.prefetch_related('skills_demonstrated', 'evidence')),
            Prefetch('projects', queryset=Project.objects.prefetch_related('skills_demonstrated', 'evidence')),
            'evidence',
            'insights',
            'career_goals',
            'preferences',
            'education_background'
        ).filter(user_id=user_id).first()

        if not profile:
            return {"error": "Profile not found"}

        # Extract Raw Models
        skills = cls._serialize_skills(profile.skills.all())
        experiences = cls._serialize_experiences(profile.experiences.all())
        projects = cls._serialize_projects(profile.projects.all())
        insights = cls._serialize_insights(profile.insights.all())
        goals = cls._serialize_goals(profile.career_goals.all(), profile.preferences.all())

        # Compute Derived State (The Career Snapshot)
        snapshot = cls._compute_snapshot(skills, insights)

        return {
            "identity": {
                "id": str(profile.id),
                "full_name": profile.full_name,
                "location": profile.location,
                "headline": profile.bio, # Currently bio, could evolve to professional headline
                "linkedin": profile.linkedin_url,
                "github": profile.github_url,
            },
            "snapshot": snapshot, # Derived Readiness, Strengths, Obstacles
            "goals": goals,
            "skills": skills,
            "experience": experiences,
            "projects": projects,
            "insights": insights,
        }

    @staticmethod
    def _serialize_skills(skills) -> List[Dict]:
        serialized = []
        for s in skills:
            serialized.append({
                "skill_name": s.skill_name,
                "category": s.skill_category,
                "proficiency_level": s.proficiency_level,
                "proficiency_score": s.proficiency_score,
                "confidence_score": float(s.confidence_score) if s.confidence_score else 0.0,
                "years_of_experience": float(s.years_of_experience) if s.years_of_experience else 0.0,
                "is_verified": s.is_verified,
                "evidence_count": s.evidence.count()
            })
        return serialized

    @staticmethod
    def _serialize_experiences(experiences) -> List[Dict]:
        return [{
            "title": e.title,
            "company": e.company,
            "start_date": e.start_date,
            "end_date": e.end_date,
            "skills_demonstrated": [s.skill_name for s in e.skills_demonstrated.all()],
            "evidence_count": e.evidence.count()
        } for e in experiences]

    @staticmethod
    def _serialize_projects(projects) -> List[Dict]:
        return [{
            "name": p.name,
            "outcomes": p.outcomes,
            "skills_demonstrated": [s.skill_name for s in p.skills_demonstrated.all()],
            "evidence_count": p.evidence.count()
        } for p in projects]

    @staticmethod
    def _serialize_insights(insights) -> List[Dict]:
        return [{
            "type": i.insight_type,
            "description": i.description,
            "severity": i.severity,
            "confidence": float(i.confidence) if i.confidence else 0.0,
            "is_resolved": i.is_resolved
        } for i in insights]

    @staticmethod
    def _serialize_goals(goals, preferences) -> Dict:
        # Simplistic merge for MVP
        goal = goals.first()
        pref = preferences.first()
        return {
            "target_role": pref.target_role if pref else None,
            "target_salary_min": float(pref.target_salary_min) if pref and pref.target_salary_min else None,
            "looking_for": goal.looking_for if goal else None,
            "deal_breakers": goal.deal_breakers if goal else None,
        }

    @classmethod
    def _compute_snapshot(cls, skills: List[Dict], insights: List[Dict]) -> Dict:
        """
        Computes the derived Career Snapshot.
        """
        # Sort skills by score
        sorted_skills = sorted([s for s in skills if s.get('proficiency_score')], 
                               key=lambda x: x['proficiency_score'], reverse=True)
        
        top_skills = [s['skill_name'] for s in sorted_skills[:5]]
        
        # Identify active obstacles
        active_obstacles = [i for i in insights if i['type'] == 'obstacle' and not i['is_resolved']]
        top_obstacles = [o['description'] for o in active_obstacles[:3]]

        # Identify strengths
        strengths = [i['description'] for i in insights if i['type'] == 'strength' and not i['is_resolved']]

        return {
            "strongest_skills": top_skills,
            "primary_obstacles": top_obstacles,
            "verified_strengths": strengths,
            "overall_readiness_score": 0, # Will be populated by Decision Engine later
            "recommended_next_action": "Complete Profile" if not top_skills else "Review Target Companies"
        }
