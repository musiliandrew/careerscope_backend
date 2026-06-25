from django.apps import AppConfig


class OauthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "Oauth"

    def ready(self):
        # Import signals to ensure handlers are registered
        from . import signals  # noqa: F401
