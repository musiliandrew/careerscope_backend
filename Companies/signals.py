from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from Companies.models import Companies
from Companies.tasks import (
    backfill_company_urls_for_company,
    ingest_company_news_for_company,
    enrich_company_metadata_for_company,
    ingest_company_jobs_for_company,
)


@receiver(post_save, sender=Companies)
def companies_post_save(sender, instance: Companies, created: bool, **kwargs):
    if not created:
        return

    def _enqueue():
        backfill_company_urls_for_company.delay(str(instance.id))
        enrich_company_metadata_for_company.delay(str(instance.id))
        ingest_company_news_for_company.delay(str(instance.id), max_items=3)
        ingest_company_jobs_for_company.delay(str(instance.id))

    # Ensure tasks run after transaction commits (admin create)
    transaction.on_commit(_enqueue)
