# Add want_to_learn column to user_skills
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('Oauth', '0004_create_jobpreferences'),
    ]

    operations = [
        migrations.AddField(
            model_name='userskills',
            name='want_to_learn',
            field=models.BooleanField(default=False, blank=True),
        ),
    ]
