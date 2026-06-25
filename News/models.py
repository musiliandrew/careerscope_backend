from django.db import models
import uuid


class NewsArticles(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500)
    url = models.TextField(unique=True)
    source = models.CharField(max_length=200, blank=True, null=True)
    published_at = models.DateTimeField()
    summary = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    tags = models.JSONField(blank=True, null=True)
    topics = models.JSONField(blank=True, null=True)
    sentiment_score = models.DecimalField(max_digits=4, decimal_places=3, blank=True, null=True)
    fetched_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "news_articles"

# Create your models here.
