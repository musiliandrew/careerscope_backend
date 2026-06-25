from django.shortcuts import render

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from Jobs.models import Jobs
from Oauth.models import Profile
from Intelligence.vectorDB.client import embed_text, search_jobs


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def recommended_jobs(request: Request) -> Response:
    """Return semantically recommended jobs for the authenticated user.

    This is a minimal first cut: we build an embedding from the user's skills
    (if any) + optional query string, search Qdrant, and return basic job data.
    """

    user = request.user
    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        return Response({"results": [], "detail": "No profile"})

    q = request.query_params.get("q") or ""
    skills_qs = profile.skills.all().values_list("skill_name", flat=True)
    skills_text = ", ".join(skills_qs)

    base_text = f"Skills: {skills_text}"
    if q:
        base_text += f"\nQuery: {q}"

    try:
        emb = embed_text(base_text)
        results = search_jobs(emb, top_k=20)
    except Exception as exc:
        return Response({"results": [], "error": str(exc)[:300]}, status=500)

    job_ids = [r.get("payload", {}).get("job_id") for r in results if r.get("payload")]
    jobs = list(Jobs.objects.filter(id__in=job_ids).select_related('company', 'location'))
    jobs_by_id = {str(j.id): j for j in jobs}

    # Fetch cached scores
    from Jobs.models import JobMatchScores
    from .utils import trigger_match_calculation
    from django.utils import timezone
    
    cached_scores = JobMatchScores.objects.filter(
        user=user, 
        job_id__in=job_ids
    )
    
    # Only use cache if it's less than 3 days old
    recent_cache = {
        str(cs.job_id): cs 
        for cs in cached_scores 
        if cs.calculated_at and (timezone.now() - cs.calculated_at).days < 3
    }
    
    jobs_to_calculate = []
    out = []
    
    for r in results[:8]:
        payload = r.get("payload") or {}
        jid = payload.get("job_id")
        job = jobs_by_id.get(jid)
        if not job:
            continue
            
        cached = recent_cache.get(jid)
        
        if cached:
            display_score = int(cached.win_probability if cached.win_probability is not None else cached.overall_score)
            reasons = cached.match_reasons or ""
            concerns = cached.concerns or ""
        else:
            # Cache miss! Use raw vector score as fast fallback and trigger async calc
            raw_score = r.get("score") or 0
            display_score = int(max(10, min(100, (raw_score - 0.4) * 200)))
            reasons = "AI is currently analyzing your professional signals for this specific role..."
            concerns = ""
            jobs_to_calculate.append(jid)
        
        out.append(
            {
                "id": str(job.id),
                "title": job.title,
                "company_name": job.company.name if job.company else "Unknown",
                "location_text": f"{job.location.city}, {job.location.country}" if job.location else "Remote",
                "work_type": job.work_type,
                "posted_at": job.posted_at,
                "skills": job.skills or [],
                "technologies": job.technologies or [],
                "categories": job.categories or [],
                "external_url": job.external_url,
                "apply_url": job.apply_url,
                "status": job.status,
                "freshness_score": job.freshness_score,
                "job_match": display_score,
                "match_reasons": reasons,
                "match_concerns": concerns,
            }
        )

    # Trigger background calculation for jobs without a recent cache
    if jobs_to_calculate:
        trigger_match_calculation(user.id, jobs_to_calculate)

    # Sort results by the new job match score
    out.sort(key=lambda x: x["job_match"], reverse=True)
    return Response({"results": out})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def learning_recommendations(request: Request) -> Response:
    """
    Get course recommendations based on the user's 'want to learn' skills.
    Wraps links with affiliate tags.
    """
    user = request.user
    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        return Response({"results": [], "detail": "No profile"})

    # Get skills the user wants to learn
    learning_skills = list(profile.skills.filter(want_to_learn=True).values_list("skill_name", flat=True))
    
    # If none, use technical skills as fallback or a default
    if not learning_skills:
        learning_skills = list(profile.skills.filter(want_to_learn=False).values_list("skill_name", flat=True))[:3]
    
    if not learning_skills:
        # Final fallback
        learning_skills = ["Software Engineering", "Cloud Computing"]

    from agents.AIService.OpenRouterAI import generate_learning_recommendations
    from .utils import wrap_affiliate_link

    recs = generate_learning_recommendations(learning_skills)
    
    # Wrap with affiliate links
    for r in recs:
        r["url"] = wrap_affiliate_link(r.get("url", ""))

    return Response({"results": recs})

@api_view(["POST"])
@permission_classes([AllowAny]) # Webhook should be secured via token in production
def calculate_matches_webhook(request: Request) -> Response:
    """
    Background webhook to calculate deep job matches for a user asynchronously.
    """
    user_id = request.data.get("user_id")
    job_ids = request.data.get("job_ids", [])
    
    if not user_id or not job_ids:
        return Response({"error": "Missing user_id or job_ids"}, status=400)
        
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=user_id)
        profile = Profile.objects.get(user=user)
        
        jobs = Jobs.objects.filter(id__in=job_ids)
        
        from Intelligence.JobMatching.matcher import calculate_win_probability
        
        for job in jobs:
            # Force deep analysis, cache handles saving
            try:
                calculate_win_probability(profile, job, deep_analysis=True)
            except Exception as e:
                print(f"Error calculating match for job {job.id}: {e}")
                
        return Response({"status": "success", "calculated": len(jobs)})
    except Exception as e:
        return Response({"error": str(e)}, status=500)
