from django.core.management.base import BaseCommand, CommandError

from Intelligence.vectorDB.client import qdrant_health


class Command(BaseCommand):
    help = "Check Qdrant connectivity using QDRANT_ENDPOINT and QDRANT_API_KEY/CAREERSCOPE_VECTOR_API."

    def handle(self, *args, **options):
        try:
            result = qdrant_health()
        except Exception as exc:
            raise CommandError(f"Qdrant health check failed: {exc}") from exc

        if not result["ok"]:
            raise CommandError(f"Qdrant returned HTTP {result['status_code']}: {result['detail']}")

        collections = ", ".join(result["collections"]) or "none"
        self.stdout.write(self.style.SUCCESS(f"Qdrant reachable. Collections: {collections}"))
