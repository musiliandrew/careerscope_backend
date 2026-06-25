from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("Oauth", "0005_add_want_to_learn"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="github_url",
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="profile",
            name="location",
            field=models.CharField(max_length=255, blank=True, null=True),
        ),
    ]
