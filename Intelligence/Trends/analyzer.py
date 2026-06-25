import os
import json
from collections import Counter
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
import requests

from Jobs.models import Jobs
from Companies.models import TechTrend, TechTrendNews
from News.models import NewsArticles

def analyze_tech_trends():
    """
    Analyzes job postings and news to detect technology trends.
    """
    # 1. Analyze Jobs for technology demand
    all_tech_mentions = []
    # Get technologies from jobs posted in the last 30 days
    last_30_days = timezone.now() - timedelta(days=30)
    jobs_qs = Jobs.objects.filter(posted_at__gte=last_30_days).values_list('technologies', 'skills')
    
    for techs, skills in jobs_qs:
        if techs: all_tech_mentions.extend(techs)
        if skills: all_tech_mentions.extend(skills)
    
    tech_counts = Counter(all_tech_mentions)
    total_jobs = max(len(jobs_qs), 1)

    # 2. Analyze News for social volume
    # Topic keywords for our news search
    news_qs = NewsArticles.objects.filter(published_at__gte=last_30_days).values_list('title', 'summary')
    news_corpus = " ".join([f"{t} {s}" for t, s in news_qs]).lower()

    # 3. Known categories (Heuristic)
    CATEGORIES = {
        'Languages': ['Python', 'JavaScript', 'TypeScript', 'Go', 'Rust', 'Java', 'C++', 'Swift', 'Kotlin', 'PHP', 'SQL'],
        'AI/ML': ['PyTorch', 'TensorFlow', 'LLM', 'RAG', 'LangChain', 'OpenAI', 'Transformers', 'Deep Learning', 'Computer Vision'],
        'Frameworks': ['React', 'Next.js', 'Vue', 'Angular', 'Django', 'FastAPI', 'Node.js', 'Spring Boot', 'Laravel', 'Tailwind'],
        'Cloud/DevOps': ['AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Terraform', 'CI/CD', 'Serverless', 'Supabase', 'Vercel'],
        'Databases': ['PostgreSQL', 'MongoDB', 'Redis', 'Pinecone', 'Qdrant', 'Milvus', 'Weaviate', 'Snowflake'],
    }

    results = []

    # Flatten categories for easier lookup
    tech_categories = {}
    for cat, techs in CATEGORIES.items():
        for t in techs:
            tech_categories[t.lower()] = cat

    # Synthesis
    all_detected_techs = set([t.lower() for t in tech_counts.keys()] + [t.lower() for t in tech_categories.keys()])
    
    for tech_name_lower in all_detected_techs:
        # Match back to display name
        display_name = next((t for t in tech_categories.keys() if t.lower() == tech_name_lower), tech_name_lower.capitalize())
        # Try to find original casing from tech_counts
        orig_case = next((t for t in tech_counts.keys() if t.lower() == tech_name_lower), display_name)
        
        # Calculate scores
        demand = tech_counts.get(orig_case, 0)
        # Check mentions in news
        news_mentions = news_corpus.count(tech_name_lower)
        
        # Simple popularity score (0-100)
        # Normalized by total jobs and news volume
        pop_score = min(100, ((demand / total_jobs) * 500) + (news_mentions / 5))
        
        if pop_score < 5: # Filter out noise
            if tech_name_lower not in [t.lower() for t in tech_categories.keys()]:
                continue
        
        category = tech_categories.get(tech_name_lower, 'General Tool')
        
        # Create or Update Trend
        trend, created = TechTrend.objects.update_or_create(
            name=orig_case,
            defaults={
                'category': category,
                'popularity_score': round(pop_score, 2),
                'growth_percentage': 12.5, # Placeholder for now, would need historical comparison
                'demand_rank': 0, # Will set after loop
                'social_volume': news_mentions,
                'sentiment_score': 0.75, # Placeholder
                'is_active': True
            }
        )
        results.append(trend)

    # Re-calculate demand ranks
    results.sort(key=lambda x: x.popularity_score, reverse=True)
    for i, t in enumerate(results):
        t.demand_rank = i + 1
        t.save()
        
    return len(results)

def synthesize_tech_commentary():
    """
    Uses AI to create a 'What people are talking about' summary.
    """
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        return "Tech landscape is shifting towards AI integration and efficient DX."

    # Get top trends and recent news
    top_techs = TechTrend.objects.order_by('-popularity_score')[:5]
    top_names = [t.name for t in top_techs]
    
    recent_news = NewsArticles.objects.order_by('-published_at')[:10]
    news_titles = [n.title for n in recent_news]

    prompt = (
        f"Analyze these current tech trends: {', '.join(top_names)}.\n"
        f"Based on these recent headlines: {'; '.join(news_titles)}.\n"
        f"Write a short, punchy 'What's Hot' summary (2-3 sentences) about what developers are talking about RIGHT NOW. "
        f"Mention social sentiment and emerging technologies."
    )

    try:
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        body = {
            "model": "openai/gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}]
        }
        resp = requests.post("https://openrouter.ai/api/v1/chat/completions", json=body, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
    except:
        pass
    
    return f"The community is buzzing about {', '.join(top_names[:3])}."
