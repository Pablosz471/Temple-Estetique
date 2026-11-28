from django.apps import AppConfig


class EmpleadosAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.empleados_app'
    label = 'empleados_app'
    verbose_name = "Empleados"
