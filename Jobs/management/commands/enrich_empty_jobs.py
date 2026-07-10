import os
import requests
from django.core.management.base import BaseCommand
from Jobs.models import Jobs

class Command(BaseCommand):
    help = "Enrich jobs that have no skills/technologies using the AI Enrichment System."

    def handle(self, *args, **options):
        from django.db.models import Q
        # Find jobs with empty skills list or the basic placeholder
        jobs_to_enrich = Jobs.objects.filter(Q(skills=[]) | Q(skills=['Software Engineering']))
        total = jobs_to_enrich.count()
        self.stdout.write(self.style.SUCCESS(f"Found {total} jobs needing skill enrichment."))

        ai_url = f"{os.getenv('AI_ENRICHMENT_URL', 'http://127.0.0.1:8002')}/sync-execute"
        
        success_count = 0
        fail_count = 0

        for i, job in enumerate(jobs_to_enrich, 1):
            self.stdout.write(f"[{i}/{total}] Enriching job: {job.title} (ID: {job.id})...")
            
            try:
                payload = {
                    "capability": "skill_extraction",
                    "payload": {
                        "title": job.title,
                        "description": job.description or ""
                    }
                }
                resp = requests.post(ai_url, json=payload, timeout=10)
                if resp.status_code == 200:
                    extracted = resp.json().get("result", {}).get("skills", [])
                    if extracted:
                        job.skills = extracted
                        job.technologies = extracted
                        job.save()
                        self.stdout.write(self.style.SUCCESS(f"  Successfully enriched with skills: {extracted}"))
                        success_count += 1
                    else:
                        self.stdout.write(self.style.WARNING("  No skills extracted by AI."))
                        fail_count += 1
                else:
                    self.stdout.write(self.style.ERROR(f"  AI Enrichment returned status code {resp.status_code}"))
                    fail_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Failed to enrich: {e}"))
                fail_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Enrichment completed. Success: {success_count}, Failed/Skipped: {fail_count}"
        ))
