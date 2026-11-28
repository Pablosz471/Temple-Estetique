from django.contrib import admin
from .models import RegistroMensual

@admin.register(RegistroMensual)
class RegistroMensualAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "empleado",
        "mes",
        "anio",
        "total_generado",
        "total_comisiones",
    )
    search_fields = (
        "empleado__nombre",
        "empleado__apellido",
    )
    list_filter = ("mes", "anio")

    # Los totales se calculan solos desde los servicios realizados.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

