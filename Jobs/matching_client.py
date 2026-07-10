import os
import json
import requests
from typing import Dict, Any
from shared.digital_twin.builder import DigitalTwinBuilder
from shared.contracts.requests.evaluate_match import EvaluateMatchRequest, JobRequirementSnapshot
from shared.contracts.responses.mission import IntelligenceSnapshot
from shared.domain.capability import Capability
from Jobs.models import JobMatchScores
from django.utils import timezone

def calculate_win_probability(profile, job, deep_analysis=False) -> Dict[str, Any]:
    """
    Wrapper to call the stateless decision-engine microservice using standard contracts.
    """
    # 0. Check DB Cache first
    try:
        cached = JobMatchScores.objects.filter(user=profile.user, job=job).first()
        if cached and cached.calculated_at and (timezone.now() - cached.calculated_at).days < 3:
            val = int(cached.overall_score) if cached.overall_score is not None else 65
            return {
                "win_probability": val,
                "overall_score": val,
                "reasons": cached.match_reasons or "Match analyzed successfully.",
                "concerns": cached.concerns
            }
    except Exception as e:
        print(f"Failed to read from cache: {e}")

    # 1. Build the Digital Twin Snapshot
    twin = DigitalTwinBuilder.build(str(profile.user_id))
    if "error" in twin:
        return {"win_probability": 65, "reasons": "Could not load profile", "concerns": None}
        
    snapshot = twin.get("snapshot", {})
    
    # Extract skills/capabilities from user profile or twin
    skills = list(profile.skills.all().values_list("skill_name", flat=True))
    if not skills:
        skills = snapshot.get("strongest_skills", [])
        
    capabilities = [Capability(name=s, capability_score=80.0) for s in skills]

    # Get target role
    pref = profile.preferences.first()
    target_role = pref.target_role if pref and pref.target_role else getattr(profile, "target_role", "Software Engineer")
    if not target_role:
        target_role = "Software Engineer"

    # 2. Build IntelligenceSnapshot
    profile_snapshot = IntelligenceSnapshot(
        version=1,
        target_role=target_role,
        career_readiness=float(snapshot.get("overall_readiness_score", 0.0)),
        capabilities=capabilities
    )
    
    # 3. Build Job Snapshot
    required_skills = []
    if job.skills:
        required_skills.extend(job.skills)
    if job.technologies:
        required_skills.extend(job.technologies)
        
    # If the job has no skills/technologies in the database, enrich it using AI Enrichment System!
    if not required_skills:
        ai_url = f"{os.getenv('AI_ENRICHMENT_URL', 'http://127.0.0.1:8002')}/sync-execute"
        try:
            payload = {
                "capability": "skill_extraction",
                "payload": {
                    "title": job.title,
                    "description": job.description or ""
                }
            }
            resp = requests.post(ai_url, json=payload, timeout=5)
            if resp.status_code == 200:
                extracted = resp.json().get("result", {}).get("skills", [])
                if extracted:
                    job.skills = extracted
                    job.technologies = extracted
                    job.save()
                    required_skills.extend(extracted)
        except Exception as e:
            print(f"Failed to enrich job skills: {e}")
        
    job_snapshot = JobRequirementSnapshot(
        title=job.title or target_role,
        company_name=job.company.name if job.company else "Unknown",
        required_skills=required_skills,
        nice_to_have_skills=[],
        description=job.description or ""
    )
    
    # 4. Build EvaluateMatchRequest
    request_obj = EvaluateMatchRequest(
        profile_snapshot=profile_snapshot,
        job_snapshot=job_snapshot,
        relevant_evidence=[]
    )
    
    # 5. Call Decision Engine
    engine_url = f"{os.getenv('DECISION_ENGINE_URL', 'http://127.0.0.1:8003')}/api/v1/reasoning/evaluate_match"
    try:
        # Safe serialization using Pydantic
        payload = json.loads(request_obj.model_dump_json())
        
        resp = requests.post(engine_url, json=payload, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        
        # Parse DecisionResult contract
        overall_readiness = result.get("overall_readiness", 65.0)
        win_prob = int(overall_readiness)
        
        explanations = result.get("explanations", [])
        if explanations:
            reasons = explanations[0].get("reasoning_trace", "Match analyzed successfully.")
        else:
            reasons = "Match analyzed successfully."
        
        # 6. Cache it in DB
        import uuid
        score_obj, created = JobMatchScores.objects.get_or_create(
            user=profile.user,
            job_id=job.id,
            defaults={
                "id": uuid.uuid4(),
                "overall_score": win_prob,
                "match_reasons": reasons,
                "calculated_at": timezone.now()
            }
        )
        if not created:
            score_obj.overall_score = win_prob
            score_obj.match_reasons = reasons
            score_obj.calculated_at = timezone.now()
            score_obj.save()
        
        return {
            "win_probability": win_prob,
            "overall_score": win_prob,
            "reasons": reasons,
            "concerns": None
        }
    except Exception as e:
        print(f"Decision Engine Error: {e}")
        return {"win_probability": 65, "reasons": "AI Matching temporarily unavailable", "concerns": None}

