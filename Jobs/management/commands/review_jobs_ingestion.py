import json
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from Jobs.models import Jobs
from DataIngestion.Jobs.filters import ROLE_KEYWORDS, extract_skills, is_relevant_role


class Command(BaseCommand):
    help = "Review recent ingested jobs for QA: relevance, skills, and source breakdown."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=7, help="Look back N days (default 7)")
        parser.add_argument("--limit", type=int, default=50, help="Max sample size to print (default 50)")
        parser.add_argument("--source", type=str, default=None, help="Filter by source name (optional)")

    def handle(self, *args, **options):
        days = options["days"]
        limit = options["limit"]
        source = options["source"]

        since = timezone.now() - timedelta(days=days)
        qs = Jobs.objects.filter(posted_at__gte=since).order_by("-posted_at")
        if source:
            qs = qs.filter(source__name__iexact=source)

        total = qs.count()
        by_source = (
            qs.values_list("source__name", flat=False)
        )

        # Build summary
        summary = {
            "window_days": days,
            "total_jobs": total,
            "sources": {},
            "role_terms": list({t for arr in ROLE_KEYWORDS.values() for t in arr}),
        }

        # Source counts
        src_counts = {}
        for s in qs.values_list("source__name", flat=True):
            src_counts[s] = src_counts.get(s, 0) + 1
        summary["sources"] = src_counts

        # Sample details
        sample = []
        for j in qs[:limit]:
            text = f"{j.title}\n{j.description or ''}"
            rel = is_relevant_role(text)
            skills = extract_skills(text)
            sample.append({
                "id": str(j.id),
                "title": j.title,
                "source": getattr(j.source, "name", None),
                "company": getattr(j.company, "name", None),
                "location": getattr(j.location, "city", None),
                "posted_at": j.posted_at.isoformat() if j.posted_at else None,
                "relevant": rel,
                "skills": skills,
                "external_url": j.external_url,
            })

        payload = {
            "summary": summary,
            "sample": sample,
        }
        self.stdout.write(json.dumps(payload, indent=2, default=str))
