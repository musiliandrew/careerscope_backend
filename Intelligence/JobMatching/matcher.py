import os
import requests
import json
from typing import Dict, Any, List
from django.utils import timezone
from Oauth.models import Profile
from Jobs.models import Jobs

def calculate_win_probability(profile: Profile, job: Jobs, deep_analysis: bool = False) -> Dict[str, Any]:
    """
    Implements a 'Signal Matching' algorithm that estimates win probability.
    Relative to the competition, and turns that into a probability of success.
    
    NOTE: DB caching is temporarily disabled to resolve 'relation missing' errors.
    """
    
    # 1. Gather Candidate Signals
    skills = [s.skill_name for s in profile.skills.all()]
    resume_data = profile.resume_data or {}
    
    # Fallback to resume extracted skills if profile skills are empty
    if not skills and resume_data.get("extractedData", {}).get("skills"):
        skills = resume_data["extractedData"]["skills"]
    
    # If still no skills, use a default to avoid 0% for everyone
    if not skills:
        skills = ["Software Engineering", "Problem Solving"] # General baseline
        
    github_url = profile.github_url
    portfolio_url = profile.portfolio
    
    # 2. Gather Job Signals
    job_skills = job.skills or []
    job_desc = job.description
    company_tier = job.company.tier if job.company else "startup"
    apply_count = job.apply_count or 0
    
    # 3. Check for existing cached score (DISABLED for now)
    # try:
    #     from Jobs.models import JobMatchScores
    #     cached = JobMatchScores.objects.filter(user=profile.user, job=job).order_by('-calculated_at').first()
    #     if cached and cached.calculated_at and (timezone.now() - cached.calculated_at).days < 1:
    #         return {
    #             "overall_score": float(cached.overall_score or 0),
    #             "win_probability": float(cached.overall_score or 0),
    #             "reasons": cached.match_reasons,
    #             "concerns": cached.concerns,
    #             "cached": True
    #         }
    # except:
    #     pass

    # 4. Deep Alignment Algorithm (Heuristic + AI)
    key = os.getenv("OPENROUTER_API_KEY")
    
    def get_heuristic_score():
        # Jitter based on job ID to make it feel unique per job even if signals are similar
        raw_uuid = str(job.id)
        jitter = (sum(ord(c) for c in raw_uuid[:6]) % 15) - 7 # -7 to +7
        
        # 1. Title Match (Role identity)
        title_norm = job.title.lower()
        skills_norm = [s.lower() for s in skills]
        
        title_signal = 0
        if any(s in title_norm for s in skills_norm if len(s) > 4):
            title_signal = 20
            
        # 2. Core Technical alignment (DS/AI specialized)
        tech_boost = 0
        core_keywords = ['data', 'ai', 'learning', 'python', 'software', 'engineer']
        for k in core_keywords:
            if k in title_norm:
                tech_boost += 5
        
        # 3. Skill overlap
        common = set(skills_norm) & set([s.lower() for s in job_skills])
        overlap_pct = len(common) / max(len(job_skills), 1)
        
        # 4. Base Calculation
        base_win_prob = 30 + title_signal + tech_boost + (overlap_pct * 35) + jitter
        
        # 5. Competition Penalty
        noise_penalty = min(20, (apply_count / 8))
        
        final_prob = max(15, min(96, base_win_prob - noise_penalty))
        
        # Reasons
        if title_signal > 0:
            reason = f"Personalized signals show high alignment with your {title_norm} background."
        elif overlap_pct > 0.3:
            reason = f"Strong match for your technical stack including {', '.join(list(common)[:2])}."
        else:
            reason = "Good foundational alignment. Your professional signals represent a solid candidate profile."

        return {
            "overall_score": int(base_win_prob),
            "win_probability": int(final_prob),
            "reasons": reason,
            "concerns": "Market competition is active for this role." if apply_count > 20 else "Niche role specialization may apply."
        }

    result = get_heuristic_score()

    if deep_analysis and key:
        # (AI Logic remains if user wants to use it, but bypassed default in serializer)
        try:
            prompt = (
                f"Act as a high-stakes tech recruiter. Estimate the JOB MATCH PROBABILITY (0-100) "
                f"for this candidate against current market competition for this specific role.\n\n"
                f"CANDIDATE SIGNALS:\n"
                f"- Skills: {', '.join(skills)}\n"
                f"- Portfolio/GitHub: {portfolio_url or 'None'}, {github_url or 'None'}\n"
                f"- Experience Depth: {resume_data.get('summary', 'Experienced professional')}\n\n"
                f"JOB SIGNALS:\n"
                f"- Title: {job.title}\n"
                f"- Company Tier: {company_tier}\n"
                f"- Market Noise (Applicants): {apply_count}\n"
                f"- Requirements: {', '.join(job_skills)}\n\n"
                f"Task: Quantify alignment. Don't just check keywords. "
                f"Respond ONLY with strict JSON: "
                f"{{\"overall_score\": 0-100, \"win_probability\": 0-100, \"reasons\": \"...\", \"concerns\": \"...\"}}"
            )
            
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            body = {
                "model": os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
            }
            resp = requests.post("https://openrouter.ai/api/v1/chat/completions", json=body, headers=headers, timeout=15)
            if resp.status_code == 200:
                ai_raw = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "{}")
                import re
                json_match = re.search(r'\{.*\}', ai_raw, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    result = json.loads(ai_raw)
        except Exception as e:
            print(f"Matcher AI Error: {e}")

    # 5. Save/Update cache record (DISABLED to fix errors)
    # try:
    #     from Jobs.models import JobMatchScores
    #     import uuid
    #     win_prob = result.get("win_probability") or result.get("overall_score") or 50
    #     overall = result.get("overall_score") or win_prob
    #     JobMatchScores.objects.update_or_create(...)
    # except:
    #     pass

    win_prob = result.get("win_probability") or result.get("overall_score") or 50
    overall = result.get("overall_score") or win_prob
    result["win_probability"] = win_prob
    result["overall_score"] = overall
    return result
