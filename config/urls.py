from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuentas/", include("cuentas.urls")),
    path("personal/", include("apps.empleados_app.urls")),
    path("operaciones/", include("apps.servicios_app.urls")),
    path("asistencias/", include("apps.asistencias_app.urls")),
    path("liquidaciones/", include("apps.liquidaciones_app.urls")),
    path("", include("inicio.urls")),
]
admin.site.site_header = "Administración de la organización"
admin.site.site_title = "Administración"
