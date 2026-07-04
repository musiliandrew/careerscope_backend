import os
import requests
from typing import Dict, Any
from shared.digital_twin.builder import DigitalTwinBuilder
from Jobs.models import JobMatchScores
from django.utils import timezone

def calculate_win_probability(profile, job, deep_analysis=False) -> Dict[str, Any]:
    """
    Wrapper to call the stateless decision-engine microservice.
    """
    # 1. Build the Digital Twin Snapshot
    twin = DigitalTwinBuilder.build(str(profile.user_id))
    if "error" in twin:
        return {"win_probability": 65, "reasons": "Could not load profile", "concerns": None}
        
    snapshot = twin.get("snapshot", {})
    
    # 2. Build Job Snapshot
    required_skills = []
    if job.skills:
        required_skills.extend(job.skills)
    if job.technologies:
        required_skills.extend(job.technologies)
        
    job_snap = {
        "title": job.title or "Unknown",
        "company_name": job.company.name if job.company else "Unknown",
        "required_skills": required_skills,
        "nice_to_have_skills": [],
        "description": job.description or ""
    }
    
    payload = {
        "profile_snapshot": {
            "overall_readiness_score": snapshot.get("overall_readiness_score", 0),
            "strongest_skills": snapshot.get("strongest_skills", []),
            "primary_obstacles": snapshot.get("primary_obstacles", []),
            "verified_strengths": snapshot.get("verified_strengths", [])
        },
        "job_snapshot": job_snap,
        "relevant_evidence": []
    }
    
    # 3. Call Decision Engine
    engine_url = f"{os.getenv('DECISION_ENGINE_URL', 'http://127.0.0.1:8000')}/api/v1/reasoning/evaluate_match"
    try:
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
        
        # 4. Cache it in DB
        JobMatchScores.objects.update_or_create(
            user=profile.user,
            job_id=job.id,
            defaults={
                "overall_score": win_prob,
                "win_probability": win_prob,
                "match_reasons": reasons,
                "calculated_at": timezone.now()
            }
        )
        
        return {
            "win_probability": win_prob,
            "overall_score": win_prob,
            "reasons": reasons,
            "concerns": None
        }
    except Exception as e:
        print(f"Decision Engine Error: {e}")
        return {"win_probability": 65, "reasons": "AI Matching temporarily unavailable", "concerns": None}
