from django.db import models
import uuid
from django.contrib.postgres.fields import ArrayField


class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    event_type = models.CharField(max_length=100, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    tech_focus = ArrayField(models.CharField(max_length=100), blank=True, null=True, default=list)
    organizer = models.CharField(max_length=200, blank=True, null=True)
    sponsors = ArrayField(models.CharField(max_length=200), blank=True, null=True, default=list)
    prize_money = models.CharField(max_length=100, blank=True, null=True)
    attendee_count = models.IntegerField(blank=True, null=True)
    registration_deadline = models.DateTimeField(blank=True, null=True)
    external_url = models.TextField(blank=True, null=True)
    image_url = models.TextField(blank=True, null=True)
    is_virtual = models.BooleanField(blank=True, null=True)
    is_hybrid = models.BooleanField(blank=True, null=True)
    target_audience = ArrayField(models.CharField(max_length=100), blank=True, null=True, default=list)
    requirements = ArrayField(models.CharField(max_length=200), blank=True, null=True, default=list)
    status = models.CharField(max_length=50, blank=True, null=True)
    source = models.CharField(max_length=100, blank=True, null=True)
    match_score = models.IntegerField(blank=True, null=True)
    tags = ArrayField(models.CharField(max_length=100), blank=True, null=True, default=list)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'events'

# Create your models here.
