from django.db import models
from django.utils import timezone
from django.conf import settings


class ApplicationEvents(models.Model):
    id = models.UUIDField(primary_key=True)
    application = models.ForeignKey('Applications', models.DO_NOTHING)
    event_type = models.CharField(max_length=30, blank=True, null=True)
    event_date = models.DateTimeField()
    title = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    interviewer_name = models.CharField(max_length=200, blank=True, null=True)
    interviewer_title = models.CharField(max_length=200, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    duration_minutes = models.IntegerField(blank=True, null=True)
    offer_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    offer_currency = models.CharField(max_length=10, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    preparation_notes = models.TextField(blank=True, null=True)
    outcome = models.CharField(max_length=50, blank=True, null=True)
    reminder_set = models.BooleanField(blank=True, null=True)
    reminder_datetime = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'application_events'


class ApplicationStatusHistory(models.Model):
    id = models.UUIDField(primary_key=True)
    application = models.ForeignKey('Applications', models.DO_NOTHING)
    old_status = models.CharField(max_length=20, blank=True, null=True)
    new_status = models.CharField(max_length=20)
    changed_by_user = models.BooleanField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'application_status_history'


class Applications(models.Model):
    # Application status choices
    STATUS_CHOICES = [
        ('saved', 'Saved'),
        ('applied', 'Applied'),
        ('screening', 'Screening'),
        ('interview', 'Interview'),
        ('offer', 'Offer'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
        ('accepted', 'Accepted'),
    ]

    # Application source choices (expanded to accept any value)
    SOURCE_CHOICES = [
        ('careerscope', 'CareerScope'),
        ('linkedin', 'LinkedIn'),
        ('company_site', 'Company Site'),
        ('referral', 'Referral'),
        ('recruiter', 'Recruiter'),
        ('job_board', 'Job Board'),
        ('indeed', 'Indeed'),
        ('glassdoor', 'Glassdoor'),
        ('angel_list', 'AngelList'),
        ('github', 'GitHub'),
        ('twitter', 'Twitter'),
        ('email', 'Email'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.DO_NOTHING)
    job = models.ForeignKey('Jobs.Jobs', models.DO_NOTHING, blank=True, null=True)
    job_interest = models.ForeignKey('Jobs.JobInterests', models.DO_NOTHING, blank=True, null=True)
    company_name = models.CharField(max_length=255)
    job_title = models.CharField(max_length=255)
    status = models.CharField(max_length=20, blank=True, null=True)
    applied_date = models.DateField()
    application_url = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=50, blank=True, null=True)  # Increased max_length to 50
    salary_range = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    work_type = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    cover_letter = models.TextField(blank=True, null=True)
    resume_version = models.CharField(max_length=100, blank=True, null=True)
    interview_dates = models.TextField(blank=True, null=True)  # This field type is a guess.
    interview_notes = models.TextField(blank=True, null=True)
    next_action = models.CharField(max_length=255, blank=True, null=True)
    next_action_date = models.DateField(blank=True, null=True)
    follow_up_count = models.IntegerField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    feedback_received = models.TextField(blank=True, null=True)
    offer_details = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    last_status_change = models.DateTimeField(blank=True, null=True)
    
    
    @property
    def days_since_applied(self):
        """Return number of days since application was submitted."""
        if not self.applied_date:
            return None
        delta = timezone.now().date() - self.applied_date
        return delta.days

    class Meta:
        managed = True
        db_table = 'applications'
        
class EmailTracking(models.Model):
    id = models.UUIDField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.DO_NOTHING)
    application = models.ForeignKey(Applications, models.DO_NOTHING, blank=True, null=True)
    email_id = models.CharField(unique=True, max_length=255)
    thread_id = models.CharField(max_length=255, blank=True, null=True)
    subject = models.CharField(max_length=500, blank=True, null=True)
    sender = models.CharField(max_length=255, blank=True, null=True)
    sender_name = models.CharField(max_length=255, blank=True, null=True)
    received_at = models.DateTimeField()
    body_text = models.TextField(blank=True, null=True)
    body_html = models.TextField(blank=True, null=True)
    email_type = models.CharField(max_length=30, blank=True, null=True)
    company_identified = models.CharField(max_length=255, blank=True, null=True)
    job_title_identified = models.CharField(max_length=255, blank=True, null=True)
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    is_processed = models.BooleanField(blank=True, null=True)
    processing_status = models.CharField(max_length=20, blank=True, null=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    application_created = models.BooleanField(blank=True, null=True)
    event_created = models.BooleanField(blank=True, null=True)
    user_notified = models.BooleanField(blank=True, null=True)
    ai_model_used = models.CharField(max_length=100, blank=True, null=True)
    extraction_data = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'email_tracking'


class PendingInterviewConfirmation(models.Model):
    application = models.OneToOneField('Applications', on_delete=models.CASCADE)
    email_thread_id = models.CharField(max_length=255)
    gmail_message_id = models.CharField(max_length=255)
    proposed_times = models.JSONField()  # list of ISO strings
    recruiter_email = models.EmailField()
    company_name = models.CharField(max_length=200)
    role = models.CharField(max_length=200)
    stage = models.CharField(max_length=50)
    status = models.CharField(
        max_length=20,
        default="pending",
        choices=[
            ("pending", "Pending"),
            ("confirmed", "Confirmed"),
            ("rejected", "Rejected"),
        ],
    )
    user_response = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'pending_interview_confirmations'
