from django.apps import AppConfig


class CompaniesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "Companies"

    def ready(self) -> None:  # type: ignore[override]
        # Import signals to hook into post-save for Companies
        from . import signals  # noqa: F401
        return super().ready()
