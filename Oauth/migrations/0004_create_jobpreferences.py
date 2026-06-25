# Generated manually to create missing JobPreferences table
from django.db import migrations, models
import django.db.models.deletion
import uuid
from django.conf import settings


class Migration(migrations.Migration):
    dependencies = [
        ('Oauth', '0003_alter_userskills_id_profile_educationbackground_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobPreferences',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, serialize=False)),
                ('target_role', models.TextField(blank=True, null=True)),
                ('preferred_work_type', models.TextField(blank=True, null=True)),
                ('preferred_locations', models.TextField(blank=True, null=True)),
                ('target_salary_min', models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)),
                ('target_salary_max', models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)),
                ('available_from', models.DateTimeField(blank=True, null=True)),
                ('notice_period', models.CharField(max_length=20, blank=True, null=True)),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='preferences', to='Oauth.profile')),
            ],
        ),
    ]
