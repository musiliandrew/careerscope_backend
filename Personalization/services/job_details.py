"""
job_details.py - The Job Details Aggregation Service

Owns the Dashboard View Model for the Job Details experience.
Orchestrates data from the Digital Twin and Decision Engine.
"""
from typing import Dict, Any
from django.conf import settings
import sys
import os

# Ensure decision-engine is in the path
engine_path = os.path.join(settings.BASE_DIR.parent, "decision-engine")
if engine_path not in sys.path:
    sys.path.append(engine_path)

from shared.digital_twin.builder import DigitalTwinBuilder
from decisions.explain_match_score import ExplainMatchScore

class JobDetailsService:
    
    @classmethod
    def build(cls, user_id: str, job_id: str) -> Dict[str, Any]:
        """
        Builds the complete Job Details View Model.
        """
        from Jobs.models import Jobs
        try:
            job = Jobs.objects.get(id=job_id)
        except Jobs.DoesNotExist:
            return {"error": "Job not found"}

        # 1. Load the Career State (Digital Twin)
        twin = DigitalTwinBuilder.build(user_id)
        if "error" in twin:
            return {"error": twin["error"]}

        # 2. Execute ExplainMatchScore Decision
        decision_engine = ExplainMatchScore()
        # Ensure job has skills
        required_skills = job.skills if job.skills else []
        # If job has technologies but no skills, merge them
        if not required_skills and job.technologies:
            required_skills = job.technologies
            
        result = decision_engine.execute(twin, required_skills=required_skills)

        # 3. Transform Result into View Model Strings
        overall_score = int(result.conclusion.get("overall_score", 0) * 100)
        matched_skills = result.conclusion.get("matched_skills", [])
        missing_skills = result.conclusion.get("missing_skills", [])
        
        # Build coach assessment
        if overall_score >= 80:
            coach_text = f"You are a strong fit for this role. You already meet the core technical requirements, including {', '.join(matched_skills[:2])}."
            if missing_skills:
                coach_text += f" The largest gap is {missing_skills[0]}. Completing one project addressing this would substantially strengthen your application."
        else:
            coach_text = f"This role is currently a stretch. While you have {', '.join(matched_skills[:2]) if matched_skills else 'some foundational skills'}, the requirements heavily emphasize {', '.join(missing_skills[:2])}."

        # Map to View Model
        response = {
            "job": {
                "id": str(job.id),
                "title": job.title,
                "company": job.company.name if job.company else "Unknown",
                "salary": job.salary_formatted or "Not specified",
                "location": f"{job.location.city}, {job.location.country}" if job.location else "Remote",
                "work_type": job.work_type,
                "description": job.description,
                "external_url": job.external_url,
            },
            "career_readiness": {
                "score": overall_score,
                "label": "Strong Match" if overall_score >= 80 else "Growing Match"
            },
            "coach_assessment": {
                "text": coach_text,
                "confidence": result.confidence
            },
            "verified_strengths": [
                {
                    "name": s,
                    "evidence_link": "Verified via past experience", # Mocked link logic for now
                    "is_verified": True
                } for s in matched_skills
            ],
            "critical_gaps": [
                {
                    "name": ms,
                    "impact": f"+{int(100 / (len(required_skills) or 1))}%",
                    "priority": "High" if i == 0 else "Medium"
                } for i, ms in enumerate(missing_skills)
            ],
            "highest_roi_actions": [
                {
                    "title": f"Build a project using {missing_skills[0]}" if missing_skills else "Apply Now",
                    "type": "project" if missing_skills else "apply"
                }
            ],
            "match_breakdown": {
                "technical": overall_score,
                "experience": overall_score - 5, # Simulated
                "culture": 85 # Simulated
            },
            "supporting_evidence": result.evidence_used,
            "recommended_next_step": {
                "action": "Complete Infrastructure Project" if missing_skills else "Submit Application",
                "target": missing_skills[0] if missing_skills else "Resume"
            },
            "application_readiness": {
                "technical": overall_score,
                "resume_quality": 82,
                "portfolio": 74,
                "interview": 67,
                "overall_recommendation": "Apply after completing one additional project." if missing_skills else "Ready to apply."
            },
            "related_projects": []
        }
        
        return response
