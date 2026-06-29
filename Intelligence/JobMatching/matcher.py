import os
import requests
import json
from typing import Dict, Any, List
from django.utils import timezone
from asgiref.sync import async_to_sync
from Oauth.models import Profile
from Jobs.models import Jobs

from shared.sdk.decision_client import DecisionEngineClient
from shared.contracts.requests.evaluate_match import EvaluateMatchRequest, JobRequirementSnapshot
from shared.contracts.responses.mission import IntelligenceSnapshot
from shared.domain.capability import Capability

def calculate_win_probability(profile: Profile, job: Jobs, deep_analysis: bool = False) -> Dict[str, Any]:
    """
    Evaluates candidate job match using the DecisionEngine SDK.
    Replaces all legacy heuristic and OpenRouter string-matching logic.
    """
    # 1. Check for existing cached score
    try:
        from Jobs.models import JobMatchScores
        cached = JobMatchScores.objects.filter(user=profile.user, job=job).order_by('-calculated_at').first()
        if cached and cached.calculated_at and (timezone.now() - cached.calculated_at).days < 3:
            return {
                "overall_score": float(cached.overall_score or 0),
                "win_probability": float(cached.overall_score or 0),
                "reasons": cached.match_reasons,
                "concerns": cached.concerns,
                "cached": True
            }
    except Exception as e:
        print(f"Cache read error: {e}")

    # 2. Extract Facts into Domain Contracts
    capabilities = []
    skills = [s.skill_name for s in profile.skills.all()]
    resume_data = profile.resume_data or {}
    
    if not skills and resume_data.get("extractedData", {}).get("skills"):
        skills = resume_data["extractedData"]["skills"]
        
    if not skills:
        skills = ["Software Engineering", "Problem Solving"]
        
    for s in skills:
        capabilities.append(Capability(name=s, capability_score=80.0))

    profile_snapshot = IntelligenceSnapshot(
        version=1,
        target_role=job.title,
        capabilities=capabilities
    )
    
    job_snapshot = JobRequirementSnapshot(
        title=job.title,
        company_name=job.company.name if job.company else "Unknown",
        required_skills=job.skills or [],
        nice_to_have_skills=[],
        description=job.description or ""
    )
    
    request = EvaluateMatchRequest(
        profile_snapshot=profile_snapshot,
        job_snapshot=job_snapshot,
        relevant_evidence=[]
    )
    
    # 3. Execute through the strongly-typed DecisionEngine SDK
    base_url = os.getenv("DECISION_ENGINE_URL", "http://localhost:8000")
    client = DecisionEngineClient(base_url=base_url)
    
    overall = 50.0
    reasons = "Standard alignment expected."
    concerns = ""
    
    try:
        result = async_to_sync(client.evaluate_match)(request)
        overall = result.overall_readiness
        
        if result.explanations:
            reasons = result.explanations[0].conclusion
            concerns = result.explanations[0].reasoning_trace
            
    except Exception as e:
        print(f"Decision Engine SDK Error: {e}")
        reasons = "Could not reach inference engine. Fallback score provided."

    # 4. Save/Update cache record
    try:
        from Jobs.models import JobMatchScores
        JobMatchScores.objects.update_or_create(
            user=profile.user,
            job=job,
            defaults={
                "overall_score": overall,
                "match_reasons": reasons,
                "concerns": concerns,
                "calculated_at": timezone.now(),
                "ai_model_used": "decision_engine_sdk"
            }
        )
    except Exception as e:
        print(f"Cache write error: {e}")

    return {
        "overall_score": int(overall),
        "win_probability": int(overall),
        "reasons": reasons,
        "concerns": concerns
    }
