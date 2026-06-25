"""
Companies/tasks.py — Stub tasks. Job/company ingestion logic has moved to
the standalone 'data-ingestion-system' FastAPI service.

These Celery tasks are kept as stubs so that signals.py and existing code
still work. The DIS service handles the actual data collection independently.
"""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="Companies.tasks.backfill_company_urls_for_company")
def backfill_company_urls_for_company(company_id: str):
    """
    Stub — URL backfill is now handled by data-ingestion-system.
    Call POST http://dis-host:8001/trigger/company_backfill to run manually.
    """
    logger.info(
        "companies.tasks.backfill_company_urls_for_company: "
        "This task is stubbed. Use the DIS service (data-ingestion-system) instead. "
        "company_id=%s",
        company_id,
    )
    return {"status": "delegated_to_dis", "company_id": company_id}


@shared_task(name="Companies.tasks.ingest_company_news_for_company")
def ingest_company_news_for_company(company_id: str, max_items: int = 5):
    """Stub — company news ingestion is handled by data-ingestion-system."""
    logger.info("companies.tasks.ingest_company_news_for_company: stub. company_id=%s", company_id)
    return {"status": "delegated_to_dis", "company_id": company_id}


@shared_task(name="Companies.tasks.enrich_company_metadata_for_company")
def enrich_company_metadata_for_company(company_id: str):
    """Stub — company enrichment is handled by data-ingestion-system."""
    logger.info("companies.tasks.enrich_company_metadata_for_company: stub. company_id=%s", company_id)
    return {"status": "delegated_to_dis", "company_id": company_id}


@shared_task(name="Companies.tasks.ingest_company_jobs_for_company")
def ingest_company_jobs_for_company(company_id: str):
    """Stub — company job ingestion is handled by data-ingestion-system."""
    logger.info("companies.tasks.ingest_company_jobs_for_company: stub. company_id=%s", company_id)
    return {"status": "delegated_to_dis", "company_id": company_id}
