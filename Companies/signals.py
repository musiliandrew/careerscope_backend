from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from Companies.models import Companies
from backend.cloud_tasks import enqueue_task


@receiver(post_save, sender=Companies)
def companies_post_save(sender, instance: Companies, created: bool, **kwargs):
    if not created:
        return

    def _enqueue():
        # Dispatch a Cloud Task directly to the data-ingestion-system's worker
        enqueue_task(
            endpoint="/worker/consume",
            payload={
                "message": {
                    "data": __import__("base64").b64encode(
                        __import__("json").dumps({
                            "source_id": str(instance.id),
                            "source_name": "company_onboarding_pipeline",
                        }).encode()
                    ).decode()
                }
            }
        )

    # Ensure tasks run after transaction commits (admin create)
    transaction.on_commit(_enqueue)
