from typing import Dict, Any, List
import os
import requests


def extract_resume(text: str) -> Dict[str, Any]:
    """
    Minimal placeholder implementation so imports succeed during migrations.
    Returns a safe empty structure compatible with callers.
    """
    return {
        "header": {},
        "summary": "",
        "skills": [],
        "experience": [],
        "education": [],
        "projects": [],
        "extras": {},
        "confidence": 0.0,
    }


def generate_career_card_summary(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return { companies: [..max 3..], score: int } using OpenRouter if configured.
    Falls back to a simple heuristic when OPENROUTER_API_KEY is not present or errors.
    """
    key = os.getenv("OPENROUTER_API_KEY")
    skills: List[str] = [str(s) for s in profile.get("skills", [])]

    def heuristic() -> Dict[str, Any]:
        s = " ".join([x.lower() for x in skills])
        suggestions: List[str] = []
        if any(k in s for k in ["python", "django", "ml", "ai"]):
            suggestions += ["DeepMind", "OpenAI", "Spotify"]
        if any(k in s for k in ["javascript", "react", "node", "frontend"]):
            suggestions += ["Vercel", "Shopify", "Airbnb"]
        if any(k in s for k in ["devops", "kubernetes", "aws", "terraform"]):
            suggestions += ["AWS", "HashiCorp", "Cloudflare"]
        # de-dup and cap to 3
        companies = list(dict.fromkeys(suggestions))[:3] or ["Stripe", "Notion", "Cloudflare"]
        score = min(98, 40 + len(skills) * 5)
        return {"companies": companies, "score": score}

    if not key:
        return heuristic()

    try:
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        prompt = (
            "Given a user's skills and short profile, suggest up to 3 tech companies they could work at "
            "(array of concise brand names only, no explanations) and a CareerScore percentage 0-100.\n"
            f"Skills: {', '.join(skills)}\n"
            f"Title: {profile.get('title','')}\n"
            f"Summary: {profile.get('summary','')}\n"
            "Respond as strict JSON: {\"companies\": string[], \"score\": number}."
        )
        body = {
            "model": os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
        }
        resp = requests.post("https://openrouter.ai/api/v1/chat/completions", json=body, headers=headers, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        try:
            parsed = requests.utils.json.loads(content)  # type: ignore[attr-defined]
        except Exception:
            parsed = {}
        companies = parsed.get("companies") if isinstance(parsed.get("companies"), list) else []
        score = int(parsed.get("score", 72))
        if not companies:
            return heuristic()
        return {"companies": companies[:3], "score": max(0, min(100, score))}
    except Exception:
        return heuristic()


def generate_learning_recommendations(skills: List[str]) -> List[Dict[str, Any]]:
    """
    Given a list of skills, suggest courses from Coursera, Udemy, or edX.
    Returns a list of dicts: [{ title, provider, url, description }]
    """
    key = os.getenv("OPENROUTER_API_KEY")

    def heuristic() -> List[Dict[str, Any]]:
        # Hardcoded fallback recommendations
        s = " ".join([x.lower() for x in skills])
        recs = []
        if any(k in s for k in ["python", "django"]):
            recs.append({
                "title": "Django for Beginners",
                "provider": "Udemy",
                "url": "https://www.udemy.com/course/django-for-beginners/",
                "description": "Build powerful web applications with Python and Django."
            })
        if any(k in s for k in ["react", "javascript"]):
            recs.append({
                "title": "The Complete React Developer",
                "provider": "Coursera",
                "url": "https://www.coursera.org/specializations/react",
                "description": "Master React.js from scratch to advanced patterns."
            })
        if not recs:
            recs.append({
                "title": "Computer Science 101",
                "provider": "edX",
                "url": "https://www.edx.org/course/cs101-building-a-search-engine",
                "description": "A great foundation for any technical career."
            })
        return recs

    if not key:
        return heuristic()

    try:
        prompt = (
            f"Based on these target skills: {', '.join(skills)}, suggest 3 specific online courses "
            "from Coursera, Udemy, or edX. "
            "For each course, provide: title, provider, specific course url, and a short 1-sentence description. "
            "Respond as a strict JSON list of objects: "
            "[{\"title\": \"...\", \"provider\": \"...\", \"url\": \"...\", \"description\": \"...\"}]"
        )
        
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
        }
        resp = requests.post("https://openrouter.ai/api/v1/chat/completions", json=body, headers=headers, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "[]")
        
        # OpenRouter sometimes wraps in a key even if asked for a list
        import json
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            for val in parsed.values():
                if isinstance(val, list):
                    return val[:3]
        return parsed[:3] if isinstance(parsed, list) else heuristic()
    except Exception:
        return heuristic()

