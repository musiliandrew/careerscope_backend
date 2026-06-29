"""
company_intelligence.py - The Dynamic Company Intelligence Service

Orchestrates data from Companies (Operational Data), CompanyKnowledge, 
CompanyObservations, Jobs (Active Requirements), Digital Twin, and 
Application History to produce the Company Intelligence Roadmap View Model.
"""
from typing import Dict, Any
from django.conf import settings
import sys
import os

engine_path = os.path.join(settings.BASE_DIR.parent, "decision-engine")
if engine_path not in sys.path:
    sys.path.append(engine_path)

from shared.digital_twin.builder import DigitalTwinBuilder
from decisions.explain_match_score import ExplainMatchScore

class CompanyIntelligenceService:
    
    @classmethod
    def build(cls, user_id: str, company_id: str) -> Dict[str, Any]:
        """
        Builds the complete Company Intelligence View Model.
        """
        from Companies.models import Companies, CompanyKnowledge, CompanyObservation
        from Jobs.models import Jobs
        from Personalization.models import Profile
        
        try:
            company = Companies.objects.get(id=company_id)
        except Companies.DoesNotExist:
            return {"error": "Company not found"}
            
        try:
            profile = Profile.objects.get(user_id=user_id)
            target_role = profile.preferences.get("target_role", "") if profile.preferences else ""
        except Profile.DoesNotExist:
            target_role = ""

        # 1. Load the Career State (Digital Twin)
        twin = DigitalTwinBuilder.build(user_id)
        if "error" in twin:
            return {"error": twin["error"]}

        # 2. Select Relevant Company Openings
        jobs_query = Jobs.objects.filter(company=company, status='active')
        if target_role:
            # Filter loosely by target role if specified
            jobs_query = jobs_query.filter(title__icontains=target_role)
        
        if not jobs_query.exists():
            # Fallback to all jobs if no target role matches
            jobs_query = Jobs.objects.filter(company=company, status='active')
            
        # 3. Aggregate Requirements (Company Tech Stack for this role)
        aggregated_skills = set()
        for job in jobs_query:
            if job.skills:
                aggregated_skills.update(job.skills)
            if job.technologies:
                aggregated_skills.update(job.technologies)
                
        required_skills = list(aggregated_skills)

        # 4. Compare against verified experience
        decision_engine = ExplainMatchScore()
        result = decision_engine.execute(twin, required_skills=required_skills)
        
        overall_score = int(result.conclusion.get("overall_score", 0) * 100)
        matched_skills = result.conclusion.get("matched_skills", [])
        missing_skills = result.conclusion.get("missing_skills", [])
        
        # Decomposed Readiness (Simulated based on overall score for now)
        decomposed_readiness = {
            "overall": overall_score,
            "skills": min(100, overall_score + 8),
            "experience": max(0, overall_score - 8),
            "projects": min(100, overall_score + 5),
            "resume": 88, # Default baseline
            "company_fit": 79
        }

        # 5. Extract CompanyKnowledge (Dynamic Intel)
        knowledge_qs = CompanyKnowledge.objects.filter(company=company).order_by('-confidence_score')
        tech_trends = []
        for k in knowledge_qs.filter(fact_type='technology_used')[:3]:
            tech_trends.append({"technology": k.content, "confidence": float(k.confidence_score)})

        # 6. Generate Roadmap
        roadmap = []
        if missing_skills:
            for i, skill in enumerate(missing_skills[:3]):
                impact = int(100 / (len(required_skills) or 1))
                roadmap.append({
                    "goal": f"Master {skill}",
                    "action": f"Build a project using {skill} in a production-like environment.",
                    "evidence_produced": f"Publish GitHub repository and add architecture documentation.",
                    "estimated_improvement": f"{decomposed_readiness['overall']}% → {min(100, decomposed_readiness['overall'] + impact)}%",
                    "impact": impact
                })
                
        # 7. Generate Application Outlook
        outlook = {
            "status": "Ready to Apply" if overall_score >= 80 else "Improve First",
            "explanation": f"You meet the core requirements. {missing_skills[0] if missing_skills else ''} is your only major gap." if overall_score >= 80 else f"You are missing critical requirements for this role, specifically {', '.join(missing_skills[:2])}. Focus on building evidence for these before applying."
        }

        # 8. Map to View Model
        response = {
            "company": {
                "id": str(company.id),
                "name": company.name,
                "industry": company.industry,
                "logo_url": company.logo_url,
                "size": company.company_size,
                "careers_url": company.careers_page_url
            },
            "career_readiness": decomposed_readiness,
            "market_activity": {
                "active_jobs": jobs_query.count(),
                "tech_trends": tech_trends
            },
            "strengths": [
                {
                    "name": s,
                    "evidence_link": "Verified via past experience", 
                    "is_verified": True
                } for s in matched_skills
            ],
            "gaps": [
                {
                    "name": ms,
                    "impact": f"+{int(100 / (len(required_skills) or 1))}%",
                    "priority": "High" if i == 0 else "Medium"
                } for i, ms in enumerate(missing_skills)
            ],
            "roadmap": roadmap,
            "open_roles": [
                {
                    "id": str(j.id),
                    "title": j.title,
                    "location": f"{j.location.city}, {j.location.country}" if j.location else "Remote",
                    "type": j.work_type
                } for j in jobs_query[:5]
            ],
            "application_history": [], # To be populated from Applications model
            "application_outlook": outlook,
            "recommended_next_step": {
                "action": "Start Project" if missing_skills else "Apply to Open Roles",
                "target": missing_skills[0] if missing_skills else "Application"
            }
        }
        
        return response
