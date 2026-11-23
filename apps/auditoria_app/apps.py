from django.apps import AppConfig


class AuditoriaAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.auditoria_app"
    label = "auditoria_app"
    verbose_name = "Historial de cambios"

    def ready(self):
        from . import signals
